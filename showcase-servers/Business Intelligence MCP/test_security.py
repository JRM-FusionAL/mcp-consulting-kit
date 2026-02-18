import pathlib
import sys

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_tools import normalize_sql, validate_sql_is_safe
import main

app = main.app


def test_normalize_sql_strips_markdown_fence():
    raw = "```sql\nSELECT 1;\n```"
    assert normalize_sql(raw) == "SELECT 1;"


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM customers;",
        "WITH t AS (SELECT 1) SELECT * FROM t;",
    ],
)
def test_validate_sql_is_safe_accepts_read_queries(sql):
    validate_sql_is_safe(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM customers;",
        "SELECT * FROM customers; DROP TABLE customers;",
        "SELECT * FROM customers -- comment",
        "UPDATE customers SET name = 'x';",
    ],
)
def test_validate_sql_is_safe_blocks_dangerous_queries(sql):
    with pytest.raises(ValueError):
        validate_sql_is_safe(sql)


def test_nl_query_requires_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    monkeypatch.delenv("API_KEYS", raising=False)
    monkeypatch.delenv("REVOKED_API_KEYS", raising=False)
    client = TestClient(app)
    response = client.post("/nl-query", json={"query": "show top customers"})
    assert response.status_code == 401


def test_nl_query_rate_limit(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    monkeypatch.delenv("API_KEYS", raising=False)
    monkeypatch.delenv("REVOKED_API_KEYS", raising=False)
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setattr(main, "handle_nl_query", lambda req: {"sql": "SELECT 1;", "rows": []})

    app.state.rate_limit_store.clear()
    client = TestClient(app)

    first = client.post(
        "/nl-query",
        json={"query": "show top customers"},
        headers={"X-API-Key": "secret"},
    )
    second = client.post(
        "/nl-query",
        json={"query": "show top customers"},
        headers={"X-API-Key": "secret"},
    )

    assert first.status_code == 200
    assert second.status_code == 429


def test_nl_query_accepts_dual_rotation_keys(monkeypatch):
    monkeypatch.setenv("API_KEYS", "new-key,old-key")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("REVOKED_API_KEYS", raising=False)
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "10")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setattr(main, "handle_nl_query", lambda req: {"sql": "SELECT 1;", "rows": []})

    app.state.rate_limit_store.clear()
    client = TestClient(app)

    with_old = client.post(
        "/nl-query",
        json={"query": "show top customers"},
        headers={"X-API-Key": "old-key"},
    )
    with_new = client.post(
        "/nl-query",
        json={"query": "show top customers"},
        headers={"X-API-Key": "new-key"},
    )

    assert with_old.status_code == 200
    assert with_new.status_code == 200


def test_nl_query_rejects_revoked_key(monkeypatch):
    monkeypatch.setenv("API_KEYS", "new-key,old-key")
    monkeypatch.setenv("REVOKED_API_KEYS", "old-key")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "10")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setattr(main, "handle_nl_query", lambda req: {"sql": "SELECT 1;", "rows": []})

    app.state.rate_limit_store.clear()
    client = TestClient(app)

    response = client.post(
        "/nl-query",
        json={"query": "show top customers"},
        headers={"X-API-Key": "old-key"},
    )

    assert response.status_code == 401
