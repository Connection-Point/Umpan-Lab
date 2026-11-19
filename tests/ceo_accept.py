"""CEO acceptance: default preset, injection mode, export Release pack zip to /home/claude/team/accept and unzip."""
import asyncio, base64, os, sys, zipfile, io, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.async_api import async_playwright
from stageB_common import new_page, LAUNCH, PULL, mode
OUT = '/home/claude/team/accept'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=LAUNCH); errs = []
        pg = await new_page(b, 1440, 900, errs)
        await pg.click('#g-materialproduction-h'); await pg.wait_for_timeout(200)
        await pg.select_option('#p-prodMode', 'inject'); await pg.wait_for_timeout(900)
        await mode(pg, 'release', 1500)
        await pg.screenshot(path=os.path.join(OUT, 'release_view.png'), full_page=True)
        await pg.click('#rPack'); await pg.wait_for_timeout(5000)
        files = await pg.evaluate(PULL)
        for k, v in files.items():
            data = v['d'].encode() if v['t'] == 'text' else base64.b64decode(v['d'])
            open(os.path.join(OUT, k), 'wb').write(data); print('saved', k, len(data))
            if k.endswith('.zip'):
                shutil.rmtree(os.path.join(OUT, 'pack'), ignore_errors=True)
                zipfile.ZipFile(io.BytesIO(data)).extractall(os.path.join(OUT, 'pack'))
                import pymupdf
                doc = pymupdf.open(os.path.join(OUT, 'pack', 'techpack.pdf'))
                for i, page in enumerate(doc): page.get_pixmap(dpi=110).save(os.path.join(OUT, f'tp-{i + 1}.png'))
                print('pdf pages rendered', doc.page_count)
        print('errors', errs); await b.close()
        sys.exit(1 if errs else 0)
asyncio.run(main())
