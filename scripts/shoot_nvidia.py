#!/usr/bin/env python3
import asyncio, os
from playwright.async_api import async_playwright
OUT="/home/ubuntu/free-api-hub/video/shots/sources/nvidia_free.png"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx=await b.new_context(viewport={"width":1440,"height":900},locale="zh-CN",device_scale_factor=2)
        pg=await ctx.new_page()
        await pg.goto("https://build.nvidia.com/",wait_until="domcontentloaded",timeout=45000)
        await pg.wait_for_timeout(4000)
        for t in ["Accept All","Reject Optional","Accept","Reject All"]:
            try:
                el=pg.get_by_role("button",name=t)
                if await el.count()>0 and await el.first.is_visible():
                    await el.first.click(timeout=3000); await pg.wait_for_timeout(1500); break
            except Exception: pass
        # 再兜底用 JS 移除可能残留的弹窗
        await pg.evaluate("document.querySelectorAll('[class*=cookie i],[class*=consent i],[role=dialog]').forEach(e=>e.remove())").catch if False else None
        try:
            await pg.evaluate("document.querySelectorAll('[class*=cookie],[class*=consent],[role=dialog]').forEach(e=>e.remove())")
        except Exception: pass
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=OUT)
        print("OK",OUT)
        await b.close()
asyncio.run(main())
