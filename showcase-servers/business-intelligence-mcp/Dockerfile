FROM python:3.11-slim

WORKDIR /app

COPY business-intelligence-mcp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ ./showcase_servers/common/
RUN touch ./showcase_servers/__init__.py
COPY business-intelligence-mcp/ .

ENV PORT=8101

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8101"]
