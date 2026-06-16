# Dial wiring — IS31FL3743A matrix grid (CURRENT)

This is the **current** dial wiring, regenerated from the old Charlieplex scheme
for the IS31FL3743A matrix driver. The LED **positions are identical** to the
Charlieplex design — only the wiring/netlist changed.

| File | What it is |
|---|---|
| `generate_matrix.py` | Source of truth. Places 132 LEDs (60 sec + 60 min + 12 hour, GMT dropped), assigns each to a unique (SW, CS) matrix cell, verifies uniqueness. |
| `dial_matrix.json` | Machine-readable: every LED's xy, angle, driver #, SW/CS net. |
| `dial_matrix.csv` | Flat table (ref, region, pos, x, y, angle, driver, SW_net, CS_net). |
| `generate_matrix_netlist.py` | Builds the KiCad netlist + flat connection CSV. |
| `dial_matrix.net` | KiCad netlist (import via "Update PCB from netlist"). |
| `connections_matrix.csv` | Flat net/ref/pin table. |
| `dial_matrix_layout.svg/.png` | Visual check, colored by SW scan line. |

## Matrix topology
- IS31FL3743A = **18 CS (sink/column) × 11 SW (source/row) = 198 LEDs max**.
- 132 LEDs use 8 of 11 SW lines; **66 spare** intersections on one driver.
- Each LED: anode → its SW line, cathode → its CS line. The driver does the
  multiplexing + 8-bit PWM; the MCU just writes brightness over I²C.

## Scaling
Add IS31FL3743A drivers on the I²C bus (different ADDR strap):
| Target LEDs | Drivers |
|---|---|
| ≤198 | 1 |
| ≤396 | 2 |
| ≤594 | 3 |
| ≤792 | 4 (bus max) |

## Workflow into KiCad
1. Schematic: 132 LEDs + driver U2 + R_EXT + connector. Label each LED's
   anode/cathode to its SW/CS net per `dial_matrix.csv`.
2. Import `dial_matrix.net` to a blank board.
3. Place LEDs at the `dial_matrix.json` coordinates (the old `dial_kicad_gen.py`
   placement approach still works — positions are unchanged).
4. Route: SW lines as the scan buses, CS lines as the columns. Far simpler than
   the Charlieplex arc-bus scheme; likely 2-layer.

## Superseded files (Charlieplex, stale)
`dial_placement.*`, `dial.net`, `connections.csv`, `dial_pcb_route.*`,
`optimize_lowpins.py`, `generate_netlist.py`, `netlist_assignment.txt`,
`generate_routing.py` — all Charlieplex-era. Kept for history. See `README.md`
banner. Use the `*_matrix.*` files instead.
