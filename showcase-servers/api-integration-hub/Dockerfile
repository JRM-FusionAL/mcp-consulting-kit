FROM python:3.11-slim

WORKDIR /app

COPY api-integration-hub/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ ./showcase_servers/common/
RUN touch ./showcase_servers/__init__.py
COPY api-integration-hub/ .

ENV PORT=8102

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8102", "--forwarded-allow-ips", "*"]
