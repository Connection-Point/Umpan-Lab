"""Watertightness / volume check of exported STL files with trimesh.
usage: python3 -I stageA_meshcheck.py file1.stl [file2.stl ...]   (exit code 1 if any mesh is not watertight)"""
import sys, collections, trimesh, numpy as np
bad=0
for f in sys.argv[1:]:
    m=trimesh.load(f, force='mesh', process=False)
    m.merge_vertices(digits_vertex=7)
    e=collections.Counter(map(tuple, np.sort(m.edges,axis=1)))
    nonman=sum(1 for v in e.values() if v!=2)
    degenerate=int((m.area_faces<1e-12).sum())
    ok=m.is_watertight and m.is_winding_consistent and nonman==0
    bad+= not ok
    print(f"{f.split('/')[-1]:34s} tris={len(m.faces):6d} watertight={m.is_watertight} winding={m.is_winding_consistent} "
          f"edges!=2:{nonman} degenerate:{degenerate} volume={m.volume/1000:.3f}cm3 bodies={len(m.split(only_watertight=False))}")
sys.exit(1 if bad else 0)
