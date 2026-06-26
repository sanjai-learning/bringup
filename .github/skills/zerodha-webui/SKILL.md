---
name: zerodha-webui
description: Run a containerized Zerodha web UI with GitHub authentication and MCP-only account access on Ubuntu using Docker Compose.
---

# Zerodha Web UI

## Architecture
- Web backend: FastAPI
- Authentication: GitHub OAuth
- Data source: Zerodha MCP tools only
- Runtime: Docker Compose

## Required Environment
- `ZERODHA_API_KEY`
- `ZERODHA_API_SECRET`
- `ZERODHA_CLIENT_ID`
- `ZERODHA_ACCESS_TOKEN`
- `SESSION_SECRET`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `GITHUB_CALLBACK_URL`

## Local Run
```bash
cd /home/sass273491/delete/bringup
cp .env.example .env
docker compose up --build
```

## VM Run
```bash
cd /home/sass273491/delete/bringup
./scripts/deploy_zerodha_mcp_vm.sh
./scripts/run_docker_vm.sh
```

## Notes
- The UI authenticates users with GitHub before loading Zerodha data.
- Account profile, margins, holdings, and positions are fetched through the MCP server, not by direct UI-to-broker calls.
- For production, register the GitHub OAuth callback URL to your public domain.
