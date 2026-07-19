/**
 * Right Click AI — Result Widget Logic
 * Handles streaming AI response display with rich markdown rendering.
 */

let fullText = '';
let startTime = 0;
let streamController = null;
let autoPasteEnabled = false;

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
document.addEventListener('DOMContentLoaded', async () => {
  // Register IPC listener BEFORE any async ops (prevents race condition)
  window.rightClickAI.onActionData((data) => {
    startStreaming(data);
  });

  await initAPI();

  // Check auto-paste setting
  try {
    autoPasteEnabled = await window.rightClickAI.getAutoPaste();
  } catch (e) {
    autoPasteEnabled = false;
  }

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
  document.getElementById('exportBtn').addEventListener('click', exportResult);

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
    // Ctrl+S to export
    if ((e.ctrlKey || e.metaKey) && e.key === 's' && fullText) {
      e.preventDefault();
      exportResult();
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
      // Auto-paste if enabled
      if (autoPasteEnabled && fullText.trim()) {
        setTimeout(() => {
          window.rightClickAI.pasteToActiveWindow();
        }, 300);
      }
    },
    // onError
    (error) => {
      showError(error.message);
    }
  );
}

// --- Rich Markdown Renderer ---
function renderMarkdown(text, isStreaming) {
  const resultContent = document.getElementById('resultContent');

  // Escape HTML first, but preserve markdown structure
  let html = escapeHtml(text);

  // Phase 1: Extract and protect fenced code blocks
  const codeBlocks = [];
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const placeholder = `%%CODEBLOCK_${codeBlocks.length}%%`;
    codeBlocks.push({ lang: lang.toLowerCase(), code: code.trimEnd() });
    return placeholder;
  });

  // Phase 2: Inline formatting (before block-level so we don't break blocks)

  // Headers — at line start
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Horizontal rules
  html = html.replace(/^(?:---|\*\*\*|___)\s*$/gm, '<hr>');

  // Blockquotes — lines starting with >
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote><p>$1</p></blockquote>');
  // Merge adjacent blockquotes
  html = html.replace(/<\/blockquote>\n<blockquote>/g, '\n');

  // Task lists — must come before regular lists
  html = html.replace(/^- \[x\] (.+)$/gmi, '<li class="task-item checked"><input type="checkbox" checked disabled><span>$1</span></li>');
  html = html.replace(/^- \[ \] (.+)$/gmi, '<li class="task-item"><input type="checkbox" disabled><span>$1</span></li>');

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li class="ordered">$1</li>');

  // Unordered lists (after task lists to not double-match)
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/^\* (.+)$/gm, '<li>$1</li>');

  // Tables — detect | col | col | patterns
  // Find table rows (at least one | and one separator row)
  html = html.replace(
    /((?:\|[^\n]+\|\s*\n)+)/g,
    (tableBlock) => {
      const rows = tableBlock.trim().split('\n').filter(r => r.includes('|'));
      if (rows.length < 2) return tableBlock; // Not a valid table

      let tableHtml = '<table>';
      let headerDone = false;

      for (const row of rows) {
        const cells = row.split('|').map(c => c.trim()).filter(c => c !== '');
        // Check if this is a separator row (contains only -:| etc)
        if (cells.every(c => /^:?-{3,}:?$/.test(c))) {
          headerDone = true;
          continue;
        }

        const tag = headerDone ? 'td' : 'th';
        tableHtml += '<tr>' + cells.map(c => `<${tag}>${c}</${tag}>`).join('') + '</tr>';
        // First data row after header also uses td
        if (!headerDone) headerDone = true;
        else if (rows.indexOf(row) > 0) { /* keep td */ }
      }

      // If we only had one row after detecting no separator, treat as single row table
      tableHtml += '</table>';
      return tableHtml;
    }
  );

  // Strikethrough
  html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>');

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // Bold (double asterisk)
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Italic (single asterisk)
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Images
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%;border-radius:6px;">');

  // Phase 3: Wrap adjacent list items in proper UL/OL groups
  // Group <li> items: find sequences of <li> without task-item, and wrap
  html = html.replace(
    /((?:<li(?! class="task).*<\/li>\s*)+)/g,
    (group) => {
      if (group.includes('class="ordered"')) {
        return '<ol>' + group.replace(/ class="ordered"/g, '') + '</ol>';
      }
      return '<ul>' + group + '</ul>';
    }
  );

  // Group task list items
  html = html.replace(
    /((?:<li class="task-item.*<\/li>\s*)+)/g,
    '<ul class="task-list">$1</ul>'
  );

  // Phase 4: Restore code blocks with syntax highlighting
  codeBlocks.forEach((block, i) => {
    const placeholder = `%%CODEBLOCK_${i}%%`;
    const langClass = block.lang ? ` lang-${block.lang}` : '';
    const langAttr = block.lang ? ` data-lang="${block.lang}"` : '';
    const highlightedCode = highlightCode(block.code, block.lang);
    html = html.replace(
      placeholder,
      `<pre${langAttr}><code class="${langClass}">${highlightedCode}</code></pre>`
    );
  });

  // Phase 5: Paragraph wrapping
  // Split by double newlines and wrap non-block segments
  let parts = html.split(/\n\n+/);
  html = parts.map(part => {
    part = part.trim();
    if (!part) return '';
    // If it already starts with a block tag, don't wrap
    if (/^<(h[1-6]|ul|ol|table|blockquote|hr|pre|div|p)\b/.test(part)) {
      return part;
    }
    // Single newlines inside paragraphs become <br>
    part = part.replace(/\n/g, '<br>');
    return `<p>${part}</p>`;
  }).join('');

  // Add typing cursor if still streaming (at end)
  if (isStreaming && fullText.trim()) {
    html += '<span class="typing-cursor"></span>';
  }

  resultContent.innerHTML = html;

  // Auto-scroll to bottom
  resultContent.scrollTop = resultContent.scrollHeight;
}

// --- Syntax Highlighting ---
const KEYWORDS = {
  js: ['const','let','var','function','return','if','else','for','while','class','import','export','from','async','await','try','catch','throw','new','this','typeof','instanceof','undefined','null','true','false','switch','case','break','continue','default','of','in','yield'],
  py: ['def','return','if','elif','else','for','while','class','import','from','as','try','except','finally','raise','with','yield','lambda','pass','break','continue','and','or','not','in','is','None','True','False','async','await','global','nonlocal'],
  ts: ['const','let','var','function','return','if','else','for','while','class','import','export','from','async','await','try','catch','throw','new','this','typeof','interface','type','enum','extends','implements','undefined','null','true','false'],
  html: ['div','span','p','a','button','input','form','body','head','html','script','style','meta','link','img','h1','h2','h3','h4','h5','h6','ul','ol','li','table','tr','td','th','section','header','footer','nav','main','article','aside'],
  css: ['color','background','border','margin','padding','display','position','width','height','font-size','font-weight','flex','grid','align','justify','text','overflow'],
  sql: ['SELECT','FROM','WHERE','INSERT','INTO','VALUES','UPDATE','SET','DELETE','CREATE','TABLE','ALTER','DROP','INDEX','JOIN','LEFT','RIGHT','INNER','OUTER','ON','AND','OR','NOT','NULL','AS','ORDER','BY','GROUP','HAVING','LIMIT','OFFSET'],
};

function highlightCode(code, lang) {
  const keywords = KEYWORDS[lang];
  if (!keywords || !lang) return escapeHtml(code);

  let escaped = escapeHtml(code);

  // Highlight keywords
  const kwPattern = new RegExp(`\\b(${keywords.join('|')})\\b`, 'gi');
  escaped = escaped.replace(kwPattern, '<span class="token keyword">$1</span>');

  // Highlight strings
  escaped = escaped.replace(/(["'`])(?:(?!\1|\\).|\\.)*\1/g, '<span class="token string">$&</span>');

  // Highlight comments (single-line)
  escaped = escaped.replace(/(\/\/.*$|#.*$)/gm, '<span class="token comment">$1</span>');

  // Highlight numbers
  escaped = escaped.replace(/\b(\d+\.?\d*)\b/g, '<span class="token number">$1</span>');

  return escaped;
}

// --- Show Footer ---
function showFooter() {
  const resultFooter = document.getElementById('resultFooter');
  const resultStats = document.getElementById('resultStats');

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  const wordCount = fullText.split(/\s+/).filter(Boolean).length;
  resultStats.innerHTML = `${wordCount} kata · ${elapsed}s`;

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

// --- Export Result ---
async function exportResult() {
  if (!fullText) return;

  try {
    const result = await window.rightClickAI.saveFileDialog({
      defaultName: 'rightclick-ai-result.md',
      content: fullText,
    });

    if (result.success) {
      const exportBtn = document.getElementById('exportBtn');
      exportBtn.innerHTML = '✓ Saved!';
      setTimeout(() => {
        exportBtn.innerHTML = '💾 Export';
      }, 2000);
    }
  } catch (err) {
    console.error('Export failed:', err);
    showError('Failed to save file: ' + err.message);
  }
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
