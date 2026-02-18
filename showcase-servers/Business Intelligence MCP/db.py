from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import os

def get_engine() -> Engine:
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise RuntimeError("DB_URL is not set")
    return create_engine(db_url)

def run_query(sql: str, params: dict | None = None):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        rows = [dict(r) for r in result]
    return rows
