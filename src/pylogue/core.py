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
            await asyncio.sleep(0.05)
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
