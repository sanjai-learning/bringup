---
name: hosting-info
description: Reference non-sensitive production host information and safe SSH usage steps for the bringup environment.
---

# Hosting Info (Non-Sensitive)

## Server Profile
- Hostname: vm526300408.manageserver.in
- IP address: 203.57.85.108
- OS: Ubuntu 24.04
- Admin user: root

## Access Notes
- SSH key authentication is configured and working.
- Do not store passwords, tokens, or private keys in this repository.

## Common Commands
```bash
# Verify SSH access with key auth
ssh root@203.57.85.108

# Quick connectivity check
ssh -o BatchMode=yes -o ConnectTimeout=10 root@203.57.85.108 'echo SSH_KEY_OK'
```

## Safety Guardrails
- Prefer key-based authentication over password login.
- Rotate credentials immediately if secrets are exposed.
- Keep firewall rules and SSH hardening settings reviewed regularly.
