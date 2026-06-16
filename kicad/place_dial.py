#!/usr/bin/env python3
"""
KiCad pcbnew placement script for the DIAL board.
Run from KiCad's Scripting Console (Tools > Scripting Console) with the dial
.kicad_pcb open AND after importing dial_matrix.net (so footprints D1..D132 exist).

  - reads dial_matrix.json (place it next to this script, or edit JSON_PATH)
  - positions each LED footprint Dn at its (x,y) with tangential rotation
  - positions 3 registration posts H1..H3

Our coords: origin = dial center, +Y up, mm. KiCad: +Y DOWN, nanometers.
Set CENTER_MM to where the dial center sits on your KiCad sheet.
"""
import json, os, math

JSON_PATH = os.path.join(os.path.dirname(__file__), "dial_matrix.json")
CENTER_MM = (150.0, 100.0)   # dial center on the KiCad sheet — edit to taste

def run():
    import pcbnew
    board = pcbnew.GetBoard()
    data = json.load(open(JSON_PATH))
    cx, cy = CENTER_MM
    nm = lambda mm: int(mm * 1e6)
    placed = 0
    for L in data["leds"]:
        ref = f"D{L['idx']+1}"
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            continue
        x = cx + L["x"]            # +X same
        y = cy - L["y"]            # flip Y (our +Y up -> KiCad +Y down)
        fp.SetPosition(pcbnew.VECTOR2I(nm(x), nm(y)))
        fp.SetOrientationDegrees((-L["angle"]) % 360)   # tangent to ring
        placed += 1
    # registration posts
    for i, p in enumerate(data.get("posts", []), start=1):
        fp = board.FindFootprintByReference(f"H{i}")
        if fp is None:
            continue
        a = math.radians(p["angle"] - 90)
        x = cx + p["r"]*math.cos(a)
        y = cy - p["r"]*math.sin(a)
        fp.SetPosition(pcbnew.VECTOR2I(nm(x), nm(y)))
    pcbnew.Refresh()
    print(f"placed {placed} / {len(data['leds'])} LEDs + {len(data.get('posts',[]))} posts")

if __name__ == "__main__":
    try:
        import pcbnew  # noqa
        run()
    except ImportError:
        print("Run from KiCad's Scripting Console with the dial board open.")
        print(f"Reads {os.path.basename(JSON_PATH)}; positions D1..D132 + H1..H3.")
