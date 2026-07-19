/**
 * Right Click AI — Settings Logic
 * Manages settings UI, provider configuration, custom prompts, and history.
 */

let currentSettings = {};

const ACTION_META = {
  translate: { icon: '\u{1F310}', name: 'Translate' },
  explain: { icon: '\u{1F4D6}', name: 'Explain' },
  summarize: { icon: '\u{1F4DD}', name: 'Summarize' },
  fix_writing: { icon: '\u270D\uFE0F', name: 'Fix Writing' },
  explain_code: { icon: '\u{1F41B}', name: 'Explain Code' },
  review_code: { icon: '\u{1F50D}', name: 'Review Code' },
  describe_image: { icon: '\u{1F5BC}\uFE0F', name: 'Describe Image' },
  ocr: { icon: '\u{1F4C4}', name: 'Extract Text' },
  ask_ai: { icon: '\u{1F4AC}', name: 'Ask AI' },
};

// --- Init ---
document.addEventListener('DOMContentLoaded', async () => {
  try {
    await initAPI();
  } catch (e) {
    console.error('API init failed:', e);
  }

  // Window controls
  document.getElementById('closeBtn').addEventListener('click', () => {
    window.rightClickAI.closeWindow();
  });
  document.getElementById('minimizeBtn').addEventListener('click', () => {
    window.rightClickAI.minimizeWindow();
  });

  // Sidebar navigation
  document.querySelectorAll('.sidebar-item').forEach(item => {
    item.addEventListener('click', () => {
      const section = item.dataset.section;
      switchSection(section);
      if (section === 'history') {
        loadHistory();
      }
    });
  });

  // Load settings with retry (backend might not be ready yet)
  await loadSettingsWithRetry(5);
  
  try {
    await loadPrompts();
  } catch (e) {
    console.error('Failed to load prompts:', e);
  }
  
  try {
    checkProviderStatus();
  } catch (e) {
    console.error('Failed to check providers:', e);
  }

  // General settings change handlers
  document.getElementById('languageSelect').addEventListener('change', async (e) => {
    await updateSettings({ language: e.target.value });
    showToast('Bahasa default diperbarui');
  });

  document.getElementById('streamToggle').addEventListener('change', async (e) => {
    await updateSettings({ stream_responses: e.target.checked });
    showToast('Streaming ' + (e.target.checked ? 'diaktifkan' : 'dinonaktifkan'));
  });

  // Hotkey input
  setupHotkeyInput();
});

async function loadSettingsWithRetry(maxRetries) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await loadSettings();
      return;
    } catch (e) {
      console.warn(`Settings load attempt ${i + 1}/${maxRetries} failed:`, e.message);
      if (i < maxRetries - 1) {
        await new Promise(r => setTimeout(r, 1500));
      }
    }
  }
  console.error('All settings load attempts failed');
  showToast('Backend belum siap. Coba restart aplikasi.', 'error');
}

// --- Section Navigation ---
function switchSection(sectionId) {
  // Update sidebar
  document.querySelectorAll('.sidebar-item').forEach(item => {
    item.classList.toggle('active', item.dataset.section === sectionId);
  });

  // Update content
  document.querySelectorAll('.settings-section').forEach(section => {
    section.classList.toggle('active', section.id === `section-${sectionId}`);
  });
}

// --- Load Settings ---
async function loadSettings() {
  try {
    currentSettings = await getSettings();

    // General
    document.getElementById('languageSelect').value = currentSettings.language || 'id';
    document.getElementById('streamToggle').checked = currentSettings.stream_responses !== false;
    document.getElementById('hotkeyInput').value = currentSettings.hotkey || 'CommandOrControl+Shift+Q';

    // Provider-specific
    if (currentSettings.ollama) {
      document.getElementById('ollama-url').value = currentSettings.ollama.base_url || 'http://localhost:11434';
    }

    // Highlight active provider
    updateActiveProviderUI(currentSettings.active_provider || 'ollama');
  } catch (err) {
    console.error('Failed to load settings:', err);
    showToast('Gagal memuat settings', 'error');
  }
}

// --- Active Provider UI ---
function updateActiveProviderUI(providerName) {
  document.querySelectorAll('.provider-card').forEach(card => {
    card.classList.remove('active-provider');
  });
  const card = document.getElementById(`card-${providerName}`);
  if (card) {
    card.classList.add('active-provider');
  }
}

// --- Set Active Provider ---
async function setActiveProvider(providerName) {
  try {
    await updateSettings({ active_provider: providerName });
    updateActiveProviderUI(providerName);
    showToast(`Provider aktif: ${providerName}`);
  } catch (err) {
    showToast('Gagal mengubah provider', 'error');
  }
}

// --- Save & Use Provider ---
async function saveAndUseProvider(providerName) {
  try {
    const updates = {};

    if (providerName === 'openai') {
      const key = document.getElementById('openai-key').value;
      const model = document.getElementById('openai-model').value;
      if (!key) {
        showToast('Masukkan API key yang valid', 'error');
        return;
      }
      if (isKeyMasked(key, currentSettings.openai?.api_key)) {
        updates.openai = { default_model: model, enabled: true };
      } else {
        updates.openai = { api_key: key, default_model: model, enabled: true };
      }
    } else if (providerName === 'gemini') {
      const key = document.getElementById('gemini-key').value;
      const model = document.getElementById('gemini-model').value;
      if (!key) {
        showToast('Masukkan API key yang valid', 'error');
        return;
      }
      if (isKeyMasked(key, currentSettings.gemini?.api_key)) {
        updates.gemini = { default_model: model, enabled: true };
      } else {
        updates.gemini = { api_key: key, default_model: model, enabled: true };
      }
    } else if (providerName === 'anthropic') {
      const key = document.getElementById('anthropic-key').value;
      const model = document.getElementById('anthropic-model').value;
      if (!key) {
        showToast('Masukkan API key yang valid', 'error');
        return;
      }
      if (isKeyMasked(key, currentSettings.anthropic?.api_key)) {
        updates.anthropic = { default_model: model, enabled: true };
      } else {
        updates.anthropic = { api_key: key, default_model: model, enabled: true };
      }
    } else if (providerName === 'openrouter') {
      const key = document.getElementById('openrouter-key').value;
      const model = document.getElementById('openrouter-model').value;
      if (!key) {
        showToast('Masukkan API key yang valid', 'error');
        return;
      }
      if (isKeyMasked(key, currentSettings.openrouter?.api_key)) {
        updates.openrouter = { default_model: model, enabled: true };
      } else {
        updates.openrouter = { api_key: key, default_model: model, enabled: true };
      }
    }

    updates.active_provider = providerName;
    await updateSettings(updates);
    updateActiveProviderUI(providerName);
    showToast(`${providerName} tersimpan dan aktif`);

    checkProviderStatus();
  } catch (err) {
    showToast('Gagal menyimpan: ' + err.message, 'error');
  }
}

function isKeyMasked(inputValue, maskedValue) {
  if (!inputValue || !maskedValue) return false;
  return inputValue === maskedValue;
}

// --- Check Provider Status ---
async function checkProviderStatus() {
  try {
    const providers = await getProviders();

    providers.forEach(p => {
      const badge = document.getElementById(`status-${p.name}`);
      if (!badge) return;

      if (p.healthy) {
        badge.className = 'badge badge-success';
        badge.textContent = `Online (${p.models.length} models)`;

        // Update model select for Ollama
        if (p.name === 'ollama' && p.models.length > 0) {
          const select = document.getElementById('ollama-model');
          select.innerHTML = p.models.map(m =>
            `<option value="${m}">${m}</option>`
          ).join('');
        }
      } else if (p.enabled || p.name === 'ollama') {
        badge.className = 'badge badge-error';
        badge.textContent = 'Offline';
      } else {
        badge.className = 'badge';
        badge.textContent = 'Tidak dikonfigurasi';
        badge.style.color = 'var(--text-tertiary)';
      }
    });
  } catch (err) {
    console.error('Failed to check providers:', err);
  }
}

// --- Load Custom Prompts ---
async function loadPrompts() {
  try {
    const prompts = await getCustomPrompts();
    renderPrompts(prompts);
  } catch (err) {
    console.error('Failed to load prompts:', err);
  }
}

function renderPrompts(prompts) {
  const list = document.getElementById('promptList');
  list.innerHTML = '';

  prompts.forEach(prompt => {
    const item = document.createElement('div');
    item.className = 'prompt-item';
    item.innerHTML = `
      <div class="prompt-item-icon">${prompt.icon}</div>
      <div class="prompt-item-info">
        <div class="prompt-item-name">${prompt.name}</div>
        <div class="prompt-item-desc">${prompt.description || (prompt.prompt_template.length > 60 ? prompt.prompt_template.substring(0, 60) + '...' : prompt.prompt_template)}</div>
      </div>
      <div class="prompt-item-types">
        ${prompt.content_types.map(t =>
          `<span class="prompt-type-tag">${t}</span>`
        ).join('')}
      </div>
    `;
    list.appendChild(item);
  });
}

// --- History ---
async function loadHistory() {
  const historyList = document.getElementById('historyList');
  if (!historyList) return;

  historyList.innerHTML = '<div class="history-loading">Loading history...</div>';

  try {
    const result = await getHistory(50, 0);
    const items = result.items || [];

    if (items.length === 0) {
      historyList.innerHTML = '<div class="history-empty">No interactions yet. Use the hotkey to trigger AI actions.</div>';
      return;
    }

    historyList.innerHTML = '';
    items.forEach(item => {
      const meta = ACTION_META[item.action_id] || { icon: '\u26A1', name: item.action_id };
      const preview = (item.content_preview || '').substring(0, 80);
      const date = item.created_at ? new Date(item.created_at).toLocaleString() : '';

      const row = document.createElement('div');
      row.className = 'history-item';
      row.innerHTML = `
        <div class="history-item-icon">${meta.icon}</div>
        <div class="history-item-info">
          <div class="history-item-name">${meta.name}</div>
          <div class="history-item-preview">${escapeHtml(preview)}</div>
          <div class="history-item-meta">
            <span>${date}</span>
            <span class="badge" style="background:var(--bg-tertiary);color:var(--text-tertiary);font-size:9px;">${escapeHtml(item.provider || 'unknown')}</span>
          </div>
        </div>
        <div class="history-item-actions">
          <button class="btn-icon history-view-btn" data-id="${item.id}" title="View full response">\u{1F50D}</button>
          <button class="btn-icon history-delete-btn" data-id="${item.id}" title="Delete">\u{1F5D1}</button>
        </div>
      `;

      historyList.appendChild(row);
    });

    // Bind click events
    historyList.querySelectorAll('.history-view-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        await viewHistoryItem(parseInt(id));
      });
    });

    historyList.querySelectorAll('.history-delete-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        await deleteHistoryItem(parseInt(id));
        loadHistory();
      });
    });

    // Click on item to view
    historyList.querySelectorAll('.history-item').forEach(item => {
      item.addEventListener('click', async () => {
        const btn = item.querySelector('.history-view-btn');
        if (btn) await viewHistoryItem(parseInt(btn.dataset.id));
      });
    });

  } catch (err) {
    console.error('Failed to load history:', err);
    historyList.innerHTML = '<div class="history-error">Failed to load history. Backend may be unavailable.</div>';
  }
}

async function viewHistoryItem(id) {
  try {
    const item = await getHistoryItem(id);
    const meta = ACTION_META[item.action_id] || { icon: '\u26A1', name: item.action_id };

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'history-modal-overlay';
    modal.innerHTML = `
      <div class="history-modal">
        <div class="history-modal-header">
          <span>${meta.icon} ${meta.name}</span>
          <span class="badge" style="background:var(--bg-tertiary);color:var(--text-tertiary);font-size:10px;">${escapeHtml(item.provider || 'unknown')}</span>
          <button class="btn-icon history-modal-close">\u2715</button>
        </div>
        <div class="history-modal-preview">
          <strong>Input:</strong> ${escapeHtml(item.content_preview || '')}
        </div>
        <div class="history-modal-content">${escapeHtml(item.response || '')}</div>
      </div>
    `;

    document.body.appendChild(modal);

    modal.querySelector('.history-modal-close').addEventListener('click', () => {
      modal.remove();
    });
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.remove();
    });

  } catch (err) {
    showToast('Failed to load response', 'error');
  }
}

// --- Hotkey Input ---
function setupHotkeyInput() {
  const input = document.getElementById('hotkeyInput');
  let isRecording = false;

  input.addEventListener('click', () => {
    if (!isRecording) {
      isRecording = true;
      input.value = 'Tekan kombinasi tombol...';
      input.style.borderColor = 'var(--accent-primary)';
      input.style.boxShadow = '0 0 0 2px var(--accent-subtle)';
    }
  });

  input.addEventListener('keydown', async (e) => {
    if (!isRecording) return;
    e.preventDefault();

    if (e.key === 'Escape') {
      isRecording = false;
      input.value = currentSettings.hotkey || 'CommandOrControl+Shift+Q';
      input.style.borderColor = '';
      input.style.boxShadow = '';
      return;
    }

    const parts = [];
    if (e.ctrlKey || e.metaKey) parts.push('CommandOrControl');
    if (e.altKey) parts.push('Alt');
    if (e.shiftKey) parts.push('Shift');

    const key = e.key;
    if (!['Control', 'Alt', 'Shift', 'Meta'].includes(key)) {
      parts.push(key.length === 1 ? key.toUpperCase() : key);
    }

    if (parts.length >= 2 && !['Control', 'Alt', 'Shift', 'Meta'].includes(e.key)) {
      const hotkey = parts.join('+');
      isRecording = false;
      input.value = hotkey;
      input.style.borderColor = '';
      input.style.boxShadow = '';

      // Save
      await updateSettings({ hotkey });
      window.rightClickAI.updateHotkey(hotkey);
      showToast(`Hotkey diperbarui: ${hotkey}`);
    }
  });

  input.addEventListener('blur', () => {
    if (isRecording) {
      isRecording = false;
      input.value = currentSettings.hotkey || 'CommandOrControl+Shift+Q';
      input.style.borderColor = '';
      input.style.boxShadow = '';
    }
  });
}

// --- Toast ---
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast show ${type}`;

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Expose for inline onclick handlers
window.setActiveProvider = setActiveProvider;
window.saveAndUseProvider = saveAndUseProvider;
