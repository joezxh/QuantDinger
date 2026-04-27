import json
from dotenv import load_dotenv
from sqlalchemy import text

from app.database.session import get_session

# Load .env file
load_dotenv()


def _run_query(pattern: str) -> list[dict]:
    stmt = text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name LIKE :pattern"
    )
    with get_session() as session:
        result = session.execute(stmt, {"pattern": pattern})
        return [dict(row) for row in result.mappings().fetchall()]


try:
    results = _run_query("%ai%")
    print("AI related tables:")
    print(json.dumps(results, indent=2))

    results = _run_query("%llm%")
    print("LLM related tables:")
    print(json.dumps(results, indent=2))
except Exception as e:
    print(f"Error: {e}")
