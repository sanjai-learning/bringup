#!/usr/bin/env bash

set -euo pipefail

remote_host="${ZERODHA_VM_HOST:-root@203.57.85.108}"
remote_dir="${ZERODHA_REMOTE_DIR:-/opt/bringup}"
repo_url="${ZERODHA_REPO_URL:-https://github.com/sanjai-learning/bringup.git}"

ssh "$remote_host" "bash -s" -- "$remote_dir" "$repo_url" <<'REMOTE'
set -euo pipefail

remote_dir="$1"
repo_url="$2"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl git docker.io docker-compose-v2
systemctl enable --now docker

if [[ ! -d "$remote_dir/.git" ]]; then
  git clone "$repo_url" "$remote_dir"
else
  git -C "$remote_dir" pull --ff-only
fi

cd "$remote_dir"
mkdir -p data

if [[ ! -f .env.web ]]; then
  cp .env.web.example .env.web
  echo "Created $remote_dir/.env.web from template. Fill in GitHub OAuth credentials before using login." >&2
fi

docker compose build
docker compose up -d
docker compose ps
REMOTE

echo "Docker web UI deployment complete on $remote_host"
