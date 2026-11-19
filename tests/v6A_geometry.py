"""v6 Stage A geometry / model suite (Node, pure model code from index.html + trimesh).
 - every family preset builds: finite numbers, BOM / costing / 4 drawing sheets, ranges from the brief
   (3/8 oz spinnerbait 10-12 g, pencil rest 20-60 deg, topwaters / frogs float, sinkers sink, densities of lead / tungsten / brass / silicone / PVC)
 - every solid (bodies, cast heads, spoon blank, spinner / prop / buzz blades) is watertight: JS edge check + trimesh
 - convert-to-editable keeps the mass (< 6 %), 60 random custom spline bodies with components stay watertight
 - v5 crank presets: analysis / dive / swim / release identical to team/index_v5.html (bit for bit)
Run: python3 -I v6A_geometry.py      (exit 1 on any failure)"""
import json, os, subprocess, sys, glob
HERE=os.path.dirname(os.path.abspath(__file__)); NODE=os.path.join(HERE,'node'); OUT='/tmp/v6A_stl'
os.makedirs(OUT,exist_ok=True); [os.remove(f) for f in glob.glob(OUT+'/*.stl')]
fails=[]
r=subprocess.run(['node',os.path.join(NODE,'v6A_model.js'),OUT],capture_output=True,text=True,cwd=NODE)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
d=json.loads(r.stdout.strip().split('\n')[-1])
print(f"{'preset':11s} {'family':12s} {'g':>7s} {'net g':>7s} {'rest°':>6s}  strip")
for k,v in d['presets'].items():
    print(f"{k:11s} {v['family']:12s} {v['M']:7.2f} {v['net']:7.2f} {('' if v['rest'] is None else v['rest']):>6}  {v['strip'] or ''}")
    print('            KPIs:',' | '.join(v['kpis']) if v['kpis'] else '(crank KPIs)')
print('convert-to-editable:',', '.join(f"{k} {v['M0']}→{v['M1']} g ({v['pct']}%)" for k,v in d['convert'].items()))
print('custom fuzz:',d['fuzz'])
for f in d['fails']: print('FAIL',f); fails.append(f)
stls=sorted(os.path.join(OUT,f) for f in d['stls'])
r=subprocess.run([sys.executable,'-I',os.path.join(HERE,'stageA_meshcheck.py')]+stls,capture_output=True,text=True)
lines=r.stdout.strip().split('\n'); bad=[l for l in lines if 'watertight=False' in l or 'winding=False' in l]
print(f'trimesh: {len(lines)} solids checked, {len(bad)} not watertight'); [print('  ',l) for l in bad[:10]]
if r.returncode: fails.append('trimesh watertight')
r=subprocess.run(['node',os.path.join(NODE,'v6A_v5compat.js')],capture_output=True,text=True,cwd=NODE)
print(r.stdout.strip()); 
if 'IDENTICAL' not in r.stdout: fails.append('v5 crank figures differ'+r.stderr[-300:])
print('ALL PASS' if not fails else 'FAIL: '+'; '.join(fails)); sys.exit(1 if fails else 0)
