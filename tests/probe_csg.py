import asyncio
from playwright.async_api import async_playwright
exec(open('check.py').read().split('async def main')[0])
EDGE=r"""
window.edgeCheck=(t)=>{ const key=(i)=>`${t[i].toFixed(3)},${t[i+1].toFixed(3)},${t[i+2].toFixed(3)}`; const E=new Map(); let deg=0;
   for(let k=0;k<t.length;k+=9){ const a=key(k),b=key(k+3),cc=key(k+6); if(a===b||b===cc||a===cc){deg++;continue}
     for(const [x,y] of [[a,b],[b,cc],[cc,a]]){ const kk=x<y?x+'|'+y:y+'|'+x; E.set(kk,(E.get(kk)||0)+1);} }
   let bad=0; for(const n of E.values()) if(n!==2) bad++; return {tris:t.length/9,nonManifoldEdges:bad,degenerate:deg}; };
"""
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
        await pg.add_script_tag(content=EDGE)
        await pg.add_script_tag(content="window.module={};")
        await pg.add_script_tag(path='/tmp/csgchk/csg-1.0.1/package/csg.js')
        await pg.add_script_tag(path='/tmp/csgchk/modeling-2.13.0/package/dist/jscad-modeling.min.js')
        print(await pg.evaluate("typeof CSG+' '+typeof jscadModeling"))
        # evanw csg union
        r=await pg.evaluate(r"""(()=>{ const toCSG=t=>{const polys=[]; for(let k=0;k<t.length;k+=9){ const vs=[0,3,6].map(o=>new CSG.Vertex(new CSG.Vector(t[k+o],t[k+o+1],t[k+o+2]),new CSG.Vector(0,0,1))); polys.push(new CSG.Polygon(vs)); } return CSG.fromPolygons(polys)};
          const fromCSG=c=>{const out=[]; c.toPolygons().forEach(p=>{const v=p.vertices; for(let i=1;i<v.length-1;i++) for(const q of [v[0],v[i],v[i+1]]) out.push(q.pos.x,q.pos.y,q.pos.z)}); return new Float32Array(out)};
          const t0=performance.now(); const u=toCSG(cache.body.tris).union(toCSG(cache.bill.tris)); const t1=performance.now(); const tri=fromCSG(u);
          const half=CSG.cube({center:[0,-500,0],radius:[1000,500,1000]}); const t2=performance.now(); const L=toCSG(cache.body.tris).subtract(half); const t3=performance.now();
          return {unionMs:Math.round(t1-t0), union:edgeCheck(tri), V:massProps(tri).V, halfMs:Math.round(t3-t2), half:edgeCheck(fromCSG(L))} })()""")
        print('evanw csg.js', r)
        r=await pg.evaluate(r"""(()=>{ const M=jscadModeling, {geom3}=M.geometries;
          const toG=t=>{const polys=[]; for(let k=0;k<t.length;k+=9) polys.push([[t[k],t[k+1],t[k+2]],[t[k+3],t[k+4],t[k+5]],[t[k+6],t[k+7],t[k+8]]]); return geom3.fromPoints(polys)};
          const fromG=g=>{const out=[]; geom3.toPolygons(g).forEach(p=>{const v=p.vertices; for(let i=1;i<v.length-1;i++) for(const q of [v[0],v[i],v[i+1]]) out.push(q[0],q[1],q[2])}); return new Float32Array(out)};
          const t0=performance.now(); const u=M.booleans.union(toG(cache.body.tris),toG(cache.bill.tris)); const t1=performance.now(); const tri=fromG(u);
          const half=M.primitives.cuboid({center:[0,-500,0],size:[2000,1000,2000]});
          const t2=performance.now(); const L=M.booleans.subtract(toG(cache.body.tris),half); const t3=performance.now();
          // hollow: subtract scaled? skip
          return {unionMs:Math.round(t1-t0), union:edgeCheck(tri), V:massProps(tri).V, halfMs:Math.round(t3-t2), half:edgeCheck(fromG(L))} })()""")
        print('jscad', r)
        print('body V', await pg.evaluate("massProps(cache.body.tris).V+massProps(cache.bill.tris).V"))
        await b.close()
asyncio.run(main())
