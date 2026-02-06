**Pylogue Integration Manual**
This guide shows how to embed Pylogue’s streaming chat into any FastHTML app, and how to plug it into a larger app ecosystem.

**What You Get**
- A drop-in WebSocket chat endpoint (`/ws`) that streams responses
- A default chat UI or a custom UI layout
- Optional history persistence (localStorage or SQLite via FastSQL)

**Concepts**
- **Core runtime**: `pylogue.core` provides UI helpers and the streaming WS handler.
- **Responder**: an object that receives user messages and yields streamed tokens.
- **FastHTML app**: the web server and router.

**Minimal Integration (Use the Default UI)**
This is the simplest way to add Pylogue to a FastHTML app.

```python
from pylogue.core import main

app = main(
    responder=MyResponder(),
    title="My Chat",
    subtitle="Streaming chat with Pylogue",
)
```

**Custom UI + Core WebSocket**
If you want your own layout (sidebar, custom header, etc.), you only need to keep the WebSocket handler from core and build your own HTML.

```python
from fasthtml.common import *
from pylogue.core import get_core_headers, register_ws_routes, render_cards, render_input

def app_factory():
    app = FastHTML(exts="ws", hdrs=tuple(get_core_headers()), pico=False)

    # Register streaming websocket at /ws
    register_ws_routes(app, responder=MyResponder())

    @app.route("/")
    def home():
        return (
            Title("Custom Chat"),
            Body(
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
            ),
        )

    return app
```

**Responder Basics**
Responders can be synchronous, async, or async generators. Streaming happens when your responder yields chunks.

- **Sync responder**: returns a string (no streaming).
- **Async responder**: returns a string (no streaming).
- **Async generator**: yields chunks (streaming).

If you use `PydanticAIResponder` or `AgnoResponder`, it streams by default.

**History & Persistence**
Pylogue doesn’t enforce history storage. You can choose where to keep it.

- **Client-only**: localStorage in JS (fast, no server storage).
- **Server storage**: SQLite with FastSQL (shared across browsers).

In the chat app with histories, the flow is:
1. JS calls `/api/chats` to list/create chats.
2. JS loads a chat payload and sends it to `/ws` using `__PYLOGUE_IMPORT__`.
3. The WS handler renders cards from that payload.
4. JS saves payload back to `/api/chats/{id}`.

**Recommended Integration Patterns**
- Use `register_ws_routes` for shared streaming behavior.
- Keep layout in your app; keep chat mechanics in core.
- Attach any custom CSS/JS as static assets.
- If you mount the app under a subpath, set `base_path` in `register_ws_routes`.

**Common Pitfalls**
- If messages arrive all at once, your responder is not yielding chunks.
- If WS doesn’t connect, check the `ws_connect` path and base path.
- If chat history doesn’t load, ensure the `__PYLOGUE_IMPORT__` payload is valid JSON.

**Where to Look in This Repo**
- Core runtime: `src/pylogue/core.py`
- Pydantic AI responder: `src/pylogue/integrations/pydantic_ai.py`
- Agno responder: `src/pylogue/integrations/agno.py`
- Multi-history app: `src/pylogue/shell.py`
- JS UI logic: `scripts/examples/chat_app_with_histories/static/chat_app.js`
