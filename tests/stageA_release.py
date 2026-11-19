"""Stage A end-to-end test: production mode, release tab, every export, import validation, QC import, locking.
Run:  python3 -I stageA_release.py      (writes files + screenshots to /tmp/stageA_out, exit 1 on failure)
Libraries are routed from /tmp/libs (three, OrbitControls, JSZip, jsPDF 2.5.1 from `npm pack jspdf@2.5.1`)."""
import asyncio, base64, csv, hashlib, io, json, os, re, subprocess, sys, zipfile
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright

L = '/tmp/libs/'
MAP = {'three.min.js': L + 'three-0.128.0/package/build/three.min.js',
       'OrbitControls.js': L + 'three-0.128.0/package/examples/js/controls/OrbitControls.js',
       'jszip.min.js': L + 'jszip-3.10.1/package/dist/jszip.min.js',
       'jspdf.umd.min.js': L + 'jspdf-2.5.1/package/dist/jspdf.umd.min.js'}
OUT = '/tmp/stageA_out'; os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
STUB = """window.__saved={}; window.claude={use: async n => n==='downloads' ? {save: async ({filename,data}) => { window.__saved[filename]=data; return {status:'saved'}; }} : null};"""
PULL = """async () => { const out={}; for(const [k,v] of Object.entries(window.__saved)){
  if(typeof v==='string') out[k]={t:'text',d:v};
  else { const b = v instanceof Blob ? v : new Blob([v]); const buf=new Uint8Array(await b.arrayBuffer()); let s=''; for(let i=0;i<buf.length;i+=32768) s+=String.fromCharCode.apply(null,buf.subarray(i,i+32768)); out[k]={t:'b64',d:btoa(s)}; } }
  window.__saved={}; return out; }"""
fails = []
def check(cond, msg):
    print(('PASS ' if cond else 'FAIL ') + msg)
    if not cond: fails.append(msg)

def canon_hash(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

async def pull(pg):
    files = await pg.evaluate(PULL)
    res = {}
    for k, v in files.items():
        data = v['d'].encode() if v['t'] == 'text' else base64.b64decode(v['d'])
        open(os.path.join(OUT, k), 'wb').write(data); res[k] = data
    return res

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width': 1440, 'height': 900})
        errs = []
        pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
        pg.on('console', lambda m: m.type == 'error' and 'ERR_FAILED' not in m.text and 'boom' not in m.text and errs.append('console: ' + m.text))
        async def route(r):
            u = r.request.url
            for k, v in MAP.items():
                if u.endswith(k): return await r.fulfill(path=v, content_type='application/javascript')
            if 'fonts' in u: return await r.abort()
            await r.continue_()
        await pg.route('**/*', route)
        await pg.add_init_script(STUB)
        await pg.goto('file:///home/claude/umpan-lab/index.html'); await pg.wait_for_timeout(2500)

        # ---------- production group (screenshot) + injection mode
        await pg.evaluate("document.querySelector('details.prodgrp').open=true; document.querySelector('details.prodgrp').scrollIntoView()")
        await pg.select_option('details.prodgrp select >> nth=0', 'inject'); await pg.wait_for_timeout(900)
        mass_inj = await pg.inner_text('#kMass'); net_inj = await pg.inner_text('#stSub')
        print('inject mode:', mass_inj, net_inj, '|', await pg.inner_text('#prodNote'))
        check('ABS' in await pg.inner_text('#massTable'), 'mass table shows the ABS injection body')
        check(await pg.is_disabled('details:has(#injNote) select'), 'prototype body material disabled in injection mode')
        await pg.locator('#controls').screenshot(path=os.path.join(OUT, 'production_group.png'))
        await pg.check('#showHalves'); await pg.wait_for_timeout(1200)
        await pg.screenshot(path=os.path.join(OUT, 'halves_preview.png'))
        await pg.uncheck('#showHalves'); await pg.wait_for_timeout(400)

        # ---------- release tab
        await pg.click('.tab[data-t=pRel]'); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=os.path.join(OUT, 'release_tab.png'))
        await pg.click('#rTall'); await pg.wait_for_timeout(600)
        await pg.screenshot(path=os.path.join(OUT, 'release_tab_tall.png'))
        sku = await pg.inner_text('#relSku'); print('SKU', sku)
        check(re.match(r'^UL-TDC90(F|SP|S)-FT01$', sku) is not None, 'SKU follows UL-{family}{L}{class}-{colour}')
        hash_attr = await pg.get_attribute('#relHash', 'title')
        check(bool(re.fullmatch(r'[0-9a-f]{64}', hash_attr or '')), 'release tab shows a SHA-256')

        # ---------- QC import
        qc_csv = os.path.join(OUT, 'measured.csv')
        tpl_rows = None
        await pg.click('#rQcTpl'); await pg.wait_for_timeout(500)
        got = await pull(pg); tname = [k for k in got if k.endswith('tank_test.csv')][0]
        tpl = list(csv.reader(io.StringIO(got[tname].decode())))
        check(tpl[0] == ['sample_id','weight_g','float_rate_cms','depth_05_m','depth_10_m','tracking_mm','roll_ok','hook_pull_kg'], 'tank_test.csv template header')
        tgt = dict(zip(tpl[0], tpl[1]))
        good = ['S01', f"{float(tgt['weight_g'])+0.1:.2f}", tgt['float_rate_cms'], tgt['depth_05_m'], tgt['depth_10_m'], '20', 'Y', f"{float(tgt['hook_pull_kg'])+1:.1f}"]
        bad = ['S03', f"{float(tgt['weight_g'])+0.9:.2f}", tgt['float_rate_cms'], tgt['depth_05_m'], tgt['depth_10_m'], '80', 'N', '1']
        open(qc_csv, 'w').write(','.join(tpl[0]) + '\n' + ','.join(tpl[1]) + '\n' + ','.join(good) + '\n' + ','.join(good).replace('S01', 'S02') + '\n' + ','.join(bad) + '\n')
        await pg.set_input_files('#qcFile', qc_csv); await pg.wait_for_timeout(900)
        qc_text = await pg.inner_text('#qcT')
        rows = [r for r in qc_text.split('\n') if r.startswith('S0')]
        print('QC rows:', rows)
        check(len(rows) == 3 and 'PASS' in rows[0] and 'PASS' in rows[1] and 'FAIL' in rows[2], 'QC import: 2 pass, 1 fail (TARGET row skipped)')
        await pg.locator('#pRel').screenshot(path=os.path.join(OUT, 'release_qc.png'))

        # ---------- BOM override edit
        await pg.fill('#bomT input[data-role=hookB][data-f=supplier]', 'Test Hook Co.'); await pg.press('#bomT input[data-role=hookB][data-f=supplier]', 'Enter'); await pg.wait_for_timeout(700)
        check(await pg.get_attribute('#bomT input[data-role=hookB][data-f=supplier]', 'class') == 'ovr', 'BOM override is kept and highlighted')

        # ---------- exports
        for bid in ['#rPack', '#rPdf', '#rHtml', '#rSvg', '#rBom']:
            await pg.click(bid); await pg.wait_for_timeout(3500 if bid == '#rPack' else 1500)
        files = await pull(pg); print('downloads:', sorted(files))
        zname = [k for k in files if k.endswith('_release.zip')]
        check(len(zname) == 1, 'release pack zip downloaded')
        z = zipfile.ZipFile(io.BytesIO(files[zname[0]]))
        names = set(z.namelist()); print('zip:', sorted(names))
        need = {'body_L.stl','body_R.stl','body_shell.stl','bill.stl','assembly_preview.stl','sections.csv','drawing.svg','techpack.html','techpack.pdf','bom.csv','qc_criteria.md','tank_test.csv','costing.csv','design.json','README.txt'}
        check(need <= names, 'zip has every A9 file' + ('' if need <= names else f' (missing {need - names})'))
        check('qc_results.csv' in names and 'preview.png' in names, 'zip has qc_results.csv and preview.png')
        zdir = os.path.join(OUT, 'zip'); os.makedirs(zdir, exist_ok=True); z.extractall(zdir)
        r = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'stageA_meshcheck.py')] + [os.path.join(zdir, n) for n in ['body_L.stl', 'body_R.stl', 'body_shell.stl', 'bill.stl']], capture_output=True, text=True)
        print(r.stdout.strip())
        lines = r.stdout.strip().split('\n')
        halves_ok = len(lines) == 4 and all('watertight=True' in l and 'edges!=2:0' in l and 'degenerate:0' in l for l in lines)
        check(halves_ok, 'body_L / body_R / body_shell / bill watertight in trimesh (every edge shared by exactly 2 triangles, no degenerate faces)')
        check(all('bodies=1' in l for l in lines if 'body_L' in l or 'body_R' in l), 'each half is a single connected body')
        # PDF
        pdf = z.read('techpack.pdf'); check(pdf[:5] == b'%PDF-', 'techpack.pdf starts with %PDF')
        from pypdf import PdfReader
        rd = PdfReader(io.BytesIO(pdf)); check(len(rd.pages) == 2, f'techpack.pdf has 2 pages ({len(rd.pages)})')
        mb = rd.pages[0].mediabox; w_mm, h_mm = float(mb.width) / 72 * 25.4, float(mb.height) / 72 * 25.4
        check(abs(w_mm - 420) < 1 and abs(h_mm - 297) < 1, f'PDF page is A3 landscape ({w_mm:.0f}×{h_mm:.0f} mm)')
        t1, t2 = rd.pages[0].extract_text(), rd.pages[1].extract_text()
        check('ISO 2768-m' in t1 and 'SIDE VIEW' in t1 and 'TDC90' in t1, 'PDF page 1 has the drawing text (title block, views)')
        check('BILL OF MATERIALS' in t2 and 'QC ACCEPTANCE' in t2 and 'COSTING' in t2, 'PDF page 2 has BOM, QC and costing')
        check(rd.pages[0].images == [] or len(rd.pages[0].images) == 0, 'PDF page 1 is vector (no raster images)')
        pdf_single = [k for k in files if k.endswith('_techpack.pdf')]
        check(len(pdf_single) == 1 and files[pdf_single[0]][:5] == b'%PDF-', 'standalone techpack.pdf download')
        # SVG
        svg = z.read('drawing.svg').decode(); root = ET.fromstring(svg)
        check(root.get('width') == '420mm' and root.get('height') == '297mm' and root.get('viewBox') == '0 0 420 297', 'drawing.svg is A3 in mm')
        fams = set(re.findall(r'font-family="([^"]+)"', svg)); check(all(',' in f for f in fams), f'every SVG font-family has fallbacks {fams}')
        # hash consistency
        design = json.loads(z.read('design.json')); h = canon_hash(design['spec'])
        check(design['version'] == 2 and {'spec', 'sim', 'meta'} <= set(design), 'design.json is v2 with spec / sim / meta')
        check(design['meta']['specSha256'] == h, 'design.json meta hash == SHA-256 of canonical spec (python)')
        check(h in svg and h in z.read('README.txt').decode() and h in z.read('techpack.html').decode(), 'same hash printed on drawing.svg, README, techpack.html')
        hash_now = await pg.get_attribute('#relHash', 'title')
        check(h == hash_now and h != hash_attr, 'hash shown in the release tab matches the export (and changed after the BOM edit)')
        check(h.encode() in pdf or h in t1.replace('\n', ''), 'hash printed in the PDF')
        check('castDist' in design['sim'] and 'castDist' not in design['spec'] and 'L' in design['spec'] and 'wallMm' in design['spec']['production'], 'spec / sim split')
        check(design['spec']['bom']['overrides'].get('hookB', {}).get('supplier') == 'Test Hook Co.', 'BOM override saved in spec.bom.overrides')
        # CSVs
        for n in ['bom.csv', 'costing.csv', 'sections.csv', 'tank_test.csv', 'qc_results.csv']:
            rows = list(csv.reader(io.StringIO(z.read(n).decode())))
            check(len(rows) > 2 and len(set(len(r) for r in rows)) == 1, f'{n} parses ({len(rows)} rows × {len(rows[0])} cols)')
        sec = list(csv.DictReader(io.StringIO(z.read('sections.csv').decode())))
        check(len(set(r['station'] for r in sec)) == 25, 'sections.csv has 25 stations')
        bom = list(csv.DictReader(io.StringIO(z.read('bom.csv').decode())))
        bm = sum(float(r['mass_g']) * float(r['qty']) for r in bom if r['inLure'] == 'yes')
        print(f'BOM mass {bm:.3f} g; design weight {design["results"]["weight_g"]} g')
        check(abs(bm - design['results']['weight_g']) < 0.05, 'BOM in-lure mass equals the model weight')
        check(any(r['partNo'].startswith('WIR-SS304-') for r in bom), 'BOM has the gauge wire line')
        sv = (z.read('README.txt').decode())
        open(os.path.join(OUT, 'README_from_zip.txt'), 'w').write(sv)

        # ---------- import validation (B9) + v1 migration + rollback
        v1 = {'app': 'Umpan Lab', 'version': 1, 'name': 'old', 'params': {'L': '92', 'hookStr': 'x5', 'bodyMat': 'oak', 'hookB': 2, 'wire': 1.3, 'top': 'abc', 'ballN': 3.6, 'se': 99}, 'paint': {'back': 'javascript:x', 'side': '#123456'}}
        fn = os.path.join(OUT, 'v1_bad.json'); json.dump(v1, open(fn, 'w'))
        await pg.set_input_files('#importFile', fn); await pg.wait_for_timeout(1200)
        st = await pg.evaluate("({L:P.L,hookStr:P.hookStr,bodyMat:P.bodyMat,hookB:P.hookB,wireGauge:P.wireGauge,top:P.top,ballN:P.ballN,se:P.se,back:PAINT.back,side:PAINT.side,warn:window.__lastImportWarnings,log:META.changelog.map(e=>e.changes.join(';'))})")
        print('v1 import ->', st)
        check(st['L'] == 92 and st['hookStr'] in ('std', 'x2', 'x3', 'x4') and st['bodyMat'] != 'oak' and st['hookB'] == '2' and st['wireGauge'] == '1.2' and st['ballN'] == 4 and st['se'] == 3.5 and st['back'].startswith('#') and st['side'] == '#123456',
              'v1 file validated (numbers coerced/clamped, enums defaulted, wire g → gauge)')
        vb = await pg.evaluate("document.getElementById('side').getAttribute('viewBox')")
        check(all(abs(float(v)) < 1000 for v in vb.split()), f'side view viewBox sane after import ({vb})')
        before = await pg.evaluate('JSON.stringify(P)')
        fn2 = os.path.join(OUT, 'garbage.json'); open(fn2, 'w').write('{"hello": 1}')
        await pg.set_input_files('#importFile', fn2); await pg.wait_for_timeout(600)
        check(await pg.evaluate('JSON.stringify(P)') == before, 'non-design JSON is rejected and the state is unchanged')
        # rollback when the build throws
        r = await pg.evaluate("""(()=>{ const prev=JSON.stringify(P); const orig=window.buildBill; let n=0; window.buildBill=function(p){ if(n++===0) throw new Error('boom'); return orig(p); };
            const ok=loadDesign({version:2,spec:{L:120},sim:{}},'boom'); window.buildBill=orig; return {ok, same: JSON.stringify(P)===prev}; })()""")
        check(r['ok'] is False and r['same'], 'load rolls back when the rebuild throws')
        # legacy localStorage entry
        await pg.evaluate("""localStorage.setItem('umpanlab.designs.v1', JSON.stringify({'legacy one':{params:Object.assign({},PRESETS.crank70.p,{wire:0.7}),paint:PATTERNS.chartreuse}})); refreshMine();""")
        await pg.select_option('#mine', 'legacy one'); await pg.wait_for_timeout(900)
        check(await pg.evaluate('P.L') == 70 and await pg.evaluate('P.wireGauge') == '0.8', 'legacy localStorage design loads (wire 0.7 g → Ø0.8)')

        # ---------- changelog auto-diff on save + status lock + reopen
        await pg.fill('#dname', 'Stage A test'); await pg.evaluate("P.L=72; changed()"); await pg.wait_for_timeout(500)
        await pg.click('#saveBtn'); await pg.wait_for_timeout(500)
        log = await pg.evaluate('META.changelog[META.changelog.length-1]')
        check(log and any(c.startswith('L: 70 → 72') for c in log['changes']), f'save logs the spec diff ({log and log["changes"][:2]})')
        await pg.select_option('#mStatus', 'Released'); await pg.wait_for_timeout(600)
        check(await pg.is_disabled('#controls details:first-of-type input[type=range]'), 'Released locks the spec inputs')
        check(not await pg.is_disabled('#simctl input[type=range]'), 'simulation inputs stay editable when released')
        await pg.click('.tab[data-t=pRel]'); await pg.wait_for_timeout(1200)
        check(await pg.is_disabled('#bomT input >> nth=0'), 'BOM editor locked when released')
        await pg.locator('#pRel').screenshot(path=os.path.join(OUT, 'release_locked.png'))
        await pg.select_option('#mStatus', 'T1'); await pg.wait_for_timeout(500)
        check(await pg.evaluate('META.rev') == 'B' and not await pg.is_disabled('#controls details:first-of-type input[type=range]'), 'reopening a released design bumps the rev and unlocks')
        # saved v2 entry reloads
        await pg.select_option('#mine', 'Stage A test'); await pg.wait_for_timeout(900)
        check(await pg.evaluate('P.L') == 72 and await pg.evaluate("META.changelog.length") >= 1, 'saved v2 design reloads with its changelog')

        # ---------- bug regressions (review_dev B5, B6, B8, B11) + legacy exports
        check(await pg.evaluate('W===null && FISH===null'), 'B11: underwater world and fish are not built at start-up')
        await pg.select_option('#preset', 'toman90'); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""(()=>{ P.billLen=10; P.billW=40; rebuild(); const bc=billSideCorners(cache.p,cache.bill.B,cache.bill.outline.tip);
            const B=cache.bill.B, d=(bc[1].x-B.root.x)*B.d.x+(bc[1].z-B.root.z)*B.d.z; return {tip:cache.bill.outline.tip, side:d, phys:cache.A.tip}; })()""")
        check(abs(r['tip'] - 21) < 1e-6 and abs(r['side'] - 21) < 0.01 and abs(r['phys'] - 21) < 1e-6, f'B5: short wide bill uses the real tip everywhere ({r})')
        r = await pg.evaluate("(()=>{ loadPreset('toman90'); P.ballN=8; P.ballD=8; P.ballX=24; P.ballZ=-4; rebuild(); return cache.A.ballInside; })()")
        check(r is False, 'B6: 8 × 8 mm balls that stick out at the nose are flagged')
        r = await pg.evaluate("(()=>{ loadPreset('toman90'); startSwim(true); fish.trigger=true; spawnFish(true); const t=fish.trigger; startSwim(false); return {t, built: W!==null && FISH!==null}; })()")
        check(r['t'] is False and r['built'], 'B8: spawnFish clears the reaction-strike trigger; B11: world built on first swim')
        await pg.click('#zipBtn'); await pg.wait_for_timeout(2500); await pg.click('#svgBtn'); await pg.wait_for_timeout(600)
        files = await pull(pg)
        zp = [k for k in files if k.endswith('.zip')]
        zz = zipfile.ZipFile(io.BytesIO(files[zp[0]])) if zp else None
        check(zz is not None and any(n.endswith('_bill-slot-cutter.stl') for n in zz.namelist()) and json.loads(zz.read([n for n in zz.namelist() if n.endswith('.json')][0]))['version'] == 2, 'legacy STL pack still exports (with design.json v2)')
        tsvg = [k for k in files if k.endswith('_template_1to1.svg')]
        check(len(tsvg) == 1 and ET.fromstring(files[tsvg[0]].decode()).get('width', '').endswith('mm'), '1:1 template SVG still exports')

        # ---------- presets in injection mode: no errors, figures finite
        for k in ['toman90', 'crank70', 'square60', 'minnow110']:
            await pg.select_option('#preset', k); await pg.wait_for_timeout(500)
            await pg.evaluate("P.prodMode='inject'; syncControls(); changed()"); await pg.wait_for_timeout(700)
            print(f'{k:10s} inject:', await pg.inner_text('#kMass'), await pg.inner_text('#stSub'), '| proto→', end=' ')
            await pg.evaluate("P.prodMode='proto'; syncControls(); changed()"); await pg.wait_for_timeout(500)
            print(await pg.inner_text('#kMass'), await pg.inner_text('#stSub'))
        check(not errs, 'no page errors' + ('' if not errs else ': ' + ' | '.join(errs[:5])))
        await b.close()
    print('\n' + ('ALL PASS' if not fails else f'{len(fails)} FAIL(S): ' + '; '.join(fails)))
    sys.exit(1 if fails else 0)

asyncio.run(main())
