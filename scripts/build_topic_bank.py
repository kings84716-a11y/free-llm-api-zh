#!/usr/bin/env python3
"""
选题库构建器：把 HF/GitHub 监控产出沉淀成视频选题库
输入：
  - ~/.hermes/scripts/.hf_watch_state.json （HF 监控快照）
  - ~/.hermes/scripts/.gh_watch_state.json （GitHub 监控快照）
  - data/history/discover-*.json （免费API项目自身的发现记录）
输出：
  - video/topic_bank.json （机读选题库，带评分/标签/选题角度）
  - video/topic_bank.md （人读选题清单，视频脚本直接取用）
评分逻辑：高星/去审查/视频图像语音类 → 高分；附带现成标题钩子
"""
import json, os, datetime, glob

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = "/home/ubuntu/free-api-hub"
HF_STATE = os.path.expanduser("~/.hermes/scripts/.hf_watch_state.json")
GH_STATE = os.path.expanduser("~/.hermes/scripts/.gh_watch_state.json")

# 选题角度映射：关键词 → (赛道, 视频钩子)
ANGLE_MAP = [
    (("uncensored", "abliterated", "heretic", "nsfw"), "无审查模型", "这个模型什么都敢答？实测去审查模型的真实边界"),
    (("video", "img2video", "talking", "digital human", "lip sync"), "AI视频/数字人", "本地跑AI视频/数字人，新出的这个项目什么水平"),
    (("image", "photo", "restor", "upscal", "coloriz", "inpaint", "flux", "stable diffusion", "comfyui"), "AI图像/老照片修复", "老照片修复/AI出图新神器，开源免费本地跑"),
    (("tts", "voice", "speech", "asr", "music", "audio"), "AI语音/音乐", "语音克隆/配音新方案，不用付费API"),
    (("agent", "mcp", "computer use"), "AI Agent", "Agent又出新玩法，这个开源项目值得抄"),
    (("3d", "avatar", "animation"), "AI 3D/动画", "一句话生成3D/动画，开源新玩家"),
    (("gguf", "quantiz", "llama", "qwen", "deepseek", "gemma", "llm"), "开源大模型", "又一个能白嫖的开源大模型，本地部署实测"),
]

def angle_for(name, desc=""):
    text = (name + " " + desc).lower()
    for kws, track, hook in ANGLE_MAP:
        if any(k in text for k in kws):
            return track, hook
    return "其他AI工具", "新出的AI开源项目，值不值得跟"

def score_hf(model_id):
    s = 0
    t = model_id.lower()
    if any(k in t for k in ("uncensored", "abliterated", "heretic", "nsfw")): s += 3
    if any(k in t for k in ("video", "voice", "tts", "image", "flux", "vision")): s += 2
    if any(k in t for k in ("qwen", "llama", "deepseek", "gemma", "gguf")): s += 1
    return s

def main():
    topics = []

    # 1. HF 模型选题
    if os.path.exists(HF_STATE):
        hf = json.load(open(HF_STATE))
        for mid, rec in hf.get("models", {}).items():
            track, hook = angle_for(mid)
            # rec 是整条模型记录(dict)，更新时间在其 "modified" 字段；
            # 不能把 dict 直接当 updated，否则后续排序会触发 TypeError
            updated = rec.get("modified", "") if isinstance(rec, dict) else str(rec or "")
            topics.append({
                "source": "HuggingFace",
                "name": mid,
                "track": track,
                "hook": hook,
                "score": score_hf(mid),
                "updated": updated or "",
                "url": f"https://huggingface.co/{mid}",
            })

    # 2. GitHub 项目选题：直接复用 gh_watch 的过滤+拉取真实 star/描述
    gh_script = os.path.expanduser("~/.hermes/scripts/gh_watch_tg.py")
    if os.path.exists(gh_script):
        import importlib.util
        spec = importlib.util.spec_from_file_location("ghw", gh_script)
        ghw = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ghw)
        try:
            for r in ghw.fetch_new_repos():
                if r.get("scam"):
                    continue
                text = (r["id"] + " " + r["desc"] + " " + r.get("topics", "")).lower()
                if getattr(ghw, "is_noise", lambda t: None)(text):
                    continue
                # gh_watch 没有 classify()，等价的 AI 相关性判断是 hit_keywords()
                kws = ghw.hit_keywords(text)
                if not kws:  # 只收 AI 方向，非AI项目不进选题库
                    continue
                track, hook = angle_for(r["id"], r["desc"])
                topics.append({
                    "source": "GitHub",
                    "name": r["id"],
                    "track": track,
                    "hook": hook,
                    "score": min(5, 1 + r["stars"] // 300 + len(kws)),
                    "stars": r["stars"],
                    "desc": r["desc"],
                    "updated": r["created"],
                    "url": r["url"],
                })
        except Exception as e:
            print(f"[warn] GitHub 拉取失败: {e}")

    # 3. 免费API项目自身发现的新平台/模型
    for f in sorted(glob.glob(f"{HUB}/data/history/discover-*.json"))[-3:]:
        try:
            d = json.load(open(f))
            for item in (d if isinstance(d, list) else d.get("new", [])):
                name = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)[:80]
                topics.append({
                    "source": "FreeAPI",
                    "name": name,
                    "track": "免费API",
                    "hook": "免费API榜单更新：新平台/新免费模型实测",
                    "score": 2,
                    "updated": os.path.basename(f)[9:19],
                    "url": "https://kings84716-a11y.github.io/free-llm-api-zh/",
                })
        except Exception:
            pass

    # 去重（同名保留最高分）+ 排序
    best = {}
    for t in topics:
        if t["name"] not in best or t["score"] > best[t["name"]]["score"]:
            best[t["name"]] = t
    # 排序键统一强转类型：score 必为 int、updated 必为 str，
    # 避免不同来源字段类型不一致（dict/None/str）触发 TypeError
    topics = sorted(best.values(),
                    key=lambda x: (int(x.get("score", 0)), str(x.get("updated") or "")),
                    reverse=True)

    os.makedirs(f"{HUB}/video", exist_ok=True)
    json.dump({"built_at": datetime.datetime.now().isoformat(), "count": len(topics),
               "topics": topics}, open(f"{HUB}/video/topic_bank.json", "w"), ensure_ascii=False, indent=1)

    # 人读版
    lines = [f"# 视频选题库（自动生成 {datetime.datetime.now():%Y-%m-%d %H:%M}，共 {len(topics)} 条）", ""]
    tracks = {}
    for t in topics:
        tracks.setdefault(t["track"], []).append(t)
    for track, items in sorted(tracks.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"\n## {track}（{len(items)} 条）")
        for t in items[:8]:
            lines.append(f"- [{t['source']}|评分{t['score']}] {t['name']}")
            lines.append(f"    钩子：{t['hook']} ｜ {t['url']}")
    open(f"{HUB}/video/topic_bank.md", "w").write("\n".join(lines))
    print(f"选题库已生成：{len(topics)} 条 → video/topic_bank.{{json,md}}")
    print("赛道分布：" + ", ".join(f"{k}{len(v)}" for k, v in
          sorted(tracks.items(), key=lambda kv: -len(kv[1]))))

if __name__ == "__main__":
    main()
