"""v6 Stage A UI suite (Playwright, 1440x880): every family preset loads with 0 page errors and finite figures in every mode,
family / species selects, custom profile editor by mouse (drag, double-click add, select + Delete, undo / redo >= 30 steps,
snap 0.5 mm, table edit, tracing underlay, blank ellipsoid), components palette add / remove, Convert to editable,
v5 JSON (exported by team/index_v5.html) loads as crank with identical figures, custom JSON round trip (spec hash).
Screenshots: tests/v6A_<family>.png (Design mode, 1440x880).
Run: python3 -I v6A_ui.py   (exit 1 on failure)"""
import asyncio, json, math, os, sys, base64, struct, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.async_api import async_playwright
from stageB_common import new_page, LAUNCH, mode, preset, Checker, HERE, MAP, STUB

check = Checker()
V5 = 'file:///home/claude/team/index_v5.html'


def tiny_png(w=64, h=24):
    raw = b''.join(b'\x00' + b''.join(bytes([(x * 4) % 256, 90, 160, 255]) for x in range(w)) for _ in range(h))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


FIG = "(()=>({M:cache.A.M,net:cache.A.net,CG:cache.A.CG,CB:cache.A.CB,Vd:cache.A.Vd,depth:cache.A.depth,fam:P.family,vP:cache.A.vPause,sim:cache.sim.maxZ}))()"


async def drag_point(pg, svg, curve, i, dx, dy):
    box = await pg.evaluate(f"(()=>{{ const c=document.querySelector('#{svg} circle.pt[data-c={curve}][data-i=\"{i}\"]'); const r=c.getBoundingClientRect(); return [r.x+r.width/2,r.y+r.height/2]; }})()")
    await pg.mouse.move(box[0], box[1]); await pg.mouse.down()
    for k in range(1, 6): await pg.mouse.move(box[0] + dx * k / 5, box[1] + dy * k / 5); await pg.wait_for_timeout(40)
    await pg.mouse.up(); await pg.wait_for_timeout(500)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=LAUNCH); errs = []
        pg = await new_page(b, 1440, 880, errs)
        check(not errs, f'page loads with 0 errors {errs[:2]}')
        fams = await pg.evaluate("Object.keys(FAMILIES)")
        presets = await pg.evaluate("Object.fromEntries(Object.entries(PRESETS).map(([k,v])=>[k,v.p.family||'crank']))")
        check(set(presets.values()) == set(fams), f'every family has a preset ({sorted(set(presets.values()))})')
        # ---------- 1. every preset, every mode: no page errors, finite figures, family-relevant KPIs
        shot = {}
        for k, fam in presets.items():
            n0 = len(errs)
            await preset(pg, k, 1300)
            f = await pg.evaluate(FIG)
            fin = all(isinstance(v, (int, float)) and math.isfinite(v) for v in [f['M'], f['net'], f['Vd'], f['depth'], f['vP'], f['sim']] + f['CG'] + f['CB'])
            strip = await pg.inner_text('#specstrip')
            ui = await pg.evaluate("({fam:document.getElementById('famSel').value, kp:document.querySelectorAll('#famKpis .kpi').length, grp:[...document.querySelectorAll('#controls .grp .acc')].map(a=>a.firstChild.textContent), nan:/NaN|undefined|Infinity/.test(document.getElementById('stats').innerText+document.getElementById('specstrip').innerText)})")
            check(fin and f['fam'] == fam and ui['fam'] == fam and not ui['nan'], f'{k}: loads as {fam}, finite figures, no NaN in the panels (M {f["M"]:.2f} g, net {f["net"]:+.2f} g)')
            if fam != 'crank': check(ui['kp'] >= 1 and 'Dive ' not in strip, f'{k}: family KPIs shown ({ui["kp"]}) and the strip shows "{[l for l in strip.split(chr(10)) if "est." in l]}"')
            else: check(ui['grp'] == ['Shape', 'Bill', 'Hardware', 'Ballast', 'Material & mold', 'Finish'], f'{k}: crank keeps the v5 accordion {ui["grp"]}')
            if fam not in shot:
                shot[fam] = k
                await pg.evaluate("document.querySelectorAll('#toast').forEach(t=>t.classList.remove('show'))"); await pg.wait_for_timeout(300)
                await pg.screenshot(path=os.path.join(HERE, f'v6A_{fam}.png'))
            for m in ['analyse', 'simulate', 'release']:
                await mode(pg, m, 900 if m != 'release' else 1500)
                if m == 'simulate':
                    await pg.click('#swimBtn'); await pg.wait_for_timeout(900); await pg.click('#swimBtn'); await pg.wait_for_timeout(200)
                    sty = await pg.evaluate("[...document.querySelectorAll('#p-style option')].map(o=>o.value)")
                    allowed = await pg.evaluate("FAM(P).retrieve")
                    check(sty == allowed, f'{k}: retrieve styles offered = family list {sty}')
                if m == 'release':
                    rel = await pg.evaluate("(()=>{ const r=relModel(); return {sku:r.sku, bom:r.bom.length, M:r.A.M, nan:/NaN/.test(document.getElementById('relRoot').innerText)}; })()")
                    check(rel['bom'] > 3 and math.isfinite(rel['M']) and not rel['nan'], f'{k}: Release renders (BOM {rel["bom"]} lines, {rel["M"]:.2f} g, SKU {rel["sku"]})')
            await mode(pg, 'design', 600)
            check(len(errs) == n0, f'{k}: no page errors in Design / Analyse / Simulate (swim) / Release {errs[n0:n0+2]}')
        # ---------- 2. family + species selects
        await pg.select_option('#famSel', 'pencil'); await pg.wait_for_timeout(1500)
        check(await pg.evaluate("P.family==='pencil'&&cache.p.family==='pencil'"), 'family select loads the pencil preset')
        await pg.select_option('#spSel', 'peacock'); await pg.wait_for_timeout(900)
        check(await pg.evaluate("P.species==='peacock'") and 'peacock' in (await pg.inner_text('#kOddsL')).lower(), 'species select sets P.species and the strike model label')
        # ---------- 3. custom profile editor by mouse
        await pg.select_option('#famSel', 'custom'); await pg.wait_for_timeout(1500)
        check(await pg.is_visible('#edSide') and await pg.is_visible('#edTop') and not await pg.is_visible('#side'), 'custom: profile editor replaces the side profile in Design')
        s0 = await pg.evaluate("({top:P.shape.top.length,v:P.shape.top[4][1],M:cache.A.M,Vd:cache.A.Vd})")
        await drag_point(pg, 'edSide', 'top', 4, 0, -30)
        s1 = await pg.evaluate("({top:P.shape.top.length,v:P.shape.top[4][1],M:cache.A.M,Vd:cache.A.Vd,snap:P.shape.top.every(q=>Math.abs(q[1]*2-Math.round(q[1]*2))<1e-9),cm:cache.p.shape.top[4][1]})")
        check(s1['v'] > s0['v'] + 2 and s1['cm'] == s1['v'] and s1['Vd'] > s0['Vd'] and s1['M'] != s0['M'], f'drag a top point up: value {s0["v"]}→{s1["v"]} mm, displacement {s0["Vd"]/1000:.2f}→{s1["Vd"]/1000:.2f} cm³, mass {s0["M"]:.2f}→{s1["M"]:.2f} g')
        check(s1['snap'], 'dragged values snap to 0.5 mm')
        await drag_point(pg, 'edTop', 'hw', 4, 0, -20)
        s2 = await pg.evaluate("({hw:P.shape.hw[4][1],Vd:cache.A.Vd})")
        check(s2['Vd'] > s1['Vd'], f'drag the half-width point out: displacement {s1["Vd"]/1000:.2f}→{s2["Vd"]/1000:.2f} cm³')
        # double-click on the top curve between points 2 and 3 adds a point
        xy = await pg.evaluate("""(()=>{ const sv=document.getElementById('edSide'), a=P.shape.top[2], b=P.shape.top[3], x=(a[0]+b[0])/2, z=radii(x/P.L,P)[0];
            const pt=sv.createSVGPoint(); pt.x=x; pt.y=-z; const q=pt.matrixTransform(sv.getScreenCTM()); return [q.x,q.y]; })()""")
        await pg.mouse.dblclick(xy[0], xy[1]); await pg.wait_for_timeout(600)
        s3 = await pg.evaluate("({top:P.shape.top.length,sel:ED.sel,M:cache.A.M})")
        check(s3['top'] == s1['top'] + 1 and s3['sel'] and s3['sel']['c'] == 'top', f'double-click on the top curve adds a point ({s1["top"]}→{s3["top"]})')
        # select a point by clicking, Delete key removes it
        c = await pg.evaluate("(()=>{ const r=document.querySelector('#edSide circle.pt[data-c=top][data-i=\"3\"]').getBoundingClientRect(); return [r.x+r.width/2,r.y+r.height/2]; })()")
        await pg.mouse.click(c[0], c[1]); await pg.wait_for_timeout(200); await pg.keyboard.press('Delete'); await pg.wait_for_timeout(600)
        s4 = await pg.evaluate("({top:P.shape.top.length,M:cache.A.M})")
        check(s4['top'] == s3['top'] - 1 and abs(s4['M'] - s3['M']) > 1e-6, f'select + Delete removes the point ({s3["top"]}→{s4["top"]}) and the mass follows ({s3["M"]:.3f}→{s4["M"]:.3f} g)')
        # undo / redo
        await pg.click('#edUndo'); await pg.wait_for_timeout(500)
        check(await pg.evaluate("P.shape.top.length") == s3['top'], 'Undo restores the deleted point')
        await pg.click('#edUndo'); await pg.wait_for_timeout(500); await pg.click('#edUndo'); await pg.wait_for_timeout(500)
        u = await pg.evaluate("({n:P.shape.top.length,hw:P.shape.hw[4][1]})")
        await pg.click('#edUndo'); await pg.wait_for_timeout(500)
        u2 = await pg.evaluate("({v:P.shape.top[4][1],M:cache.A.M})")
        check(u['n'] == s1['top'] and abs(u2['v'] - s0['v']) < 1e-9 and abs(u2['M'] - s0['M']) < 1e-9, f'Undo ×4 walks back to the original body (top[4] {u2["v"]}, mass {u2["M"]:.3f} g)')
        await pg.click('#edRedo'); await pg.wait_for_timeout(500)
        check(abs(await pg.evaluate("P.shape.top[4][1]") - s1['v']) < 1e-9, 'Redo re-applies the drag')
        await pg.focus('#pEdit'); await pg.keyboard.press('Control+z'); await pg.wait_for_timeout(400)
        check(abs(await pg.evaluate("P.shape.top[4][1]") - s0['v']) < 1e-9, 'Ctrl+Z undoes in the editor')
        # >= 30 undo steps through the numeric table
        await pg.select_option('#edCurve', 'bot'); await pg.wait_for_timeout(200)
        b0 = await pg.evaluate("JSON.stringify(P.shape)"); u0 = await pg.evaluate("ED.undo.length")
        for i in range(32):
            await pg.fill('#edTable input[data-ti="4"][data-tk="1"]', str(6 + i * 0.5)); await pg.press('#edTable input[data-ti="4"][data-tk="1"]', 'Tab'); await pg.wait_for_timeout(160)
        n_undo = await pg.evaluate("ED.undo.length") - u0
        for i in range(n_undo): await pg.evaluate("edUndo()")
        await pg.wait_for_timeout(500)
        check(n_undo >= 32 and await pg.evaluate("JSON.stringify(P.shape)") == b0, f'numeric table: 32 edits = {n_undo} undo steps; undoing all restores the body exactly')
        # tracing image underlay
        png = '/tmp/v6A_trace.png'; open(png, 'wb').write(tiny_png())
        await pg.set_input_files('#edImg', png); await pg.wait_for_timeout(700)
        await pg.fill('#edOp', '0.6'); await pg.dispatch_event('#edOp', 'input'); await pg.wait_for_timeout(200)
        im = await pg.evaluate("(()=>{ const i=document.querySelector('#edSide image'); return i?{op:i.getAttribute('opacity'),w:+i.getAttribute('width')}:null; })()")
        check(im and im['op'] == '0.6' and im['w'] > 10, f'tracing image shows under the side view with opacity / scale ({im})')
        # components palette: add a rear prop and a spinner blade, remove one
        await pg.click('#g-components-h'); await pg.wait_for_timeout(200)
        M0 = await pg.evaluate("cache.A.M"); nC = await pg.evaluate("P.comps.length")
        await pg.select_option('#addCompSel', 'prop'); await pg.click('#addCompBtn'); await pg.wait_for_timeout(900)
        await pg.select_option('#addCompSel', 'blade'); await pg.click('#addCompBtn'); await pg.wait_for_timeout(900)
        a = await pg.evaluate("({n:P.comps.length,t:P.comps.map(c=>c.type),M:cache.A.M,parts:cache.A.parts.map(q=>q.n)})")
        check(a['n'] == nC + 2 and 'prop' in a['t'] and 'blade' in a['t'] and a['M'] > M0 + 0.2, f'components: add a prop and a blade → {a["t"]}, mass {M0:.2f}→{a["M"]:.2f} g')
        await pg.fill(f'#cmp-{a["n"]-2}-dia', '24'); await pg.press(f'#cmp-{a["n"]-2}-dia', 'Tab'); await pg.wait_for_timeout(800)
        check(await pg.evaluate(f"P.comps[{a['n']-2}].dia") == 24, 'component field edit (prop Ø 24 mm)')
        await pg.click(f'[data-del="{a["n"]-1}"]'); await pg.wait_for_timeout(900)
        check(await pg.evaluate("P.comps.length") == nC + 1 and 'blade' not in await pg.evaluate("P.comps.map(c=>c.type)"), 'components: remove (×) the blade')
        await pg.select_option('#addCompSel', 'bill'); await pg.click('#addCompBtn'); await pg.wait_for_timeout(1000)
        bl = await pg.evaluate("({bill:hasBill(P),grp:[...document.querySelectorAll('#controls .grp .acc')].map(a=>a.firstChild.textContent),tip:cache.A.tip,d:cache.A.depth})")
        check(bl['bill'] and 'Bill' in bl['grp'] and bl['tip'] > 5 and bl['d'] > 0.3, f'components: adding a bill shows the Bill group and the dive estimate ({bl["d"]:.1f} m)')
        hk = await pg.evaluate("P.comps.filter(c=>c.type==='hook').length")
        for i in range(4 - hk): await pg.select_option('#addCompSel', 'hook'); await pg.click('#addCompBtn'); await pg.wait_for_timeout(600)
        check(await pg.evaluate("P.comps.filter(c=>c.type==='hook').length") == 4 and await pg.evaluate("document.querySelector('#addCompSel option[value=hook]').disabled"), 'hook hangers are limited to 4')
        # blank ellipsoid
        await pg.fill('#blL', '70'); await pg.fill('#blH', '20'); await pg.fill('#blW', '16'); await pg.click('#blankBtn'); await pg.wait_for_timeout(900)
        bk = await pg.evaluate("({L:P.L,top:Math.max(...P.shape.top.map(q=>q[1])),hw:Math.max(...P.shape.hw.map(q=>q[1])),x:P.shape.top[P.shape.top.length-1][0]})")
        check(bk['L'] == 70 and bk['top'] == 10 and bk['hw'] == 8 and bk['x'] == 70, f'blank ellipsoid 70 × 20 × 16 ({bk})')
        await pg.click('#edUndo'); await pg.wait_for_timeout(600)
        check(await pg.evaluate("P.L") != 70 or await pg.evaluate("Math.max(...P.shape.top.map(q=>q[1]))") != 10, 'blank can be undone')
        # body length slider rescales the splines
        await pg.click('#g-shape-h'); await pg.wait_for_timeout(200)
        await pg.fill('#p-L', '100'); await pg.press('#p-L', 'Tab'); await pg.wait_for_timeout(900)
        check(await pg.evaluate("P.shape.top[P.shape.top.length-1][0]===100&&P.shape.hw[P.shape.hw.length-1][0]===100"), 'changing L rescales the custom curves')
        # custom JSON round trip (spec incl. shape + comps, same SHA-256)
        j = await pg.evaluate("designJSON()"); d = json.loads(j)
        check('shape' in d['spec'] and 'comps' in d['spec'], 'design file v2 carries spec.shape and spec.comps for custom')
        h0 = await pg.evaluate("specHash(stateNow())")
        await preset(pg, 'toman90', 1200)
        await pg.evaluate(f"loadDesign({j},'rt','imported')"); await pg.wait_for_timeout(1300)
        h1 = await pg.evaluate("specHash(stateNow())")
        check(h0 == h1 and await pg.evaluate("P.family") == 'custom', f'custom design re-imports with the same spec hash ({h0[:12]})')
        # ---------- 4. Convert to editable
        await preset(pg, 'popper70', 1300)
        m0 = await pg.evaluate("cache.A.M")
        await pg.click('#convBtn'); await pg.wait_for_timeout(1500)
        cv = await pg.evaluate("({f:P.family,M:cache.A.M,c:P.comps.map(c=>c.type),nose:P.noseFace,pts:P.shape.top.length})")
        check(cv['f'] == 'custom' and abs(cv['M'] / m0 - 1) < 0.06 and cv['nose'] == 'cup' and 'hook' in cv['c'], f'Convert to editable: popper → custom ({m0:.2f}→{cv["M"]:.2f} g, cup kept, parts {cv["c"]})')
        await pg.screenshot(path=os.path.join(HERE, 'v6A_custom_converted.png'))
        # ---------- 5. v5 JSON loads as crank with identical figures
        v5 = await b.new_page(viewport={'width': 1440, 'height': 880}); v5e = []
        v5.on('pageerror', lambda e: v5e.append(str(e)))
        async def route(r):
            u = r.request.url
            for k_, v_ in MAP.items():
                if u.endswith(k_): return await r.fulfill(path=v_, content_type='application/javascript')
            if 'fonts' in u: return await r.abort()
            await r.continue_()
        await v5.route('**/*', route); await v5.add_init_script(STUB); await v5.goto(V5); await v5.wait_for_timeout(2200)
        for k in ['toman90', 'minnow110']:
            await v5.evaluate(f"loadPreset('{k}')"); await v5.wait_for_timeout(900)
            j5 = await v5.evaluate("designJSON()"); f5 = await v5.evaluate(FIG.replace(',fam:P.family', ''))
            open(f'/tmp/v6A_{k}_v5.json', 'w').write(j5)
            await pg.set_input_files('#importFile', f'/tmp/v6A_{k}_v5.json'); await pg.wait_for_timeout(1500)
            f6 = await pg.evaluate(FIG)
            same = all(abs(f5[q] - f6[q]) < 1e-12 for q in ['M', 'net', 'Vd', 'depth', 'vP', 'sim']) and all(abs(a_ - b_) < 1e-12 for a_, b_ in zip(f5['CG'] + f5['CB'], f6['CG'] + f6['CB']))
            sp = await pg.evaluate("specObject(stateNow())"); sp5 = json.loads(j5)['spec']
            keys_same = all(sp.get(q) == sp5[q] for q in sp5 if q not in ('production', 'paint', 'colourway', 'bom', 'packaging')) and sp['production'] == sp5['production']
            added = sorted(set(sp) - set(sp5))
            check(f6['fam'] == 'crank' and same and keys_same, f'v5 JSON {k}: loads as crank, figures identical (M {f5["M"]:.4f} = {f6["M"]:.4f} g), every v5 spec value unchanged; added fields: {len(added)}')
        await v5.close()
        check(not v5e, f'v5 page clean {v5e[:1]}')
        check(not errs, f'no page errors in the whole run {errs[:3]}')
        await b.close()
    print('ALL PASS' if not check.fails else f'FAILED: {len(check.fails)}'); sys.exit(1 if check.fails else 0)

asyncio.run(main())
