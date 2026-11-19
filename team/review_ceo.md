# Umpan Lab v4 — CEO Stakeholder Review

**Question:** Can our product team and our contract factories (China/Malaysia, injection-molded ABS, PC bills, SS through-wire, blister-carded) go from Umpan Lab to mass production?
**Verdict:** Not yet. It is a strong **concept and pre-sample tool**. It is not a **production hand-off tool**. Approve for R&D use now, and approve for factory use once the MUST items below ship.

## 1. What already has business value

- **Fast concept iteration.** 8 body and 7 bill parameters plus presets let a designer explore a family in minutes.
- **Buoyancy and balance maths.** Per-part mass, net buoyancy (+4.8 g), CB–CG margin (6.8 mm) and pause rise rate (~18 cm/s) decide whether a SKU ships as F, SP or S. That is the costliest thing to get wrong after the mold is cut.
- **Hardware checks.** Hook-swing circles catch tie fouling and treble tangles before samples, which saves a sample round.
- **Dive simulation (gear ratio, retrieve style)** gives defensible card claims ("3.5–4 m on PE3, 6.3:1").
- **Underwater toman strike scene** is marketing and dealer-training material, not engineering.
- **Exports** (STLs, slot cutter, 1:1 SVG, JSON) are enough for a 3D-printed **T0 look-and-feel sample**.

## 2. What a factory still needs (against OEM practice)

A factory quotes and tools from a **tech pack per SKU**. Today's outputs fall short in these areas:

| Area | Today | Factory needs |
|---|---|---|
| Drawing | 1:1 SVG outline, 50 mm scale bar, no dimensions | Dimensioned 3 views with tolerances (L ±0.3 mm, bill angle ±1°, hanger X ±0.3 mm), title block |
| Body construction | "ABS (3D print)" shell + infill; solid STL | **Two-half mold** split at Y=0: hollow shell, **1.2–2.0 mm wall**, 1–2° draft, weld/glue flange, harness channel, ballast pockets, rattle chamber, bill-slot clearance; L/R half STLs |
| BOM | Weight table; hooks are a generic "#1/0 4X"; wire is only "1.0 g" | Treble model/size/finish ("VMC 9626 #1/0 BN"), split ring size + **rated kg**, SS304 wire Ø0.8–1.2 mm + harness drawing, ballast, rattle, 3D eyes, PC bill grade |
| Paint | Hex picker, 6 patterns, preview only | Colourway code (FT01), layer stack (base, foil, pearl, stencil), **Pantone/RAL refs**, finish, top-coat thickness |
| Buoyancy class | Label + net g | F/SP/S class, **weight ±0.3 g**, float/sink rate at 28 °C fresh water |
| QC / tank test | One note: "tank-test it" | Swim at 0.5/1.0 m/s, tracking ±50 mm over 3 m, no roll-over, depth ±0.3 m, float rate, hook-pull test, AQL 2.5 GII |
| Packaging/SKU | Free-text name | SKU code, EAN-13, blister size, carton qty, BM/EN card copy |
| Costing | None | Per-part cost, labour, packaging, mold amortisation, FOB |
| Control | localStorage plus JSON `version:1` | Model code, **rev letter**, change log, status (Concept→T0→T1→Golden→Released), sign-off |

**Further issues:**
- The JSON mixes product spec with angler/simulation settings (cast distance, gear, clarity). These need to be separated.
- The depth model is "calibrated on typical floating crankbaits", and there is no way to feed our own tank results back into it.
- The "ABS" choice models a print with infill, not a molded hollow shell.

## 3. Top 10 requirements to approve

1. **MUST – Production material mode "Injection ABS 2-half".** Hollow shell with `wallMm` 1.2–2.0, `draftDeg`, `flangeMm` and `partingPlane:"Y0"`. Recompute mass and buoyancy for the hollow body. Run DFM checks (wall < 1.2, zero-draft zones near the parting line, ballast pocket wall < 1.0). Export `body_L.stl` and `body_R.stl` with alignment-pin bosses inside the zip.
2. **MUST – Tech-pack export (PDF + HTML in zip).** One page per SKU containing:
   - a dimensioned side/top/front drawing with a per-field `tol` value;
   - a spec block (L, weight ± tol, F/SP/S class, float rate, target depth by line class, action Hz);
   - a title block (model code, rev, date, drawn/checked/approved).
3. **MUST – Hardware library + BOM CSV.** An editable table (`partNo, desc, spec, size, finish, ratedKg, mass_g, supplier, unitCostUSD, qty`) covering hooks, rings, wire Ø, eyes, ballast, rattles and the bill. Replace the free-gram `wire` field with gauge + length. Export `bom.csv`.
4. **MUST – Revision control & sign-off.** Fields `modelCode`, `rev` (A, B…) and `status`, an auto-diff change log, a SHA-256 of the spec JSON printed on every export, and a sign-off table with name/date. Lock edits when status is "Released".
5. **MUST – QC acceptance sheet + tank-test log.** Auto-generate `qc_criteria.md` and a `tank_test.csv` template with target ± tolerance (weight, depth at 0.5/1.0 m/s, tracking, roll, float rate, hook-pull). An import of the measured CSV shows pass/fail per sample.
6. **SHOULD – Colourway manager.** Several colourways per body, each with `code`, layer stack, Pantone/RAL refs, finish and eye spec. Export `colour_chart.pdf` with swatches and side-view renders (PNG).
7. **SHOULD – Costing sheet.** Rate tables for resin per gram, hardware per BOM line, paint labour per colourway complexity, packaging and mold cost/qty, used to amortise per unit. Output unit FOB at 1k/3k/5k MOQ to `costing.csv`.
8. **SHOULD – SKU & packaging generator.** A naming rule such as `UL-TDC90F-FT01`, EAN-13 field and check digit, blister dimensions checked against the lure envelope including hooks, and carton qty. Export `packaging.csv` plus a card-copy HTML (BM/EN).
9. **SHOULD – Internals editor.** Through-wire harness path drawing (bend points), rattle chamber, fixed weight pockets and an optional magnet weight-transfer rail, drawn on the 2D drawing and included in the mass/CG calculation.
10. **COULD – Calibration & tolerance study.**
    - Fit the depth/action coefficients per family from imported tank-test data.
    - Run a ±tolerance Monte Carlo (weight, wall, bill angle) and report the % of units that fall outside the buoyancy class.
    - Move the fish strike scene behind a "Marketing" toggle.

*These are requirements for v5.*
