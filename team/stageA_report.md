# Stage A report: correctness and production engineering (A1–A9)

File: `/home/claude/umpan-lab/index.html` (1306 → about 2560 lines; still one file). Backup of v4: `/home/claude/team/index_v4_backup.html`.

## What was done

**A1: bugs B1–B9 and B11 (plus B10)**
- **B1.** The tab is now sized from the local body section: 80 % of the body half-width along u ∈ [−TAB, −1.5].
- **B2.** The coat volume is added to displacement.
- **B3.** Bill mass includes the tab. The tab is subtracted only from displacement.
- **B4.** The shell mass is now exact:
  - printed bodies use outer loft minus inner loft;
  - injection uses the exact half mesh.
- **B5.** `billOutline().tip` is used in the side view, the 1:1 SVG, the drawing, depth, plan area, camera and grid.
- **B6.** The inside check now tests every ballast ball.
- **B7.** The fish state is read before `fishReset`.
- **B8.** `spawnFish` clears `fish.trigger`.
- **B9.** One schema (`paramSchema()`, built from `GROUPS` and `SIM_ITEMS`) now drives everything:
  - `validateParams`, which applies `Number()` + clamp, integer rounding and enum fallback;
  - validators for paint, meta, colourway, BOM and cost;
  - `migrateDesign`, which reads v2, v1 and legacy localStorage formats;
  - `loadDesign` and `safeRebuild`, which roll back if a build fails.
- **B11.**
  - Collinear outline points are removed.
  - The line-tie hole is now an explicit 24-gon. `absarc` had left a near-duplicate point, which caused the 4 zero-area triangles.
  - The underwater world and the fish are built lazily on the first swim.
  - Every SVG font has fallbacks.
- **B10.** Marker and eye materials are shared, and the grid material is disposed.

**A2: production mode "Injection ABS — 2-half mold"** (`productionGeometry(p, full)`)
- New parameters: `wallMm`, `draftDeg`, `flangeMm`, `pins`, `wireGauge`.
- The halves are built analytically from the loft grid, as in review_dev §2:
  - The canonical half is columns j = 16..48 with y forced to 0.
  - The inner loft uses radii − wall (− flange at the seam) between solid nose and tail plugs.
  - The parting face is earcut of the outline, with holes for the cavity and the pins.
  - The bill-slot pocket is a through-pocket. Skin triangles are clipped in XZ, because each half is a height field. It has vertical walls and a floor at the tab depth plus 0.1. T-junctions are removed by tracking each vertex's parent grid edge.
  - Pins are real geometry, not separate bodies: Ø2.0 × 1.5 bosses on L and Ø2.1 × 1.8 blind holes on R. Draft is applied to both. They sit in the solid plugs, and the plugs grow until a hole with a 0.7 mm floor fits.
  - `body_R` is the mirror of the canonical half. `body_shell` is L + R welded at y = 0, with the parting faces removed.
- Mass and buoyancy in injection mode use the exact shell volume.
- DFM checks (`dfmChecks`):
  - minimum wall, measured;
  - plug lengths;
  - slot pocket wall;
  - tab volume outside the body;
  - root inside the body;
  - draft zones, from analytic surface gradients;
  - pins;
  - ballast inside the cavity;
  - mesh check;
  - the TODOs.

**A3: hardware library and BOM.**
- `hardwareRows()` is the single source for both the BOM and the weight model. It uses generic codes such as `TRB-1/0-4X-BN`, `SPR-5-SS-BN` and `WIR-SS304-1.0`.
- `wire` (grams) is replaced by the wire gauge. The wire length comes from the harness path (tab anchor → belly → tail) plus 3 eyes.
- Two parts were added to the mass model: the line-tie split ring and the 3D eyes.
- The BOM table in the Release tab is editable and stored as `spec.bom.overrides`. Mass or qty edits on hardware rows feed the weight model.

**A4: revision control.**
- Family code, rev and status (Concept → T0 → T1 → Golden → Released).
- SKU rule: `UL-{family}{L}{class}-{colour}`.
- Save diffs the spec against the last baseline and appends a changelog entry.
- Sign-off table (drawn / checked / approved).
- Released locks the spec, paint, colourway and BOM inputs. The sim inputs stay editable. Reopening bumps the rev (A → B).
- The SHA-256 is computed over the canonical spec JSON (sorted keys). It uses crypto.subtle with a pure-JS fallback, and both match Python's hashlib.
- Saved JSON is v2: `{spec{…params, production, paint, colourway, bom.overrides}, sim{…}, costing, meta{family, modelCode, sku, rev, status, changelog[], signoff{}, specSha256}, results}`. Costing is kept outside the spec.

**A5: tech pack.**
- `drawingModel()` builds one primitive list. It is rendered by `sheetSVG()` (an A3 SVG in mm) and by `sheetPDF()` (jsPDF vectors, lazy-loaded from cdnjs).
- The drawing contains:
  - side, top and front views, 1st-angle projection, with auto scale 2:1, 1:1 or 1:2;
  - sections A–A to D–D at 2:1, showing the exact superellipse and the mold wall;
  - real dimensions with arrows (L, hanger X, overall, H, W, bill length aligned, bill angle);
  - the bill flat pattern with dimensions;
  - the hardware coordinate table;
  - the spec block (class, weight ±0.3, float rate, depth by line, Hz);
  - specific tolerances;
  - notes;
  - the title block (model, SKU, rev, status, date, scale, mm, ISO 2768-m, drawn / checked / approved, SHA-256).
- PDF page 2 has the BOM, QC criteria, costing, DFM, colourway and revisions.
- `techpackHTML()` is self-contained and printable.

**A6: QC.**
- `qcCriteria()` covers weight ±0.3, float rate, depth at 0.5 and 1.0 m/s ±0.3, tracking ±50, roll, and the hook-pull proof load (0.6 × the lowest rating).
- `qc_criteria.md` adds the AQL 2.5 GII table, defect classes and the test procedure.
- The `tank_test.csv` template includes TARGET / TOL rows.
- Importing a measured CSV gives a per-sample pass/fail table and a summary. Delimiters `,`, `;` and tab are accepted.

**A7: costing** (`costing()`). Resin plus runner, bill, hardware from the BOM, paint by complexity level, glue, packaging, assembly, QC, scrap, then mold and bill-tool amortisation. Output is unit cost and FOB at 1k / 3k / 5k, in `costing.csv`.

**A8: colourway.** Code, name, Pantone / RAL, finish, paint complexity and layer stack. Changing the paint pattern pre-fills them.

**A9: release pack** (`exportReleasePack()`). The zip contains:
- `body_L.stl`, `body_R.stl`, `body_shell.stl`, `bill.stl`;
- `assembly_preview.stl` and `preview.png`;
- `sections.csv` (25 stations, outer and inner);
- `drawing.svg`, `techpack.html`, `techpack.pdf`;
- `bom.csv`, `qc_criteria.md`, `tank_test.csv`, `costing.csv`;
- `design.json` and `README.txt`;
- `qc_results.csv`, if a tank test was imported.

**UI (kept minimal for Stage B)**
- New sidebar group **Production**: build mode, mold parameters, identity and revision, colourway, and an open-book halves preview.
- New bottom tab **Release / tech pack**:
  - SKU, revision and hash bar with the 5 export buttons;
  - drawing preview;
  - production figures;
  - revision and sign-off;
  - DFM checks;
  - editable BOM;
  - costing inputs and results;
  - QC import and results.
- ⤢ makes the panel taller.

**Code layout for Stage B.** Everything above the `UI: controls` marker is DOM-free; `tests/node/load_model.js` runs it in Node. The view functions to re-house are:
- `buildProductionExtras`, `syncMeta`, `setStatus`, `applyLock`;
- `renderRelease`, `relDirty`;
- `exportReleasePack`, `exportOne`;
- `loadDesign`, `loadPreset`, `logChanges`, `safeRebuild`.

## Verified (numbers)

`tests/stageA_geometry.py` runs Node and then trimesh. `tests/stageA_release.py` runs Playwright end to end with 59 checks and passes all of them. The original `check.py` and `uw.py` pass, with no page errors.

| preset | body_L cm³ | body_R cm³ | exact shell cm³ / ABS g | old area×wall cm³ / g | old tab outside → new | printed shell, exact vs A×wall |
|---|---|---|---|---|---|---|
| toman90 | 5.227 | 5.206 | 10.435 / 10.96 | 8.284 / 8.70 | 23.5 % → 3.5 % | 6.13 vs 6.63 (+8 %) |
| crank70 | 3.428 | 3.407 | 6.837 / 7.18 | 5.478 / 5.75 | 24.0 % → 2.3 % | 3.36 vs 3.65 (+9 %) |
| square60 | 2.485 | 2.464 | 4.951 / 5.20 | 4.308 / 4.52 | 32.7 % → 0.4 % | wood (solid) |
| minnow110 | 3.108 | 3.087 | 6.198 / 6.51 | 6.052 / 6.35 | 47.9 % → 1.4 % | 3.63 vs 4.03 (+11 %) |

- **Watertight.** All 16 exported STLs (L, R, shell and bill × 4 presets) and the STLs in the zip pass trimesh. Each is watertight, has consistent winding, has 0 edges whose use count is ≠ 2 and has 0 degenerate faces. Each half is 1 body; the shell is 2 closed surfaces (skin and cavity). The bill STL had 3 open edges and 4 degenerate faces before; it now has none.
- **Fuzz.** 750 random designs (450 during development plus 300 in the suite) gave 0 non-watertight halves.
  - About 9 % of them are extreme bill roots where the slot cannot be molded. They are flagged as a DFM error and exported without a slot.
  - About 4 % fit fewer than 2 pins, which is a DFM warning.
- **The area×wall estimate is wrong for molded parts.** Injection mass with the exact shell is about 2.3 g heavier than area×wall on toman90, because the nose and tail plugs and the 0.4 mm seam land are solid.
- **toman90 (v4 → v5).**
  - v4: 25.1 g, +4.8 g net.
  - v5 prototype: 24.8 g, +6.3 g net. The changes come from the coat displacement (B2), tab mass (B3), exact shell (B4), and the new tie ring, eyes and wire.
  - v5 injection: 24.35 g, +6.72 g net, class F, SKU `UL-TDC90F-FT01`.
  - BOM in-lure mass is 24.350 g against 24.353 g in the model. The 3 mg gap is pin volume minus hole volume.
- **Exports.**
  - The PDF has 2 pages, A3 landscape, vector only (no images), and its text is extractable.
  - The SVG is `420mm × 297mm`.
  - All CSVs parse.
  - The hash in `design.json` matches Python's SHA-256 of the canonical spec. The same hash is printed on drawing.svg, README, techpack.html, the PDF and the Release tab.
- **Import.**
  - A v1 file with `L:"92"`, `hookStr:'x5'`, `bodyMat:'oak'`, `hookB:2`, `top:'abc'` and `se:99` loads with 6 listed corrections.
  - Non-design JSON is rejected with the state unchanged.
  - A build error during load rolls back.
  - A legacy localStorage entry (`wire 0.7 g`) loads as Ø0.8.
- **Speed.** Injection mode adds 50–90 ms per rebuild (memoized). The full halves for the preview or release take 130–200 ms.

## Deferred, or done differently

- **Not modelled:**
  - **Harness channel and ballast pocket.** They are listed as a TODO in the DFM list, the drawing notes, the tech pack and the README. The harness path and ballast centre are drawn.
  - **Eye sockets.**
- **Slot walls are modelled at 0° draft.** The DFM note asks the toolmaker for ≤ 0.5°. `draftDeg` is applied to the pins and holes. The outer skin is checked analytically, not modified.
- **`flangeMm` is modelled as extra wall at the dorsal and ventral seam.** It widens the glue land; there is no tongue-and-groove.
- **No 3MF, DXF or STEP.** `sections.csv` (25 exact stations) is provided for re-lofting.
- **Out of scope for A:**
  - multiple colourways per body;
  - colour_chart.pdf;
  - SKU, EAN and packaging;
  - Monte Carlo tolerance study;
  - render-on-demand.
- **Release figures always use injection mode in fresh water.** The tab says so when the design panel is in prototype mode.
- **BOM mass edits on molded, bill or paint rows only change the BOM.** Hardware mass and qty edits feed the weight model.
- **UI is functional but cramped** in the 270 px bottom panel, and the header wraps at 1440 px. This is left for Stage B.
