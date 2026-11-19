import asyncio, json
from playwright.async_api import async_playwright
L='/tmp/libs/'
MAP={'three.min.js':L+'three-0.128.0/package/build/three.min.js','OrbitControls.js':L+'three-0.128.0/package/examples/js/controls/OrbitControls.js','jszip.min.js':L+'jszip-3.10.1/package/dist/jszip.min.js'}
JS=r"""
() => {
 const out={};
 const c=cache, p=c.p, A=c.A;
 out.mass=A.M; out.net=A.net; out.area=A.bm.A; out.V=A.bm.V;
 out.coatVol_cm3=A.bm.A*p.coat/1000; out.coatMass=1.1*A.bm.A*p.coat/1000;
 out.tabVol=TAB*2*c.bill.outline.tabHW*p.billT; out.tabMass_g=BILL_MATS[p.billMat].rho*out.tabVol/1000;
 // inside test of body (analytic)
 const inside=(x,y,z)=>{ if(x<=0||x>=p.L) return false; const [t,b,w]=radii(x/p.L,p); const zz=z>=0?z/t:z/b; return Math.pow(Math.abs(y/w),p.se)+Math.pow(Math.abs(zz),p.se) < 1; };
 const B=c.bill.B, T=p.billT/2, o=c.bill.outline;
 let tabOut=0, tabN=0, exposedIn=0, expN=0;
 for(let u=-TAB;u<=0;u+=0.5) for(const v of [-o.tabHW,o.tabHW]) for(const s of [-T,T]){ const q=B.root.clone().addScaledVector(B.d,u).addScaledVector(B.n,s); q.y=v; tabN++; if(!inside(q.x,q.y,q.z)) tabOut++; }
 // exposed bill root edge points: u in 0..5 at v=+-hwRoot
 const hwRoot=Math.min(9,o.R);
 for(let u=0;u<=4;u+=0.5) for(const v of [-hwRoot,0,hwRoot]) for(const s of [-T,T]){ const q=B.root.clone().addScaledVector(B.d,u).addScaledVector(B.n,s); q.y=v; expN++; if(inside(q.x,q.y,q.z)) exposedIn++; }
 out.tabCornersOutsideBody=`${tabOut}/${tabN}`; out.exposedBillPointsInsideBody=`${exposedIn}/${expN}`;
 out.tieInsideBody=inside(A.pts.tie[0],0,A.pts.tie[2]);
 // Monte Carlo overlap volume bill exposed ∩ body
 const inv=new THREE.Matrix4().copy(B.M).invert(); let hit=0,N=200000; const bb=new THREE.Box3().setFromBufferAttribute(c.bill.geo.attributes.position);
 const sz=bb.getSize(new THREE.Vector3()); const vbox=sz.x*sz.y*sz.z; const q=new THREE.Vector3();
 // point-in-bill: transform to local (u,v,s) and test against outline polygon & |s|<T
 const poly=o.pts; const pip=(x,y)=>{let r=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const [xi,yi]=poly[i],[xj,yj]=poly[j]; if(((yi>y)!=(yj>y))&&(x<(xj-xi)*(y-yi)/(yj-yi)+xi)) r=!r;} return r;};
 let inBill=0, inBoth=0, exposedInBoth=0;
 for(let i=0;i<N;i++){ q.set(bb.min.x+Math.random()*sz.x,bb.min.y+Math.random()*sz.y,bb.min.z+Math.random()*sz.z); const l=q.clone().applyMatrix4(inv);
   if(Math.abs(l.z)<=T && pip(l.x,l.y)){ inBill++; if(inside(q.x,q.y,q.z)){ inBoth++; if(l.x>0) exposedInBoth++; } } }
 out.billVol_MC=inBill/N*vbox; out.overlapVol_mm3=inBoth/N*vbox; out.exposedOverlap_mm3=exposedInBoth/N*vbox; out.Vbill_used=A.Vbill;
 // manifold check: count edges by position
 const edgeCheck=(t)=>{ const key=(i)=>`${t[i].toFixed(4)},${t[i+1].toFixed(4)},${t[i+2].toFixed(4)}`; const E=new Map(); let deg=0;
   for(let k=0;k<t.length;k+=9){ const a=key(k),b=key(k+3),cc=key(k+6); if(a===b||b===cc||a===cc){deg++;continue}
     for(const [x,y] of [[a,b],[b,cc],[cc,a]]){ const kk=x<y?x+'|'+y:y+'|'+x; const d=x<y?1:-1; const e=E.get(kk)||{n:0,s:0}; e.n++; e.s+=d; E.set(kk,e);} }
   let bad=0, nonopp=0; for(const e of E.values()){ if(e.n!==2) bad++; else if(e.s!==0) nonopp++; } return {tris:t.length/9,edges:E.size,nonManifoldEdges:bad,inconsistentWinding:nonopp,degenerate:deg}; };
 out.bodyMesh=edgeCheck(c.body.tris); out.billMesh=edgeCheck(c.bill.tris);
 const st=slotTris(p,B); let sOut=0; for(let k=0;k<st.length;k+=3) if(!inside(st[k],st[k+1],st[k+2])) sOut++; out.slotCutterVertsOutsideBody=`${sOut}/${st.length/3}`;
 out.billTip_actual=o.tip; out.billLen_param=p.billLen;
 return out;
}
"""
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':1440,'height':880})
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        async def route(r):
            u=r.request.url
            for k,v in MAP.items():
                if u.endswith(k): return await r.fulfill(path=v, content_type='application/javascript')
            if 'fonts' in u: return await r.abort()
            await r.continue_()
        await pg.route('**/*',route)
        await pg.goto('file:///home/claude/team/index_v4.html'); await pg.wait_for_timeout(2500)
        for k in ['toman90','crank70','square60','minnow110']:
            await pg.evaluate(f"loadDesign(PRESETS.{k}.p,null,'x')"); await pg.wait_for_timeout(300)
            print(k, json.dumps(await pg.evaluate(JS)))
        # short bill wide
        await pg.evaluate("P.billLen=10;P.billW=40;changed()"); await pg.wait_for_timeout(300)
        print('shortwide', await pg.evaluate("({tip:cache.bill.outline.tip,len:cache.p.billLen})"))
        # memory
        m0=await pg.evaluate("JSON.stringify(renderer.info.memory)+' prog '+renderer.info.programs.length")
        await pg.evaluate("(async()=>{for(let i=0;i<60;i++){P.L=60+i; rebuild(); renderer.render(scene,camera);} })()")
        m1=await pg.evaluate("JSON.stringify(renderer.info.memory)+' prog '+renderer.info.programs.length")
        print('mem before/after 60 rebuilds', m0, m1)
        t=await pg.evaluate("(()=>{const t0=performance.now(); for(let i=0;i<10;i++) rebuild(); return (performance.now()-t0)/10})()")
        print('rebuild ms', t)
        # NaN sweep
        res=await pg.evaluate("""(()=>{ const bad=[]; const base=JSON.parse(JSON.stringify(PRESETS.toman90.p));
          const items=GROUPS.flatMap(g=>g.items).concat(SIM_ITEMS).filter(i=>i.type!=='select');
          for(const it of items) for(const v of [it.min,it.max]){ P=Object.assign({},base,{[it.k]:v}); try{ rebuild(); const A=cache.A,s=cache.sim;
            const vals=[A.M,A.net,A.depth,A.vPause,...A.CG,...A.CB,s.maxZ,s.T,cache.swim.f];
            if(vals.some(x=>!isFinite(x))) bad.push(it.k+'='+v+' nonfinite'); if(s.T>=900) bad.push(it.k+'='+v+' sim hit 900s cap');
            if(!A.ballInside) bad.push(it.k+'='+v+' ballOutside'); if(!cache.bill.holeOK) bad.push(it.k+'='+v+' holeOff');
          }catch(e){bad.push(it.k+'='+v+' THROW '+e.message)} }
          // combos
          const combos=[{L:40,top:35,bot:35,halfW:25},{L:160,top:4,bot:4,halfW:3,billW:40,billLen:85},{fat:0.6,taper:0.4},{fat:0.2,taper:1.6,se:3.5},{ballN:8,ballD:12},{style:'pump',tps:0.3,gear:'5.2',spoolD:25},{style:'stopgo',tps:3,goTurns:12,pauseS:4}];
          for(const cmb of combos){ P=Object.assign({},base,cmb); try{rebuild(); const A=cache.A,s=cache.sim; bad.push('combo '+JSON.stringify(cmb)+' M='+A.M.toFixed(2)+' net='+A.net.toFixed(2)+' T='+s.T.toFixed(0)+' ballInside='+A.ballInside+' dz='+(A.CB[2]-A.CG[2]).toFixed(2)) }catch(e){bad.push('combo THROW '+e.message)} }
          return bad; })()""")
        for r in res: print(' ', r)
        # ball row check
        print(await pg.evaluate("(()=>{P=Object.assign({},PRESETS.toman90.p,{ballN:8,ballD:8}); rebuild(); const p=cache.p; const off=(p.ballN-1)/2*p.ballD*1.02; return {ballInside:cache.A.ballInside, firstBallX:p.ballX-off, lastBallX:p.ballX+off}})()"))
        # import robustness
        r=await pg.evaluate("""(()=>{const out=[]; for(const params of [{L:'90'},{hookStr:'x5'},{bodyMat:'oak'},{hookB:2},{L:0},{billW:null}]){ try{ loadDesign(params,null,'t'); rebuild(); out.push(JSON.stringify(params)+' ok M='+cache.A.M+' viewBox='+document.getElementById('side').getAttribute('viewBox')) }catch(e){ out.push(JSON.stringify(params)+' THROW '+e.message) } } return out })()""")
        for x in r: print(' import', x)
        # fish.trigger sticky
        print('trigger sticky?', await pg.evaluate("(()=>{fish.trigger=true; spawnFish(false); fishReset(); spawnFish(true); return fish.trigger})()"))
        print('errors', errs[:5])
        await b.close()
asyncio.run(main())
