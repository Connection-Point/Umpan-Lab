# Umpan Lab v4 — UX review (CAD/configurator lens)

Evidence: `tests/shot1–3.png`, `uw1–3.png`, `side.png`, plus my own renders `tests/ux_1280.png`, `ux_390.png`, `ux_focus.png` (script `tests/ux_audit.py`, run against index_v4.html).

## 1. Top problems observed

1. **No workflow or hierarchy.** Design inputs, physics results, the fishing game and file I/O all have equal visual weight. Nothing tells a factory engineer which numbers are the spec and which are estimates. A score like "Hook-up odds 76 %" sits next to "Total weight 25.1 g" in the same card style (shot1).
2. **Header is a toolbar dump.** It wraps to 2 rows at 1440 px (97 px tall) and to 213 px at 390 px. The design name is cut off ("Toman Deep Crank 9(", shot1). The **✕ delete runs with no confirm and no undo** (line 1293). Exports are 4 equal-weight buttons with no context. Revision, units and saved/unsaved state are not shown.
3. **The sidebar is one long scroll.** It has 33 sliders, 33 number fields, 17 selects and 5 colour pickers. With only 3 groups open it is already 1404 px tall in a 783 px panel. Labels such as "Bill root X/Z", "Half width", "Fattest point × length" and "Flank squareness 2 = round" use solver terms, not drawing terms. Units sit in a grey `em` that wraps ("Angle below body axis ° (lower = deeper)").
4. **The KPIs give no reference.** The 11 cards have no target, tolerance or pass/fail band. Only colour changes ("6.8 mm" in green), with no legend. Estimates and model outputs are not marked as estimates. The **Checks list is below the fold** at 1440×880 and is about 2000 px down on mobile, so a red error can go unseen.
5. **The strike card covers the scene.** It is 290 px wide at top-right (uw2/uw3), over the lure and fish exactly when the user wants to watch. It also overlaps where `#fishLog` sits.
6. **The bottom panel is cramped at a fixed 270 px.** The side profile renders at about 50 % width. The dive sim squeezes 10 controls into a 230 px column, so labels wrap to 2 lines (shot3), and the result paragraph is cut off.
7. **The SVG uses a serif fallback.** `font-family="IBM Plex Mono"` has no fallback (line 1056), so CB/CG labels and the grid caption render in Times when offline (side.png). Factory PCs are often offline or behind a firewall.
8. **Narrow layouts.** At 1280 px the view toolbar wraps to 2 rows over the model. Below 1100 px the page becomes a 3000 px single column: header, then a 420 px view, then controls, then results. You cannot see a slider and its result together (ux_390.png).
9. **Accessibility.**
   - 85 of 88 inputs have no programmatic label: there is no `for` and no `aria-label`, and the range and number fields are siblings of a bare `<label>`.
   - There are no `:focus-visible` styles (0 rules), and the page has no ARIA roles or live regions. The canvas has no text alternative.
   - White on the orange Swim button is about 3.9:1, and white on the warn status (#c98a12) is about 3.0:1. Both fail AA.
   - `--mute` on paper is 4.6:1, which only just passes, and it is used at 11 px.
   - The profile tabs are `<button>` elements without `role=tab` or `aria-selected`.
10. **Exports are not discoverable for the factory.** There is no tech pack, drawing PDF, BOM, tolerances, revision or approval record. "Export STL pack" is the only primary action, and a QC engineer cannot tell from the name what is inside it.

## 2. Proposed information architecture

```
[Logo] [Design name ▾ · Rev C · ● Draft] | Design  Analyse  Simulate  Release | [Undo][Redo] [Share/Export ▾]
------------------------------------------------------------------------------------------
Spec strip: 90 mm · 25.1 g · Floating +4.8 g · Dive 3.8 m (est.) · Hooks 2× 1/0 4X · ⚠ 1 issue
------------------------------------------------------------------------------------------
Left: parameter tree   |  Viewport (3D / Side / Top / Section)  |  Right: context panel
```

- **Design** (default). Parameter groups appear as a stepper: *Shape → Bill → Hardware → Ballast → Material → Finish*. Only 1 group is open at a time (accordion). Each group has a **Basic / Advanced** toggle: Advanced holds `se`, `tailR`, `rootX/Z`, `wire`, `coat`, `infill`. The right panel shows the Spec + Checks.
- **Analyse.** The side profile goes full height, with mass breakdown, CG/CB, stability, a hook-swing clearance table and a sensitivity readout ("+1 mm ballast Z → −0.4 mm stability").
- **Simulate.** The retrieve settings move to the left panel, with the dive chart plus swim/strike. "Fishing conditions" moves here out of Design. The strike odds appear only in this mode and are tagged *model estimate*.
- **Release (Tech pack).** For the factory, laid out as a read-only A4/A3 sheet:
  - Title block: SKU, Rev, Date, Designer, Approver, Status (Draft / In review / Approved / Released).
  - Dimensioned 3-view drawing.
  - BOM: body material, bill material, ballast count/size/material, hooks, rings, wire.
  - Target weight ± tolerance, target float rate, ballast position with tolerance.
  - QC acceptance tests: tank float test, swim test at 0.8 m/s, pull test kg.
  - Revision history.
  - Export buttons: *Tech pack PDF*, *STL pack*, *1:1 template*, *Design JSON*.

## 3. Concrete UI changes

**Header**
```html
<header class="appbar">
  <div class="brand">Umpan<span>Lab</span></div>
  <div class="doc"><input id="dname" aria-label="Design name"><span class="rev">Rev C</span><span class="badge draft">Draft</span><span class="dirty" aria-live="polite">Unsaved</span></div>
  <nav class="modes" role="tablist"><button role="tab" aria-selected="true">Design</button>…<button role="tab">Release</button></nav>
  <div class="actions"><button class="ghost">Save</button><details class="menu"><summary>Export ▾</summary>…</details></div>
</header>
```
- `.appbar{display:grid;grid-template-columns:auto minmax(200px,1fr) auto auto;height:52px;flex-wrap:nowrap}`
- `.modes button[aria-selected=true]{box-shadow:inset 0 -2px var(--accent);color:var(--ink)}`
- Move presets and My designs into a **File ▾** menu (New from preset… / Open… / Import JSON… / Delete…). Delete asks for confirmation: *"Delete 'Toman 90 Rev C'? This can't be undone."*

**Spec strip** `.specstrip`: a 36 px band, IBM Plex Mono 12.5 px, chips `.chip.ok|.warn|.err`. Clicking the issue chip opens the Checks drawer and scrolls to it.

**Parameter rows**
- Use `<label for="p-L">Length</label><output>` with units in a fixed right-aligned column (`grid-template-columns:1fr 72px 28px`).
- Give each range `aria-labelledby` pointing to the label.
- Show the default value as a tick on the track.
- Double-click a label to reset it to the default.
- Rename the solver-style parameters:

| Current label | New label |
|---|---|
| Half width | Body width (full) |
| Fattest point | Max-thickness station, % of length |
| Bill root X/Z | Bill root position, from nose / from axis |
| Flank squareness | Cross-section: round ↔ flat-sided |

**KPI cards** `.kpi[data-kind=calc|est|model]`:
- Add a small tag in the top-right corner: *CALC* (teal) / *EST* (amber) / *MODEL* (grey).
- Add a target line: `Target 24–26 g · ✓`.
- Hook-up odds and Reel move to Simulate.

**Viewport**
- Collapse the toggles into a single `.viewbar` segmented control: `3D | Side | Top | Section` + `Layers ▾` (CG/CB, Grid, X-ray).
- Swim controls move to a bottom-centre transport bar `.transport` (▶ Swim · speed · Underwater · Fish · Strike).
- The strike card becomes a **bottom-left toast stack** (`max-width:260px; bottom:56px`), which collapses to one line after 3 s. Full detail moves to a "Session log" tab.

**Bottom panel**
- Make it resizable: `grid-template-rows:1fr var(--panel-h,270px)` with a 6 px drag handle `.splitter[role=separator][aria-orientation=horizontal]`, min 200 px, max 60 vh. The value persists in localStorage.
- In Analyse mode, set it to 50 %.

**Accessibility**
- `:focus-visible{outline:2px solid var(--teal);outline-offset:2px}`
- `.playbtn{background:#b4500f}` (about 5:1). On the warn status use ink text, not white.
- Add `aria-live="polite"` to `#stBig` and `#checks`, and `role="img" aria-label="3D model of …"` to the canvas.
- In SVG, use `font-family="IBM Plex Mono, ui-monospace, monospace"`.
- Keyboard: `[`/`]` step the focused parameter, Shift for ×10, and `Space` starts/stops the swim.

**Narrow (<1100 px)**
- Keep the viewport sticky at `40vh` on top.
- Put the parameters and results in a tab bar below (`Params | Results | Checks`).
- Collapse the header actions into an overflow ⋯ menu.

## 4. Prioritised changes

| # | Pri | Change |
|---|---|---|
| 1 | MUST | Mode switcher Design / Analyse / Simulate / Release; move fishing-game features out of Design |
| 2 | MUST | Release / Tech-pack view: SKU, Rev, status, BOM, tolerances, QC tests, PDF export |
| 3 | MUST | Spec strip with an always-visible issue count; Checks never below the fold |
| 4 | MUST | Single-row header with File and Export menus; confirm on delete; unsaved indicator |
| 5 | MUST | A11y basics: `for`/`aria-label` on all 85 inputs, `:focus-visible`, AA contrast on orange/amber, SVG font fallback |
| 6 | SHOULD | Accordion parameter groups with Basic/Advanced; rename solver-style labels; fixed unit column |
| 7 | SHOULD | KPI provenance tags (CALC/EST/MODEL) with target ranges |
| 8 | SHOULD | Resizable bottom panel; sim controls get full-width rows |
| 9 | SHOULD | Strike card becomes a non-blocking toast; transport bar for the swim |
| 10 | COULD | Narrow layout with sticky viewport and tabs; keyboard nudge shortcuts; undo/redo history |
