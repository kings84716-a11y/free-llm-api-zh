#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shoot_sources.py — 截取能证明“免费”的官网真实页面（避开登录墙）
只抓带 free/$0/免费 字样的公开页，自动关 cookie 弹窗。
"""
import asyncio, os
from playwright.async_api import async_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "video", "shots", "sources")
os.makedirs(OUT, exist_ok=True)

# 优先选无需登录、能直接看到免费证据的公开页面
TARGETS = [
    # OpenRouter 免费模型目录（$0 / free 标签）
    ("https://openrouter.ai/models?max_price=0", "openrouter_free.png"),
    # NVIDIA 免费推理首页（Free inference 字样+模型列表）
    ("https://build.nvidia.com/", "nvidia_free.png"),
    # Groq 定价页（公开，写免费额度，不是登录墙）
    ("https://groq.com/pricing/", "groq_pricing.png"),
    # Google AI Gemini API 文档/免费档说明
    ("https://ai.google.dev/gemini-api/docs/rate-limits", "gemini_limits.png"),
    # Cloudflare Workers AI 定价（免费 neuron 额度）
    ("https://developers.cloudflare.com/workers-ai/platform/pricing/", "cloudflare_pricing.png"),
]

# 常见 cookie/同意按钮文案
COOKIE_BTNS = ["Accept All","Accept all","Accept","Reject All","Reject optional",
               "I agree","Got it","同意","接受","全部接受","允许全部"]

async def dismiss_cookie(page):
    for txt in COOKIE_BTNS:
        try:
            btn = page.get_by_role("button", name=txt)
            if await btn.count() > 0 and await btn.first.is_visible():
                await btn.first.click(timeout=3000); await page.wait_for_timeout(800); return
        except Exception:
            pass
    # 兜底：找含 accept/cookie 的按钮
    try:
        await page.click("button:has-text('ccept')", timeout=2000)
    except Exception:
        pass

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx = await browser.new_context(
            viewport={"width":1440,"height":900}, locale="zh-CN",
            device_scale_factor=2)
        page = await ctx.new_page()
        for url, name in TARGETS:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(3500)
                await dismiss_cookie(page)
                await page.wait_for_timeout(1200)
                await page.screenshot(path=os.path.join(OUT,name), full_page=False)
                print("OK", name)
            except Exception as e:
                print("FAIL", name, str(e)[:120])
        await browser.close()

asyncio.run(main())
