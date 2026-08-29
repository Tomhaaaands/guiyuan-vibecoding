#!/usr/bin/env sh
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "[error] python3 not found. Install Python 3.11+ first."
  exit 1
fi
exec python3 tools/one_click_install.py "$@"
