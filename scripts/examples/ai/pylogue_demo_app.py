# fasthtml solveit
from pylogue.core import main as create_core_app
from dotenv import load_dotenv
import logfire, os
from pydantic_ai import Agent
from pylogue.integrations.pydantic_ai import PydanticAIResponder

load_dotenv(override=True)

logfire.configure(
    environment="development",
    service_name="kitchen-helper-bot",
)
logfire.instrument_pydantic_ai()

system_prompt = """
You talk only as much as needed and not a word more.
If greeted, talk about your capabilities such as telling time, drawing mermaid charts in the form of "I can do" example bullet points
All your mermaid diagrams should have pastel colors where the colors should be appropriate to the text in the block.
"""

agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt=system_prompt,
)
deps = None

@agent.tool_plain
def time_now(timezone: str = "UTC") -> str:
    """Get the current time in the specified timezone."""
    from datetime import datetime
    import pytz

    tz = pytz.timezone(timezone)
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def app_factory():
    return create_core_app(
        responder_factory=lambda: PydanticAIResponder(agent=agent, agent_deps=deps),
        tag_line="PYDANTIC AI",
        tag_line_href="https://ai.divami.com",
        title="Pydantic AI Chat",
        subtitle="Powerful AI chat with Pydantic-ai Agents. Supports tools, mermaid diagrams, raw html embedding and more.",
    )


if __name__ == "__main__":
    # Run with: python -m scripts.examples.ai.pylogue_demo_app
    import uvicorn

    uvicorn.run(
        "scripts.examples.ai.pydantic_ai_app:app_factory",
        host="0.0.0.0",
        port=5004,
        reload=True,
        factory=True,
    )
