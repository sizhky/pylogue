import duckdb
import json
import base64
import altair as alt
import pandas as pd
from pathlib import Path
from pydantic_ai import Agent
from pylogue.core import main as create_core_app
from pylogue.embeds import store_html
import logfire
from pylogue.integrations.pydantic_ai import PydanticAIResponder

logfire.configure()
logfire.instrument_pydantic_ai()

instructions = """
You analyze IPL match data stored in CSV files. 
You can read CSV files, summarize data, and answer questions about IPL matches.
When we went to purchase. Watch They made us pay only through Apple Pay. Apple Watch. Only Apple pays a lot. Of last game. But he said Apple figure he started with Apple. Amazon is also like that. No pays Amazon pay, then we'll give you discount. The two tables given are 'matches' and 'deliveries', containing match-level and ball-level data respectively.
Always Use read_csv_with_schema to inspect the structure and sample data of these tables instead of guessing.
Use execute_sql_on_csv to run SQL queries on these tables to extract insights.
Before any complex SQL, call read_csv_with_schema on the relevant tables.
Only use columns that exist in the schema. Never invent aliases or columns.
Start with a LIMIT 5 validation query to confirm column names and joins.
If a column or table is missing, ask for clarification instead of guessing.
Never reference an alias unless it is defined in the FROM clause.
For year-based filters, first query the latest year from the correct table and use it as the default.
If the user's question is vague, ask for clarification.
You can also build interactive Altair dashboards by calling the render_altair_chart tool with a SELECT query and an Altair (Vega-Lite) JSON spec. Keep queries small (<2000 rows).
If the Vega-Lite JSON spec fails, prefer render_altair_chart_py and provide Altair-Python code that defines a `chart` variable using the provided `df` (e.g., `chart = alt.Chart(df)...`).
When using render_altair_chart_py, you may use import statements if needed.
Available tables are registered from local CSVs (e.g., matches, deliveries); query them directly.
Every tool call must include a `purpose` argument that briefly and non-technically states what the tool is about to do.
Use read_vega_doc to fetch Vega/Vega-Lite specs from URLs before deciding to render charts.

You will talk in less than 200 words at a time. You will not generate tables, diagrams or reasons unless asked.
Note that the end user is not familiar with SQL or data analysis, so don't bother giving technical details what so ever.

ALWAYS FIRST READ THE SCHEMA
"""

agent = Agent(
    # "openai:gpt-5-mini",
    "google-gla:gemini-3-flash-preview",
    instructions=instructions,
)
deps = None

DATA_DIR = Path(__file__).resolve().parent


def register_csv_views(conn: duckdb.DuckDBPyConnection, csv_path: str | None = None):
    """Register CSV files as DuckDB views for convenient querying.

    - If csv_path is provided, only that file is registered.
    - Otherwise, all top-level CSV files alongside this script are registered.
    """

    targets = [Path(csv_path)] if csv_path else list(DATA_DIR.glob("*.csv"))

    for csv_file in targets:
        alias = csv_file.stem.replace("-", "_")
        conn.execute(
            f"CREATE OR REPLACE VIEW {alias} AS SELECT * FROM read_csv_auto('{csv_file.as_posix()}')"
        )


# Eagerly register known CSVs on startup so tools can query by table name (e.g., matches, deliveries)
_startup_conn = duckdb.connect()
register_csv_views(_startup_conn)
_startup_conn.close()

@agent.tool_plain()
def read_csv_with_schema(table: str, purpose: str):
    """Show schema + sample for a registered CSV table (avoids sending full data)."""
    conn = duckdb.connect()
    register_csv_views(conn)  # ensure views exist

    # Sample the first 50 rows instead of loading the whole file
    sample_df = conn.execute(
        f"SELECT * FROM {table} LIMIT 50"
    ).df()

    # Get schema info
    schema_df = conn.execute(
        f"DESCRIBE SELECT * FROM {table}"
    ).df()

    # Count rows without materializing the table
    row_count = conn.execute(
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
def execute_sql_on_csv(sql_query: str, purpose: str) -> str:
    """Execute a SELECT against registered CSV tables. Avoid 1000s of rows."""
    conn = duckdb.connect()
    register_csv_views(conn)

    # allow only select queries
    sql_query = sql_query.strip().rstrip(";")
    # black_list_cmds = ["insert", "update", "delete", "create", "drop", "alter"]
    # if any(
    #     cmd in sql_query for cmd in black_list_cmds
    # ):
    #     return "Error: Only SELECT queries are allowed."
    result_df = conn.execute(sql_query).df()

    print(f"Executed SQL: {sql_query}")
    print(f"Result rows: {len(result_df)}")
    print(result_df.head())

    return result_df.to_csv()


@agent.tool_plain()
def render_altair_chart_py(sql_query: str, altair_python: str, purpose: str):
    import altair as alt
    import altair
    import pandas as pd, numpy as np
    """Render an Altair chart using Python code that defines `chart`.

    The code runs with access to: df (pandas DataFrame), alt (Altair), pd (pandas).
    """
    conn = duckdb.connect()
    register_csv_views(conn)

    # Enforce SELECT-only
    normalized_query = sql_query.strip().rstrip(";")
    # if not normalized_query.lower().startswith("select"):
    #     return "Error: Only SELECT queries are allowed. Reference registered tables like matches or deliveries."

    limited_query = f"SELECT * FROM ({normalized_query}) t LIMIT 2000"
    df = conn.execute(limited_query).df()

    exec_env = {"__builtins__": __builtins__, "df": df, "alt": alt, "pd": pd}

    try:
        exec(altair_python, exec_env)
    except Exception as exc:  # noqa: BLE001
        return f"Error executing Altair code: {exc}"

    chart = exec_env.get("chart")
    if chart is None or not hasattr(chart, "to_html"):
        return "Error: Altair code must define a `chart` variable."

    def _spec_height(spec):
        if isinstance(spec, list):
            return max((_spec_height(s) for s in spec), default=0)
        if not isinstance(spec, dict):
            return 0
        if "height" in spec and isinstance(spec["height"], (int, float)):
            return int(spec["height"])
        if "vconcat" in spec:
            items = spec["vconcat"]
            return sum(_spec_height(s) for s in items) + max(len(items) - 1, 0) * 20
        if "hconcat" in spec:
            return max((_spec_height(s) for s in spec["hconcat"]), default=0)
        if "layer" in spec:
            return max((_spec_height(s) for s in spec["layer"]), default=0)
        if "spec" in spec:
            return _spec_height(spec["spec"])
        return 0

    try:
        html_content = chart.to_html(embed_options={"actions": False})
    except Exception as exc:  # noqa: BLE001
        return f"Error serializing chart HTML: {exc}"

    try:
        spec = chart.to_dict()
        chart_height = _spec_height(spec)
    except Exception:  # noqa: BLE001
        chart_height = 0

    # Add padding for titles/axes/legend to avoid scrollbars.
    iframe_height = max(300, chart_height + 120)

    iframe_html = (
        f"<iframe src=\"data:text/html;base64,{base64.b64encode(html_content.encode()).decode()}\" "
        f"frameborder=\"0\" style=\"width:100%; height:{iframe_height}px;\"></iframe>"
    )

    html_id = store_html(iframe_html)
    return {"_pylogue_html_id": html_id, "message": "Chart rendered."}
