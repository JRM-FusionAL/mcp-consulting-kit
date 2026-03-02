# Contributing to MCP Consulting Kit

Thanks for helping improve this project.

## Development Setup

1. Clone and enter the repo:
   - `git clone https://github.com/TangMan69/mcp-consulting-kit.git`
   - `cd mcp-consulting-kit`
2. Install dependencies (example):
   - `pip install fastapi uvicorn[standard] python-dotenv pydantic requests beautifulsoup4 feedparser lxml sqlalchemy "mcp[cli]"`
3. Configure local env files from examples:
   - `cp showcase-servers/business-intelligence-mcp/.env.example showcase-servers/business-intelligence-mcp/.env`
   - `cp showcase-servers/api-integration-hub/.env.example showcase-servers/api-integration-hub/.env`
   - `cp showcase-servers/content-automation-mcp/.env.example showcase-servers/content-automation-mcp/.env`
4. Start services:
   - Linux/macOS: `./launch.sh`
   - Windows: `launch-all-servers.bat`
   - Python: `python launch.py`

## Branch and PR Workflow

- Branch from `main`.
- Keep changes focused and easy to review.
- Use descriptive commit messages (`fix:`, `feat:`, `docs:`).
- Include test/verification notes in PR descriptions.

## Contribution Rules

- Do not commit secrets, `.env`, or API credentials.
- Keep server-specific changes isolated when possible.
- Update docs when behavior or setup changes.

## Testing

- Validate relevant health endpoints and changed functionality.
- Add/adjust tests when practical.

## Reporting Issues

Please use the issue templates for bug reports and feature requests.
