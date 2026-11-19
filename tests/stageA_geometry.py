"""Stage A geometry test: builds body_L / body_R / body_shell / bill for every preset in Node (pure model code
extracted from index.html), verifies them with trimesh, fuzzes 300 random designs, prints report numbers.
Run: python3 -I stageA_geometry.py      (exit 1 on any failure)"""
import json, os, subprocess, sys
HERE=os.path.dirname(os.path.abspath(__file__)); NODE=os.path.join(HERE,'node'); OUT='/tmp/stageA_geom'
os.makedirs(OUT,exist_ok=True); fails=[]
r=subprocess.run(['node',os.path.join(NODE,'report_numbers.js'),OUT],capture_output=True,text=True,cwd=NODE)
if r.returncode: print(r.stderr); sys.exit(1)
rows=json.loads(r.stdout.strip().split('\n')[-1])
print(f"{'preset':10s} {'V_L':>7s} {'V_R':>7s} {'shell':>7s} {'m_shell':>8s} {'old A*w':>8s} {'m_old':>6s} {'cavity x':>13s} pins slot | print exact vs A*wall | tab HW old→new, % outside old→new | ms fast/full")
for x in rows:
    print(f"{x['preset']:10s} {x['VL']:7.3f} {x['VR']:7.3f} {x['Vshell']:7.3f} {x['mShell']:7.2f}g {x['oldA_wall']:8.3f} {x['mOld']:5.2f}g {str(x['cav']):>13s} {x['pins']:4d} {str(x['slot']):5s}| "
          f"{'wood (solid)' if x['wood'] else f'''{x['printExact']:.3f} vs {x['printOld']:.3f} cm3 ({100*(x['printOld']/x['printExact']-1):+.0f}%)'''} | "
          f"{x['tabOld']:.1f}→{x['tabNew']:.1f} mm, {x['outOld']:.1f}%→{x['outNew']:.1f}% | {x['tFast']:.0f}/{x['tFull']:.0f}")
    if not all(x['checks']): fails.append(x['preset']+' JS mesh check')
stls=sorted(os.path.join(OUT,f) for f in os.listdir(OUT) if f.endswith('.stl'))
r=subprocess.run([sys.executable,'-I',os.path.join(HERE,'stageA_meshcheck.py')]+stls,capture_output=True,text=True)
print(r.stdout.strip())
if r.returncode: fails.append('trimesh watertight')
r=subprocess.run(['node',os.path.join(NODE,'fuzz.js'),'300','4242'],capture_output=True,text=True,cwd=NODE)
print('fuzz:',r.stdout.strip().split('\n')[-1])
if 'fails=0' not in r.stdout: fails.append('fuzz')
print('ALL PASS' if not fails else 'FAIL: '+', '.join(fails)); sys.exit(1 if fails else 0)
