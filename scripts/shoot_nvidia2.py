#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
OUT="/home/ubuntu/free-api-hub/video/shots/sources/nvidia_free.png"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx=await b.new_context(viewport={"width":1440,"height":900},locale="en-US",device_scale_factor=2)
        pg=await ctx.new_page()
        # 预置 cookie 同意，尽量不弹
        await pg.add_init_script("window.localStorage.setItem('cookie-consent','true');")
        await pg.goto("https://build.nvidia.com/",wait_until="commit",timeout=45000)
        await pg.wait_for_timeout(5000)
        # 强力移除所有弹窗/遮罩
        for _ in range(3):
            try:
                await pg.evaluate("""() => {
                  document.querySelectorAll('[class*=cookie],[class*=Cookie],[class*=consent],[class*=Consent],[role=dialog],[class*=modal],[class*=overlay],[class*=backdrop]').forEach(e=>e.remove());
                  document.body.style.overflow='auto';
                }""")
            except Exception: pass
            await pg.wait_for_timeout(800)
        await pg.wait_for_timeout(1500)
        await pg.screenshot(path=OUT)
        print("OK",OUT)
        await b.close()
asyncio.run(main())
