import asyncio
from playwright.async_api import async_playwright
exec(open('check.py').read().split('async def main')[0])
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg=await b.new_page()
        async def route(r):
            u=r.request.url
            for k,v in MAP.items():
                if u.endswith(k): return await r.fulfill(path=v, content_type='application/javascript')
            if 'fonts' in u: return await r.abort()
            await r.continue_()
        await pg.route('**/*',route)
        await pg.goto('file:///home/claude/team/index_v4.html'); await pg.wait_for_timeout(2500)
        print(await pg.evaluate("(()=>{const t0=performance.now(); causticTex(); return performance.now()-t0})()"))
        # exact shell volume using radii-wall inner loft vs A*wall
        print(await pg.evaluate("""(()=>{const p=cache.p; const q=Object.assign({},p,{top:p.top-p.wall,bot:p.bot-p.wall,halfW:p.halfW-p.wall,tailR:Math.max(p.tailR-p.wall,0.01)}); const Vi=massProps(buildBody(q).tris).V; return {approxShell:cache.A.bm.A*p.wall, loftShell:cache.A.bm.V-Vi}})()"""))
        await b.close()
asyncio.run(main())
