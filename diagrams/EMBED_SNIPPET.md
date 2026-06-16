# Diagrams — HUME Lumen 132

All diagrams render in both light and dark variants. To make GitHub show the
right one automatically (light on light theme, dark on dark), use the `<picture>`
trick:

```markdown
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="diagrams/01_controller_schematic_dark.png">
  <img alt="Controller schematic" src="diagrams/01_controller_schematic_light.png">
</picture>
```

Or just reference the light file directly if your README renders on one theme.

## The diagrams
1. `01_controller_schematic` — ATtiny3217 + IS31FL3743A driver, everything on I²C
2. `02_firmware_states` — sleep / display / set-time flow (driver frame model)
3. `03_dial_geometry` — ring radii, counts, three-zone layout, registration posts
4. `04_full_stack` — cross-section, layer thicknesses

All reflect the current driver-based, GMT-dropped, HUME-mask design.
