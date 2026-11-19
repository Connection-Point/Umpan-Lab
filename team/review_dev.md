# Umpan Lab v4: developer / CAD review

Findings come from headless probes in `tests/probe_dev*.py` and `probe_csg*.py`. The app files were not modified.

## 1. Correctness bugs

| # | Where | What I measured | Fix |
|---|---|---|---|
| B1 | `billOutline` `tabHW=min(7,R-0.5)` | The bill tab is 14 mm wide at a root where the body is only 7–9.5 mm wide. **16–37 % of the tab volume sits outside the body** in all 4 presets, about 2.2 mm per side on toman90 and 3.5 mm on minnow110. **18/36 to 36/36 slot-cutter vertices are outside the body**, so subtracting the cutter opens the skin and the print leaks. | Size the tab from the local section: `tabHW = min(7, 0.75*w(x,z))` sampled along u∈[-TAB,0] (superellipse width at height z). |
| B2 | `analyse` displacement | Coat mass is counted (`1.1·A·coat`), but the coat volume (0.7–1.1 cm³) is **not added to `Vd`**. Net buoyancy is about 1.1 g too low on toman90 (4.85 g shown). | `disp.push({v:bm.A*p.coat, c:bm.C})` |
| B3 | `analyse` `mBill` | Tab mass is dropped (`Vbill = lm.V - tabVol`). The tab is real PC/FR4 inside the body: 0.25–0.42 g. The bill CG still includes the tab. | Mass = `rho*lm.V`, CG = `lm.C`. Subtract the tab only from displacement. |
| B4 | `analyse` printed body | The shell is approximated as `A·wall`. That is about 18 % above an inward loft: 6.63 vs 5.59 cm³ on toman90, roughly 1 g of PLA. | Use the exact hollow-shell mesh from §2 and take `massProps(outer) − massProps(inner)`. |
| B5 | `billOutline` vs `billSideCorners`, depth, `planA` | For a short, wide bill the real tip is `max(billLen−R,1)+R`. With billLen=10 and billW=40 the **STL tip is 21 mm, but the side view, 1:1 SVG and physics use 10**. | Return `o.tip` and use it everywhere, or clamp `billLen ≥ R+1` in the UI. |
| B6 | `ballInside` | Only the centre ball is tested. With 8×8 mm balls the flag reads `true` while **2 of 8 balls stick out at the nose**. | Loop over each ball at `ballX+(i-(N-1)/2)*D*1.02`. |
| B7 | `updateFish` l.976 | `fishReset()` sets `state='none'` before `if(fish.state==='lost')` runs, so the retrieve-restart line is dead code. | Save the state before resetting. |
| B8 | `fish.trigger` | It is set on an event and **never cleared** (confirmed). Every later strike gets the +12 % "reaction strike" bonus. | Set `fish.trigger=false` in `spawnFish`. |
| B9 | Import / `loadDesign` | No validation. `{L:"90"}` gives viewBox width **9064** (string concat in `p.L+…`). `hookStr:'x5'`, `bodyMat:'oak'` and `hookB:2` throw inside rAF. P is then poisoned and every slider change throws until a preset is loaded. | Build a schema from `GROUPS`+`SIM_ITEMS`: `Number()` then clamp, check enums against their tables (fall back to default), coerce selects with `String()`, read `version`, migrate. Run `rebuild` in try/catch and roll back to the previous P on failure. |
| B10 | Memory | 60 rebuilds: geometries 44→41 and programs stay at 4, so **no GPU leak**. Markers, eyes and the grid make new materials on every rebuild. They are GC'd (WeakMap) but wasteful. | Share those materials and dispose `grid.material`. |
| B11 | Minor | 4 zero-area triangles in the bill STL (outline points along the tab edge are collinear). The Google Fonts `<link>` is blocked by the sandbox. `causticTex` costs **210 ms at startup** even if the user never swims. | Dedupe collinear outline points. Use system fonts. Build the underwater world lazily. |

A min/max sweep of every slider plus 7 extreme combinations gave no NaN or Infinity. The body STL has 0 non-manifold edges and consistent outward winding. The SVG is truly 1:1.

**Assembly STL:** two intersecting shells, and because of B1 the tab pierces the flanks. Mold shops reject self-intersecting assemblies.

## 2. What a factory or mold maker needs

**CSG in the browser is not viable here.** I checked these:
- `three-bvh-csg` needs three ≥0.151 (latest ≥0.179) plus `three-mesh-bvh` ≥0.159.
- `three-csg-ts` 3.1.x accepts r125+, but it is only published as CJS or ESM that does `import 'three'`, so loading it beside the UMD global needs an import-map hack.
- evanw `csg.js` (`csg@1.0.1`) **overflows the stack** on the 13.8k-triangle body.
- `@jscad/modeling` (UMD) works, but union takes **3.8 s and returns 419 non-manifold edges**. The half-space split takes 3.6 s with 226 bad edges.
- manifold-3d needs a `.wasm` fetch, which the sandbox likely blocks.

**Feasible instead: analytic generation.** The body is a lofted superellipse on an (i, j) grid, so most solid operations can be built exactly:

1. **Left/right halves.** With NA=64, columns j=16 and j=48 lie exactly on y=0 (force `y=0`). Each half is columns 16..48 (or 48..16), and its parting face is a strip of quads between the top and bottom ring points at each station. The result is watertight by construction. Add Ø2 pins on one half and Ø2.1 holes on the other.
2. **Hollow wall shell.** Build an inner loft with `top−wall`, `bot−wall`, `halfW−wall` over t∈[t₀,t₁] where every radius is greater than wall+0.3. Cap it, reverse its winding, and leave solid nose and tail plugs. The wall is exact for round sections and within about 10 % for se≤3. Split it at y=0 the same way to get half-shells.
3. **Pockets and harness channel.** Draw the parting face as a `THREE.Shape` (Earcut is in r128) with holes for the bill-slot section, the ballast pocket circles, and a 1.2 mm channel polyline running tie → belly → tail. Then add the side walls and floor of each recess by extruding down by the depth. This is the one hard part.
4. **STEP.** True NURBS STEP is not realistic client-side (opencascade.js is tens of MB). A faceted STEP is possible but is just a mesh in disguise. The realistic route is a **station-section export** (CSV/DXF of 25 sections plus the profile curves) that the shop re-lofts in SolidWorks or Fusion in minutes, with **3MF** (zip + XML, explicit mm units, multiple named bodies) alongside the STL.
5. **Dimensioned drawing (SVG, A4/A3 in mm).** It should have side, top and front views, sections A–A to E–E at chosen stations (exact superellipse curves), a dimensioned bill flat pattern and slot, hardware coordinates, and a title block with tolerances (ISO 2768-m, slot = billT +0.1/+0.2). PDF can come from jsPDF (cdnjs UMD) drawing lines directly, without needing svg2pdf.
6. **BOM CSV and spec sheet (md/html).** Both can be built from `A.parts` plus hardware sizes, ring ratings, wall/infill, CG/CB and net buoyancy.
7. **Draft check.** Colour each vertex by the angle between its normal and ±Y. Each half is y-monotone, so there are no undercuts apart from the slot and eyes.

## 3. Code structure that matters

- Split a pure **model** (params → body/bill/shell/halves → analysis) from the **view**, so the maths can be unit-tested in Node.
- Keep one parameter schema, used for the UI, clamping, import and migration.
- Give paint changes a fast path that recolours vertices only, with no rebuild.
- Render on demand when not swimming. It currently renders at 60 fps all the time.
- Create the underwater world and fish lazily on the first Swim.
- Write all exports from one immutable `cache` snapshot.

## 4. Top-10 implementation list

1. B1: tab and slot sized to the body (S)
2. B2–B4: buoyancy and mass fixes (S)
3. B9: import schema, validation and migration with rollback (S)
4. B5–B8, B11: small bugs (S)
5. Analytic left/right halves with parting face and pins (M)
6. Hollow shell (inner loft and caps) and exact shell mass (M)
7. Parting-face pockets: bill slot, ballast, harness channel (L)
8. Dimensioned drawing SVG and PDF with sections and tolerances (M)
9. BOM CSV, spec sheet, station-section CSV/DXF, 3MF (S–M)
10. Model/view split, render-on-demand, lazy environment (M)
