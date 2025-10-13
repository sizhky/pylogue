"""Example 4: Code Assistant - Multi-language code examples with syntax highlighting."""

import asyncio
from pylogue.chatapp import create_default_chat_app, ChatAppConfig
from pylogue.cards import ChatCard


async def code_assistant(message: str, context=None) -> str:
    """Code-focused assistant."""
    await asyncio.sleep(0.5)

    msg_lower = message.lower()

    if "python" in msg_lower:
        return """Here's a Python example:

```python
def hello(name: str) -> str:
    return f"Hello, {name}!"

print(hello("World"))
```
"""
    elif "javascript" in msg_lower or "js" in msg_lower:
        return """Here's a JavaScript example:

```javascript
function hello(name) {
    return `Hello, ${name}!`;
}

console.log(hello("World"));
```
"""
    elif "help" in msg_lower:
        return """I can help with:
- Python code examples
- JavaScript code examples
- General programming questions

Just ask me about a language!
"""
    else:
        return f"💻 You asked: {message}\n\nTry asking about Python or JavaScript!"


if __name__ == "__main__":
    code_app = create_default_chat_app(
        responder=code_assistant,
        config=ChatAppConfig(
            app_title="💻 Code Assistant",
            syntax_highlighting=True,
            highlight_langs=["python", "javascript", "typescript", "html", "css"],
        ),
        card=ChatCard(
            user_color="#1e1e1e",
            assistant_color="#252526",
            user_emoji="👨‍💻",
            assistant_emoji="🤖",
        ),
    )

    print("✅ Code assistant ready!")
    code_app.run(port=5001)
