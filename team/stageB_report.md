# Stage B report: UX restructure (B1–B9)

**Files**
- Working file: `/home/claude/umpan-lab/index.html`. It is still one file, now 3078 lines.
- Untouched Stage A backup: `/home/claude/team/index_stageA.html` (md5 `798e7fea…`).
- Pieces used to build the new file: `team/stageB_head.html` (CSS and markup) and `team/stageB_controls.js` (controls block).

**What did not change**
- The whole pure model is byte-for-byte identical to Stage A. This is everything between `"use strict";` and the `UI: controls` marker: geometry, physics, the release model, the drawing, the documents, the schema and migration.
- `GROUPS` and `SIM_ITEMS` are unchanged. Internal keys, spec / sim / production sections and the SHA-256 are therefore identical.
- Labels and grouping now live in a separate UI-only layer (`LBL`, `UI_GROUPS`, `SIM_GROUPS`).

## What changed

**B1 App bar (52 px, one row at ≥ 1100 px)**
- Contents, left to right:
  - brand;
  - design name (labelled);
  - `Rev X`;
  - status badge;
  - live "● Unsaved changes" flag (spec + meta + costing + name, compared with the last load or save);
  - Design / Analyse / Simulate / Release `role=tablist`, with arrow / Home / End keys and roving tabindex;
  - Save;
  - **File ▾**;
  - **Export ▾**.
- **File ▾** contains the presets, a saved-design select with **Delete…**, and Import.
- **Export ▾** has two sections:
  - Prototype: STL pack, 1:1 SVG, JSON.
  - Factory: release zip, PDF, HTML, drawing SVG, BOM.
- Menus close on outside click, Escape or after an action. Arrow keys move through items.
- **Delete** opens an in-page `role=alertdialog`:
  - it reads "Delete 'X Rev A'? … can't be undone";
  - focus starts on Cancel, and focus is trapped inside;
  - Escape or a backdrop click cancels.
- Hash routing uses `#design`, `#analyse`, `#simulate` and `#release` (`history.replaceState`, `hashchange`). A deep link opens the right mode.

**B2 Spec strip (36 px, always visible)**
- Shows length · weight · class and net buoyancy · dive estimate · hooks · build mode.
- The issue chip shows ✓ / ! / ✕ with a count. Clicking it switches to Design, scrolls to Checks and focuses the heading. On narrow screens it opens the Checks tab.

**B3 Design**
- Accordion with one group open at a time: Shape, Bill, Hardware, Ballast, Material & production, Finish. Groups that have advanced inputs get an Advanced toggle.
- Advanced inputs: `se`, `tailR`, `billT`, `rootX`/`rootZ`, `infill`, `coat`, `draftDeg`, `flangeMm`, `pins`.
- Labels are renamed, and units sit in a fixed column. Two inputs are shown on a display scale while keeping the key:
  - **Body width (full)** shows 2 × `halfW`;
  - **Max-thickness station %** shows 100 × `fat`.
- Every row has `<label for>`; the range input uses `aria-labelledby`.
- A datalist tick marks the loaded value.
- Double-clicking a label resets it to the loaded value.
- `[` / `]` nudge the focused value, and Shift multiplies the step by 10.
- Identity, revision and colourway moved to the Release side panel. "Preview mold halves" stays in Material & production.

**B4 KPIs**
- Each KPI has a CALC / EST / MODEL tag and a legend.
- Targets are shown on:
  - stability (≥ 1.5 mm);
  - depth against the target depth (±0.6 m);
  - simulated max depth;
  - weight (QC ±0.3).
- Checks are sorted errors → warnings, and passed checks fold into a "N checks passed" disclosure. This keeps Checks above the fold.
- Hook-up odds (MODEL) and retrieve speed moved to Simulate.

**B5 Analyse**
- The side profile takes 50 % of the centre height.
- The right panel shows:
  - the mass table;
  - CG/CB coordinates, stability, rest attitude and float rate;
  - a hook-clearance table (reach, tie gap, hanger gap, hook-to-body ratio, each with a status);
  - the DFM list. It comes from `releaseModel` (always injection), is debounced, and is noted when the design is in Prototype mode.

**B6 Simulate**
- The left panel has full-width rows for Retrieve, Cast & water and Fishing conditions (line, water and clarity moved here).
- The bottom panel holds the dive chart and the result text.
- The transport bar sits bottom-centre: ▶ Swim / ■ Stop (`aria-pressed`), speed, Underwater, Fish, Strike.
- The HUD is at top-right.
- Strike events now appear as a toast stack at bottom-left. There are at most 3; each collapses to one line after 3 s and fades after 12 s. The full detail goes to the **Strike session** log, which shows hook-up odds with the reasons. The old blocking strike card is gone.
- The fish game is labelled MODEL and "not a catch-rate prediction".
- The swim camera framing now comes from the FOV and aspect, so the lure stays in the central ~58 % of the view.

**B7 Release**
- Left panel: identity and revision, with a lock banner when released; colourway.
- Main area: the Stage A release view at full width. It includes:
  - the export bar and SHA-256;
  - a large read-only drawing preview;
  - production figures;
  - sign-off and changelog;
  - DFM;
  - the BOM editor;
  - costing;
  - QC import.
- The ⤢ button was removed; the full-height layout replaces it.

**B8 Layout and accessibility**
- **Splitter.**
  - It is a `role=separator` that can be dragged or moved with the keyboard: ↑/↓ by 20 px, Shift for 60, Home / End.
  - Double-click resets it.
  - Height is stored per mode in `localStorage`, inside try/catch. Limits are 160 px to min(60 vh, centre − 140).
  - Analyse defaults to 50 %.
- **Accessibility.**
  - `:focus-visible` uses a teal outline.
  - The canvas has `role=img`, with a live `aria-label` (name, L, mass, buoyancy, bill angle).
  - `aria-live` is set on status, checks, toasts, session log, DFM, unsaved flag and toast.
  - All 268 inputs, plus the 151 Release-table inputs (BOM cells and sign-off fields now carry `aria-label`), have programmatic labels.
- **Contrast.**

  | Element | Change | Contrast |
  |---|---|---|
  | Orange buttons | `#b4500f` | 5.1:1 |
  | Amber "Near suspending" status | ink text on `#e0a526` | — |
  | Warning text | `#7f5300` | — |
  | OK green | `#26733f` | — |
  | `--mute` | `#5f6763` | — |
  | Tags and chips | — | pass AA (tested) |

- **Space.** Space toggles the swim, switching to Simulate if needed. It is ignored inside inputs, buttons, tabs, menus and modals.
- **Narrow layout (< 1100 px).**
  - The app bar has 2 rows; the modes get the second row.
  - The spec strip scrolls sideways, with the issue chip first.
  - The viewport is sticky at 40 vh.
  - A sticky tab bar below it switches between **Params | Results | Checks**.
  - In Release, the form and the document are stacked.

**B9 Render on demand**
- `renderer.setAnimationLoop` runs only while something changes, then stops itself after 20 idle frames. A frame is drawn when:
  - the lure is swimming;
  - `controls.update()` reports camera movement, which covers the OrbitControls damping tail;
  - the camera is easing back after a fish;
  - `requestRender()` was called by a rebuild, resize, mode switch, layer toggle or the 'change' / 'start' events.
- `window.__renders` counts frames for the tests.
- Camera presets 3D / Side / Top were added.
- `fitCamera` is now aspect-aware, so the tail hook is no longer cropped at 1280 px and 390 px. `resize()` runs before the first build.

## What was verified

Test files are in `/home/claude/tests`. Run each one with `python3 -I`.

**`stageB_ui.py`: 72 checks, ALL PASS, zero page errors.**
- App bar is one row at 1440 and 1280. Tablist roles and aria are correct.
- Spec strip content is right.
- All 4 presets load through File ▾ and the strip follows them.
- Every mode renders and sets its hash. A deep link to `#analyse` works.
- Analyse tables are filled, and the side profile is at least 35 % of the centre.
- Release form, BOM and preview are present.
- Accordion: exclusive opening, Advanced toggle, renamed labels.
- Full-width round trip: 24 mm → `halfW` 12. Double-click reset and `[`/`]` nudge work.
- Label audit, `:focus-visible`, canvas role, aria-live and tab keyboard all pass.
- Contrast passes on Swim, status (Floating and Sinking), tags and the issue chip.
- Issue chip → Checks works.
- **Render on demand:**
  - idle gives 0 renders and the loop is off;
  - a drag renders, and the damping tail keeps rendering after mouse-up (12 frames in 0.5 s);
  - the loop then stops, with 0 renders afterwards;
  - a parameter change triggers a render.
- **Swim.**
  - Space starts and stops the swim, and Space inside an input is ignored.
  - The HUD is filled.
  - **No overlap between the lure's projected bounding box and the transport bar, HUD or viewbar across 6 samples. The same holds at 1280.**
  - A forced strike shows a toast at bottom-left, off the lure; it collapses after 3 s. The session log records the strike with its odds.
  - Leaving Simulate stops the swim.
- **Splitter.**
  - Dragging gives 240 → 360 px, and the value is persisted.
  - Pressing ↓ subtracts 20 px.
  - The height is restored after a reload.
- **Delete modal.**
  - Focus starts on Cancel, and Escape keeps the design.
  - Confirming deletes it.
- **JSON import.**
  - Exported v2 keeps `halfW` 9.5 and `fat` 0.41.
  - Re-importing shows 19 mm / 41 % and gives an identical SHA-256.
  - A v1 file (wire in grams) migrates, and the UI shows the full width.
- **At 390×844:**
  - the viewport is 40 vh and stays sticky while scrolling;
  - there is no horizontal scroll, including in Release;
  - the Results and Checks tabs show the right content;
  - the transport bar fits.

**`stageB_release.py`: 58 checks, ALL PASS.**
- This is the Stage A end-to-end suite with its selectors ported to the new UI.
- It covers injection mode, the QC import (2 pass, 1 fail), the BOM override and every export.
- The zip has all 17 files. Trimesh finds `body_L`, `body_R`, `body_shell` and `bill` **watertight, with 0 bad edges and 0 degenerate faces**.
- The PDF is A3, 2 pages, vector-only.
- The hash matches Python and appears on every document.
- v1 validation, garbage rejection, build rollback and legacy localStorage all pass.
- On save, the changelog diff works and the unsaved flag clears.
- **Status locking:**
  - Released locks the spec inputs and the badge reads Released;
  - reopening goes to Rev B and the inputs unlock.
- B5, B6, B8 and B11 regressions pass.
- The Export ▾ BOM download works.
- Figures are identical to Stage A: 24.4 / 24.8 g, +6.7 / +6.3 g, and so on.

**`stageA_geometry.py`** still passes, including the 300-design fuzz. The pure section was compared byte-for-byte with `index_stageA.html`.

**Screenshots** were reviewed by eye. Clipping, overlap and wrapping found along the way were fixed:
- the Release pane was hijacking the side panel;
- the Release grid had a stray row;
- the swim camera covered the lure;
- the status badge overlapped Save at 390 px;
- KPI labels wrapped;
- the HUD wrapped;
- the tail hook was cropped.

| Width | Screenshots (`tests/stageB_*.png`) |
|---|---|
| 1440 | `design_1440`, `analyse_1440`, `simulate_1440`, `simulate_swim_1440`, `simulate_strike_1440`, `simulate_after_1440`, `release_1440`, `design_issues_1440`, `delete_confirm_1440` |
| 1280 | `design_1280`, `analyse_1280`, `release_1280`, `simulate_swim_1280`, `filemenu_1280`, `exportmenu_1280` |
| 390 | `design_390`, `design_390_scrolled`, `results_390`, `simulate_390`, `release_390` |

## Known gaps / notes

- **The old `check.py` and `uw.py` no longer run.** They use removed selectors: `#preset` select, `.tab[data-t=…]`, `#strikeCard`. `stageB_ui.py` and `stageB_release.py` supersede them, and `stageA_release.py` targets the Stage A file layout.
- **Not done:**
  - undo / redo;
  - the Analyse sensitivity readout ("+1 mm ballast Z → …");
  - a Section camera view;
  - the "⋯ overflow" menu at narrow widths. Save, File and Export fit at 390 px, so it was not needed.
- **Damping tail.** It lasts about 7 s under SwiftShader at about 22 fps, because OrbitControls' default `dampingFactor` 0.05 decays slowly. On real GPUs it is about 2–3 s. Rendering still stops afterwards.
- **Space on a focused button** activates that button, which is standard behaviour. Space toggles the swim only when focus is on the page or canvas.
- **Release view.** It still re-renders its HTML on every relevant edit, as in Stage A. Focus is kept for the field being typed in (`onchange`), but it is not restored after a re-render.
- **Strike timing.** The forced strike sequence takes about 2–3 s under SwiftShader, because the sim runs at 0.5× and dt is capped. The tests poll for it.
