#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_digest.py — 全网免费 AI API 每日巡检
数据源:
  1. OpenRouter /models 实时免费模型(无需key)
  2. ClawLabsAI/free-ai-models 每日健康库(answering_now/rate/data_use)
  3. providers.json 平台端点存活探测(无key, GET /models 判 200/401=活)
  4. 有 key 的平台(读 keys.env)实测 /key 额度或 1-token 探针
产出:
  reports/digest_YYYY-MM-DD.md   中文日报(可直接作视频脚本素材)
  reports/latest.json            结构化最新
  changes.json                   与上次对比的新增/下架/额度变化
"""
import json, os, ssl, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

BASE=os.path.dirname(os.path.abspath(__file__))
REP=os.path.join(BASE,"reports"); os.makedirs(REP,exist_ok=True)
CST=timezone(timedelta(hours=8)); now=datetime.now(CST)
KEYS_FILE=os.path.join(BASE,"keys.env")
CTX=ssl.create_default_context()

def http(url, headers=None, timeout=20, data=None):
    req=urllib.request.Request(url,data=data,headers=headers or {"User-Agent":"freehub/1.0"})
    return urllib.request.urlopen(req,timeout=timeout,context=CTX)

def jget(url,headers=None,timeout=20):
    try:
        with http(url,headers,timeout) as r: return json.load(r),None
    except urllib.error.HTTPError as e: return None,f"HTTP{e.code}"
    except Exception as e: return None,f"{type(e).__name__}"

def load_keys():
    ks={}
    if os.path.exists(KEYS_FILE):
        for line in open(KEYS_FILE):
            line=line.strip()
            if line and not line.startswith("#") and "=" in line:
                k,v=line.split("=",1); ks[k.strip()]=v.strip().strip('"').strip("'")
    return ks

def probe_alive(base_url):
    """无key探活: /models 返回200或401(端点在,要key)都算活; 404/超时算挂"""
    for path in ("/models",""):
        try:
            with http(base_url.rstrip("/")+path,timeout=10) as r:
                return "alive", r.status
        except urllib.error.HTTPError as e:
            if e.code in (401,403): return "alive_auth", e.code
            if e.code==404: continue
            return "http_err", e.code
        except Exception:
            continue
    return "down","-"

def openrouter_free():
    d,err=jget("https://openrouter.ai/api/v1/models")
    if err: return [],err
    out=[]
    for m in d.get("data",[]):
        p=m.get("pricing",{})
        try:
            if float(p.get("prompt",1) or 1)==0 and float(p.get("completion",1) or 1)==0:
                out.append(m.get("id"))
        except (ValueError,TypeError): pass
    return sorted(out),None

def clawlabs():
    d,err=jget("https://raw.githubusercontent.com/ClawLabsAI/free-ai-models/main/data/models.json")
    if err: return [],err
    ms=[]
    for m in d.get("models",[]):
        ms.append({"id":m.get("id"),"health":(m.get("health") or "").lower(),
                   "rate":m.get("rate_limit"),"data_use":m.get("data_use"),
                   "ctx":m.get("context_window"),"mod":",".join(m.get("modalities",[]) or [])})
    return {"updated":d.get("updated_at"),"models":ms},None

def or_quota(keys):
    k=keys.get("OPENROUTER_API_KEY")
    if not k: return None
    d,err=jget("https://openrouter.ai/api/v1/key",{"Authorization":f"Bearer {k}"})
    if err: return {"error":err}
    x=d.get("data",{})
    return {"free_tier":x.get("is_free_tier"),
            "free_used":x.get("free_model_daily_requests",{}).get("used"),
            "free_limit":x.get("free_model_daily_requests",{}).get("limit")}

def main():
    providers=json.load(open(os.path.join(BASE,"providers.json")))["providers"]
    keys=load_keys()
    orf,orf_err=openrouter_free()
    cl,cl_err=clawlabs()
    quota=or_quota(keys)

    # 平台端点探活(轻量, 只探有base_url的)
    alive={}
    for p in providers:
        bu=p.get("base_url","")
        if bu and "{account_id}" not in bu and "generativelanguage" not in bu:
            alive[p["id"]]=probe_alive(bu)
            time.sleep(0.3)

    state={"date":now.strftime("%Y-%m-%d %H:%M"),
           "openrouter_free_models":orf,"openrouter_err":orf_err,
           "openrouter_quota":quota,
           "clawlabs":cl,
           "providers_alive":alive,
           "providers_total":len(providers),
           "keys_configured":sorted(k for k in keys)}
    json.dump(state,open(os.path.join(REP,"latest.json"),"w"),ensure_ascii=False,indent=1)

    # 变化对比
    changes={"new_or_models":[],"gone_or_models":[],"new_providers":[]}
    snap=os.path.join(BASE,"snapshots")
    os.makedirs(snap,exist_ok=True)
    importglob=os.path.join(snap,"digest_*.json")
    import glob
    olds=sorted(glob.glob(importglob))
    if olds:
        prev=json.load(open(olds[-1]))
        po=set(prev.get("openrouter_free_models",[])); co=set(orf)
        changes["new_or_models"]=sorted(co-po); changes["gone_or_models"]=sorted(po-co)
    json.dump(changes,open(os.path.join(BASE,"changes.json"),"w"),ensure_ascii=False,indent=1)
    json.dump(state,open(os.path.join(snap,f"digest_{now:%Y%m%d}.json"),"w"),ensure_ascii=False,indent=1)
    for f in sorted(glob.glob(os.path.join(snap,"digest_*.json")))[:-14]: os.remove(f)

    # ===== 生成中文日报 =====
    L=[f"# 全网免费 AI API 日报 · {now:%Y-%m-%d}",
       "","> 自动巡检生成｜自用选模型 & 视频素材｜数据来自 OpenRouter 实时目录 + ClawLabs 健康库 + 平台实测","",
       f"## 📊 今日速览","",
       f"- 收录平台：**{len(providers)}** 个（另有已失效/改收费 {4} 个单独标注）",
       f"- OpenRouter 免费模型：**{len(orf)}** 个（新增 {len(changes['new_or_models'])} / 下架 {len(changes['gone_or_models'])}）",
       f"- ClawLabs 健康库更新：{cl.get('updated','?')[:10] if cl else '拉取失败'}",
       f"- 已配置 key 实测：{', '.join(keys.keys()) if keys else '暂无（注册后填 keys.env 即自动实测额度）'}"]
    if quota:
        if "error" in quota: L.append(f"- OpenRouter 额度查询失败: {quota['error']}")
        else: L.append(f"- OpenRouter 今日免费请求：**{quota['free_used']}/{quota['free_limit']}**")
    L+=["","## 🏆 平台推荐排序（按免费力度+易用）",""]
    tier_names={1:"🟢 第一梯队（额度大、不要卡、优先注册）",2:"🟡 第二梯队（实用/国内直连）",3:"⚪ 第三梯队（额度小/有门槛/备用）"}
    for tier in (1,2,3):
        L.append(f"### {tier_names[tier]}"); L.append("")
        for p in providers:
            if p["tier"]!=tier: continue
            keyflag="✅已接" if p["status"]=="in_use" else ("🔑待注册" if p["need_key"] else "🆓无需key")
            al=alive.get(p["id"],("",""))
            alicon={"alive":"🟢","alive_auth":"🔐","http_err":"🟡","down":"🔴"}.get(al[0],"⚪")
            L.append(f"- {alicon} **{p['name']}** [{keyflag}] — {p['free_quota']}")
            L.append(f"  - 注册: {p['register']}（{p['signup']}）")
            L.append(f"  - base_url: `{p['base_url']}`")
            if p.get("gotcha"): L.append(f"  - ⚠️ {p['gotcha']}")
        L.append("")
    if cl:
        healthy=[m for m in cl["models"] if m["health"]=="ok"]
        L+=["## 💚 当前健康的 OpenRouter 免费模型","",
            "| 模型 | 上下文 | 限速 | 数据训练 | 模态 |","|---|---|---|---|---|"]
        for m in sorted(healthy,key=lambda x:x["id"]):
            L.append(f"| `{m['id']}` | {m['ctx']} | {m['rate']} | {m['data_use']} | {m['mod']} |")
        L.append("")
    if changes["new_or_models"] or changes["gone_or_models"]:
        L.append("## 🔔 今日变化")
        if changes["new_or_models"]: L+=["**新出现的免费模型：**"]+[f"- `{x}`" for x in changes["new_or_models"]]
        if changes["gone_or_models"]: L+=["**下架的免费模型：**"]+[f"- `{x}`" for x in changes["gone_or_models"]]
        L.append("")
    L+=["## 🪦 已失效/改收费（别再推荐）",""]
    dep=json.load(open(os.path.join(BASE,"providers.json"))).get("deprecated_2026",[])
    for x in dep: L.append(f"- ~~{x['name']}~~ — {x['reason']}")
    L.append("")
    rep="\n".join(L)
    open(os.path.join(REP,f"digest_{now:%Y-%m-%d}.md"),"w").write(rep)
    open(os.path.join(REP,"latest.md"),"w").write(rep)
    print(rep[:1500]); print("\n[saved]",os.path.join(REP,f"digest_{now:%Y-%m-%d}.md"))

if __name__=="__main__": main()
