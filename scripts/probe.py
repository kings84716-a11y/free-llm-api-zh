#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe.py — 免费 AI API 每日实测引擎（开源版）

做什么:
  1. 读 providers.json，对每个有 base_url 的平台做【无 key 探活】
     GET {base_url}/models：200=alive，401/403=alive_auth(端点在、要key)，
     404=回退试根路径，超时/连接错误=down。记录 HTTP 状态与延迟(ms)。
  2. 读 keys.env（存在才读，chmod 600，绝不入库），对配了 key 的平台做
     【真实 1-token 推理探测】：POST /chat/completions {"messages":[{"role":"user",
     "content":"hi"}],"max_tokens":8}，成功=alive_verified。推理类模型 max_tokens
     给 200。Cloudflare 走原生 /ai/run。每平台只发 1 次请求，间隔 0.5s。
  3. 拉 OpenRouter /models 免费模型列表（无 key）。
  4. 拉 ClawLabsAI/free-ai-models 每日健康库（health/rate/data_use）。
  5. 合并产出:
       data/providers-latest.json          — 最新结构化结果
       data/history/digest-YYYY-MM-DD.json — 每日历史快照
       data/openrouter-free.json           — OpenRouter 免费模型
       data/clawlabs-health.json           — ClawLabs 健康库
       data/summary.json                   — 给站点/徽章用的计数摘要

确定性: 列表按固定顺序/排序输出；唯一动态字段是 checked_at（ISO8601, 北京时区）。
退出码: 只要引擎本身跑完就是 0（平台挂了不算引擎失败）。
"""
import json
import os
import ssl
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
HIST = os.path.join(DATA, "history")
os.makedirs(HIST, exist_ok=True)

CST = timezone(timedelta(hours=8))
NOW = datetime.now(CST)
CHECKED_AT = NOW.isoformat(timespec="seconds")
TODAY = NOW.strftime("%Y-%m-%d")

KEYS_FILE = os.path.join(BASE, "keys.env")
CTX = ssl.create_default_context()
UA = "free-api-hub-bot/2.0 (+https://github.com/; daily-probe; 1-request-per-provider)"
TIMEOUT_ALIVE = 10
TIMEOUT_INFER = 25
SLEEP_BETWEEN = 0.5

# 推理类/输出极慢模型：max_tokens 放宽（reasoning models 会先吐思考链）
REASON_HINTS = ("reason", "r1", "o1", "o3", "o4", "thinking", "/gemini-2.5-pro")


def log(msg):
    print(f"[{NOW:%H:%M:%S}] {msg}", flush=True)


def http_request(url, headers=None, data=None, timeout=15):
    """返回 (status, body_bytes, latency_ms, err)。不抛异常。"""
    t0 = time.monotonic()
    req = urllib.request.Request(url, data=data, headers=headers or {"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            body = r.read(2 * 1024 * 1024)
            return r.status, body, int((time.monotonic() - t0) * 1000), None
    except urllib.error.HTTPError as e:
        body = e.read(64 * 1024) if hasattr(e, "read") else b""
        return e.code, body, int((time.monotonic() - t0) * 1000), None
    except Exception as e:
        return None, b"", int((time.monotonic() - t0) * 1000), f"{type(e).__name__}: {e}"


def jget(url, headers=None, timeout=20):
    status, body, lat, err = http_request(url, headers=headers, timeout=timeout)
    if err:
        return None, err, lat
    try:
        return json.loads(body.decode("utf-8", "replace")), None, lat
    except Exception as e:
        return None, f"BadJSON: {e}", lat


def load_keys():
    """keys.env 优先；CI 环境下同名环境变量也认（secrets 注入）。"""
    ks = {}
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    v = v.strip().strip('"').strip("'")
                    if v:
                        ks[k.strip()] = v
    # 环境变量覆盖（GitHub Actions secrets -> env）
    for name in (
        "OPENROUTER_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "CEREBRAS_API_KEY",
        "CF_API_TOKEN", "CF_ACCOUNT_ID", "NVIDIA_API_KEY", "COHERE_API_KEY",
        "SAMBANOVA_API_KEY", "MISTRAL_API_KEY", "SILICONFLOW_API_KEY",
        "MODELSCOPE_API_TOKEN", "DASHSCOPE_API_KEY", "ZHIPU_API_KEY",
        "AMD_API_KEY", "SENSENOVA_API_KEY", "LONGCAT_API_KEY",
    ):
        if os.environ.get(name):
            ks[name] = os.environ[name]
    return ks


# ---------------------------------------------------------------- 无 key 探活

def probe_alive(p):
    """返回 dict: today_status / http_status / latency_ms / note"""
    base = p["base_url"].rstrip("/")
    # Cloudflare 原生端点必须带 account_id 且路径是 /ai/run/...，无 key 没法标准探活
    if "{account_id}" in base:
        return {"today_status": "unknown", "http_status": None, "latency_ms": None,
                "alive_note": "非标准端点(需 account_id)，配 key 后直接实测推理"}
    paths = ["/models"]
    if p["id"] == "pollinations":
        paths = ["/models"]
    tried = []
    for path in paths:
        status, body, lat, err = http_request(base + path, timeout=TIMEOUT_ALIVE)
        tried.append(f"{path}->{status or err}")
        if err:
            return {"today_status": "down", "http_status": None, "latency_ms": lat,
                    "alive_note": err[:160]}
        if status == 200:
            return {"today_status": "alive", "http_status": 200, "latency_ms": lat,
                    "alive_note": "GET /models 200"}
        if status in (401, 403):
            return {"today_status": "alive_auth", "http_status": status, "latency_ms": lat,
                    "alive_note": f"GET /models {status}（端点在线，要求鉴权）"}
        if status == 404:
            continue
        if status in (405, 400):
            return {"today_status": "alive_auth", "http_status": status, "latency_ms": lat,
                    "alive_note": f"GET /models {status}（端点在，不支持该探测方式）"}
        if 300 <= status < 500:
            return {"today_status": "alive_auth", "http_status": status, "latency_ms": lat,
                    "alive_note": f"GET /models {status}"}
        return {"today_status": "down", "http_status": status, "latency_ms": lat,
                "alive_note": f"GET /models {status}"}
    return {"today_status": "down", "http_status": 404, "latency_ms": None,
            "alive_note": " / ".join(tried)}


# ---------------------------------------------------------------- 有 key 实测

def pick_model(p, key):
    """优先用 providers.json 里 probe_models；否则从 /models 挑一个最小的非嵌入模型。"""
    pref = p.get("probe_models") or []
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    status, body, lat, err = http_request(
        p["base_url"].rstrip("/") + "/models",
        headers=headers, timeout=TIMEOUT_ALIVE)
    catalog = []
    if status == 200:
        try:
            d = json.loads(body.decode("utf-8", "replace"))
            items = d.get("data") or d.get("models") or []
            for m in items:
                mid = m.get("id") or m.get("name") if isinstance(m, dict) else str(m)
                if not mid:
                    continue
                low = mid.lower()
                if any(bad in low for bad in ("embed", "rerank", "whisper", "tts", "speech",
                                              "image", "flux", "stable", "dall-e", "vision")):
                    continue
                catalog.append(mid)
        except Exception:
            pass
    catalog = sorted(set(catalog))
    for want in pref:
        if want in catalog:
            return want, catalog
    if pref:
        return pref[0], catalog  # /models 没列全也先试配置里的
    if catalog:
        # 挑名字看起来最小的（8b/mini/flash-lite/turbo/nano/small）
        small = [m for m in catalog if any(k in m.lower()
                 for k in ("flash-lite", "8b", "mini", "nano", "small", "turbo", "lite", "haiku"))]
        return (small or catalog)[0], catalog
    return None, catalog


def is_reasoning(model_id):
    # 额外把已验证为推理型/小token不出正文的免费模型纳入，给足 max_tokens
    extra = ("cohere/north-mini-code", "nemotron-3", "qwen3", "minimax-m3")
    low = model_id.lower()
    return any(h in low for h in REASON_HINTS) or any(h in low for h in extra)


def verify_cloudflare(p, keys):
    token = keys.get("CF_API_TOKEN")
    acct = keys.get("CF_ACCOUNT_ID")
    if not token or not acct or "{account_id}" not in p["base_url"]:
        return None
    model = (p.get("probe_models") or ["@cf/meta/llama-3.1-8b-instruct"])[0]
    url = (p["base_url"].replace("{account_id}", acct).rstrip("/")
           + f"/run/{model}")
    payload = json.dumps({"messages": [{"role": "user", "content": "hi"}],
                          "max_tokens": 8}).encode()
    status, body, lat, err = http_request(
        url, headers={"Authorization": f"Bearer {token}",
                      "Content-Type": "application/json"},
        data=payload, timeout=TIMEOUT_INFER)
    if err:
        return {"ok": False, "model": model, "latency_ms": lat, "detail": err[:160]}
    if status == 200:
        return {"ok": True, "model": model, "latency_ms": lat,
                "detail": "CF 原生 /ai/run 200"}
    return {"ok": False, "model": model, "latency_ms": lat,
            "detail": f"HTTP {status}: " + body.decode("utf-8", "replace")[:160]}


def verify_inference(p, keys):
    """真实 1-token 推理。返回 dict 或 None(没配 key 且平台需要 key 时跳过)。"""
    env = p.get("key_env") or ""
    key = keys.get(env) if env else None
    if not key and p.get("need_key", True):
        return None
    if p["id"] == "cloudflare":
        return verify_cloudflare(p, keys)

    model, catalog = pick_model(p, key)
    if not model:
        return {"ok": False, "model": None, "latency_ms": None,
                "detail": "未能从 /models 选取可测对话模型"}
    max_tokens = 200 if is_reasoning(model) else 32
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": max_tokens,
        "stream": False,
    }).encode()
    url = p["base_url"].rstrip("/") + "/chat/completions"
    hdr = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    # 偶发 403/429/5xx（CF 风控/限流）退避重试一次，避免误判
    status, body, lat, err = http_request(url, headers=hdr, data=payload, timeout=TIMEOUT_INFER)
    if status in (403, 429, 500, 502, 503):
        time.sleep(2.5)
        status, body, lat, err = http_request(url, headers=hdr, data=payload, timeout=TIMEOUT_INFER)
    if err:
        return {"ok": False, "model": model, "latency_ms": lat, "detail": err[:160]}
    if status != 200:
        return {"ok": False, "model": model, "latency_ms": lat,
                "detail": f"HTTP {status}: " + body.decode("utf-8", "replace")[:160]}
    try:
        d = json.loads(body.decode("utf-8", "replace"))
        content = (d.get("choices") or [{}])[0].get("message", {}).get("content")
        usage = d.get("usage") or {}
        ok = bool(content)
        return {"ok": ok, "model": d.get("id") or model, "latency_ms": lat,
                "detail": ("返回正文: " + str(content)[:40]) if ok else "200 但无正文",
                "usage": {"prompt": usage.get("prompt_tokens"),
                          "completion": usage.get("completion_tokens")}}
    except Exception as e:
        return {"ok": False, "model": model, "latency_ms": lat,
                "detail": f"200 但响应解析失败: {e}"}


# ---------------------------------------------------------------- OpenRouter

def openrouter_free_models():
    d, err, lat = jget("https://openrouter.ai/api/v1/models", timeout=25)
    if err:
        return {"fetched": False, "error": err, "checked_at": CHECKED_AT, "models": []}
    out = []
    for m in d.get("data", []):
        pr = m.get("pricing", {})
        try:
            if float(pr.get("prompt", 1) or 1) == 0 and float(pr.get("completion", 1) or 1) == 0:
                out.append({
                    "id": m.get("id"),
                    "name": m.get("name"),
                    "context": m.get("context_length"),
                    "modality": ",".join(m.get("architecture", {}).get("input_modalities", []) or []),
                })
        except (ValueError, TypeError):
            pass
    out.sort(key=lambda x: x["id"] or "")
    return {"fetched": True, "checked_at": CHECKED_AT, "count": len(out),
            "models": out}


def clawlabs_health():
    url = ("https://raw.githubusercontent.com/ClawLabsAI/free-ai-models/"
           "main/data/models.json")
    d, err, lat = jget(url, timeout=25)
    if err:
        return {"fetched": False, "error": err, "checked_at": CHECKED_AT, "models": []}
    ms = []
    for m in d.get("models", []):
        ms.append({
            "id": m.get("id"),
            "health": (m.get("health") or "").lower(),
            "rate": m.get("rate_limit"),
            "data_use": m.get("data_use"),
            "context_window": m.get("context_window"),
            "modalities": ",".join(m.get("modalities", []) or []),
        })
    ms.sort(key=lambda x: x["id"] or "")
    return {"fetched": True, "source_updated_at": d.get("updated_at"),
            "checked_at": CHECKED_AT, "count": len(ms), "models": ms}


# ---------------------------------------------------------------- main

def main():
    providers = json.load(open(os.path.join(BASE, "providers.json")))["providers"]
    keys = load_keys()
    log(f"providers={len(providers)} keys_configured={sorted(keys.keys())}")

    results = []
    for p in providers:
        rec = {
            "id": p["id"], "name": p["name"], "tier": p["tier"],
            "register": p["register"], "signup": p["signup"],
            "need_card": p["need_card"], "need_key": p["need_key"],
            "base_url": p["base_url"], "compat": p.get("compat"),
            "free_quota": p["free_quota"], "refresh": p.get("refresh"),
            "models": p.get("models"), "gotcha": p.get("gotcha"),
            "privacy": p.get("privacy"),
            "base_url_note": p.get("base_url_note"),
            "checked_at": CHECKED_AT,
        }
        rec.update(probe_alive(p))
        v = verify_inference(p, keys)
        if v is not None:
            rec["verified"] = v
            if v.get("ok"):
                rec["today_status"] = "alive_verified"
                rec["latency_ms"] = v.get("latency_ms")
            elif rec["today_status"] in ("unknown",):
                rec["today_status"] = "down"
            # verify 失败但无 key 探活显示在线的，保留 alive_auth 并记录失败细节
        time.sleep(SLEEP_BETWEEN)
        log(f"{rec['id']:12s} {rec['today_status']:15s} "
            f"{str(rec.get('latency_ms')):>6s}ms {rec.get('alive_note','')[:70]}")
        results.append(rec)

    log("拉取 OpenRouter 免费模型 ...")
    orf = openrouter_free_models()
    log(f"OpenRouter free models: {orf.get('count','ERR')}")
    time.sleep(SLEEP_BETWEEN)
    log("拉取 ClawLabs 健康库 ...")
    cl = clawlabs_health()
    log(f"ClawLabs models: {cl.get('count','ERR')}")

    # ---- 汇总
    def cnt(status):
        return sum(1 for r in results if r["today_status"] == status)
    summary = {
        "date": TODAY,
        "checked_at": CHECKED_AT,
        "providers_total": len(results),
        "alive_verified": cnt("alive_verified"),
        "alive": cnt("alive"),
        "alive_auth": cnt("alive_auth"),
        "down": cnt("down"),
        "unknown": cnt("unknown"),
        "keys_used": sorted(k for k in keys),
        "openrouter_free_count": orf.get("count", 0),
        "clawlabs_count": cl.get("count", 0),
    }

    latest = {"checked_at": CHECKED_AT, "date": TODAY,
              "summary": summary, "providers": results}
    deprec = json.load(open(os.path.join(BASE, "providers.json"))).get("deprecated", [])

    def dump(path, obj):
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=False)
            f.write("\n")
        os.replace(tmp, path)

    dump(os.path.join(DATA, "providers-latest.json"), latest)
    dump(os.path.join(DATA, "history", f"digest-{TODAY}.json"), latest)
    dump(os.path.join(DATA, "openrouter-free.json"), orf)
    dump(os.path.join(DATA, "clawlabs-health.json"), cl)
    dump(os.path.join(DATA, "summary.json"), summary)
    dump(os.path.join(DATA, "deprecated.json"),
         {"updated": TODAY, "deprecated": deprec})

    log("汇总: " + json.dumps(summary, ensure_ascii=False))
    log("完成 -> data/providers-latest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
