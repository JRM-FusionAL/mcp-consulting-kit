# Multi-Client MCP Configuration
# FusionAL custom servers now support Streamable HTTP transport.
# Start servers first: cd mcp-consulting-kit && docker compose up
# Then configure whichever client you use below.

---

## Claude Desktop
**File:** `C:\Users\puddi\AppData\Roaming\Claude\claude_desktop_config.json`

Add these alongside the existing `fusional-gateway` entry:

```json
"business-intelligence-mcp": {
  "type": "streamable-http",
  "url": "http://localhost:8101/mcp"
},
"api-integration-hub": {
  "type": "streamable-http",
  "url": "http://localhost:8102/mcp"
},
"content-automation-mcp": {
  "type": "streamable-http",
  "url": "http://localhost:8103/mcp"
}
```

---

## Cursor
**File:** `%APPDATA%\Cursor\User\globalStorage\cursor-mcp.json`
Or per-project: `.cursor/mcp.json` in repo root.

```json
{
  "mcpServers": {
    "business-intelligence-mcp": {
      "type": "streamable-http",
      "url": "http://localhost:8101/mcp"
    },
    "api-integration-hub": {
      "type": "streamable-http",
      "url": "http://localhost:8102/mcp"
    },
    "content-automation-mcp": {
      "type": "streamable-http",
      "url": "http://localhost:8103/mcp"
    }
  }
}
```

---

## VSCode Copilot (v1.99+)
**File:** `.vscode/mcp.json` in workspace root.

```json
{
  "servers": {
    "business-intelligence-mcp": {
      "type": "http",
      "url": "http://localhost:8101/mcp"
    },
    "api-integration-hub": {
      "type": "http",
      "url": "http://localhost:8102/mcp"
    },
    "content-automation-mcp": {
      "type": "http",
      "url": "http://localhost:8103/mcp"
    }
  }
}
```

---

## Amazon Q CLI
**File:** `~/.aws/amazonq/mcp.json`

```json
{
  "mcpServers": {
    "business-intelligence-mcp": {
      "transport": "http",
      "url": "http://localhost:8101/mcp"
    },
    "api-integration-hub": {
      "transport": "http",
      "url": "http://localhost:8102/mcp"
    },
    "content-automation-mcp": {
      "transport": "http",
      "url": "http://localhost:8103/mcp"
    }
  }
}
```

---

## mcphost (Ollama / any local model)
No Claude subscription required. Works with Llama, Mistral, Qwen, Phi, Gemma.

**Install:**
```bash
go install github.com/mark3labs/mcphost@latest
```

**Config:** `~/.mcphost/config.json`
```json
{
  "mcpServers": {
    "business-intelligence-mcp": {
      "transport": "http",
      "url": "http://localhost:8101/mcp"
    },
    "api-integration-hub": {
      "transport": "http",
      "url": "http://localhost:8103/mcp"
    },
    "content-automation-mcp": {
      "transport": "http",
      "url": "http://localhost:8103/mcp"
    }
  }
}
```

**Run:**
```bash
# With Llama 3.2 (requires: ollama pull llama3.2)
mcphost --model ollama:llama3.2 --config ~/.mcphost/config.json

# With Mistral
mcphost --model ollama:mistral --config ~/.mcphost/config.json
```

---

## Remote Access (Cloudflare Tunnel)
Once you set up a Cloudflare Tunnel, replace `localhost` with your tunnel URL.
Example: `https://bi.yourtunnel.trycloudflare.com/mcp`
This enables clients to connect from anywhere without port forwarding.
