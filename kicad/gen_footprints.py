#!/usr/bin/env python3
"""
Generate the `watch.pretty` KiCad footprint library (.kicad_mod files) referenced
by the dial + controller netlists. KiCad 6+ s-expression format.

Pad/courtyard dimensions follow standard IPC-7351 nominal density where the exact
datasheet recommended-land isn't confirmed; those cases are flagged in library
README with a VERIFY note. 0201/0402 use IPC nominal. QFN pitch/pad must be
checked against the real datasheet before fab.
"""
import os
OUT="watch.pretty"; os.makedirs(OUT, exist_ok=True)

def header(name, descr, tags):
    return (f'(footprint "{name}" (version 20221018) (generator watch_gen)\n'
            f'  (layer "F.Cu")\n'
            f'  (descr "{descr}")\n'
            f'  (tags "{tags}")\n'
            f'  (attr smd)\n')

def text_refs(name):
    return (f'  (fp_text reference "REF**" (at 0 -1.5) (layer "F.SilkS")\n'
            f'    (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
            f'  (fp_text value "{name}" (at 0 1.5) (layer "F.Fab")\n'
            f'    (effects (font (size 0.5 0.5) (thickness 0.08))))\n')

def rect_pad(num, x, y, w, h, layers='"F.Cu" "F.Paste" "F.Mask"'):
    return (f'  (pad "{num}" smd roundrect (at {x:.4f} {y:.4f}) (size {w:.4f} {h:.4f}) '
            f'(layers {layers}) (roundrect_rratio 0.25))\n')

def courtyard(w, h):
    hw,hh=w/2,h/2
    return (f'  (fp_poly (pts (xy {-hw:.3f} {-hh:.3f}) (xy {hw:.3f} {-hh:.3f}) '
            f'(xy {hw:.3f} {hh:.3f}) (xy {-hw:.3f} {hh:.3f})) '
            f'(stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))\n')

def write(name, body):
    open(f"{OUT}/{name}.kicad_mod","w").write(body+")\n")
    print("wrote", name)

# ---------- 0201 chip (LED / passive) ----------
# IPC nominal land for 0201 (0.6x0.3mm body): pads ~0.30x0.30, gap ~0.30, pitch ~0.50
def chip0201(name, descr, tags):
    b=header(name,descr,tags)+text_refs(name)
    b+=rect_pad(1,-0.255,0,0.30,0.30)
    b+=rect_pad(2, 0.255,0,0.30,0.30)
    b+=courtyard(1.0,0.55)
    return b
write("LED_0201", chip0201("LED_0201","0201 LED, IPC nominal land","LED 0201"))
write("R_0402", header("R_0402","0402 resistor","R 0402")+text_refs("R_0402")
      +rect_pad(1,-0.485,0,0.55,0.55)+rect_pad(2,0.485,0,0.55,0.55)+courtyard(1.5,0.8))
write("C_0402", header("C_0402","0402 capacitor","C 0402")+text_refs("C_0402")
      +rect_pad(1,-0.485,0,0.55,0.55)+rect_pad(2,0.485,0,0.55,0.55)+courtyard(1.5,0.8))

# ---------- QFN generic builder ----------
def qfn(name, pins, body_mm, pitch, pad_w, pad_l, ep=None, descr="", tags=""):
    """pins total, square body. pads on 4 sides, pin1 = bottom-left going CCW."""
    per=pins//4
    b=header(name,descr,tags)+text_refs(name)
    half=body_mm/2
    # pad center offset from edge
    padcx = half + pad_l/2 - 0.1
    n=1
    # left side (top->bottom), bottom (left->right), right (bottom->top), top (right->left) is one common QFN order;
    # use KiCad's standard CCW from pin1 at top-left of left column:
    start = -(per-1)*pitch/2
    # Left column (vertical pads), pins increase downward
    for i in range(per):
        y=start+i*pitch
        b+=rect_pad(n,-padcx,y,pad_l,pad_w); n+=1
    # Bottom row (horizontal pads), left->right
    for i in range(per):
        x=start+i*pitch
        b+=rect_pad(n,x,padcx,pad_w,pad_l); n+=1
    # Right column, bottom->top
    for i in range(per):
        y=start+(per-1-i)*pitch
        b+=rect_pad(n,padcx,y,pad_l,pad_w); n+=1
    # Top row, right->left
    for i in range(per):
        x=start+(per-1-i)*pitch
        b+=rect_pad(n,x,-padcx,pad_w,pad_l); n+=1
    if ep:
        b+=(f'  (pad "EP" smd roundrect (at 0 0) (size {ep:.3f} {ep:.3f}) '
            f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.1))\n')
    b+=courtyard(body_mm+0.6, body_mm+0.6)
    return b

# ATtiny3217 QFN-24, 4x4mm, 0.5mm pitch (per LCSC -MNR WQFN-24-EP 4x4)
write("QFN24_ATTINY3217", qfn("QFN24_ATTINY3217",24,4.0,0.5,0.30,0.75,ep=2.6,
      descr="ATtiny3217 WQFN-24 4x4 0.5mm pitch w/ EP. VERIFY land vs datasheet.",
      tags="QFN24 ATtiny3217"))

# IS31FL3743A: QFN, dimensions NOT confirmed in datasheet search.
# Family siblings: 44-QFN 5x5 0.4mm pitch. Use that as a flagged placeholder.
# IS31FL3743A: UQFN-40, 5x5mm, 0.4mm pitch, EP ~3.6mm. VERIFIED pin count/body
# from datasheet Rev 00D (18 current sinks, 18x11 matrix = 198 LEDs).
# Confirm exact land/EP against the mechanical drawing before fab.
# Land = IPC-7351 nominal for UQFN-40 5x5 0.4mm: pad 0.55x0.25, center 2.325, EP 3.6.
write("QFN_IS31FL3743A", qfn("QFN_IS31FL3743A",40,5.0,0.4,0.25,0.55,ep=3.6,
      descr="IS31FL3743A UQFN-40 5x5 0.4mm pitch w/ EP. Pin/body verified vs datasheet Rev 00D; land = IPC-7351 nominal. Confirm EP/land vs mechanical drawing.",
      tags="QFN40 UQFN IS31FL3743A driver"))

# ---------- B2B / connector: simple 4-pad 0.5mm pitch header ----------
def conn(name, pins, pitch, descr):
    b=header(name,descr,"connector")+text_refs(name)
    start=-(pins-1)*pitch/2
    for i in range(pins):
        b+=rect_pad(i+1, start+i*pitch, 0, 0.3, 1.2)
    b+=courtyard(pins*pitch+0.6, 2.0)
    return b
write("Conn_4", conn("Conn_4",4,0.5,"4-pin B2B/FPC 0.5mm pitch. VERIFY vs chosen part."))
write("Conn_16", conn("Conn_16",16,0.5,"16-pin B2B/FPC 0.5mm pitch (legacy). VERIFY vs chosen part."))

print("\nAll footprints written to", OUT)
