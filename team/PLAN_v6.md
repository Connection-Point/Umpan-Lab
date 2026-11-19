# Umpan Lab v6 — SE-Asian lure families + design-from-scratch
Baseline: /home/claude/umpan-lab/index.html (v5, published). Backup before work: /home/claude/team/index_v5.html.
Sandbox constraints unchanged (CDN scripts only from cdnjs/jsdelivr/unpkg; downloads via save(); no alert/confirm/prompt; localStorage may throw; font fallbacks).
Original work only: no brand names / trademarked product names (e.g. say "rotating-tail propbait", not a brand), no copying of commercial lure designs.

## 1. Lure-family framework
A `FAMILIES` registry; P.family selects it. Each family declares: label, description, typical target species, which body generator & components are enabled, default params, which param groups/fields show, physics model, swim/sim behaviour, retrieve styles offered, production process (hard 2-half injection, wood/hand-made, soft PVC/rotocast, lead-cast head + wire form, stamped metal), BOM template. Existing crankbait becomes family `crank` with zero behaviour change (v5 files load as crank).

Families (defaults are typical SEA sizes; designer can change everything):
| key | name | body | key components | buoyancy | typical (L, weight) |
|---|---|---|---|---|---|
| crank | Crankbait | lofted | bill | float | 50–110 mm, 6–30 g |
| pencil | Topwater pencil / stickbait (walk-the-dog) | lofted slim, no bill | nose line-tie, tail-weight | float tail-down 25–60° | 90–140 mm, 12–30 g |
| popper | Popper / chugger | lofted + cupped face | cup (diameter, depth), optional tail feather/skirt | float tail-down | 55–90 mm, 8–20 g |
| propbait | Propbait (front/rear props) | lofted | 1–2 propellers on shaft (dia, blade count 2–4, pitch) | float level | 70–110 mm, 10–25 g |
| jumpfrog | Jump frog (SEA hard/wood frog for haruan/toman) | short flattened lofted body | spinner blade (front or rear), silicone legs, upturned double hook (weedless) | float | 35–60 mm, 8–20 g |
| softfrog | Soft hollow frog | soft PVC hollow body | double hook along back, silicone skirt legs, weight in belly | float | 50–65 mm, 10–20 g |
| spinnerbait | Spinnerbait | lead head on hook | R-bend wire arm, 1–2 blades (Colorado/Indiana/Willow, sizes #2–#6), skirt, optional trailer hook | sinks | 1/4–1 oz |
| buzzbait | Buzzbait | lead head on hook | wire arm, 2- or 3-wing buzz blade (dia), optional clacker, skirt | sinks; planes at speed | 1/4–5/8 oz |
| lipless | Lipless vibration | lofted, flat sides | top line-tie, rattle | sinks | 55–80 mm, 10–28 g |
| spoon | Casting / weedless spoon | stamped plate with cup | split ring, treble or single + weed guard | sinks | 7–28 g |
| custom | **Custom — from scratch** | spline body (see §2) | ANY component can be added | computed | — |

Target species select (affects strike model + default sizes): Toman (giant snakehead), Haruan (snakehead), Sebarau (hampala barb), Peacock bass, Siakap (barramundi). Each: typical weight range, mouth size → min hook gap, preferred zone (surface/mid/bottom), aggressiveness, preferred speed band.

## 2. Design from scratch (custom family, also "Convert to editable" from any lofted family)
- Profile editor panel (SVG, mm grid): side view with TOP and BELLY curves, top view with HALF-WIDTH curve. Draggable control points (Catmull-Rom/monotone cubic), add point (double-click on curve), delete (select + Del / button), numeric table of points (station x mm, value mm), symmetric about centreline, snap to 0.5 mm, undo/redo for the editor (at least 30 steps).
- Cross-section control: superellipse exponent per station (simple: nose / mid / tail values), and nose face type: round / flat / cupped (cup depth) / chisel.
- Start options: blank ellipsoid of chosen L/H/W; import side-profile image as a tracing underlay (file input → image under the grid, opacity + scale handles); convert current preset.
- Components palette (add/remove, each with position/params): bill, cup face, front/rear prop, spinner blade on clevis, wire arm + blades, buzz blade, legs/skirt, rattle chamber, line-tie (position), hook hangers (N = 0–4, each x/z, type treble/single/double/upturned double, size), weed guard, tail feather/skirt, ballast(s) (multiple, position, material).
- Body generator: radii(t) reads splines when present; all existing analysis (mass, CG/CB, buoyancy, halves/shell, drawing) must work for any spline body.

## 3. Physics per family (rule-of-thumb, tagged EST/MODEL like v5)
- Generic: rest attitude angle on the surface / in water from CG vs CB (equilibrium pitch), float/sink rate (existing).
- pencil: walk-the-dog glide width estimate from length, CG aft position and rest angle; recommended twitch cadence.
- popper: spit/pop strength index from cup area & depth; chug sound index.
- propbait: prop rpm ≈ v / (pitch·k); minimum speed to spin; noise index.
- jumpfrog/softfrog: planing/walk index, weedless index (hook exposure), blade rpm.
- spinnerbait: blade rpm by type (Colorado ~ slow/thump, Willow ~ fast/flash), lift vs speed → running depth after countdown at given speed; sink rate at rest; helicopter fall.
- buzzbait: minimum planing speed (lift ≥ weight), blade rpm, surface noise index.
- lipless: sink rate, vibration frequency vs speed, countdown depth.
- spoon: sink rate, wobble/flutter freq, flutter-on-the-fall.
Dive/retrieve sim gets new styles: walk-the-dog (twitch cadence), pop & pause, slow roll, burn, countdown + steady, yo-yo/lift & drop, and keeps reel gear ratio/cranking pace. Topwater families stay at the surface (depth 0, animate surface interaction).

## 4. Swim / underwater animation per family
Walk-the-dog zigzag with glide; popper pop + splash/bubble burst; props spinning with bubble trail; jump frog legs pulsing + blade spin + V-wake; spinnerbait blades rotating around the clevis + skirt pulsing; buzzbait blade spinning at surface with bubble trail; lipless high-frequency shimmy; spoon flutter. Surface strikes (topwater blow-up splash) for surface families. The procedural fish adapts to target species (proportions/colour), still original procedural geometry.

## 5. Production per family
Process + BOM templates: hard bodies → 2-half injection (existing halves/shell) or wood; soft frog → PVC rotocast / injection soft body (export body STL + wall thickness note, no halves); spinnerbait/buzzbait → lead/tungsten head cast (export head STL + 2-half head mold blocks if feasible, else head STL only) + wire form drawing (bend points table, wire Ø) + blade spec table (type, size, finish, clevis); spoon → flat blank outline DXF-like SVG + cup press depth; props/blades as parts with size/thickness. Tech pack, BOM, costing, QC criteria, packaging adapt per family (e.g. spinnerbait QC: blade spins ≥ x rpm at 0.5 m/s, tracks true; buzzbait planes ≤ x m/s; topwater: rest angle ±5°, walk test).

## 6. UX
- Family picker: a "New lure" gallery (cards with small original line icons + one-line description + typical species) shown from File ▾ → New…, and family select in Design mode. "Start from scratch" card first.
- Design mode shows only groups relevant to the family; Components panel for custom.
- Spec strip & KPIs adapt (e.g. topwater shows rest angle instead of dive depth).

## Stages
A: framework + families geometry/physics + spline editor + presets (dev #1).
B: per-family swim animation + sims + production/BOM/tech pack + family gallery UX (dev #2).
C: acceptance — CEO (production), UX designer, and a Malaysian pro angler / custom lure maker (realism of families, presets, actions); fixes; publish.
