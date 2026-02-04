import duckdb
import os
import base64
import altair as alt
import altair
import dotenv
import pandas as pd
from pathlib import Path
from pydantic_ai import Agent
from pylogue.core import main as create_core_app
from pylogue.embeds import store_html
import logfire
from pylogue.integrations.pydantic_ai import PydanticAIResponder

dotenv.load_dotenv()
from simple_salesforce import Salesforce

config = dict(
    username=os.environ['SALESFORCE_USERNAME'],
    password=os.environ['SALESFORCE_PASSWORD'],
    security_token=os.environ['SALESFORCE_SECURITY_TOKEN'],
)
sf = Salesforce(**config)

def get_salesforce_tables():
    "Get list of all queryable Salesforce tables"
    tables = [obj['name'] for obj in sf.describe()['sobjects'] if obj['queryable']]
    return tables

logfire.configure()
logfire.instrument_pydantic_ai()

instructions = f"""
System Instruction for Salesforce Query Assistant:

You have access to three tools for interacting with Salesforce data:

get_table_schema(table_name) - Returns schema details for a specific table including field names, types, labels, picklist values, and references
run_salesforce_query(soql_query) - Executes a SOQL query and returns records
Your task: Answer user questions about Salesforce data by intelligently chaining these tools.

Approach:

If the user asks about a specific table's structure or fields, call get_table_schema(table_name)
Before writing a SOQL query, use get_table_schema() to verify field names and types exist
When executing queries, use run_salesforce_query(soql_query) with proper SOQL syntax
Chain tools as needed: e.g., list tables → examine schema → construct query → execute query
Present results clearly, explaining what you found
SOQL syntax reminders:

Use SELECT, FROM, WHERE, ORDER BY, LIMIT
Field references use dot notation for relationships (e.g., Account.Name)
String values need single quotes
No JOIN keyword - use relationship queries instead
Always verify table and field names before querying to avoid errors.

Do not generate mermaid diagrams or dashboards or visualizations unless explicitly requested by the user.
The default response should always be text-based answers.
Do not give technical explanations of Salesforce ever.
Every tool call must include a `purpose` argument that is just max three words of verb-noun kind of a phrase in present tense, e.g., counting records.

available tables: {get_salesforce_tables()}
"""

agent = Agent(
    # "openai:gpt-5-mini",
    "google-gla:gemini-3-flash-preview",
    instructions=instructions,
)
deps = None

DATA_DIR = Path(__file__).resolve().parent

@agent.tool_plain()
def get_table_schema(table_name: str, purpose: str):
    "Get schema details for a specific Salesforce table"
    try:
        table = getattr(sf, table_name)
        fields = table.describe()['fields']
        schema = []
        for f in fields:
            field_info = dict(name=f['name'], type=f['type'], label=f['label'])
            if f['type'] == 'picklist': field_info['values'] = [v['value'] for v in f['picklistValues']]
            if f['type'] == 'reference': field_info['references'] = f['referenceTo']
            schema.append(field_info)
        return schema
    except Exception as e:
        return f"Error retrieving schema for table {table_name}: {e}"

@agent.tool_plain()
def run_salesforce_query(soql_query: str, purpose: str):
    "Execute a SOQL query and return results"
    try:
        result = sf.query(soql_query)
        return result['records']
    except Exception as e:
        return f"Error executing SOQL query: {e}"

def _flatten_record(record: dict, prefix: str = "") -> dict:
    flat = {}
    for key, value in record.items():
        if key == "attributes":
            continue
        full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(value, dict):
            flat.update(_flatten_record(value, full_key))
        else:
            flat[full_key] = value
    return flat


@agent.tool_plain()
def render_altair_chart_py(soql_query: str, altair_python: str, purpose: str):
    """Render an Altair chart using Python code that defines `chart`.

    Always provided tooltips for interactivity in the chart.

    The code runs with access to: results (raw Salesforce records),
    df (pandas DataFrame), alt (Altair), pd (pandas).
    """
    try:
        results = run_salesforce_query(soql_query, purpose="Fetch Salesforce data for the chart.")
        flattened = [_flatten_record(r) for r in results]
        df = pd.DataFrame(flattened)

        safe_builtins = {
            "len": len,
            "min": min,
            "max": max,
            "sum": sum,
            "range": range,
            "list": list,
            "dict": dict,
        }
        safe_globals = {"__builtins__": safe_builtins}
        safe_locals = {"results": results, "df": df, "alt": alt, "pd": pd}

        try:
            exec(altair_python, safe_globals, safe_locals)
        except Exception as exc:  # noqa: BLE001
            return f"Error executing Altair code: {exc}"

        chart = safe_locals.get("chart")
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
        return f"Error in render_altair_chart_py: {e}"

def app_factory():
    return create_core_app(
        responder_factory=lambda: PydanticAIResponder(
            agent=agent,
            agent_deps=deps,
            show_tool_details=False,
        ),
        tag_line="Divami AI",
        tag_line_href="https://ai.divami.com",
        title="Salesforce Query Assistant",
        subtitle="Ask questions about your Salesforce data",
    )


if __name__ == "__main__":
    # Run with: python -m scripts.examples.ai.pylogue_demo_app
    import uvicorn

    uvicorn.run(
        "salesforce-agent:app_factory",
        host="0.0.0.0",
        port=5004,
        reload=True,
        factory=True,
    )
