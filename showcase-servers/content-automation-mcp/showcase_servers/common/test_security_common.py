from types import SimpleNamespace
import json

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import security


def build_request(path: str = "/nl-query", ip: str = "127.0.0.1"):
    app = SimpleNamespace(
        state=SimpleNamespace(
            rate_limit_store={},
            redis_client=None,
            redis_degraded=False,
            revoked_api_keys=set(),
        )
    )
    return SimpleNamespace(
        app=app,
        client=SimpleNamespace(host=ip),
        url=SimpleNamespace(path=path),
        headers={},
    )


class FakeRedisClient:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.counts = {}
        self.ttls = {}

    def incr(self, key: str) -> int:
        if self.should_fail:
            raise RuntimeError("redis unavailable")
        current = self.counts.get(key, 0) + 1
        self.counts[key] = current
        return current

    def expire(self, key: str, ttl_seconds: int) -> bool:
        if self.should_fail:
            raise RuntimeError("redis unavailable")
        self.ttls[key] = ttl_seconds
        return True


def test_get_allowed_origins_from_env(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.com, https://b.com ")
    assert security.get_allowed_origins() == ["https://a.com", "https://b.com"]


def test_get_allowed_origins_rejects_wildcards(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.com, *, https://b.com")
    assert security.get_allowed_origins() == ["https://a.com", "https://b.com"]


def test_get_allowed_origins_rejects_invalid_schemes(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.com, ftp://invalid.com, https://b.com")
    assert security.get_allowed_origins() == ["https://a.com", "https://b.com"]


def test_verify_api_key_rejects_missing_config(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_KEYS", raising=False)
    with pytest.raises(HTTPException) as exc:
        security.verify_api_key(build_request(), "secret")
    assert exc.value.status_code == 500


def test_verify_api_key_rejects_invalid_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "expected")
    with pytest.raises(HTTPException) as exc:
        security.verify_api_key(build_request(), "wrong")
    assert exc.value.status_code == 401


def test_verify_api_key_accepts_valid_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "expected")
    security.verify_api_key(build_request(), "expected")


def test_verify_api_key_accepts_dual_rotation_keys(monkeypatch):
    monkeypatch.setenv("API_KEYS", "new-key,old-key")
    monkeypatch.delenv("API_KEY", raising=False)

    request = build_request()
    security.verify_api_key(request, "new-key")
    security.verify_api_key(request, "old-key")


def test_verify_api_key_rejects_revoked_runtime_key(monkeypatch):
    monkeypatch.setenv("API_KEYS", "new-key,old-key")
    request = build_request()

    security.revoke_api_key(request.app, "old-key")

    with pytest.raises(HTTPException) as exc:
        security.verify_api_key(request, "old-key")
    assert exc.value.status_code == 401


def test_verify_api_key_rejects_revoked_env_key(monkeypatch):
    monkeypatch.setenv("API_KEYS", "new-key,old-key")
    monkeypatch.setenv("REVOKED_API_KEYS", "old-key")

    with pytest.raises(HTTPException) as exc:
        security.verify_api_key(build_request(), "old-key")
    assert exc.value.status_code == 401


def test_enforce_rate_limit_blocks_after_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    request = build_request()
    security.enforce_rate_limit(request)

    with pytest.raises(HTTPException) as exc:
        security.enforce_rate_limit(request)
    assert exc.value.status_code == 429


def test_enforce_rate_limit_resets_after_window(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "1")

    request = build_request()
    security.enforce_rate_limit(request)

    key = "127.0.0.1:/nl-query"
    request.app.state.rate_limit_store[key]["reset_at"] = 0

    security.enforce_rate_limit(request)


def test_enforce_rate_limit_increments_within_window(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "3")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    request = build_request()
    security.enforce_rate_limit(request)
    security.enforce_rate_limit(request)

    key = "127.0.0.1:/nl-query"
    assert request.app.state.rate_limit_store[key]["count"] == 2


def test_enforce_rate_limit_uses_redis_when_available(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    request = build_request()
    request.app.state.redis_client = FakeRedisClient()

    security.enforce_rate_limit(request)
    security.enforce_rate_limit(request)

    key = "rate_limit:127.0.0.1:/nl-query"
    assert request.app.state.redis_client.counts[key] == 2
    assert request.app.state.redis_client.ttls[key] == 60
    assert request.app.state.redis_degraded is False


def test_enforce_rate_limit_redis_blocks_after_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    request = build_request()
    request.app.state.redis_client = FakeRedisClient()

    security.enforce_rate_limit(request)

    with pytest.raises(HTTPException) as exc:
        security.enforce_rate_limit(request)
    assert exc.value.status_code == 429


def test_enforce_rate_limit_falls_back_when_redis_degraded(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    request = build_request()
    request.app.state.redis_client = FakeRedisClient(should_fail=True)

    security.enforce_rate_limit(request)
    security.enforce_rate_limit(request)

    with pytest.raises(HTTPException) as exc:
        security.enforce_rate_limit(request)
    assert exc.value.status_code == 429
    assert request.app.state.redis_degraded is True


def test_observability_adds_request_id_header_and_logs(monkeypatch, caplog):
    monkeypatch.delenv("SERVICE_NAME", raising=False)
    monkeypatch.setenv("LOG_HEALTH_REQUESTS", "false")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    app = FastAPI(title="Test Service")
    security.configure_observability(app)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)

    with caplog.at_level("INFO", logger=security.LOGGER_NAME):
        response = client.get("/ping", headers={security.REQUEST_ID_HEADER: "req-123"})

    assert response.status_code == 200
    assert response.headers[security.REQUEST_ID_HEADER] == "req-123"
    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "http_request"
    assert payload["request_id"] == "req-123"
    assert payload["path"] == "/ping"
    assert payload["status_code"] == 200
    assert payload["service"] == "Test Service"


def test_observability_redacts_sensitive_headers(monkeypatch, caplog):
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    app = FastAPI(title="Redaction Service")
    security.configure_observability(app)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)

    with caplog.at_level("INFO", logger=security.LOGGER_NAME):
        response = client.get(
            "/ping",
            headers={
                "Authorization": "Bearer super-secret-token",
                "X-API-Key": "my-api-key-value",
            },
        )

    assert response.status_code == 200
    payload = json.loads(caplog.records[-1].message)
    assert "authorization" in payload["header_names"]
    assert "x-api-key" in payload["header_names"]


def test_sanitize_request_id_accepts_valid_format():
    valid_id = "req-123-abc"
    assert security._sanitize_request_id(valid_id) == valid_id


def test_sanitize_request_id_generates_uuid_for_invalid():
    invalid_id = "req@@@<script>"
    result = security._sanitize_request_id(invalid_id)
    assert result != invalid_id
    assert len(result) == 36  # UUID format


def test_sanitize_request_id_truncates_long_ids():
    long_id = "a" * 100
    result = security._sanitize_request_id(long_id)
    assert len(result) <= 64


def test_sanitize_request_id_generates_uuid_for_none():
    result = security._sanitize_request_id(None)
    assert len(result) == 36


def test_observability_adds_security_headers(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    app = FastAPI(title="Security Headers")
    security.configure_observability(app)

    @app.get("/data")
    def get_data():
        return {"value": 42}

    client = TestClient(app)
    response = client.get("/data")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers


def test_enforce_rate_limit_blocks_burst_same_route(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    request = build_request(path="/api/data")
    security.enforce_rate_limit(request)
    security.enforce_rate_limit(request)

    with pytest.raises(HTTPException) as exc:
        security.enforce_rate_limit(request)
    assert exc.value.status_code == 429


def test_enforce_rate_limit_per_route_isolation(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    request_a = build_request(path="/api/a")
    request_b = build_request(path="/api/b")

    security.enforce_rate_limit(request_a)
    security.enforce_rate_limit(request_b)

    with pytest.raises(HTTPException) as exc:
        security.enforce_rate_limit(request_a)
    assert exc.value.status_code == 429


def test_enforce_rate_limit_different_paths_tracked_separately(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    request_path_a = build_request(path="/api/query")
    request_path_b = build_request(path="/api/other")

    security.enforce_rate_limit(request_path_a)

    with pytest.raises(HTTPException) as exc:
        security.enforce_rate_limit(request_path_a)
    assert exc.value.status_code == 429

    security.enforce_rate_limit(request_path_b)


def test_observability_skips_health_logs_by_default(monkeypatch, caplog):
    monkeypatch.setenv("LOG_HEALTH_REQUESTS", "false")

    app = FastAPI(title="Health Test")
    security.configure_observability(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    client = TestClient(app)
    caplog.clear()
    with caplog.at_level("INFO", logger=security.LOGGER_NAME):
        response = client.get("/health")

    assert response.status_code == 200
    assert len(caplog.records) == 0


def test_observability_logs_health_when_enabled(monkeypatch, caplog):
    monkeypatch.setenv("LOG_HEALTH_REQUESTS", "true")

    app = FastAPI(title="Health Logging")
    security.configure_observability(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    client = TestClient(app)

    with caplog.at_level("INFO", logger=security.LOGGER_NAME):
        response = client.get("/health")

    assert response.status_code == 200
    payload = json.loads(caplog.records[-1].message)
    assert payload["path"] == "/health"


def test_log_payload_header_names_is_a_list(monkeypatch, caplog):
    """header_names in the log payload must be a list, not a dict."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    app = FastAPI(title="HeaderList Test")
    security.configure_observability(app)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)
    with caplog.at_level("INFO", logger=security.LOGGER_NAME):
        response = client.get("/ping", headers={"X-Custom-Header": "some-value"})

    assert response.status_code == 200
    payload = json.loads(caplog.records[-1].message)
    assert isinstance(payload["header_names"], list)


def test_log_payload_header_names_sorted_alphabetically(monkeypatch, caplog):
    """header_names must be sorted alphabetically."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    app = FastAPI(title="Sorted Headers Test")
    security.configure_observability(app)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)
    with caplog.at_level("INFO", logger=security.LOGGER_NAME):
        response = client.get(
            "/ping",
            headers={
                "Z-Last-Header": "z-value",
                "A-First-Header": "a-value",
                "M-Middle-Header": "m-value",
            },
        )

    assert response.status_code == 200
    payload = json.loads(caplog.records[-1].message)
    header_names = payload["header_names"]
    assert header_names == sorted(header_names)


def test_log_payload_no_header_values_in_payload(monkeypatch, caplog):
    """Header values must not appear anywhere in the log payload."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    app = FastAPI(title="No Values Test")
    security.configure_observability(app)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)
    secret_value = "Bearer super-secret-token-12345"
    api_key_value = "my-very-secret-api-key"

    with caplog.at_level("INFO", logger=security.LOGGER_NAME):
        response = client.get(
            "/ping",
            headers={
                "Authorization": secret_value,
                "X-API-Key": api_key_value,
            },
        )

    assert response.status_code == 200
    raw_log = caplog.records[-1].message
    assert secret_value not in raw_log
    assert api_key_value not in raw_log


def test_log_payload_no_headers_key(monkeypatch, caplog):
    """The old 'headers' key must not be present in the log payload."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    app = FastAPI(title="No Headers Key Test")
    security.configure_observability(app)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)
    with caplog.at_level("INFO", logger=security.LOGGER_NAME):
        response = client.get("/ping", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    payload = json.loads(caplog.records[-1].message)
    assert "headers" not in payload
    assert "header_names" in payload


def test_log_payload_header_names_contains_sent_names(monkeypatch, caplog):
    """Non-sensitive header names must appear in header_names."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    app = FastAPI(title="Header Names Present")
    security.configure_observability(app)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)
    with caplog.at_level("INFO", logger=security.LOGGER_NAME):
        response = client.get(
            "/ping",
            headers={
                "X-Custom-Header": "value1",
                "Accept-Language": "en-US",
            },
        )

    assert response.status_code == 200
    payload = json.loads(caplog.records[-1].message)
    assert "x-custom-header" in payload["header_names"]
    assert "accept-language" in payload["header_names"]


def test_build_log_payload_header_names_directly():
    """Unit test for _build_log_payload: header_names is sorted keys of request headers."""
    headers = {"z-header": "z-val", "a-header": "a-val", "m-header": "m-val"}
    request = SimpleNamespace(
        client=SimpleNamespace(host="10.0.0.1"),
        headers=headers,
        method="GET",
        url=SimpleNamespace(path="/test"),
    )
    payload = security._build_log_payload(
        request=request,
        request_id="test-id",
        status_code=200,
        duration_ms=12.5,
        service_name="test-service",
    )
    assert payload["header_names"] == ["a-header", "m-header", "z-header"]
    assert "headers" not in payload


def test_build_log_payload_header_values_absent():
    """Unit test: header values must not appear in _build_log_payload output."""
    headers = {"authorization": "Bearer secret-token", "x-api-key": "sensitive-key"}
    request = SimpleNamespace(
        client=SimpleNamespace(host="10.0.0.1"),
        headers=headers,
        method="POST",
        url=SimpleNamespace(path="/data"),
    )
    payload = security._build_log_payload(
        request=request,
        request_id="req-abc",
        status_code=201,
        duration_ms=5.0,
        service_name="svc",
    )
    serialized = json.dumps(payload)
    assert "Bearer secret-token" not in serialized
    assert "sensitive-key" not in serialized
    assert "authorization" in payload["header_names"]
    assert "x-api-key" in payload["header_names"]


def test_build_log_payload_empty_headers():
    """Unit test: _build_log_payload with no request headers yields empty list."""
    request = SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers={},
        method="GET",
        url=SimpleNamespace(path="/empty"),
    )
    payload = security._build_log_payload(
        request=request,
        request_id="req-empty",
        status_code=200,
        duration_ms=1.0,
        service_name="svc",
    )
    assert payload["header_names"] == []
