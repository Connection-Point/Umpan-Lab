# Umpan Lab v5: UX acceptance (Stage C)

**Evidence.**
- Scripts: `tests/ux_accept_audit.py` (4 viewports × 4 modes, swim, strike, menus) and `tests/ux_accept_a11y.py` (Tab walk, contrast).
- Images: `tests/ux_accept_*.png`.
- 0 console errors; `stageB_ui.py` ALL PASS.

## Original 10 changes

| # | Verdict | Evidence |
|---|---|---|
| 1 Modes | MET | Tablist, arrow keys, hash links. Fishing UI is in Simulate only. |
| 2 Release/tech pack | MET | SKU, Rev, lock, A3 preview, BOM, costing, QC, sign-off, SHA. |
| 3 Spec strip | PARTIAL | Always visible; chip opens Checks. It says "✓ No issues" while DFM shows 3 ⚠. |
| 4 Header/menus | MET | 52 px row at 1440 and 1280. Delete asks first. Unsaved flag is shown. |
| 5 A11y | MET | 0 unlabeled inputs (of 117 and 268). Teal `:focus-visible` on every Tab stop. No text contrast failures. |
| 6 Accordion/labels | MET | One group open, Advanced, renamed labels, unit column. |
| 7 KPI provenance | PARTIAL | Tags and legend present. Weight shows only "QC ±0.3", no target band. |
| 8 Splitter | MET | Drag or keyboard; height persists. Sim rows are full width. |
| 9 Toast/transport | MET | Toast bottom-left, collapses. The lure is never covered. |
| 10 Narrow/undo | PARTIAL | Sticky view, tabs and `[`/`]` work. No undo/redo. |

## BLOCKERS

1. **The camera doesn't refit when the lure gets longer** (`ux_accept_L130_1440.png`).
   - At L 90→110→130, the lure's right edge moves 1068→1201→1358 px. The canvas ends at 1120, so the tail and hook leave the screen.
   - Fix: call an eased `fitCamera()` when the bounding box passes 85 % of the frustum.
2. **Below 1100 px, Rev and Unsaved are hidden** (`.doc .rev,.doc .dirty{display:none}`). Tablet users can lose edits without a warning.
   - Fix: keep a dot with `aria-label` next to `#dname`, and show "A · Concept" in the badge.
3. **On narrow screens Analyse looks the same as Design** (`analyse_1024`, `analyse_390`). Params stays selected, so the mass, hook and DFM tables stay hidden.
   - Fix: switch to `data-ntab=results` when Analyse is entered.
4. **The swim HUD is hidden below 1100 px** (`#swimInfo{display:none}`), so speed and depth go missing.
   - Fix: show a compact one-line HUD at 10 px.

## POLISH

- **Release BOM table** scrolls sideways (1143 px in a 934 px area at 1280). Cell inputs cut text off, e.g. "Through-wire harness (tab ancho…". Fix: wrap the desc/spec cells and add `title`.
- **Selects cut off their text:** `#p-clarity` ("Tea-stained (reservo…") and `#cwCx`. Fix: shorter options or `min-width:150px`.
- **A unit gets clipped:** `span.u` shows "turns" as "turn". Fix: make the column 34 px.
- **The dive chart is about 330 px wide at 1280**, with labels about 6 px. Fix: `#dive{width:100%}` and put the text below the chart.
- **The side profile in Design** has CB/CG labels about 6 px. Fix: set a minimum font size.
- **Group header "MATERIAL & PRODUCTION"** wraps, and "· locked" splits across lines. Fix: shorten the label, or `nowrap` on the badge.
- **Released number fields still look editable.** Fix: `input:disabled{background:var(--paper);color:var(--mute)}`.
- **Release at 1440** leaves an empty column under Production figures. Fix: move Sign-off there.
- **At 390 `#dname` is cut off with no ellipsis.** Fix: add `text-overflow:ellipsis` and `title`.
- **The strike toast at 390** covers about 30 % of the view. Fix: `max-width:180px` and collapse after 2 s.
- **Range `aria-describedby`** points at the number field (value read twice). Fix: remove it.

**Verdict:** ACCEPT once Blockers 1–4 are fixed. Polish can follow.
