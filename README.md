# MCP Consulting Kit

Three production-grade MCP servers + FusionAL execution engine. Done-for-you AI automation implementation service framework.

**Works on Windows, Linux, and macOS.**

---

## What's in here

| Server | Port | What it does |
|---|---|---|
| Business Intelligence MCP | 8101 | Natural language → SQL (PostgreSQL / MySQL / SQLite) |
| API Integration Hub | 8102 | Slack, GitHub, Stripe via natural language |
| Content Automation MCP | 8103 | Web scraping, RSS feeds, link extraction |
| FusionAL Execution Engine | 8009 | Dynamic code execution + MCP server registry |

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/TangMan69/mcp-consulting-kit
cd mcp-consulting-kit
```

### 2. Install dependencies

```bash
pip3 install fastapi uvicorn[standard] python-dotenv pydantic requests \
             beautifulsoup4 feedparser lxml sqlalchemy "mcp[cli]"
```

### 3. Configure

Copy `.env.example` to `.env` in each server directory and fill in your values:

```bash
cp showcase-servers/business-intelligence-mcp/.env.example showcase-servers/business-intelligence-mcp/.env
cp showcase-servers/api-integration-hub/.env.example showcase-servers/api-integration-hub/.env
cp showcase-servers/content-automation-mcp/.env.example showcase-servers/content-automation-mcp/.env
```

### 4. Launch

**Linux / macOS:**
```bash
chmod +x launch.sh
./launch.sh
```

**Windows:**
```cmd
launch-all-servers.bat
```

**Any platform (Python):**
```bash
python3 launch.py
```

### 5. Verify

```bash
curl http://localhost:8101/health
curl http://localhost:8102/health
curl http://localhost:8103/health
curl http://localhost:8009/health
```

All should return `{"status":"ok"}`.

---

## Architecture

```
Claude Desktop / Christopher / Any MCP client
        │
        │  MCP protocol (Streamable HTTP)
        ▼
  ┌─────────────────────────────────────┐
  │  Business Intelligence MCP  :8101   │  Natural language → SQL
  │  API Integration Hub        :8102   │  Slack / GitHub / Stripe
  │  Content Automation MCP     :8103   │  Scraping / RSS
  │  FusionAL Execution Engine  :8009   │  Dynamic code + registry
  └─────────────────────────────────────┘
```

Each server exposes:
- REST API endpoints
- MCP Streamable HTTP at `/mcp` (connect any MCP client)
- `/health` for monitoring

---

## Connecting to Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "business-intelligence": {
      "type": "streamable-http",
      "url": "http://localhost:8101/mcp"
    },
    "api-integration": {
      "type": "streamable-http",
      "url": "http://localhost:8102/mcp"
    },
    "content-automation": {
      "type": "streamable-http",
      "url": "http://localhost:8103/mcp"
    }
  }
}
```

**Config file locations:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

---

## API Key Rotation

```bash
# Rotate all keys across all .env files at once
python3 rotate_keys.py

# Dry run first
python3 rotate_keys.py --dry-run

# Rotate and restart servers
python3 rotate_keys.py --restart
```

---

## Security

- API key auth on all endpoints (`X-API-Key` header)
- Rate limiting (configurable via `.env`)
- Shared security module: `showcase-servers/common/security.py`
- See `showcase-servers/common/SECURITY-HARDENING.md`

---

## Consulting Service

This repo is the technical foundation for a done-for-you MCP implementation service.

- 📧 jonathanmelton004@gmail.com
- 📅 calendly.com/jonathanmelton004/30min
- 🔗 github.com/TangMan69/mcp-consulting-kit
