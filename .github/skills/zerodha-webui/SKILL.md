---
name: zerodha-webui
description: Operate the Zerodha trading platform web dashboard with GitHub OAuth (via OAuth2 Proxy), Caddy HTTPS, and MCP-backed data access.
---

# Zerodha Web Dashboard

## Architecture
```
Browser → Caddy (HTTPS/443) → OAuth2 Proxy (4180) → Web UI (3000) → MCP Server (8000) → Zerodha API
```

### Components (single docker-compose stack)
| Container | Image | Port | Role |
|-----------|-------|------|------|
| caddy | caddy:2 | 80, 443 | TLS termination, reverse proxy |
| oauth2-proxy | oauth2-proxy:v7.7.1 | 4180 | GitHub authentication gateway |
| web-ui | bringup-web-ui | 3000 | FastAPI dashboard |
| platform-mcp | bringup-platform-mcp | 8000 | MCP SSE server (Zerodha tools) |

## URL
- Production: https://vysale.duckdns.org
- After GitHub login → shows Zerodha account dashboard

## Authentication
- Provider: GitHub OAuth (via OAuth2 Proxy)
- Allowed user: `sanjaiAI` only
- OAuth App callback URL: `https://vysale.duckdns.org/oauth2/callback`
- Session cookie: 7-day expiry, secure (HTTPS only)
- Web UI reads user identity from `X-Forwarded-User` / `X-Forwarded-Email` headers

## Zerodha Login Flow
1. User visits https://vysale.duckdns.org → GitHub OAuth login
2. Dashboard shows "Connect Zerodha" if no access token
3. Click "Login to Zerodha" → Kite Connect login page
4. After Zerodha login → redirects to `https://vysale.duckdns.org/auth/zerodha/callback`
5. Token exchanged automatically → account details displayed

### Zerodha App Settings (developers.kite.trade)
- Redirect URL: `https://vysale.duckdns.org/auth/zerodha/callback`
- Client ID: LI8768
- Status: Active

## Environment Files
- `.env` (on VM at `/opt/bringup/.env`, gitignored):
  ```
  GITHUB_CLIENT_ID=Ov23liX13xYWnY34sytH
  GITHUB_CLIENT_SECRET=<secret>
  OAUTH2_PROXY_COOKIE_SECRET=<generated>
  ```
- `.env.mcp` (committed, no secrets — template for overrides)

## Dashboard Features
- Profile: name, email, broker, exchanges
- Margins: available balance, used, net (₹ formatted)
- Holdings: table with symbol, qty, avg price, LTP, value, P&L, % change
- Positions: table with open positions and P&L
- Color-coded: green for profit, red for loss

## Web UI Technical Details
- Framework: FastAPI + Jinja2
- MCP Client: `mcp.client.sse.sse_client` connecting to `http://platform-mcp:8000/sse`
- No direct Zerodha API calls — all data via MCP tools
- No session middleware — auth handled entirely by OAuth2 Proxy upstream

## Deployment
Automatic: push to `main` → GitHub Actions → build → deploy on VM

Manual:
```bash
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && git pull && docker compose build web-ui && docker compose up -d'
```

## Troubleshooting
```bash
# Check all services
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose ps'

# Check OAuth2 Proxy logs (login issues)
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose logs oauth2-proxy --tail=20'

# Check web-ui logs (rendering issues)
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose logs web-ui --tail=20'

# Check MCP server logs (Zerodha API issues)
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose logs platform-mcp --tail=20'

# Check Caddy logs (TLS/proxy issues)
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose logs caddy --tail=20'

# Restart everything
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose restart'
```

## Guardrails
- Never commit `.env` with OAuth secrets.
- Only `sanjaiAI` GitHub user can access the dashboard.
- All Zerodha data flows exclusively through MCP — no direct API calls in web UI.
- Access token expires daily (~6 AM IST) — re-login via Zerodha required.
