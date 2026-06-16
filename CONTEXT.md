# HUME Lumen 132 — design handoff

# CONTEXT — resuming the LED watch design

Paste this whole file to an AI assistant to continue the project with full context. It captures every locked decision, the reasoning behind each, the open questions, and the next steps.

---

## What this project is

A homebrew analog-style wristwatch with **no mechanical hands and no display module**. Time is shown by ~156 individually-addressable LEDs in concentric rings on a PCB dial, with light carried to the dial face by optical fibers and light pipes. It targets an off-the-shelf **39.5 mm Seiko-mod case**.

I'm the builder. I want to keep iterating on the design and eventually fabricate it. Please continue as a collaborator: reason through tradeoffs, do the math, flag risks honestly, and ask me before making decisions that change the architecture.

---

## ⚠️ ARCHITECTURE UPDATE (latest) — read this first

The electronics were **reworked** after the original Charlieplex design. Current architecture:

- **Brain: ATtiny3217** (not ATmega328). 22 I/O, modern AVR core, lower power, cheaper. Only ~7 pins used now.
- **LED driving: dedicated matrix driver IC (Lumissil IS31FL3743A)** over I²C — NOT MCU-bit-banged Charlieplex anymore. The driver does all multiplexing + true 8-bit hardware PWM per LED.
- **Scaling: add driver chips on the same I²C bus.** One IS31FL3743A = 198 LEDs (up to 4 chained on one bus → ~400+). Chosen specifically because the builder may want many more LEDs. Alternatives: IS31FL3741 (351 LEDs), IS31FL3758 (360 LEDs, 2025, ext PMOS for thermal).
- **Driver package VERIFIED:** IS31FL3743A is **UQFN-40, 5×5mm** (datasheet Rev 00D), 18 current sinks, 18×11 matrix = 198 LEDs. KiCad footprint corrected from an earlier 44-pin placeholder to the real 40-pin part.
- **Consequence — seconds sweep & hand fades are now trivial:** true hardware PWM, just write brightness bytes. No firmware time-slicing.
- **Consequence — current limiting:** one external R_EXT sets full-scale current for the whole array. No 13 per-pin resistors.
- **STALE because of this change:** the dial wiring/netlist files in `pcb/dial/` (Charlieplex arc-bus scheme, `dial.net`, `connections.csv`, `dial_pcb_route.*`). LED **positions** are unchanged; the **wiring topology** must be regenerated to the driver's row×column matrix grid (e.g. 39×9). This dial-rewiring pass is the main outstanding engineering task.
- Original Charlieplex reasoning is kept below for history, but the driver-based architecture supersedes it.

**Design/visual direction also evolved** (see dedicated section lower down): branded **HUME** dial used as a physical **mask** over the LED PCB; GMT complication **dropped**; seconds shown as flush square light-guide segments; hours/minutes as flush flat-ridge light channels in a three-zone radial layout (hour stubs at center, branding gap, minute pipes outer band, + an outer hour-marker ring); all positions physically present, only the active ones lit. See the FINAL three-zone layout note below.

---

## Hard requirements (from me, the builder)

- **No ESP.** AVR or simpler. (We chose ATmega328P. Pure-analog was rejected as impractical.)
- 100+ LEDs on the dial, Charlieplexed.
- Four rings: GMT, hour, minute, second — thin rings, maximize dial space.
- Light pipes / fibers to blend the light into "hands" on the dial face (not bare LEDs).
- Dial made from PCB.
- 39.5 mm case.

(Solar power was an early goal but was **dropped** — see decisions.)

---

## Locked decisions (with reasoning)

1. **Controller: ATmega328P (QFN32), internal oscillator.** Enough I/O; the RTC keeps time so no crystal is needed, freeing the XTAL pins for the LED matrix.

2. **LED addressing: Charlieplexing, 13 pins → 156 LEDs** (13×12 = 156, zero waste).

3. **Resolution:** 60 second, 60 minute, 24 GMT, 12 hour LEDs. (Doubling seconds to 120 was considered and rejected — pushes to 16 pins, worse duty cycle, and seconds resolution is already 1/sec. Smooth motion is done in firmware instead.)

4. **Display mode: ON-DEMAND, not always-on.** This is the pivotal decision. Always-on drains a wrist battery in ~10 h. On-demand (raise-to-wrist via accelerometer, or button) → months of runtime. Solar was dropped because on-demand made it unnecessary and the transparent-FPC/solar stack was impractical at this size.

5. **Seconds motion: brightness-interpolated sweep** across the 60 second LEDs (PWM by time-allocation within the Charlieplex scan). Smooth glide, zero extra LEDs/pins. Optionally minutes too; hours/minutes can stay stepped for a "premium" mechanical feel.

6. **Optics:** fiber per LED position + light-pipe "hands." Each fiber is an isolated channel (crosstalk-resistant).

7. **GMT readout: piped radially OUT to the rim bezel**, no inner GMT ring. The 24 GMT LEDs sit ~13 mm radius; their light threads through the gaps between minute/second LEDs to glow at the rim against a 24-hour bezel. Lane angles are **nudged** to the nearest gap center (±3°) because 24-vs-60 beat against each other; the bezel scale is printed to match.

8. **Two-tier hands:**
   - **Minute** = 60 long thin light-pipes, center-to-ring, **flush** with the alignment-plate top (~1.3 mm). Lit one at a time.
   - **Hour** = 12 short fat pipes, **raised ~0.5 mm** above the minute plane (~1.8 mm).
   - Long-thin-low = minute, short-fat-high = hour. Reads like real stacked hands.
   - The flush minute pipe is embedded in the **alignment plate** (chosen over milling the PCB). It sits above the GMT fibers (own thin layer, +0.3 mm) so they don't collide.

9. **Timekeeping: RV-3028 RTC** (~45 nA, ±1–2 ppm) over I²C. AVR deep-sleeps and reads it on wake.

10. **Wake: LIS2DH12 accelerometer** (wrist-raise, ~10 µA) + crown button, each on an external interrupt.

11. **Charging: magnetic pogo-pin caseback contacts.** Gold sealed feedthroughs; pads dead until a charger is detected (Hall/voltage sense + ideal-diode FET); protected LiPo cell required (worn against skin).

12. **Dial: 37 mm 4-layer rigid PCB**, dark soldermask face (no texture), 0201 LEDs, reflow-assembled. Three asymmetric registration posts (0°/130°/240°) lock the alignment plate.

---

## Key numbers

- Charlieplex: 13 pins, 156 LEDs, 13 scan rows of 12, ~70 Hz frame, 1/13 duty.
- Ring radii: second 16.5 mm, minute 14.5 mm, GMT LED ~13 mm (piped to ~18 mm rim), hour at hub ~2.5 mm.
- Pitch: second 1.73 mm, minute 1.52 mm (binding constraints for 0201).
- GMT clearance after nudging: 3° from nearest LED (~0.76 mm).
- Tolerance budget for fiber-on-LED alignment: ~±0.15 mm against a 0.3 mm LED.
- Pin budget: 13 matrix + 2 I²C + 2 INT + 1 charger-status = 18 used, ~8 spare on QFN32.
- Current limiting: one ~47 Ω resistor per pin (13 total), not per LED.
- Power: on-demand avg ~29–66 µA → ~1–5 months depending on cell and glances/day. Accelerometer (~10 µA) is the resting limiter. Glance drive can be ~30 mA.
- Stack height ≈ 9–10 mm; LiPo (3.2 mm) is the bottleneck.

---

## HUME dial design direction (evolved during design)

- **Branding:** dial is branded **HUME** (Swiss-grotesk wordmark, Helvetica/Arial, ~0.2em tracking) with a **crest** = open-top shield whose two walls + a crossbar form an "H" (Concept C, locked). Exact crest SVG path: `M18 14 V58 C18 84 34 100 50 108 C66 100 82 84 82 58 V14` plus a crossbar rect `x18 y40 w64 h9` (in a 0–100 viewBox). Co-brand slot above 6 o'clock holds the **ANTHROP\C** logo (provided as a white PNG). Tagline: MASTER CHRONOMETER.
- **GMT complication DROPPED.** Now 3 indicators: second (60), minute (60), hour (12) = **132 LEDs** (was 156). This also makes 12×11=132 a clean Charlieplex fit historically, and sits comfortably under one IS31FL3743A (198).
- **Dial-as-mask architecture:** the branded HUME dial is a physical **mask/overlay** on top of the LED PCB. Three layers: (1) LED PCB bottom, (2) opaque branded mask middle with flush window-guides for seconds, (3) raised light-pipe hands on top for minute/hour (depth/dimension). Seconds = flush square near-touching light-guide segments set into the mask face (cohesive segmented ring), bright electric blue (`0x33ccff`). Minute = long thin raised pipe; hour = short fat raised pipe (higher). All 60 minute + 12 hour + 60 second positions are PHYSICAL pipes always present (faint clear acrylic when unlit); only the active one of each is lit.
- **Flush seconds achieved via filled-window light guides** (single rigid board kept). Flex PCB at the mask surface is the documented fallback only if bench tests show piped light isn't bright enough.
- **Dial size stays 37 mm** (from 39.5 mm case − rehaut). Claude Design doc assumed 38 mm; 37 governs.
- Live interactive render: `renders/watch_hume_3d_mask.html` (3-layer, exploded/assembled toggle, pan-tilt-zoom, illuminated). Earlier renders (`dial_pcb_3d_v2`, `watch_demo_animated`) predate the mask architecture.

- **Hand support (decided):** the raised minute/hour hands are **molded raised channels**, not free-floating pipes. Each is a half-round light guide formed as part of the mask (or a clear layer bonded to it): flat base flush to the mask face, rounded top proud of it, supported along its whole length. This fixes the structural problem that a free-standing pipe can't support itself. Seconds stay flush in the mask plane; hands are supported ridges rising from it. Render `watch_hume_3d_mask.html` reflects this (assembled = channels seated on mask, exploded = lifted to show layers).
- **Hand mounting (decided):** channels are seated **flush along their WHOLE length** on the mask, not point-mounted. Center-only mounting was considered and rejected — a thin acrylic guide cantilevered from the center would flex/sag/drift out of LED alignment. The protrusion is the cross-section standing proud, NOT an unsupported projecting length. Channels are simple flat ridges (modeled as flat bars in the render) lying flat on the dial. **No center hub** (an earlier "shared hub boss" idea was dropped — the hour hands now branch straight from the center).
- **Hand translucency (decided):** lit channels glow but stay **translucent** (not opaque blockers) so the printed branding (HUME wordmark, ANTHROP\C logo, indices) reads THROUGH a hand that crosses it. Legibility bar: branding must read clearly at rest (faint unlit channels ~0.06 opacity); a lit hand briefly crossing it is acceptable. Achieved physically by a frosted/edge-lit guide material (diffuse glow, stays see-through), not a polished solid core — note this for the optics prototype.
- **FINAL three-zone layout (current render):** the indicators form three concentric zones radiating from center, with branding in a clear gap between them:
  - **Hour hands:** 12 short amber stubs branching from the **center** outward (~0.8 -> 4.2mm). No center hub dot.
  - **Branding gap** (~5-9.5mm): crest, HUME wordmark, ANTHROP\C logo, MASTER CHRONOMETER - clear of both hands and minute pipes.
  - **Minute pipes:** 60 thin green channels in the **outer band** (~10 -> 15mm). Deliberately thin (0.4mm wide) so the ring is uncrowded.
  - **Outer hour markers:** ring of 12 amber ticks just inside the minute band (~9.4mm); the active one lights with the current hour, so the eye connects the inner hour stub + outer marker into one long hour-hand reference (solves the short-hour-hand problem without a pipe crossing the branding).
  - **Seconds:** flush square segments at the rim (~16.5mm), electric blue 0x33ccff.
  - All positions are physical pieces, faint when unlit (~0.09 opacity); only the active hour/minute/second lights. Geometry is flat-box ridges lying flat on the dial (an earlier half-cylinder approach made hands render standing up - fixed).
  - This SUPERSEDES the earlier 'outer-band start ~8.2mm / hour ~5mm / shared hub boss' notes above.
---

## Open questions / not yet decided

- **Dial rewiring to driver matrix (BIGGEST open task):** regenerate `pcb/dial/` from Charlieplex arc-bus to the IS31FL3743A row×column matrix grid. LED positions unchanged; wiring + netlist change.
- **Exact MPNs:** 0201 LED color mix, protected LiPo that fits depth, B2B connector, the specific driver package, ATtiny3217 package.
- **One vs multiple drivers:** start with one IS31FL3743A (198 ≥ 132). Decide trigger for chaining a 2nd (if LED count grows past ~198).
- **Mask fabrication:** the branded mask + flush second-guides + raised hand-pipes is the precision part (evolved from the old "alignment plate"). Needs prototyping; registration to the LED PCB still via the 3 asymmetric posts.
- **Fiber/pipe brightness gradient:** long minute pipe lit from one end dims along its length — bench test; driver per-LED PWM can compensate by driving that LED brighter.
- **Single-position pipe prototype:** de-risk one minute pipe + one second guide before committing all 132.
- **Case finish:** forged-carbon Sub-style explored in 3D but procedural texture looked poor; aesthetic still open. Real carbon photo as texture is the fix at render time.
- **Firmware:** rewrite for the driver — I²C frame writes to IS31FL3743A, not Charlieplex bit-bang. Much simpler (sleep → read RTC → write brightness frame → sleep).

---

## Suggested next steps (pick up here)

1. **Regenerate dial wiring** for the IS31FL3743A matrix grid (replaces the stale Charlieplex `pcb/dial/` files). This is where the "more LEDs" payoff lives.
2. Rewrite the firmware skeleton for the driver (I²C frame model) — far simpler than the Charlieplex scan loop.
3. Update the BOM: swap ATmega328→ATtiny3217, drop 13 resistors + add driver IC(s) + R_EXT, drop GMT LEDs (156→132). Re-price.
4. Single-position pipe/guide prototype to de-risk the optics + mask.
5. Start KiCad: controller board (ATtiny + driver + RTC + accel + power) and the matrix-grid dial.

---

## Style of collaboration I want

- Do the math (don't hand-wave power, geometry, or tolerances).
- Flag risks and tradeoffs honestly, even when I'm enthusiastic about something.
- Ask before changing architecture-level decisions.
- Diagrams/renders welcome. Note that interactive 3D renders can't be exported as flat images without a screenshot.
