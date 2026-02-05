# Pylogue

A FastHTML‑first, streaming chat framework with enough structure to stay polite in production — and enough whimsy to keep the lights on.

**Core promise:** You bring the agent. Pylogue handles the UI, streaming, and chat plumbing.

## What It Is
- **Core runtime** for streaming chat over WebSockets
- **Responder integration** (e.g. Pydantic‑AI) with token streaming
- **Composable UI** helpers for chat cards, input, markdown, and tool status
- **Optional history** storage (local or SQLite via FastSQL)

## Separation of Concerns (The USP)
- **Your business:** build the agent + responder (what it should say).
- **Pylogue’s business:** render the chat UI, stream tokens, and handle the wire protocol.

## Quick Start (Minimal)
```python
from pylogue.core import main

app = main(
    responder=MyResponder(),
    title="My Chat",
    subtitle="Streaming chat with Pylogue",
)
```

## Custom UI + Core WebSocket
Build your own layout but keep core streaming behavior.
```python
from fasthtml.common import *
from pylogue.core import get_core_headers, register_ws_routes, render_cards, render_input

def app_factory():
    app = FastHTML(exts="ws", hdrs=tuple(get_core_headers()), pico=False)
    register_ws_routes(app, responder=MyResponder())

    @app.route("/")
    def home():
        return Body(
            Div(
                Div(render_cards([])),
                Form(
                    render_input(),
                    id="form",
                    hx_ext="ws",
                    ws_connect="/ws",
                    ws_send=True,
                    hx_target="#cards",
                    hx_swap="outerHTML",
                ),
            )
        )

    return app
```

## Multi‑Chat Example (SQLite)
See `scripts/examples/chat_app_with_histories/` for:
- Sidebar history
- Title editing
- Delete with confirmation
- SQLite persistence via FastSQL

Run it:
```bash
python -m scripts.examples.chat_app_with_histories.main
```

## Architecture
- **Flow diagram**: `docs/architecture.md`
- **Integration manual**: `docs/pylogue_integration_manual.md`

## How Streaming Works (Short Version)
- Browser connects to `/ws`.
- Core (`register_ws_routes`) streams chunks as they arrive.
- Responder yields tokens; UI updates incrementally.

## Folder Map
- Core runtime: `src/pylogue/core.py`
- Pydantic‑AI responder: `src/pylogue/integrations/pydantic_ai.py`
- Multi‑chat app: `scripts/examples/chat_app_with_histories/`

## Notes
- If output appears all at once, your responder is not yielding chunks.
- If WS doesn’t connect, check `ws_connect` path and `base_path`.

## Contributing
Professional, pragmatic, and a little whimsical. If you add a feature, add a small example.
