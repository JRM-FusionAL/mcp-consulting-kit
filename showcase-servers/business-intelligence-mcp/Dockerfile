FROM python:3.11-slim

WORKDIR /app

COPY business-intelligence-mcp/requirements.txt .
# Upgrade setuptools first so its vendored jaraco.context and wheel are patched
# (setuptools 79.0.1 vendors jaraco.context 5.3.0/wheel 0.45.1 → CVE-2026-23949/CVE-2026-24049)
RUN pip install --no-cache-dir "setuptools>=82.0.1" && \
    pip install --no-cache-dir -r requirements.txt

COPY common/ ./showcase_servers/common/
RUN touch ./showcase_servers/__init__.py
COPY business-intelligence-mcp/ .

ENV PORT=8101

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8101", "--forwarded-allow-ips", "*"]
