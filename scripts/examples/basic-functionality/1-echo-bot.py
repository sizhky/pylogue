"""Example 1: Simple Echo Bot - The simplest possible chat app."""

import asyncio
from pylogue.chatapp import create_default_chat_app


async def echo_bot(message: str, context=None) -> str:
    """Simple echo responder."""
    await asyncio.sleep(0.3)  # Simulate processing
    return f"🔊 You said: {message}"


# Create the app instance at module level for reload support
echo_app = create_default_chat_app(responder=echo_bot)

if __name__ == "__main__":
    echo_app.run(port=5001)
