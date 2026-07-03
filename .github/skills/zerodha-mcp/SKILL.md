---
name: zerodha-mcp
description: Configure and operate the Zerodha MCP platform server running as a Docker container with SSE transport on the production VM.
---

# Zerodha MCP Platform Server

## Architecture
- Server: `mcp/zerodha_server.py` using FastMCP
- Transport: SSE (Server-Sent Events) over HTTP on port 8000
- Container: `platform-mcp` Docker service
- Network: Internal Docker network only (not exposed to internet)
- Client ID: LI8768

## Docker Configuration
- Image built from `Dockerfile.mcp`
- Dependencies: `requirements-mcp.txt` (mcp, kiteconnect, uvicorn)
- Environment variables:
  - `MCP_TRANSPORT=sse`
  - `MCP_PORT=8000`
- Volumes:
  - `/root/secret.txt` → `/run/secrets/zerodha_secret.txt` (API key/secret)
  - `platform-data` → `/data` (persisted access token)

## Secret File Format (`/root/secret.txt` on VM)
```
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_api_secret
```
Alternative 4-line format:
```
API key
your_api_key
API secret
your_api_secret
```

## Available MCP Tools
| Tool | Purpose | Auth Required |
|------|---------|---------------|
| `zerodha_healthcheck` | Check config status | No |
| `zerodha_login_url` | Generate Kite login URL | No |
| `zerodha_exchange_request_token` | Exchange token + persist | No |
| `zerodha_profile` | Fetch user profile | Yes |
| `zerodha_margins` | Fetch account margins | Yes |
| `zerodha_holdings` | Fetch holdings | Yes |
| `zerodha_positions` | Fetch positions | Yes |
| `zerodha_quote` | Fetch symbol quote | Yes |

## Access Token
- Stored at `/data/zerodha_access_token` inside container (Docker volume)
- Expires daily at ~6 AM IST
- Auto-persisted by `zerodha_exchange_request_token` tool
- Can be refreshed via web UI Zerodha login flow

## Connecting as a Client

### From Python (via SSH tunnel)
```bash
# Open tunnel
ssh -L 8000:localhost:8000 -i ~/.ssh/github_learning root@203.57.85.108

# Run client
python client/zerodha_client.py profile
```

### From Web UI
The web-ui container connects internally: `http://platform-mcp:8000/sse`

### SSE Endpoint
```
http://platform-mcp:8000/sse  (internal)
http://localhost:8000/sse      (via SSH tunnel)
```

## Deployment
Automatic via GitHub Actions on push to main:
1. Build image → push to ghcr.io
2. Pull on VM → docker compose up

Manual:
```bash
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && git pull && docker compose build platform-mcp && docker compose up -d platform-mcp'
```

## Guardrails
- Never commit `.env` or secret files.
- Access token expires daily — refresh via web UI.
- All Zerodha API calls go through this MCP server — no direct broker access from web UI.
