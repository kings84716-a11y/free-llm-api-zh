#!/usr/bin/env bash
# 等 GitHub Pages 构建完成，成功后推送 TG 通知（最多等 90 分钟）
cd /home/ubuntu/free-api-hub
URL="https://kings84716-a11y.github.io/free-llm-api-zh/"
TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' /home/ubuntu/.hermes/.env | cut -d= -f2)
for i in $(seq 1 45); do
  code=$(curl -s -m20 -o /dev/null -w "%{http_code}" "$URL")
  if [ "$code" = "200" ]; then
    curl -s -m15 "https://api.telegram.org/bot${TOKEN}/sendMessage" \
      --data-urlencode "chat_id=6643416725" \
      --data-urlencode "text=✅ 免费API实测榜网站已上线: $URL" >/dev/null
    echo "$(date '+%F %T') LIVE $code"; exit 0
  fi
  sleep 120
done
curl -s -m15 "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  --data-urlencode "chat_id=6643416725" \
  --data-urlencode "text=⚠️ GitHub Pages 构建超时仍404，需手动检查: https://github.com/kings84716-a11y/free-llm-api-zh/settings/pages" >/dev/null
echo "timeout"
