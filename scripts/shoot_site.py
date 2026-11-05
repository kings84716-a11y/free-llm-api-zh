#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shoot_site.py — 无头浏览器自动截取榜单网站截图（全页 + 首屏）
供视频/社媒使用，无需人工打开浏览器。
"""
import asyncio, os, sys
from playwright.async_api import async_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(BASE, "video", "shots")
os.makedirs(SHOTS, exist_ok=True)

URLS = [
    ("https://kings84716-a11y.github.io/free-llm-api-zh/", "site_full.png", True, 1440, 900),
    ("https://kings84716-a11y.github.io/free-llm-api-zh/", "site_fold.png", False, 1440, 900),
    # 移动端竖屏视口（卡片自动单列，适合短视频）。只截视口，不做超长 full_page
    ("https://kings84716-a11y.github.io/free-llm-api-zh/", "mobile_fold.png", False, 430, 932),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--force-color-profile=srgb"],
        )
        for url, name, full, vw, vh in URLS:
            page = await browser.new_page(viewport={"width": vw, "height": vh},
                                          device_scale_factor=2, is_mobile=(vw < 700))
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(2500)  # 等字体/卡片渲染
            out = os.path.join(SHOTS, name)
            await page.screenshot(path=out, full_page=full, type="png")
            print("saved", out)
            await page.close()
        await browser.close()

asyncio.run(main())
