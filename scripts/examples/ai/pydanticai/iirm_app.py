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

@agent.tool_plain
def render_altair_chart_py(altair_python: str):
    """Render an Altair chart using Python code that defines `chart`.

    Always provided tooltips for interactivity in the chart.

    The code runs with access to: 
    df (pandas DataFrame), alt (Altair), pd (pandas).
    """
    logger.info(f"Rendering Altair chart with provided Python code. {altair_python}")
    import pandas as pd
    import altair as alt
    import base64
    try:
        local_scope = {"alt": alt, "pd": pd}

        try:
            exec(altair_python, local_scope)
        except Exception as exc:  # noqa: BLE001
            return f"Error executing Altair code: {exc}"

        chart = local_scope.get("chart")
        if chart is None or not hasattr(chart, "to_html"):
            return "Error: Altair code must define a `chart` variable."

        try:
            html_content = chart.to_html(embed_options={"actions": False})
        except Exception as exc:  # noqa: BLE001
            return f"Error serializing chart HTML: {exc}"

        iframe_html = (
            f"<iframe src=\"data:text/html;base64,{base64.b64encode(html_content.encode()).decode()}\" "
            f"frameborder=\"0\" style=\"width:100%; height:480px;\"></iframe>"
        )

        html_id = store_html(iframe_html)
        return {"_pylogue_html_id": html_id, "message": "Chart rendered."}
    except Exception as e:
        logger.error(f"Error in render_altair_chart_py: {e}")
        return f"Error in render_altair_chart_py: {e}"


agent = Agent(
    name="Agent",
    model=OpenAIResponses(id="gpt-5-nano"),
    system_message="You talk as little as you can.",
    tools=[
        render_altair_chart_py,
    ],
    markdown=True,
)


def _app_factory():
    return app_factory(
        responder_factory=lambda: AgnoResponder(agent=agent),
        hero_title="SQL Agent",
        hero_subtitle="Ask questions about the F1 database and get SQL queries in response.",
        sidebar_title="History"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.examples.ai.agno.iirm_app:_app_factory",
        host="0.0.0.0",
        port=5003,
        reload=True,
        factory=True,
    )
