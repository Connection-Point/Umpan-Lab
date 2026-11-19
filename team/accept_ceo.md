# Umpan Lab v5: CEO acceptance

Inspected `accept/TDC90-FT01_revA_release.zip` (toman90, injection mode, made with `tests/ceo_accept.py`), the PDF at 300 dpi, the SVG and all CSV/MD files.

## Requirements

| # | Req | Mark | Evidence |
|---|---|---|---|
| 1 | Injection 2-half | MET | Watertight L/R halves, Ø2/2.1 pins, 1.5 wall, 1° draft, exact mass, DFM. Pocket and channel are only a TODO. |
| 2 | Tech pack | PARTIAL | Views, sections, tolerances and title block are complete. Text is about 1.5 mm cap height, labels overlap and the eyes are not located. |
| 3 | BOM CSV | MET | All fields, rated kg, wire Ø1.0×127. BOM 24.35 g equals the model. |
| 4 | Rev/sign-off | PARTIAL | SHA, lock and changelog work. Released is allowed with blank sign-off. |
| 5 | QC/tank | MET | AQL 2.5 GII, defect classes, TARGET/TOL template, import gives pass/fail. |
| 6 | Colourway | PARTIAL | One colourway only, Pantone "TBD", no colour chart. |
| 7 | Costing | PARTIAL | No moulding cycle cost. The margin is applied to tooling. Tooling is buried in FOB. |
| 8 | SKU/packaging | NOT MET | SKU string only. No EAN-13, blister size, carton or card copy. |
| 9 | Internals | PARTIAL | The harness path and ballast are drawn. No bend points, rattle chamber or magnet rail. Ballast fixed or loose is not stated. |
| 10 | Calibration/MC | NOT MET | No fit from tank data and no tolerance study. |

## BLOCKERS

1. **Text size.** Raise the minimum drawing text to 2.5 mm cap height (ISO 3098) and titles to 3.5 mm. Today 93 labels are 2.1 font units and the title block is 1.7. Factories print at A4, so this becomes unreadable.
2. **Overlaps in the side view.** "20° ±1°" sits on "bill 50.0 ±0.3". The "SLOT (note 5)" leader crosses line A. "PL" collides with the tail eye. Offset these labels and add a label-overlap test.
3. **Release gate.** Refuse T1, Golden and Released until three things are in place: sign-off names and dates, zero DFM errors, and Pantone/RAL filled. Below Released, stamp "NOT FOR PRODUCTION – {status}" on the PDF and SVG.
4. **Costing.**
   - Add moulding cost: machine USD/h × cycle s ÷ cavities.
   - Apply the margin to the variable cost only.
   - Show tooling (NRE USD 6,950) as a separate line.
   - Give FOB both excluding and including tooling.
   - Add currency, Incoterm and the rate date.
5. **Packaging.**
   - EAN-13 with a check digit.
   - Lure envelope (134.4 mm plus hook drop) → blister inner L×W×D +5 mm.
   - Carton qty and dimensions.
   - packaging.csv plus a block on PDF page 2.
6. **Eyes and ballast.**
   - Locate the eyes (x, z, recess) in the hardware table and the side view.
   - State "ballast fixed in Ø6.2 pocket" or "loose rattle", with pocket dimensions.
7. **Glyph.** The glue size prints "?0.02 g" because jsPDF has no ≈. Replace non-Latin-1 symbols in PDF text.

## NICE-TO-HAVES

- Default to Injection mode at status T0 or later. Today the strip shows 24.8 g (PLA) and the tech pack 24.35 g.
- Label the side view "15.0" dimension and give it ±0.2. Add a wall leader "1.50 ±0.15" on B–B.
- tank_test.csv: add lot, date, operator, water_temp_c and line columns.
- BOM:
  - add a bill adhesive line;
  - add a primer line;
  - add a `moq` column;
  - add a `leadTimeDays` column.
- 2–6 colourways per body, each with a swatch, a side render PNG and its own SKU suffix.
- A harness bend-point table and a wire-forming sketch.
- A tolerance Monte Carlo giving "% out of class F" on the spec block.
- Card copy in BM/EN.
- Design KPI 4.5 Hz vs spec 2.8/5.7 Hz: state the speed on the Design KPI.

**Verdict:** major progress. Geometry, BOM and QC are factory-grade. After blockers 1–4 I would send for a T0 RFQ. I would not raise a production PO until 5–7 are also closed.
