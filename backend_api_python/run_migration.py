import os
from dotenv import load_dotenv
from sqlalchemy import text

from app.database.session import get_session

# Load .env file
load_dotenv()


def run_sql_file(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        print(f"Executing {file_path}...")
        with get_session() as session:
            session.execute(text(sql))
            session.commit()
        print("Successfully executed SQL migration.")
    except Exception as e:
        print(f"Error executing SQL: {e}")

if __name__ == "__main__":
    run_sql_file("migrations/llm_lb_setup.sql")
