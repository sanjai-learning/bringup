#!/usr/bin/env bash

set -euo pipefail

repo_dir="${ZERODHA_REPO_DIR:-/opt/bringup}"
secret_file="${ZERODHA_SECRET_FILE:-/root/secret.txt}"
token_file="${ZERODHA_ACCESS_TOKEN_FILE:-/root/zerodha_access_token}"

if [[ ! -d "$repo_dir" ]]; then
  echo "Repository directory not found: $repo_dir" >&2
  exit 1
fi

if [[ ! -f "$secret_file" ]]; then
  echo "Secret file not found: $secret_file" >&2
  exit 1
fi

eval "$(python3 - "$secret_file" "$token_file" <<'PY'
from pathlib import Path
import shlex
import sys

secret_path = Path(sys.argv[1])
token_path = Path(sys.argv[2])

lines = [line.strip() for line in secret_path.read_text().splitlines() if line.strip()]
values = {}

if lines and all("=" in line for line in lines):
    for line in lines:
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
elif len(lines) >= 4:
    values["ZERODHA_API_KEY"] = lines[1]
    values["ZERODHA_API_SECRET"] = lines[3]

values.setdefault("ZERODHA_CLIENT_ID", "LI8768")

if token_path.exists():
    token = token_path.read_text().strip()
    if token:
        values["ZERODHA_ACCESS_TOKEN"] = token

required = ["ZERODHA_API_KEY", "ZERODHA_API_SECRET", "ZERODHA_CLIENT_ID"]
missing = [name for name in required if not values.get(name)]
if missing:
    raise SystemExit("Missing required secret values: " + ", ".join(missing))

for key, value in values.items():
    if value:
        print(f"export {key}={shlex.quote(value)}")
PY
)"

exec "$repo_dir/.venv/bin/python" "$repo_dir/mcp/zerodha_server.py"
