import asyncio, sys
from playwright.async_api import async_playwright
L='/tmp/libs/'
MAP={'three.min.js':L+'three-0.128.0/package/build/three.min.js','OrbitControls.js':L+'three-0.128.0/package/examples/js/controls/OrbitControls.js','jszip.min.js':L+'jszip-3.10.1/package/dist/jszip.min.js'}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':1440,'height':880})
        errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.on('console',lambda m: m.type=='error' and errs.append(m.text))
        async def route(r):
            u=r.request.url
            for k,v in MAP.items():
                if u.endswith(k): return await r.fulfill(path=v, content_type='application/javascript')
            if 'fonts' in u: return await r.abort()
            await r.continue_()
        await pg.route('**/*',route)
        await pg.goto('file:///home/claude/umpan-lab/index.html'); await pg.wait_for_timeout(2500)
        print('status:',await pg.inner_text('#stBig'),await pg.inner_text('#stSub'),'| mass',await pg.inner_text('#kMass'),'| disp',await pg.inner_text('#kDisp'),'| depth',await pg.inner_text('#kDepth'),'| stab',await pg.inner_text('#kStab'),'| rest',await pg.inner_text('#kRest'))
        await pg.screenshot(path='/home/claude/tests/shot1.png')
        for k in ['crank70','square60','minnow110']:
            await pg.select_option('#preset',k); await pg.wait_for_timeout(600)
            print(k, await pg.inner_text('#stBig'),await pg.inner_text('#stSub'),await pg.inner_text('#kMass'),await pg.inner_text('#kDepth'),await pg.inner_text('#kStab'))
        await pg.screenshot(path='/home/claude/tests/shot2.png')
        await pg.select_option('#preset','toman90'); await pg.wait_for_timeout(500)
        print('checks:', await pg.inner_text('#checks'))
        print('pause/swim:', await pg.inner_text('#kPause'), '|', await pg.inner_text('#kSwim'), await pg.inner_text('#kSwimS'))
        await pg.click('#swimBtn'); await pg.click('.tab[data-t=pSim]'); await pg.wait_for_timeout(1700)
        print('sim:', await pg.inner_text('#simRes'))
        await pg.screenshot(path='/home/claude/tests/shot3.png')
        # stress: tangle case
        await pg.evaluate("P.bellyX=70; P.hookB='2/0'; changed()"); await pg.wait_for_timeout(400)
        print('tangle checks:', [l for l in (await pg.inner_text('#checks')).split('\n') if 'hook' in l.lower()][:3])
        # test zip generation path without downloads (DL null -> toast)
        await pg.click('#jsonBtn'); await pg.wait_for_timeout(300)
        print('modal shown:', await pg.is_visible('#modal'))
        print('errors:',errs)
        await b.close()
asyncio.run(main())
