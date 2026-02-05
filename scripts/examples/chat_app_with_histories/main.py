from .factory import app_factory
from ...agents.ipl.main import agent as ipl_agent
# from ...agents.salesforce.main import agent as salesforce_agent
from pylogue.integrations.pydantic_ai import PydanticAIResponder

ipl_agent_responder = PydanticAIResponder(agent=ipl_agent)

def _app_factory():
    return app_factory(responder=ipl_agent_responder)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.examples.chat_app_with_histories.main:_app_factory",
        host="0.0.0.0",
        port=5010,
        reload=True,
        factory=True,
    )
