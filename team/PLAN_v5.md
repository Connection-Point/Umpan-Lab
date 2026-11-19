# Umpan Lab v5 — consolidated build plan
Sources: review_ceo.md (stakeholder), review_dev.md (developer), review_ux.md (UI/UX). Working file: /home/claude/umpan-lab/index.html (single-file artifact; may add sibling files only if loaded by relative path — prefer keeping one file).

Sandbox constraints (unchanged): scripts only from cdnjs / cdn.jsdelivr.net/npm / unpkg; no fetch; no alert/confirm/prompt; downloads only through `await claude.use("downloads")` → `save({filename,data})` with extensions zip/svg/json/csv/pdf/html/md/txt/png (STL/3MF only inside a zip); localStorage may throw; Google Fonts may be blocked → always give font fallbacks.

## Stage A — correctness + production engineering (developer agent #1)
A1  Bugs B1–B9, B11 from review_dev.md (tab/slot sized to body, coat volume in displacement, tab mass, exact shell mass, bill tip consistency, per-ball inside check, fish restart + trigger reset, import schema validation/migration/rollback, collinear points, lazy underwater env creation, SVG font fallbacks).
A2  Production mode "Injection ABS — 2-half mold": params wallMm (1.2–2.0, default 1.5), draftDeg (0–3, default 1), flangeMm (0–1.5), pins on/off. Analytic hollow shell (inner loft) and LEFT/RIGHT halves split exactly at y=0, watertight per half, parting face with bill-slot pocket and Ø2 pin / Ø2.1 hole pairs; ballast pocket + harness channel recess if feasible (else documented as TODO in tech pack). Mass/buoyancy use exact shell volume. DFM checks list (wall < 1.2, local radius < wall+0.3, pocket wall < 1.0, bill tab outside body).
A3  Hardware library + BOM: editable part table (partNo, desc, spec, size, finish, ratedKg, mass_g, supplier, unitCostUSD, qty) seeded with generic-but-realistic entries (no real brand part numbers needed; use descriptive codes like TRB-1/0-4X-BN). Replace free `wire` grams with wire gauge (0.8/1.0/1.2 mm SS304) + computed length from harness path → mass. Export bom.csv.
A4  Revision control: modelCode, sku (rule UL-{family}{L}{class}-{colourCode}), rev letter, status (Concept→T0→T1→Golden→Released), changelog auto-diff on save, SHA-256 (crypto.subtle) of the spec JSON printed on exports, sign-off table (drawn/checked/approved name+date). Status Released ⇒ inputs locked.
    Separate saved JSON into `spec` (product) and `sim` (angler/simulation) sections; migrate v1 files.
A5  Tech pack (Release): dimensioned drawing SVG (A3 landscape, mm): side/top/front views, sections A–A..D–D, bill flat pattern + slot, hardware coordinates, title block with general tolerance ISO 2768-m and explicit tols (L ±0.3, weight ±0.3 g, bill angle ±1°, hanger X ±0.3, slot billT +0.1/+0.2). Spec block (F/SP/S class, float rate, target depth by line, action Hz est.). Export techpack.html (self-contained, printable) and techpack.pdf via jsPDF from cdnjs (draw vectors directly).
A6  QC: qc_criteria.md + tank_test.csv template (sample_id, weight_g, float_rate_cms, depth_05_m, depth_10_m, tracking_mm, roll_ok, hook_pull_kg) with target ± tolerance; import measured CSV → per-sample pass/fail table + summary.
A7  Costing: rates (resin USD/kg, paint labour per colourway complexity, packaging, mold cost & MOQ amortisation) → unit cost at 1k/3k/5k; costing.csv.
A8  Colourway: colour code (e.g. FT01), name, layer stack text, Pantone/RAL reference text fields, finish; listed in tech pack.
A9  Production zip ("Release pack"): body_L.stl, body_R.stl, body_shell.stl, bill.stl, assembly preview, sections.csv (25 stations of exact superellipse sections), drawing.svg, techpack.html, techpack.pdf, bom.csv, qc_criteria.md, tank_test.csv, costing.csv, design.json, README.txt.

## Stage B — UX restructure (developer agent #2, after A)
B1  Mode switcher in a single-row app bar: Design / Analyse / Simulate / Release (role=tablist). File ▾ menu (presets, open saved, import, delete with in-page confirm dialog), Export ▾ menu, design name + Rev + status badge + unsaved indicator.
B2  Spec strip (always visible): length · weight · class · dive est · hooks · issue chip (click → checks).
B3  Design mode: accordion groups (Shape, Bill, Hardware, Ballast, Material/Production, Finish) with Basic/Advanced, renamed labels (Body width (full) etc. — keep internal keys), label for/aria, fixed unit column, double-click label to reset.
B4  KPI provenance tags CALC/EST/MODEL + targets; hook-up odds & reel move to Simulate.
B5  Analyse mode: side profile large + mass table + hook clearance table + DFM checks.
B6  Simulate mode: retrieve settings full-width in panel; transport bar (▶ Swim, speed, Underwater, Fish, Strike); strike card → non-blocking toast stack bottom-left + session log. Fish game tagged as marketing/estimate.
B7  Release mode: tech-pack sheet preview (read-only), revision/sign-off form, BOM table editor, QC import, costing, colourway, export buttons.
B8  Resizable bottom panel (splitter, persisted), a11y (focus-visible, AA contrast: orange #b4500f for white text, warn uses ink text, aria-live on status/checks, canvas role=img), narrow layout (<1100px: sticky viewport + tabs).
B9  Render on demand when idle (not swimming) to save CPU.

## Stage C — acceptance
CEO agent + UX agent review the running build against their reviews; developer fixes blockers; publish.
