#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_intro.py — 生成片头/片尾卡片图（1920x1080 横屏 + 1080x1920 竖屏）"""
import os
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "video", "shots", "cards")
os.makedirs(OUT, exist_ok=True)

URL = "https://kings84716-a11y.github.io/free-llm-api-zh/"

def card_html(title, sub, tag):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{background:#0d1117;color:#e6edf3;font-family:'Noto Sans CJK SC',sans-serif;
      display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;text-align:center;padding:6%}}
    .tag{{color:#3fb950;border:1px solid #234a2e;border-radius:20px;padding:8px 22px;font-size:calc(1vw + 14px);margin-bottom:5vh}}
    h1{{font-size:calc(3vw + 34px);background:linear-gradient(90deg,#58a6ff,#3fb950);
      -webkit-background-clip:text;background-clip:text;color:transparent;line-height:1.3;margin-bottom:3vh}}
    p{{color:#8b949e;font-size:calc(1.2vw + 18px);max-width:80%}}
    .url{{margin-top:5vh;color:#58a6ff;font-family:monospace;font-size:calc(1vw + 16px)}}
    </style></head><body>
    <div class="tag">{tag}</div><h1>{title}</h1><p>{sub}</p>
    <div class="url">{URL}</div></body></html>"""

CARDS = [
    ("intro", "全网免费大模型 API 实测榜", "每天真实请求实测 · 谁活着/额度多少/谁改收费", "免费开源"),
    ("outro", "收藏起来，每天自动更新", "GitHub 开源 · 一键接入 · 评论区告诉我想测哪家", "关注不迷路"),
]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
    for name, title, sub, tag in CARDS:
        html = card_html(title, sub, tag)
        hp = os.path.join(OUT, f"{name}.html")
        open(hp, "w").write(html)
        for w, h, suffix in [(1920,1080,"h"),(1080,1920,"v")]:
            pg = b.new_page(viewport={"width":w,"height":h}, device_scale_factor=2)
            pg.goto("file://"+hp); pg.wait_for_timeout(800)
            pg.screenshot(path=os.path.join(OUT,f"{name}_{suffix}.png"))
            pg.close()
            print("OK",f"{name}_{suffix}.png")
    b.close()
