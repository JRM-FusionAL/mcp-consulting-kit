FROM python:3.11-slim

WORKDIR /app

COPY content-automation-mcp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ ./showcase_servers/common/
RUN touch ./showcase_servers/__init__.py
COPY content-automation-mcp/ .

ENV PORT=8103

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8103"]
