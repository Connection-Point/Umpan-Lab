"""Toman deep-diving crankbait (4 m class) — generates STL meshes, 1:1 SVG templates and a preview.
Units: millimetres. Axes: X along body (nose=0 -> tail), Y width, Z up.
"""
import numpy as np, trimesh, manifold3d as m3d
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os, json

OUT = os.path.join(os.path.dirname(__file__), "out"); os.makedirs(OUT, exist_ok=True)

# ---------------- parameters ----------------
L        = 90.0   # body length
TOP_MAX  = 15.0   # back height above axis
BOT_MAX  = 13.0   # belly depth below axis
HALF_W   = 10.0   # half width (20 mm wide)
A, B     = 0.45, 0.85   # nose bluntness / tail taper
SE       = 2.4    # superellipse exponent (slightly boxy flanks -> more wobble)
TAIL_R   = 3.2    # tail thickness kept for the hook hanger
LIP_ANG  = 20.0   # lip angle below body axis (deg); lower = deeper
LIP_LEN  = 50.0   # exposed bill length
LIP_W    = 26.0   # max bill width
LIP_T    = 2.5    # bill thickness (printed)
TAB_LEN  = 10.0   # part of bill that sits inside the body
TIE_U    = 14.0   # line-tie hole distance from bill root
LIP_ROOT = np.array([3.0, 0.0, -6.0])  # where the bill leaves the nose

def f(t):
    v = (t ** A) * ((1 - t) ** B)
    tm = A / (A + B); return v / ((tm ** A) * ((1 - tm) ** B))

def g(t):  # keeps a rounded tail instead of a needle
    return np.sqrt(np.clip(1 - t ** 10, 0, 1))

def radii(t):
    base = f(t)
    s = np.clip((t - 0.35) / 0.45, 0, 1); s = s * s * (3 - 2 * s)  # smoothstep blend into tail
    top = TOP_MAX * base + TAIL_R * g(t) * (1 - base) * s
    bot = BOT_MAX * base + TAIL_R * g(t) * (1 - base) * s
    w   = HALF_W  * base + TAIL_R * 0.8 * g(t) * (1 - base) * s
    return top, bot, w

# ---------------- body mesh ----------------
NS, NA = 160, 96
t = (1 - np.cos(np.linspace(0, np.pi, NS))) / 2
ang = np.linspace(0, 2 * np.pi, NA, endpoint=False)
verts = []
for ti in t[1:-1]:
    top, bot, w = radii(ti)
    for a in ang:
        c, s = np.cos(a), np.sin(a)
        y = w * np.sign(c) * abs(c) ** (2 / SE)
        z = (top if s >= 0 else bot) * np.sign(s) * abs(s) ** (2 / SE)
        verts.append([ti * L, y, z])
verts = np.array(verts); nose = len(verts); verts = np.vstack([verts, [0, 0, 0], [L, 0, 0]]); tail = nose + 1
faces = []; R = NS - 2
for i in range(R - 1):
    for j in range(NA):
        a0, a1 = i * NA + j, i * NA + (j + 1) % NA
        b0, b1 = a0 + NA, a1 + NA
        faces += [[a0, b0, a1], [a1, b0, b1]]
for j in range(NA):
    faces.append([nose, j, (j + 1) % NA])
    o = (R - 1) * NA; faces.append([tail, o + (j + 1) % NA, o + j])
body = trimesh.Trimesh(verts, np.array(faces), process=True)
body.fix_normals()
assert body.is_watertight

# ---------------- bill (lip) ----------------
def lip_polygon():
    pts = []
    us = np.linspace(-TAB_LEN, LIP_LEN - LIP_W / 2, 40)
    for u in us:  # right edge
        if u < 0: hw = 7.0
        else:
            k = min(u / (LIP_LEN - LIP_W / 2), 1)
            hw = 9.0 + (LIP_W / 2 - 9.0) * np.sin(k * np.pi / 2)
        pts.append((u, hw))
    c = LIP_LEN - LIP_W / 2
    for a in np.linspace(0, np.pi, 40)[1:-1]:
        pts.append((c + (LIP_W / 2) * np.sin(a), (LIP_W / 2) * np.cos(a)))
    pts += [(u, -hw) for (u, hw) in pts[:40][::-1]]
    poly = Polygon(pts).buffer(0)
    return poly.difference(Point(TIE_U, 0).buffer(1.1, 32))  # 2.2 mm tie hole

lip2d = lip_polygon()
lip_local = trimesh.creation.extrude_polygon(lip2d, LIP_T)
lip_local.apply_translation([0, 0, -LIP_T / 2])
th = np.radians(LIP_ANG)
d = np.array([-np.cos(th), 0, -np.sin(th)])   # forward/down
n = np.array([-np.sin(th), 0, np.cos(th)])    # bill normal
M = np.eye(4); M[:3, 0] = d; M[:3, 1] = [0, 1, 0]; M[:3, 2] = n; M[:3, 3] = LIP_ROOT
lip = lip_local.copy(); lip.apply_transform(M)

def to_m(tm): return m3d.Manifold(m3d.Mesh(np.asarray(tm.vertices, np.float32), np.asarray(tm.faces, np.uint32)))
def from_m(mf):
    me = mf.to_mesh(); return trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts)

# body with slot for the bill (separate parts) + one-piece assembly
slot = trimesh.creation.extrude_polygon(Polygon([(-TAB_LEN - 0.5, -7.3), (2, -7.3), (2, 7.3), (-TAB_LEN - 0.5, 7.3)]), LIP_T + 0.4)
slot.apply_translation([0, 0, -(LIP_T + 0.4) / 2]); slot.apply_transform(M)
body_slot = from_m(to_m(body) - to_m(slot))
assembly = from_m(to_m(body) + to_m(lip))

body_slot.export(f"{OUT}/toman_crank_body_slotted.stl")
lip.export(f"{OUT}/toman_crank_bill.stl")
assembly.export(f"{OUT}/toman_crank_assembly.stl")

# hardware / ballast points (body frame)
tie = LIP_ROOT + d * TIE_U
hard = {"line_tie": tie.round(1).tolist(), "belly_hanger": [40.0, 0, -radii(40 / L)[1] + 0.5],
        "tail_hanger": [L - 1.5, 0, 0], "ballast_center": [36.0, 0, -6.0]}
hard = {k: [round(float(x), 1) for x in v] for k, v in hard.items()}

# ---------------- 2D templates (1:1 SVG) + preview ----------------
xs = t * L; tops, bots, ws = zip(*[radii(x) for x in t])
tops, bots, ws = np.array(tops), np.array(bots), np.array(ws)
lip_side = [LIP_ROOT + d * u + n * s for u, s in [(-TAB_LEN, LIP_T/2), (LIP_LEN, LIP_T/2), (LIP_LEN, -LIP_T/2), (-TAB_LEN, -LIP_T/2)]]

def svg():
    W, H = 160, 130; ox, oy = 45, 35
    side = " ".join(f"{ox+x:.2f},{oy-z:.2f}" for x, z in zip(np.r_[xs, xs[::-1]], np.r_[tops, -bots[::-1]]))
    lipp = " ".join(f"{ox+p[0]:.2f},{oy-p[2]:.2f}" for p in lip_side)
    oy2 = 100
    top = " ".join(f"{ox+x:.2f},{oy2-y:.2f}" for x, y in zip(np.r_[xs, xs[::-1]], np.r_[ws, -ws[::-1]]))
    lb = np.array(lip2d.exterior.coords)
    liptop = " ".join(f"{ox+LIP_ROOT[0]-u*np.cos(th):.2f},{oy2-v:.2f}" for u, v in lb)
    dots = "".join(f'<circle cx="{ox+p[0]}" cy="{oy-p[2]}" r="1" fill="red"/><text x="{ox+p[0]+1.5}" y="{oy-p[2]+3.5}" font-size="2.6">{k.replace("_"," ")}</text>' for k, p in hard.items())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="sans-serif">
<rect width="{W}" height="{H}" fill="white"/>
<text x="5" y="7" font-size="4" font-weight="bold">Toman Deep Crank 90 — 1:1 template (print at 100%)</text>
<text x="5" y="12" font-size="3">SIDE VIEW</text>
<polygon points="{side}" fill="#f1e3c8" stroke="black" stroke-width="0.3"/>
<polygon points="{lipp}" fill="#cfe6f5" stroke="black" stroke-width="0.3"/>
<line x1="{ox}" y1="{oy}" x2="{ox+L}" y2="{oy}" stroke="#999" stroke-dasharray="1,1" stroke-width="0.2"/>
{dots}
<text x="5" y="72" font-size="3">TOP VIEW (bill shown flat-projected)</text>
<polygon points="{liptop}" fill="#cfe6f5" stroke="black" stroke-width="0.3"/>
<polygon points="{top}" fill="#f1e3c8" stroke="black" stroke-width="0.3"/>
<line x1="{ox}" y1="122" x2="{ox+50}" y2="122" stroke="black" stroke-width="0.5"/><text x="{ox}" y="127" font-size="3">50 mm scale check</text>
</svg>'''
open(f"{OUT}/toman_crank_template_1to1.svg", "w").write(svg())

fig = plt.figure(figsize=(12, 7))
ax = fig.add_subplot(221); ax.fill_between(xs, -bots, tops, color="#e8c26a", ec="k")
P = np.array(lip_side); ax.fill(P[:, 0], P[:, 2], color="#9cc8e8", ec="k")
for k, p in hard.items(): ax.plot(p[0], p[2], "ro"); ax.annotate(k, (p[0], p[2]), fontsize=7, xytext=(3, -9), textcoords="offset points")
ax.set_aspect("equal"); ax.set_title("Side (mm)"); ax.grid(alpha=.3)
ax = fig.add_subplot(223); ax.fill_between(xs, -ws, ws, color="#e8c26a", ec="k"); ax.set_aspect("equal"); ax.set_title("Top (mm)"); ax.grid(alpha=.3)
ax = fig.add_subplot(122, projection="3d")
v = assembly.vertices; ax.plot_trisurf(v[:, 0], v[:, 1], v[:, 2], triangles=assembly.faces, color="#e8c26a", lw=0, alpha=.95)
ax.set_box_aspect((np.ptp(v[:, 0]), np.ptp(v[:, 1]), np.ptp(v[:, 2]))); ax.view_init(18, -60); ax.set_title("Assembly")
plt.tight_layout(); plt.savefig(f"{OUT}/toman_crank_preview.png", dpi=130)

info = {"body_volume_cm3": round(body.volume / 1000, 2), "bill_volume_cm3": round(lip.volume / 1000, 2),
        "overall_length_mm": round(float(np.ptp(assembly.vertices[:, 0])), 1),
        "assembly_watertight": bool(assembly.is_watertight), "hardware_points_mm": hard,
        "bbox": assembly.bounds.round(1).tolist()}
json.dump(info, open(f"{OUT}/info.json", "w"), indent=2); print(json.dumps(info, indent=2))
