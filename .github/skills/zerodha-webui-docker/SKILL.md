---
name: zerodha-webui-docker
description: Deploy a Docker-based web UI for Zerodha account access with GitHub authentication and MCP-only backend calls.
---

# Zerodha Web UI via Docker

## Architecture
- FastAPI web UI inside Docker
- GitHub OAuth for user authentication
- Zerodha data accessed only through `mcp/zerodha_server.py`
- Docker bind mounts for `/root/secret.txt` and persisted access token data

## Local Build
```bash
cd /home/sass273491/delete/bringup
cp .env.web.example .env.web
docker compose build
docker compose up -d
```

## Required GitHub OAuth Settings
- Set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in `.env.web`
- Set `SESSION_SECRET` to a strong random value
- GitHub callback URL: `http://HOST:8000/auth/github/callback`

## Zerodha Settings
- Keep API key and secret in `/root/secret.txt` on the VM
- Configure Zerodha redirect URL to `http://HOST:8000/auth/zerodha/callback`
- Access token is stored in `./data/zerodha_access_token` on the VM host

## VM Deployment
```bash
cd /home/sass273491/delete/bringup
./scripts/install_docker_webui_vm.sh
```

## Guardrails
- Do not commit `.env.web`.
- Do not copy Zerodha secrets into repo files.
- The web app must call Zerodha only through MCP tools.
