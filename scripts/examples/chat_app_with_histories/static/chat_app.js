const STORE_KEY = 'pylogue_chat_index_v1';
const CHAT_PREFIX = 'pylogue_chat_';
const IMPORT_PREFIX = document.body?.dataset.importPrefix || '__PYLOGUE_IMPORT__:';

const uuid = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'chat-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
};

const loadIndex = () => {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    return [];
  }
};

const saveIndex = (index) => {
  localStorage.setItem(STORE_KEY, JSON.stringify(index));
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

const ensureChat = () => {
  let index = loadIndex();
  if (index.length === 0) {
    const now = new Date().toISOString();
    const chat = {
      id: uuid(),
      title: 'New chat',
      created_at: now,
      updated_at: now
    };
    index = [chat];
    saveIndex(index);
    localStorage.setItem(CHAT_PREFIX + chat.id, JSON.stringify({ cards: [] }));
  }
  return index;
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
      <div class="chat-item-title">${chat.title}</div>
      <div class="chat-item-meta">${formatTime(chat.updated_at)}</div>
    `;
    btn.addEventListener('click', () => selectChat(chat.id));
    list.appendChild(btn);
  });
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

const selectChat = (chatId) => {
  const index = loadIndex();
  const chat = index.find(c => c.id === chatId);
  if (!chat) return;
  setActiveChatId(chatId);
  renderChatList(index);
  const stored = localStorage.getItem(CHAT_PREFIX + chatId);
  let payload = { cards: [] };
  if (stored) {
    try { payload = JSON.parse(stored); } catch (err) { payload = { cards: [] }; }
  }
  sendImport(payload);
};

const createChat = () => {
  const index = loadIndex();
  const now = new Date().toISOString();
  const chat = {
    id: uuid(),
    title: 'New chat',
    created_at: now,
    updated_at: now
  };
  index.unshift(chat);
  saveIndex(index);
  localStorage.setItem(CHAT_PREFIX + chat.id, JSON.stringify({ cards: [] }));
  setActiveChatId(chat.id);
  renderChatList(index);
  sendImport({ cards: [] });
};

const updateChatTitle = (cards) => {
  if (!cards || !cards.length) return;
  const first = cards[0]?.question || '';
  if (!first) return;
  const index = loadIndex();
  const chatId = getActiveChatId();
  const chat = index.find(c => c.id === chatId);
  if (!chat) return;
  if (chat.title !== 'New chat') return;
  chat.title = first.slice(0, 48);
  saveIndex(index);
};

const saveCurrentChat = () => {
  const chatId = getActiveChatId();
  if (!chatId) return;
  const exportEl = document.getElementById('chat-export');
  if (!exportEl || !exportEl.value) return;
  let payload = null;
  try { payload = JSON.parse(exportEl.value); } catch (err) { return; }
  localStorage.setItem(CHAT_PREFIX + chatId, JSON.stringify(payload));
  const index = loadIndex();
  const chat = index.find(c => c.id === chatId);
  if (chat) {
    chat.updated_at = new Date().toISOString();
    saveIndex(index);
  }
  updateChatTitle(payload.cards || []);
  renderChatList(index);
};

const init = () => {
  const index = ensureChat();
  const active = index[0]?.id;
  if (active) {
    setActiveChatId(active);
  }
  renderChatList(index);
  if (active) selectChat(active);
};

document.getElementById('new-chat-btn')?.addEventListener('click', createChat);
document.body.addEventListener('htmx:wsAfterMessage', saveCurrentChat);
document.body.addEventListener('htmx:afterSwap', saveCurrentChat);

init();
