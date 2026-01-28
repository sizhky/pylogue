# fasthtml solveit
from pylogue.core import main as create_core_app
from dotenv import load_dotenv
import logfire
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
"""

if 1:
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

else:
    import sys
    # sys.path.append('/Users/yeshwanth/Code/Divami/client-projects/optinn/anveeksha/src/anveeksha/test_agent_day_0/')
    # from agent import agent
    sys.path.append('/Users/yeshwanth/Code/Divami/client-projects/optinn/anveeksha/src/anveeksha/')
    from ChatSCM2_agent import rca_agent as agent
    from ChatSCM2_agent.deps import Deps
    from ChatSCM2_agent.config import config
    from ChatSCM2_agent.oracle_client import OracleClient

    db = OracleClient(
        user=config.oracle.user,
        password=config.oracle.password,
        host=config.oracle.host,
        port=config.oracle.port,
        service_name=config.oracle.service_name,
    )
    # Initialize dependencies
    deps = Deps(
        db=db,
        owner="SCPOMGR",
        schema_cache={},
    )


def app_factory():
    return create_core_app(
        responder_factory=lambda: PydanticAIResponder(agent=agent, agent_deps=deps),
        tag_line="PYDANTIC AI",
        tag_line_href="/",
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
