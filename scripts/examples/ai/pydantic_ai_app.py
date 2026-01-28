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

        pending_tool_calls = {}
        tool_call_counter = 0
        buffered_text = []

        def _safe_json(value):
            if value is None:
                return "{}"
            if isinstance(value, str):
                try:
                    return json.dumps(json.loads(value), indent=2, sort_keys=True, ensure_ascii=True)
                except json.JSONDecodeError:
                    return value
            try:
                return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True)
            except TypeError:
                return json.dumps(str(value), indent=2, sort_keys=True, ensure_ascii=True)

        def _get_tool_call_id(part):
            return getattr(part, "tool_call_id", None) or getattr(part, "call_id", None)

        def _extract_tool_result(event):
            part = getattr(event, "part", None)
            if part is not None:
                tool_name = getattr(part, "tool_name", None) or getattr(part, "name", None)
                result = (
                    getattr(part, "content", None)
                    or getattr(part, "result", None)
                    or getattr(part, "return_value", None)
                    or getattr(part, "value", None)
                )
                call_id = _get_tool_call_id(part)
                return tool_name, result, call_id
            result = getattr(event, "result", None)
            tool_name = getattr(event, "tool_name", None)
            call_id = getattr(event, "tool_call_id", None) or getattr(event, "call_id", None)
            return tool_name, result, call_id
            return None, None, None

        def _format_tool_result_summary(tool_name: str, args, result):
            tool_label = html.escape(tool_name or "tool")
            safe_args = html.escape(_safe_json(args))
            safe_result = html.escape(_safe_json(result))
            return (
                "\n\n"
                f'<details class="tool-call"><summary>Tool Call: {tool_label}</summary>'
                f"<div><strong>Args</strong></div>"
                f"<pre><code>{safe_args}</code></pre>"
                f"<div><strong>Result</strong></div>"
                f"<pre><code>{safe_result}</code></pre></details>\n\n"
            )

        async for event in self.agent.run_stream_events(
            text,
            message_history=self.message_history,
            deps=self.agent_deps,
        ):
            kind = getattr(event, "event_kind", "")

            if kind == "part_start" and isinstance(event.part, messages.TextPart):
                if event.part.content:
                    buffered_text.append(event.part.content)
                    await asyncio.sleep(0)
                continue

            if kind == "part_delta" and isinstance(event.delta, messages.TextPartDelta):
                if event.delta.content_delta:
                    buffered_text.append(event.delta.content_delta)
                    await asyncio.sleep(0)
                continue

            if kind == "function_tool_call":
                part = event.part
                tool_call_counter += 1
                call_id = _get_tool_call_id(part) or f"tool-{tool_call_counter}"
                pending_tool_calls[call_id] = (part.tool_name, part.args)
                await asyncio.sleep(0)
                continue

            if kind == "builtin_tool_call":
                part = event.part
                tool_call_counter += 1
                call_id = _get_tool_call_id(part) or f"tool-{tool_call_counter}"
                pending_tool_calls[call_id] = (part.tool_name, part.args)
                await asyncio.sleep(0)
                continue

            if kind in {
                "function_tool_result",
                "builtin_tool_result",
                "tool_result",
                "function_tool_return",
                "builtin_tool_return",
                "tool_return",
            }:
                tool_name, result, call_id = _extract_tool_result(event)
                if call_id in pending_tool_calls:
                    tool_name, args = pending_tool_calls.pop(call_id)
                else:
                    args = None
                if tool_name or args or result:
                    yield _format_tool_result_summary(tool_name, args, result)
                if buffered_text:
                    yield "".join(buffered_text)
                    buffered_text.clear()
                await asyncio.sleep(0)
                continue

            if isinstance(event, AgentRunResultEvent):
                self.message_history = event.result.all_messages()
                if pending_tool_calls:
                    for tool_name, args in pending_tool_calls.values():
                        yield _format_tool_result_summary(tool_name, args, None)
                if buffered_text:
                    yield "".join(buffered_text)
                    buffered_text.clear()

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
        responder_factory=lambda: PydanticAIStreamingResponder(agent=agent, agent_deps=deps),
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
