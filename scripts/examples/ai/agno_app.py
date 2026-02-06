# fasthtml solveit
from dotenv import load_dotenv
from pylogue.core import main as create_core_app
from pylogue.integrations.agno import AgnoResponder

load_dotenv(override=True)

try:
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "This example requires Agno. Install with: pip install agno"
    ) from exc


agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions=[
        "You talk only as much as needed and not a word more.",
    ],
)


def app_factory():
    return create_core_app(
        responder_factory=lambda: AgnoResponder(agent=agent),
        tag_line="AGNO",
        tag_line_href="/",
        title="Agno Chat",
        subtitle="Streaming tokens and tool events from Agno over WebSockets.",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.examples.ai.agno_app:app_factory",
        host="0.0.0.0",
        port=5003,
        reload=True,
        factory=True,
    )
