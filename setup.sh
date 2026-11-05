#!/usr/bin/env bash
# ============================================================
# 免费大模型 API 一键接入助手
# 项目: free-llm-api-zh  |  每日实测: https://kings84716-a11y.github.io/free-llm-api-zh/
#
# 作用：引导你把【自己申请的免费 Key】填进 .env，并生成各客户端的接入配置。
# 本脚本不收集、不上传任何 Key，全部在你本地运行。
# 用法：bash setup.sh
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'; YEL='\033[0;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok(){ echo -e "${GREEN}✓${NC} $*"; }
info(){ echo -e "${CYAN}▸${NC} $*"; }
warn(){ echo -e "${YEL}!${NC} $*"; }

cd "$(dirname "$0")"
ENV_FILE="keys.env"
[ -f "$ENV_FILE" ] || cp keys.env.example "$ENV_FILE" 2>/dev/null || touch "$ENV_FILE"
chmod 600 "$ENV_FILE" 2>/dev/null || true

echo "================================================"
echo "  免费大模型 API 一键接入（Key 只存在你本机 $ENV_FILE）"
echo "  没有 Key 的平台直接回车跳过即可，填几个用几个"
echo "================================================"

ask(){
  local key="$1" label="$2" url="$3" cur
  cur=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2-)
  if [ -n "$cur" ]; then info "$label 已配置，回车保留"; fi
  echo "    申请地址: $url"
  read -r -p "    请粘贴 $label 的 Key（留空跳过）: " val
  if [ -n "$val" ]; then
    if grep -qE "^#?\s*${key}=" "$ENV_FILE"; then
      sed -i.bak -E "s|^#?\s*${key}=.*|${key}=${val}|" "$ENV_FILE"
    else
      echo "${key}=${val}" >> "$ENV_FILE"
    fi
    ok "$label 已保存"
  fi
}

ask GROQ_API_KEY        "Groq（1000次/天，免手机）"   "https://console.groq.com/keys"
ask GEMINI_API_KEY      "Google Gemini（额度最大）"  "https://aistudio.google.com/apikey"
ask NVIDIA_API_KEY      "NVIDIA NIM（45免费端点）"   "https://build.nvidia.com"
ask OPENROUTER_API_KEY  "OpenRouter（一个Key多模型）" "https://openrouter.ai/keys"
ask CF_API_TOKEN        "Cloudflare Token（1万/天）" "https://dash.cloudflare.com"
ask CF_ACCOUNT_ID       "Cloudflare Account ID"      "Cloudflare 控制台右侧"

echo
ok "配置完成，当前已启用的 Key："
grep -oE '^[A-Z_]+=' "$ENV_FILE" | sed 's/=//' | sed 's/^/   - /'
echo
info "下一步：运行每日实测  →  bash scripts/run_daily.sh"
info "查看榜单网站        →  浏览器打开 site/index.html"
echo
warn "提醒：$ENV_FILE 已在 .gitignore 中，不会被提交；请勿分享你的 Key。"
