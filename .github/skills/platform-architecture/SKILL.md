---
name: platform-architecture
description: Overall architecture of the Vysale trading platform — components, data flow, client access patterns, and configuration.
---

# Vysale Trading Platform Architecture

## Overview
A centralized trading platform server running on a VM, exposing Zerodha account data via MCP (Model Context Protocol) over SSE. Authenticated access through GitHub OAuth (web) and SSH tunnel (CLI).

## System Diagram
```
┌─────────────────────────────────────────────────────────┐
│  VM: 203.57.85.108 (vysale.duckdns.org)                 │
│                                                         │
│  ┌─────────┐   ┌──────────────┐   ┌─────────┐         │
│  │  Caddy  │──▶│ OAuth2 Proxy │──▶│ Web UI  │         │
│  │ :80/443 │   │    :4180     │   │  :3000  │         │
│  └─────────┘   └──────────────┘   └────┬────┘         │
│                                         │ MCP SSE      │
│                                    ┌────▼────┐         │
│                                    │ MCP Srv │         │
│                                    │  :8000  │         │
│                                    └────┬────┘         │
│                                         │              │
│                                    Zerodha API         │
└─────────────────────────────────────────────────────────┘

Clients:
  • Browser → https://vysale.duckdns.org (GitHub OAuth)
  • Python CLI → SSH tunnel → localhost:8000/sse
  • AI Agent → SSH tunnel → MCP SSE
```

## Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Caddy | caddy:2 | HTTPS termination, auto Let's Encrypt |
| OAuth2 Proxy | oauth2-proxy:v7.7.1 | GitHub OAuth gateway |
| Web UI | FastAPI + Jinja2 | Human-readable dashboard |
| MCP Server | FastMCP (Python) + SSE | Broker API abstraction |
| CI/CD | GitHub Actions | Auto-deploy on push to main |
| Runner | Self-hosted on VM | Executes deploy job |

## Key Decisions
- **Single user**: Only `sanjaiAI` GitHub account can access
- **Read-only**: No order placement (profile, margins, holdings, positions, quotes)
- **Zerodha only**: No multi-broker abstraction
- **MCP as protocol**: All broker data flows through MCP — enables AI agent access
- **SSE transport**: HTTP-based, works through proxies and firewalls
- **OAuth2 Proxy**: Auth is decoupled from the application — web UI trusts forwarded headers

## Repository Structure
```
├── app/
│   ├── main.py              # FastAPI web UI (MCP SSE client)
│   ├── templates/index.html # Dashboard template
│   └── static/styles.css    # Dashboard styles
├── mcp/
│   └── zerodha_server.py    # MCP server (SSE transport)
├── client/
│   └── zerodha_client.py    # Python CLI client
├── Dockerfile.mcp           # MCP server container
├── Dockerfile.web           # Web UI container
├── Caddyfile                # Caddy reverse proxy config
├── docker-compose.yml       # Full stack definition
├── docker-compose.prod.yml  # Production override (ghcr.io images)
├── .github/workflows/
│   ├── deploy.yml           # CI/CD pipeline
│   └── server-info.yml      # VM diagnostics
└── .env.example             # Environment template
```

## Access Patterns

### Web Browser (human)
1. Visit https://vysale.duckdns.org
2. Authenticate via GitHub OAuth
3. View dashboard with account details
4. Zerodha login for daily token refresh

### Python CLI (developer)
```bash
ssh -L 8000:localhost:8000 -i ~/.ssh/github_learning root@203.57.85.108
python client/zerodha_client.py profile
```

### AI Agent (Claude Desktop, Copilot, etc.)
Connect MCP client to `http://localhost:8000/sse` via SSH tunnel.
All standard MCP tools are available.

## Daily Operations
- **Zerodha token expires** at ~6 AM IST daily
- **Refresh**: Visit web UI → click "Login to Zerodha" → enter credentials → auto-redirects back
- **CI/CD**: Push to main → auto-deploys in ~60 seconds
- **Monitoring**: `docker compose logs` on VM

## Security Model
- HTTPS everywhere (Caddy + Let's Encrypt)
- GitHub OAuth restricts access to single user
- Secrets stored only on VM (`/root/secret.txt`, `/opt/bringup/.env`)
- SSH key auth for CLI/admin access
- MCP server not exposed to internet (internal Docker network only)
- OAuth2 Proxy cookie: secure, httponly, 7-day expiry
