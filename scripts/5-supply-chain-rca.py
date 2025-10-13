"""Example 5: Supply Chain RCA Assistant - Full custom DI with specialized components."""

import asyncio
from pylogue.chatapp import ChatApp, ChatAppConfig
from pylogue.session import InMemorySessionManager, Message, ChatSession
from pylogue.service import ChatService
from pylogue.renderer import ChatRenderer
from pylogue.cards import ChatCard


class SupplyChainResponder:
    """Specialized responder for supply chain queries."""

    def __init__(self):
        self.knowledge = {
            "inventory": "📦 Inventory management tracks stock levels and movements.",
            "logistics": "🚚 Logistics coordinates transportation and delivery.",
            "demand": "📊 Demand forecasting predicts future needs.",
            "supplier": "🏭 Supplier management ensures reliable sourcing.",
            "rca": "🔍 Root Cause Analysis identifies problem origins.",
        }

    async def __call__(self, message: str, context=None) -> str:
        await asyncio.sleep(0.3)

        msg_lower = message.lower()

        # Check for known topics
        for topic, info in self.knowledge.items():
            if topic in msg_lower:
                return f"{info}\n\nWould you like to know more about {topic}?"

        # Default response with context
        if context and len(context) > 0:
            return f"📋 Analyzing: {message}\n\nBased on our conversation history, I'm tracking your supply chain queries."

        return f"🔍 Let me analyze: {message}\n\nAsk me about: inventory, logistics, demand, suppliers, or RCA."


def supply_chain_initial():
    """Custom initial messages for supply chain assistant."""
    return [
        Message(
            role="Assistant",
            content="👋 Welcome to Supply Chain RCA Assistant!\n\nI can help you with:\n- 📦 Inventory issues\n- 🚚 Logistics problems\n- 📊 Demand analysis\n- 🏭 Supplier concerns\n\nWhat would you like to analyze?",
        )
    ]


if __name__ == "__main__":
    # Create with full DI
    supply_chain_app = ChatApp(
        session_manager=InMemorySessionManager(),
        chat_service=ChatService(
            responder=SupplyChainResponder(),
            context_provider=lambda s: s.get_messages(),
        ),
        renderer=ChatRenderer(
            card=ChatCard(
                user_color="#1a3a1a",
                assistant_color="#1a1a3a",
                user_emoji="👤",
                assistant_emoji="🔍",
                width="75%",
            ),
            input_placeholder="Describe your supply chain issue...",
        ),
        config=ChatAppConfig(
            app_title="Supply Chain RCA Assistant",
            page_title="Supply Chain Analysis",
            bg_color="#0d1117",
            initial_messages_factory=supply_chain_initial,
        ),
    )

    print("✅ Supply chain assistant ready!")
    supply_chain_app.run(port=5001)
