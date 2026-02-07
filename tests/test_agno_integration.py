#!/usr/bin/env python

import asyncio
import sys
import types

import pytest

from pylogue.integrations.agno import AgnoResponder, logfire_instrument_agno
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

    assert any("Tool: render_altair_chart_py" in p for p in parts)
    assert any("chart-html" in p for p in parts)


def test_logfire_instrument_agno_requires_write_token(monkeypatch):
    monkeypatch.delenv("LOGFIRE_TOKEN", raising=False)
    monkeypatch.delenv("LOGFIRE_WRITE_TOKEN", raising=False)
    with pytest.raises(ValueError):
        logfire_instrument_agno()


def test_logfire_instrument_agno_wires_otlp_and_instruments(monkeypatch):
    state = {
        "set_provider": None,
        "instrument_called": False,
        "exporter": None,
        "processor": None,
    }

    class _FakeAgnoInstrumentor:
        def instrument(self):
            state["instrument_called"] = True

    class _FakeExporter:
        def __init__(self, endpoint=None, headers=None):
            state["exporter"] = {"endpoint": endpoint, "headers": headers}

    class _FakeProcessor:
        def __init__(self, exporter):
            state["processor"] = {"cls": self.__class__.__name__, "exporter": exporter}

    class _FakeBatchSpanProcessor(_FakeProcessor):
        pass

    class _FakeSimpleSpanProcessor(_FakeProcessor):
        pass

    class _FakeTracerProvider:
        def __init__(self, resource=None):
            self.resource = resource
            self.processors = []

        def add_span_processor(self, processor):
            self.processors.append(processor)

    class _FakeResource:
        @staticmethod
        def create(attrs):
            return {"attrs": attrs}

    trace_module = types.ModuleType("opentelemetry.trace")
    trace_module.set_tracer_provider = lambda provider: state.update(set_provider=provider)
    opentelemetry_module = types.ModuleType("opentelemetry")
    opentelemetry_module.trace = trace_module

    monkeypatch.setitem(sys.modules, "opentelemetry", opentelemetry_module)
    monkeypatch.setitem(sys.modules, "opentelemetry.trace", trace_module)

    exporter_mod = types.ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    exporter_mod.OTLPSpanExporter = _FakeExporter
    monkeypatch.setitem(sys.modules, "opentelemetry.exporter.otlp.proto.http.trace_exporter", exporter_mod)

    resources_mod = types.ModuleType("opentelemetry.sdk.resources")
    resources_mod.Resource = _FakeResource
    monkeypatch.setitem(sys.modules, "opentelemetry.sdk.resources", resources_mod)

    trace_sdk_mod = types.ModuleType("opentelemetry.sdk.trace")
    trace_sdk_mod.TracerProvider = _FakeTracerProvider
    monkeypatch.setitem(sys.modules, "opentelemetry.sdk.trace", trace_sdk_mod)

    export_mod = types.ModuleType("opentelemetry.sdk.trace.export")
    export_mod.BatchSpanProcessor = _FakeBatchSpanProcessor
    export_mod.SimpleSpanProcessor = _FakeSimpleSpanProcessor
    monkeypatch.setitem(sys.modules, "opentelemetry.sdk.trace.export", export_mod)

    openinference_mod = types.ModuleType("openinference")
    openinference_instrumentation_mod = types.ModuleType("openinference.instrumentation")
    openinference_agno_mod = types.ModuleType("openinference.instrumentation.agno")
    openinference_agno_mod.AgnoInstrumentor = _FakeAgnoInstrumentor
    monkeypatch.setitem(sys.modules, "openinference", openinference_mod)
    monkeypatch.setitem(sys.modules, "openinference.instrumentation", openinference_instrumentation_mod)
    monkeypatch.setitem(sys.modules, "openinference.instrumentation.agno", openinference_agno_mod)

    provider = logfire_instrument_agno(write_token="test-token", service_name="test-service")

    assert provider is state["set_provider"]
    assert state["instrument_called"] is True
    assert state["exporter"]["endpoint"] == "https://logfire-us.pydantic.dev/v1/traces"
    assert state["exporter"]["headers"] == {"Authorization": "test-token"}
    assert state["processor"]["cls"] == "_FakeBatchSpanProcessor"
    assert provider.resource == {"attrs": {"service.name": "test-service"}}


def test_logfire_instrument_agno_uses_logfire_token_env(monkeypatch):
    monkeypatch.setenv("LOGFIRE_TOKEN", "env-token")
    monkeypatch.delenv("LOGFIRE_WRITE_TOKEN", raising=False)

    state = {"exporter_headers": None}

    class _FakeAgnoInstrumentor:
        def instrument(self):
            return None

    class _FakeExporter:
        def __init__(self, endpoint=None, headers=None):
            state["exporter_headers"] = headers

    class _FakeProcessor:
        def __init__(self, exporter):
            self.exporter = exporter

    class _FakeTracerProvider:
        def __init__(self, resource=None):
            self.resource = resource

        def add_span_processor(self, processor):
            self.processor = processor

    class _FakeResource:
        @staticmethod
        def create(attrs):
            return {"attrs": attrs}

    trace_module = types.ModuleType("opentelemetry.trace")
    trace_module.set_tracer_provider = lambda provider: None
    opentelemetry_module = types.ModuleType("opentelemetry")
    opentelemetry_module.trace = trace_module

    monkeypatch.setitem(sys.modules, "opentelemetry", opentelemetry_module)
    monkeypatch.setitem(sys.modules, "opentelemetry.trace", trace_module)

    exporter_mod = types.ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    exporter_mod.OTLPSpanExporter = _FakeExporter
    monkeypatch.setitem(sys.modules, "opentelemetry.exporter.otlp.proto.http.trace_exporter", exporter_mod)

    resources_mod = types.ModuleType("opentelemetry.sdk.resources")
    resources_mod.Resource = _FakeResource
    monkeypatch.setitem(sys.modules, "opentelemetry.sdk.resources", resources_mod)

    trace_sdk_mod = types.ModuleType("opentelemetry.sdk.trace")
    trace_sdk_mod.TracerProvider = _FakeTracerProvider
    monkeypatch.setitem(sys.modules, "opentelemetry.sdk.trace", trace_sdk_mod)

    export_mod = types.ModuleType("opentelemetry.sdk.trace.export")
    export_mod.BatchSpanProcessor = _FakeProcessor
    export_mod.SimpleSpanProcessor = _FakeProcessor
    monkeypatch.setitem(sys.modules, "opentelemetry.sdk.trace.export", export_mod)

    openinference_mod = types.ModuleType("openinference")
    openinference_instrumentation_mod = types.ModuleType("openinference.instrumentation")
    openinference_agno_mod = types.ModuleType("openinference.instrumentation.agno")
    openinference_agno_mod.AgnoInstrumentor = _FakeAgnoInstrumentor
    monkeypatch.setitem(sys.modules, "openinference", openinference_mod)
    monkeypatch.setitem(sys.modules, "openinference.instrumentation", openinference_instrumentation_mod)
    monkeypatch.setitem(sys.modules, "openinference.instrumentation.agno", openinference_agno_mod)

    logfire_instrument_agno()

    assert state["exporter_headers"] == {"Authorization": "env-token"}
