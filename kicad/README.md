# KiCad files

Footprint library + placement script + workflow to take the design into KiCad,
route it, and export Gerbers. This environment can't run KiCad, so these are the
inputs KiCad needs — the interactive routing and Gerber export happen in KiCad.

## Contents
| File | What it is |
|---|---|
| `watch.pretty/` | Footprint library (`.kicad_mod`) referenced by the netlists. |
| `gen_footprints.py` | Regenerates the library. |
| `place_dial.py` | pcbnew Python script: auto-places D1..D132 + posts from `dial_matrix.json`. |
| `dial_matrix.json` | LED positions/nets (copy of `pcb/dial/dial_matrix.json`). |

## ⚠️ VERIFY before fabrication
Footprint lands use IPC nominal geometry. **Confirm these against real datasheets
before ordering boards:**
- `QFN_IS31FL3743A` — **UQFN-40, 5×5mm, 0.4mm pitch, EP** — pin count + body
  VERIFIED from datasheet (Rev 00D; 18 CS, 18×11 = 198 LEDs). Land pattern is
  **IPC-7351 nominal** (pad 0.55×0.25mm, center 2.325mm from origin, EP 3.6mm,
  0.15mm pad clearance) — the standard derivation when the vendor land table
  isn't machine-readable. The datasheet's mechanical drawing couldn't be
  extracted here (PDF host blocked + image-based dimensions); **do a final eyeball
  of pad length and EP size against that drawing before ordering** — they're
  usually within 0.05mm of IPC nominal for a standard UQFN body.
- `QFN24_ATTINY3217` — WQFN-24 4×4 0.5mm; verify the recommended land + EP size.
- `Conn_4` / `Conn_16` — generic 0.5mm; replace with the chosen connector's land.
- `LED_0201` / `R_0402` / `C_0402` — IPC nominal; fine for most fabs.

## Add the library to KiCad
1. **Preferences → Manage Footprint Libraries → Project Specific Libraries → +**
2. Nickname `watch`, path `${KIPRJMOD}/kicad/watch.pretty`. The netlists reference
   footprints as `watch:LED_0201`, `watch:QFN_IS31FL3743A`, etc.

## Workflow — dial board
1. **Schematic** (`dial.kicad_sch`): place 132 LEDs (D1..D132), the driver (U2,
   `watch:QFN_IS31FL3743A`), R_EXT (R1), and the connector (J1). Assign each LED's
   anode→its SW net and cathode→its CS net per `../pcb/dial/dial_matrix.csv`
   (columns `SW_net`, `CS_net`). Add 3 mounting holes H1..H3 for the posts.
2. **Annotate** so refs match (D1..D132, U2, R1, J1, H1..H3).
3. **Assign footprints** (or rely on the `watch:` footprints set in symbol props).
4. Open Pcbnew → **File → Import → Netlist** → `../pcb/dial/dial_matrix.net`
   (or "Update PCB from Schematic" if you drew the schematic).
5. **Place:** open **Tools → Scripting Console**, edit `CENTER_MM` in
   `place_dial.py`, then:
   ```python
   exec(open('/full/path/to/kicad/place_dial.py').read())
   ```
   All 132 LEDs snap to their ring coordinates with tangential rotation; posts too.
6. **Route:** the IS31FL3743A matrix is SW lines (scan/source) × CS lines (sink).
   Route each SW as a bus to its LEDs' anodes, each CS to its column's cathodes.
   Far simpler than the old Charlieplex arc-bus; likely 2-layer.
7. **Edge cuts:** 37 mm circle centered on `CENTER_MM`. Add the 3 post holes.
8. **DRC**, then **File → Fabrication Outputs → Gerbers + drill**.

## Workflow — controller board
Same flow with `../pcb/controller/` parts: U1 ATtiny3217 (`watch:QFN24_ATTINY3217`),
U2 driver, U3 RV-3028, U4 LIS2DH12, U5 MCP73831, U6 LDO, R1 R_EXT, R2/R3 pull-ups,
C1..C8, J1 connector, BT1, charge pads. ~31 mm round edge cut. (No auto-placer
script for the controller — few enough parts to place by hand against
`controller_pcb.png` as a layout reference.)

## What this does NOT include
- `.kicad_pcb` / `.kicad_sch` project files (must be created in KiCad; hand-written
  ones tend to fail to open). These scripts/libraries feed those files.
- Symbol library — assign symbols from KiCad's built-ins (LED, R, C, generic IC,
  conn) and point each at the `watch:` footprint.
- DRC-clean routing / Gerbers — done interactively in KiCad.
