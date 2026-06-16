#!/usr/bin/env python3
"""Controller board placement + routed render, ATtiny3217 + IS31FL3743A driver.
Round ~31mm board, 2-layer, classic PCB-render style (red=top, blue=bottom)."""
import math, cairosvg

W=H=820; CX=CY=410; S=11
BG="#0b0d0a"; TOP="#d11414"; BOT="#2f6fd1"; PAD="#d11ad1"; SILK="#39e0e0"
def P(x,y): return (CX+x*S, CY-y*S)

parts=[
  dict(ref="U1",x=-4,y=2,w=5,h=5,pins=24,lab="ATtiny3217"),       # QFN-24 MCU
  dict(ref="U2",x=6,y=2,w=6,h=6,pins=44,lab="IS31FL3743A"),        # driver, bigger QFN
  dict(ref="U3",x=-9,y=8,w=3,h=3,pins=8,lab="RV-3028"),
  dict(ref="U4",x=-11,y=2,w=2,h=2,pins=12,lab="LIS2DH12"),
  dict(ref="U5",x=-10,y=-5,w=3,h=2.5,pins=5,lab="MCP73831"),
  dict(ref="U6",x=-6,y=-7,w=2,h=1.6,pins=5,lab="LDO"),
  dict(ref="R1",x=2,y=-3,w=1.4,h=0.7,pins=2,lab="R_EXT"),
  dict(ref="J1",x=0,y=-11,w=10,h=2.2,pins=4,lab="B2B → dial"),
  dict(ref="BT1",x=2,y=10,w=13,h=3,pins=2,lab="LiPo +/−"),
  dict(ref="CP+",x=12,y=-6,w=2.4,h=2.4,pins=1,lab="V+"),
  dict(ref="CP-",x=12,y=-9,w=2.4,h=2.4,pins=1,lab="GND"),
]

b=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica">']
b.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
b.append(f'<circle cx="{CX}" cy="{CY}" r="{15.5*S}" fill="#0e140d" stroke="#1c3a1c" stroke-width="2"/>')

def seg(x1,y1,x2,y2,col,wd=2.0,op=0.9):
    a=P(x1,y1); c=P(x2,y2)
    return f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{c[0]:.1f}" y2="{c[1]:.1f}" stroke="{col}" stroke-width="{wd}" stroke-linecap="round" opacity="{op}"/>'

# I2C bus (blue, bottom): MCU <-> driver, RTC, accel  (the key story: 2 wires carry everything)
b.append(seg(-1.5,2,3,2,BOT,2.6))                 # MCU -> driver SDA/SCL
b.append(seg(-1.5,1,3,1,BOT,2.6))
b.append(seg(-6.5,2,-9,7,BOT,2.0)); b.append(seg(-6.5,1,-9.5,2.5,BOT,2.0))  # to RTC/accel
b.append(seg(-9,7,-9,7,BOT,2.0))
# driver matrix lines (red, top) fanning to the B2B connector — many short traces
for i in range(11):
    sx=4.0+ i*0.55
    b.append(seg(sx,-1, -4+ i*0.7, -10, TOP, 1.4, 0.8))  # SW/CS lines down to J1
# R_EXT to driver (red)
b.append(seg(2,-3,4.5,0,TOP,2.0))
# power: LDO->MCU+driver (red), charger->battery, charge pads
b.append(seg(-6,-7,-2,1.5,TOP,2.4,0.7))
b.append(seg(-10,-5,2,9.5,TOP,2.4,0.5))
b.append(seg(12,-6,-8.5,-4.5,TOP,2.0,0.6))
b.append(seg(2,10,9,3,BOT,2.4,0.5))

def chip(p):
    out=[]; x,y=P(p["x"],p["y"]); ww=p["w"]*S; hh=p["h"]*S
    out.append(f'<rect x="{x-ww/2:.1f}" y="{y-hh/2:.1f}" width="{ww:.1f}" height="{hh:.1f}" rx="2" fill="none" stroke="{SILK}" stroke-width="1.4"/>')
    n=p["pins"]
    if p["ref"].startswith("U") and n>=5:
        for s in range(4):
            cnt=n//4+(1 if s<n%4 else 0)
            for k in range(cnt):
                tt=(k+1)/(cnt+1)
                if s==0: px=x-ww/2+ww*tt; py=y+hh/2
                elif s==1: px=x+ww/2; py=y-hh/2+hh*tt
                elif s==2: px=x-ww/2+ww*tt; py=y-hh/2
                else: px=x-ww/2; py=y-hh/2+hh*tt
                out.append(f'<rect x="{px-1.8:.1f}" y="{py-1.8:.1f}" width="3.6" height="3.6" rx="0.8" fill="{PAD}"/>')
    elif p["ref"].startswith("R"):
        out.append(f'<rect x="{x-ww/2-2:.1f}" y="{y-2:.1f}" width="4" height="4" rx="1" fill="{PAD}"/>')
        out.append(f'<rect x="{x+ww/2-2:.1f}" y="{y-2:.1f}" width="4" height="4" rx="1" fill="{PAD}"/>')
    elif p["ref"]=="J1":
        for k in range(4):
            px=x-ww/2+ww*(k+0.5)/4
            out.append(f'<rect x="{px-2.4:.1f}" y="{y-2.4:.1f}" width="4.8" height="4.8" rx="0.8" fill="{PAD}"/>')
    elif p["ref"]=="BT1":
        out.append(f'<circle cx="{x-ww/3:.1f}" cy="{y:.1f}" r="4" fill="{PAD}"/>')
        out.append(f'<circle cx="{x+ww/3:.1f}" cy="{y:.1f}" r="4" fill="{PAD}"/>')
    elif p["ref"].startswith("CP"):
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{ww/2:.1f}" fill="#caa72a" stroke="#eedd88" stroke-width="1"/>')
    if p["lab"]:
        out.append(f'<text x="{x:.1f}" y="{y-hh/2-4:.1f}" fill="{SILK}" font-size="11" text-anchor="middle">{p["ref"]} {p["lab"]}</text>')
    return "".join(out)

for p in parts: b.append(chip(p))
for deg in (45,135,225,315):
    a=math.radians(deg); px=CX+14.5*S*math.cos(a); py=CY-14.5*S*math.sin(a)
    b.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="{BG}" stroke="{SILK}" stroke-width="1.2"/>')
    b.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="#222" stroke="#777" stroke-width="0.6"/>')

b.append(f'<rect x="14" y="12" width="14" height="6" fill="{TOP}"/><text x="34" y="18" fill="#ccc" font-size="12">top copper (matrix + power)</text>')
b.append(f'<rect x="14" y="30" width="14" height="6" fill="{BOT}"/><text x="34" y="36" fill="#ccc" font-size="12">bottom copper (I²C bus)</text>')
b.append(f'<text x="{CX}" y="{H-14}" fill="#9a9a9a" font-size="12" text-anchor="middle">Controller ~31mm — ATtiny3217 + IS31FL3743A driver · matrix on I²C · representative 2-layer routing</text>')
b.append('</svg>')
open("repo/pcb/controller/controller_pcb.svg","w").write("".join(b))
cairosvg.svg2png(url="repo/pcb/controller/controller_pcb.svg",write_to="repo/pcb/controller/controller_pcb.png",scale=1.6)
print("wrote controller_pcb.svg/.png (ATtiny + driver)")
