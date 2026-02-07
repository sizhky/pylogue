from pylogue.shell import app_factory
from pylogue.integrations.agno import AgnoResponder, logfire_instrument_agno
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from pylogue.dashboarding import render_altair_chart_py

logfire_instrument_agno()
# log to a file
# logger.add("iirm_app.log", rotation="1 MB", level="DEBUG")

def _render_altair_chart_py(altair_python: str):
    return render_altair_chart_py(sql_query_runner=None, sql_query=None, altair_python=altair_python)

agent = Agent(
    name="Agent",
    model=OpenAIResponses(id="gpt-5-nano"),
    system_message="You talk as little as you can.",
    tools=[
        _render_altair_chart_py,
    ],
    markdown=True,
)


def _app_factory():
    return app_factory(
        responder_factory=lambda: AgnoResponder(agent=agent),
        hero_title="SQL Agent",
        hero_subtitle="Ask questions about the Insurance Database",
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
