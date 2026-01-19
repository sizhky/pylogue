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
    "openai:gpt-4o-mini",
    system_prompt=system_prompt,
)


class PydanticAIStreamingResponder:
    """Streaming responder using Pydantic AI's run_stream."""

    def __init__(self, agent=None, agent_deps=None):
        self.agent = agent if agent is not None else self.init_agent()
        self.agent_deps = agent_deps
        self.message_history = None

    async def __call__(self, text: str, context=None):
        import asyncio

        async with self.agent.run_stream(
            text,
            message_history=self.message_history,
            deps=self.agent_deps,
        ) as response:
            async for token in response.stream_text(delta=True):
                yield token
                await asyncio.sleep(0)

            self.message_history = response.all_messages()


def app_factory():
    responder = PydanticAIStreamingResponder(agent=kitchen_helper_agent)
    return create_core_app(
        responder=responder,
        tag_line="PYDANTIC AI",
        title="Pydantic AI Chat",
        subtitle="Streaming tokens from PydanticAI over WebSockets.",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.examples.ai.pydantic_ai_app:app_factory",
        host="0.0.0.0",
        port=5002,
        reload=True,
        factory=True,
    )
