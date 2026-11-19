"""Stage C acceptance fixes (accept_ceo.md + accept_ux.md): drawing legibility + label overlaps, release gate, watermark,
EAN-13, packaging.csv, costing maths, eyes / ballast on the drawing, PDF glyphs, camera refit, narrow layout, issue chip,
Release BOM / dive chart / units at 1280. Renders the Golden PDF pages to /home/claude/team/accept/tp-golden-{1..4}.png.
Run: python3 -I stageC_accept.py   (exit 1 on failure)"""
import asyncio, base64, csv, hashlib, io, json, os, subprocess, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.async_api import async_playwright
from stageB_common import new_page, LAUNCH, PULL, mode, preset, Checker, HERE

OUT = '/tmp/stageC'; os.makedirs(OUT, exist_ok=True)
TEAM = '/home/claude/team/accept'; os.makedirs(TEAM, exist_ok=True)
check = Checker()


def ean13_py(base12):
    s = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(base12))
    return base12 + str((10 - s % 10) % 10)


def canon_hash(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


async def pull(pg):
    files = await pg.evaluate(PULL); res = {}
    for k, v in files.items():
        res[k] = v['d'].encode() if v['t'] == 'text' else base64.b64decode(v['d'])
        open(os.path.join(OUT, k), 'wb').write(res[k])
    return res

PROJ = """(()=>{ const b=lureBox(), r=renderer.domElement.getBoundingClientRect(); camera.updateMatrixWorld(); const xs=[],ys=[];
  for(const x of [b.min.x,b.max.x]) for(const y of [b.min.y,b.max.y]) for(const z of [b.min.z,b.max.z]){ const v=new THREE.Vector3(x,y,z).project(camera); xs.push((v.x+1)/2*r.width); ys.push((1-v.y)/2*r.height); }
  return {x0:Math.min(...xs),x1:Math.max(...xs),y0:Math.min(...ys),y1:Math.max(...ys),w:r.width,h:r.height}; })()"""


async def main():
    # ---------- 1. drawing sheets: text height and label overlaps, every preset (Node, pure model)
    for k in ['toman90', 'crank70', 'square60', 'minnow110']:
        r = subprocess.run(['node', os.path.join(HERE, 'node', 'draw_sheets.js'), k], capture_output=True, text=True, cwd=os.path.join(HERE, 'node'))
        d = json.loads(r.stdout.strip().split('\n')[-1]) if r.returncode == 0 else {'small': ['node failed ' + r.stderr[-200:]], 'overlaps': []}
        check(not d['small'], f'{k}: every drawing text has cap height >= 2.5 mm (ISO 3098) on all 4 sheets {d["small"][:3]}')
        check(not d['overlaps'], f'{k}: no overlapping labels / text outside the frame on all 4 sheets {d["overlaps"][:3]}')

    async with async_playwright() as p:
        b = await p.chromium.launch(args=LAUNCH); errs = []
        pg = await new_page(b, 1440, 900, errs)

        # ---------- 2. issue chip = design checks + DFM (single source)
        await pg.wait_for_timeout(800)
        n_chip = int(await pg.get_attribute('#sIssues', 'data-n'))
        n_list = await pg.evaluate("document.querySelectorAll('#checks > ul.checks li.e, #checks > ul.checks li.w').length")
        n_dfm = await pg.evaluate("(DFM_LAST||[]).filter(d=>d[0]==='e'||d[0]==='w').length")
        check(n_chip == n_list and n_dfm > 0 and await pg.evaluate("document.querySelectorAll('#checks li[data-src=dfm]').length") >= n_dfm,
              f'issue chip counts design + DFM issues from one list (chip {n_chip}, listed {n_list}, DFM {n_dfm})')

        # ---------- 3. camera refit at L=130 and L=40
        for L in [130, 40]:
            await pg.evaluate(f"P.L={L}; changed()"); await pg.wait_for_timeout(1500)
            r = await pg.evaluate(PROJ)
            inside = r['x0'] >= 0 and r['y0'] >= 0 and r['x1'] <= r['w'] and r['y1'] <= r['h']
            check(inside and (r['x1'] - r['x0']) > 0.3 * r['w'], f'camera: whole lure in view and not tiny at L={L} ({r})')
        await preset(pg, 'toman90', 1200)
        cam0 = await pg.evaluate("camera.position.toArray()")
        await pg.evaluate("FIT.userMoved=true; P.L=93; changed()"); await pg.wait_for_timeout(900)
        check(await pg.evaluate("camera.position.toArray()") == cam0, 'camera: a small change after a manual orbit does not move the camera')
        await pg.click('#vFit'); await pg.wait_for_timeout(900)
        check(await pg.evaluate("FIT.userMoved===false"), 'Fit view button refits')
        await preset(pg, 'toman90', 1000)

        # ---------- 4. EAN-13, packaging, costing maths
        await mode(pg, 'release', 1500)
        await pg.fill('#k_ean13', '955000000001'); await pg.press('#k_ean13', 'Tab'); await pg.wait_for_timeout(900)
        want = ean13_py('955000000001')
        check(await pg.evaluate('PKG.ean13') == want and want in await pg.inner_text('#eanOut'), f'EAN-13: 12-digit base 955000000001 → {want} (Python check digit)')
        bad = want[:12] + str((int(want[12]) + 3) % 10)
        await pg.fill('#k_ean13', bad); await pg.press('#k_ean13', 'Tab'); await pg.wait_for_timeout(900)
        check('wrong check digit' in await pg.inner_text('#eanOut') and await pg.evaluate("relModel().gate.missing.some(m=>m.startsWith('Valid EAN-13'))"), 'EAN-13: wrong check digit is flagged and blocks the gate')
        for e in ['4006381333931', '9780306406157']:
            r = await pg.evaluate(f"ean13Status('{e}').ok"); check(r is True, f'EAN-13 {e} validates')
        await pg.fill('#k_ean13', want); await pg.press('#k_ean13', 'Tab'); await pg.wait_for_timeout(700)
        cst = await pg.evaluate("(()=>{ const r=relModel(), c=r.costing; return {cost:COST, lines:c.lines, variable:c.variable, margin:c.margin, fobEx:c.fobEx, tooling:c.tooling, tiers:c.tiers, mould:c.mould}; })()")
        C = cst['cost']; mould = C['machineUSDh'] * C['cycleS'] / 3600 / C['cavities']
        check(abs(cst['mould'] - mould) < 1e-9 and any(l[1] == cst['mould'] and l[0].startswith('Moulding') for l in cst['lines']), f'costing: moulding = {C["machineUSDh"]} USD/h × {C["cycleS"]} s ÷ {C["cavities"]} = {mould:.4f} USD/unit')
        base = sum(l[1] for l in cst['lines'] if not l[0].startswith('Scrap'))
        check(abs(cst['variable'] - base * (1 + C['scrapPct'] / 100)) < 1e-9, 'costing: variable = lines + scrap (no tooling inside)')
        check(abs(cst['fobEx'] - cst['variable'] * (1 + C['marginPct'] / 100)) < 1e-9 and abs(cst['margin'] - cst['variable'] * C['marginPct'] / 100) < 1e-9, 'costing: margin applied to the unit cost only')
        check(abs(cst['tooling'] - (C['moldUSD'] + C['billToolUSD'])) < 1e-9 and all(abs(t['fobIncl'] - (cst['fobEx'] + cst['tooling'] / t['qty'])) < 1e-9 and abs(t['fobEx'] - cst['fobEx']) < 1e-12 for t in cst['tiers']),
              'costing: tooling is a separate one-off line; FOB incl. = FOB excl. + tooling ÷ qty (margin not applied to tooling)')
        await pg.fill('#c_rateDate', '2026-11-01'); await pg.press('#c_rateDate', 'Tab'); await pg.wait_for_timeout(500)

        # ---------- 5. release gate + watermark
        await pg.select_option('#mStatus', 'T1'); await pg.wait_for_timeout(900)
        msg = await pg.inner_text('#gateCard')
        check(await pg.evaluate('META.status') == 'Concept' and 'T1 was refused' in msg and 'Drawn: name' in msg and 'Pantone' in msg, 'gate: T1 refused with blank sign-off / Pantone; in-page message lists what is missing')
        await pg.select_option('#mStatus', 'Released'); await pg.wait_for_timeout(900)
        check(await pg.evaluate('META.status') == 'Concept', 'gate: Released refused too')
        await pg.select_option('#mStatus', 'T0'); await pg.wait_for_timeout(1200)
        check(await pg.evaluate('META.status') == 'T0' and await pg.evaluate("P.prodMode") == 'inject', 'T0 allowed without the gate; build mode switches to Injection at T0+')
        await pg.click('#rSvg'); await pg.click('#rHtml'); await pg.wait_for_timeout(1500)
        f = await pull(pg)
        svg = [v for k, v in f.items() if k.endswith('_drawing.svg')][0].decode(); html = [v for k, v in f.items() if k.endswith('_techpack.html')][0].decode()
        check('NOT FOR PRODUCTION – T0' in svg and 'NOT FOR PRODUCTION – T0' in html and 'class="watermark"' in svg, 'watermark "NOT FOR PRODUCTION – T0" on drawing.svg and techpack.html')
        for r in ['drawn', 'checked', 'approved']:
            await pg.fill(f'input[data-so={r}][data-f=name]', r.title() + ' Person'); await pg.press(f'input[data-so={r}][data-f=name]', 'Tab'); await pg.wait_for_timeout(250)
            await pg.fill(f'input[data-so={r}][data-f=date]', '2026-11-10'); await pg.press(f'input[data-so={r}][data-f=date]', 'Tab'); await pg.wait_for_timeout(250)
        await pg.fill('#cwPantone', 'PMS 802 C / RAL 1026'); await pg.press('#cwPantone', 'Tab'); await pg.wait_for_timeout(800)
        check(await pg.evaluate('relModel().gate.ok'), 'gate opens once sign-off, Pantone and DFM are complete')
        await pg.screenshot(path=os.path.join(OUT, 'release_gate_ok.png'), full_page=True)
        # Golden still watermarked
        await pg.select_option('#mStatus', 'Golden'); await pg.wait_for_timeout(900)
        check(await pg.evaluate('META.status') == 'Golden', 'Golden allowed when the gate is complete')
        await pg.click('#rPack'); await pg.wait_for_timeout(6000)
        f = await pull(pg); zn = [k for k in f if k.endswith('_release.zip')]
        check(len(zn) == 1, 'Golden release pack exported')
        z = zipfile.ZipFile(io.BytesIO(f[zn[0]]))
        check('packaging.csv' in z.namelist(), 'release zip contains packaging.csv')
        pk = {r[0]: r[1] for r in csv.reader(io.StringIO(z.read('packaging.csv').decode()))}
        check(pk.get('ean13') == want and 'blister_inner_LxHxD' in pk and 'carton_LxWxH' in pk and pk.get('card_copy_bm'), f'packaging.csv: EAN {pk.get("ean13")}, blister {pk.get("blister_inner_LxHxD")}, carton {pk.get("carton_LxWxH")}')
        d = json.loads(z.read('design.json'))
        check(d['spec']['packaging']['ean13'] == want and d['spec']['ballFix'] == 'pocket' and d['meta']['specSha256'] == canon_hash(d['spec']), 'design.json: packaging + ballFix in the hashed spec; hash == Python SHA-256')
        pdf = z.read('techpack.pdf'); open(os.path.join(OUT, 'golden_techpack.pdf'), 'wb').write(pdf)
        import pymupdf
        doc = pymupdf.open(stream=pdf, filetype='pdf')
        check(doc.page_count == 4, f'PDF has 4 A3 pages ({doc.page_count})')
        small, qmarks, wm = [], [], 0
        for i, page in enumerate(doc):
            for blk in page.get_text('dict')['blocks']:
                for ln in blk.get('lines', []):
                    for sp in ln['spans']:
                        t = sp['text']
                        if 'NOT FOR PRODUCTION' in t: wm += 1; continue
                        cap = sp['size'] * 25.4 / 72 * (0.571 if 'Courier' in sp['font'] else 0.716)
                        if t.strip() and cap < 2.49: small.append((i + 1, t[:30], round(sp['size'], 2)))
                        if '?' in t: qmarks.append((i + 1, t[:40]))
            page.get_pixmap(dpi=110).save(os.path.join(TEAM, f'tp-golden-{i + 1}.png'))
        check(not small, f'PDF: every text span >= 2.5 mm cap height {small[:4]}')
        check(not qmarks, f'PDF: no "?" replacement glyphs {qmarks[:4]}')
        check(wm == 4, f'PDF: Golden pack is watermarked on all 4 pages ({wm})')
        t_all = ''.join(pg_.get_text() for pg_ in doc)
        check('EYE' in t_all and 'GLUED IN POCKET' in t_all and 'PACKAGING' in t_all and 'EAN-13' in t_all and 'FOB excl.' in t_all and 'TOOLING (one-off NRE)' in t_all,
              'PDF: eyes, ballast fixing, packaging block, costing with separate tooling')
        # Released: no watermark
        await pg.select_option('#mStatus', 'Released'); await pg.wait_for_timeout(1200)
        check(await pg.evaluate('META.status') == 'Released', 'Released allowed when the gate is complete')
        await pg.click('#rSvg'); await pg.wait_for_timeout(1200)
        f = await pull(pg); svg = [v for k, v in f.items() if k.endswith('_drawing.svg')][0].decode()
        check('NOT FOR PRODUCTION' not in svg and not await pg.is_visible('#nfpBar'), 'Released drawing has no watermark')
        check(await pg.is_disabled('#k_ean13'), 'packaging fields lock on release')
        await pg.select_option('#mStatus', 'T1'); await pg.wait_for_timeout(800)

        # ---------- 6. old files still load with defaults
        r = await pg.evaluate("(()=>{ const ok=loadDesign({version:1,params:{L:80}},'old v1'); return {ok,fix:P.ballFix,pkg:PKG.cardW,ean:PKG.ean13}; })()")
        check(r['ok'] and r['fix'] == 'pocket' and r['pkg'] == 95 and r['ean'] == '', 'v1 file loads with ballFix / packaging defaults')
        r = await pg.evaluate("(()=>{ const d=designV2(stateNow(),'x'); delete d.spec.packaging; delete d.spec.ballFix; const ok=loadDesign(d,'old v2'); return {ok,fix:P.ballFix,inner:PKG.innerQty}; })()")
        check(r['ok'] and r['fix'] == 'pocket' and r['inner'] == 6, 'v2 file without packaging / ballFix loads with defaults')
        await pg.close()

        # ---------- 7. 1280: Release BOM, selects, units, dive chart labels
        pg = await new_page(b, 1280, 800, errs)
        await mode(pg, 'release', 1500)
        r = await pg.evaluate("""(()=>{ const w=document.querySelector('.bomwrap'), t=document.getElementById('bomT');
          const ta=[...t.querySelectorAll('textarea')].filter(x=>x.scrollHeight>x.clientHeight+3).map(x=>x.dataset.role+'.'+x.dataset.f);
          const c=document.createElement('canvas').getContext('2d'); const inp=[...t.querySelectorAll('input')].filter(x=>{ const cs=getComputedStyle(x); c.font=cs.font; return c.measureText(x.value).width>x.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight)+1; }).map(x=>x.dataset.role+'.'+x.dataset.f+'='+x.value);
          return {sw:t.scrollWidth, cw:w.clientWidth, ta, inp}; })()""")
        check(r['sw'] <= r['cw'] + 1 and not r['ta'] and not r['inp'], f'1280: Release BOM fits without sideways scroll, no truncated cells ({r})')
        await pg.screenshot(path=os.path.join(OUT, 'release_1280.png'), full_page=False)
        await pg.evaluate("document.getElementById('bomT').scrollIntoView()"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(HERE, 'stageC_release_bom_1280.png'))
        SELTRUNC = """ids=>ids.map(id=>{ const e=document.getElementById(id); const cs=getComputedStyle(e); const c=document.createElement('canvas').getContext('2d'); c.font=cs.font; const t=e.options[e.selectedIndex].text; return [id, Math.round(c.measureText(t).width), Math.round(e.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight)-14)]; })"""
        sel = await pg.evaluate(SELTRUNC, ['cwCx'])
        await mode(pg, 'simulate', 1200)
        sel += await pg.evaluate(SELTRUNC, ['p-clarity', 'p-style', 'p-line', 'p-gear'])
        check(all(w <= a + 1 for _, w, a in sel), f'1280: selects not truncated {sel}')
        u = await pg.evaluate("(()=>{ const e=document.querySelector('[data-k=goTurns] .u'); return [e.textContent,e.scrollWidth,e.clientWidth]; })()")
        check(u[0] == 'turns' and u[1] <= u[2], f'1280: unit "turns" not clipped {u}')
        fs = await pg.evaluate("(()=>{ const s=document.getElementById('dive'), m=s.getScreenCTM(); return Math.min(...[...s.querySelectorAll('text')].map(t=>parseFloat(t.getAttribute('font-size'))*m.a)); })()")
        check(fs >= 10, f'1280: dive chart labels render at >= 10 px ({fs:.1f})')
        await pg.screenshot(path=os.path.join(HERE, 'stageC_simulate_1280.png'))
        await mode(pg, 'analyse', 1200)
        fs2 = await pg.evaluate("(()=>{ const s=document.getElementById('side'), m=s.getScreenCTM(); return Math.min(...[...s.querySelectorAll('text')].map(t=>parseFloat(t.getAttribute('font-size'))*m.a)); })()")
        check(fs2 >= 10, f'1280: side-profile CG / CB labels render at >= 10 px ({fs2:.1f})')
        await pg.close()

        # ---------- 8. narrow: rev / unsaved, Analyse content, swim HUD
        for w, h in [(1024, 768), (390, 844)]:
            pg = await new_page(b, w, h, errs)
            check((await pg.inner_text('#barStatus')).replace('\n', '') == 'A · Concept', f'{w}: status badge shows "A · Concept"')
            await pg.evaluate("P.L=91; changed()"); await pg.wait_for_timeout(500)
            dv = await pg.evaluate("(()=>{ const e=document.getElementById('dirty'), r=e.getBoundingClientRect(); return [e.textContent.includes('●'), r.width>0&&r.height>0, e.getAttribute('aria-label')]; })()")
            check(dv[0] and dv[1] and dv[2] == 'Unsaved changes', f'{w}: unsaved dot visible with aria-label {dv}')
            await mode(pg, 'analyse', 1300)
            check(await pg.evaluate("document.body.dataset.ntab") == 'results' and await pg.is_visible('#massTable') and await pg.is_visible('#dfmList'), f'{w}: Analyse switches to Results and shows mass / DFM tables')
            await pg.screenshot(path=os.path.join(HERE, f'stageC_analyse_{w}.png'))
            await mode(pg, 'simulate', 900); await pg.click('#swimBtn'); await pg.wait_for_timeout(2200)
            hud = await pg.evaluate("(()=>{ const e=document.getElementById('swimInfo'), r=e.getBoundingClientRect(), t=document.querySelector('.transport').getBoundingClientRect(); return {vis:r.width>0&&!e.hidden&&getComputedStyle(e).display!=='none', txt:e.innerText, over:!(r.right<t.left||t.right<r.left||r.bottom<t.top||t.bottom<r.top), fs:parseFloat(getComputedStyle(e).fontSize), right:r.right, vw:innerWidth}; })()")
            check(hud['vis'] and 'm/s' in hud['txt'] and not hud['over'] and hud['fs'] >= 10 and hud['right'] <= hud['vw'], f'{w}: swim HUD visible ({hud["txt"]!r}), >= 10 px, clear of the transport bar')
            await pg.screenshot(path=os.path.join(HERE, f'stageC_swim_{w}.png'))
            await pg.click('#swimBtn'); await pg.close()
        check(not errs, 'no page errors' + ('' if not errs else ': ' + ' | '.join(errs[:4])))
        await b.close()
    print('\n' + ('ALL PASS' if not check.fails else f'{len(check.fails)} FAIL(S): ' + '; '.join(check.fails)))
    sys.exit(1 if check.fails else 0)

asyncio.run(main())
