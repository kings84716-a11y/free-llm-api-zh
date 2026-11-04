#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
free_api_scan.py — 免费 AI API 定期扫描器 (双源融合)
主源 ClawLabsAI/free-ai-models: 每日更新, 自带健康探测/速率/隐私/评分
辅源 OpenRouter /models: 实时, 交叉补充
- 对比上次快照 → 新增/消失/健康变化
- 探测资源库平台端点存活
- 输出 Markdown 报告 + JSON 快照 + last_scan.json
"""
import json, os, urllib.request, urllib.error, ssl
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(BASE, "snapshots")
os.makedirs(SNAP, exist_ok=True)
DB = os.path.join(BASE, "free_apis.json")
REPORT = os.path.join(BASE, "latest_report.md")
CST = timezone(timedelta(hours=8))
now = datetime.now(CST)

CLAWLABS = "https://raw.githubusercontent.com/ClawLabsAI/free-ai-models/main/data/models.json"
OR = "https://openrouter.ai/api/v1/models"

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "free-api-hub/2.0"})
    return urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context())

def load_prev(key_file):
    snaps = sorted(f for f in os.listdir(SNAP) if f.startswith(key_file))
    if not snaps:
        return None
    try:
        return json.load(open(os.path.join(SNAP, snaps[-1])))
    except Exception:
        return None

def fetch_clawlabs():
    try:
        with get(CLAWLABS) as r:
            d = json.load(r)
        models = []
        for m in d.get("models", []):
            models.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "provider": m.get("provider"),
                "context": m.get("context_window"),
                "modalities": ",".join(m.get("modalities", []) or []),
                "tools": m.get("supports_tools"),
                "rate_limit": m.get("rate_limit"),
                "data_use": m.get("data_use"),
                "health": (m.get("health") or "").lower(),
                "answering_now": m.get("answering_now"),
                "rank": m.get("rank"),
                "score": m.get("score"),
            })
        return {"updated": d.get("updated_at"), "models": models}, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

def fetch_or_free():
    try:
        with get(OR) as r:
            d = json.load(r)
        out = []
        for m in d.get("data", []):
            p = m.get("pricing", {})
            try:
                if float(p.get("prompt", 1) or 1) == 0 and float(p.get("completion", 1) or 1) == 0:
                    out.append(m.get("id"))
            except (ValueError, TypeError):
                pass
        return out, None
    except Exception as e:
        return [], f"{type(e).__name__}: {e}"

def probe(url):
    for path in ("/models", ""):
        try:
            with get(url.rstrip("/") + path, timeout=10) as r:
                return "alive", r.status
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404, 405):
                return "alive", e.code
            return "error", e.code
        except Exception as e:
            last = type(e).__name__
    return "down", last

def main():
    L = ["# 免费 AI API 扫描报告", "", f"**扫描时间**: {now:%Y-%m-%d %H:%M} CST", ""]

    cl, cl_err = fetch_clawlabs()
    orids, or_err = fetch_or_free()

    # 快照与 diff
    prev = load_prev("clawlabs_")
    cur_ids = {m["id"] for m in (cl["models"] if cl else [])}
    prev_ids = {m["id"] for m in (prev["models"] if prev else [])} if prev else set()
    new = sorted(cur_ids - prev_ids)
    gone = sorted(prev_ids - cur_ids)

    if cl:
        json.dump({"ts": now.isoformat(), "models": cl["models"]},
                  open(os.path.join(SNAP, f"clawlabs_{now:%Y%m%d_%H%M}.json"), "w"),
                  ensure_ascii=False, indent=1)
        for old in sorted(f for f in os.listdir(SNAP) if f.startswith("clawlabs_"))[:-10]:
            os.remove(os.path.join(SNAP, old))

    # 健康变化 (仅对上次也在的模型) — 以 health 字段为准
    health_changed = []
    if cl and prev:
        pre_v = {m["id"]: (m.get("health") or "") for m in prev["models"]}
        for m in cl["models"]:
            cur = (m.get("health") or "")
            if m["id"] in pre_v and pre_v[m["id"]] != cur and (pre_v[m["id"]] == "ok" or cur == "ok"):
                health_changed.append((m["id"], pre_v[m["id"]], cur))

    if cl_err:
        L += [f"## ⚠️ ClawLabs 源失败: `{cl_err}`", ""]
    else:
        live = [m for m in cl["models"] if m.get("health") == "ok"]
        L += [f"## ClawLabs 每日免费模型: **{len(cl['models'])}** 个 (源更新 {cl['updated'][:10]})",
              f"当前探测存活: **{len(live)}** 个", ""]
        if new:
            L += [f"### 🆕 本次新增 ({len(new)})"] + [f"- `{i}`" for i in new] + [""]
        if gone:
            L += [f"### ❌ 下架 ({len(gone)})"] + [f"- `{i}`" for i in gone] + [""]
        if health_changed:
            L.append(f"### 🩺 健康变化 ({len(health_changed)})")
            for i, a, b in health_changed:
                L.append(f"- `{i}`: {'活' if a else '死'} → {'活' if b else '死'}")
            L.append("")
        L.append("### 全部免费模型(按评分排名)")
        L.append("| # | 模型 | 上下文 | 模态 | 限速 | 数据训练 | 健康 |")
        L.append("|---|---|---|---|---|---|---|")
        for m in cl["models"]:
            du = (m.get("data_use") or "")[:18]
            L.append(f"| {m.get('rank')} | `{m['id']}` | {m.get('context')} | {m.get('modalities')} | {m.get('rate_limit')} | {du} | {'🟢' if m.get('health')=='ok' else '⚪'} |")
        L.append("")

    if not or_err:
        extra = sorted(set(orids) - cur_ids)
        L += [f"## OpenRouter 零定价模型: {len(orids)} 个" +
              (f"（其中 {len(extra)} 个未在 ClawLabs）" if extra else ""), ""]
        if extra:
            L += [f"- `{i}`" for i in extra[:20]] + [""]
    else:
        L += [f"## ⚠️ OpenRouter 源失败: `{or_err}`", ""]

    # 平台端点
    db = json.load(open(DB))
    L += ["## 关键平台端点", "", "| 平台 | 状态 |", "|---|---|"]
    for item in db.get("text_llm", []):
        url = item.get("base_url", "")
        if not url or url.startswith("各自") or "{acct}" in url:
            L.append(f"| {item['provider']} | — |")
            continue
        st, code = probe(url)
        L.append(f"| {item['provider']} | {{'alive':'🟢','down':'🔴','error':'🟡'}}.get(st,'⚪') {st}({code}) |")
    L.append("")

    report = "\n".join(L)
    open(REPORT, "w").write(report)
    json.dump({"ts": now.isoformat(), "total": len(cl["models"]) if cl else 0,
               "new": new, "gone": gone, "health_changed": [c[0] for c in health_changed],
               "error": cl_err or or_err},
              open(os.path.join(BASE, "last_scan.json"), "w"), ensure_ascii=False, indent=1)
    print(report)
    print("\n[saved]", REPORT)

if __name__ == "__main__":
    main()
