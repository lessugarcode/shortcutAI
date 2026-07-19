/**
 * Right Click AI — API Communication Layer
 * Handles all HTTP requests to the Python backend.
 */

let BACKEND_URL = 'http://127.0.0.1:8765';
let AUTH_TOKEN = null;

/**
 * Build headers with auth token for all API requests.
 */
function apiHeaders(extra = {}) {
  const headers = { ...extra };
  if (AUTH_TOKEN) {
    headers['X-Auth-Token'] = AUTH_TOKEN;
  }
  return headers;
}

// Initialize backend URL and auth token from Electron
async function initAPI() {
  if (window.rightClickAI) {
    BACKEND_URL = await window.rightClickAI.getBackendUrl();
    try {
      AUTH_TOKEN = await window.rightClickAI.getAuthToken();
    } catch (e) {
      console.warn('Failed to get auth token:', e);
    }
  }
}

/**
 * Detect content type and get available actions.
 */
async function detectContent(content, hasImage = false) {
  const res = await fetch(`${BACKEND_URL}/api/ai/detect`, {
    method: 'POST',
    headers: apiHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ content, has_image: hasImage }),
  });
  if (!res.ok) throw new Error(`Detection failed: ${res.status}`);
  return res.json();
}

/**
 * Execute an AI action with streaming SSE response.
 * @param {Object} params - Action parameters
 * @param {Function} onChunk - Called with each text chunk
 * @param {Function} onDone - Called when streaming is complete
 * @param {Function} onError - Called on error
 * @returns {AbortController} - Controller to abort the stream
 */
function executeActionStream(params, onChunk, onDone, onError) {
  const controller = new AbortController();

  // 3-minute timeout
  const timeoutId = setTimeout(() => controller.abort(), 180000);

  fetch(`${BACKEND_URL}/api/ai/action`, {
    method: 'POST',
    headers: apiHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ ...params, stream: true }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(err.detail || `HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.chunk) {
                onChunk(data.chunk);
              }
              if (data.done) {
                onDone?.();
                return;
              }
              if (data.error) {
                onError?.(new Error(data.error));
                return;
              }
            } catch (e) {
              console.warn('SSE parse error:', line.substring(0, 100), e.message);
            }
          }
        }
      }
      onDone?.();
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err);
      }
    })
    .finally(() => {
      clearTimeout(timeoutId);
    });

  return controller;
}

/**
 * Get app settings.
 */
async function getSettings() {
  const res = await fetch(`${BACKEND_URL}/api/settings`, {
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(`Settings fetch failed: ${res.status}`);
  return res.json();
}

/**
 * Update app settings.
 */
async function updateSettings(updates) {
  const res = await fetch(`${BACKEND_URL}/api/settings`, {
    method: 'PUT',
    headers: apiHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error(`Settings update failed: ${res.status}`);
  return res.json();
}

/**
 * Get custom prompts.
 */
async function getCustomPrompts() {
  const res = await fetch(`${BACKEND_URL}/api/settings/prompts`, {
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(`Prompts fetch failed: ${res.status}`);
  return res.json();
}

/**
 * Get available providers and their status.
 */
async function getProviders() {
  const res = await fetch(`${BACKEND_URL}/api/ai/providers`, {
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(`Providers fetch failed: ${res.status}`);
  return res.json();
}
