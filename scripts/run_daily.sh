#!/usr/bin/env bash
# 每日实测 + 重建站点。crontab 或 GitHub Actions 调用。
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"
python3 scripts/probe.py
python3 scripts/build_site.py
echo "[$(date '+%F %T')] data + site updated"
