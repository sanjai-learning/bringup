#!/usr/bin/env bash

set -euo pipefail

remote_host="${ZERODHA_VM_HOST:-root@203.57.85.108}"
remote_dir="${ZERODHA_REMOTE_DIR:-/opt/bringup}"

ssh "$remote_host" "bash -s" -- "$remote_dir" <<'REMOTE'
set -euo pipefail

remote_dir="$1"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl

if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

cd "$remote_dir"
docker compose build
docker compose up -d
docker compose ps
REMOTE
