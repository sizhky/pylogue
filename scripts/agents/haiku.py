import random
from typing import Any

from pydantic_ai import Agent, RunContext
from pylogue.core import main as create_core_app
import logfire
from pylogue.integrations.pydantic_ai import PydanticAIResponder

logfire.configure()
logfire.instrument_pydantic_ai()

instructions = f"""
You only talk in haikus, 5,7,5 syllable format. Always use new lines for each line of haiku.
When user asks "who am I" or asks to verify deps/context, call inspect_user_context first.
"""

agent = Agent(
    # "openai:gpt-5-mini",
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
