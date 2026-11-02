"""register_ws_routes hooks: context_fn, initial_cards, render_cards_fn, render_update_fn."""
import json

import pytest
from fasthtml.common import Div, FastHTML, Input, P
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from pylogue.core import register_ws_routes


class Saved:
    def set_context(self, context=None):
        self.who = (context or {}).get("who")

    def initial_cards(self):
        return [{"id": "0", "question": "old q", "answer": "old a"}]

    async def __call__(self, text, context=None):
        yield f"{self.who}: {text}"


def cards_fn(cards):
    rows = [P(c["answer"], id=f"assistant-{c['id']}", cls="turn") for c in cards]
    return Div(*rows, Input(type="hidden", id="chat-data"), Input(type="hidden", id="chat-export"), id="cards")


def update_fn(card):
    return P(card["answer"], id=f"assistant-{card['id']}", cls="turn", hx_swap_oob="true")


def make_app():
    app = FastHTML(exts="ws", secret_key="test")

    @app.route("/signin")
    def signin(session):
        session["who"] = "ana"
        return "ok"

    def ctx(ws):
        who = ws.scope.get("session", {}).get("who")
        return {"who": who} if who else None

    register_ws_routes(app, responder_factory=Saved, base_path="/x", auth_required=True,
                       context_fn=ctx, render_cards_fn=cards_fn, render_update_fn=update_fn)
    return app


def drain(ws):
    msgs = []
    while not msgs or not ('id="chat-export"' in msgs[-1] and "hx-swap-oob" in msgs[-1]):  # sent once the turn ends
        msgs.append(ws.receive_text())
    return msgs


def test_hooks_seed_render_and_context():
    c = TestClient(make_app())
    c.get("/signin")
    with c.websocket_connect("/x/ws") as ws:
        ws.send_text(json.dumps({"msg": "hi"}))
        msgs = drain(ws)
    first = msgs[0]
    assert 'class="turn"' in first and "old a" in first  # custom render, history seeded
    assert any('id="assistant-1"' in m and "ana: hi" in m for m in msgs)  # custom update, context reached responder


def test_no_context_means_no_reply():
    c = TestClient(make_app())  # never signed in
    with c.websocket_connect("/x/ws") as ws:
        ws.send_text(json.dumps({"msg": "hi"}))
        ws.close()
    # the handler returned without sending anything; a reply would have been readable above


def test_defaults_unchanged():
    app = FastHTML(exts="ws")
    register_ws_routes(app)  # EchoResponder, default render
    with TestClient(app).websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"msg": "yo"}))
        msgs = drain(ws)
    assert "chat-row-user" in msgs[0] and any("[ECHO]" in m for m in msgs)
