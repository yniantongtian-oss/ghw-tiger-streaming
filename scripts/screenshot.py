"""Headless screenshot of the running Streamlit dashboard."""
import sys, asyncio
from playwright.async_api import async_playwright
async def main(url, out):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1400, "height": 1000})
        await pg.goto(url); await pg.wait_for_selector("text=Latest events", timeout=60000); await pg.wait_for_timeout(6000)
        await pg.screenshot(path=out, full_page=True); await b.close()
asyncio.run(main(sys.argv[1], sys.argv[2]))
