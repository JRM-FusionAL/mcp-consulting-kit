FROM python:3.11-slim

WORKDIR /app

COPY social-poster-mcp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY social-poster-mcp/ .
COPY common/ ./common

ENV PORT=8105

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8105"]
