#!/usr/bin/env python3
"""
Generate a real-routing PCB-style render of the dial.
Routing strategy (4-layer board):
  - Each scan ROW = 12 LEDs sharing one HIGH net (anode). That HIGH net runs as
    an ARC BUS along the ring, on an inner layer, spanning just that row's arc.
  - Each LED's CATHODE (LOW net) drops as a short RADIAL SPOKE to a ring-shaped
    cathode collector. There are 13 cathode collector nets too (CP0..CP12), but
    a given pin acts as anode for one row and cathode for others -> the SAME 13
    physical nets serve both roles (that's Charlieplexing). We render:
      * top copper (red)  : LED pads + short cathode spokes + second-ring buses
      * inner layer (blue): minute/gmt/hour arc buses + cross-unders
  This is a representative routing showing feasibility + style, not a DRC-clean
  Gerber. Real routing happens in KiCad; this proves the topology fits.
"""
import json, math, cairosvg
d=json.load(open("dial_placement.json")); leds=d["leds"]; R=d["rings"]
S=22; CX=CY=460   # bigger canvas for trace detail
W=H=920
def P(x,y): return (CX+x*S, CY-y*S)

# group LEDs by scan row
rows={}
for L in leds: rows.setdefault(L["row"],[]).append(L)

TOP="#d11414"; TOPGLOW="#ff4d4d"; INNER="#2f6fd1"; INNER2="#39b0c4"
PAD="#d11ad1"; PADHOLE="#1a1a1a"; SILK="#39e0e0"; BG="#0b0d0a"

b=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica">']
b.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
# board outline + soldermask hint
b.append(f'<circle cx="{CX}" cy="{CY}" r="{18.5*S:.0f}" fill="#0e140d" stroke="#1c3a1c" stroke-width="2"/>')
b.append(f'<circle cx="{CX}" cy="{CY}" r="{R["rim"]*S+8:.0f}" fill="none" stroke="#9c8221" stroke-width="2" opacity="0.4"/>')

def arc_path(r, a0, a1, steps=24):
    pts=[]
    for i in range(steps+1):
        a=math.radians((a0+(a1-a0)*i/steps)-90)
        pts.append((CX+r*S*math.cos(a), CY-r*S*math.sin(a)))
    dd="M"+" L".join(f"{x:.1f},{y:.1f}" for x,y in pts)
    return dd

# ---- draw ARC BUSES per row (the HIGH/anode net for that row) ----
# choose layer color by region: second->top(red), minute->inner(blue),
# gmt->inner2(teal), hour->top(red)
def region_of_row(row):
    if row<5: return "second"
    if row<10: return "minute"
    if row<12: return "gmt"
    return "hour"

for row,Ls in sorted(rows.items()):
    Ls=sorted(Ls,key=lambda L:L["angle"])
    reg=region_of_row(row); r=Ls[0]["r"]
    a0=Ls[0]["angle"]; a1=Ls[-1]["angle"]
    # bus sits slightly inboard of the LED ring
    rb = r-0.7
    col = {"second":TOP,"minute":INNER,"gmt":INNER2,"hour":TOP}[reg]
    wdt = 3.2 if reg in ("second","hour") else 2.6
    b.append(f'<path d="{arc_path(rb,a0,a1)}" fill="none" stroke="{col}" stroke-width="{wdt}" stroke-linecap="round" opacity="0.95"/>')
    # short anode spoke from bus to each LED pad
    for L in Ls:
        a=math.radians(L["angle"]-90)
        x1=CX+rb*S*math.cos(a); y1=CY-rb*S*math.sin(a)
        x2,y2=P(L["x"],L["y"])
        b.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="1.6"/>')

# ---- cathode spokes: each LED's LOW net drops outward (top copper, red) ----
for L in leds:
    a=math.radians(L["angle"]-90)
    x1,y1=P(L["x"],L["y"])
    ro=L["r"]+1.0
    x2=CX+ro*S*math.cos(a); y2=CY-ro*S*math.sin(a)
    b.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{TOP}" stroke-width="1.3" opacity="0.85"/>')
    # tiny via at the outboard end (where cathode goes to inner collector)
    b.append(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="2.0" fill="{INNER}" stroke="#888" stroke-width="0.4"/>')

# ---- GMT fibers? no - electrical only. but show gmt cathode reach to rim pads ----
# ---- LED pads (0201, two pads) ----
for L in leds:
    px,py=P(L["x"],L["y"])
    ang=L["angle"]
    # draw as two small pads tangential
    dx=math.cos(math.radians(ang)); dy=math.sin(math.radians(ang))
    # tangential direction
    tx=-math.sin(math.radians(ang-90)); ty=math.cos(math.radians(ang-90))
    for s in (-1,1):
        cxp=px+tx*3.0*s; cyp=py+ty*3.0*s
        b.append(f'<rect x="{cxp-2.3:.1f}" y="{cyp-1.8:.1f}" width="4.6" height="3.6" rx="0.8" fill="{PAD}"/>')

# ---- registration posts (NPTH) ----
for p in d["posts"]:
    a=math.radians(p["angle"]-90)
    px=CX+p["r"]*S*math.cos(a); py=CY-p["r"]*S*math.sin(a)
    b.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="9" fill="{BG}" stroke="{SILK}" stroke-width="1.5"/>')
    b.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="#222" stroke="#777" stroke-width="0.8"/>')

# ---- center hub keepout + 13-pin fanout to connector (bottom) ----
b.append(f'<circle cx="{CX}" cy="{CY}" r="{2.2*S:.0f}" fill="none" stroke="{SILK}" stroke-width="1" stroke-dasharray="4 3" opacity="0.6"/>')

# legend
lg=[("top copper (anode buses + cathode spokes)",TOP,18),
    ("inner: minute bus",INNER,38),
    ("inner: GMT bus",INNER2,58),
    ("via to inner cathode collector",INNER,78),
    ("0201 LED pad",PAD,98),
    ("registration post (NPTH)",SILK,118)]
for txt,col,yy in lg:
    b.append(f'<rect x="14" y="{yy-9}" width="14" height="6" rx="1" fill="{col}"/>')
    b.append(f'<text x="34" y="{yy-3}" fill="#cfcfcf" font-size="12">{txt}</text>')
b.append(f'<text x="{CX}" y="{H-16}" fill="#9a9a9a" font-size="12" text-anchor="middle">Dial PCB routing (4-layer) — 13 arc buses + radial cathode spokes · representative topology</text>')
b.append('</svg>')
open("dial_pcb_route.svg","w").write("".join(b))
cairosvg.svg2png(url="dial_pcb_route.svg", write_to="dial_pcb_route.png", scale=1.6)
print("wrote dial_pcb_route.svg / .png")
