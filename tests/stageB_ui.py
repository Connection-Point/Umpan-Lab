"""Stage B UI test: modes, app bar, presets, a11y, render-on-demand, swim + forced strike, toasts, splitter,
delete-confirm modal, JSON v1/v2 import, narrow layout, screenshots (stageB_*.png). Exit 1 on failure.
Run: python3 -I stageB_ui.py"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.async_api import async_playwright
from stageB_common import LAUNCH, Checker, new_page, mode, menu, preset, open_saved, pull, HERE

OUT = '/tmp/stageB_ui'; os.makedirs(OUT, exist_ok=True)
SHOT = lambda n: os.path.join(HERE, f'stageB_{n}.png')
check = Checker()

LURE_BOX = """(()=>{ const B=new THREE.Box3(); [bodyMesh,billMesh].forEach(m=>{ if(m) B.expandByObject(m); });
  const r=renderer.domElement.getBoundingClientRect(), xs=[], ys=[];
  for(const x of [B.min.x,B.max.x]) for(const y of [B.min.y,B.max.y]) for(const z of [B.min.z,B.max.z]){ const v=new THREE.Vector3(x,y,z).project(camera); xs.push(r.left+(v.x+1)/2*r.width); ys.push(r.top+(1-v.y)/2*r.height); }
  return {l:Math.min(...xs),r:Math.max(...xs),t:Math.min(...ys),b:Math.max(...ys)}; })()"""
RECT = """s=>{ const e=document.querySelector(s); if(!e) return null; const cs=getComputedStyle(e); if(cs.display==='none'||e.hidden||cs.visibility==='hidden') return null;
  const r=e.getBoundingClientRect(); return r.width&&r.height?{l:r.left,r:r.right,t:r.top,b:r.bottom}:null; }"""
def overlap(a, b):
    if not a or not b: return 0
    w = min(a['r'], b['r']) - max(a['l'], b['l']); h = min(a['b'], b['b']) - max(a['t'], b['t'])
    return max(0, w) * max(0, h)

def lum(hexrgb):
    def ch(c):
        c = c / 255; return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hexrgb; return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)
def contrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + 0.05) / (lb + 0.05)
def rgb(s):
    s = s[s.index('(') + 1:s.index(')')].split(','); return tuple(int(float(x)) for x in s[:3])


async def header_one_row(pg, w):
    r = await pg.evaluate("""(()=>{ const h=document.querySelector('.appbar').getBoundingClientRect();
      const kids=[...document.querySelectorAll('.appbar > *')].filter(e=>getComputedStyle(e).display!=='none'&&!e.hidden&&e.type!=='file').map(e=>e.getBoundingClientRect());
      return {h:h.height, right:Math.max(...kids.map(k=>k.right)), tops:kids.map(k=>Math.round(k.top)), bots:kids.map(k=>Math.round(k.bottom)), sw:document.documentElement.scrollWidth}; })()""")
    ok = r['h'] <= 53 and max(r['bots']) <= 53 and r['right'] <= w and r['sw'] <= w
    check(ok, f'app bar is one row at {w}px (height {r["h"]:.0f}, rightmost {r["right"]:.0f}, scrollWidth {r["sw"]})')


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=LAUNCH)
        errs = []
        pg = await new_page(b, 1440, 880, errs)

        # ---------- B1 app bar / modes
        await header_one_row(pg, 1440)
        tabs = await pg.evaluate("[...document.querySelectorAll('.modes [role=tab]')].map(t=>[t.textContent,t.getAttribute('aria-selected')])")
        check(await pg.get_attribute('.modes', 'role') == 'tablist' and [t[0] for t in tabs] == ['Design', 'Analyse', 'Simulate', 'Release'] and tabs[0][1] == 'true', 'mode tablist Design / Analyse / Simulate / Release with aria-selected')
        check(await pg.inner_text('#dirty') == '' and await pg.inner_text('#barRev') == 'Rev A' and await pg.inner_text('#barStatus') == 'Concept', 'app bar shows Rev, status badge, no unsaved flag at start')
        check(await pg.evaluate('W===null && FISH===null'), 'underwater world and fish still built lazily')
        await pg.screenshot(path=SHOT('design_1440'))

        # ---------- B2 spec strip
        strip = await pg.inner_text('#specstrip'); print('strip:', strip.replace('\n', ' · '))
        check('90 mm' in strip and '24.8 g' in strip and 'Floating' in strip and 'Dive 3.8' in strip and '1/0' in strip, 'spec strip: length · weight · class · dive · hooks')

        # ---------- presets via File menu
        seen = {}
        for k in ['crank70', 'square60', 'minnow110', 'toman90']:
            await preset(pg, k, 700)
            seen[k] = (await pg.inner_text('#kMass'), await pg.inner_text('#sLen'), await pg.input_value('#dname'))
            check(not await pg.evaluate("document.getElementById('fileMenu').open"), f'File menu closes after choosing {k}') if k == 'crank70' else None
        print('presets:', seen)
        check(len({v[0] for v in seen.values()}) == 4 and seen['minnow110'][1].startswith('110'), 'every preset loads (4 different weights, strip follows)')

        # ---------- every mode renders
        for m, sel in [('analyse', '#hookTable'), ('simulate', '#dive polyline'), ('release', '#relSku'), ('design', '#kMass')]:
            await mode(pg, m, 1300)
            vis = await pg.is_visible(sel)
            sel_ok = await pg.get_attribute(f'#tab-{m}', 'aria-selected') == 'true'
            h = await pg.evaluate('location.hash')
            check(vis and sel_ok and h == '#' + m, f'{m} mode renders ({sel} visible, aria-selected, hash {h})')
        await mode(pg, 'analyse', 1200)
        dfm = await pg.inner_text('#dfmList'); hk = await pg.inner_text('#hookTable')
        check('Cavity' in dfm and 'clear' in hk and 'Total' in await pg.inner_text('#massTable'), 'Analyse: mass table, hook clearance and DFM list filled')
        side_h = await pg.evaluate("document.getElementById('side').getBoundingClientRect().height")
        center_h = await pg.evaluate("document.querySelector('.center').getBoundingClientRect().height")
        check(side_h > 0.35 * center_h, f'Analyse: side profile is large ({side_h:.0f}px of {center_h:.0f}px)')
        await pg.screenshot(path=SHOT('analyse_1440'))
        await mode(pg, 'release', 1500); await pg.screenshot(path=SHOT('release_1440'))
        check(await pg.is_visible('#mStatus') and await pg.is_visible('#cwCode') and await pg.is_visible('#bomT') and await pg.is_visible('#drawPrev svg'), 'Release: revision / colourway form, BOM editor and drawing preview')
        check(not await pg.is_visible('#view'), 'Release: 3D view hidden, document uses the space')
        await mode(pg, 'design', 800)

        # ---------- B3 accordion + basic/advanced + reset
        r = await pg.evaluate("""(()=>{ const g=[...document.querySelectorAll('#controls .grp')]; return {n:g.length, names:g.map(x=>x.querySelector('.acc').firstChild.textContent), open:g.filter(x=>x.querySelector('.acc').getAttribute('aria-expanded')==='true').length}; })()""")
        check(r['names'] == ['Shape', 'Bill', 'Hardware', 'Ballast', 'Material & mold', 'Finish'] and r['open'] == 1, f'Design accordion groups {r["names"]}, one open')
        await pg.click('#g-bill-h'); await pg.wait_for_timeout(150)
        r = await pg.evaluate("[...document.querySelectorAll('#controls .acc')].filter(a=>a.getAttribute('aria-expanded')==='true').map(a=>a.id)")
        check(r == ['g-bill-h'], 'opening Bill closes Shape (accordion)')
        check(not await pg.is_visible('#p-rootX') and await pg.is_visible('#p-billLen'), 'advanced bill root hidden in Basic')
        await pg.click('#g-bill-h >> xpath=../label/input'); await pg.wait_for_timeout(100)
        check(await pg.is_visible('#p-rootX'), 'Advanced toggle reveals bill root position')
        check(await pg.inner_text('#lbl-rootX') == 'Bill root position, from nose', 'renamed label (Bill root position, from nose)')
        await pg.click('#g-shape-h'); await pg.wait_for_timeout(100)
        check(await pg.input_value('#p-halfW') == '20' and await pg.inner_text('#lbl-halfW') == 'Body width (full)', 'Body width (full) shows 2 × halfW (20 mm for halfW 10)')
        await pg.fill('#p-halfW', '24'); await pg.press('#p-halfW', 'Enter'); await pg.wait_for_timeout(500)
        check(await pg.evaluate('P.halfW') == 12, 'editing full width 24 stores internal halfW 12 (keys unchanged)')
        await pg.dblclick('#lbl-halfW'); await pg.wait_for_timeout(500)
        check(await pg.evaluate('P.halfW') == 10, 'double-click label resets to the loaded value')
        await pg.focus('#p-L'); await pg.keyboard.press(']'); await pg.wait_for_timeout(300)
        await pg.keyboard.press('Shift+]'); await pg.wait_for_timeout(400)
        check(await pg.evaluate('P.L') == 101, '] nudges +1, Shift+] +10')
        await pg.dblclick('#lbl-L'); await pg.wait_for_timeout(400)

        # ---------- a11y
        r = await pg.evaluate("""(()=>{ const bad=[]; document.querySelectorAll('input,select,textarea').forEach(e=>{ if(e.type==='file'&&e.hidden&&e.getAttribute('aria-label')) return;
            const ok=(e.labels&&e.labels.length)||e.getAttribute('aria-label')||e.getAttribute('aria-labelledby'); if(!ok) bad.push(e.id||e.outerHTML.slice(0,60)); });
          return {n:document.querySelectorAll('input,select,textarea').length,bad}; })()""")
        await mode(pg, 'release', 1200)
        r2 = await pg.evaluate("""(()=>{ const bad=[]; document.querySelectorAll('#relRoot input,#relRoot select').forEach(e=>{ const ok=(e.labels&&e.labels.length)||e.getAttribute('aria-label')||e.getAttribute('aria-labelledby'); if(!ok) bad.push(e.outerHTML.slice(0,70)); }); return {n:document.querySelectorAll('#relRoot input').length,bad}; })()""")
        await mode(pg, 'design', 600)
        print(f'labelled inputs: {r["n"]} app + {r2["n"]} release; unlabelled: {r["bad"][:5]} {r2["bad"][:3]}')
        check(not r['bad'] and not r2['bad'], 'every input / select / textarea has a programmatic label (incl. Release tables)')
        r = await pg.evaluate("""(()=>{ let fv=0; for(const sh of document.styleSheets){ try{ for(const ru of sh.cssRules) if(ru.selectorText&&ru.selectorText.includes(':focus-visible')) fv++; }catch(e){} }
          const c=renderer.domElement; return {fv, role:c.getAttribute('role'), label:c.getAttribute('aria-label'), live:['checks','stBig','strikeToasts','sessionLog','dfmList'].map(id=>document.getElementById(id).getAttribute('aria-live'))}; })()""")
        check(r['fv'] >= 1 and r['role'] == 'img' and 'mm body' in (r['label'] or '') and all(x == 'polite' for x in r['live']), f'focus-visible rules, canvas role=img "{(r["label"] or "")[:50]}…", aria-live on status / checks / toasts / log')
        await pg.focus('#tab-design'); await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(500)
        check(await pg.evaluate("document.body.dataset.mode") == 'analyse' and await pg.evaluate("document.activeElement.id") == 'tab-analyse', 'arrow keys move between mode tabs')
        outline = await pg.evaluate("getComputedStyle(document.activeElement).outlineStyle")
        check(outline == 'solid', 'keyboard focus shows a visible outline')
        await mode(pg, 'simulate', 600)
        col = await pg.evaluate("(()=>{ const s=getComputedStyle(document.getElementById('swimBtn')); return [s.color,s.backgroundColor]; })()")
        cr = contrast(rgb(col[0]), rgb(col[1])); check(cr >= 4.5, f'Swim button contrast {cr:.2f}:1 (white on {col[1]})')
        await mode(pg, 'design', 500)
        await pg.evaluate("P.ballN=0; P.hookB='6'; P.hookT='6'; changed()"); await pg.wait_for_timeout(600)
        st = await pg.evaluate("(()=>{ const s=getComputedStyle(document.getElementById('statusBox')); return [document.getElementById('stBig').textContent, s.color, s.backgroundColor]; })()")
        print('status sample:', st)
        cr = contrast(rgb(st[1]), rgb(st[2])); check(cr >= 4.5, f'status box "{st[0]}" text contrast {cr:.2f}:1')
        await pg.evaluate("P.ballN=4; P.ballD=9; P.hookB='2/0'; P.hookT='2/0'; changed()"); await pg.wait_for_timeout(600)
        st = await pg.evaluate("(()=>{ const s=getComputedStyle(document.getElementById('statusBox')); return [document.getElementById('stBig').textContent, s.color, s.backgroundColor]; })()")
        cr = contrast(rgb(st[1]), rgb(st[2])); check(cr >= 4.5, f'status box "{st[0]}" text contrast {cr:.2f}:1')
        tg = await pg.evaluate("[...document.querySelectorAll('.tag')].slice(0,1).concat([...document.querySelectorAll('.tag.est')].slice(0,1)).map(e=>{const s=getComputedStyle(e);return [s.color,s.backgroundColor]})")
        check(all(contrast(rgb(a), rgb(b_)) >= 4.5 for a, b_ in tg), 'CALC / EST tags pass AA')
        chip = await pg.evaluate("(()=>{ const s=getComputedStyle(document.getElementById('sIssues')); return [s.color,s.backgroundColor,document.getElementById('sIssues').textContent]; })()")
        check(contrast(rgb(chip[0]), rgb(chip[1])) >= 4.5, f'issue chip "{chip[2]}" passes AA')

        # ---------- issue chip → checks
        await mode(pg, 'analyse', 400)
        await pg.click('#sIssues'); await pg.wait_for_timeout(600)
        vis = await pg.evaluate(f"({RECT})('#checksSec')")
        check(await pg.evaluate("document.body.dataset.mode") == 'design' and vis and vis['t'] < 880, 'issue chip switches to Design and shows the checks')
        await pg.screenshot(path=SHOT('design_issues_1440'))
        await preset(pg, 'toman90', 700)

        # ---------- B9 render on demand (OrbitControls damping still animates)
        await pg.wait_for_timeout(800)
        n0 = await pg.evaluate('window.__renders'); await pg.wait_for_timeout(1200); n1 = await pg.evaluate('window.__renders')
        check(n1 == n0 and not await pg.evaluate('loopOn'), f'idle: no renders and loop stopped ({n0}→{n1})')
        box = await pg.evaluate("(()=>{const r=renderer.domElement.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()")
        await pg.mouse.move(box[0], box[1]); await pg.mouse.down();
        for i in range(8): await pg.mouse.move(box[0] + 12 * i, box[1] + 3 * i); await pg.wait_for_timeout(16)
        await pg.mouse.up(); n2 = await pg.evaluate('window.__renders'); await pg.wait_for_timeout(500); n3 = await pg.evaluate('window.__renders')
        stopped_after = None
        for i in range(40):   # damping decays 5 %/frame; under SwiftShader that takes a few seconds
            await pg.wait_for_timeout(250)
            if not await pg.evaluate('loopOn'): stopped_after = (i + 1) * 0.25; break
        n4 = await pg.evaluate('window.__renders'); await pg.wait_for_timeout(800); n4b = await pg.evaluate('window.__renders')
        print(f'renders: drag→{n2-n1}, damping tail (0.5 s)→{n3-n2}, loop stopped {stopped_after} s later after {n4-n3} more; idle after: {n4b-n4}')
        check(n2 > n1 and n3 > n2 + 3 and stopped_after is not None and n4b == n4, 'orbit drag renders, damping keeps rendering after release, then the loop stops')
        await pg.evaluate("P.L=91; changed()"); await pg.wait_for_timeout(400); n5 = await pg.evaluate('window.__renders')
        check(n5 > n4, 'a parameter change triggers a render')
        await pg.click('#vSide'); await pg.wait_for_timeout(400)
        check(await pg.get_attribute('#vSide', 'aria-pressed') == 'true', 'camera preset Side')
        await pg.click('#v3d'); await pg.wait_for_timeout(300)
        await pg.evaluate("P.L=90; changed()"); await pg.wait_for_timeout(400)

        # ---------- B6 simulate: Space swim, forced strike, toasts, session log, nothing over the lure
        await mode(pg, 'simulate', 800)
        await pg.screenshot(path=SHOT('simulate_1440'))
        await pg.focus('body'); await pg.evaluate("document.activeElement.blur()")
        await pg.keyboard.press('Space'); await pg.wait_for_timeout(2500)
        check(await pg.evaluate('swimming') and await pg.get_attribute('#swimBtn', 'aria-pressed') == 'true', 'Space starts the swim')
        hud = await pg.inner_text('#swimInfo'); print('hud:', hud.replace('\n', ' | '))
        check('m/s' in hud and 'depth' in hud, 'swim HUD shows speed and depth')
        r_tr = await pg.evaluate(f"({RECT})('.transport')"); r_hud = await pg.evaluate(f"({RECT})('#swimInfo')"); r_vb = await pg.evaluate(f"({RECT})('.viewbar')")
        worst = 0
        for i in range(6):
            lb = await pg.evaluate(LURE_BOX)
            worst = max(worst, overlap(lb, r_tr), overlap(lb, r_hud), overlap(lb, r_vb))
            await pg.wait_for_timeout(250)
        check(worst == 0, f'no control covers the lure during the swim (max overlap {worst:.0f} px²)')
        await pg.screenshot(path=SHOT('simulate_swim_1440'))
        await pg.click('#strikeBtn')
        for i in range(60):   # sim time runs at 0.5x and SwiftShader frames are slow
            await pg.wait_for_timeout(200)
            if await pg.evaluate("document.querySelectorAll('#strikeToasts .stoast').length"): break
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=SHOT('simulate_strike_1440'))
        toasts = await pg.inner_text('#strikeToasts'); print('toasts:', toasts.replace('\n', ' | ')[:200])
        check(any(t in toasts for t in ['Fish on!', 'Missed strike']), 'forced strike shows a toast (Fish on! / Missed strike)')
        r_to = await pg.evaluate(f"({RECT})('#strikeToasts')")
        lb = await pg.evaluate(LURE_BOX)
        check(r_to is not None and overlap(lb, r_to) == 0 and r_to['l'] < 400, f'strike toast sits bottom-left, off the lure ({r_to}, lure {lb})')
        await pg.wait_for_timeout(5500)
        mini = await pg.evaluate("[...document.querySelectorAll('#strikeToasts .stoast')].map(e=>e.classList.contains('mini'))")
        check(mini and mini[0], 'toast collapses to one line after 3 s')
        log = await pg.inner_text('#sessionLog'); stats = await pg.inner_text('#sessStats')
        print('session:', stats, '|', log.replace('\n', ' | ')[:240])
        check('strike' in stats and ('Fish on!' in log or 'Missed strike' in log), 'session log records the strike with odds')
        await pg.screenshot(path=SHOT('simulate_after_1440'))
        await pg.evaluate("document.activeElement.blur()")   # focus was on Strike; Space on a focused button activates that button
        await pg.keyboard.press('Space'); await pg.wait_for_timeout(500)
        check(not await pg.evaluate('swimming'), 'Space stops the swim')
        await pg.focus('#p-tps'); await pg.keyboard.press('Space'); await pg.wait_for_timeout(300)
        check(not await pg.evaluate('swimming'), 'Space inside an input does not toggle the swim')
        await pg.click('#swimBtn'); await pg.wait_for_timeout(600); await mode(pg, 'design', 500)
        check(not await pg.evaluate('swimming'), 'leaving Simulate stops the swim')

        # ---------- B8 splitter (resizable, persisted)
        sp = await pg.evaluate(f"({RECT})('#splitter')")
        h0 = await pg.evaluate("document.getElementById('panel').getBoundingClientRect().height")
        await pg.mouse.move((sp['l'] + sp['r']) / 2, sp['t'] + 3); await pg.mouse.down()
        await pg.mouse.move((sp['l'] + sp['r']) / 2, sp['t'] - 120, steps=6); await pg.mouse.up(); await pg.wait_for_timeout(400)
        h1 = await pg.evaluate("document.getElementById('panel').getBoundingClientRect().height")
        stored = await pg.evaluate("JSON.parse(localStorage.getItem('umpanlab.panelH.v1')||'{}')")
        check(h1 > h0 + 100 and stored.get('design') == round(h1), f'splitter drag resizes the panel {h0:.0f}→{h1:.0f}px and persists {stored}')
        await pg.focus('#splitter'); await pg.keyboard.press('ArrowDown'); await pg.wait_for_timeout(200)
        h2 = await pg.evaluate("document.getElementById('panel').getBoundingClientRect().height")
        check(abs(h2 - (h1 - 20)) < 2, 'splitter keyboard ArrowDown −20 px')
        await pg.reload(); await pg.wait_for_timeout(2200)
        h3 = await pg.evaluate("document.getElementById('panel').getBoundingClientRect().height")
        check(abs(h3 - h2) < 2, f'panel height restored after reload ({h3:.0f})')
        await pg.dblclick('#splitter'); await pg.wait_for_timeout(300)

        # ---------- delete-confirm modal
        await pg.fill('#dname', 'Delete me'); await pg.click('#saveBtn'); await pg.wait_for_timeout(400)
        await pg.click('#fileMenu > summary'); await pg.wait_for_timeout(150)
        await pg.select_option('#mine', 'Delete me'); await pg.wait_for_timeout(700)
        await pg.click('#fileMenu > summary'); await pg.wait_for_timeout(150)
        await pg.click('#delBtn'); await pg.wait_for_timeout(300)
        check(await pg.is_visible('#confirmDlg') and "Delete me" in await pg.inner_text('#cTitle') and await pg.evaluate("document.activeElement.id") == 'cCancel', 'Delete opens an in-page confirm dialog (focus on Cancel)')
        await pg.screenshot(path=SHOT('delete_confirm_1440'))
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
        check(not await pg.is_visible('#confirmDlg') and 'Delete me' in await pg.evaluate("Object.keys(readSaved())"), 'Escape cancels; the design is kept')
        await pg.click('#fileMenu > summary'); await pg.wait_for_timeout(150); await pg.select_option('#mine', 'Delete me'); await pg.wait_for_timeout(500)
        await pg.click('#fileMenu > summary'); await pg.wait_for_timeout(150); await pg.click('#delBtn'); await pg.wait_for_timeout(200)
        await pg.click('#cOk'); await pg.wait_for_timeout(300)
        check('Delete me' not in await pg.evaluate("Object.keys(readSaved())") and not await pg.is_visible('#confirmDlg'), 'confirming deletes the saved design')

        # ---------- JSON v1 / v2 import (labels changed, keys and hash not)
        await preset(pg, 'crank70', 600)
        await pg.evaluate("P.halfW=9.5; P.fat=0.41; changed()"); await pg.wait_for_timeout(500)
        await menu(pg, 'exportMenu', '#jsonBtn', 800)
        files = await pull(pg, OUT); jn = [k for k in files if k.endswith('.json')][0]; d2 = json.loads(files[jn])
        check(d2['version'] == 2 and d2['spec']['halfW'] == 9.5 and d2['spec']['fat'] == 0.41 and 'castDist' in d2['sim'], 'exported v2 JSON keeps internal keys (halfW 9.5, fat 0.41)')
        await preset(pg, 'toman90', 600)
        await pg.set_input_files('#importFile', os.path.join(OUT, jn)); await pg.wait_for_timeout(1200)
        r = await pg.evaluate("({halfW:P.halfW, fat:P.fat, L:P.L, ui:document.getElementById('p-halfW').value, fui:document.getElementById('p-fat').value, hash:null})")
        h_now = await pg.evaluate("specHash(stateNow())")
        check(r['halfW'] == 9.5 and r['fat'] == 0.41 and r['L'] == 70 and r['ui'] == '19' and r['fui'] == '41' and h_now == d2['meta']['specSha256'], f'v2 import round-trips (UI 19 mm / 41 %, same SHA-256) {r}')
        v1 = {'app': 'Umpan Lab', 'version': 1, 'name': 'v1 file', 'params': {'L': 84, 'halfW': 8, 'hookB': '2', 'wire': 0.9}, 'paint': {'back': '#112233'}}
        fn = os.path.join(OUT, 'v1.json'); json.dump(v1, open(fn, 'w'))
        await pg.set_input_files('#importFile', fn); await pg.wait_for_timeout(1200)
        r = await pg.evaluate("({L:P.L,halfW:P.halfW,ui:document.getElementById('p-halfW').value,w:P.wireGauge,name:document.getElementById('dname').value,back:PAINT.back})")
        check(r['L'] == 84 and r['halfW'] == 8 and r['ui'] == '16' and r['w'] == '1.0' and r['back'] == '#112233', f'v1 import migrates and fills the UI {r}')

        await header_one_row(pg, 1440)
        print('errors 1440:', errs)
        await pg.close()

        # ---------- 1280 × 800
        pg = await new_page(b, 1280, 800, errs)
        await header_one_row(pg, 1280)
        vb = await pg.evaluate(f"({RECT})('.viewbar')")
        check(vb['b'] - vb['t'] < 34, 'viewport toolbar is one row at 1280')
        await pg.screenshot(path=SHOT('design_1280'))
        for m in ['simulate', 'release']:
            await mode(pg, m, 1200); await header_one_row(pg, 1280)
        await pg.screenshot(path=SHOT('release_1280'))
        await mode(pg, 'simulate', 800); await pg.click('#swimBtn'); await pg.wait_for_timeout(2500)
        tr = await pg.evaluate(f"({RECT})('.transport')"); lb = await pg.evaluate(LURE_BOX)
        check(overlap(lb, tr) == 0, 'transport bar clear of the lure at 1280')
        await pg.screenshot(path=SHOT('simulate_swim_1280'))
        await pg.close()

        # ---------- narrow 390 × 844
        pg = await new_page(b, 390, 844, errs)
        r = await pg.evaluate("""(()=>{ const v=document.getElementById('view').getBoundingClientRect(), t=document.querySelector('.ntabs').getBoundingClientRect();
          return {vh:v.height, ih:innerHeight, tabs:getComputedStyle(document.querySelector('.ntabs')).display, sw:document.documentElement.scrollWidth}; })()""")
        check(abs(r['vh'] - 0.4 * r['ih']) < 3 and r['tabs'] == 'flex' and r['sw'] <= 390, f'390px: viewport 40vh ({r["vh"]:.0f}px), tab bar shown, no horizontal scroll ({r["sw"]})')
        await pg.screenshot(path=SHOT('design_390'))
        await pg.mouse.wheel(0, 500); await pg.wait_for_timeout(400)
        top = await pg.evaluate("document.getElementById('view').getBoundingClientRect().top")
        check(abs(top) < 2, f'viewport stays sticky while the parameters scroll (top {top:.0f})')
        await pg.screenshot(path=SHOT('design_390_scrolled'))
        await pg.evaluate("scrollTo(0,0)")
        await pg.click('.ntabs [data-ntab=results]'); await pg.wait_for_timeout(300)
        check(not await pg.is_visible('#left') and await pg.is_visible('#kMass') and await pg.is_visible('#side') and not await pg.is_visible('#checksSec'), 'Results tab: KPIs + side profile, no params / checks')
        await pg.screenshot(path=SHOT('results_390'))
        await pg.click('.ntabs [data-ntab=checks]'); await pg.wait_for_timeout(300)
        check(await pg.is_visible('#checksSec') and not await pg.is_visible('#kMass') and not await pg.is_visible('#left'), 'Checks tab: checks only')
        await pg.click('.ntabs [data-ntab=params]'); await pg.wait_for_timeout(200)
        await mode(pg, 'simulate', 800); await pg.screenshot(path=SHOT('simulate_390'))
        tr = await pg.evaluate(f"({RECT})('.transport')")
        check(tr and tr['r'] <= 390 and tr['l'] >= 0, f'390px: transport bar fits ({tr})')
        await mode(pg, 'release', 1500); await pg.screenshot(path=SHOT('release_390'))
        check(await pg.is_visible('#relSku') and await pg.is_visible('#mStatus'), '390px: Release shows the form and the document')
        sw = await pg.evaluate('document.documentElement.scrollWidth'); check(sw <= 392, f'390px Release: no page-level horizontal scroll ({sw})')
        await pg.close()

        # ---------- deep link
        pg = await new_page(b, 1440, 880, errs, hash_='#analyse')
        check(await pg.evaluate("document.body.dataset.mode") == 'analyse', 'hash #analyse opens Analyse mode')
        await pg.close()

        check(not errs, 'no page errors' + ('' if not errs else ': ' + ' | '.join(errs[:5])))
        await b.close()
    print('\n' + ('ALL PASS' if not check.fails else f'{len(check.fails)} FAIL(S): ' + '; '.join(check.fails)))
    sys.exit(1 if check.fails else 0)

asyncio.run(main())
