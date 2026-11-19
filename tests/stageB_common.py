"""Shared Playwright setup for the Stage B tests: library routing from /tmp/libs, blocked fonts, stubbed downloads."""
import base64, os
L = '/tmp/libs/'
MAP = {'three.min.js': L + 'three-0.128.0/package/build/three.min.js',
       'OrbitControls.js': L + 'three-0.128.0/package/examples/js/controls/OrbitControls.js',
       'jszip.min.js': L + 'jszip-3.10.1/package/dist/jszip.min.js',
       'jspdf.umd.min.js': L + 'jspdf-2.5.1/package/dist/jspdf.umd.min.js'}
URL = 'file:///home/claude/umpan-lab/index.html'
HERE = os.path.dirname(os.path.abspath(__file__))
STUB = """window.__saved={}; window.claude={use: async n => n==='downloads' ? {save: async ({filename,data}) => { window.__saved[filename]=data; return {status:'saved'}; }} : null};"""
PULL = """async () => { const out={}; for(const [k,v] of Object.entries(window.__saved)){
  if(typeof v==='string') out[k]={t:'text',d:v};
  else { const b = v instanceof Blob ? v : new Blob([v]); const buf=new Uint8Array(await b.arrayBuffer()); let s=''; for(let i=0;i<buf.length;i+=32768) s+=String.fromCharCode.apply(null,buf.subarray(i,i+32768)); out[k]={t:'b64',d:btoa(s)}; } }
  window.__saved={}; return out; }"""
LAUNCH = ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist']


class Checker:
    def __init__(self): self.fails = []
    def __call__(self, cond, msg):
        print(('PASS ' if cond else 'FAIL ') + msg)
        if not cond: self.fails.append(msg)


async def new_page(browser, w, h, errs, stub=True, hash_=''):
    pg = await browser.new_page(viewport={'width': w, 'height': h})
    pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and 'ERR_FAILED' not in m.text and 'boom' not in m.text and errs.append('console: ' + m.text))
    async def route(r):
        u = r.request.url
        for k, v in MAP.items():
            if u.endswith(k): return await r.fulfill(path=v, content_type='application/javascript')
        if 'fonts' in u: return await r.abort()
        await r.continue_()
    await pg.route('**/*', route)
    if stub: await pg.add_init_script(STUB)
    await pg.goto(URL + hash_); await pg.wait_for_timeout(2200)
    return pg


async def pull(pg, out):
    files = await pg.evaluate(PULL); res = {}
    for k, v in files.items():
        data = v['d'].encode() if v['t'] == 'text' else base64.b64decode(v['d'])
        open(os.path.join(out, k), 'wb').write(data); res[k] = data
    return res


async def mode(pg, m, wait=900):
    await pg.click(f'#tab-{m}'); await pg.wait_for_timeout(wait)


async def menu(pg, which, item_selector, wait=700):
    """Open File / Export menu and click an item in it."""
    await pg.click(f'#{which} > summary'); await pg.wait_for_timeout(150)
    await pg.click(item_selector); await pg.wait_for_timeout(wait)


async def preset(pg, k, wait=700):
    await menu(pg, 'fileMenu', f'[data-preset={k}]', wait)


async def open_saved(pg, name, wait=900):
    await pg.click('#fileMenu > summary'); await pg.wait_for_timeout(150)
    await pg.select_option('#mine', name); await pg.wait_for_timeout(wait)
