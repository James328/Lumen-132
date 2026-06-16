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

| #                                           | Designator(s) | Component                       | MPN                        | Package  | Qty | Unit $                   | Line $  | Distributor  | Source / notes                                                                                                 |
|---------------------------------------------|---------------|---------------------------------|----------------------------|----------|-----|--------------------------|---------|--------------|----------------------------------------------------------------------------------------------------------------|
| DIAL BOARD + MASK                           |               |                                 |                            |          |     |                          |         |              |                                                                                                                |
| 1                                           | D1–D132       | LED 0201 (per-ring colors)      | Kingbright APG0201xxC-TT   | 0201     | 132 | $0.210                   | $27.720 | DigiKey/LCSC | 132 = 60 sec + 60 min + 12 hour (GMT dropped). ~$0.21@100. Wired in the driver's matrix grid, not Charlieplex. |
| 2                                           | J1(dial)      | Board-to-board hdr              | matrix rows/cols + V + GND | —        | 1   | $0.400                   | $0.400  | LCSC         | Carries the driver matrix lines to the dial.                                                                   |
| 3                                           | —             | Dial PCB 2-layer 37mm           | custom                     | —        | 1   | $5.000                   | $5.000  | JLCPCB       | Driver matrix grid is simpler than 4-layer Charlieplex; may drop to 2-layer. ENIG, black mask.                 |
| 4                                           | —             | Mask / light-guide plate        | custom                     | —        | 1   | $5.500                   | $5.500  | JLCPCB/3D    | Branded HUME mask: flush square second guides + raised hour/minute pipes. Evolved from alignment plate.        |
| CONTROLLER BOARD (ATtiny3217 + IS31FL3743A) |               |                                 |                            |          |     |                          |         |              |                                                                                                                |
| 6                                           | U1            | MCU ATtiny3217                  | ATTINY3217-MFR             | QFN-24   | 1   | $1.050                   | $1.050  | LCSC         | ~$1.04 LCSC (-MFR). 22 I/O, ~7 used. Replaces ATmega328.                                                       |
| 7                                           | U2            | LED matrix driver               | IS31FL3743A                | QFN      | 1   | $1.000                   | $1.000  | LCSC/DigiKey | 198 LEDs, 8-bit hw PWM each, I2C. ~$1 @10k. Chain up to 4 for ~400+ LEDs.                                      |
| 8                                           | U3            | RTC                             | RV-3028-C7                 | SON-8    | 1   | $1.490                   | $1.490  | LCSC         | 45nA timebase, I2C.                                                                                            |
| 9                                           | U4            | Accelerometer                   | LIS2DH12TR                 | LGA-12   | 1   | $0.450                   | $0.450  | LCSC         | Wrist-raise wake, I2C+INT.                                                                                     |
| 10                                          | U5            | LiPo charger                    | MCP73831T-2ACI/OT          | SOT-23-5 | 1   | $0.760                   | $0.760  | DigiKey      |                                                                                                                |
| 11                                          | U6            | LDO 3.3V low-Iq                 | TPS7A2033PDBVR             | SOT-23-5 | 1   | $0.330                   | $0.330  | DigiKey      | ~25nA Iq.                                                                                                      |
| 12                                          | R1            | R_EXT (sets array current)      | generic 0402 1%            | 0402     | 1   | $0.010                   | $0.010  | LCSC         | ONE resistor sets full-scale LED current. Replaces the 13 Charlieplex resistors.                               |
| 13                                          | R2–R3         | I2C pull-ups 4.7k               | generic 0402               | 0402     | 2   | $0.005                   | $0.010  | LCSC         |                                                                                                                |
| 14                                          | C1–C8         | Decoupling 0.1µF/1µF            | generic 0402               | 0402     | 8   | $0.010                   | $0.080  | LCSC         | MCU/driver/RTC/accel/LDO.                                                                                      |
| 15                                          | BT1           | Protected LiPo cell             | 110mAh pouch w/ PCM        | —        | 1   | $4.500                   | $4.500  | varies       | Mandatory protection (skin contact). Sets case depth.                                                          |
| 16                                          | Q1            | Reverse-prot / dead-pad FET     | generic SOT                | SOT-23   | 1   | $0.100                   | $0.100  | LCSC         | Charge-path protection + dead pads until charger detected.                                                     |
| 17                                          | J1(ctrl)      | B2B hdr (mate)                  | generic                    | —        | 1   | $0.400                   | $0.400  | LCSC         | Mates dial J1.                                                                                                 |
| 18                                          | —             | Controller PCB 2-layer ~31mm    | custom                     | —        | 1   | $2.000                   | $2.000  | JLCPCB       | Sparse 2-layer.                                                                                                |
| CASE / OPTICS / MECHANICAL                  |               |                                 |                            |          |     |                          |         |              |                                                                                                                |
| 20                                          | —             | Seiko-mod case 39.5mm           | off-the-shelf              | —        | 1   | $35.000                  | $35.000 | watch-mod    | Sub-style; price varies.                                                                                       |
| 21                                          | —             | Sapphire crystal (domed)        | off-the-shelf              | —        | 1   | $12.000                  | $12.000 | watch-mod    |                                                                                                                |
| 22                                          | —             | Bezel / chapter ring            | off-the-shelf              | —        | 1   | $6.000                   | $6.000  | watch-mod    | Plain bezel now (GMT 24h scale dropped).                                                                       |
| 23                                          | —             | PMMA fiber / acrylic pipe stock | bulk                       | —        | 1   | $6.000                   | $6.000  | varies       | For 132 guides + raised hand pipes.                                                                            |
| 24                                          | —             | Magnetic charging puck          | DIY/off-the-shelf          | —        | 1   | $6.000                   | $6.000  | varies       | Pogo pins + magnet; external.                                                                                  |
| 25                                          | —             | Strap                           | off-the-shelf              | —        | 1   | $15.000                  | $15.000 | varies       |                                                                                                                |
|                                             |               |                                 |                            |          |     | Dial+mask subtotal       | $38.62  |              |                                                                                                                |
|                                             |               |                                 |                            |          |     | Controller subtotal      | $12.18  |              |                                                                                                                |
|                                             |               |                                 |                            |          |     | Case/optics subtotal     | $80.00  |              |                                                                                                                |
|                                             |               |                                 |                            |          |     | PER-WATCH TOTAL (1 unit) | $130.80 |              |                                                                                                                |
