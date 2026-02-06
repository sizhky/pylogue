# fasthtml solveit
import random
from typing import Any

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

from pylogue.shell import app_factory
from pylogue.integrations.pydantic_ai import PydanticAIResponder

load_dotenv(override=True)

logfire.configure(
    environment="development",
    service_name="pylogue-haiku-example",
)
logfire.instrument_pydantic_ai()

instructions = """
You only talk in haikus, 5,7,5 syllable format.
Always use new lines for each line of haiku.
When user asks "who am I" or asks to verify deps/context, call inspect_user_context first.
"""

agent = Agent(
    "google-gla:gemini-3-flash-preview",
    instructions=instructions,
)
deps = None


@agent.tool
def inspect_user_context(ctx: RunContext[Any], purpose: str = "verifying user context"):
    """Inspect runtime deps and return the authenticated user payload from Pylogue."""
    deps_obj = ctx.deps
    if isinstance(deps_obj, dict):
        user = deps_obj.get("pylogue_user")
    else:
        user = getattr(deps_obj, "pylogue_user", None)
    if not isinstance(user, dict):
        return {
            "ok": False,
            "message": "No pylogue_user found in ctx.deps",
            "session_sig": f"haiku-{random.randint(1000, 9999)}",
        }
    return {
        "ok": True,
        "name": user.get("display_name") or user.get("name"),
        "email": user.get("email"),
        "provider": user.get("provider"),
        "session_sig": f"haiku-{random.randint(1000, 9999)}",
    }


def _app_factory():
    return app_factory(
        responder_factory=lambda: PydanticAIResponder(
            agent=agent,
            agent_deps=deps,
            show_tool_details=False,
        ),
        hero_title="Haiku Assistant",
        hero_subtitle="Answers in 5-7-5 haikus with streaming responses.",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.examples.ai.pydanticai.haiku_app:_app_factory",
        host="0.0.0.0",
        port=5004,
        reload=True,
        factory=True,
    )
