# Pydantic AI integration for Pylogue
import html
import json
from typing import Any, Optional


class PydanticAIResponder:
    """Streaming responder using Pydantic AI's run_stream_events."""
    pylogue_instructions = (
        "You are also a helpful AI assistant integrated with Pylogue enviroment."
        "The enviroment supports auto injection of html, i.e., if you respond with raw HTML it will be rendered as HTML."
        "The environment also supports markdown rendering, so you can use markdown syntax for formatting."
        "Finally the environment supports mermaid diagrams, so you can create diagrams using mermaid syntax. with ```mermaid ... ``` blocks."
        "Always generate (block appropriate) css based colorful mermaid diagrams (e.g., classDef evaporation fill:#add8e6,stroke:#333,stroke-width:2px) when appropriate to illustrate concepts."
        "also ensure in mermaid blocks you wrap the text with double quotes to avoid syntax errors."
        "prefer vertical layouts for flowcharts and sequence diagrams."
    )
    
    def __init__(self, agent: Any, agent_deps: Optional[Any] = None):
        self.agent = agent
        # Preserve any existing system prompt from the agent
        existing_prompt = getattr(agent, 'system_prompt', None) or ""
        base_prompt = existing_prompt if isinstance(existing_prompt, str) else ""
        # Share state on the agent to avoid multiple registrations
        state = getattr(agent, "_pylogue_prompt_state", None)
        if state is None:
            state = {
                "base_prompt": base_prompt,
                "additional": [],
            }
            agent._pylogue_prompt_state = state
        self._prompt_state = state
        self.agent_deps = agent_deps
        self.message_history = None
        
        # Register dynamic system prompt function once per agent
        if not getattr(agent, "_pylogue_prompt_registered", False):
            @self.agent.system_prompt
            def custom_instructions() -> str:
                segments = []
                if self._prompt_state.get("base_prompt"):
                    segments.append(self._prompt_state["base_prompt"])
                segments.append(self.pylogue_instructions)
                if self._prompt_state["additional"]:
                    segments.extend(self._prompt_state["additional"])
                return "\n\n".join(segments)

            agent._pylogue_prompt_registered = True

    def append_instructions(self, additional_instructions: str) -> None:
        """Append additional instructions to the agent's system prompt."""
        if additional_instructions:
            self._prompt_state["additional"].append(additional_instructions)
    
    async def __call__(self, text: str, context=None):
        import asyncio
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

        def _format_tool_result_summary(tool_name: str, args, result):
            tool_label = html.escape(tool_name or "tool")
            safe_args = html.escape(_safe_json(args))
            safe_result = html.escape(_safe_json(result))
            return (
                "\n\n"
                f'<details class="tool-call"><summary>Tool: {tool_label}</summary>'
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
