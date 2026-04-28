FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8105

COPY github-mcp-safe/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ ./common/
COPY github-mcp-safe/ .

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8105
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8105", "--forwarded-allow-ips", "*"]
