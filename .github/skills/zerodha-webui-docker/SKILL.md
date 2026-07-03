---
name: zerodha-webui-docker
description: Docker Compose configuration and CI/CD pipeline for the Zerodha trading platform deployment.
---

# Docker & CI/CD Deployment

## Docker Compose Stack
File: `docker-compose.yml` at `/opt/bringup/` on VM

### Services
```yaml
caddy:         # TLS termination (ports 80, 443)
oauth2-proxy:  # GitHub OAuth gateway (port 4180 internal)
web-ui:        # FastAPI dashboard (port 3000 internal)
platform-mcp:  # MCP SSE server (port 8000 internal)
```

### Volumes
- `platform-data` — persists Zerodha access token
- `caddy-data` — persists TLS certificates
- `caddy-config` — Caddy configuration state

### Networks
- `platform` — internal bridge network connecting all services

## Dockerfiles
| File | Service | Base | Entrypoint |
|------|---------|------|------------|
| `Dockerfile.mcp` | platform-mcp | python:3.12-slim | `python mcp/zerodha_server.py` |
| `Dockerfile.web` | web-ui | python:3.12-slim | `uvicorn app.main:app --port 3000` |

## Caddyfile
```
vysale.duckdns.org {
    reverse_proxy oauth2-proxy:4180
}
```
Caddy auto-obtains and renews Let's Encrypt TLS certificates.

## CI/CD Pipeline
File: `.github/workflows/deploy.yml`

### Trigger
Push to `main` branch.

### Jobs
1. **build-and-push** (runs on `ubuntu-latest`):
   - Builds `platform-mcp` and `web-ui` images
   - Pushes to `ghcr.io/sanjai-learning/bringup/platform-mcp:latest`
   - Pushes to `ghcr.io/sanjai-learning/bringup/web-ui:latest`

2. **deploy** (runs on self-hosted runner `vm526300408`):
   - Pulls latest code to `/opt/bringup`
   - Builds containers from source
   - Runs `docker compose up -d --remove-orphans`
   - Verifies services are running

### Required Secrets
- `GITHUB_TOKEN` — auto-provided by Actions for ghcr.io push

### Required Files on VM
- `/opt/bringup/.env` — contains `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `OAUTH2_PROXY_COOKIE_SECRET`
- `/root/secret.txt` — Zerodha API key and secret

## Manual Deployment
```bash
# Full rebuild and restart
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && git pull && docker compose build && docker compose up -d --remove-orphans'

# Rebuild single service
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && git pull && docker compose build web-ui && docker compose up -d web-ui'

# View running containers
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose ps'

# Tail all logs
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose logs -f --tail=20'
```

## Production Override (optional)
`docker-compose.prod.yml` — pulls pre-built images from ghcr.io instead of building locally:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Environment Setup (one-time on VM)
```bash
# Create .env from template
cd /opt/bringup
cp .env.example .env
# Edit .env with real values:
#   GITHUB_CLIENT_ID=Ov23liX13xYWnY34sytH
#   GITHUB_CLIENT_SECRET=<your-secret>
#   OAUTH2_PROXY_COOKIE_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

## Guardrails
- Never commit `.env` file.
- The deploy workflow checks for `.env` existence before starting.
- Only port 80 and 443 are exposed to the internet (via Caddy).
- All internal services communicate over the Docker bridge network.
