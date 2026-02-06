# Pydantic AI integration for Pylogue
import asyncio
import copy
import html
import json
import re
from typing import Any, Optional

_TOOL_HTML_RE = re.compile(r'<div class="tool-html">.*?</div>', re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def _sanitize_history_answer(answer: str) -> str:
    if not isinstance(answer, str) or not answer:
        return ""
    text = _TOOL_HTML_RE.sub("Rendered tool output.", answer)
    text = _TAG_RE.sub("", text)
    return html.unescape(text).strip()


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


def _truncate(text: str, limit: int = 100) -> str:
    if not isinstance(text, str):
        return ""
    return text if len(text) <= limit else f"{text[:limit//2]} ... (truncated) ... {text[-limit//2:]}"


def _get_tool_call_id(part):
    return getattr(part, "tool_call_id", None) or getattr(part, "call_id", None)


def _unwrap_tool_return(part_or_result, messages_module):
    if isinstance(part_or_result, messages_module.BaseToolReturnPart):
        return (
            part_or_result.tool_name,
            part_or_result.content,
            part_or_result.tool_call_id,
        )
    return None


def _extract_tool_result(event, messages_module):
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
    unwrapped = _unwrap_tool_return(result, messages_module)
    if unwrapped is not None:
        tool_name = tool_name or unwrapped[0]
        result = unwrapped[1]
        call_id = call_id or unwrapped[2]
    return tool_name, result, call_id


def _format_tool_result_summary(tool_name: str, args, result):
    tool_label = html.escape(tool_name or "tool")
    safe_args = html.escape(_safe_json(args))
    safe_result = html.escape(_truncate(_safe_json(result)))
    return (
        "\n\n"
        f'<details class="tool-call"><summary>Tool: {tool_label}</summary>'
        f"<div><strong>Args</strong></div>"
        f"<pre><code>{safe_args}</code></pre>"
        f"<div><strong>Result</strong></div>"
        f"<pre><code>{safe_result}</code></pre></details>\n\n"
    )


def _safe_dom_id(value: str | None) -> str:
    if not value:
        return "tool-status"
    safe = []
    for ch in str(value):
        if ch.isalnum() or ch in {"-", "_"}:
            safe.append(ch)
    return "".join(safe) or "tool-status"


def _format_tool_status_running(tool_name: str, args, call_id: str | None):
    purpose = None
    if isinstance(args, dict):
        purpose = args.get("purpose")
    label = purpose or (tool_name.replace("_", " ").title() if tool_name else "Working")
    status_id = _safe_dom_id(f"tool-status-{call_id or ''}")
    safe_label = html.escape(str(label))
    return (
        f'<div id="{status_id}" class="tool-status tool-status--running">{safe_label}</div><br />\n\n'
    )


def _format_tool_status_done(args, call_id: str | None):
    if isinstance(args, dict):
        purpose = args.get("purpose")
        if isinstance(purpose, str) and purpose.strip():
            safe_label = purpose.strip()
        else:
            safe_label = "Completed"
    else:
        safe_label = "Completed"
    status_id = _safe_dom_id(f"tool-status-{call_id or ''}")
    safe_label_escaped = html.escape(safe_label)
    return (
        f'<div class="tool-status-update" data-target-id="{status_id}">'
        f"{safe_label_escaped}</div><br />\n\n"
    )


def _resolve_tool_html(result):
    if isinstance(result, dict) and "_pylogue_html_id" in result:
        token = result.get("_pylogue_html_id")
        try:
            from pylogue.embeds import take_html
        except Exception:
            return None
        return take_html(token)
    return None


def _should_render_tool_result_raw(tool_name: str | None, result) -> bool:
    if not isinstance(result, str):
        return False
    stripped = result.lstrip()
    if not stripped.startswith("<"):
        return False
    # Allow raw HTML for tool results (e.g., chart renderers).
    return True


def _wrap_tool_html(result: str) -> str:
    stripped = result.strip()
    if stripped.startswith("<div") and stripped.endswith("</div>"):
        return result
    return f'<div class="tool-html">{result}</div>'


def _merge_user_into_deps(base_deps, context):
    user = context.get("user") if isinstance(context, dict) else None
    if not isinstance(user, dict):
        return base_deps

    # No baseline deps configured: pass a lightweight mapping as deps.
    if base_deps is None:
        return {"pylogue_user": user}

    # Common case for dict-based deps.
    if isinstance(base_deps, dict):
        merged = dict(base_deps)
        merged["pylogue_user"] = user
        return merged

    # Try to preserve existing deps type while attaching user context.
    try:
        merged = copy.copy(base_deps)
    except Exception:
        merged = base_deps
    try:
        setattr(merged, "pylogue_user", user)
        return merged
    except Exception:
        return base_deps


class PydanticAIResponder:
    """Streaming responder using Pydantic AI's run_stream_events."""
    pylogue_instructions = (
        "You are also a helpful AI assistant integrated with Pylogue enviroment."
        "The enviroment supports auto injection of html, i.e., if you respond with raw HTML it will be rendered as HTML."
        "The environment also supports markdown rendering, so you can use markdown syntax for formatting."
        "Finally the environment supports mermaid diagrams, so you can create diagrams using mermaid syntax. with ```mermaid ... ``` blocks."
        "Always generate (block appropriate) css based colorful mermaid diagrams (e.g., classDef evaporation fill:#add8e6,stroke:#333,stroke-width:2px) when appropriate to illustrate concepts."
        "also ensure in mermaid blocks you wrap the text with double quotes to avoid syntax errors, and <br> for line breaks instead of \\n"
        "prefer vertical layouts for flowcharts and sequence diagrams. "
        "Render math using LaTeX syntax within $$ ... $$ blocks or inline with $ ... $."
        "when embedding HTML do not wrap it inside ```html ... ``` blocks, just output the raw HTML directly. Do not add <html> or <body> tags."
        "Just because you can respond with HTML or generate mermaid diagrams does not mean you should always do that. Apart from accuracy of response, your next biggest goals is to save as many tokens as possible while ensuring the response is clear and complete.")

    def __init__(
        self,
        agent: Any,
        agent_deps: Optional[Any] = None,
        show_tool_details: bool = True,
    ):
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
        self.show_tool_details = show_tool_details
        
        # Register dynamic system prompt function once per agent
        if not getattr(agent, "_pylogue_prompt_registered", False):
            @self.agent.system_prompt
            def custom_instructions() -> str:
                return self._compose_system_prompt()

            agent._pylogue_prompt_registered = True

    def append_instructions(self, additional_instructions: str) -> None:
        """Append additional instructions to the agent's system prompt."""
        if additional_instructions:
            self._prompt_state["additional"].append(additional_instructions)

    def _compose_system_prompt(self) -> str:
        segments = []
        if self._prompt_state.get("base_prompt"):
            segments.append(self._prompt_state["base_prompt"])
        segments.append(self.pylogue_instructions)
        if self._prompt_state["additional"]:
            segments.extend(self._prompt_state["additional"])
        return "\n\n".join(segments)

    def get_export_state(self) -> dict:
        """Return exportable system instruction state."""
        return {
            "prompt_state": {
                "base_prompt": self._prompt_state.get("base_prompt", ""),
                "additional": list(self._prompt_state.get("additional", [])),
            },
            "system_prompt": self._compose_system_prompt(),
        }

    def load_state(self, meta: dict) -> None:
        """Restore system instruction state from exported metadata."""
        if not isinstance(meta, dict):
            return
        prompt_state = meta.get("prompt_state") if isinstance(meta.get("prompt_state"), dict) else {}
        if "base_prompt" in prompt_state:
            self._prompt_state["base_prompt"] = prompt_state.get("base_prompt") or ""
        if "additional" in prompt_state and isinstance(prompt_state.get("additional"), list):
            self._prompt_state["additional"] = list(prompt_state.get("additional", []))
        elif isinstance(meta.get("system_prompt"), str):
            self._prompt_state["additional"] = [meta["system_prompt"]]

    def load_history(self, cards) -> None:
        """Load conversation history from Pylogue cards."""
        try:
            from pydantic_ai import messages as pai_messages
        except Exception:
            return
        history = []
        system_prompt = self._compose_system_prompt()
        if system_prompt:
            history.append(
                pai_messages.ModelRequest(
                    parts=[pai_messages.SystemPromptPart(content=system_prompt)]
                )
            )
        for card in cards or []:
            question = card.get("question")
            answer = card.get("answer")
            if question is not None:
                history.append(
                    pai_messages.ModelRequest(
                        parts=[pai_messages.UserPromptPart(content=str(question))]
                    )
                )
            answer_text = card.get("answer_text") if isinstance(card, dict) else None
            if answer_text is None:
                answer_text = answer
            answer_text = _sanitize_history_answer(answer_text)
            if answer_text:
                history.append(
                    pai_messages.ModelResponse(
                        parts=[pai_messages.TextPart(content=str(answer_text))]
                    )
                )
        self.message_history = history
    
    async def __call__(self, text: str, context=None):
        from pydantic_ai import messages
        from pydantic_ai.run import AgentRunResultEvent

        pending_tool_calls = {}
        tool_call_counter = 0

        run_deps = _merge_user_into_deps(self.agent_deps, context)

        async for event in self.agent.run_stream_events(
            text,
            message_history=self.message_history,
            deps=run_deps,
        ):
            kind = getattr(event, "event_kind", "")

            if kind == "part_start" and isinstance(event.part, messages.TextPart):
                if event.part.content:
                    yield event.part.content
                continue

            if kind == "part_delta" and isinstance(event.delta, messages.TextPartDelta):
                if event.delta.content_delta:
                    yield event.delta.content_delta
                continue

            if kind == "function_tool_call":
                part = event.part
                tool_call_counter += 1
                call_id = _get_tool_call_id(part) or f"tool-{tool_call_counter}"
                pending_tool_calls[call_id] = (part.tool_name, part.args)
                if not self.show_tool_details:
                    yield _format_tool_status_running(part.tool_name, part.args, call_id)
                await asyncio.sleep(0)
                continue

            if kind == "builtin_tool_call":
                part = event.part
                tool_call_counter += 1
                call_id = _get_tool_call_id(part) or f"tool-{tool_call_counter}"
                pending_tool_calls[call_id] = (part.tool_name, part.args)
                if not self.show_tool_details:
                    yield _format_tool_status_running(part.tool_name, part.args, call_id)
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
                tool_name, result, call_id = _extract_tool_result(event, messages)
                if call_id in pending_tool_calls:
                    tool_name, args = pending_tool_calls.pop(call_id)
                else:
                    args = None
                if tool_name or args or result:
                    resolved_html = _resolve_tool_html(result)
                    if not self.show_tool_details:
                        yield _format_tool_status_done(args, call_id)
                    if resolved_html:
                        yield _wrap_tool_html(resolved_html)
                    elif _should_render_tool_result_raw(tool_name, result):
                        yield _wrap_tool_html(result)
                    elif self.show_tool_details:
                        yield _format_tool_result_summary(tool_name, args, result)
                await asyncio.sleep(0)
                continue

            if isinstance(event, AgentRunResultEvent):
                self.message_history = event.result.all_messages()
                if pending_tool_calls:
                    for tool_name, args in pending_tool_calls.values():
                        yield _format_tool_result_summary(tool_name, args, None)
