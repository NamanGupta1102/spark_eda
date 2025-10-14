import os
import pandas as pd
import time
from sqlalchemy import create_engine, text
from openai import OpenAI
from langsmith import Client
from pocketflow import Flow, Node
import folium
from datetime import datetime
import dotenv

dotenv.load_dotenv()

# Configuration
DB_URL = os.getenv('DB_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


# Set environment variables for LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv('LANGCHAIN_API_KEY')
os.environ["LANGCHAIN_PROJECT"] = 'pocketflow-testing'

client = Client(api_key=os.environ.get('LANGCHAIN_API_KEY'))

def get_schema(table_name):
    """Get table schema"""
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        return f"Table '{table_name}' columns:\n" + "\n".join([f"- {col[0]} ({col[1]})" for col in columns])

def generate_sql(question, schema):
    """Generate SQL using LLM"""
    from langsmith import traceable
    
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""Question: {question}

Database: PostgreSQL

Schema:
{schema}

Generate a PostgreSQL-compatible SQL query. Return ONLY the SQL query, no explanations:"""
    
    @traceable(name="sql_generation", metadata={"model": "gpt-4o-mini", "provider": "openai"})
    def _generate_sql_inner(question, schema):
        start_time = time.time()
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        inference_time = time.time() - start_time
        
        sql = response.choices[0].message.content.strip()
        
        # Extract SQL from markdown if present
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()
        
        # Log token usage and inference time
        tokens_used = 0
        if hasattr(response, 'usage') and response.usage:
            tokens_used = response.usage.total_tokens
            metrics = {
                "total_tokens": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "inference_time_seconds": round(inference_time, 3),
                "tokens_per_second": round(response.usage.total_tokens / inference_time, 2) if inference_time > 0 else 0,
                "cost_estimate": response.usage.total_tokens * 0.00015
            }
            print(f"SQL Generation - Metrics: {metrics}")
        
        return sql, tokens_used
    
    result = _generate_sql_inner(question, schema)
    return result

def run_sql(sql):
    """Execute SQL and return DataFrame"""
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df

def generate_answer(question, df):
    """Generate answer using LLM"""
    from langsmith import traceable
    
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    data_sample = df.head(10).to_json(orient="records")
    
    prompt = f"""Question: {question}

Data:
{data_sample}

Answer:"""
    
    @traceable(name="answer_generation", metadata={"model": "gpt-4o-mini", "provider": "openai"})
    def _generate_answer_inner(question, data_sample):
        start_time = time.time()
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        inference_time = time.time() - start_time
        
        answer = response.choices[0].message.content.strip()
        
        # Log token usage and inference time
        tokens_used = 0
        if hasattr(response, 'usage'):
            tokens_used = response.usage.total_tokens
            metrics = {
                "total_tokens": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "inference_time_seconds": round(inference_time, 3),
                "tokens_per_second": round(response.usage.total_tokens / inference_time, 2) if inference_time > 0 else 0,
                "cost_estimate": response.usage.total_tokens * 0.00015
            }
            print(f"Answer Generation - Metrics: {metrics}")
        
        return answer, tokens_used
    
    result = _generate_answer_inner(question, data_sample)
    return result

# PocketFlow Nodes
class GetSchemaNode(Node):
    def prep(self, shared):
        print("Getting schema...")
        return shared.get("table_name")
    
    def exec(self, prep_res):
        schema = get_schema(prep_res)
        print(schema)
        return schema
    
    def post(self, shared, prep_res, exec_res):
        shared["schema"] = exec_res
        return "default"  # Return action to trigger next node

class GenerateSQLNode(Node):
    def prep(self, shared):
        print("\nGenerating SQL...")
        return {
            "question": shared.get("question"),
            "schema": shared.get("schema")
        }
    
    def exec(self, prep_res):
        start_time = time.time()
        sql, tokens = generate_sql(prep_res["question"], prep_res["schema"])
        sql_time = time.time() - start_time
        return {"sql": sql, "tokens": tokens, "time": sql_time}
    
    def post(self, shared, prep_res, exec_res):
        shared["sql"] = exec_res["sql"]
        shared["sql_tokens"] = exec_res["tokens"]
        shared["sql_time"] = exec_res["time"]
        print(f"SQL: {exec_res['sql']}")
        return "default"  # Return action to trigger next node

class RunQueryNode(Node):
    def prep(self, shared):
        print("\nExecuting SQL...")
        return shared.get("sql")
    
    def exec(self, prep_res):
        start_time = time.time()
        df = run_sql(prep_res)
        query_time = time.time() - start_time
        return {"df": df, "time": query_time}
    
    def post(self, shared, prep_res, exec_res):
        shared["df"] = exec_res["df"]
        shared["query_time"] = exec_res["time"]
        print(f"Got {len(exec_res['df'])} rows")
        return "default"  # Return action to trigger next node

class PlotMapNode(Node):
    def prep(self, shared):
        return shared.get("df")
    
    def exec(self, prep_res):
        df = prep_res
        
        # Check if df has latitude and longitude columns
        lat_col = None
        lon_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'lat' in col_lower and not lon_col:
                lat_col = col
            if 'lon' in col_lower or 'lng' in col_lower:
                lon_col = col
        
        if not lat_col or not lon_col or len(df) == 0:
            return None
        
        # Create map centered on mean coordinates
        center_lat = df[lat_col].mean()
        center_lon = df[lon_col].mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Add markers
        for _, row in df.iterrows():
            folium.Marker(
                location=[row[lat_col], row[lon_col]]
            ).add_to(m)
        
        # Create maps folder if it doesn't exist
        os.makedirs("maps", exist_ok=True)
        
        # Save map
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"maps/map_{timestamp}.html"
        m.save(filename)
        
        return filename
    
    def post(self, shared, prep_res, exec_res):
        if exec_res:
            shared["map_file"] = exec_res
            print(f"\nMap saved to: {exec_res}")
        return "default"

class GenerateAnswerNode(Node):
    def prep(self, shared):
        print("\nGenerating answer...")
        return {
            "question": shared.get("question"),
            "df": shared.get("df")
        }
    
    def exec(self, prep_res):
        start_time = time.time()
        answer, tokens = generate_answer(prep_res["question"], prep_res["df"])
        answer_time = time.time() - start_time
        return {"answer": answer, "tokens": tokens, "time": answer_time}
    
    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res["answer"]
        shared["answer_tokens"] = exec_res["tokens"]
        shared["answer_time"] = exec_res["time"]
        print(f"Answer: {exec_res['answer']}")
        return "default"  # Return action to trigger next node

class SummaryNode(Node):
    def prep(self, shared):
        return shared
    
    def exec(self, prep_res):
        total_time = prep_res.get("sql_time", 0) + prep_res.get("query_time", 0) + prep_res.get("answer_time", 0)
        total_tokens = prep_res.get("sql_tokens", 0) + prep_res.get("answer_tokens", 0)
        total_cost = total_tokens * 0.00015
        
        print("\n" + "="*60)
        print("POCKETFLOW PIPELINE SUMMARY")
        print("="*60)
        print(f"Total Pipeline Time: {round(total_time, 3)}s")
        print(f"  - SQL Generation: {round(prep_res.get('sql_time', 0), 3)}s")
        print(f"  - Query Execution: {round(prep_res.get('query_time', 0), 3)}s")
        print(f"  - Answer Generation: {round(prep_res.get('answer_time', 0), 3)}s")
        print(f"\nTotal Tokens Used: {total_tokens}")
        print(f"  - SQL Generation: {prep_res.get('sql_tokens', 0)}")
        print(f"  - Answer Generation: {prep_res.get('answer_tokens', 0)}")
        print(f"\nEstimated Cost: ${round(total_cost, 6)}")
        print("="*60)
        
        return {
            "total_time": round(total_time, 3),
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6)
        }
    
    def post(self, shared, prep_res, exec_res):
        shared["summary"] = exec_res
        return None

def main():
    # Build PocketFlow pipeline
    get_schema_node = GetSchemaNode()
    generate_sql_node = GenerateSQLNode()
    run_query_node = RunQueryNode()
    plot_map_node = PlotMapNode()
    generate_answer_node = GenerateAnswerNode()
    summary_node = SummaryNode()
    
    # Wire nodes together
    flow = Flow().start(get_schema_node)
    get_schema_node >> generate_sql_node >> run_query_node >> plot_map_node >> generate_answer_node >> summary_node
    
    # Run pipeline
    question = "What are the top 5 request types by count?"
    table_name = "Dorchester_311"
    
    print("="*60)
    print("Starting PocketFlow SQL QA Pipeline")
    print("="*60)
    
    shared = {"question": question, "table_name": table_name}
    flow._run(shared)
    
    print(f"\nFinal Answer: {shared.get('answer')}")

if __name__ == "__main__":
    main()
