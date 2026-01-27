# Core FastHTML + MonsterUI chat
from fasthtml.common import *
from monsterui.all import Theme, Container, ContainerT, TextPresets, Button, ButtonT, FastHTML as MUFastHTML, UkIcon
import asyncio
import inspect
import json


class EchoResponder:
    async def __call__(self, message: str):
        response = f"ECHO: {message}"
        for ch in response:
            await asyncio.sleep(0.01)
            yield ch


def render_input():
    return Input(
        id="msg",
        name="msg",
        placeholder="Say hi...",
        autofocus=True,
        cls="uk-input w-full bg-white border-slate-300 focus:border-slate-500 focus:ring-2 focus:ring-slate-200",
    )


def render_cards(cards):
    rows = []
    data_json = json.dumps(cards)
    for card in cards:
        card_id = card.get("id", "")
        assistant_id = f"assistant-{card_id}" if card_id else ""
        rows.append(
            Div(
                P("You", cls=(TextPresets.muted_sm, "text-right")),
                Div(card["question"], cls="marked text-base text-right"),
                cls="chat-row-block chat-row-user",
            )
        )
        rows.append(
            Div(
                P("Assistant", cls=(TextPresets.muted_sm, "text-left")),
                Div(
                    Button(
                        UkIcon("copy"),
                        cls="uk-button uk-button-text copy-btn",
                        type="button",
                        data_copy_target=assistant_id,
                        aria_label="Copy response",
                        title="Copy response",
                    ),
                    cls="flex justify-end",
                ),
                Div(
                    card["answer"] or "…",
                    id=assistant_id if assistant_id else None,
                    data_raw=card["answer"] or "",
                    cls="marked text-base text-left",
                ),
                cls="chat-row-block chat-row-assistant",
            )
        )
    return Div(
        *rows,
        Input(type="hidden", id="chat-data", value=data_json),
        id="cards",
        cls="divide-y divide-slate-200",
    )


def get_core_headers(include_markdown: bool = True):
    headers = list(Theme.slate.headers())
    if include_markdown:
        headers.append(MarkdownJS())
        headers.append(
            Script(
                """
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

                let mermaidReady = false;
                let mermaidCounter = 0;
                const mermaidStates = {};

                const ensureMermaid = () => {
                    if (mermaidReady) return;
                    mermaid.initialize({ startOnLoad: false });
                    mermaidReady = true;
                };

                const applyMermaidState = (wrapper, state) => {
                    const svg = wrapper.querySelector('svg');
                    if (!svg) return;
                    svg.style.pointerEvents = 'none';
                    svg.style.transform = `translate(${state.translateX}px, ${state.translateY}px) scale(${state.scale})`;
                    svg.style.transformOrigin = 'center center';
                };

                const fitSvgToWrapper = (wrapper, state) => {
                    const svg = wrapper.querySelector('svg');
                    if (!svg) return;
                    const wrapperRect = wrapper.getBoundingClientRect();
                    const svgRect = svg.getBoundingClientRect();
                    if (!wrapperRect.width || !wrapperRect.height || !svgRect.width || !svgRect.height) return;
                    const padding = 16;
                    const scaleX = (wrapperRect.width - padding) / svgRect.width;
                    const scaleY = (wrapperRect.height - padding) / svgRect.height;
                    const initialScale = Math.min(scaleX, scaleY, 1);
                    state.scale = initialScale;
                    state.translateX = 0;
                    state.translateY = 0;
                    applyMermaidState(wrapper, state);
                };

                const initMermaidInteraction = (wrapper) => {
                    if (wrapper.dataset.mermaidInteractive === 'true') return;
                    const svg = wrapper.querySelector('svg');
                    if (!svg) return;

                    const state = {
                        scale: 1,
                        translateX: 0,
                        translateY: 0,
                        isPanning: false,
                        startX: 0,
                        startY: 0,
                    };
                    mermaidStates[wrapper.id] = state;
                    wrapper.dataset.mermaidInteractive = 'true';

                    fitSvgToWrapper(wrapper, state);

                    wrapper.style.cursor = 'grab';
                    wrapper.style.touchAction = 'none';

                    wrapper.addEventListener('wheel', (e) => {
                        e.preventDefault();
                        const currentSvg = wrapper.querySelector('svg');
                        if (!currentSvg) return;
                        const rect = currentSvg.getBoundingClientRect();
                        const mouseX = e.clientX - rect.left - rect.width / 2;
                        const mouseY = e.clientY - rect.top - rect.height / 2;
                        const zoomIntensity = 0.01;
                        const delta = e.deltaY > 0 ? 1 - zoomIntensity : 1 + zoomIntensity;
                        const newScale = Math.min(Math.max(0.1, state.scale * delta), 12);
                        const scaleFactor = newScale / state.scale - 1;
                        state.translateX -= mouseX * scaleFactor;
                        state.translateY -= mouseY * scaleFactor;
                        state.scale = newScale;
                        applyMermaidState(wrapper, state);
                    }, { passive: false });

                    wrapper.addEventListener('pointerdown', (e) => {
                        if (e.pointerType === 'mouse' && e.button !== 0) return;
                        state.isPanning = true;
                        state.startX = e.clientX - state.translateX;
                        state.startY = e.clientY - state.translateY;
                        wrapper.setPointerCapture(e.pointerId);
                        wrapper.style.cursor = 'grabbing';
                        e.preventDefault();
                    });

                    wrapper.addEventListener('pointermove', (e) => {
                        if (!state.isPanning) return;
                        state.translateX = e.clientX - state.startX;
                        state.translateY = e.clientY - state.startY;
                        applyMermaidState(wrapper, state);
                    });

                    const stopPanning = (e) => {
                        if (!state.isPanning) return;
                        state.isPanning = false;
                        try {
                            wrapper.releasePointerCapture(e.pointerId);
                        } catch {
                            // Ignore if pointer capture is not active
                        }
                        wrapper.style.cursor = 'grab';
                    };
                    wrapper.addEventListener('pointerup', stopPanning);
                    wrapper.addEventListener('pointercancel', stopPanning);
                };

                const scheduleMermaidInteraction = (wrapper, { maxAttempts = 12, delayMs = 80 } = {}) => {
                    let attempt = 0;
                    const check = () => {
                        if (wrapper.querySelector('svg')) {
                            initMermaidInteraction(wrapper);
                            return;
                        }
                        if (attempt >= maxAttempts) return;
                        attempt += 1;
                        setTimeout(check, delayMs);
                    };
                    check();
                };

                const createMermaidContainer = (codeText) => {
                    mermaidCounter += 1;
                    const diagramId = `chat-mermaid-${mermaidCounter}`;

                    const container = document.createElement('div');
                    container.className = 'mermaid-container';

                    const controls = document.createElement('div');
                    controls.className = 'mermaid-controls';
                    controls.innerHTML = `
                        <button type="button" data-action="reset" title="Reset zoom">Reset</button>
                        <button type="button" data-action="zoom-in" title="Zoom in">+</button>
                        <button type="button" data-action="zoom-out" title="Zoom out">−</button>
                    `;

                    const wrapper = document.createElement('div');
                    wrapper.id = diagramId;
                    wrapper.className = 'mermaid-wrapper';
                    wrapper.dataset.mermaidCode = codeText;

                    const pre = document.createElement('pre');
                    pre.className = 'mermaid';
                    pre.textContent = codeText;
                    wrapper.appendChild(pre);

                    container.appendChild(controls);
                    container.appendChild(wrapper);

                    controls.addEventListener('click', (event) => {
                        const btn = event.target.closest('button');
                        if (!btn) return;
                        const action = btn.getAttribute('data-action');
                        if (action === 'reset') {
                            resetMermaidZoom(wrapper.id);
                        } else if (action === 'zoom-in') {
                            zoomMermaidIn(wrapper.id);
                        } else if (action === 'zoom-out') {
                            zoomMermaidOut(wrapper.id);
                        }
                    });

                    return { container, wrapper };
                };

                const resetMermaidZoom = (id) => {
                    const state = mermaidStates[id];
                    const wrapper = document.getElementById(id);
                    if (!state || !wrapper) return;
                    fitSvgToWrapper(wrapper, state);
                };

                const zoomMermaidIn = (id) => {
                    const state = mermaidStates[id];
                    const wrapper = document.getElementById(id);
                    if (!state || !wrapper) return;
                    state.scale = Math.min(state.scale * 1.1, 12);
                    applyMermaidState(wrapper, state);
                };

                const zoomMermaidOut = (id) => {
                    const state = mermaidStates[id];
                    const wrapper = document.getElementById(id);
                    if (!state || !wrapper) return;
                    state.scale = Math.max(state.scale * 0.9, 0.1);
                    applyMermaidState(wrapper, state);
                };

                const upgradeMermaidBlocks = (root = document) => {
                    const blocks = root.querySelectorAll('pre > code.language-mermaid');
                    const nodes = [];
                    blocks.forEach((code) => {
                        if (code.dataset.mermaidProcessed === 'true') return;
                        code.dataset.mermaidProcessed = 'true';
                        const pre = code.parentElement;
                        if (!pre) return;
                        const codeText = code.textContent || '';
                        const { container, wrapper } = createMermaidContainer(codeText);
                        pre.replaceWith(container);
                        nodes.push(wrapper.querySelector('pre.mermaid'));
                    });
                    if (nodes.length === 0) return;
                    ensureMermaid();
                    mermaid.run({ nodes }).then(() => {
                        nodes.forEach((node) => {
                            const wrapper = node.closest('.mermaid-wrapper');
                            if (wrapper) scheduleMermaidInteraction(wrapper);
                        });
                    });
                };

                const observeMermaid = () => {
                    const target = document.getElementById('cards');
                    if (!target) return;
                    const observer = new MutationObserver(() => upgradeMermaidBlocks(target));
                    observer.observe(target, { childList: true, subtree: true });
                    upgradeMermaidBlocks(target);
                };

                document.addEventListener('DOMContentLoaded', () => {
                    observeMermaid();
                    setTimeout(() => upgradeMermaidBlocks(document), 0);
                });

                document.body.addEventListener('htmx:afterSwap', (event) => {
                    upgradeMermaidBlocks(event.target || document);
                });

                if (window.htmx && typeof window.htmx.onLoad === 'function') {
                    window.htmx.onLoad((root) => upgradeMermaidBlocks(root || document));
                }
                """,
                type="module",
            )
        )
    headers.append(
        Style(
            """
            html, body {
                margin: 0;
                background: #f8fafc;
                color: #0f172a;
            }
            html {
                color-scheme: light;
            }
            :root, .uk-theme-slate {
                --background: 0 0% 98%;
                --foreground: 222 47% 11%;
            }
            .chat-panel {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                padding: 20px;
            }
            .chat-row-user {
                background: #f8fafc;
            }
            .chat-row-assistant {
                background: #ffffff;
            }
            .chat-row-block {
                margin: 0;
                padding: 14px 12px;
            }
            .marked a {
                color: #2563eb;
                text-decoration: underline;
                text-underline-offset: 3px;
                text-decoration-thickness: 1.5px;
            }
            .marked a:hover {
                color: #1d4ed8;
            }
            .marked table {
                width: 100%;
                border-collapse: collapse;
                margin: 16px 0;
                font-size: 0.95rem;
            }
            .marked thead th {
                background: #f1f5f9;
                color: #0f172a;
                font-weight: 600;
                border: 1px solid #e2e8f0;
                padding: 10px 12px;
                text-align: left;
            }
            .marked tbody td {
                border: 1px solid #e2e8f0;
                padding: 10px 12px;
                vertical-align: top;
            }
            .marked tbody tr:nth-child(odd) {
                background: #f8fafc;
            }
            .marked tbody tr:hover {
                background: #eef2ff;
            }
            .marked blockquote {
                margin: 16px 0;
                padding: 12px 14px;
                border-left: 3px solid #e2e8f0;
                background: #f8fafc;
                color: #475569;
                border-radius: 8px;
            }
            .marked pre {
                background: #f8fafc;
                color: #0f172a;
                padding: 12px 14px;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                overflow: auto;
            }
            .marked code {
                background: #f1f5f9;
                color: #0f172a;
                padding: 0.15rem 0.35rem;
                border-radius: 6px;
                font-size: 0.95em;
            }
            .marked pre code {
                background: transparent;
                color: inherit;
                padding: 0;
                border-radius: 0;
            }
            .marked .mermaid-container {
                position: relative;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                background: #ffffff;
                padding: 8px;
                margin: 16px 0;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
            }
            .marked .mermaid-wrapper {
                min-height: 260px;
                max-height: 70vh;
                overflow: hidden;
                position: relative;
            }
            .marked .mermaid-wrapper svg {
                display: block;
                width: 100%;
                height: auto;
                pointer-events: none;
            }
            .marked .mermaid-controls {
                position: absolute;
                top: 8px;
                right: 8px;
                display: inline-flex;
                gap: 6px;
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #e2e8f0;
                border-radius: 999px;
                padding: 4px 6px;
                z-index: 10;
            }
            .marked .mermaid-controls button {
                border: 0;
                background: transparent;
                color: #475569;
                font-size: 12px;
                line-height: 1;
                padding: 4px 6px;
                border-radius: 999px;
                cursor: pointer;
            }
            .marked .mermaid-controls button:hover {
                background: #f1f5f9;
                color: #0f172a;
            }
            .marked ul,
            .marked ol {
                margin: 12px 0;
                padding-left: 1.25rem;
            }
            .marked hr {
                border: 0;
                border-top: 1px solid #e2e8f0;
                margin: 20px 0;
            }
            .copy-btn {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                width: 24px;
                height: 24px;
                padding: 0;
                color: #94a3b8;
            }
            .copy-btn:hover {
                color: #475569;
            }
            .copy-chat-btn {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 4px 10px;
                color: #475569;
                gap: 6px;
                display: inline-flex;
                align-items: center;
            }
            .copy-chat-btn:hover {
                color: #1f2937;
            }
            .copy-chat-btn svg {
                width: 14px;
                height: 14px;
            }
            .copy-btn svg {
                width: 12px;
                height: 12px;
            }
            .copy-btn[data-copied="true"] {
                color: #16a34a;
                border-color: #86efac;
                background: #f0fdf4;
            }
            .copy-btn .copy-label {
                display: none;
            }
            .copy-chat-btn[data-copied="true"] {
                color: #16a34a;
                border-color: #86efac;
                background: #f0fdf4;
            }
            """
        )
    )
    headers.append(
        Script(
            """
            document.documentElement.classList.remove('dark');
            document.addEventListener('click', async (event) => {
              const btn = event.target.closest('.copy-btn');
              if (!btn) return;
              const targetId = btn.getAttribute('data-copy-target');
              if (!targetId) return;
              const el = document.getElementById(targetId);
              if (!el) return;
              const text = el.getAttribute('data-raw') || el.innerText;
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
              const input = document.getElementById('chat-data');
              if (!input) return;
              const text = input.value || '[]';
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
            """,
            type="module",
        )
    )
    return headers


def register_routes(
    app,
    responder=None,
    responder_factory=None,
    tag_line: str = "STREAMING DEMO",
    title: str = "Minimal Stream Chat",
    subtitle: str = "One question, one answer card. Response streams character-by-character.",
    base_path: str = "",
    inject_headers: bool = False,
    include_markdown: bool = True,
    tag_line_href: str = "",
):
    if responder_factory is None and responder is not None and hasattr(responder, "message_history"):
        raise ValueError(
            "Responder appears to be stateful (has message_history). "
            "Pass responder_factory to create a fresh responder per connection."
        )
    if base_path and not base_path.startswith("/"):
        base_path = f"/{base_path}"
    chat_path = f"{base_path}/" if base_path else "/"
    ws_path = f"{base_path}/ws" if base_path else "/ws"

    if inject_headers:
        for header in get_core_headers(include_markdown=include_markdown):
            app.hdrs = (*app.hdrs, header)

    if responder_factory is None:
        responder = responder or EchoResponder()
    sessions = {}

    @app.route(chat_path)
    def home():
        tag_line_node = (
            A(
                tag_line,
                href=tag_line_href,
                cls="text-xs uppercase tracking-widest text-slate-500 hover:text-slate-700",
            )
            if tag_line_href
            else P(tag_line, cls="text-xs uppercase tracking-widest text-slate-500")
        )
        return (
            Title(title),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Body(
                Container(
                    Div(
                        Div(
                            tag_line_node,
                            H1(title, cls="text-3xl md:text-4xl font-semibold text-slate-900"),
                            P(subtitle, cls=TextPresets.muted_sm),
                            cls="space-y-2",
                        ),
                        Div(
                            Button(
                                UkIcon("copy"),
                                Span("Copy conversation as JSON", cls="text-xs font-medium"),
                                cls="uk-button uk-button-text copy-chat-btn",
                                type="button",
                                aria_label="Copy conversation as JSON",
                                title="Copy conversation as JSON",
                            ),
                            cls="flex justify-end",
                        ),
                        Div(
                            Div(render_cards([])),
                            Form(
                                render_input(),
                                Button("Send", cls=ButtonT.primary, type="submit"),
                                id="form",
                                hx_ext="ws",
                                ws_connect=ws_path,
                                ws_send=True,
                                cls="flex flex-col sm:flex-row gap-3 items-stretch pt-4",
                            ),
                            cls="chat-panel space-y-4",
                        ),
                        cls="space-y-6",
                    ),
                    cls=(ContainerT.lg, "py-10"),
                ),
                cls="min-h-screen bg-slate-50 text-slate-900",
            ),
        )

    def _on_connect(ws, send):
        ws_id = id(ws)
        sessions[ws_id] = {
            "cards": [],
            "responder": responder_factory() if responder_factory else responder,
        }

    def _on_disconnect(ws):
        sessions.pop(id(ws), None)

    @app.ws(ws_path, conn=_on_connect, disconn=_on_disconnect)
    async def ws_handler(msg: str, send, ws):
        ws_id = id(ws)
        session = sessions.get(ws_id)
        if session is None:
            session = {
                "cards": [],
                "responder": responder_factory() if responder_factory else responder,
            }
            sessions[ws_id] = session
        cards = session["cards"]
        session_responder = session["responder"]

        cards.append({"id": str(len(cards)), "question": msg, "answer": ""})
        await send(render_cards(cards))

        result = session_responder(msg)
        if inspect.isasyncgen(result):
            async for chunk in result:
                cards[-1]["answer"] += str(chunk)
                await send(render_cards(cards))
        else:
            if inspect.isawaitable(result):
                result = await result
            for ch in str(result):
                cards[-1]["answer"] += ch
                await send(render_cards(cards))

        await send(render_input())


def main(
    responder=None,
    responder_factory=None,
    tag_line: str = "STREAMING DEMO",
    title: str = "Minimal Stream Chat",
    subtitle: str = "One question, one answer card. Response streams character-by-character.",
    include_markdown: bool = True,
    tag_line_href: str = "",
):
    if responder is None:
        responder = EchoResponder()
    headers = get_core_headers(include_markdown=include_markdown)
    app = MUFastHTML(exts="ws", hdrs=tuple(headers), pico=False)
    register_routes(
        app,
        responder=responder,
        responder_factory=responder_factory,
        tag_line=tag_line,
        title=title,
        subtitle=subtitle,
        tag_line_href=tag_line_href,
        base_path="",
    )
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("pylogue.core:main", host="0.0.0.0", port=5001, reload=True, factory=True)
