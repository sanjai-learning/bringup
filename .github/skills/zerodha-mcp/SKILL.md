---
name: zerodha-mcp
description: Configure and run a Zerodha MCP server for client LI8768 with environment-based secrets and safe token rotation.
---

# Zerodha MCP

## Scope
- Client ID: LI8768
- Transport: stdio
- Server entrypoint: mcp/zerodha_server.py

## Local Setup
```bash
cd /home/sass273491/delete/bringup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Runtime Environment
- `ZERODHA_API_KEY`
- `ZERODHA_API_SECRET`
- `ZERODHA_CLIENT_ID` (default `LI8768`)
- `ZERODHA_ACCESS_TOKEN` (daily token after login)

## Run Server
```bash
cd /home/sass273491/delete/bringup
source .venv/bin/activate
set -a && source .env && set +a
python mcp/zerodha_server.py
```

## Available MCP Tools
- `zerodha_healthcheck`
- `zerodha_login_url`
- `zerodha_exchange_request_token`
- `zerodha_profile`
- `zerodha_margins`
- `zerodha_holdings`
- `zerodha_positions`
- `zerodha_quote`

## VM Secret Flow (No Plaintext in Git)
```bash
# Pull values from the VM secret file and map to local env without committing them
ssh root@203.57.85.108 'cat ~/secret.txt'
```

## Guardrails
- Never commit `.env` or secret files.
- Rotate `ZERODHA_ACCESS_TOKEN` when it expires.
- Keep API key/secret only in secure host-local storage.
