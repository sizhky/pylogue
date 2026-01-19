# fasthtml solveit
from pylogue.core import main as create_core_app
from dotenv import load_dotenv
import logfire
from pydantic_ai import Agent

load_dotenv(override=True)

logfire.configure(
    environment="development",
    service_name="kitchen-helper-bot",
)
logfire.instrument_pydantic_ai()

system_prompt = """
You talk only as much as needed and not a word more.
"""

kitchen_helper_agent = Agent(
    "openai:gpt-4-mini",
    system_prompt=system_prompt,
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
                await asyncio.sleep(1)  # Delay AFTER yield to see effect

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
    # Create responder compatible with core app (async generator)
    responder = PydanticAIStreamingResponder(agent=kitchen_helper_agent)

    # Create core app (streams chars from returned response)
    app = create_core_app(responder=responder)
    print("✅ Pydantic AI Chat ready!")
    print("💬 Try asking questions and watch responses stream in real-time!")
    print("🔗 Chat endpoint: http://localhost:5001/")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=False)
