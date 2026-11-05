#!/usr/bin/env python3
import asyncio, os
from playwright.async_api import async_playwright
OUT = "/home/ubuntu/free-api-hub/video/shots/sources"
JOBS = [
    ("https://ai.google.dev/gemini-api/docs/pricing", "gemini_pricing.png"),
    ("https://groq.com/pricing/", "groq_pricing2.png"),
]
COOKIE = ["Accept All","Accept all","Reject All","Accept","Reject optional","Got it","同意","接受"]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
        pg = await (await b.new_context(viewport={"width":1440,"height":900},locale="zh-CN",device_scale_factor=2)).new_page()
        for url,name in JOBS:
            try:
                await pg.goto(url, wait_until="domcontentloaded", timeout=40000)
                await pg.wait_for_timeout(4000)
                for t in COOKIE:
                    try:
                        el=pg.get_by_role("button",name=t)
                        if await el.count()>0 and await el.first.is_visible():
                            await el.first.click(timeout=2500); await pg.wait_for_timeout(700); break
                    except Exception: pass
                await pg.wait_for_timeout(1000)
                await pg.screenshot(path=os.path.join(OUT,name))
                print("OK",name)
            except Exception as e:
                print("FAIL",name,str(e)[:100])
        await b.close()
asyncio.run(main())
