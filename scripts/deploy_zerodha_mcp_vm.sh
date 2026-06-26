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
apt-get install -y git python3 python3-venv python3-pip

if [[ ! -d "$remote_dir/.git" ]]; then
  git clone "$repo_url" "$remote_dir"
else
  git -C "$remote_dir" pull --ff-only
fi

cd "$remote_dir"
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m py_compile mcp/zerodha_server.py
bash -n scripts/zerodha_remote_mcp.sh
REMOTE

echo "VM deployment complete: $remote_host:$remote_dir"
