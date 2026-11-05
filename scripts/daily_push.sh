#!/usr/bin/env bash
# 每日实测 + 重建站点 + 推送到 GitHub（US cron 调用，用仓库级 token）
set -euo pipefail
DIR="/home/ubuntu/free-api-hub"
cd "$DIR"

# 1. 跑实测引擎 + 新资源发现 + 生成站点
python3 scripts/probe.py
python3 scripts/discover.py
python3 scripts/build_site.py

# 2. 同步 site -> docs（Pages 从 /docs 发布）
mkdir -p docs
cp site/index.html site/data.json docs/

# 3. 提交推送（credential helper 用 .git/.freehub-cred）
export GIT_TERMINAL_PROMPT=0
git config credential.helper 'store --file=.git/.freehub-cred'
git add data site docs
if git diff --staged --quiet; then
  echo "$(date '+%F %T') 无变化"
  exit 0
fi
git -c user.name="kings84716-a11y" -c user.email="kings84716@gmail.com" \
    commit -m "chore: 每日实测 $(date -u +%F)"
git push origin main
echo "$(date '+%F %T') 已推送"
