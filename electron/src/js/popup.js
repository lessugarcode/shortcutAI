/**
 * Right Click AI — Popup Logic
 * Handles action menu display and user interaction.
 */

let clipboardData = null;
let detectedType = 'text';

const LANGUAGES = [
  { code: 'id', name: 'Indonesia', flag: '🇮🇩' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'pt', name: 'Português', flag: '🇧🇷' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'th', name: 'ไทย', flag: '🇹🇭' },
  { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳' },
  { code: 'ms', name: 'Melayu', flag: '🇲🇾' },
];

// --- Init ---
document.addEventListener('DOMContentLoaded', async () => {
  await initAPI();

  window.rightClickAI.onClipboardData(async (data) => {
    clipboardData = data;
    await processClipboard(data);
  });

  // Ask AI input
  document.getElementById('askAiInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendAskAI();
    }
  });

  document.getElementById('askAiSend').addEventListener('click', sendAskAI);

  // Language overlay back button
  document.getElementById('langBack').addEventListener('click', () => {
    document.getElementById('langOverlay').classList.remove('active');
  });

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      window.rightClickAI.closeWindow();
    }
  });
});

// --- Process Clipboard ---
async function processClipboard(data) {
  const previewText = document.getElementById('previewText');
  const contentTypeBadge = document.getElementById('contentTypeBadge');
  const actionList = document.getElementById('actionList');
  const askAiContainer = document.getElementById('askAiContainer');

  // Set preview text
  if (data.hasImage) {
    previewText.textContent = '🖼️ Gambar dari clipboard';
  } else if (data.text) {
    const preview = data.text.substring(0, 60).replace(/\n/g, ' ');
    previewText.textContent = preview + (data.text.length > 60 ? '...' : '');
  }

  try {
    // Detect content type
    const result = await detectContent(data.text, data.hasImage);
    detectedType = result.content_type;

    // Show content type badge
    const typeIcons = { text: '📝', code: '💻', image: '🖼️' };
    const typeLabels = { text: 'Teks', code: 'Kode', image: 'Gambar' };
    document.getElementById('contentTypeIcon').textContent = typeIcons[detectedType] || '📝';
    document.getElementById('contentTypeLabel').textContent = typeLabels[detectedType] || 'Teks';
    contentTypeBadge.style.display = 'flex';

    // Render actions
    renderActions(result.available_actions);

    // Show Ask AI input
    askAiContainer.style.display = 'block';
  } catch (err) {
    console.error('Detection failed:', err);
    showPopupError('Backend tidak tersedia. Pastikan aplikasi berjalan.');
    // Fallback: show default actions
    renderActions([
      { id: 'translate', name: 'Terjemahkan', icon: '🌐', description: 'Terjemahkan teks' },
      { id: 'explain', name: 'Jelaskan', icon: '📖', description: 'Jelaskan dengan sederhana' },
      { id: 'summarize', name: 'Ringkas', icon: '📝', description: 'Buat ringkasan' },
      { id: 'fix_writing', name: 'Perbaiki Tulisan', icon: '✍️', description: 'Perbaiki grammar' },
    ]);
    askAiContainer.style.display = 'block';
  }
}

// --- Render Actions ---
function renderActions(actions) {
  const actionList = document.getElementById('actionList');
  actionList.innerHTML = '';

  actions.forEach((action, index) => {
    const item = document.createElement('div');
    item.className = 'action-item animate-slide-up';
    item.style.animationDelay = `${index * 0.04}s`;

    item.innerHTML = `
      <div class="action-icon">${action.icon}</div>
      <div class="action-info">
        <div class="action-name">${action.name}</div>
        <div class="action-desc">${action.description}</div>
      </div>
      <div class="action-arrow">→</div>
    `;

    item.addEventListener('click', () => onActionClick(action));
    actionList.appendChild(item);
  });
}

// --- Action Click ---
function onActionClick(action) {
  if (action.id === 'translate') {
    showLanguageSelector();
    return;
  }

  executeSelectedAction(action.id);
}

// --- Language Selector ---
function showLanguageSelector() {
  const langOverlay = document.getElementById('langOverlay');
  const langList = document.getElementById('langList');

  langList.innerHTML = '';
  LANGUAGES.forEach((lang) => {
    const item = document.createElement('div');
    item.className = 'lang-item';
    item.innerHTML = `
      <span class="lang-flag">${lang.flag}</span>
      <span>${lang.name}</span>
    `;
    item.addEventListener('click', () => {
      langOverlay.classList.remove('active');
      executeSelectedAction('translate', lang.code);
    });
    langList.appendChild(item);
  });

  langOverlay.classList.add('active');
}

// --- Execute Action ---
function executeSelectedAction(actionId, targetLang = null) {
  const actionData = {
    action_id: actionId,
    content: clipboardData?.text || '',
    image_base64: clipboardData?.imageBase64 || null,
    image_mime_type: clipboardData?.imageMimeType || null,
    target_lang: targetLang,
    user_prompt: null,
  };

  window.rightClickAI.executeAction(actionData);
}

// --- Ask AI ---
function sendAskAI() {
  const input = document.getElementById('askAiInput');
  const prompt = input.value.trim();
  if (!prompt) return;

  const actionData = {
    action_id: 'ask_ai',
    content: clipboardData?.text || '',
    image_base64: clipboardData?.imageBase64 || null,
    image_mime_type: clipboardData?.imageMimeType || null,
    target_lang: null,
    user_prompt: prompt,
  };

  window.rightClickAI.executeAction(actionData);
}

function showPopupError(message) {
  const actionList = document.getElementById('actionList');
  actionList.innerHTML = `
    <div style="text-align:center;padding:var(--space-xl);color:var(--text-tertiary)">
      <div style="font-size:2rem;margin-bottom:var(--space-sm)">⚠️</div>
      <div>${message}</div>
      <button class="btn btn-ghost" style="margin-top:var(--space-md)"
              onclick="window.rightClickAI.openSettings()">⚙️ Buka Settings</button>
    </div>`;
}
