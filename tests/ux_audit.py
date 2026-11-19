import asyncio, json
from playwright.async_api import async_playwright
exec(open('/home/claude/tests/check.py').read().split('async def main')[0])
URL='file:///home/claude/team/index_v4.html'
async def open_page(b,w,h):
    pg=await b.new_page(viewport={'width':w,'height':h})
    async def route(r):
        u=r.request.url
        for k,v in MAP.items():
            if u.endswith(k): return await r.fulfill(path=v, content_type='application/javascript')
        if 'fonts' in u: return await r.abort()
        await r.continue_()
    await pg.route('**/*',route)
    await pg.goto(URL); await pg.wait_for_timeout(2000)
    return pg
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg=await open_page(b,1440,880)
        info=await pg.evaluate("""()=>{
          const c=document.getElementById('controls');
          const ins=[...document.querySelectorAll('input,select,button')];
          const unlabeled=ins.filter(e=>{ if(e.type==='hidden'||e.hidden) return false;
             const lab=e.labels&&e.labels.length; return !lab && !e.getAttribute('aria-label') && !(e.tagName==='BUTTON'&&e.textContent.trim()) && !e.title;}).map(e=>e.tagName+':'+e.type);
          return {ranges:document.querySelectorAll('input[type=range]').length,
            numbers:document.querySelectorAll('input[type=number]').length,
            selects:document.querySelectorAll('select').length,
            controlsScroll:c.scrollHeight, controlsClient:c.clientHeight,
            headerH:document.querySelector('header').offsetHeight,
            unlabeled:unlabeled.length, unlabeledSample:unlabeled.slice(0,8),
            ariaCount:document.querySelectorAll('[aria-label],[aria-live],[role]').length,
            canvasAria:!!document.querySelector('#view canvas[aria-label]'),
            focusStyles:[...document.styleSheets].filter(s=>!s.href).flatMap(s=>[...s.cssRules].map(r=>r.cssText)).filter(t=>t.includes(':focus')).length,
            pane:document.querySelector('.profile').offsetHeight};
        }""")
        print(json.dumps(info,indent=1))
        # keyboard: tab through first 8 stops
        stops=[]
        for i in range(10):
            await pg.keyboard.press('Tab')
            stops.append(await pg.evaluate("()=>{const e=document.activeElement;return e.tagName+(e.id?'#'+e.id:'')+(e.type?':'+e.type:'')}"))
        print('tab order:',stops)
        await pg.screenshot(path='/home/claude/tests/ux_focus.png', clip={'x':0,'y':0,'width':1440,'height':220})
        await b.close()
        for (w,h,n) in [(1280,720,'ux_1280.png'),(1024,768,'ux_1024.png'),(390,844,'ux_390.png')]:
            b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
            pg=await open_page(b,w,h)
            hh=await pg.evaluate("document.querySelector('header').offsetHeight")
            dh=await pg.evaluate("document.documentElement.scrollHeight")
            print(n,'header',hh,'docH',dh)
            await pg.screenshot(path='/home/claude/tests/'+n, full_page=(w<1100))
            await b.close()
asyncio.run(main())
