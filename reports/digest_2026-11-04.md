# 全网免费 AI API 日报 · 2026-11-04

> 自动巡检生成｜自用选模型 & 视频素材｜数据来自 OpenRouter 实时目录 + ClawLabs 健康库 + 平台实测

## 📊 今日速览

- 收录平台：**15** 个（另有已失效/改收费 4 个单独标注）
- OpenRouter 免费模型：**18** 个（新增 0 / 下架 0）
- ClawLabs 健康库更新：2026-11-03
- 已配置 key 实测：OPENROUTER_API_KEY
- OpenRouter 今日免费请求：**3/1000**

## 🏆 平台推荐排序（按免费力度+易用）

### 🟢 第一梯队（额度大、不要卡、优先注册）

- 🟢 **OpenRouter 免费模型** [✅已接] — 每账户所有 :free 模型共享 50 RPD；累计充值$10后 1000 RPD
  - 注册: https://openrouter.ai/keys（Google/GitHub/邮箱）
  - base_url: `https://openrouter.ai/api/v1`
  - ⚠️ 免费共享池常429，要fallback
- 🔐 **Groq** [🔑待注册] — 主力模型 1000 RPD；小模型(Llama 8B等) 14400 RPD，30 RPM
  - 注册: https://console.groq.com/keys（邮箱/Google/GitHub，不要手机）
  - base_url: `https://api.groq.com/openai/v1`
  - ⚠️ 协议禁止多账号；Mac直连403需走代理
- ⚪ **Cloudflare Workers AI** [🔑待注册] — 10000 Neurons/天，模型最全
  - 注册: https://dash.cloudflare.com（邮箱注册CF账号）
  - base_url: `https://api.cloudflare.com/client/v4/accounts/{account_id}/ai`
  - ⚠️ 非标准OpenAI端点，需account_id，可用LiteLLM转换
- ⚪ **Google AI Studio (Gemini)** [🔑待注册] — Flash-Lite 1000 RPD / Flash 250 RPD / Pro 50 RPD，额度最大
  - 注册: https://aistudio.google.com/apikey（必须Google账号OAuth）
  - base_url: `https://generativelanguage.googleapis.com/v1beta/openai`
  - ⚠️ Google反批量最强，一账号；地区限制
- 🔐 **Cerebras** [🔑待注册] — 30 RPM，900请求/小时，14400 RPD，1M token/天，速度极快
  - 注册: https://cloud.cerebras.ai（邮箱/Google）
  - base_url: `https://api.cerebras.ai/v1`
  - ⚠️ Free Trial定位，政策可能变

### 🟡 第二梯队（实用/国内直连）

- 🟢 **魔搭 ModelScope** [🔑待注册] — 60+免费模型，每日免费调用(早期2000/天)
  - 注册: https://www.modelscope.cn/my/myaccesstoken（手机/GitHub/支付宝）
  - base_url: `https://api-inference.modelscope.cn/v1`
  - ⚠️ 国内直连快
- 🔴 **AMD Token Factory** [🔑待注册] — 积分软限流，并发>5排队，不耗GPU额度
  - 注册: https://www.amd.com/en/developer/resources/instinct-developer-hub/token-factory.html（邮箱注册AMD开发者）
  - base_url: `https://user-icb-api-singapore-fma2.amd.com/v1`
  - ⚠️ 官方调试定位，可能随时撤
- 🔐 **硅基流动 SiliconFlow** [🔑待注册] — Qwen3-8B等标免费模型 1000 RPM/50K TPM，长期；注册另送额度
  - 注册: https://cloud.siliconflow.cn/account/ak（手机号(国内实名)）
  - base_url: `https://api.siliconflow.cn/v1`
  - ⚠️ 国内直连，部分模型收费要看标
- 🟢 **NVIDIA NIM** [🔑待注册] — 40 RPM，按模型限速，评估用途
  - 注册: https://build.nvidia.com（邮箱+手机短信）
  - base_url: `https://integrate.api.nvidia.com/v1`
  - ⚠️ 要手机验证

### ⚪ 第三梯队（额度小/有门槛/备用）

- 🔐 **Cohere 官方** [🔑待注册] — 20 RPM，1000次/月(按月，非天)
  - 注册: https://dashboard.cohere.com/api-keys（邮箱/Google/GitHub）
  - base_url: `https://api.cohere.com/compatibility/v1`
  - ⚠️ 月额度小
- 🟢 **SambaNova Cloud** [🔑待注册] — 免费档极小:20 RPM, 20 RPD, 200K TPD
  - 注册: https://cloud.sambanova.ai（邮箱/Google）
  - base_url: `https://api.sambanova.ai/v1`
  - ⚠️ 免费档基本不够用
- 🔐 **Mistral La Plateforme** [🔑待注册] — 1 RPS，实验用量限速紧，须同意数据训练
  - 注册: https://console.mistral.ai/api-keys（邮箱+强制手机验证）
  - base_url: `https://api.mistral.ai/v1`
  - ⚠️ 要手机+数据训练授权
- 🔐 **阿里百炼 DashScope** [🔑待注册] — 新用户每模型约100万token(一次性)，部分模型长期免费
  - 注册: https://bailian.console.aliyun.com/?apiKey=1（阿里云手机+实名）
  - base_url: `https://dashscope.aliyuncs.com/compatible-mode/v1`
  - ⚠️ 赠送额度多为一次性
- 🔐 **智谱 BigModel** [🔑待注册] — 实名送约2000万token(一次性)，GLM-Flash系列长期免费限速
  - 注册: https://open.bigmodel.cn/usercenter/apikeys（手机+身份证实名）
  - base_url: `https://open.bigmodel.cn/api/paas/v4`
  - ⚠️ 要身份证实名
- 🟢 **Pollinations.ai** [🆓无需key] — 免费无限但限速/不稳定
  - 注册: https://pollinations.ai（完全无需注册/key）
  - base_url: `https://text.pollinations.ai/openai`
  - ⚠️ 无SLA，玩具/备用，不能当生产依赖

## 💚 当前健康的 OpenRouter 免费模型

| 模型 | 上下文 | 限速 | 数据训练 | 模态 |
|---|---|---|---|---|
| `cohere/north-mini-code:free` | 256000 | 20 RPM · 50 RPD | no-training | text |
| `dots-studio/dots-3-note-preview:free` | 512000 | 20 RPM · 50 RPD | no-training | text,image |
| `google/gemma-4-31b-it:free` | 262144 | 20 RPM · 50 RPD | no-training | image,text,video |
| `xingchen-agi/xing4.0-29b-a4b:free` | 262144 | 20 RPM · 50 RPD | no-training | text |

## 🪦 已失效/改收费（别再推荐）

- ~~Together AI~~ — 2025-07起强制最低$5-15充值，无免费层
- ~~Fireworks AI~~ — 试用额度基本要卡
- ~~HuggingFace Inference~~ — 2026改充值制，免费仅$0.10/月
- ~~Lepton/Novita/Baseten/Hyperbolic~~ — 仅一次性赠送信用($10/$100/$30/$5)，非持续免费
