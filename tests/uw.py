import asyncio
from playwright.async_api import async_playwright
exec(open('check.py').read().split('async def main')[0])
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':1440,'height':880})
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        async def route(r):
            u=r.request.url
            for k,v in MAP.items():
                if u.endswith(k): return await r.fulfill(path=v, content_type='application/javascript')
            if 'fonts' in u: return await r.abort()
            await r.continue_()
        await pg.route('**/*',route)
        await pg.goto('file:///home/claude/umpan-lab/index.html'); await pg.wait_for_timeout(2500)
        print('kpis:', await pg.inner_text('#kOdds'), '|', await pg.inner_text('#kReel'), await pg.inner_text('#kReelS'))
        await pg.click('.tab[data-t=pSim]'); await pg.wait_for_timeout(300)
        print('sim:', await pg.inner_text('#simRes'))
        await pg.click('#swimBtn'); await pg.wait_for_timeout(3500)
        print('hud:', await pg.inner_text('#swimInfo'))
        await pg.screenshot(path='uw1.png')
        await pg.click('#strikeBtn'); await pg.wait_for_timeout(2600)
        await pg.screenshot(path='uw2.png')
        await pg.wait_for_timeout(5000)
        print('card:', (await pg.inner_text('#strikeCard'))[:300])
        await pg.screenshot(path='uw3.png')
        for st in ['steady','burnkill','rip','pump']:
            await pg.evaluate(f"P.style='{st}'; changed()"); await pg.wait_for_timeout(300)
            print(st, (await pg.inner_text('#simRes'))[:230])
        print('errors:',errs)
        await b.close()
asyncio.run(main())
