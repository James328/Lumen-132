#!/usr/bin/env python3
"""
KiCad placement generator for the dial board.
Run inside KiCad's Python (Tools > Scripting Console) with the .kicad_pcb open,
OR use as reference for the footprint/net values.

It reads dial_placement.json (place it next to this script) and:
  - moves each LED footprint Dn to its computed (x,y) and rotation
  - (net assignment is done in the schematic; this positions parts)

KiCad uses +Y DOWN and nanometers internally; we convert from our +Y-up mm.
Origin here = KiCad page point set as the dial center (edit CENTER below).
"""
import json, os, math

CENTER_MM = (150.0, 100.0)   # where the dial center sits on the KiCad sheet (edit me)

def run_in_kicad():
    import pcbnew
    board = pcbnew.GetBoard()
    data = json.load(open(os.path.join(os.path.dirname(__file__), "dial_placement.json")))
    cx, cy = CENTER_MM
    def to_nm(mm): return int(mm * 1e6)
    placed = 0
    for L in data["leds"]:
        ref = f"D{L['idx']+1}"
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            continue
        # our +Y up -> KiCad +Y down: flip y sign
        x = cx + L["x"]; y = cy - L["y"]
        fp.SetPosition(pcbnew.VECTOR2I(to_nm(x), to_nm(y)))
        # orient LED tangent to the ring: angle = position angle
        # KiCad rotation is degrees, CCW positive; tangent = ring angle
        fp.SetOrientationDegrees((-L["angle"]) % 360)
        placed += 1
    pcbnew.Refresh()
    print(f"placed {placed} / {len(data['leds'])} LED footprints")

    # registration posts as NPTH or mounting holes (refs H1..H3)
    for i, p in enumerate(data["posts"], start=1):
        ref = f"H{i}"
        fp = board.FindFootprintByReference(ref)
        if fp is None: continue
        a = math.radians(p["angle"] - 90)
        x = cx + p["r"]*math.cos(a); y = cy - p["r"]*math.sin(a)
        fp.SetPosition(pcbnew.VECTOR2I(to_nm(x), to_nm(y)))
    pcbnew.Refresh()

if __name__ == "__main__":
    try:
        import pcbnew  # noqa
        run_in_kicad()
    except ImportError:
        print("Not in KiCad. Run from KiCad's Scripting Console with the board open.")
        print("This script reads dial_placement.json and positions footprints D1..D156, H1..H3.")
