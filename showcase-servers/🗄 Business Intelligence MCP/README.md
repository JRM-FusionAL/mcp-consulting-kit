# Business Intelligence MCP

A production‑ready MCP server that converts natural‑language questions into SQL queries and executes them against PostgreSQL, MySQL, or SQLite databases.

## 🚀 Features

- Natural‑language → SQL using Claude (default provider)
- Rule‑based SQL fallback for common queries
- PostgreSQL, MySQL, and SQLite support via SQLAlchemy
- Schema exploration and table listing
- CSV‑style row output
- Fully Dockerized
- Claude Desktop MCP compatible

---

## 📦 Folder Structure

```
business-intelligence-mcp/
│
├── main.py
├── mcp_tools.py
├── llm_provider.py
├── db.py
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## ⚙️ Environment Variables

Create a `.env` file with:

```
DB_URL=postgresql+psycopg2://user:pass@host:5432/dbname
ANTHROPIC_API_KEY=your_api_key_here
API_KEY=your_shared_api_key_here
API_KEYS=next_key,current_key
REVOKED_API_KEYS=
ALLOWED_ORIGINS=http://localhost,http://127.0.0.1
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60
REDIS_URL=redis://localhost:6379/0
ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com
LOG_LEVEL=INFO
LOG_HEALTH_REQUESTS=false
SERVICE_NAME=Business Intelligence MCP
LLM_PROVIDER=claude
PORT=8101
```

Supported `LLM_PROVIDER` values:

- `claude` (default)
- `rule`
- `local` (placeholder for your future local model)

---

## 🏃 Run Locally

### **1. Install dependencies**

```bash
pip install -r requirements.txt
```

### **2. Start the server**

```bash
uvicorn main:app --host 0.0.0.0 --port 8101
```

---

## 🐳 Run with Docker

```bash
docker build -t bi-mcp-showcase .
docker run --env-file .env -p 8101:8101 bi-mcp-showcase
```

---

## 🔌 MCP Endpoints

### **POST /nl-query**

Convert natural language into SQL and execute it.

Requires header:

```
X-API-Key: <API_KEY>
```

**Request:**

```json
{
  "query": "show me the top 10 customers by revenue",
  "schema_hint": "customers(id, name, revenue)"
}
```

**Response:**

```json
{
  "sql": "SELECT ...",
  "rows": [...]
}
```

Response header includes `X-Request-ID` for tracing.

### **GET /health**

Simple health check.

---

## 🧠 Example Prompts (Claude Desktop)

Ask Claude:

- “List all tables in the database.”
- “Show me total revenue by month for 2024.”
- “Which customers churned last quarter?”
- “Give me the top 5 products by sales volume.”

---

## 🛠 Tech Stack

- FastAPI
- SQLAlchemy
- Anthropic Claude API
- Docker
- Python 3.11

---

## 📘 Notes

- The SQL generator is provider‑agnostic and can be swapped to your local model later.
- The rule‑based fallback handles simple queries without LLM usage.
- Request logs apply structured sensitive-field redaction (for auth/token/API key style fields).
- For P1 hardening (key rotation/revocation, Redis behavior), see `../common/SECURITY-HARDENING.md`.
- All responses include security headers (CSP, X-Frame-Options, etc.) and strict CORS validation.
- Request IDs are validated/sanitized; malformed IDs generate UUIDs automatically.
- For P2 hardening details (CORS, headers, request ID, auth migration plan), see `../common/P2-HARDENING.md`.

---

## 📄 License

MIT License
