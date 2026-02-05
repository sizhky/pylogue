# Core FastHTML + MonsterUI chat
from fasthtml.common import *
from monsterui.all import Theme, Container, ContainerT, TextPresets, Button, ButtonT, FastHTML as MUFastHTML, UkIcon
from pathlib import Path
from starlette.responses import FileResponse
import asyncio
import inspect
import json
import base64
import html as html_lib
import re

IMPORT_PREFIX = "__PYLOGUE_IMPORT__:"
_CORE_STATIC_DIR = Path(__file__).resolve().parent / "static"


def register_core_static(app):
    if getattr(app, "_pylogue_static_registered", False):
        return
    app._pylogue_static_registered = True

    @app.route("/static/pylogue-core.css")
    def _pylogue_core_css():
        return FileResponse(_CORE_STATIC_DIR / "pylogue-core.css")

    @app.route("/static/pylogue-core.js")
    def _pylogue_core_js():
        return FileResponse(_CORE_STATIC_DIR / "pylogue-core.js")

    @app.route("/static/pylogue-markdown.js")
    def _pylogue_markdown_js():
        return FileResponse(_CORE_STATIC_DIR / "pylogue-markdown.js")

class EchoResponder:
    async def __call__(self, message: str):
        response = f"ECHO:\n{message}"
        for ch in response:
            await asyncio.sleep(0.005)
            yield ch


def render_input():
    return Textarea(
        id="msg",
        name="msg",
        placeholder="Say hi...",
        autofocus=True,
        rows=3,
        cls="uk-textarea w-full bg-white border-slate-300 focus:border-slate-500 focus:ring-2 focus:ring-slate-200 font-mono",
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
                Div(
                    card["question"],
                    data_raw_b64=base64.b64encode(card["question"].encode("utf-8")).decode("ascii"),
                    cls="marked text-base text-right",
                ),
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
                    data_raw_b64=base64.b64encode((card["answer"] or "").encode("utf-8")).decode("ascii"),
                    cls="marked text-base text-left",
                ),
                cls="chat-row-block chat-row-assistant",
            )
        )
    return Div(
        *rows,
        Div(id="scroll-anchor"),
        Input(type="hidden", id="chat-data", value=data_json),
        Input(type="hidden", id="chat-export", value=json.dumps({"cards": cards})),
        id="cards",
        cls="divide-y divide-slate-200",
    )


def render_chat_data(cards):
    return Input(
        type="hidden",
        id="chat-data",
        value=json.dumps(cards),
        hx_swap_oob="true",
    )

_TOOL_HTML_RE = re.compile(r'<div class="tool-html">.*?</div>', re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def _normalize_answer_for_history(answer: str) -> str:
    if not isinstance(answer, str) or not answer:
        return ""
    text = _TOOL_HTML_RE.sub("Rendered tool output.", answer)
    text = _TAG_RE.sub("", text)
    return html_lib.unescape(text).strip()


def build_export_payload(cards, responder=None):
    export_cards = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        answer = card.get("answer", "")
        answer_text = card.get("answer_text")
        if not isinstance(answer_text, str) or not answer_text.strip():
            answer_text = _normalize_answer_for_history(answer)
        export_card = dict(card)
        export_card["answer_text"] = answer_text
        export_cards.append(export_card)

    payload = {"cards": export_cards}
    if responder is not None and hasattr(responder, "get_export_state"):
        try:
            meta = responder.get_export_state()
        except Exception:
            meta = None
        if meta:
            payload["meta"] = meta
    return payload


def render_chat_export(cards, responder=None):
    payload = build_export_payload(cards, responder=responder)
    return Input(
        type="hidden",
        id="chat-export",
        value=json.dumps(payload),
        hx_swap_oob="true",
    )



def render_assistant_update(card):
    card_id = card.get("id", "")
    assistant_id = f"assistant-{card_id}" if card_id else ""
    return Div(
        card.get("answer", "") or "…",
        id=assistant_id if assistant_id else None,
        data_raw_b64=base64.b64encode((card.get("answer", "") or "").encode("utf-8")).decode("ascii"),
        cls="marked text-base text-left",
        hx_swap_oob="true",
    )


def get_core_headers(include_markdown: bool = True):
    headers = list(Theme.slate.headers())
    if include_markdown:
        headers.extend(
            [
                Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"),
                Link(
                    rel="stylesheet",
                    href="https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@11.9.0/styles/github.min.css",
                ),
                Script(src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"),
                Script(src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"),
                Script(src="https://cdn.jsdelivr.net/npm/vega@5"),
                Script(src="https://cdn.jsdelivr.net/npm/vega-lite@5"),
                Script(src="https://cdn.jsdelivr.net/npm/vega-embed@6"),
            ]
        )
        headers.append(
            Script(src="https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@11.9.0/highlight.min.js")
        )
        headers.append(Script(src="/static/pylogue-markdown.js", type="module"))

    headers.append(Link(rel="stylesheet", href="/static/pylogue-core.css"))
    headers.append(Script(src="/static/pylogue-core.js", type="module"))

    return headers


def register_ws_routes(
    app,
    responder=None,
    responder_factory=None,
    base_path: str = "",
    sessions: dict | None = None,
):
    if responder_factory is None:
        responder = responder or EchoResponder()
    base_path = (base_path or "").strip()
    if base_path in {"", "/"}:
        base_path = ""
    else:
        base_path = "/" + base_path.strip("/")
        if ".." in base_path.split("/"):
            raise ValueError("base_path cannot contain '..'")
    ws_path = f"{base_path}/ws" if base_path else "/ws"
    if sessions is None:
        sessions = {}

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
                if imported and all(isinstance(item, dict) and "role" in item for item in imported):
                    pending_question = None
                    for item in imported:
                        role = item.get("role")
                        content = item.get("content", "")
                        if role == "User":
                            pending_question = content
                        elif role == "Assistant":
                            if pending_question is None:
                                continue
                            normalized.append(
                                {
                                    "id": str(len(normalized)),
                                    "question": pending_question,
                                    "answer": content,
                                }
                            )
                            pending_question = None
                else:
                    for item in imported:
                        if not isinstance(item, dict):
                            continue
                        question = item.get("question")
                        answer = item.get("answer")
                        answer_text = item.get("answer_text")
                        if question is None or answer is None:
                            continue
                        normalized.append(
                            {
                                "id": str(len(normalized)),
                                "question": str(question),
                                "answer": str(answer),
                                "answer_text": str(answer_text) if answer_text is not None else None,
                            }
                        )
            session["cards"] = normalized
            if meta is not None and hasattr(session_responder, "load_state"):
                try:
                    session_responder.load_state(meta)
                except Exception:
                    pass
            if hasattr(session_responder, "load_history"):
                try:
                    session_responder.load_history(normalized)
                except Exception:
                    pass
            await send(render_cards(normalized))
            await send(render_chat_data(normalized))
            await send(render_chat_export(normalized, responder=session_responder))
            return

        cards.append({"id": str(len(cards)), "question": msg, "answer": ""})
        await send(render_cards(cards))

        result = session_responder(msg)
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
        await send(render_chat_export(cards, responder=session_responder))
        return

    return sessions


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
    register_core_static(app)
    if base_path and not base_path.startswith("/"):
        base_path = f"/{base_path}"
    chat_path = f"{base_path}/" if base_path else "/"
    ws_path = f"{base_path}/ws" if base_path else "/ws"

    if inject_headers:
        for header in get_core_headers(include_markdown=include_markdown):
            app.hdrs = (*app.hdrs, header)

    if responder_factory is None:
        responder = responder or EchoResponder()
    register_ws_routes(
        app,
        responder=responder,
        responder_factory=responder_factory,
        base_path=base_path,
    )

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
                            P(subtitle, cls=(TextPresets.muted_sm, "text-slate-600")),
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
                            cls="flex justify-end gap-2",
                        ),
                        Div(
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
                                ws_connect=ws_path,
                                ws_send=True,
                                hx_target="#cards",
                                hx_swap="outerHTML",
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
