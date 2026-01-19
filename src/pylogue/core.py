# Core FastHTML + MonsterUI chat
from fasthtml.common import *
from monsterui.all import Theme, Container, ContainerT, TextPresets, Button, ButtonT, FastHTML as MUFastHTML
import asyncio
import inspect


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
    for card in cards:
        rows.append(
            Div(
                P("You", cls=(TextPresets.muted_sm, "text-right")),
                H4(card["question"], cls="text-lg font-semibold text-right"),
                cls="chat-row-block",
            )
        )
        rows.append(
            Div(
                P("Assistant", cls=(TextPresets.muted_sm, "text-left")),
                Div(card["answer"] or "…", cls="text-base text-left"),
                cls="chat-row-block",
            )
        )
    return Div(
        *rows,
        id="cards",
        cls="divide-y divide-slate-200",
    )


def main(responder=None):
    headers = list(Theme.slate.headers())
    headers.append(
        Style(
            """
            html, body { margin: 0; }
            .chat-row-block {
                padding: 14px 0;
            }
            .chat-panel {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                padding: 20px;
            }
            """
        )
    )

    app = MUFastHTML(exts="ws", hdrs=tuple(headers), pico=False)
    responder = responder or EchoResponder()

    sessions = {}

    @app.route("/")
    def home():
        return (
            Title("Minimal Stream Chat"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Body(
                Container(
                    Div(
                        Div(
                            P("STREAMING DEMO", cls="text-xs uppercase tracking-widest text-slate-500"),
                            H1("Minimal Stream Chat", cls="text-3xl md:text-4xl font-semibold text-slate-900"),
                            P("One question, one answer card. Response streams character-by-character.", cls=TextPresets.muted_sm),
                            cls="space-y-2",
                        ),
                        Div(
                            Div(render_cards([])),
                            Form(
                                render_input(),
                                Button("Send", cls=ButtonT.primary, type="submit"),
                                id="form",
                                hx_ext="ws",
                                ws_connect="/ws",
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

    @app.ws("/ws")
    async def ws_handler(msg: str, send, ws):
        ws_id = id(ws)
        cards = sessions.setdefault(ws_id, [])

        cards.append({"question": msg, "answer": ""})
        await send(render_cards(cards))

        result = responder(msg)
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

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("pylogue.core:main", host="0.0.0.0", port=5001, reload=True, factory=True)
