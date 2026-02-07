from pylogue.shell import app_factory
from pylogue.integrations.agno import AgnoResponder
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from pylogue.dashboarding import render_altair_chart_py

# log to a file
# logger.add("iirm_app.log", rotation="1 MB", level="DEBUG")

agent = Agent(
    name="Agent",
    model=OpenAIResponses(id="gpt-5-nano"),
    system_message="You talk as little as you can.",
    tools=[
        render_altair_chart_py,
    ],
    markdown=True,
)


def _app_factory():
    return app_factory(
        responder_factory=lambda: AgnoResponder(agent=agent),
        hero_title="SQL Agent",
        hero_subtitle="Ask questions about the F1 database and get SQL queries in response.",
        sidebar_title="History"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.examples.ai.agno.iirm_app:_app_factory",
        host="0.0.0.0",
        port=5003,
        reload=True,
        factory=True,
    )
