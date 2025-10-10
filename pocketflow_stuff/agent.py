"""
Simple PocketFlow PostgreSQL Agent

Minimal PocketFlow implementation for querying a PostgreSQL database.
Adds optional LLM-backed Natural-Language → SQL translation.
"""

import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, List
from abc import ABC, abstractmethod
from contextlib import closing

try:
    # Optional; only used if OPENAI_API_KEY is provided
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


class Node(ABC):
    """Base class for all PocketFlow nodes"""
    
    @abstractmethod
    def execute(self, shared_store: Dict[str, Any]) -> None:
        """Execute the node's logic and update the shared store"""
        pass


class DatabaseQueryNode(Node):
    """Node that executes SQL queries against PostgreSQL database"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
    
    def execute(self, shared_store: Dict[str, Any]) -> None:
        """Execute SQL query and store results in shared store"""
        query = shared_store.get('sql_query', 'SELECT 1 as test')
        
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                # Convert to JSON-serializable format
                json_results = [dict(row) for row in results]
                
                shared_store['query_results'] = json_results
                shared_store['query_success'] = True
                shared_store['row_count'] = len(json_results)
                
        except Exception as e:
            shared_store['query_error'] = str(e)
            shared_store['query_success'] = False
        finally:
            if 'conn' in locals():
                conn.close()


class NLToSQLNode(Node):
    """Node that converts natural language to SQL using an LLM (optional).

    - If the input already looks like SQL, it is passed through unchanged.
    - If no OPENAI_API_KEY or OpenAI SDK is available, falls back to simple rules.
    """

    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        if load_dotenv is not None:
            try:
                load_dotenv()
            except Exception:
                pass
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()

    def _looks_like_sql(self, text: str) -> bool:
        if not text:
            return False
        head = text.strip().lower()
        return bool(re.match(r"^(with|select|explain|show|describe|\s*--)", head))

    def _introspect_schema(self) -> str:
        """Return a compact schema description to guide the LLM.

        Keeps it short to reduce token usage.
        """
        ddl_lines: List[str] = []
        try:
            with closing(psycopg2.connect(**self.db_config)) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema='public'
                        ORDER BY table_name
                        LIMIT 5
                        """
                    )
                    tables = [r["table_name"] for r in cur.fetchall()]
                    for t in tables:
                        cur.execute(
                            """
                            SELECT column_name, data_type
                            FROM information_schema.columns
                            WHERE table_schema='public' AND table_name=%s
                            ORDER BY ordinal_position
                            LIMIT 40
                            """,
                            (t,),
                        )
                        cols = ", ".join(f"{r['column_name']} {r['data_type']}" for r in cur.fetchall())
                        ddl_lines.append(f"TABLE {t}({cols})")
        except Exception:
            # Best effort; empty schema is acceptable
            pass
        return "\n".join(ddl_lines)[:2000]

    def _fallback_rules(self, nl: str) -> str:
        q = nl.lower()
        if "top" in q and "request" in q and "count" in q:
            return (
                "SELECT case_title, COUNT(*) AS count "
                "FROM crimes311 GROUP BY case_title ORDER BY count DESC LIMIT 5"
            )
        if "total" in q and ("records" in q or "rows" in q or "count" in q):
            return "SELECT COUNT(*) AS total_records FROM crimes311"
        if "recent" in q or "latest" in q:
            return "SELECT * FROM crimes311 ORDER BY open_dt DESC NULLS LAST LIMIT 10"
        if "district" in q:
            return (
                "SELECT police_district, COUNT(*) AS count FROM crimes311 "
                "WHERE police_district IS NOT NULL GROUP BY police_district "
                "ORDER BY count DESC LIMIT 10"
            )
        return "SELECT * FROM crimes311 LIMIT 5"

    def _call_openai(self, nl: str, schema: str) -> str:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:  # SDK not installed
            raise RuntimeError("OpenAI SDK not installed. Install 'openai'.") from e

        client = OpenAI(api_key=self.openai_api_key)
        system_prompt = (
            "You are a PostgreSQL expert. Translate the user's natural language question "
            "into a single safe SQL SELECT query in PostgreSQL dialect using the given schema. "
            "Rules: only SELECT queries, never modify data, prefer explicit columns, include LIMIT 100 if not present, "
            "and ensure valid identifiers. Return ONLY the SQL, no prose, no code fences."
        )
        user_prompt = (
            f"Schema (approx):\n{schema}\n\n"
            f"Question: {nl}\n\n"
            "Output: a single SQL SELECT statement."
        )

        # Use chat.completions for wide compatibility
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        sql = resp.choices[0].message.content.strip()
        # Strip code fences if present
        sql = re.sub(r"^```.*\n|\n```$", "", sql).strip()
        # Safety: force SELECT and add LIMIT if missing
        if not sql.lower().startswith("select") and not sql.lower().startswith("with"):
            raise RuntimeError("Model did not return a SELECT/CTE query.")
        if re.search(r"\blimit\b", sql, flags=re.IGNORECASE) is None:
            sql += " LIMIT 100"
        return sql

    def execute(self, shared_store: Dict[str, Any]) -> None:
        text = shared_store.get('user_input') or shared_store.get('sql_query') or ""
        if self._looks_like_sql(text):
            shared_store['sql_query'] = text
            shared_store['nl2sql_used'] = False
            return

        # Need NL → SQL
        if not self.openai_api_key:
            # Fallback to deterministic rules if no API key
            shared_store['sql_query'] = self._fallback_rules(text)
            shared_store['nl2sql_used'] = False
            shared_store['nl2sql_mode'] = 'fallback_rules'
            return

        schema = self._introspect_schema()
        try:
            sql = self._call_openai(text, schema)
            shared_store['sql_query'] = sql
            shared_store['nl2sql_used'] = True
            shared_store['nl2sql_mode'] = 'openai'
        except Exception as e:
            # Last-resort fallback
            shared_store['sql_query'] = self._fallback_rules(text)
            shared_store['nl2sql_used'] = False
            shared_store['nl2sql_mode'] = f"fallback_due_to_error: {e}"


class ResultFormatterNode(Node):
    """Node that formats query results for display"""
    
    def execute(self, shared_store: Dict[str, Any]) -> None:
        """Format query results for display"""
        if not shared_store.get('query_success', False):
            shared_store['formatted_output'] = f"Error: {shared_store.get('query_error', 'Unknown error')}"
            return
        
        results = shared_store.get('query_results', [])
        row_count = shared_store.get('row_count', 0)
        
        if row_count == 0:
            shared_store['formatted_output'] = "Query executed successfully but returned no results."
            return
        
        # Simple formatting
        output_lines = [f"Query returned {row_count} rows:"]
        for i, row in enumerate(results[:10], 1):  # Limit to first 10 rows
            output_lines.append(f"Row {i}: {row}")
        
        if row_count > 10:
            output_lines.append(f"... and {row_count - 10} more rows")
        
        shared_store['formatted_output'] = '\n'.join(output_lines)


class Flow:
    """Simple PocketFlow implementation"""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.transitions: Dict[str, List[str]] = {}
    
    def add_node(self, name: str, node: Node) -> None:
        """Add a node to the flow"""
        self.nodes[name] = node
    
    def add_transition(self, from_node: str, to_node: str) -> None:
        """Add a transition between nodes"""
        if from_node not in self.transitions:
            self.transitions[from_node] = []
        self.transitions[from_node].append(to_node)
    
    def execute(self, shared_store: Dict[str, Any], start_node: str = None) -> Dict[str, Any]:
        """Execute the flow starting from the specified node"""
        if start_node is None:
            start_node = list(self.nodes.keys())[0]
        
        current_node = start_node
        execution_path = [current_node]
        
        while current_node in self.nodes:
            # Execute current node
            self.nodes[current_node].execute(shared_store)
            
            # Move to next node
            if current_node in self.transitions and self.transitions[current_node]:
                current_node = self.transitions[current_node][0]
                execution_path.append(current_node)
            else:
                break
        
        shared_store['execution_path'] = execution_path
        return shared_store


class PostgreSQLAgent:
    """Simple PostgreSQL agent using PocketFlow"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.flow = self._build_flow()
    
    def _build_flow(self) -> Flow:
        """Build the agent flow"""
        flow = Flow()
        
        # Create nodes
        n2s_node = NLToSQLNode(self.db_config)
        query_node = DatabaseQueryNode(self.db_config)
        formatter_node = ResultFormatterNode()
        
        # Add nodes to flow
        flow.add_node('translate_nl', n2s_node)
        flow.add_node('query_database', query_node)
        flow.add_node('format_results', formatter_node)
        
        # Define flow transitions
        flow.add_transition('translate_nl', 'query_database')
        flow.add_transition('query_database', 'format_results')
        
        return flow
    
    def query(self, sql_query: str) -> str:
        """Execute a SQL query using the agent flow"""
        shared_store = {'sql_query': sql_query}
        
        # Execute the flow
        # Start after translation to ensure uniform path
        result = self.flow.execute(shared_store, 'translate_nl')
        
        return result.get('formatted_output', 'No output generated')

    def ask(self, text: str) -> str:
        """Natural-language entry point. Translates to SQL (LLM or fallback) and executes."""
        shared_store = {'user_input': text}
        result = self.flow.execute(shared_store, 'translate_nl')
        sql = result.get('sql_query', '')
        # If translation produced SQL, run remaining nodes explicitly
        if 'query_results' not in result:
            # Continue from query -> formatter
            result = self.flow.execute(result, 'query_database')
        formatted = result.get('formatted_output', 'No output generated')
        return f"SQL: {sql}\n\n{formatted}"


# Database configuration (same as your existing setup)
DB_CONFIG = {
    'host': 'dpg-d3g661u3jp1c73eg9v1g-a.ohio-postgres.render.com',
    'port': 5432,
    'database': 'crime_rate_h3u5',
    'user': 'user1',
    'password': 'BbWTihWnsBHglVpeKK8XfQgEPDOcokZZ'
}


def main():
    """Simple demo of the PocketFlow agent"""
    agent = PostgreSQLAgent(DB_CONFIG)
    
    # Test queries
    test_queries = [
        "SELECT COUNT(*) as total_records FROM crimes311",
        "SELECT * FROM crimes311 LIMIT 3",
        "SELECT case_title, COUNT(*) as count FROM crimes311 GROUP BY case_title ORDER BY count DESC LIMIT 5"
    ]
    
    print("Simple PocketFlow PostgreSQL Agent")
    print("=" * 40)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 30)
        
        result = agent.query(query)
        print(result)
        print()


if __name__ == "__main__":
    main()
