#!/usr/bin/env python3
"""
Regenerate dial wiring for the IS31FL3743A matrix driver (replaces Charlieplex).
Driver topology: an 18x11 matrix = up to 198 single-color LEDs.
  - 11 "SW" lines (current sources / scan rows, SW1..SW11)
  - 18 "CS" lines (current sinks / columns, CS1..CS18)
Each LED sits at one (SW, CS) intersection -> unique address. We have 132 LEDs
(60 sec + 60 min + 12 hour), so we use 132 of the 198 intersections.

Assignment strategy (simple, regular, fab-friendly):
  walk all 132 LEDs in ring order and assign them sequentially to (SW,CS) cells
  filling row by row: SW1 takes CS1..CS18 (18 LEDs), SW2 next 18, etc.
  -> 132 / 18 = 7 full rows (126) + 6 in the 8th row -> uses SW1..SW8.
LED positions are UNCHANGED from the Charlieplex design; only the wiring differs.
"""
import json, math, csv

R = {"second":16.5, "minute":14.5, "hour":2.5, "rim":18.0}
COUNT = {"second":60, "minute":60, "hour":12}  # 132, GMT dropped
POSTS = [(0,16.0),(130,16.0),(240,16.0)]
SW_LINES=11; CS_LINES=18; MAXLED=SW_LINES*CS_LINES  # 198

leds=[]
def addring(region,count,radius):
    for i in range(count):
        ang=i*(360.0/count); a=math.radians(ang-90)
        leds.append(dict(idx=len(leds),region=region,pos=i,angle=round(ang,2),
                         r=radius,x=round(radius*math.cos(a),3),y=round(radius*math.sin(a),3)))
addring("second",60,R["second"])
addring("minute",60,R["minute"])
addring("hour",12,R["hour"])
assert len(leds)==132

# sequential matrix assignment
for n,L in enumerate(leds):
    sw=n//CS_LINES        # 0-based scan row
    cs=n%CS_LINES         # 0-based column
    L["sw"]=sw+1          # SW1..
    L["cs"]=cs+1          # CS1..
    L["driver"]=1         # single driver (132 <= 198)
    L["net_sw"]=f"SW{sw+1}"
    L["net_cs"]=f"CS{cs+1}"

rows_used=max(L["sw"] for L in leds)
print(f"LEDs: {len(leds)}  matrix: {SW_LINES}x{CS_LINES}={MAXLED} max  used SW rows: {rows_used}")
print(f"spare intersections on 1 driver: {MAXLED-len(leds)}")
# verify unique cells
cells={(L['sw'],L['cs']) for L in leds}
assert len(cells)==132, "duplicate matrix cell!"
print("all 132 (SW,CS) cells unique — valid matrix assignment")

out=dict(units="mm",origin="dial_center",driver="IS31FL3743A",
         matrix=dict(sw=SW_LINES,cs=CS_LINES,max_leds=MAXLED),
         rings=R,counts=COUNT,posts=[dict(angle=p[0],r=p[1]) for p in POSTS],
         note="LED positions identical to Charlieplex design; wiring is driver matrix grid.",
         leds=leds)
json.dump(out,open("repo/pcb/dial/dial_matrix.json","w"),indent=1)
with open("repo/pcb/dial/dial_matrix.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["ref","region","pos","x_mm","y_mm","angle_deg","driver","SW_net","CS_net"])
    for L in leds:
        w.writerow([f"D{L['idx']+1}",L["region"],L["pos"],L["x"],L["y"],L["angle"],L["driver"],L["net_sw"],L["net_cs"]])
print("wrote dial_matrix.json / dial_matrix.csv")

# how many drivers if scaled
print("\nScaling: if LED count grows ->", )
for target in (132,198,264,396):
    nd=(target+MAXLED-1)//MAXLED
    print(f"  {target} LEDs -> {nd} driver(s)")
