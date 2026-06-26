---
name: zerodha-mcp
description: Configure and run a Zerodha MCP server for client LI8768 using VM-hosted secrets, SSH transport, and safe token rotation.
---

# Zerodha MCP

## Scope
- Client ID: LI8768
- Transport: stdio
- Server entrypoint: mcp/zerodha_server.py
- Default MCP target: remote VM via SSH

## Repo Setup
```bash
cd /home/sass273491/delete/bringup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## VM Deployment
```bash
cd /home/sass273491/delete/bringup
./scripts/deploy_zerodha_mcp_vm.sh
```

## VS Code MCP Usage
- The default MCP server in `.vscode/mcp.json` connects over SSH to `root@203.57.85.108`.
- Secrets stay on the VM in `/root/secret.txt`.
- Optional local fallback server remains available as `zerodha-local`.

## Remote Secret Requirements
- `/root/secret.txt` may be either `KEY=value` lines or a 4-line label/value format.
- Supported variables are `ZERODHA_API_KEY`, `ZERODHA_API_SECRET`, `ZERODHA_CLIENT_ID`, and `ZERODHA_ACCESS_TOKEN`.
- If `ZERODHA_CLIENT_ID` is absent, the launcher defaults to `LI8768`.
- If `/root/zerodha_access_token` exists, it is loaded automatically.

## Remote Run Command
```bash
ssh root@203.57.85.108 /opt/bringup/scripts/zerodha_remote_mcp.sh
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

## Access Token Rotation
```bash
# Save a fresh daily access token on the VM after exchanging the request token
ssh root@203.57.85.108 "printf '%s\n' 'NEW_ACCESS_TOKEN' > /root/zerodha_access_token"
```

## Guardrails
- Never commit `.env` or secret files.
- Rotate `ZERODHA_ACCESS_TOKEN` when it expires.
- Keep API key/secret only in secure host-local storage.

