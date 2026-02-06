#!/usr/bin/env python

import asyncio

from pylogue.integrations.agno import AgnoResponder
from pylogue.embeds import store_html


class _Chunk:
    def __init__(self, *, event=None, content=None, tools=None, tool=None, messages=None):
        self.event = event
        self.content = content
        self.tools = tools
        self.tool = tool
        self.messages = messages


class _Tool:
    def __init__(self, *, tool_name=None, tool_args=None, result=None, tool_call_id=None):
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.result = result
        self.tool_call_id = tool_call_id


class _FakeAgent:
    def __init__(self):
        self.instructions = "Base instructions"
        self.calls = []

    async def arun(self, run_input, **kwargs):
        self.calls.append((run_input, kwargs))

        async def _stream():
            yield _Chunk(event="RunContent", content="Hel")
            yield _Chunk(event="RunContent", content="Hello")
            yield _Chunk(
                event="ToolCallStarted",
                tools=[{"tool_name": "search_docs", "tool_args": {"purpose": "Lookup"}, "tool_call_id": "tool-1"}],
            )
            yield _Chunk(
                event="ToolCallCompleted",
                tools=[
                    {
                        "tool_name": "search_docs",
                        "tool_args": {"purpose": "Lookup"},
                        "result": {"ok": True},
                        "tool_call_id": "tool-1",
                    }
                ],
            )

        return _stream()


class _FakeAgentDirectStream:
    def __init__(self):
        self.instructions = "Base instructions"
        self.calls = []

    def arun(self, run_input, **kwargs):
        self.calls.append((run_input, kwargs))

        async def _stream():
            yield _Chunk(event="RunContent", content="Hi")
            yield _Chunk(event="RunContent", content="Hi there")

        return _stream()


class _FakeAgentWithSingularToolEvents:
    def __init__(self, tool_result):
        self.instructions = "Base instructions"
        self.calls = []
        self.tool_result = tool_result

    def arun(self, run_input, **kwargs):
        self.calls.append((run_input, kwargs))

        async def _stream():
            yield _Chunk(
                event="ToolCallStarted",
                tool=_Tool(tool_name="render_altair_chart_py", tool_args={"purpose": "chart"}, tool_call_id="tool-7"),
            )
            yield _Chunk(
                event="ToolCallCompleted",
                tool=_Tool(
                    tool_name="render_altair_chart_py",
                    tool_args={"purpose": "chart"},
                    result=self.tool_result,
                    tool_call_id="tool-7",
                ),
            )
            yield _Chunk(event="RunContent", content="Rendered chart.")

        return _stream()


def test_agno_responder_streams_and_tracks_history():
    agent = _FakeAgent()
    responder = AgnoResponder(agent=agent, show_tool_details=False)

    async def _run():
        chunks = []
        async for part in responder("hi", context={"user": {"email": "dev@example.com"}}):
            chunks.append(part)
        return chunks

    parts = asyncio.run(_run())

    assert any(p == "Hel" for p in parts)
    assert any(p == "lo" for p in parts)
    assert any("tool-status--running" in p for p in parts)
    assert any("tool-status-update" in p for p in parts)

    assert len(responder.message_history) >= 2
    assert responder.message_history[-2]["role"] == "user"
    assert responder.message_history[-2]["content"] == "hi"
    assert responder.message_history[-1]["role"] == "assistant"
    assert responder.message_history[-1]["content"] == "Hello"

    assert len(agent.calls) == 1
    _, kwargs = agent.calls[0]
    assert kwargs["stream"] is True
    assert kwargs["stream_events"] is True
    assert kwargs["user_id"] == "dev@example.com"
    assert "pylogue" in kwargs["additional_context"].lower()


def test_agno_responder_accepts_direct_async_stream():
    agent = _FakeAgentDirectStream()
    responder = AgnoResponder(agent=agent, show_tool_details=False)

    async def _run():
        chunks = []
        async for part in responder("hello"):
            chunks.append(part)
        return chunks

    parts = asyncio.run(_run())

    assert parts == ["Hi", " there"]
    assert responder.message_history[-2]["content"] == "hello"
    assert responder.message_history[-1]["content"] == "Hi there"
    assert len(agent.calls) == 1


def test_agno_responder_load_history_sanitizes_html():
    agent = _FakeAgent()
    responder = AgnoResponder(agent=agent)
    responder.load_history(
        [
            {
                "question": "What happened?",
                "answer": '<div class="tool-html"><b>chart</b></div> done',
            }
        ]
    )
    assert responder.message_history[0]["role"] == "user"
    assert responder.message_history[0]["content"] == "What happened?"
    assert responder.message_history[1]["role"] == "assistant"
    assert responder.message_history[1]["content"] == "Rendered tool output. done"


def test_agno_responder_renders_html_from_singular_tool_event():
    token = store_html("<div>chart-html</div>")
    tool_result = f"{{'_pylogue_html_id': '{token}', 'message': 'Chart rendered.'}}"
    agent = _FakeAgentWithSingularToolEvents(tool_result=tool_result)
    responder = AgnoResponder(agent=agent)

    async def _run():
        chunks = []
        async for part in responder("plot"):
            chunks.append(part)
        return chunks

    parts = asyncio.run(_run())

    assert any("chart-html" in p for p in parts)
