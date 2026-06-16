# Firmware

`watch_firmware.c` — **current** skeleton for the ATtiny3217 + IS31FL3743A driver
architecture. Structure/reference, not a drop-in binary (TWI driver, RTC reads,
and exact driver register addresses are stubbed/simplified).

## Flow (much simpler than the old Charlieplex version)
1. Power-down sleep (~1µA). RTC keeps time. Wake on accel (wrist-raise) or button.
2. Display session (~3s): enable driver, read RTC, then ~60fps:
   `render()` writes a brightness byte per LED into a 132-byte framebuffer,
   then `drv_write_frame()` pushes it to the driver over I²C.
3. Seconds sweep = cross-fade of two brightness bytes — the driver does the PWM
   in hardware. No scan loop, no tristate timing.
4. Session ends → clear frame, driver back to SDB shutdown, MCU sleeps.

## Why it shrank
The IS31FL3743A handles multiplexing + per-LED 8-bit PWM. The MCU's only job is
to compute brightness values and write them. The old Charlieplex firmware had to
bit-bang 13 pins in a constant scan loop with ghost-prevention and time-sliced
PWM — all of that is gone.

## Scaling
More LEDs = larger framebuffer + more driver chips on the same I²C bus. `render()`
and the `led_to_reg[]` map grow; the control structure is unchanged.

## Stale
`watch_firmware_charlieplex_STALE.c` — the old ATmega328P Charlieplex skeleton,
kept for reference. Do not build against it.

## Build
Modern ATtiny toolchain (megaTinyCore-style), `-mmcu=attiny3217`, program via UPDI.
The `led_to_reg[]` map comes from `pcb/dial/dial_matrix.csv` ((SW,CS) → register).
