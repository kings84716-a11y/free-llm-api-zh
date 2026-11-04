# 🆓 免费大模型 API 实测榜

> **每天用真实请求实测全网免费 LLM/AI API：谁还活着、免费额度多少、谁偷偷改收费了。**
> 不是抄文档的静态列表——每个平台每天真实发请求验证，数据带实测时间戳和延迟。

![更新](https://img.shields.io/badge/每日-自动更新-brightgreen) ![语言](https://img.shields.io/badge/语言-中文-red) ![成本](https://img.shields.io/badge/API-免费-success)

## 这是什么

网上"免费 API 大全"很多，但都是人工抄文档、发完就过期、英文、不告诉你现在到底还能不能用。

本项目做三件别人懒得做的事：

1. **每日实测**：对每个平台的端点真实发请求（有 Key 的直接跑一次推理），输出 🟢实测可用 / 🔵端点在线 / 🔴无法访问
2. **额度情报**：免费额度、是否要信用卡、是否要实名、按天还是一次性赠送、OpenAI 兼容地址
3. **变更追踪**：谁新开放免费、谁改收费、谁下架（历史快照存 `data/history/`）

## 榜单

👉 **打开 [站点首页](site/index.html)**（`site/index.html`，可直接部署 GitHub Pages）

- 平台榜单（状态灯 + 免费额度 + 注册链接 + base_url + 实测延迟）
- OpenRouter 免费模型实时列表
- ClawLabs 健康模型（含限速、是否拿数据训练）
- 已失效/改收费平台黑名单（避免浪费时间）

## 自己跑

```bash
# 无需任何 Key 即可探活；有 Key 会做真实推理验证
python3 scripts/probe.py        # 实测 -> data/
python3 scripts/build_site.py   # 渲染 -> site/index.html
# 或一键
bash scripts/run_daily.sh
```

### 可选：配置你自己的 Key 做真实验证

复制 `keys.env.example` 为 `keys.env`，填入任一平台的 Key（**不要提交**）。有 Key 的平台会从"端点在线"升级为"实测调通"。

## 数据

- `data/providers-latest.json` — 最新实测结果（程序可读）
- `data/history/digest-*.json` — 每日快照
- `data/openrouter-free.json` / `data/clawlabs-health.json` — 免费模型清单
- `site/data.json` — 站点同份数据

## 自己用：免费模型聚合网关

配合 [LiteLLM](https://github.com/BerriAI/litellm) 可把多家免费模型聚合成一个 OpenAI 兼容端点，429 自动切换。示例配置思路见各平台 `base_url`。

## 红线 / 合规

- 本项目**只做情报和探活，不转发、不转售、不分发任何 API Key**
- 请遵守各平台 ToS：**一个人一个账号一个 Key**，不要批量注册、不要逆向（如 gpt4free）
- 免费层大多会记录数据，**不要发送敏感/隐私内容**
- 免费额度随时可能变化，一切以各官网为准

## 免责

数据仅供学习研究，自动探测每个平台每天仅发极少量请求。平台名称归各自所有者。
