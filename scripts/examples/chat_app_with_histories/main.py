"""
Chat app wrapper with multiple local histories.
Run: python -m scripts.examples.chat_app_with_histories.main
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

from fasthtml.common import *
from monsterui.all import (
    Button,
    ButtonT,
    Container,
    ContainerT,
    FastHTML as MUFastHTML,
    TextPresets,
    Theme,
    UkIcon,
)

from pylogue.core import (
    EchoResponder,
    IMPORT_PREFIX,
    get_core_headers,
    register_core_static,
    render_assistant_update,
    render_cards,
    render_chat_data,
    render_chat_export,
    render_input,
)
from starlette.responses import FileResponse


def app_factory():
    headers = list(get_core_headers(include_markdown=True))
    headers.extend(
        [
            Link(
                rel="stylesheet",
                href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap",
            ),
            Link(rel="stylesheet", href="/static/chat_app.css"),
            Script(src="/static/chat_app.js", type="module"),
        ]
    )

    app = MUFastHTML(exts="ws", hdrs=tuple(headers), pico=False)
    register_core_static(app)
    app_static_dir = Path(__file__).resolve().parent / "static"

    @app.route("/static/chat_app.css")
    def _chat_app_css():
        return FileResponse(app_static_dir / "chat_app.css")

    @app.route("/static/chat_app.js")
    def _chat_app_js():
        return FileResponse(app_static_dir / "chat_app.js")

    sessions: dict[int, dict] = {}

    def _sidebar():
        return Div(
            Div(
                H1("Pylogue", cls="text-xl font-semibold"),
                Span("Multi-Chat", cls="meta-pill"),
                cls="sidebar-header",
            ),
            Button(
                UkIcon("plus"),
                Span("New chat"),
                cls=(ButtonT.secondary, "w-full justify-center"),
                type="button",
                id="new-chat-btn",
            ),
            Div(id="chat-list", cls="chat-list"),
            P(
                "Chats are stored locally in your browser.",
                cls="text-xs text-slate-500",
            ),
            cls="sidebar",
        )

    def _hero():
        return Div(
            Div(
                P("PYLOGUE WRAPPER", cls="meta-pill"),
                H2("Fast HTML + Pylogue Core", cls="hero-title"),
                P(
                    "One UI wraps multiple Pylogue chat sessions. Pick a chat on the left, "
                    "start a new one, or return to previous conversations instantly.",
                    cls="hero-sub",
                ),
                cls="space-y-2",
            ),
            Div(
                Button(
                    UkIcon("download"),
                    cls="uk-button uk-button-text copy-chat-btn",
                    type="button",
                    aria_label="Download conversation JSON",
                    title="Download conversation JSON",
                ),
                Button(
                    UkIcon("upload"),
                    cls="uk-button uk-button-text copy-chat-btn upload-chat-btn",
                    type="button",
                    aria_label="Upload conversation JSON",
                    title="Upload conversation JSON",
                ),
                Input(
                    type="file",
                    id="chat-upload",
                    accept="application/json",
                    cls="sr-only",
                ),
                cls="flex gap-2 justify-end",
            ),
            cls="hero",
        )

    def _chat_panel():
        return Div(
            Div(render_cards([])),
            Form(
                render_input(),
                Div(
                    Button("Send", cls=ButtonT.primary, type="submit"),
                    P("Cmd/Ctrl+Enter to send", cls="text-xs text-slate-400"),
                    cls="flex flex-col gap-2 items-stretch",
                ),
                id="form",
                hx_ext="ws",
                ws_connect="/ws",
                ws_send=True,
                hx_target="#cards",
                hx_swap="outerHTML",
                cls="flex flex-col sm:flex-row gap-3 items-stretch pt-4",
            ),
            cls="chat-panel space-y-4",
        )

    def _main_panel():
        return Div(
            _hero(),
            _chat_panel(),
            cls="main-panel space-y-6",
        )

    def _shell():
        return Div(
            _sidebar(),
            _main_panel(),
            cls="app-shell",
        )

    @app.route("/")
    def home():
        return (
            Title("Pylogue Multi-Chat"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Body(
                _shell(),
                cls="min-h-screen",
                data_import_prefix=IMPORT_PREFIX,
            ),
        )

    def _on_connect(ws, send):
        ws_id = id(ws)
        sessions[ws_id] = {
            "cards": [],
            "responder": EchoResponder(),
        }

    def _on_disconnect(ws):
        sessions.pop(id(ws), None)

    @app.ws("/ws", conn=_on_connect, disconn=_on_disconnect)
    async def ws_handler(msg: str, send, ws):
        ws_id = id(ws)
        session = sessions.get(ws_id)
        if session is None:
            session = {"cards": [], "responder": EchoResponder()}
            sessions[ws_id] = session
        cards = session["cards"]
        responder = session["responder"]

        if isinstance(msg, str) and msg.startswith(IMPORT_PREFIX):
            payload = msg[len(IMPORT_PREFIX) :].strip()
            try:
                imported = json.loads(payload) if payload else []
            except json.JSONDecodeError:
                imported = []
            meta = None
            if isinstance(imported, dict):
                meta = imported.get("meta")
                imported = imported.get("cards", [])
            normalized = []
            if isinstance(imported, list):
                for item in imported:
                    if not isinstance(item, dict):
                        continue
                    question = item.get("question")
                    answer = item.get("answer")
                    if question is None or answer is None:
                        continue
                    normalized.append(
                        {
                            "id": str(len(normalized)),
                            "question": str(question),
                            "answer": str(answer),
                        }
                    )
            session["cards"] = normalized
            if meta is not None and hasattr(responder, "load_state"):
                try:
                    responder.load_state(meta)
                except Exception:
                    pass
            if hasattr(responder, "load_history"):
                try:
                    responder.load_history(normalized)
                except Exception:
                    pass
            await send(render_cards(normalized))
            await send(render_chat_data(normalized))
            await send(render_chat_export(normalized, responder=responder))
            return

        cards.append({"id": str(len(cards)), "question": msg, "answer": ""})
        await send(render_cards(cards))

        result = responder(msg)
        if inspect.isasyncgen(result):
            async for chunk in result:
                cards[-1]["answer"] += str(chunk)
                await send(render_assistant_update(cards[-1]))
        else:
            if inspect.isawaitable(result):
                result = await result
            for ch in str(result):
                cards[-1]["answer"] += ch
                await send(render_assistant_update(cards[-1]))

        await send(render_chat_data(cards))
        await send(render_chat_export(cards, responder=responder))
        return

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.examples.chat_app_with_histories.main:app_factory",
        host="0.0.0.0",
        port=5010,
        reload=True,
        factory=True,
    )
