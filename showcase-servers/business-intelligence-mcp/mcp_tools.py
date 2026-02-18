from pydantic import BaseModel
from typing import Optional
import re
from db import run_query
from llm_provider import get_llm_provider

class NLQueryRequest(BaseModel):
    query: str
    schema_hint: Optional[str] = None


FORBIDDEN_SQL_PATTERNS = [
    r"\bdrop\b",
    r"\bdelete\b",
    r"\binsert\b",
    r"\bupdate\b",
    r"\balter\b",
    r"\btruncate\b",
    r"\bcreate\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\bexecute\b",
    r"\bcall\b",
]


def normalize_sql(sql: str) -> str:
    normalized = sql.strip()
    if normalized.startswith("```"):
        normalized = re.sub(r"^```(?:sql)?", "", normalized, flags=re.IGNORECASE).strip()
        normalized = re.sub(r"```$", "", normalized).strip()
    return normalized


def validate_sql_is_safe(sql: str) -> None:
    compact = sql.strip()
    if not compact:
        raise ValueError("Generated SQL is empty")

    if "--" in compact or "/*" in compact or "*/" in compact:
        raise ValueError("SQL comments are not allowed")

    if compact.count(";") > 1 or (";" in compact and not compact.endswith(";")):
        raise ValueError("Only a single SQL statement is allowed")

    if re.search(r"^\s*(select|with)\b", compact, flags=re.IGNORECASE) is None:
        raise ValueError("Only read-only SELECT/CTE queries are allowed")

    for pattern in FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, compact, flags=re.IGNORECASE):
            raise ValueError("Generated SQL contains blocked keywords")

def handle_nl_query(payload: NLQueryRequest):
    llm = get_llm_provider()
    sql = normalize_sql(llm.generate_sql(payload.query, payload.schema_hint))
    validate_sql_is_safe(sql)
    rows = run_query(sql)
    return {"sql": sql, "rows": rows}
