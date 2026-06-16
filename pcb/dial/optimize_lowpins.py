#!/usr/bin/env python3
"""
Refine the Charlieplex LOW-pin assignment to minimize cathode spoke length,
while preserving the hard constraint: all 156 ordered (hi,lo) pairs unique.

Constraint structure:
 - 13 scan rows. Row r uses HIGH pin = r. Its 12 LEDs must use 12 distinct LOW
   pins drawn from the 12 pins != r. So within a row it's a PERMUTATION of the
   other 12 pins onto the 12 LED positions.
 - Global uniqueness: pair (hi,lo)=(r, p) appears once. Since hi=r is fixed per
   row and each row uses each lo!=r exactly once, ANY per-row permutation keeps
   global uniqueness automatically. So we can optimize each row independently!
 - "Spoke length" proxy: a LOW pin p is physically the bus/pin associated with
   scan row p (its arc sits at some mean angle). Routing the cathode toward the
   pin whose arc is ANGULARLY NEAREST the LED minimizes spoke travel.

So: for each row, solve an assignment problem (Hungarian) matching its 12 LEDs
to the 12 available LOW pins, cost = angular distance between the LED and the
target pin's arc center. Minimizes total cathode routing.
"""
import json, math
import numpy as np
from scipy.optimize import linear_sum_assignment

d=json.load(open("dial_placement.json")); leds=d["leds"]
N=13

# mean angle of each scan row's arc (the "location" of pin p as a bus)
row_leds={}
for L in leds: row_leds.setdefault(L["row"],[]).append(L)
pin_angle={}
for r,Ls in row_leds.items():
    angs=[math.radians(L["angle"]) for L in Ls]
    # circular mean
    s=sum(math.sin(a) for a in angs); c=sum(math.cos(a) for a in angs)
    pin_angle[r]=math.atan2(s,c)

def ang_dist(a,b):
    d=abs(a-b)%(2*math.pi); return min(d,2*math.pi-d)

# optimize each row
total_before=0; total_after=0
for r,Ls in sorted(row_leds.items()):
    Ls=sorted(Ls,key=lambda L:L["pos"])
    avail=[p for p in range(N) if p!=r]   # 12 candidate LOW pins
    # cost matrix 12x12: led i -> pin avail[j]
    C=np.zeros((12,12))
    for i,L in enumerate(Ls):
        la=math.radians(L["angle"])
        for j,p in enumerate(avail):
            C[i,j]=ang_dist(la, pin_angle[p])
    # baseline cost = current assignment
    for i,L in enumerate(Ls):
        total_before+=ang_dist(math.radians(L["angle"]), pin_angle[L["lo"]])
    ri,ci=linear_sum_assignment(C)
    for i,j in zip(ri,ci):
        Ls[i]["lo"]=avail[j]
        Ls[i]["net_cathode"]=f"CP{avail[j]}"
        total_after+=C[i,j]

# re-verify uniqueness
pairs=set()
for L in leds:
    k=(L["hi"],L["lo"])
    assert k not in pairs, f"dup {k}"; pairs.add(k)
assert len(pairs)==156
print(f"uniqueness preserved: {len(pairs)} pairs")
print(f"total angular spoke cost: before {total_before:.2f} rad -> after {total_after:.2f} rad")
print(f"reduction: {(1-total_after/total_before)*100:.0f}%")

# write optimized json/csv
json.dump(d, open("dial_placement.json","w"), indent=1)
import csv
with open("dial_placement.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["ref","region","pos","x_mm","y_mm","angle_deg","net_anode","net_cathode","scan_row"])
    for L in leds:
        w.writerow([f"D{L['idx']+1}",L["region"],L["pos"],L["x"],L["y"],L["angle"],L["net_anode"],L["net_cathode"],L["row"]])
print("rewrote dial_placement.json / .csv with optimized LOW pins")
