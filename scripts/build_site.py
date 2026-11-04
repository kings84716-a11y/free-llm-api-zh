#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_site.py — 把 data/ 实测数据渲染成单文件静态站 site/index.html
零依赖、内联 CSS，GitHub Pages / 任何静态托管直接用。
"""
import json, os
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SITE = os.path.join(BASE, "site")
os.makedirs(SITE, exist_ok=True)

d = json.load(open(os.path.join(DATA, "providers-latest.json")))
providers = d["providers"]
summ = d.get("summary", {})
checked = d.get("checked_at", "")[:16].replace("T", " ")
or_free = json.load(open(os.path.join(DATA, "openrouter-free.json")))
claw = json.load(open(os.path.join(DATA, "clawlabs-health.json")))
deprecated_raw = json.load(open(os.path.join(DATA,"deprecated.json"))) if os.path.exists(os.path.join(DATA,"deprecated.json")) else []
deprecated = deprecated_raw.get("deprecated", []) if isinstance(deprecated_raw, dict) else deprecated_raw

STATUS = {
    "alive_verified": ("🟢", "实测可用", "verified"),
    "alive": ("🔵", "端点在线", "alive"),
    "alive_auth": ("🔵", "在线·待Key", "auth"),
    "down": ("🔴", "无法访问", "down"),
    "unknown": ("⚪", "未知", "unknown"),
}
TIER = {1: "🟢 第一梯队", 2: "🟡 第二梯队", 3: "⚪ 第三梯队"}

def esc(s):
    return str(s if s is not None else "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

cards = []
for p in sorted(providers, key=lambda x: (x.get("tier",9), {"alive_verified":0,"alive":1,"alive_auth":2,"down":3}.get(x.get("today_status"),4))):
    icon, label, _ = STATUS.get(p.get("today_status"), STATUS["unknown"])
    lat = p.get("latency_ms")
    lat_s = f"{int(lat)}ms" if isinstance(lat,(int,float)) else "—"
    need = []
    need.append("信用卡" if p.get("need_card") else "免信用卡")
    need.append(esc(p.get("signup") or ""))
    verified = ""
    v = p.get("verify") or {}
    if isinstance(v, dict) and v.get("model"):
        verified = f'<div class="vf">实测模型 <code>{esc(v.get("model"))}</code> · {esc(v.get("detail",""))[:60]}</div>'
    cards.append(f"""
    <div class="card st-{STATUS.get(p.get('today_status'),STATUS['unknown'])[2]}">
      <div class="top"><span class="ico">{icon}</span><span class="name">{esc(p.get('name'))}</span><span class="lat">{lat_s}</span></div>
      <div class="quota">{esc(p.get('free_quota'))}</div>
      <div class="meta">{(' · '.join(x for x in need if x))} · 刷新:{esc(p.get('refresh'))}</div>
      <code class="url">{esc(p.get('base_url'))}</code>
      {verified}
      {f'<div class="gotcha">⚠️ {esc(p.get("gotcha"))}</div>' if p.get('gotcha') else ''}
      <div class="btns">
        <a href="{esc(p.get('register'))}" target="_blank" rel="noopener">注册/拿Key ↗</a>
        <span class="tier">{TIER.get(p.get('tier'),'')}</span>
      </div>
    </div>""")

# OpenRouter 免费模型表
orm = or_free.get("models", []) if isinstance(or_free, dict) else []
or_rows = "".join(
    f'<tr><td><code>{esc(m.get("id"))}</code></td><td>{m.get("context","")}</td><td>{esc(m.get("modality",""))}</td></tr>'
    for m in orm)

# ClawLabs 健康模型
clms = claw.get("models", []) if isinstance(claw, dict) else []
healthy = [m for m in clms if (m.get("health") or "") == "ok"]
cl_rows = "".join(
    f'<tr><td><code>{esc(m.get("id"))}</code></td><td>{m.get("ctx","")}</td><td>{esc(m.get("rate",""))}</td><td>{esc(m.get("data_use",""))}</td></tr>'
    for m in sorted(healthy, key=lambda x:x.get("id","")))

dep_rows = "".join(
    f'<li><b>{esc(x.get("name"))}</b> — {esc(x.get("reason"))}</li>' for x in deprecated)

nv = summ.get("alive_verified",0); na = summ.get("alive",0); naa = summ.get("alive_auth",0); nd = summ.get("down",0)

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>免费大模型 API 实测榜 · 每日自动更新</title>
<meta name="description" content="每天真实请求实测全网免费 LLM/AI API：谁活着、额度多少、谁改收费。中文、OpenAI 兼容、免信用卡优先。">
<style>
:root{{--bg:#0d1117;--card:#161b22;--bd:#30363d;--fg:#e6edf3;--mut:#8b949e;--gr:#3fb950;--bl:#58a6ff;--rd:#f85149;--yl:#d29922}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--fg);font-family:-apple-system,'PingFang SC','Microsoft YaHei',Segoe UI,sans-serif;line-height:1.6}}
.wrap{{max-width:1100px;margin:0 auto;padding:24px 16px 80px}}
header{{text-align:center;padding:32px 0 16px}}
h1{{font-size:clamp(22px,4vw,34px);background:linear-gradient(90deg,#58a6ff,#3fb950);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{color:var(--mut);margin-top:8px;font-size:15px}}
.badge{{display:inline-block;margin-top:14px;padding:5px 14px;border:1px solid var(--bd);border-radius:20px;font-size:13px;color:var(--mut)}}
.stats{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin:22px 0}}
.stat{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px 22px;text-align:center;min-width:110px}}
.stat b{{font-size:26px;display:block}}
.stat span{{color:var(--mut);font-size:12px}}
h2{{font-size:20px;margin:38px 0 16px;padding-left:10px;border-left:4px solid var(--bl)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:8px}}
.card.st-verified{{border-color:#234a2e}}
.card.st-down{{opacity:.65}}
.top{{display:flex;align-items:center;gap:8px}}
.name{{font-weight:600;font-size:16px;flex:1}}
.lat{{color:var(--mut);font-size:12px}}
.ico{{font-size:15px}}
.quota{{font-size:14px;color:#a5d6ff}}
.meta{{font-size:12px;color:var(--mut)}}
.url{{font-size:11px;background:#0d1117;border:1px solid var(--bd);border-radius:6px;padding:5px 7px;color:var(--mut);word-break:break-all}}
.vf{{font-size:12px;color:var(--gr)}}
.gotcha{{font-size:12px;color:var(--yl)}}
.btns{{display:flex;justify-content:space-between;align-items:center;margin-top:auto;padding-top:8px}}
.btns a{{color:var(--bl);text-decoration:none;font-size:13px;border:1px solid var(--bl);padding:5px 12px;border-radius:8px}}
.btns a:hover{{background:var(--bl);color:#000}}
.tier{{font-size:11px;color:var(--mut)}}
table{{width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;overflow:hidden;font-size:13px}}
th,td{{padding:9px 12px;text-align:left;border-bottom:1px solid var(--bd)}}
th{{background:#1c2330;color:var(--mut);font-weight:600}}
code{{font-family:ui-monospace,Menlo,monospace;font-size:12px}}
.dep li{{margin:6px 0;color:var(--mut)}}
.foot{{text-align:center;color:var(--mut);font-size:12px;margin-top:50px;border-top:1px solid var(--bd);padding-top:20px}}
.legend{{font-size:12px;color:var(--mut);text-align:center;margin-top:8px}}
</style></head><body><div class="wrap">
<header>
  <h1>🆓 免费大模型 API 实测榜</h1>
  <div class="sub">每天真实发请求实测 · 谁活着 / 额度多少 / 谁改收费 · 中文 · OpenAI 兼容 · 免信用卡优先</div>
  <div class="badge">🔄 最近实测：{esc(checked)}</div>
</header>
<div class="stats">
  <div class="stat"><b style="color:var(--gr)">{nv}</b><span>🟢 实测调通</span></div>
  <div class="stat"><b style="color:var(--bl)">{na+naa}</b><span>🔵 端点在线</span></div>
  <div class="stat"><b>{summ.get('providers_total',len(providers))}</b><span>收录平台</span></div>
  <div class="stat"><b>{summ.get('openrouter_free_count',len(orm))}</b><span>免费模型</span></div>
</div>
<div class="legend">🟢 配 Key 真实推理通过 &nbsp;·&nbsp; 🔵 端点在线（注册拿 Key 即用）&nbsp;·&nbsp; 🔴 当前无法访问</div>
<h2>平台榜单</h2>
<div class="grid">{''.join(cards)}</div>
{('<h2>已失效 / 改收费（别再浪费时间）</h2><ul class="dep">'+dep_rows+'</ul>') if dep_rows else ''}
<h2>OpenRouter 免费模型（一个 Key 通用）</h2>
<table><thead><tr><th>模型</th><th>上下文</th><th>模态</th></tr></thead><tbody>{or_rows}</tbody></table>
{('<h2>当前健康的免费模型 · ClawLabs 探活</h2><table><thead><tr><th>模型</th><th>上下文</th><th>限速</th><th>数据训练</th></tr></thead><tbody>'+cl_rows+'</tbody></table>') if cl_rows else ''}
<div class="foot">
  数据由开源脚本每日自动实测生成 · 免费额度随时可能变化，以各官网为准 · 本榜单永久免费开放<br>
  仅供学习研究 · 请遵守各平台服务条款 · 一个账号一个 Key，勿批量注册
</div>
</div></body></html>"""

open(os.path.join(SITE, "index.html"), "w").write(html)
# site/data.json 给程序读
json.dump({"checked_at": checked, "summary": summ, "providers": providers,
           "openrouter_free": orm, "healthy": healthy},
          open(os.path.join(SITE, "data.json"), "w"), ensure_ascii=False, indent=1)
print("site built:", os.path.join(SITE, "index.html"), len(html), "bytes")
