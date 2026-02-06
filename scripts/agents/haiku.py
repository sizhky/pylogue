from pydantic_ai import Agent
from pylogue.core import main as create_core_app
import logfire
from pylogue.integrations.pydantic_ai import PydanticAIResponder

logfire.configure()
logfire.instrument_pydantic_ai()

instructions = f"""
You only talk in haikus
"""

agent = Agent(
    "openai:gpt-5-mini",
    # "google-gla:gemini-3-flash-preview",
    instructions=instructions,
)
deps = None

def app_factory():
    return create_core_app(
        responder_factory=lambda: PydanticAIResponder(
            agent=agent,
            agent_deps=deps,
            show_tool_details=False,
        ),
        tag_line="Divami AI",
        tag_line_href="https://ai.divami.com",
        title="Haiku Assistant",
        subtitle="You only talk in haikus",
    )
