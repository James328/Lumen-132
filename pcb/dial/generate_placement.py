#!/usr/bin/env python3
"""
Dial PCB placement + Charlieplex netlist generator.
Outputs: dial_placement.json, dial_placement.csv, dial_kicad_gen.py, dial_layout.svg
Coordinate origin = dial center. Units = mm. KiCad uses +Y down; we keep math in
standard +Y up and flip on export.
"""
import json, math, csv

# ---------------- geometry ----------------
DIAL_D   = 37.0
N_PINS   = 13
# ring radii (mm)
R = {"second":16.5, "minute":14.5, "gmt_led":13.0, "hour":2.5, "rim":18.0}
COUNT = {"second":60, "minute":60, "gmt":24, "hour":12}   # = 156

# registration posts (asymmetric)
POSTS = [(0,16.0),(130,16.0),(240,16.0)]

# ---------------- Charlieplex assignment ----------------
# 13 scan rows of 12 LEDs. Each row shares one HIGH pin = one physical arc.
# Row -> region mapping (5 sec arcs, 5 min arcs, 2 gmt arcs, 1 hour):
#   rows 0..4  second  (each = 12 consecutive second positions = 72 deg arc)
#   rows 5..9  minute
#   rows 10..11 gmt
#   row  12    hour
# Within a row, the 12 LEDs use the row's HIGH pin and 12 distinct LOW pins.
# LOW pins are the other 12 pins (all pins except the HIGH one) -> 13x12=156, each
# (hi,lo) pair unique. We assign lo pins in order skipping hi. This guarantees the
# Charlieplex uniqueness (every ordered pin pair used exactly once).

def low_pins_for(hi):
    return [p for p in range(N_PINS) if p != hi]   # 12 pins

leds = []   # each: idx, region, pos_in_region, angle_deg, r, x, y, hi, lo
def add_region(region, count, radius, row_start, rows):
    per_row = count // rows
    assert per_row == 12, f"{region}: expected 12/row got {per_row}"
    for rrow in range(rows):
        hi = row_start + rrow
        lows = low_pins_for(hi)
        for j in range(per_row):
            posidx = rrow*per_row + j
            # angle: distribute around the circle by global position in region
            ang = posidx * (360.0/count)
            a = math.radians(ang - 90)   # 12 o'clock = up
            x = radius*math.cos(a); y = radius*math.sin(a)
            leds.append(dict(idx=len(leds), region=region, pos=posidx,
                             angle=round(ang,2), r=radius,
                             x=round(x,3), y=round(y,3),
                             hi=hi, lo=lows[j], row=hi))

# GMT positions are nudged to gap centers; recompute angle for gmt specially.
def gap_center(a):
    n = round((a-3)/6); return (3+6*n)%360

add_region("second", 60, R["second"], 0, 5)
add_region("minute", 60, R["minute"], 5, 5)
# gmt: 24 leds, 2 rows of 12, at nudged angles, radius = gmt_led
for rrow in range(2):
    hi = 10+rrow; lows = low_pins_for(hi)
    for j in range(12):
        posidx = rrow*12+j
        ideal = posidx*(360.0/24)
        ang = gap_center(ideal)
        a = math.radians(ang-90)
        x=R["gmt_led"]*math.cos(a); y=R["gmt_led"]*math.sin(a)
        leds.append(dict(idx=len(leds),region="gmt",pos=posidx,angle=round(ang,2),
                         r=R["gmt_led"],x=round(x,3),y=round(y,3),hi=hi,lo=lows[j],row=hi))
# hour: 12 leds, 1 row, at hub radius
hi=12; lows=low_pins_for(hi)
for j in range(12):
    ang=j*30.0; a=math.radians(ang-90)
    x=R["hour"]*math.cos(a); y=R["hour"]*math.sin(a)
    leds.append(dict(idx=len(leds),region="hour",pos=j,angle=round(ang,2),
                     r=R["hour"],x=round(x,3),y=round(y,3),hi=hi,lo=lows[j],row=hi))

# ---------------- verify Charlieplex uniqueness ----------------
pairs = set()
for L in leds:
    key=(L["hi"],L["lo"])
    assert key not in pairs, f"dup pair {key}"
    pairs.add(key)
assert len(leds)==156, len(leds)
print(f"LEDs placed: {len(leds)}  unique (hi,lo) pairs: {len(pairs)}")
# every ordered pair of distinct pins should be used once
assert len(pairs)==N_PINS*(N_PINS-1)==156
print("Charlieplex netlist verified: all 156 ordered pin-pairs unique.")

# net names: CP0..CP12. Each LED connects anode->CPhi via that LED, cathode->CPlo.
# (antiparallel partner is the LED with hi/lo swapped.)
for L in leds:
    L["net_anode"]=f"CP{L['hi']}"
    L["net_cathode"]=f"CP{L['lo']}"

# ---------------- write JSON ----------------
out = dict(units="mm", origin="dial_center", dial_diameter=DIAL_D,
          pins=N_PINS, net_prefix="CP", rings=R, counts=COUNT,
          posts=[dict(angle=p[0],r=p[1]) for p in POSTS],
          leds=leds)
json.dump(out, open("dial_placement.json","w"), indent=1)
print("wrote dial_placement.json")

# ---------------- write CSV ----------------
with open("dial_placement.csv","w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["ref","region","pos","x_mm","y_mm","angle_deg","net_anode","net_cathode","scan_row"])
    for L in leds:
        ref=f"D{L['idx']+1}"
        w.writerow([ref,L["region"],L["pos"],L["x"],L["y"],L["angle"],
                    L["net_anode"],L["net_cathode"],L["row"]])
print("wrote dial_placement.csv")

# quick stats
from collections import Counter
print("per-region:", dict(Counter(L["region"] for L in leds)))
