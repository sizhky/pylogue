# fasthtml solveit
from pylogue.core import main as create_core_app
from dotenv import load_dotenv
import logfire
from pydantic_ai import Agent

load_dotenv(override=True)

logfire.configure(
    environment="development",
    service_name="kitchen-helper-bot",
)
logfire.instrument_pydantic_ai()

system_prompt = """
You talk only as much as needed and not a word more.
"""

class PydanticAIStreamingResponder:
    """Streaming responder using Pydantic AI's run_stream."""

    def __init__(self, agent=None, agent_deps=None):
        self.agent = agent if agent is not None else Agent(
            "openai:gpt-4o-mini",
            system_prompt=system_prompt,
        )
        self.agent_deps = agent_deps
        self.message_history = None

    async def __call__(self, text: str, context=None):
        import asyncio
        import html
        import json
        from pydantic_ai import messages
        from pydantic_ai.run import AgentRunResultEvent

        def _format_tool_call_summary(tool_name: str, args):
            if args is None:
                pretty_args = "{}"
            elif isinstance(args, str):
                try:
                    pretty_args = json.dumps(json.loads(args), indent=2, sort_keys=True, ensure_ascii=True)
                except json.JSONDecodeError:
                    pretty_args = args
            else:
                pretty_args = json.dumps(args, indent=2, sort_keys=True, ensure_ascii=True)

            tool_label = html.escape(tool_name or "tool")
            safe_args = html.escape(pretty_args)
            return (
                "\n\n"
                f'<details class="tool-call"><summary>Tool call: {tool_label}</summary>'
                f"<pre><code>{safe_args}</code></pre></details>\n\n"
            )

        async for event in self.agent.run_stream_events(
            text,
            message_history=self.message_history,
            deps=self.agent_deps,
        ):
            kind = getattr(event, "event_kind", "")

            if kind == "part_delta" and isinstance(event.delta, messages.TextPartDelta):
                if event.delta.content_delta:
                    yield event.delta.content_delta
                    await asyncio.sleep(0)
                continue

            if kind == "function_tool_call":
                part = event.part
                yield _format_tool_call_summary(part.tool_name, part.args)
                await asyncio.sleep(0)
                continue

            if kind == "builtin_tool_call":
                part = event.part
                yield _format_tool_call_summary(part.tool_name, part.args)
                await asyncio.sleep(0)
                continue

            if isinstance(event, AgentRunResultEvent):
                self.message_history = event.result.all_messages()

agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt=system_prompt,
)

@agent.tool_plain
def time_now(timezone: str = "UTC") -> str:
    """Get the current time in the specified timezone."""
    from datetime import datetime
    import pytz

    tz = pytz.timezone(timezone)
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def app_factory():
    return create_core_app(
        responder_factory=lambda: PydanticAIStreamingResponder(agent=agent),
        tag_line="PYDANTIC AI",
        tag_line_href="https://google.com",
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
