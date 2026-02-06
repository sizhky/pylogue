"""
Chat app wrapper with multiple local histories.
Run: python -m scripts.examples.chat_app_with_histories.main
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from fasthtml.common import *
from fastsql import Database
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
    register_ws_routes,
    render_cards,
    render_input,
)
from starlette.requests import Request
from starlette.responses import FileResponse
from starlette.responses import JSONResponse

DB_PATH = Path(__file__).resolve().parent / "chat_app.db"
db = Database(f"sqlite:///{DB_PATH}")


@dataclass
class Chat:
    id: str
    title: str
    created_at: str
    updated_at: str
    payload: str = ""


chats = db.create(Chat, pk="id")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def app_factory(
    responder=None,
    sidebar_title: str = "Pylogue",
    sidebar_tag: str = "Multi-Chat",
    hero_tag: str = "PYLOGUE WRAPPER",
    hero_title: str = "Fast HTML + Pylogue Core",
    hero_subtitle: str = (
        "One UI wraps multiple Pylogue chat sessions. Pick a chat on the left, "
        "start a new one, or return to previous conversations instantly."
    ),
) -> MUFastHTML:
    responder = responder or EchoResponder()
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

    @app.route("/api/chats", methods=["GET"])
    def list_chats():
        items = list(chats())
        items.sort(key=lambda c: c.updated_at or c.created_at, reverse=True)
        return JSONResponse(
            [
                {
                    "id": c.id,
                    "title": c.title,
                    "created_at": c.created_at,
                    "updated_at": c.updated_at,
                }
                for c in items
            ]
        )

    @app.route("/api/chats", methods=["POST"])
    async def create_chat(request: Request):
        data = await request.json()
        chat_id = data.get("id") or str(uuid4())
        title = data.get("title") or "New chat"
        now = _utc_iso()
        payload = data.get("payload")
        payload_str = json.dumps(payload) if payload is not None else ""
        chat = Chat(chat_id, title, now, now, payload_str)
        try:
            _ = chats[chat_id]
            chats.update(chat)
        except Exception:
            chats.insert(chat)
        return JSONResponse(
            {
                "id": chat.id,
                "title": chat.title,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
            }
        )

    @app.route("/api/chats/{chat_id}", methods=["GET"])
    def get_chat(chat_id: str):
        try:
            chat = chats[chat_id]
        except Exception:
            return JSONResponse({"cards": []})
        payload = chat.payload or ""
        if not payload:
            return JSONResponse({"cards": []})
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {"cards": []}
        return JSONResponse(data)

    @app.route("/api/chats/{chat_id}", methods=["POST"])
    async def save_chat(chat_id: str, request: Request):
        data = await request.json()
        payload = data.get("payload") or {"cards": []}
        title = data.get("title") or "New chat"
        now = _utc_iso()
        try:
            existing = chats[chat_id]
            created_at = existing.created_at
        except Exception:
            created_at = data.get("created_at") or now
        chat = Chat(chat_id, title, created_at, now, json.dumps(payload))
        try:
            _ = chats[chat_id]
            chats.update(chat)
        except Exception:
            chats.insert(chat)
        return JSONResponse(
            {
                "id": chat.id,
                "title": chat.title,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
            }
        )

    @app.route("/api/chats/{chat_id}", methods=["DELETE"])
    def delete_chat(chat_id: str):
        try:
            chats.delete(chat_id)
        except Exception:
            pass
        return JSONResponse({"deleted": True})

    sessions: dict[int, dict] = {}
    register_ws_routes(app, responder=responder, sessions=sessions)

    def _sidebar():
        return Div(
            Div(
                H1(sidebar_title, cls="text-xl font-semibold"),
                Span(sidebar_tag, cls="meta-pill"),
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
            cls="sidebar",
        )

    def _hero():
        return Div(
            Div(
                P(hero_tag, cls="meta-pill"),
                H2(hero_title, cls="hero-title"),
                P(hero_subtitle, cls="hero-sub"),
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
                    Button("Send", cls=ButtonT.primary, type="submit", id="chat-send-btn"),
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

    return app
