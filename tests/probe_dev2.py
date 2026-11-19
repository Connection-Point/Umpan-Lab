import asyncio, json
from playwright.async_api import async_playwright
exec(open('check.py').read().split('async def main')[0])
JS=r"""()=>{const c=cache,p=c.p,B=c.bill.B,o=c.bill.outline,T=p.billT/2;
 const inside=(x,y,z)=>{ if(x<=0||x>=p.L) return false; const [t,b,w]=radii(x/p.L,p); const zz=z>=0?z/t:z/b; return Math.pow(Math.abs(y/w),p.se)+Math.pow(Math.abs(zz),p.se) < 1; };
 let n=0,out=0,outSide=0; for(let i=0;i<40000;i++){const u=-TAB*Math.random(), v=(2*Math.random()-1)*o.tabHW, s=(2*Math.random()-1)*T;
  const q=B.root.clone().addScaledVector(B.d,u).addScaledVector(B.n,s); q.y=v; n++; if(!inside(q.x,q.y,q.z)){out++;}}
 // ball row
 const off=(p.ballN-1)/2*p.ballD*1.02, r=p.ballD/2; let bout=0; for(let i=0;i<p.ballN;i++){const x=p.ballX-off+i*p.ballD*1.02; for(const [dx,dy,dz] of [[r,0,0],[-r,0,0],[0,r,0],[0,-r,0],[0,0,r],[0,0,-r]]) if(!inside(x+dx,dy,p.ballZ+dz)) {bout++;break}}
 // body half-width at root and at tab end
 const w0=radii(B.root.x/p.L,p)[2], te=B.root.clone().addScaledVector(B.d,-TAB), w1=radii(te.x/p.L,p)[2];
 return {tabVolOutsidePct:Math.round(100*out/n), tabHW:o.tabHW, bodyHalfWidthAtRoot:+w0.toFixed(2), atTabEnd:+w1.toFixed(2), rootZ:p.rootZ, bellyAtRoot:-radii(B.root.x/p.L,p)[1], ballsOutside:bout+'/'+p.ballN, ballInsideFlag:c.A.ballInside}}"""
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':1440,'height':880})
        async def route(r):
            u=r.request.url
            for k,v in MAP.items():
                if u.endswith(k): return await r.fulfill(path=v, content_type='application/javascript')
            if 'fonts' in u: return await r.abort()
            await r.continue_()
        await pg.route('**/*',route)
        await pg.goto('file:///home/claude/team/index_v4.html'); await pg.wait_for_timeout(2500)
        for k in ['toman90','crank70','square60','minnow110']:
            await pg.evaluate(f"loadDesign(PRESETS.{k}.p,null,'x'); rebuild()")
            print(k, await pg.evaluate(JS))
        await pg.evaluate("P=Object.assign({},PRESETS.toman90.p,{ballN:8,ballD:8}); rebuild()")
        print('8x8 balls', await pg.evaluate(JS))
        # zip assembly test
        n=await pg.evaluate("""(async()=>{const {body,bill}=cache; const z=new JSZip(); z.file('a.stl',stlBinary(body.tris,'b')); const blob=await z.generateAsync({type:'uint8array'}); return blob.length})()""")
        print('zip bytes',n)
        # svg template check
        s=await pg.evaluate("(loadDesign(PRESETS.toman90.p,null,'x'),rebuild(),templateSVG().slice(0,200))")
        print(s)
        await b.close()
asyncio.run(main())
