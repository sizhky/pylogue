# fasthtml solveit
from dotenv import load_dotenv
from pylogue.shell import app_factory
from pylogue.integrations.agno import AgnoResponder
import sys
sys.path.append("/Users/yeshwanth/Code/Personal/agno/cookbook/01_showcase/01_agents/text_to_sql")

load_dotenv(override=True)

from agent import sql_agent

def _app_factory():
    return app_factory(
        responder_factory=lambda: AgnoResponder(agent=sql_agent),
        hero_title="SQL Agent",
        hero_subtitle="Ask questions about the F1 database and get SQL queries in response.",
        sidebar_title="History"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.examples.ai.agno.f1_app:_app_factory",
        host="0.0.0.0",
        port=5003,
        reload=True,
        factory=True,
    )
