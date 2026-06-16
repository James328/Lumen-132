# Bill of Materials (rev 2 — ATtiny3217 + IS31FL3743A)

`LED_Watch_BOM.xlsx` — sourced parts list with live formulas (edit blue qty/price
cells; totals recalculate). Three sections: dial+mask / controller / case+optics.

Per-watch estimate (single quantity, June 2026 pricing): **~$131**
- Dial board + mask ~$39 (132 × 0201 LEDs dominate)
- Controller board ~$12 (ATtiny3217 + IS31FL3743A driver)
- Case / optics / mechanical ~$80

## What changed from rev 1
- **Brain:** ATmega328P → **ATtiny3217** (~$1.04 LCSC).
- **LED driving:** added **IS31FL3743A** matrix driver (~$1) with hardware PWM;
  **removed the 13 Charlieplex series resistors** (driver uses one R_EXT).
- **GMT dropped:** 156 → **132 LEDs** (60 sec + 60 min + 12 hour).
- Dial may drop from 4-layer to 2-layer (driver matrix grid is simpler to route).
- Net effect: ~$9 cheaper per watch *and* better brightness control + LED scaling.

## Scaling LEDs
Add IS31FL3743A driver(s) (~$1 each) on the same I²C bus + more 0201 LEDs.
One driver = 198 LEDs; up to 4 chain to ~400+. No extra MCU pins needed.

Prices are estimates — verify live before ordering. Excludes shipping, assembly,
tariffs, and PCB NRE (amortize over a batch).
