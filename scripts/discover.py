#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discover.py — 新免费资源发现器
每天对比权威目录(models.dev / ClawLabs / OpenRouter)与本项目 providers.json，
发现“有零成本模型、但我们还没收录”的新 provider，并检测已收录平台的新增免费模型。
产出 data/discoveries-latest.json（候选池，人工/后续自动探活确认后才进正式榜）。
"""
import json, os, ssl, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)
CST = timezone(timedelta(hours=8))
CTX = ssl.create_default_context()
CHECKED = datetime.now(CST).strftime("%Y-%m-%dT%H:%M:%S%z")

def jget(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "freehub-discovery/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return json.load(r), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

# 排除：聚合网关/订阅计划/非独立平台/内部/需付费
EXCLUDE_KEYWORDS = ("-coding-plan","-token-plan","-coding","orcarouter","aihubmix","kilo",
                    "opencode","unorouter","tempr","zenmux","bothub","llmgateway","merge-gateway",
                    "azure-cognitive","requesty","vercel","pioneer","qvac","nan","empirio",
                    "gitlab","lmstudio","atomic-chat","agnes","inferx","kenari","pendra",
                    "commandcode","meganova","lynkr","zeldoc","llmtr","nova-2","poolside",
                    "regolo","cortecs","ovhcloud","hetzner","infomaniak","iteracompute",
                    "digitalocean","qiniu","sensenova","reflection","sambanova-coding")

def is_excluded(pid):
    return any(k in pid for k in EXCLUDE_KEYWORDS)

def main():
    # 已收录 provider id（来自 providers.json）
    pj = json.load(open(os.path.join(BASE, "providers.json")))
    known = {p["id"] for p in pj["providers"]}

    findings = {"checked_at": CHECKED, "new_providers": [], "new_openrouter_models": [],
                "sources_status": {}}

    # ---------- 源1: models.dev（找新 provider）----------
    md, err = jget("https://models.dev/api.json")
    findings["sources_status"]["models.dev"] = err or "ok"
    if md:
        for pid, info in md.items():
            if not isinstance(info, dict) or is_excluded(pid) or pid in known:
                continue
            free_models = []
            for mid, m in info.get("models", {}).items():
                if isinstance(m, dict):
                    c = m.get("cost", {})
                    if c.get("input") == 0 and c.get("output") == 0:
                        free_models.append(mid)
            if not free_models:
                continue
            # 取 API base / 环境变量线索
            api = info.get("api") or info.get("baseURL") or ""
            env = info.get("env_var") or (info.get("env") or "")
            findings["new_providers"].append({
                "candidate_id": pid,
                "name": info.get("name") or pid,
                "free_model_count": len(free_models),
                "sample_models": free_models[:5],
                "api_base": api,
                "env_var": env,
                "source": "models.dev",
                "note": "待人工确认注册门槛/是否真免费/是否中转",
            })
        findings["new_providers"].sort(key=lambda x: -x["free_model_count"])

    # ---------- 源2: OpenRouter 新增免费模型 ----------
    or_d, err2 = jget("https://openrouter.ai/api/v1/models")
    findings["sources_status"]["openrouter"] = err2 or "ok"
    prev_or = os.path.join(DATA, "openrouter-free.json")
    prev_ids = set()
    if os.path.exists(prev_or):
        try:
            prev = json.load(open(prev_or))
            prev_ids = {m["id"] for m in prev.get("models", [])}
        except Exception:
            pass
    if or_d:
        cur_free = []
        for m in or_d.get("data", []):
            pr = m.get("pricing", {})
            try:
                if float(pr.get("prompt", 1) or 1) == 0 and float(pr.get("completion", 1) or 1) == 0:
                    cur_free.append({"id": m.get("id"), "context": m.get("context_length"),
                                     "name": m.get("name")})
            except (ValueError, TypeError):
                pass
        findings["new_openrouter_models"] = [m for m in cur_free if m["id"] not in prev_ids]
        findings["openrouter_free_total"] = len(cur_free)

    # ---------- 源3: ClawLabs 健康库（新冒头的免费模型）----------
    cl, err3 = jget("https://raw.githubusercontent.com/ClawLabsAI/free-ai-models/main/data/models.json")
    findings["sources_status"]["clawlabs"] = err3 or "ok"
    if cl:
        findings["clawlabs_total"] = len(cl.get("models", []))
        findings["clawlabs_healthy"] = sum(1 for m in cl.get("models", [])
                                           if (m.get("health") or "") == "ok")

    # 历史对比：把今天的候选和昨天比，标出真正首次出现的
    out = os.path.join(DATA, "discoveries-latest.json")
    prev_new = set()
    if os.path.exists(out):
        try:
            old = json.load(open(out))
            prev_new = {x["candidate_id"] for x in old.get("new_providers", [])}
        except Exception:
            pass
    for x in findings["new_providers"]:
        x["first_seen_today"] = x["candidate_id"] not in prev_new

    json.dump(findings, open(out, "w"), ensure_ascii=False, indent=1)
    # 历史快照
    hist = os.path.join(DATA, "history")
    os.makedirs(hist, exist_ok=True)
    day = datetime.now(CST).strftime("%Y-%m-%d")
    json.dump(findings, open(os.path.join(hist, f"discover-{day}.json"), "w"),
              ensure_ascii=False, indent=1)

    print(f"发现候选新平台: {len(findings['new_providers'])} 个")
    print(f"OpenRouter 新增免费模型: {len(findings['new_openrouter_models'])} 个")
    print(f"ClawLabs 健康模型: {findings.get('clawlabs_healthy')}/{findings.get('clawlabs_total')}")
    for x in findings["new_providers"][:10]:
        flag = "🆕" if x["first_seen_today"] else "  "
        print(f"  {flag} {x['candidate_id']:24} 免费模型{x['free_model_count']:2}个 e.g.{x['sample_models'][:2]}")

if __name__ == "__main__":
    main()
