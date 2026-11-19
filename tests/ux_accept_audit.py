"""UX acceptance audit (Stage C) for Umpan Lab v5. Screens per viewport x mode, swim + forced strike,
overflow/clipping, overlap with the 3D view, unlabeled inputs, console errors. Writes ux_accept_*.png and
/tmp/ux_accept/audit.json. Run: python3 -I ux_accept_audit.py"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.async_api import async_playwright
from stageB_common import LAUNCH, new_page, mode, HERE

OUT = '/tmp/ux_accept'; os.makedirs(OUT, exist_ok=True)
SHOT = lambda n: os.path.join(HERE, f'ux_accept_{n}.png')
VPS = [(1440, 880), (1280, 800), (1024, 768), (390, 844)]

# visible elements whose content is clipped (scrollWidth > clientWidth and overflow hides it / text-overflow)
CLIP = r"""(()=>{ const out=[]; const vis=e=>{const r=e.getBoundingClientRect(); const cs=getComputedStyle(e); return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none';};
 for(const e of document.querySelectorAll('body *')){ if(!vis(e)||e.tagName==='CANVAS'||e.tagName==='svg'||e.closest('svg')) continue;
   const cs=getComputedStyle(e); const sw=e.scrollWidth, cw=e.clientWidth;
   if(sw>cw+2 && cw>0){ const ox=cs.overflowX; if(ox==='auto'||ox==='scroll') { if(!['HTML','BODY'].includes(e.tagName)) out.push({kind:'hscroll',sel:sig(e),sw,cw}); } else out.push({kind:'clip',sel:sig(e),sw,cw,ox,txt:(e.innerText||e.value||'').slice(0,50)}); }
   if((e.tagName==='SELECT')&&e.options.length){ const t=e.options[e.selectedIndex]?.text||''; const c=document.createElement('canvas').getContext('2d'); c.font=cs.font; const tw=c.measureText(t).width; const avail=e.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight)-14; if(tw>avail+1) out.push({kind:'select-trunc',sel:sig(e),txt:t,tw:Math.round(tw),avail:Math.round(avail)}); }
   if(e.tagName==='INPUT'&&['text','number'].includes(e.type)&&e.value){ const c=document.createElement('canvas').getContext('2d'); c.font=cs.font; const tw=c.measureText(e.value).width; const avail=e.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight); if(tw>avail+1) out.push({kind:'input-trunc',sel:sig(e),txt:e.value,tw:Math.round(tw),avail:Math.round(avail)}); }
 }
 function sig(e){ return e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(e.className&&typeof e.className==='string'?'.'+e.className.trim().split(/\s+/).join('.'):''); }
 return out; })()"""

# elements painted over the 3D canvas rect that are not its known overlays
OVER = r"""(()=>{ const c=document.querySelector('#view canvas')||document.querySelector('canvas'); if(!c) return null; const R=c.getBoundingClientRect();
 const known=['.viewbar','.transport','#swimInfo','#strikeToasts','.legend','#legend','.splitter','.layers'];
 const res=[]; const seen=new Set();
 for(let x=R.left+4;x<R.right;x+=24) for(let y=R.top+4;y<R.bottom;y+=24){ const e=document.elementFromPoint(x,y); if(!e||e===c||e.contains(c)) continue;
   if(known.some(k=>e.closest(k))) continue; const s=e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(typeof e.className==='string'&&e.className?'.'+e.className.split(' ')[0]:''); if(!seen.has(s)){seen.add(s);res.push(s);} }
 return {canvas:{l:R.left,t:R.top,w:R.width,h:R.height},others:res}; })()"""

UNLAB = r"""(()=>{ const bad=[]; for(const e of document.querySelectorAll('input,select,textarea')){ if(e.type==='hidden'||e.type==='file') continue;
  const r=e.getBoundingClientRect(); const visible=r.width>0&&r.height>0;
  const ok=e.labels?.length||e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')||e.title||e.closest('label');
  if(!ok) bad.push({id:e.id,type:e.type,visible,name:e.name||'',ph:e.placeholder||''}); }
  return {total:document.querySelectorAll('input,select,textarea').length,bad}; })()"""

RECTS = r"""sels=>sels.map(s=>{const e=document.querySelector(s); if(!e) return [s,null]; const r=e.getBoundingClientRect(); const cs=getComputedStyle(e); return [s, cs.display==='none'||!r.width?null:{l:Math.round(r.left),t:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom)}];})"""


async def audit(pg, tag, report):
    report[tag] = {'clip': await pg.evaluate(CLIP), 'over': await pg.evaluate(OVER),
                   'sw': await pg.evaluate('[document.documentElement.scrollWidth, innerWidth]'),
                   'rects': await pg.evaluate(RECTS, ['.appbar', '#specstrip', '.viewbar', '.transport', '#swimInfo', '#strikeToasts', '#view', '.ntabs'])}


async def main():
    report = {}; errs_all = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=LAUNCH)
        for w, h in VPS:
            errs = []
            pg = await new_page(b, w, h, errs)
            report[f'unlabeled_{w}'] = await pg.evaluate(UNLAB)
            for m in ['design', 'analyse', 'simulate', 'release']:
                await mode(pg, m, 1400)
                await pg.screenshot(path=SHOT(f'{m}_{w}'))
                await audit(pg, f'{m}_{w}', report)
                if m == 'release':
                    report[f'unlabeled_release_{w}'] = await pg.evaluate(UNLAB)
                    await pg.screenshot(path=SHOT(f'release_full_{w}'), full_page=True)
                if m == 'design' and w == 390:
                    for t in ['results', 'checks']:
                        await pg.click(f'.ntabs [data-ntab={t}]'); await pg.wait_for_timeout(400)
                        await pg.screenshot(path=SHOT(f'design_{t}_{w}'))
                        await audit(pg, f'design_{t}_{w}', report)
                    await pg.click('.ntabs [data-ntab=params]'); await pg.wait_for_timeout(300)
                    await pg.evaluate("[...document.querySelectorAll('.grp, details')].forEach(()=>0)")
            # simulate: swim + strike
            await mode(pg, 'simulate', 900)
            await pg.click('#swimBtn'); await pg.wait_for_timeout(2500)
            await pg.screenshot(path=SHOT(f'swim_{w}')); await audit(pg, f'swim_{w}', report)
            await pg.click('#strikeBtn')
            for i in range(60):
                await pg.wait_for_timeout(200)
                if await pg.evaluate("document.querySelectorAll('#strikeToasts .stoast').length"): break
            await pg.wait_for_timeout(300)
            await pg.screenshot(path=SHOT(f'strike_{w}')); await audit(pg, f'strike_{w}', report)
            await pg.wait_for_timeout(3500)
            await pg.screenshot(path=SHOT(f'strike_after_{w}'))
            await pg.click('#swimBtn'); await pg.wait_for_timeout(300)
            # menus
            if w in (1024, 390):
                await mode(pg, 'design', 600)
                await pg.click('#fileMenu > summary'); await pg.wait_for_timeout(300)
                await pg.screenshot(path=SHOT(f'filemenu_{w}')); await audit(pg, f'filemenu_{w}', report)
                await pg.keyboard.press('Escape'); await pg.click('#exportMenu > summary'); await pg.wait_for_timeout(300)
                await pg.screenshot(path=SHOT(f'exportmenu_{w}')); await audit(pg, f'exportmenu_{w}', report)
                await pg.keyboard.press('Escape')
            errs_all[w] = errs
            await pg.close()
        await b.close()
    report['errors'] = errs_all
    json.dump(report, open(os.path.join(OUT, 'audit.json'), 'w'), indent=1)
    for k, v in report.items():
        if isinstance(v, dict) and 'clip' in v:
            clips = [c for c in v['clip'] if c['kind'] != 'hscroll']
            print(f'== {k}: sw={v["sw"]} clip={len(clips)} over={v["over"]["others"] if v["over"] else None}')
            for c in clips[:12]: print('   ', c)
            hs = [c for c in v['clip'] if c['kind'] == 'hscroll']
            if hs: print('    hscroll:', [(c['sel'], c['sw'], c['cw']) for c in hs][:6])
        elif k.startswith('unlabeled'):
            print(f'== {k}: total {v["total"]}, unlabeled {len(v["bad"])}', v['bad'][:8])
    print('errors:', errs_all)
    # ---- Stage C: the audit now gates (exit 1). Allowed: screen-reader-only spans; #dname, which ellipsises and carries a title.
    fails = []
    for k, v in report.items():
        if isinstance(v, dict) and 'clip' in v:
            bad = [c for c in v['clip'] if c['kind'] != 'hscroll' and not c['sel'].startswith('span.sr') and not c['sel'].startswith('input#dname')
                   and not (c['sel'] == 'div.doc' and k.endswith('_390'))]
            if bad: fails.append(f'{k}: clipped {bad[:3]}')
            if v['sw'][0] > v['sw'][1]: fails.append(f'{k}: page scrolls sideways {v["sw"]}')
            hs = [c for c in v['clip'] if c['kind'] == 'hscroll' and 'bomT' in c['sel']]
            if hs and not k.endswith('_390'): fails.append(f'{k}: BOM scrolls sideways {hs}')
        elif k.startswith('unlabeled') and v['bad']: fails.append(f'{k}: unlabeled inputs {v["bad"][:3]}')
    for w, e in errs_all.items():
        if e: fails.append(f'{w}: page errors {e[:2]}')
    print('\n' + ('ALL PASS' if not fails else f'{len(fails)} FAIL(S):\n  ' + '\n  '.join(fails)))
    sys.exit(1 if fails else 0)

asyncio.run(main())
