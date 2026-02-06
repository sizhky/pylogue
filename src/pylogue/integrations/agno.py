# Agno integration for Pylogue
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


def _safe_dom_id(value: str | None) -> str:
    if not value:
        return "tool-status"
    safe = []
    for ch in str(value):
        if ch.isalnum() or ch in {"-", "_"}:
            safe.append(ch)
    return "".join(safe) or "tool-status"


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
    return True


def _wrap_tool_html(result: str) -> str:
    stripped = result.strip()
    if stripped.startswith("<div") and stripped.endswith("</div>"):
        return result
    return f'<div class="tool-html">{result}</div>'


def _extract_user_from_context(context):
    if not isinstance(context, dict):
        return None
    user = context.get("user")
    return user if isinstance(user, dict) else None


def _normalize_tool_payload(tool_entry: Any) -> tuple[str | None, Any, Any, str | None]:
    if not isinstance(tool_entry, dict):
        return None, None, None, None
    function = tool_entry.get("function")
    if isinstance(function, dict):
        function_name = function.get("name")
        function_args = function.get("arguments")
    else:
        function_name = None
        function_args = None

    tool_name = (
        tool_entry.get("tool_name")
        or tool_entry.get("name")
        or function_name
        or tool_entry.get("tool")
    )
    args = (
        tool_entry.get("tool_args")
        or tool_entry.get("args")
        or tool_entry.get("arguments")
        or function_args
        or tool_entry.get("input")
    )
    result = (
        tool_entry.get("result")
        or tool_entry.get("output")
        or tool_entry.get("content")
        or tool_entry.get("observation")
    )
    call_id = tool_entry.get("tool_call_id") or tool_entry.get("call_id") or tool_entry.get("id")
    return tool_name, args, result, call_id


def _extract_tools(chunk) -> list[tuple[str | None, Any, Any, str | None]]:
    tools = getattr(chunk, "tools", None)
    if isinstance(tools, dict):
        tools = [tools]
    if not isinstance(tools, list):
        return []
    return [_normalize_tool_payload(t) for t in tools]


def _is_event(event_value, expected_name: str) -> bool:
    if event_value is None:
        return False
    event_str = str(event_value)
    return event_str == expected_name or event_str.endswith(f".{expected_name}")


def _message_to_dict(message: Any) -> dict | None:
    if isinstance(message, dict):
        role = message.get("role")
        content = message.get("content")
        if role is None or content is None:
            return None
        return {"role": role, "content": str(content)}
    role = getattr(message, "role", None)
    content = getattr(message, "content", None)
    if role is None or content is None:
        return None
    return {"role": str(role), "content": str(content)}


def _normalize_history_messages(messages: Any) -> list[dict]:
    if not isinstance(messages, list):
        return []
    normalized = []
    for message in messages:
        converted = _message_to_dict(message)
        if converted is not None:
            normalized.append(converted)
    return normalized


class AgnoResponder:
    """Streaming responder using Agno's stream events."""

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
        "Just because you can respond with HTML or generate mermaid diagrams does not mean you should always do that. Apart from accuracy of response, your next biggest goals is to save as many tokens as possible while ensuring the response is clear and complete."
    )

    def __init__(
        self,
        agent: Any,
        show_tool_details: bool = True,
        run_kwargs: Optional[dict[str, Any]] = None,
    ):
        self.agent = agent
        existing_instructions = getattr(agent, "instructions", None)
        if isinstance(existing_instructions, str):
            base_prompt = existing_instructions
        elif isinstance(existing_instructions, (list, tuple)):
            base_prompt = "\n".join(str(p) for p in existing_instructions if p is not None)
        else:
            base_prompt = ""

        state = getattr(agent, "_pylogue_prompt_state", None)
        if state is None:
            state = {
                "base_prompt": base_prompt,
                "additional": [],
            }
            agent._pylogue_prompt_state = state

        self._prompt_state = state
        self.message_history = []
        self.show_tool_details = show_tool_details
        self._active_user = None
        self.run_kwargs = copy.deepcopy(run_kwargs) if isinstance(run_kwargs, dict) else {}

    def append_instructions(self, additional_instructions: str) -> None:
        if additional_instructions:
            self._prompt_state["additional"].append(additional_instructions)

    def _compose_system_prompt(self, user: Optional[dict] = None) -> str:
        segments = []
        if self._prompt_state.get("base_prompt"):
            segments.append(self._prompt_state["base_prompt"])
        segments.append(self.pylogue_instructions)
        if isinstance(user, dict):
            display_name = user.get("display_name") or user.get("name")
            email = user.get("email")
            user_parts = []
            if display_name:
                user_parts.append(f"name={display_name}")
            if email:
                user_parts.append(f"email={email}")
            if user_parts:
                segments.append(
                    "Authenticated user profile (source of truth): "
                    + ", ".join(user_parts)
                    + ". Use this identity when the user asks who they are or asks for personalization."
                )
        if self._prompt_state["additional"]:
            segments.extend(self._prompt_state["additional"])
        return "\n\n".join(segments)

    def get_export_state(self) -> dict:
        return {
            "prompt_state": {
                "base_prompt": self._prompt_state.get("base_prompt", ""),
                "additional": list(self._prompt_state.get("additional", [])),
            },
            "system_prompt": self._compose_system_prompt(),
        }

    def load_state(self, meta: dict) -> None:
        if not isinstance(meta, dict):
            return
        prompt_state = meta.get("prompt_state") if isinstance(meta.get("prompt_state"), dict) else {}
        if "base_prompt" in prompt_state:
            self._prompt_state["base_prompt"] = prompt_state.get("base_prompt") or ""
        if "additional" in prompt_state and isinstance(prompt_state.get("additional"), list):
            self._prompt_state["additional"] = list(prompt_state.get("additional", []))
        elif isinstance(meta.get("system_prompt"), str):
            self._prompt_state["additional"] = [meta["system_prompt"]]

    def load_history(self, cards, context=None) -> None:
        history = []
        for card in cards or []:
            question = card.get("question")
            answer = card.get("answer")
            if question is not None:
                history.append({"role": "user", "content": str(question)})
            answer_text = card.get("answer_text") if isinstance(card, dict) else None
            if answer_text is None:
                answer_text = answer
            answer_text = _sanitize_history_answer(answer_text)
            if answer_text:
                history.append({"role": "assistant", "content": str(answer_text)})
        self.message_history = history
        self.set_context(context)

    def set_context(self, context=None) -> None:
        self._active_user = _extract_user_from_context(context)

    def _build_run_input(self, text: str):
        history = list(self.message_history or [])
        history.append({"role": "user", "content": str(text)})
        return history

    def _build_run_kwargs(self) -> dict[str, Any]:
        kwargs = copy.deepcopy(self.run_kwargs)
        user = self._active_user
        if isinstance(user, dict) and "user_id" not in kwargs:
            user_id = user.get("email") or user.get("display_name") or user.get("name")
            if isinstance(user_id, str) and user_id:
                kwargs["user_id"] = user_id
        return kwargs

    async def __call__(self, text: str, context=None):
        self.set_context(context)
        user = self._active_user
        try:
            run_stream = await self.agent.arun(
                self._build_run_input(text),
                stream=True,
                stream_events=True,
                additional_context=self._compose_system_prompt(user=user),
                **self._build_run_kwargs(),
            )
        except ModuleNotFoundError as exc:
            raise RuntimeError("Agno integration requires the `agno` package. Install it with `pip install agno`.") from exc

        pending_tool_calls: dict[str, tuple[str | None, Any]] = {}
        tool_call_counter = 0
        streamed_text = ""
        history_updated_from_stream = False

        async for chunk in run_stream:
            event = getattr(chunk, "event", None)

            if _is_event(event, "RunResponse"):
                content = getattr(chunk, "content", None)
                if isinstance(content, str) and content:
                    if content.startswith(streamed_text):
                        delta = content[len(streamed_text) :]
                        streamed_text = content
                    else:
                        delta = content
                        streamed_text += content
                    if delta:
                        yield delta
                continue

            if _is_event(event, "ToolCallStarted"):
                for tool_name, args, _, call_id in _extract_tools(chunk):
                    tool_call_counter += 1
                    resolved_call_id = call_id or f"tool-{tool_call_counter}"
                    pending_tool_calls[resolved_call_id] = (tool_name, args)
                    if not self.show_tool_details:
                        yield _format_tool_status_running(tool_name, args, resolved_call_id)
                continue

            if _is_event(event, "ToolCallCompleted"):
                for tool_name, args, result, call_id in _extract_tools(chunk):
                    resolved_call_id = call_id
                    if resolved_call_id in pending_tool_calls:
                        tool_name, args = pending_tool_calls.pop(resolved_call_id)
                    if not self.show_tool_details:
                        yield _format_tool_status_done(args, resolved_call_id)
                    resolved_html = _resolve_tool_html(result)
                    if resolved_html:
                        yield _wrap_tool_html(resolved_html)
                    elif _should_render_tool_result_raw(tool_name, result):
                        yield _wrap_tool_html(result)
                    elif self.show_tool_details and (tool_name or args or result):
                        yield _format_tool_result_summary(tool_name, args, result)
                continue

            content = getattr(chunk, "content", None)
            if isinstance(content, str) and content and _is_event(event, "Reasoning"):
                yield content

            messages = _normalize_history_messages(getattr(chunk, "messages", None))
            if messages:
                self.message_history = messages
                history_updated_from_stream = True

        if pending_tool_calls and self.show_tool_details:
            for tool_name, args in pending_tool_calls.values():
                yield _format_tool_result_summary(tool_name, args, None)

        if not history_updated_from_stream:
            updated_history = list(self.message_history) if isinstance(self.message_history, list) else []
            updated_history.append({"role": "user", "content": str(text)})
            updated_history.append({"role": "assistant", "content": streamed_text})
            self.message_history = updated_history
