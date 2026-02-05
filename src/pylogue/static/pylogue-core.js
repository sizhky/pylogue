
            document.documentElement.classList.remove('dark');
            const decodeCopyB64 = (value) => {
              if (!value) return '';
              try {
                const binary = atob(value);
                const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
                return new TextDecoder('utf-8').decode(bytes);
              } catch {
                return '';
              }
            };
            document.addEventListener('click', async (event) => {
              const btn = event.target.closest('.copy-btn');
              if (!btn) return;
              const targetId = btn.getAttribute('data-copy-target');
              if (!targetId) return;
              const el = document.getElementById(targetId);
              if (!el) return;
              const rawB64 = el.getAttribute('data-raw-b64');
              const text = rawB64 ? decodeCopyB64(rawB64) : (el.getAttribute('data-raw') || el.innerText);
              try {
                await navigator.clipboard.writeText(text);
                btn.dataset.copied = 'true';
                setTimeout(() => { btn.dataset.copied = 'false'; }, 1200);
              } catch (err) {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                btn.dataset.copied = 'true';
                setTimeout(() => { btn.dataset.copied = 'false'; }, 1200);
              }
            });
            document.addEventListener('click', async (event) => {
              const btn = event.target.closest('.copy-chat-btn');
              if (!btn) return;
              const exportInput = document.getElementById('chat-export');
              const input = exportInput || document.getElementById('chat-data');
              if (!input) return;
              const text = input.value || '[]';
              const blob = new Blob([text], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const link = document.createElement('a');
              const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
              link.href = url;
              link.download = `pylogue-conversation-${timestamp}.json`;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              URL.revokeObjectURL(url);
              btn.dataset.copied = 'true';
              setTimeout(() => { btn.dataset.copied = 'false'; }, 1200);
            });
            document.addEventListener('click', (event) => {
              const btn = event.target.closest('.upload-chat-btn');
              if (!btn) return;
              const input = document.getElementById('chat-upload');
              if (!input) return;
              input.click();
            });
            document.addEventListener('change', async (event) => {
              const input = event.target;
              if (!input || input.id !== 'chat-upload') return;
              const file = input.files && input.files[0];
              if (!file) return;
              try {
                const text = await file.text();
                const data = JSON.parse(text);
                const payload = JSON.stringify(data);
                const msgInput = document.getElementById('msg');
                const form = document.getElementById('form');
                if (!msgInput || !form) return;
                msgInput.value = `__PYLOGUE_IMPORT__:${payload}`;
                form.requestSubmit();
              } finally {
                input.value = '';
              }
            });
            document.body.addEventListener('htmx:wsAfterSend', () => {
              const input = document.getElementById('msg');
              if (!input) return;
              input.value = '';
            });
            document.addEventListener('keydown', (event) => {
              if (event.key !== 'Enter') return;
              const isSubmitCombo = event.metaKey || event.ctrlKey;
              if (!isSubmitCombo) return;
              const form = document.getElementById('form');
              if (!form) return;
              event.preventDefault();
              form.requestSubmit();
            });
            (function initScrollDebug() {
              const debug = [];
              const maxEntries = 300;
              const getScrollTop = () => {
                const el = document.scrollingElement || document.documentElement;
                return el ? el.scrollTop : 0;
              };
              const getActive = () => {
                const el = document.activeElement;
                if (!el) return null;
                return { tag: el.tagName, id: el.id || '', cls: el.className || '' };
              };
              const push = (type, data) => {
                debug.push({
                  t: Date.now(),
                  type,
                  scrollTop: getScrollTop(),
                  active: getActive(),
                  ...data,
                });
                if (debug.length > maxEntries) debug.shift();
              };
              window.__scrollDebug = debug;
              window.__dumpScrollDebug = () => JSON.stringify(debug, null, 2);

              let lastScrollTop = getScrollTop();
              let scrollTimer = null;
              document.addEventListener('scroll', () => {
                if (scrollTimer) return;
                scrollTimer = requestAnimationFrame(() => {
                  scrollTimer = null;
                  const current = getScrollTop();
                  if (current !== lastScrollTop) {
                    lastScrollTop = current;
                    push('scroll', {});
                  }
                });
              }, { passive: true });

              const logSwap = (label, event) => {
                const target = event && event.detail && event.detail.target;
                push(label, {
                  targetId: target ? (target.id || '') : '',
                  targetTag: target ? target.tagName : '',
                });
              };
              document.body.addEventListener('htmx:beforeSwap', (e) => logSwap('beforeSwap', e));
              document.body.addEventListener('htmx:afterSwap', (e) => logSwap('afterSwap', e));
              document.body.addEventListener('htmx:wsBeforeMessage', (e) => logSwap('wsBeforeMessage', e));
              document.body.addEventListener('htmx:wsAfterMessage', (e) => logSwap('wsAfterMessage', e));
              document.body.addEventListener('focusin', () => push('focusin', {}));
            })();
            
