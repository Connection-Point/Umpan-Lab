"""UX acceptance: keyboard-only walk (Tab through app bar, mode tabs, first group), :focus-visible check,
contrast sweep of all visible text in every mode, delete-dialog keyboard, menu keyboard. Screens ux_accept_kb_*.png.
Run: python3 -I ux_accept_a11y.py"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.async_api import async_playwright
from stageB_common import LAUNCH, new_page, mode, HERE

SHOT = lambda n: os.path.join(HERE, f'ux_accept_{n}.png')

ACTIVE = r"""(()=>{ const e=document.activeElement; if(!e||e===document.body) return {sel:'body'}; const cs=getComputedStyle(e); const r=e.getBoundingClientRect();
  const name=(e.getAttribute('aria-label')||e.labels?.[0]?.innerText||e.innerText||e.value||'').trim().slice(0,30);
  return {sel:e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(e.className&&typeof e.className==='string'?'.'+e.className.split(' ')[0]:''), name,
   outline:cs.outlineStyle+' '+cs.outlineWidth+' '+cs.outlineColor, shadow:cs.boxShadow, fv:e.matches(':focus-visible'),
   inView:r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth&&r.width>0, rect:[Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)]}; })()"""

CONTRAST = r"""(()=>{ const L=c=>{c/=255;return c<=.03928?c/12.92:((c+.055)/1.055)**2.4}; const lum=a=>.2126*L(a[0])+.7152*L(a[1])+.0722*L(a[2]);
 const P=s=>{const m=s.match(/[\d.]+/g); return m?m.map(Number):[0,0,0,0]}; const blend=(f,b)=>{const a=f[3]===undefined?1:f[3]; return [0,1,2].map(i=>f[i]*a+b[i]*(1-a));};
 function bg(e){ const stack=[]; for(let n=e;n;n=n.parentElement){ const c=P(getComputedStyle(n).backgroundColor); if(c.length<4||c[3]>0) stack.push(c); if(c.length<4||c[3]>=1) break; if(getComputedStyle(n).backgroundImage!=='none') return null; }
   let b=[255,255,255]; for(let i=stack.length-1;i>=0;i--) b=blend(stack[i],b); return b; }
 const out=[]; const seen=new Set();
 for(const e of document.querySelectorAll('body *')){ if(['SCRIPT','STYLE','CANVAS','svg','OPTION'].includes(e.tagName)||e.closest('svg')) continue;
  const own=[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()); if(!own&&!['INPUT','SELECT','TEXTAREA'].includes(e.tagName)) continue;
  const r=e.getBoundingClientRect(); if(!r.width||!r.height||r.bottom<0||r.top>innerHeight) continue; const cs=getComputedStyle(e); if(cs.visibility==='hidden'||+cs.opacity===0) continue;
  if(e.closest('#view')&&!e.closest('.viewbar,.transport,#swimInfo,#strikeToasts,.legend')) continue;
  const b=bg(e); if(!b) continue; let f=P(cs.color); f=blend(f,b); const op=+cs.opacity;
  const l1=lum(f),l2=lum(b); const cr=(Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05); const fs=parseFloat(cs.fontSize), bold=+cs.fontWeight>=700;
  const need=(fs>=24||(fs>=18.66&&bold))?3:4.5; const txt=(e.innerText||e.value||e.placeholder||'').trim().slice(0,30);
  const key=cs.color+'|'+b.join(',')+'|'+fs;
  if(cr*(op<1?op:1)<need && !seen.has(key)){ seen.add(key); out.push({sel:e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(typeof e.className==='string'&&e.className?'.'+e.className.split(' ')[0]:''),txt,cr:+cr.toFixed(2),fs,color:cs.color,bg:'rgb('+b.map(Math.round).join(',')+')',opacity:cs.opacity}); }
 } return out; })()"""


async def main():
    res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=LAUNCH)
        errs = []
        pg = await new_page(b, 1440, 880, errs)
        # keyboard walk from the top
        await pg.evaluate("document.activeElement.blur()")
        walk = []
        for i in range(30):
            await pg.keyboard.press('Tab'); await pg.wait_for_timeout(60)
            a = await pg.evaluate(ACTIVE); walk.append(a)
            if i in (1, 4, 6, 12, 20): await pg.screenshot(path=SHOT(f'kb_tab{i+1:02d}'))
        res['walk'] = walk
        for i, a in enumerate(walk):
            print(f"{i+1:2d} {a['sel'][:38]:38s} {a.get('name','')[:26]:26s} fv={a.get('fv')} out={a.get('outline','')[:40]} inView={a.get('inView')}")
        # tab arrow nav on modes
        await pg.focus('#tab-design'); await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(500)
        res['arrow'] = await pg.evaluate("[document.activeElement.id, location.hash]")
        await pg.keyboard.press('Enter'); await pg.wait_for_timeout(800)
        res['arrow_enter'] = await pg.evaluate("[document.activeElement.id, location.hash]")
        print('arrow from Design tab ->', res['arrow'], 'after Enter', res['arrow_enter'])
        await mode(pg, 'design', 500)
        # File menu by keyboard
        await pg.focus('#fileMenu > summary'); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(250)
        await pg.keyboard.press('ArrowDown'); await pg.wait_for_timeout(100)
        res['menu_kb'] = await pg.evaluate(ACTIVE); await pg.screenshot(path=SHOT('kb_filemenu'))
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(150)
        res['menu_esc'] = await pg.evaluate("[document.getElementById('fileMenu').open, document.activeElement.tagName+'#'+document.activeElement.id+document.activeElement.parentElement.id]")
        print('menu arrow ->', res['menu_kb']['sel'], res['menu_kb']['name'], 'esc ->', res['menu_esc'])
        # accordion header keyboard
        hdr = await pg.evaluate("(()=>{const e=document.querySelector('#left summary, #left [aria-expanded]'); return e? e.outerHTML.slice(0,200):null})()")
        print('group header:', hdr)
        # contrast sweep in each mode + swim
        for m in ['design', 'analyse', 'simulate', 'release']:
            await mode(pg, m, 1300)
            res['contrast_' + m] = await pg.evaluate(CONTRAST)
        await mode(pg, 'simulate', 600); await pg.click('#swimBtn'); await pg.wait_for_timeout(2000)
        await pg.click('#strikeBtn')
        for i in range(60):
            await pg.wait_for_timeout(200)
            if await pg.evaluate("document.querySelectorAll('#strikeToasts .stoast').length"): break
        res['contrast_strike'] = await pg.evaluate(CONTRAST)
        await pg.click('#swimBtn')
        for k, v in res.items():
            if k.startswith('contrast'):
                print('==', k, len(v))
                for c in v: print('   ', c)
        # Released lock state look
        await mode(pg, 'release', 1000)
        res['errors'] = errs; print('errors', errs)
        await b.close()
    json.dump(res, open('/tmp/ux_accept/a11y.json', 'w'), indent=1)

asyncio.run(main())
