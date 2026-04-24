import os
import json
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from app.utils.db_postgres import execute_sql

try:
    results = execute_sql("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%ai%'")
    print("AI related tables:")
    print(json.dumps(results, indent=2))
    
    results = execute_sql("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%llm%'")
    print("LLM related tables:")
    print(json.dumps(results, indent=2))
except Exception as e:
    print(f"Error: {e}")
