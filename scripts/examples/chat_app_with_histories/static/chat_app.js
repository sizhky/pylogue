const IMPORT_PREFIX = document.body?.dataset.importPrefix || '__PYLOGUE_IMPORT__:';
let chatIndex = [];

const TRASH_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M3 6h18"/>
  <path d="M8 6V4h8v2"/>
  <path d="M6 6l1 14h10l1-14"/>
  <path d="M10 11v6"/>
  <path d="M14 11v6"/>
</svg>`;

const api = {
  async listChats() {
    const res = await fetch('/api/chats');
    return res.ok ? res.json() : [];
  },
  async createChat() {
    const res = await fetch('/api/chats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'New chat' })
    });
    return res.ok ? res.json() : null;
  },
  async getChat(chatId) {
    const res = await fetch(`/api/chats/${chatId}`);
    return res.ok ? res.json() : { cards: [] };
  },
  async saveChat(chatId, payload, title) {
    const res = await fetch(`/api/chats/${chatId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ payload, title })
    });
    return res.ok ? res.json() : null;
  },
  async deleteChat(chatId) {
    const res = await fetch(`/api/chats/${chatId}`, { method: 'DELETE' });
    return res.ok;
  }
};

const setActiveChatId = (chatId) => {
  document.body.dataset.activeChat = chatId;
};

const getActiveChatId = () => document.body.dataset.activeChat || '';

const renderChatList = (index) => {
  const list = document.getElementById('chat-list');
  if (!list) return;
  list.innerHTML = '';
  const active = getActiveChatId();
  index.forEach((chat) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'chat-item' + (chat.id === active ? ' is-active' : '');
    btn.dataset.chatId = chat.id;
    btn.innerHTML = `
      <div class="chat-item-main">
        <div class="chat-item-title" data-chat-title="true">${chat.title}</div>
        <div class="chat-item-meta">${formatTime(chat.updated_at)}</div>
      </div>
      <span class="chat-item-delete" title="Delete chat" aria-label="Delete chat">${TRASH_SVG}</span>
    `;
    btn.addEventListener('click', () => selectChat(chat.id));
    const titleEl = btn.querySelector('[data-chat-title="true"]');
    titleEl?.addEventListener('click', (event) => {
      event.stopPropagation();
      beginTitleEdit(chat.id, titleEl);
    });
    const del = btn.querySelector('.chat-item-delete');
    del?.addEventListener('click', (event) => {
      event.stopPropagation();
      confirmDelete(chat.id, chat.title || 'this chat');
    });
    list.appendChild(btn);
  });
};

const formatTime = (iso) => {
  if (!iso) return '';
  try {
    const date = new Date(iso);
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (err) {
    return '';
  }
};

const getChatById = (chatId) => chatIndex.find((c) => c.id === chatId);

const deriveTitle = (cards, currentTitle) => {
  if (currentTitle && currentTitle !== 'New chat') return currentTitle;
  if (!cards || !cards.length) return currentTitle || 'New chat';
  const first = cards[0]?.question || '';
  return first ? first.slice(0, 48) : (currentTitle || 'New chat');
};

const beginTitleEdit = (chatId, titleEl) => {
  if (!titleEl) return;
  const current = getChatById(chatId);
  if (!current) return;
  const input = document.createElement('input');
  input.className = 'chat-title-input';
  input.type = 'text';
  input.value = current.title || 'New chat';
  input.setAttribute('aria-label', 'Edit chat title');
  titleEl.replaceWith(input);
  input.focus();
  input.setSelectionRange(0, input.value.length);

  const finish = async (commit) => {
    const nextTitle = commit ? input.value.trim() : (current.title || 'New chat');
    const finalTitle = nextTitle || 'New chat';
    if (commit && finalTitle !== current.title) {
      const payload = await api.getChat(chatId);
      const saved = await api.saveChat(chatId, payload, finalTitle);
      if (saved) {
        const idx = chatIndex.findIndex((c) => c.id === chatId);
        if (idx !== -1) {
          chatIndex[idx] = { ...chatIndex[idx], ...saved };
        }
      }
    }
    renderChatList(chatIndex);
  };

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      finish(true);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      finish(false);
    }
  });
  input.addEventListener('blur', () => finish(true));
};

const sendImport = (payload) => {
  const form = document.getElementById('form');
  const msg = document.getElementById('msg');
  if (!form || !msg) return;
  const previous = msg.value;
  msg.value = IMPORT_PREFIX + JSON.stringify(payload || []);
  htmx.trigger(form, 'submit');
  msg.value = previous;
};

const selectChat = async (chatId) => {
  const chat = getChatById(chatId);
  if (!chat) return;
  setActiveChatId(chatId);
  renderChatList(chatIndex);
  const payload = await api.getChat(chatId);
  sendImport(payload);
};

const createChat = async () => {
  const chat = await api.createChat();
  if (!chat) return;
  chatIndex = [chat, ...chatIndex];
  setActiveChatId(chat.id);
  renderChatList(chatIndex);
  sendImport({ cards: [] });
};

const confirmDelete = async (chatId, title) => {
  const ok = window.confirm(`Delete "${title}"? This cannot be undone.`);
  if (!ok) return;
  const success = await api.deleteChat(chatId);
  if (!success) return;
  chatIndex = chatIndex.filter((c) => c.id !== chatId);
  const active = getActiveChatId();
  if (active === chatId) {
    const next = chatIndex[0]?.id || '';
    if (next) {
      setActiveChatId(next);
      renderChatList(chatIndex);
      await selectChat(next);
    } else {
      setActiveChatId('');
      renderChatList(chatIndex);
      sendImport({ cards: [] });
    }
    return;
  }
  renderChatList(chatIndex);
};

const saveCurrentChat = async () => {
  const chatId = getActiveChatId();
  if (!chatId) return;
  const exportEl = document.getElementById('chat-export');
  if (!exportEl || !exportEl.value) return;
  let payload = null;
  try { payload = JSON.parse(exportEl.value); } catch (err) { return; }
  const current = getChatById(chatId);
  const title = deriveTitle(payload.cards || [], current?.title);
  const saved = await api.saveChat(chatId, payload, title);
  if (saved) {
    const idx = chatIndex.findIndex((c) => c.id === chatId);
    if (idx !== -1) {
      chatIndex[idx] = { ...chatIndex[idx], ...saved };
      renderChatList(chatIndex);
    }
  }
};

const init = async () => {
  chatIndex = await api.listChats();
  if (!chatIndex.length) {
    const chat = await api.createChat();
    if (chat) chatIndex = [chat];
  }
  const active = chatIndex[0]?.id;
  if (active) {
    setActiveChatId(active);
  }
  renderChatList(chatIndex);
  if (active) await selectChat(active);
};

document.getElementById('new-chat-btn')?.addEventListener('click', () => {
  createChat();
});

document.body.addEventListener('htmx:wsAfterMessage', () => {
  saveCurrentChat();
});

(document.body).addEventListener('htmx:afterSwap', () => {
  saveCurrentChat();
});

init();
