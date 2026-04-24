import os
import json
from dotenv import load_dotenv
from app.utils.db_postgres import get_pg_connection

# Load .env file
load_dotenv()

def run_sql_file(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Split by semicolon but ignore inside quotes (simple split for now)
    # Better: use a proper SQL parser or just run the whole thing if the driver supports it
    # psycopg2 supports running multiple statements in one execute()
    
    try:
        with get_pg_connection() as conn:
            cursor = conn.cursor()
            print(f"Executing {file_path}...")
            cursor.execute(sql)
            conn.commit()
            print("Successfully executed SQL migration.")
    except Exception as e:
        print(f"Error executing SQL: {e}")

if __name__ == "__main__":
    run_sql_file("migrations/llm_lb_setup.sql")
