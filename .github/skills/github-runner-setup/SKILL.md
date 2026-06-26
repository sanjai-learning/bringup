---
name: github-runner-setup
description: Set up or reconfigure the self-hosted GitHub Actions runner for sanjai-learning/bringup on Ubuntu 24.04 using SSH and gh CLI.
---

# GitHub Runner Setup

## Scope
- Organization: sanjai-learning
- Repository: bringup
- Runner host: vm526300408.manageserver.in (203.57.85.108)
- Platform: Linux x64 (Ubuntu 24.04)

## Prerequisites
- `gh auth status` shows logged-in user with repo admin permissions.
- SSH key access to root@203.57.85.108 is working.
- Outbound internet access from VM to github.com is allowed.

## Setup Procedure
```bash
# 1) Generate repository registration token
TOKEN=$(gh api -X POST repos/sanjai-learning/bringup/actions/runners/registration-token --jq .token)

# 2) SSH and install/configure runner as a systemd service
ssh root@203.57.85.108 "bash -s" -- "$TOKEN" <<'REMOTE'
set -euo pipefail
RUNNER_TOKEN="$1"
export RUNNER_ALLOW_RUNASROOT=1
apt-get update -y
apt-get install -y curl tar jq ca-certificates
mkdir -p /opt/actions-runner
cd /opt/actions-runner
if [[ ! -f ./config.sh ]]; then
  VERSION=$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest | jq -r .tag_name | sed "s/^v//")
  URL="https://github.com/actions/runner/releases/download/v${VERSION}/actions-runner-linux-x64-${VERSION}.tar.gz"
  curl -fsSL -o actions-runner.tar.gz "$URL"
  tar xzf actions-runner.tar.gz
  rm -f actions-runner.tar.gz
fi
./config.sh --url https://github.com/sanjai-learning/bringup --token "$RUNNER_TOKEN" --unattended --name vm526300408 --labels self-hosted,linux,x64,vm526300408 --work _work --replace
./svc.sh install
./svc.sh start
REMOTE

# 3) Verify from GitHub API
gh api repos/sanjai-learning/bringup/actions/runners --jq '.runners[] | [.name,.status,.busy] | @tsv'
```

## Expected Result
- Runner `vm526300408` appears as `online` in repository settings.

## Security Notes
- Never commit tokens, passwords, private keys, or `.env` secrets.
- Registration tokens are short-lived and should be generated per run.
