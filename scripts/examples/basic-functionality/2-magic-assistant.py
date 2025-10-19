"""Example 2: Custom Styled Chat - Customize colors, emojis, and styling."""

import asyncio
import random
from pylogue.chatapp import create_default_chat_app, ChatAppConfig
from pylogue.cards import ChatCard


async def magic_responder(message: str, context=None) -> str:
    """Mystical responder."""
    await asyncio.sleep(0.4)
    responses = [
        f"🔮 The spirits say: {message.upper()}",
        f"✨ Magic reveals: {message[::-1]}",  # Reversed
        f"🌟 The oracle speaks: {len(message)} mystical symbols detected!",
    ]
    return random.choice(responses)


if __name__ == "__main__":
    # Define custom styling
    custom_card = ChatCard(
        user_color="#2C1810",  # Dark brown
        assistant_color="#1A2332",  # Dark blue
        user_emoji="👨‍💼",
        assistant_emoji="🔮",
        width="70%",
        font_size="1.3em",
        border_radius="1.5em",
    )

    custom_config = ChatAppConfig(
        app_title="✨ Magic Assistant",
        page_title="Magic Chat",
        bg_color="#0f0f23",
    )

    magic_app = create_default_chat_app(
        responder=magic_responder, config=custom_config, card=custom_card
    )

    print("✅ Magic assistant ready!")
    print("🔗 Chat endpoint: http://localhost:5001/chat")
    magic_app.run(port=5001)
