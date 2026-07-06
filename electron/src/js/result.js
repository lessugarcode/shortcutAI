/**
 * Right Click AI — Result Widget Logic
 * Handles streaming AI response display.
 */

let fullText = '';
let startTime = 0;
let streamController = null;

const ACTION_META = {
  translate: { icon: '🌐', name: 'Terjemahkan' },
  explain: { icon: '📖', name: 'Jelaskan' },
  summarize: { icon: '📝', name: 'Ringkas' },
  fix_writing: { icon: '✍️', name: 'Perbaiki Tulisan' },
  explain_code: { icon: '🐛', name: 'Jelaskan Kode' },
  review_code: { icon: '🔍', name: 'Review Kode' },
  describe_image: { icon: '🖼️', name: 'Jelaskan Gambar' },
  ocr: { icon: '📄', name: 'Ekstrak Teks' },
  ask_ai: { icon: '💬', name: 'Tanya AI' },
};

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
  // Register IPC listener BEFORE any async ops (prevents race condition)
  window.rightClickAI.onActionData((data) => {
    startStreaming(data);
  });

  initAPI();

  // Controls
  document.getElementById('closeBtn').addEventListener('click', () => {
    if (streamController) streamController.abort();
    window.rightClickAI.closeWindow();
  });

  document.getElementById('pinBtn').addEventListener('click', () => {
    window.rightClickAI.togglePin();
  });

  window.rightClickAI.onPinState((isPinned) => {
    const pinBtn = document.getElementById('pinBtn');
    pinBtn.textContent = isPinned ? '📍' : '📌';
    pinBtn.style.background = isPinned ? 'var(--accent-subtle)' : 'transparent';
  });

  document.getElementById('copyBtn').addEventListener('click', copyResult);

  // ESC to close
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (streamController) streamController.abort();
      window.rightClickAI.closeWindow();
    }
    // Ctrl+C to copy
    if ((e.ctrlKey || e.metaKey) && e.key === 'c' && !window.getSelection().toString()) {
      copyResult();
    }
  });
});

// --- Start Streaming ---
function startStreaming(actionData) {
  const resultContent = document.getElementById('resultContent');
  const resultFooter = document.getElementById('resultFooter');
  const resultActionIcon = document.getElementById('resultActionIcon');
  const resultActionName = document.getElementById('resultActionName');

  // Set header
  const meta = ACTION_META[actionData.action_id] || { icon: '⚡', name: actionData.action_id };
  resultActionIcon.textContent = meta.icon;
  resultActionName.textContent = meta.name;
  document.getElementById('resultProvider').textContent = actionData.provider ? ` · ${actionData.provider}` : '';

  // Reset
  fullText = '';
  startTime = Date.now();
  resultContent.innerHTML = '<span class="typing-cursor"></span>';
  resultFooter.style.display = 'none';

  // Stream the response
  streamController = executeActionStream(
    {
      action_id: actionData.action_id,
      content: actionData.content,
      image_base64: actionData.image_base64,
      image_mime_type: actionData.image_mime_type,
      target_lang: actionData.target_lang,
      user_prompt: actionData.user_prompt,
    },
    // onChunk
    (chunk) => {
      fullText += chunk;
      renderMarkdown(fullText, true);
    },
    // onDone
    () => {
      renderMarkdown(fullText, false);
      showFooter();
    },
    // onError
    (error) => {
      showError(error.message);
    }
  );
}

// --- Render Markdown (Simple) ---
function renderMarkdown(text, isStreaming) {
  const resultContent = document.getElementById('resultContent');

  // Simple markdown rendering
  let html = escapeHtml(text)
    // Code blocks (protected from subsequent regex)
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Unordered lists
    .replace(/^[*-] (.+)$/gm, '<li>$1</li>')
    // Ordered lists
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // Paragraphs (double newline)
    .replace(/\n\n/g, '</p><p>')
    // Single newlines
    .replace(/\n/g, '<br>');

  // Wrap list items
  html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
  // Fix nested ul
  html = html.replace(/<\/ul>\s*<ul>/g, '');

  // Wrap in paragraph
  if (!html.startsWith('<')) {
    html = '<p>' + html + '</p>';
  }

  // Add typing cursor if still streaming
  if (isStreaming) {
    html += '<span class="typing-cursor"></span>';
  }

  resultContent.innerHTML = html;

  // Auto-scroll to bottom
  resultContent.scrollTop = resultContent.scrollHeight;
}

// --- Show Footer ---
function showFooter() {
  const resultFooter = document.getElementById('resultFooter');
  const resultStats = document.getElementById('resultStats');

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  const wordCount = fullText.split(/\s+/).filter(Boolean).length;
  resultStats.textContent = `${wordCount} kata · ${elapsed}s`;

  resultFooter.style.display = 'flex';
  resultFooter.classList.add('animate-slide-up');
}

// --- Copy Result ---
function copyResult() {
  if (!fullText) return;

  window.rightClickAI.copyToClipboard(fullText);

  const copyBtn = document.getElementById('copyBtn');
  copyBtn.innerHTML = '✓ Copied!';
  copyBtn.classList.add('copied');

  setTimeout(() => {
    copyBtn.innerHTML = '📋 Copy';
    copyBtn.classList.remove('copied');
  }, 2000);
}

// --- Show Error ---
function showError(message) {
  const resultContent = document.getElementById('resultContent');

  resultContent.innerHTML = `
    <div class="result-error animate-scale-in">
      <div class="result-error-icon">⚠️</div>
      <div class="result-error-msg">Terjadi Kesalahan</div>
      <div class="result-error-detail">${escapeHtml(message)}</div>
      <button class="btn btn-ghost" onclick="window.rightClickAI.openSettings()" style="margin-top: 8px;">
        ⚙️ Buka Settings
      </button>
    </div>
  `;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
