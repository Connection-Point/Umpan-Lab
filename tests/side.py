import asyncio
from playwright.async_api import async_playwright
exec(open('check.py').read().split('async def main')[0])
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':1440,'height':880})
        async def route(r):
            u=r.request.url
            for k,v in MAP.items():
                if u.endswith(k): return await r.fulfill(path=v, content_type='application/javascript')
            if 'fonts' in u: return await r.abort()
            await r.continue_()
        await pg.route('**/*',route)
        await pg.goto('file:///home/claude/umpan-lab/index.html'); await pg.wait_for_timeout(2000)
        el=await pg.query_selector('.profile'); await el.screenshot(path='side.png')
        await b.close()
asyncio.run(main())
