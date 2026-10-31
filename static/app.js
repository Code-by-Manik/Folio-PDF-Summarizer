// ============================================================
// Folio — client application logic
// ============================================================

const CONFIG = {
  endpoints: {
    upload: '/api/upload',
    chat: '/api/chat',
    me: '/api/me',
  },
};

// ---------------------------------------------------------------
// State
// ---------------------------------------------------------------
const state = {
  sessionId: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
  messages: [],       // { role: 'user' | 'assistant', content, sources }
  files: new Map(),   // fileKey -> { name, status: 'indexing' | 'ready' | 'error' }
  isSending: false,
};

// ---------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------
const el = {
  hamburgerBtn: document.getElementById('hamburger-btn'),
  sidebar: document.getElementById('sidebar'),
  sidebarBackdrop: document.getElementById('sidebar-backdrop'),
  sidebarCloseBtn: document.getElementById('sidebar-close-btn'),

  newConvoBtn: document.getElementById('new-convo-btn'),

  dropzone: document.getElementById('dropzone'),
  fileInput: document.getElementById('file-input'),
  fileList: document.getElementById('file-list'),
  sourceCount: document.getElementById('source-count'),

  emptyState: document.getElementById('empty-state'),
  chatScroll: document.getElementById('chat-scroll'),
  chatMessages: document.getElementById('chat-messages'),
  promptChips: document.getElementById('prompt-chips'),

  chatInput: document.getElementById('chat-input'),
  sendBtn: document.getElementById('send-btn'),
  charStatus: document.getElementById('char-status'),

  sessionTitle: document.getElementById('session-title'),

  profileAvatar: document.getElementById('profile-avatar'),
  profileName: document.getElementById('profile-name'),
  profileEmail: document.getElementById('profile-email'),

  toastContainer: document.getElementById('toast-container'),
};

const tpl = {
  fileRow: document.getElementById('tpl-file-row'),
  msgUser: document.getElementById('tpl-msg-user'),
  msgAi: document.getElementById('tpl-msg-ai'),
  msgTyping: document.getElementById('tpl-msg-typing'),
  citationChip: document.getElementById('tpl-citation-chip'),
  toast: document.getElementById('tpl-toast'),
};

// ---------------------------------------------------------------
// Icons
// ---------------------------------------------------------------
function renderIcons() {
  if (window.lucide) lucide.createIcons();
}

// ---------------------------------------------------------------
// Toast helper
// ---------------------------------------------------------------
function showToast(message, duration = 3200) {
  if (!tpl.toast) return;
  const node = tpl.toast.content.cloneNode(true);
  node.querySelector('.toast-msg').textContent = message;
  const wrapper = document.createElement('div');
  wrapper.appendChild(node);
  const toastEl = wrapper.firstElementChild;
  el.toastContainer.appendChild(toastEl);
  renderIcons();
  setTimeout(() => {
    toastEl.style.transition = 'opacity 0.25s ease';
    toastEl.style.opacity = '0';
    setTimeout(() => toastEl.remove(), 250);
  }, duration);
}

// ---------------------------------------------------------------
// Sidebar (mobile drawer)
// ---------------------------------------------------------------
function openSidebar() {
  el.sidebar.classList.add('open');
  el.sidebarBackdrop.classList.add('open');
  el.hamburgerBtn.setAttribute('aria-expanded', 'true');
}
function closeSidebar() {
  el.sidebar.classList.remove('open');
  el.sidebarBackdrop.classList.remove('open');
  el.hamburgerBtn.setAttribute('aria-expanded', 'false');
}
el.hamburgerBtn?.addEventListener('click', () => {
  el.sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
});
el.sidebarCloseBtn?.addEventListener('click', closeSidebar);
el.sidebarBackdrop?.addEventListener('click', closeSidebar);

// ---------------------------------------------------------------
// New conversation
// ---------------------------------------------------------------
el.newConvoBtn?.addEventListener('click', () => {
  state.sessionId = crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
  state.messages = [];
  el.chatMessages.innerHTML = '';
  el.chatScroll.classList.add('hidden');
  el.emptyState.classList.remove('hidden');
  el.sessionTitle.textContent = 'New conversation';
  el.chatInput.value = '';
  autoResizeInput();
  updateSendState();
  closeSidebar();
});

// ---------------------------------------------------------------
// File upload — drag & drop + click-to-browse
// ---------------------------------------------------------------
['dragenter', 'dragover'].forEach((evt) => {
  el.dropzone?.addEventListener(evt, (e) => {
    e.preventDefault();
    el.dropzone.classList.add('drag-active');
  });
});
['dragleave', 'drop'].forEach((evt) => {
  el.dropzone?.addEventListener(evt, (e) => {
    e.preventDefault();
    el.dropzone.classList.remove('drag-active');
  });
});
el.dropzone?.addEventListener('drop', (e) => {
  const files = Array.from(e.dataTransfer.files || []).filter(f => f.type === 'application/pdf');
  if (files.length) handleFiles(files);
  else if (e.dataTransfer.files.length) showToast('Only PDF files are supported.');
});
el.fileInput?.addEventListener('change', (e) => {
  const files = Array.from(e.target.files || []);
  if (files.length) handleFiles(files);
  el.fileInput.value = '';
});

function handleFiles(files) {
  files.forEach(uploadFile);
}

function renderFileList() {
  el.fileList.innerHTML = '';
  state.files.forEach((file, key) => {
    const node = tpl.fileRow.content.cloneNode(true);
    const li = node.querySelector('li');
    li.dataset.key = key;
    node.querySelector('.filename').textContent = file.name;
    const dot = node.querySelector('.status-dot');
    const label = node.querySelector('.status-label');
    dot.classList.remove('status-indexing', 'status-ready', 'status-error');
    if (file.status === 'ready') {
      dot.classList.add('status-ready');
      label.textContent = 'Ready';
    } else if (file.status === 'error') {
      dot.classList.add('status-error');
      label.textContent = 'Failed';
    } else {
      dot.classList.add('status-indexing');
      label.textContent = 'Indexing…';
    }
    el.fileList.appendChild(node);
  });
  el.sourceCount.textContent = String(state.files.size);
  renderIcons();
}

async function uploadFile(file) {
  const key = `${file.name}-${file.size}-${Date.now()}`;
  state.files.set(key, { name: file.name, status: 'indexing' });
  renderFileList();

  const formData = new FormData();
  formData.append('files', file);
  formData.append('session_id', state.sessionId);

  try {
    const res = await fetch(CONFIG.endpoints.upload, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed (${res.status})`);
    const data = await res.json();

    const entry = state.files.get(key);
    if (entry) {
      entry.status = (data && data.status === 'error') ? 'error' : 'ready';
      renderFileList();
    }
    showToast(`${file.name} indexed and ready.`);
  } catch (err) {
    console.error(err);
    const entry = state.files.get(key);
    if (entry) {
      entry.status = 'error';
      renderFileList();
    }
    showToast(`Couldn't upload ${file.name}. Check connection and endpoint.`);
  }
}

// ---------------------------------------------------------------
// Chat input — auto-expanding textarea, send state
// ---------------------------------------------------------------
function autoResizeInput() {
  if (!el.chatInput) return;
  el.chatInput.style.height = 'auto';
  el.chatInput.style.height = Math.min(el.chatInput.scrollHeight, 200) + 'px';
}
function updateSendState() {
  if (!el.chatInput || !el.sendBtn) return;
  const hasText = el.chatInput.value.trim().length > 0;
  el.sendBtn.disabled = !hasText || state.isSending;
}
el.chatInput?.addEventListener('input', () => {
  autoResizeInput();
  updateSendState();
});
el.chatInput?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    trySend();
  }
});
el.sendBtn?.addEventListener('click', trySend);

el.promptChips?.querySelectorAll('.prompt-chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    el.chatInput.value = chip.textContent.trim();
    autoResizeInput();
    updateSendState();
    trySend();
  });
});

function trySend() {
  const text = el.chatInput.value.trim();
  if (!text || state.isSending) return;
  sendMessage(text);
}

// ---------------------------------------------------------------
// Chat rendering
// ---------------------------------------------------------------
function ensureChatVisible() {
  if (!el.chatScroll.classList.contains('hidden')) return;
  el.emptyState.classList.add('hidden');
  el.chatScroll.classList.remove('hidden');
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    el.chatScroll.scrollTop = el.chatScroll.scrollHeight;
  });
}

function appendUserMessage(text) {
  ensureChatVisible();
  const node = tpl.msgUser.content.cloneNode(true);
  node.querySelector('.bubble-user').textContent = text;
  el.chatMessages.appendChild(node);
  scrollToBottom();
}

function appendTypingIndicator() {
  const node = tpl.msgTyping.content.cloneNode(true);
  el.chatMessages.appendChild(node);
  scrollToBottom();
  return el.chatMessages.querySelector('#typing-row');
}

function appendAiMessage(answerHtml, sources) {
  const node = tpl.msgAi.content.cloneNode(true);
  node.querySelector('.ai-content').innerHTML = answerHtml;

  const citationsRow = node.querySelector('.citations-row');
  (sources || []).forEach((src) => {
    const chipNode = tpl.citationChip.content.cloneNode(true);
    const label = chipNode.querySelector('.chip-label');
    const docName = chipNode.querySelector('.chip-doc-name');
    const snippet = chipNode.querySelector('.chip-snippet');

    const page = src.page ?? src.page_number ?? '?';
    label.textContent = `p. ${page}`;
    docName.textContent = src.filename || src.document || 'Source document';
    snippet.textContent = src.snippet || src.text || 'No preview available for this citation.';

    citationsRow.appendChild(chipNode);
  });

  el.chatMessages.appendChild(node);
  renderIcons();
  scrollToBottom();
}

// ---------------------------------------------------------------
// Send message -> POST /api/chat
// ---------------------------------------------------------------
async function sendMessage(text) {
  state.isSending = true;
  updateSendState();

  appendUserMessage(text);
  state.messages.push({ role: 'user', content: text });

  el.chatInput.value = '';
  autoResizeInput();

  const typingRow = appendTypingIndicator();

  try {
    const res = await fetch(CONFIG.endpoints.chat, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        session_id: state.sessionId,
      }),
    });

    if (!res.ok) throw new Error(`Chat request failed (${res.status})`);
    const data = await res.json();

    typingRow?.remove();

    const rawAnswer = data.answer || data.response || '';
    const answerHtml = window.marked
      ? marked.parse(rawAnswer)
      : escapeHtml(rawAnswer);

    const sources = data.sources || data.citations || [];
    appendAiMessage(answerHtml, sources);
    state.messages.push({ role: 'assistant', content: rawAnswer, sources: sources });

    if (data.session_title) {
      el.sessionTitle.textContent = data.session_title;
    }
  } catch (err) {
    console.error(err);
    typingRow?.remove();
    appendAiMessage(
      `<p class="text-red-300">Something went wrong reaching the backend. Please try again.</p>`,
      []
    );
    showToast("Couldn't reach the server. Check your connection.");
  } finally {
    state.isSending = false;
    updateSendState();
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return `<p>${div.innerHTML}</p>`;
}

// ---------------------------------------------------------------
// Profile — GET /api/me
// ---------------------------------------------------------------
async function loadProfile() {
  try {
    const res = await fetch(CONFIG.endpoints.me);
    if (!res.ok) throw new Error(`Profile request failed (${res.status})`);
    const data = await res.json();

    const name = data.name || data.full_name || data.username || 'Anonymous';
    el.profileName.textContent = name;
    el.profileEmail.textContent = data.email || '';

    if (data.avatar_url) {
      el.profileAvatar.innerHTML = `<img src="${data.avatar_url}" alt="${name}" class="w-full h-full object-cover rounded-full" />`;
    } else {
      const initials = name
        .split(' ')
        .map((p) => p[0])
        .slice(0, 2)
        .join('')
        .toUpperCase();
      el.profileAvatar.textContent = initials || '?';
    }
  } catch (err) {
    console.error(err);
    el.profileName.textContent = 'Guest';
    el.profileEmail.textContent = 'Local Session';
    el.profileAvatar.textContent = 'G';
  }
}

// ---------------------------------------------------------------
// Init
// ---------------------------------------------------------------
function init() {
  renderIcons();
  updateSendState();
  autoResizeInput();
  loadProfile();

  window.addEventListener('resize', () => {
    if (window.innerWidth >= 1024) closeSidebar();
  });
}

document.addEventListener('DOMContentLoaded', init);