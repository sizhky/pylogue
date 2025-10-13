# fasthtml solveit
from pylogue.chatapp import create_default_chat_app
import logfire
from pydantic_ai import Agent

logfire.configure(token="your-token-here")
logfire.instrument_pydantic_ai()

agent = Agent(
    "google-gla:gemini-2.5-flash",
    system_prompt="You are a stoic and usually talk as less as possible.",
)


class PydanticAIStreamingResponder:
    """Streaming responder using Pydantic AI's run_stream."""

    def __init__(self, agent=None, agent_deps=None):
        self.agent = agent if agent is not None else self.init_agent()
        self.agent_deps = agent_deps
        self.message_history = None

    async def __call__(self, text: str, context=None):
        """
        Stream tokens from Pydantic AI agent.
        This is an async generator that yields tokens as they arrive.
        """
        import asyncio

        # Use run_stream to get streaming responses
        async with self.agent.run_stream(
            text,
            message_history=self.message_history,
            deps=self.agent_deps,
        ) as response:
            # Stream text deltas (only new tokens)
            token_count = 0
            async for token in response.stream_text(delta=True):
                token_count += 1
                print(f"🔹 Token #{token_count}: {repr(token)}")  # Debug
                yield token
                await asyncio.sleep(0.1)  # Delay AFTER yield to see effect

            # After streaming is complete, save message history for context
            self.message_history = response.all_messages()


class PydanticAIAgentResponder:
    """Non-streaming responder (fallback for non-streaming support)."""

    def __init__(self, agent=None, agent_deps=None):
        self.agent = agent if agent is not None else self.init_agent()
        self.agent_deps = agent_deps
        self.message_history = None

    async def __call__(self, text: str, context=None) -> str:
        response = await self.agent.run(
            text,
            message_history=self.message_history,
            deps=self.agent_deps,
        )
        self.message_history = response.all_messages()
        return response.output


if __name__ == "__main__":
    # Create streaming responder
    responder = PydanticAIStreamingResponder(agent=agent)

    # Create chat app with streaming support
    app = create_default_chat_app(responder=responder)
    print("✅ Pydantic AI Streaming Chat ready!")
    print("💬 Try asking questions and watch responses stream in real-time!")
    app.run(port=5001)
