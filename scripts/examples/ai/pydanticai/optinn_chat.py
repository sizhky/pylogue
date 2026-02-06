# fasthtml solveit
from pylogue.core import main as create_core_app
from dotenv import load_dotenv
import logfire
from pydantic_ai import Agent
from pylogue.integrations.pydantic_ai import PydanticAIResponder

load_dotenv(override=True)

logfire.configure(
    environment="development",
    service_name="optinn_ai_app",
)
logfire.instrument_pydantic_ai()

import sys
sys.path.append('/Users/yeshwanth/Code/Divami/client-projects/optinn/anveeksha/src/anveeksha/')
# sys.path.append('/home/yeshwanth/projects/optinn/anveeksha/src/anveeksha/')
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
        tag_line="OPTINN AI",
        tag_line_href="/",
        title="Chat-SCM",
        subtitle="Perform RCA and Scenario Analysis for SCM issues",
    )


if __name__ == "__main__":
    # run command "python -m scripts.examples.ai.optinn_chat"
    import uvicorn

    uvicorn.run(
        "scripts.examples.ai.optinn_chat:app_factory",
        host="0.0.0.0",
        port=5002,
        reload=True,
        factory=True,
    )
