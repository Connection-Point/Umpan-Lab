# Umpan Lab v5: Stage C final report (acceptance fixes)

**Files**
- Working file: `/home/claude/umpan-lab/index.html`. It is still one file, 3437 lines (md5 `a012d535e3e3…`).
- Unchanged baseline: `/home/claude/team/index_stageB.html`.
- Pieces used to build it: `team/drawing_v5c.js` (drawing engine) and `team/render_release_v5c.js` (Release view).

**Test status: every suite passes with zero page errors.**

| Suite | Result |
|---|---|
| `stageA_geometry.py` | ALL PASS, including the 300-design fuzz and trimesh watertight checks |
| `stageB_ui.py` | 72/72 |
| `stageB_release.py` | 60/60, updated for the 4-page PDF, packaging.csv, the gate and the new tank columns |
| `stageC_accept.py` (**new**) | 55/55 |
| `ux_accept_audit.py` | Now exits 1 on clipping, sideways scroll, unlabeled inputs or page errors. ALL PASS. |
| `ux_accept_a11y.py` | 0 contrast failures |
| `ceo_accept.py` | Re-exported the pack to `team/accept/pack/` and rendered `team/accept/tp-1..4.png` |

**Images reviewed by eye**
- `team/accept/tp-1..4.png` (Concept, watermarked) and `tp-golden-1..4.png`.
- `tests/ux_accept_*.png` and `tests/stageC_*.png`.

## CEO blockers

**1. Text size**
- **Fix**
  - Every drawing and PDF text is now at least 3.5 mm font, which is 2.5 mm cap height under ISO 3098 (Helvetica/Arial cap height is 0.716 em). The Courier SKU is 4.4 mm.
  - Titles are 5 mm, which is 3.6 mm cap height.
  - The minimum is enforced inside `sheet().text()`, so no text can be smaller.
- **Relayout.** The tech pack is now 4 A3 sheets.
  - **Sheet 1:** side, front and top views; spec; hardware coordinates; 8 notes; title block.
  - **Sheet 2:** sections at 2:1, bill flat pattern (scale picked automatically, 2:1 for toman90), specific tolerances, title block.
  - **Sheet 3:** BOM, costing, FOB by quantity, packaging.
  - **Sheet 4:** QC, DFM, colourway, revisions, release gate.
  - The release zip now has `drawing.svg` (sheet 1) and `drawing_sheet2.svg`.
- **Evidence**
  - `stageC_accept`: the Node check over all 4 presets × 4 sheets finds 0 texts with cap height under 2.5 mm.
  - pymupdf reads every PDF span and finds none under 2.5 mm cap height.

**2. Overlapping labels**
- **Fix**
  - Movable labels go through a collision resolver (`S.label` / `S.resolve`):
    - bill angle;
    - TIE, SLOT, CG, CB, EYE, BALLAST, PL;
    - the "wall" leader on B–B;
    - the eye y label in the front view;
    - a bill length dimension that is too short for its text.
  - The resolver tries rings of candidate positions. It rejects any position that collides with other text or with a dimension or section-cut line. It also penalises crossing the part outline, ballast circles or the eye.
  - Fixed dimension texts slide along their line, or move outside it, to avoid other text and the frame.
- **Evidence**
  - The `stageC_accept` overlap test checks text boxes pairwise, plus text outside the frame. It finds 0 on all 4 presets × 4 sheets.
  - Checked by eye in tp-1 for toman90, and in the crank70, minnow110 and square60 renders.

**3. Release gate and watermark**
- **Gate.** `releaseGate()` refuses T1, Golden and Released until all of these are true:
  - Drawn, Checked and Approved each have a name and a YYYY-MM-DD date;
  - Pantone / RAL is filled in and is not "TBD";
  - there are 0 DFM errors;
  - the EAN-13 is valid, if one was entered.
- **What the user sees when a status is refused**
  - The status select reverts.
  - The view switches to Release.
  - The Release gate card flashes, reads "T1 was refused", and lists every missing item.
- **Watermark.** Below Released, or when a Released status is loaded with the gate incomplete, every export carries a diagonal "NOT FOR PRODUCTION – <status>":
  - drawing sheets 1–2, all 4 PDF pages, techpack.html (overlay and banner) and the README;
  - the Release preview, which also shows a red bar.
- **Evidence (`stageC_accept`)**
  - T1 and Released are refused, and the message lists what is missing.
  - The T0 SVG and HTML are watermarked.
  - The gate opens once everything is filled in.
  - The Golden PDF is watermarked on 4/4 pages.
  - The Released SVG has no watermark.
  - `stageB_release` covers the refusal, the fill-in and the release.

**4. Costing**
- **Fix**
  - New inputs: machine USD/h, cycle s, and cavities (L+R sets per shot).
  - Moulding per unit = rate × cycle ÷ 3600 ÷ cavities. With the defaults (18 × 28 ÷ 3600 ÷ 4) that is 0.035 USD.
  - The margin applies to the unit (variable) cost only.
  - "FOB excl. tooling" is shown on its own.
  - Tooling NRE of 6,950 USD is a separate one-off line and is not in FOB.
  - "FOB incl. amortised tooling" is shown for 1k / 3k / 5k as information.
  - Currency, Incoterm (default FOB Port Klang) and the rate date are inputs. They appear in the UI, costing.csv, the PDF and the HTML.
- **Evidence:** `stageC_accept` checks every one of these against Python:
  - moulding;
  - variable = lines + scrap;
  - margin on unit cost only;
  - tooling = mold + die;
  - FOB incl. = FOB excl. + tooling ÷ qty.
  - `costing.csv` gives 1.4947 excl. tooling, and 8.4447 / 3.8114 / 2.8847 incl. tooling.

**5. Packaging**
- **New spec field `spec.packaging`.** It is hashed and locked on release, and contains:
  - EAN-13;
  - card W×H;
  - inner and carton qty;
  - card copy in EN and BM (left empty, it is generated automatically).
- **EAN-13.** Entering 12 digits adds the check digit automatically. A wrong check digit is flagged and blocks the gate.
- **Size check**
  - The lure envelope includes the hanging hooks: 145.7 × 63.7 × 26 mm for toman90.
  - The blister inner adds 5 mm: 151 × 69 × 31 mm.
  - The blister is checked against the card size, allowing a 30 mm hang header and margins.
- **Inner box and carton**
  - Inner box dimensions are computed.
  - The carton is the best grid of inner boxes: 5×2×2 = 505 × 402 × 438 mm, 6.8 kg gross.
- **Outputs**
  - `packaging.csv` is in the release zip.
  - A PACKAGING block is on PDF sheet 3, and also in the HTML.
  - The BOM packaging line now states the blister and card sizes.
- **Evidence:** base 955000000001 → 9550000000018, which equals the Python implementation. Known valid codes (4006381333931, 9780306406157) also pass. `packaging.csv` is in the zip with the EAN, blister and carton.

**6. Eyes and ballast**
- **Eyes**
  - `eyeSpec()` uses the same placement as the 3D view.
  - Each eye is located by x, ±y and z, with its Ø and a recess Ø(d+0.3) × 0.3.
  - They appear in the side, front and top views, the hardware table (row "Eye Ø4.0 L / R"), note 7, the HTML and the README.
- **Ballast**
  - New spec parameter `ballFix`: "glued in pocket" (default) or "loose rattle". It is in Design → Ballast.
  - Note 6 states the method with the pocket or chamber Ø × length and its centre.
  - The pocket outline is drawn in the side view.
  - The spec block, the DFM TODO, the tolerance table and the README use it.
- **Evidence:** the PDF text contains "EYE" and "GLUED IN POCKET" (`stageC_accept`).

**7. Glyphs**
- **Fix**
  - `pdfSafe()` keeps the Latin-1 symbols that jsPDF's WinAnsi fonts render (± ° Ø × · ³).
  - Everything else is mapped to ASCII: ≈→~, →→->, ✓/✗→OK/X, –/—→-, ≤/≥→<=/>=. Any other character falls back to its stripped accent, or is dropped.
  - The BOM glue size now reads "approx. 0.02 g".
- **Evidence:** pymupdf finds 0 "?" characters in any PDF span.

**CEO nice-to-haves done**
- T0 and later statuses switch the build to Injection.
- The side view "15.0 ±0.2" dimension, and the "wall 1.50 ±0.15" leader on B–B.
- `tank_test.csv` gains lot, date, operator, water_temp_c and line columns.
- BOM gains primer and bill-adhesive lines, plus `moq` and `leadTimeDays` columns (editable).
- Card copy in BM and EN.
- The Swim KPI states the speed ("at 0.78 m/s").

**Not done:** 2–6 colourways per body, the harness bend table / forming sketch, the tolerance Monte Carlo, and calibration from tank data.

## UX blockers

**1. Camera refit**
- **Fix**
  - `fitCamera()` now fits the lure's real bounding box (body, bill, hooks, eyes) to the FOV and aspect.
  - After each rebuild, `autoRefit()` does an eased (0.45 s) refit when:
    - the box would be clipped (any corner beyond 92 % of the view); or
    - the size changed by more than 15 % and the user has not orbited since the last fit.
  - A manual orbit is otherwise left alone.
  - A new **Fit** button sits in the camera segment.
- **Evidence**
  - At L=130 and L=40 the projected box is inside the canvas and wider than 30 % of it.
  - After a manual orbit, a small change does not move the camera.
  - Fit resets the "user moved" state.

**2. Rev and unsaved below 1100 px**
- **Fix**
  - The "●" dot stays visible with `aria-label="Unsaved changes"`; only its text label is hidden.
  - The badge reads "A · Concept".
  - At 560 px and below the brand shortens to "UL" so the name, badge and dot fit.
- **Evidence:** at 1024 and 390 the badge reads "A · Concept" and the dot is visible.

**3. Analyse on narrow screens**
- **Fix:** entering Analyse switches the narrow tab to Results; going back to Design restores Params.
- **Evidence:** at 1024 and 390, `#massTable` and `#dfmList` are visible (`stageC_analyse_*.png`).

**4. Swim HUD on narrow screens**
- **Fix:** a compact one-line HUD (speed, depth, Hz) at 10 px, bottom-right above the transport bar.
- **Evidence:** at 1024 and 390 the HUD is visible, at least 10 px, and clear of the transport bar.

**5. Issue chip (single source)**
- **Fix**
  - `issueList()` combines the design checks with the injection DFM (debounced, shared cached `relModel()`).
  - That one list drives the Checks list (DFM items are tagged), the chip and the narrow Checks tab.
  - Two permanent DFM notes are now "info" rather than warnings: the 0°-draft slot note and the toolmaker TODO.
- **Evidence:** the chip count equals the e/w items listed, and includes the DFM items (toman90: "! 2 issues").

**6. Release layout and readability**
- **BOM**
  - Fixed-layout table; text cells are auto-growing textareas that wrap, never truncate, and carry a title.
  - Enter commits an edit.
  - Number cells use compact inputs.
- **Other fixes**
  - Long selects are stacked full width (`#p-clarity`, `#cwCx`, `prodMode`, …).
  - The unit column is 36 px, so "turns" is not clipped.
  - The dive chart is drawn in CSS pixels at an 11 px font.
  - Side-profile labels are at least 11 px on screen.
- **Evidence (1280)**
  - BOM scrollWidth equals clientWidth, with 0 truncated cells.
  - Selects are not truncated.
  - "turns" measures 36/36.
  - Dive labels are 11.0 px and side labels 10.5 px.
  - `stageC_release_bom_1280.png`, `stageC_simulate_1280.png`.

**UX polish done**
- Disabled inputs use paper/mute styling.
- The group label is now "Material & mold", with nowrap on "· locked".
- Release at 1440: the right column stacks Gate, Sign-off and Production figures, so there is no empty column.
- The drawing preview has Sheet 1 / Sheet 2 buttons.
- `#dname` uses an ellipsis and a title.
- Strike toasts at 390: max 180 px wide, collapse after 2 s.
- The duplicate `aria-describedby` on ranges is removed.
- The weight KPI shows the QC band.

**Not done:** undo / redo.

## Compatibility
- Parameter keys are unchanged.
- New spec content: `ballFix` (in the Ballast group), `spec.packaging`, and new costing fields (costing is outside the hash).
- v1, v2 and legacy files load with defaults. Tested: a v1 file, and a v2 file without packaging or ballFix.
- The spec hash still equals Python's SHA-256 of the canonical spec.
- Hashes of old designs change once they are re-saved, because the spec gained fields. This was allowed in the brief.
- Mass and buoyancy figures are unchanged: toman90 is 24.35 g in injection mode and 24.8 g as a prototype.
