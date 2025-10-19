"""Example 3: Context-Aware Assistant - Uses conversation history."""

import asyncio
from pylogue.chatapp import create_default_chat_app, ChatAppConfig
from pylogue.session import ChatSession


class SmartResponder:
    """Responder that tracks conversation context."""

    def __init__(self):
        self.keywords = {
            "hello": "👋 Hello! Nice to meet you!",
            "bye": "👋 Goodbye! Have a great day!",
            "help": "💡 I can help you with various tasks. Just ask!",
            "thanks": "😊 You're welcome!",
        }

    async def __call__(self, message: str, context=None) -> str:
        await asyncio.sleep(0.2)

        # Check conversation history
        if context and isinstance(context, list):
            message_count = len(context)

            # Check for keywords
            msg_lower = message.lower()
            for keyword, response in self.keywords.items():
                if keyword in msg_lower:
                    return f"{response}\n\n_We've exchanged {message_count} messages so far._"

        return f"📝 Interesting! You said: '{message}'"


def provide_history(session: ChatSession):
    """Provide message history as context."""
    return session.get_messages()


if __name__ == "__main__":
    smart_app = create_default_chat_app(
        responder=SmartResponder(),
        context_provider=provide_history,
        config=ChatAppConfig(app_title="🧠 Smart Assistant"),
    )

    print("✅ Smart assistant ready!")
    print("🔗 Chat endpoint: http://localhost:5001/chat")
    smart_app.run(port=5001)
