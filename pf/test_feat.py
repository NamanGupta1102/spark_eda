from simple_sql_qa_pocketflow import generate_sql, get_schema
import json

# Test dual SQL query generation
print("="*60)
print("Testing Dual SQL Query Generation")
print("="*60)

# Get schema for the table
table_name = "Dorchester_311"
schema = get_schema(table_name)
print(f"\nSchema:\n{schema}\n")

# Test question
question = "What are the total numer of noise complaints in the month of October 2024?"

print(f"Question: {question}\n")

# Generate SQL queries
queries, tokens = generate_sql(question, schema)

print("Generated Queries:")
print("="*60)
print("\n1. Answer Query:")
print(queries["answer_query"])
print("\n2. Map Query:")
print(queries["map_query"])
print("\n" + "="*60)
print(f"Tokens used: {tokens}")

# Verify structure
print("\n" + "="*60)
print("Verification:")
print("="*60)
assert "answer_query" in queries, "Missing 'answer_query' key"
assert "map_query" in queries, "Missing 'map_query' key"
assert isinstance(queries["answer_query"], str), "answer_query is not a string"
assert isinstance(queries["map_query"], str), "map_query is not a string"
assert "LIMIT" in queries["map_query"].upper(), "map_query doesn't have LIMIT"

print("✓ Both queries returned successfully")
print("✓ Queries are valid strings")
print("✓ Map query has LIMIT clause")
print("\nTest passed!")

