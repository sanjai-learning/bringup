---
name: hosting-info
description: Reference non-sensitive production host information and safe SSH usage steps for the bringup environment.
---

# Hosting Info (Non-Sensitive)

## Server Profile
- Hostname: vm526300408.manageserver.in
- IP address: 203.57.85.108
- Domain: vysale.duckdns.org (HTTPS via Let's Encrypt + Caddy)
- OS: Ubuntu 24.04
- Admin user: root

## Ports
- 22: SSH (externally accessible)
- 80: Caddy HTTP (redirects to HTTPS)
- 443: Caddy HTTPS → OAuth2 Proxy → Web UI
- 8000: MCP SSE server (internal Docker network only)
- 3000: Web UI (internal Docker network only)
- 4180: OAuth2 Proxy (internal Docker network only)

## Access Notes
- SSH key authentication is configured and working.
- Only ports 22, 80, 443 are externally reachable.
- Port 2016 and 8000 are blocked by hosting provider firewall.
- Do not store passwords, tokens, or private keys in this repository.

## DNS
- vysale.duckdns.org → 203.57.85.108 (DuckDNS, free)
- TLS certificate: auto-managed by Caddy via Let's Encrypt

## Common Commands
```bash
# Verify SSH access with key auth
ssh -i ~/.ssh/github_learning root@203.57.85.108

# Quick connectivity check
ssh -i ~/.ssh/github_learning -o BatchMode=yes -o ConnectTimeout=10 root@203.57.85.108 'echo SSH_KEY_OK'

# Check running services
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose ps'

# View logs
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose logs --tail=20'

# Restart all services
ssh -i ~/.ssh/github_learning root@203.57.85.108 'cd /opt/bringup && docker compose restart'
```

## Safety Guardrails
- Prefer key-based authentication over password login.
- Rotate credentials immediately if secrets are exposed.
- Keep firewall rules and SSH hardening settings reviewed regularly.
