import duckdb
import json
import base64
import altair as alt
from pathlib import Path
from pydantic_ai import Agent
from pylogue.core import main as create_core_app
import logfire
from pylogue.integrations.pydantic_ai import PydanticAIResponder

logfire.configure()
logfire.instrument_pydantic_ai()

instructions = """
You analyze IPL match data stored in CSV files. 
You can read CSV files, summarize data, and answer questions about IPL matches.
You will talk in less than 200 words at a time. You will not generate tables, diagrams or reasons unless asked.
If the user's question is vague, ask for clarification.
You can also build interactive Altair dashboards by calling the render_altair_chart tool with a SELECT query and an Altair (Vega-Lite) JSON spec. Keep queries small (<2000 rows).
Available tables are registered from local CSVs (e.g., matches, deliveries); query them directly.
"""

agent = Agent(
    # "openai:gpt-5-mini",
    "google-gla:gemini-flash-lite-latest",
    instructions=instructions,
)
deps = None

# Shared DuckDB connection reused across tool calls
DUCKDB_CONN = duckdb.connect()
DATA_DIR = Path(__file__).resolve().parent


def register_csv_views(csv_path: str | None = None):
    """Register CSV files as DuckDB views for convenient querying.

    - If csv_path is provided, only that file is registered.
    - Otherwise, all top-level CSV files alongside this script are registered.
    """

    cur = DUCKDB_CONN.cursor()

    targets = [Path(csv_path)] if csv_path else list(DATA_DIR.glob("*.csv"))

    for csv_file in targets:
        alias = csv_file.stem.replace("-", "_")
        cur.execute(
            f"CREATE OR REPLACE VIEW {alias} AS SELECT * FROM read_csv_auto('{csv_file.as_posix()}')"
        )


# Eagerly register known CSVs on startup so tools can query by table name (e.g., matches, deliveries)
register_csv_views()

@agent.tool_plain()
def read_csv_with_schema(table: str):
    """Show schema + sample for a registered CSV table (avoids sending full data)."""
    register_csv_views()  # ensure views exist
    cur = DUCKDB_CONN.cursor()

    # Sample the first 50 rows instead of loading the whole file
    sample_df = cur.execute(
        f"SELECT * FROM {table} LIMIT 50"
    ).df()

    # Get schema info
    schema_df = cur.execute(
        f"DESCRIBE SELECT * FROM {table}"
    ).df()

    # Count rows without materializing the table
    row_count = cur.execute(
        f"SELECT COUNT(*) AS rows FROM {table}"
    ).fetchone()[0]

    print("Schema:")
    print(schema_df)
    print(f"\nTotal Rows: {row_count}")
    print("\nSample rows:")
    print(sample_df.head())

    return {
        "sample_csv": sample_df.to_csv(index=False),
        "schema_csv": schema_df.to_csv(index=False),
        "row_count": row_count,
    }

@agent.tool_plain()
def execute_sql_on_csv(sql_query: str) -> str:
    """Execute a SELECT against registered CSV tables. Avoid 1000s of rows."""
    register_csv_views()
    cur = DUCKDB_CONN.cursor()

    # allow only select queries
    if any(
        sql_query.strip().lower().startswith(cmd)
        for cmd in ["insert", "update", "delete", "create", "drop", "alter"]
    ):
        return "Error: Only SELECT queries are allowed."
    result_df = cur.execute(sql_query).df()

    print(f"Executed SQL: {sql_query}")
    print(f"Result rows: {len(result_df)}")
    print(result_df.head())

    return result_df.to_csv()


@agent.tool_plain()
def render_altair_chart(sql_query: str, altair_spec_json: str):
    """Run a SELECT on the CSV and render an Altair/Vega-Lite chart spec. Returns iframe HTML.

    - Only SELECT queries are allowed.
    - The result is limited to 2000 rows to keep payloads reasonable.
    - The provided Altair spec must be JSON; data is inlined (no external URLs).
    """

    register_csv_views()
    cur = DUCKDB_CONN.cursor()

    # Enforce SELECT-only
    if not sql_query.strip().lower().startswith("select"):
        return "Error: Only SELECT queries are allowed. Reference registered tables like matches or deliveries."

    # Apply a hard limit to avoid huge HTML
    limited_query = f"SELECT * FROM ({sql_query}) t LIMIT 2000"

    df = cur.execute(limited_query).df()

    try:
        spec = json.loads(altair_spec_json)
    except json.JSONDecodeError as exc:
        return f"Error: altair_spec_json is not valid JSON ({exc})."

    if not isinstance(spec, dict):
        return "Error: altair_spec_json must decode to a JSON object."

    # Inline data to prevent external fetches
    spec["data"] = {"values": df.to_dict(orient="records")}

    try:
        spec_json = json.dumps(spec, ensure_ascii=True)
    except Exception as exc:  # noqa: BLE001
        return f"Error serializing chart spec: {exc}"

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\" />
    <style>
        html, body {{ margin: 0; padding: 0; }}
        #vis {{ width: 100%; height: 600px; }}
    </style>
    <script src=\"https://cdn.jsdelivr.net/npm/vega@5\"></script>
    <script src=\"https://cdn.jsdelivr.net/npm/vega-lite@5\"></script>
    <script src=\"https://cdn.jsdelivr.net/npm/vega-embed@6\"></script>
</head>
<body>
    <div id=\"vis\"></div>
    <script>
        (function() {{
            const spec = {spec_json};
            const opts = {{ actions: false }};
            if (typeof vegaEmbed !== 'function') {{
                const el = document.getElementById('vis');
                if (el) el.innerHTML = '<pre style="color:red;white-space:pre-wrap;">vegaEmbed not available</pre>';
                return;
            }}
            vegaEmbed('#vis', spec, opts).catch((err) => {{
                const el = document.getElementById('vis');
                if (el) el.innerHTML = `<pre style="color:red; white-space:pre-wrap;">${{String(err)}}</pre>`;
                console.error(err);
            }});
        }})();
    </script>
</body>
</html>
"""

    iframe_html = (
        f"<iframe src=\"data:text/html;base64,{base64.b64encode(html_content.encode()).decode()}\" "
        f"frameborder=\"0\" style=\"width:100%; height:600px;\"></iframe>"
    )

    return iframe_html

def app_factory():
    return create_core_app(
        responder_factory=lambda: PydanticAIResponder(agent=agent, agent_deps=deps),
        tag_line="PYDANTIC AI",
        tag_line_href="https://ai.divami.com",
        title="IPL Dashboard with Pydantic-ai Agents",
        subtitle="An example app demonstrating Pydantic-ai integration",
    )


if __name__ == "__main__":
    # Run with: python -m scripts.examples.ai.pylogue_demo_app
    import uvicorn

    uvicorn.run(
        "ipl-dashboard-agent:app_factory",
        host="0.0.0.0",
        port=5004,
        reload=True,
        factory=True,
    )
