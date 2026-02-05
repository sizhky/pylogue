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
import psycopg2
from psycopg2.extras import RealDictCursor

dotenv.load_dotenv()
from simple_salesforce import Salesforce

# Salesforce Configuration
config = dict(
    username=os.environ['SALESFORCE_USERNAME'],
    password=os.environ['SALESFORCE_PASSWORD'],
    security_token=os.environ['SALESFORCE_SECURITY_TOKEN'],
)
sf = Salesforce(**config)

# PostgreSQL Configuration
db_config = dict(
    host=os.environ.get('DB_HOST', 'localhost'),
    port=os.environ.get('DB_PORT', '5432'),
    database=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
)

# Insurance Database Configuration
insurance_db_config = dict(
    host=os.environ.get('INSURANCE_DB_HOST', 'localhost'),
    port=os.environ.get('INSURANCE_DB_PORT', '5432'),
    database=os.environ['INSURANCE_DB_NAME'],
    user=os.environ['INSURANCE_DB_USER'],
    password=os.environ['INSURANCE_DB_PASSWORD'],
)

def get_db_connection():
    """Create a PostgreSQL database connection"""
    with logfire.span('get_db_connection', database=db_config['database'], host=db_config['host']):
        logfire.info('Connecting to main database', database=db_config['database'])
        conn = psycopg2.connect(**db_config)
        logfire.info('Main database connection established')
        return conn

def get_insurance_db_connection():
    """Create an Insurance database connection"""
    with logfire.span('get_insurance_db_connection', database=insurance_db_config['database'], host=insurance_db_config['host']):
        logfire.info('Connecting to insurance database', database=insurance_db_config['database'])
        conn = psycopg2.connect(**insurance_db_config)
        logfire.info('Insurance database connection established')
        return conn

def get_salesforce_tables():
    "Get list of all queryable Salesforce tables"
    with logfire.span('get_salesforce_tables'):
        logfire.info('Fetching Salesforce tables list')
        tables = [obj['name'] for obj in sf.describe()['sobjects'] if obj['queryable']]
        logfire.info('Salesforce tables retrieved', count=len(tables))
        return tables

def load_database_schema():
    """Load database schema from eb-db-schema.sql file"""
    schema_file = Path(__file__).resolve().parent / 'eb-db-schema.sql'
    try:
        with open(schema_file, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Database schema file not found."

def load_insurance_database_schema():
    """Load insurance database schema from insurance-db-schema.sql file"""
    schema_file = Path(__file__).resolve().parent / 'insurance-db-schema.sql'
    try:
        with open(schema_file, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Insurance database schema file not found."

# Configure Logfire with write token
logfire.configure(
    token=os.environ.get('EB_LOGFIRE_WRITE_TOKEN'),
    service_name='salesforce-agent',
    environment='dev',
)
logfire.instrument_pydantic_ai()
logfire.instrument_psycopg()
logfire.info('Application started', service='salesforce-agent')

instructions = f"""
System Instruction for Salesforce & Database Query Assistant:

You are a multi-source data assistant with access to Salesforce, PostgreSQL database, and Insurance database.

=== SALESFORCE TOOLS ===
get_table_schema(table_name) - Returns schema details for a Salesforce table
run_salesforce_query(soql_query) - Executes a SOQL query and returns records
render_altair_chart_py(soql_query, altair_python) - Renders charts from Salesforce data

SOQL Syntax:
- Use SELECT, FROM, WHERE, ORDER BY, LIMIT
- Field references use dot notation (e.g., Account.Name)
- String values need single quotes
- No JOIN keyword - use relationship queries

Available Salesforce Tables: {get_salesforce_tables()}

=== MAIN DATABASE TOOLS ===
run_database_query(sql_query) - Executes a SQL query and returns records
render_db_chart_py(sql_query, altair_python) - Renders charts from database data

SQL Syntax:
- Standard PostgreSQL syntax
- Use JOINs for related tables
- String values need single quotes

=== MAIN DATABASE SCHEMA ===
{load_database_schema()}

=== INSURANCE DATABASE TOOLS ===
run_insurance_db_query(sql_query) - Executes a SQL query on insurance database and returns records
render_insurance_db_chart_py(sql_query, altair_python) - Renders charts from insurance database data

SQL Syntax:
- Standard PostgreSQL syntax
- Use JOINs for related tables
- String values need single quotes

=== INSURANCE DATABASE SCHEMA ===
{load_insurance_database_schema()}

=== YOUR TASK ===
Answer user questions by intelligently determining whether to query Salesforce, main database, or insurance database (or combination).

Approach:
1. Analyze the user's question to determine data source(s)
2. Refer to the database schemas above for table and column names
3. Construct and execute appropriate queries
4. Present results clearly

Rules:
- NEVER connect to database to retrieve schema information - use the provided schemas above
- Refer directly to the schema files provided in the instructions
- Default to text-based answers
- Only create visualizations when explicitly requested
- Do not give technical explanations unless asked
- Every tool call must include a `purpose` argument (max 3 words, verb-noun phrase, e.g., "fetching user data")
"""

agent = Agent(
    # "openai:gpt-5-mini",
    "google-gla:gemini-2.5-flash",
    instructions=instructions,
)
deps = None

DATA_DIR = Path(__file__).resolve().parent

@agent.tool_plain()
def get_table_schema(table_name: str, purpose: str):
    "Get schema details for a specific Salesforce table"
    with logfire.span('get_table_schema', table_name=table_name, purpose=purpose):
        try:
            logfire.info('Fetching Salesforce table schema', table=table_name, purpose=purpose)
            table = getattr(sf, table_name)
            fields = table.describe()['fields']
            schema = []
            for f in fields:
                field_info = dict(name=f['name'], type=f['type'], label=f['label'])
                if f['type'] == 'picklist': field_info['values'] = [v['value'] for v in f['picklistValues']]
                if f['type'] == 'reference': field_info['references'] = f['referenceTo']
                schema.append(field_info)
            logfire.info('Schema retrieved successfully', table=table_name, field_count=len(schema))
            return schema
        except Exception as e:
            logfire.error('Error retrieving schema', table=table_name, error=str(e))
            return f"Error retrieving schema for table {table_name}: {e}"

@agent.tool_plain()
def run_salesforce_query(soql_query: str, purpose: str):
    "Execute a SOQL query and return results"
    with logfire.span('run_salesforce_query', query=soql_query, purpose=purpose):
        try:
            logfire.info('Executing SOQL query', query=soql_query, purpose=purpose)
            result = sf.query(soql_query)
            record_count = len(result['records'])
            logfire.info('SOQL query executed successfully', record_count=record_count, purpose=purpose)
            return result['records']
        except Exception as e:
            logfire.error('SOQL query execution failed', query=soql_query, error=str(e))
            return f"Error executing SOQL query: {e}"

@agent.tool_plain()
def run_database_query(sql_query: str, purpose: str):
    """Execute a PostgreSQL SQL query and return results"""
    with logfire.span('run_database_query', query=sql_query, purpose=purpose, database='main'):
        try:
            logfire.info('Executing SQL query on main database', query=sql_query, purpose=purpose)
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(sql_query)
            
            # Check if it's a SELECT query
            if cursor.description:
                results = cursor.fetchall()
                results = [dict(row) for row in results]
                logfire.info('SQL query executed successfully', row_count=len(results), purpose=purpose)
            else:
                results = {"message": "Query executed successfully", "rowcount": cursor.rowcount}
                logfire.info('SQL command executed', rows_affected=cursor.rowcount, purpose=purpose)
            
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            logfire.error('SQL query execution failed', query=sql_query, error=str(e), database='main')
            return f"Error executing SQL query: {e}"

@agent.tool_plain()
def run_insurance_db_query(sql_query: str, purpose: str):
    """Execute a SQL query on Insurance database and return results"""
    with logfire.span('run_insurance_db_query', query=sql_query, purpose=purpose, database='insurance'):
        try:
            logfire.info('Executing SQL query on insurance database', query=sql_query, purpose=purpose)
            conn = get_insurance_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(sql_query)
            
            # Check if it's a SELECT query
            if cursor.description:
                results = cursor.fetchall()
                results = [dict(row) for row in results]
                logfire.info('SQL query executed successfully', row_count=len(results), purpose=purpose)
            else:
                results = {"message": "Query executed successfully", "rowcount": cursor.rowcount}
                logfire.info('SQL command executed', rows_affected=cursor.rowcount, purpose=purpose)
            
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            logfire.error('SQL query execution failed', query=sql_query, error=str(e), database='insurance')
            return f"Error executing insurance database SQL query: {e}"

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
    with logfire.span('render_altair_chart_py', query=soql_query, purpose=purpose, data_source='salesforce'):
        try:
            logfire.info('Rendering Salesforce chart', purpose=purpose)
            results = run_salesforce_query(soql_query, purpose="Fetch Salesforce data for the chart.")
            flattened = [_flatten_record(r) for r in results]
            df = pd.DataFrame(flattened)
            logfire.debug('Data prepared for chart', rows=len(df), columns=len(df.columns))

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
            logfire.info('Salesforce chart rendered successfully', html_id=html_id, purpose=purpose)
            return {"_pylogue_html_id": html_id, "message": "Chart rendered."}
        except Exception as e:
            logfire.error('Chart rendering failed', error=str(e), data_source='salesforce')
            return f"Error in render_altair_chart_py: {e}"

@agent.tool_plain()
def render_db_chart_py(sql_query: str, altair_python: str, purpose: str):
    """Render an Altair chart using Python code that defines `chart` from database data.

    Always provide tooltips for interactivity in the chart.

    The code runs with access to: results (raw database records),
    df (pandas DataFrame), alt (Altair), pd (pandas).
    """
    with logfire.span('render_db_chart_py', query=sql_query, purpose=purpose, data_source='main_database'):
        try:
            logfire.info('Rendering database chart', purpose=purpose, database='main')
            results = run_database_query(sql_query, purpose="Fetch database data for the chart.")
            
            if isinstance(results, str):  # Error message
                logfire.error('Failed to fetch data for chart', error=results)
                return results
                
            df = pd.DataFrame(results)
            logfire.debug('Data prepared for chart', rows=len(df), columns=len(df.columns))

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
            logfire.info('Database chart rendered successfully', html_id=html_id, purpose=purpose, database='main')
            return {"_pylogue_html_id": html_id, "message": "Chart rendered."}
        except Exception as e:
            logfire.error('Chart rendering failed', error=str(e), data_source='main_database')
            return f"Error in render_db_chart_py: {e}"

@agent.tool_plain()
def render_insurance_db_chart_py(sql_query: str, altair_python: str, purpose: str):
    """Render an Altair chart using Python code that defines `chart` from insurance database data.

    Always provide tooltips for interactivity in the chart.

    The code runs with access to: results (raw insurance database records),
    df (pandas DataFrame), alt (Altair), pd (pandas).
    """
    with logfire.span('render_insurance_db_chart_py', query=sql_query, purpose=purpose, data_source='insurance_database'):
        try:
            logfire.info('Rendering insurance chart', purpose=purpose, database='insurance')
            results = run_insurance_db_query(sql_query, purpose="Fetch insurance database data for the chart.")
            
            if isinstance(results, str):  # Error message
                logfire.error('Failed to fetch data for chart', error=results)
                return results
                
            df = pd.DataFrame(results)
            logfire.debug('Data prepared for chart', rows=len(df), columns=len(df.columns))

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
            logfire.info('Insurance chart rendered successfully', html_id=html_id, purpose=purpose, database='insurance')
            return {"_pylogue_html_id": html_id, "message": "Insurance chart rendered."}
        except Exception as e:
            logfire.error('Chart rendering failed', error=str(e), data_source='insurance_database')
            return f"Error in render_insurance_db_chart_py: {e}"

def app_factory():
    logfire.info('Creating application instance')
    app = create_core_app(
        responder_factory=lambda: PydanticAIResponder(
            agent=agent,
            agent_deps=deps,
            show_tool_details=True,
        ),
        tag_line="Divami AI",
        tag_line_href="https://ai.divami.com",
        title="Salesforce & G Suite Intelligence",
        subtitle="Ask questions about your Salesforce and PostgreSQL data",
    )
    logfire.info('Application instance created successfully')
    return app


if __name__ == "__main__":
    # Run with: python -m scripts.examples.ai.pylogue_demo_app
    import uvicorn

    logfire.info('Starting server', host="0.0.0.0", port=5004)
    uvicorn.run(
        "salesforce-agent:app_factory",
        host="0.0.0.0",
        port=5004,
        reload=True,
        factory=True,
    )
