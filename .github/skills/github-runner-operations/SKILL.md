---
name: github-runner-operations
description: Operate and troubleshoot the self-hosted runner service for sanjai-learning/bringup on vm526300408.
---

# GitHub Runner Operations

## Service Commands (on VM)
```bash
# Check service status
systemctl status actions.runner.sanjai-learning-bringup.vm526300408.service

# Restart service
systemctl restart actions.runner.sanjai-learning-bringup.vm526300408.service

# Tail logs
journalctl -u actions.runner.sanjai-learning-bringup.vm526300408.service -n 200 --no-pager
journalctl -u actions.runner.sanjai-learning-bringup.vm526300408.service -f
```

## Runner Binary Location
- `/opt/actions-runner`

## GitHub Visibility Checks
```bash
# From local machine with gh auth
gh api repos/sanjai-learning/bringup/actions/runners --jq '.runners[] | [.name,.status,.busy] | @tsv'
```

## Re-Registration (if offline/stale)
```bash
TOKEN=$(gh api -X POST repos/sanjai-learning/bringup/actions/runners/registration-token --jq .token)
ssh root@203.57.85.108 "cd /opt/actions-runner && RUNNER_ALLOW_RUNASROOT=1 ./config.sh --url https://github.com/sanjai-learning/bringup --token $TOKEN --unattended --name vm526300408 --labels self-hosted,linux,x64,vm526300408 --work _work --replace && ./svc.sh restart"
```

## Troubleshooting Tips
- If status is `offline`, restart the systemd service and inspect journal logs.
- If token errors occur, generate a fresh registration token.
- Ensure VM clock is correct (`timedatectl`) and DNS/network can reach github.com.
