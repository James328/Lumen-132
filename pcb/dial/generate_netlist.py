#!/usr/bin/env python3
"""
Emit an importable netlist for the dial. Two outputs:
 1) dial.net  -- KiCad legacy netlist format (importable via Pcbnew 'Update from netlist'
                 / or 'Import netlist'). Lists components + per-net node lists.
 2) connections.csv -- flat (net, ref, pin) table for any other tool.
LED model: 2-pin SMD LED. pin 1 = anode (-> net_anode), pin 2 = cathode (-> net_cathode).
Also includes 13 series resistors R-CP0..R-CP12 (one per pin) and the B2B connector J1.
"""
import json, csv, datetime
d=json.load(open("dial_placement.json")); leds=d["leds"]
N=13

# Build net -> [(ref,pin),...]
nets={f"CP{i}":[] for i in range(N)}
# resistor side nets: MCU pin -> resistor -> CPi bus. We'll model bus net = CPi,
# and a "drive" net MCUi on the other side of each resistor going to the connector.
for i in range(N):
    nets[f"CP{i}"].append((f"R{i+1}","2"))     # resistor low side ties to bus CPi
    nets.setdefault(f"MCU{i}",[]).append((f"R{i+1}","1"))  # resistor high side
    nets[f"MCU{i}"].append(("J1", str(i+1)))    # to connector pin

for L in leds:
    ref=f"D{L['idx']+1}"
    nets[L["net_anode"]].append((ref,"1"))     # anode
    nets[L["net_cathode"]].append((ref,"2"))   # cathode

# power/gnd to connector (pins 14,15,16)
nets.setdefault("GND",[]).append(("J1","15"))
nets.setdefault("VLED",[]).append(("J1","14"))

# ---- KiCad legacy .net ----
ts=datetime.datetime.now().isoformat()
comps=[]
for L in leds: comps.append((f"D{L['idx']+1}","LED_0201","LED"))
for i in range(N): comps.append((f"R{i+1}","R_0402","47R"))
comps.append(("J1","Conn_16","B2B_16"))

with open("dial.net","w") as f:
    f.write('(export (version D)\n')
    f.write(f'  (design (source "dial_placement.json") (date "{ts}") (tool "gen_netlist.py"))\n')
    f.write('  (components\n')
    for ref,fp,val in comps:
        f.write(f'    (comp (ref "{ref}") (value "{val}") (footprint "watch:{fp}"))\n')
    f.write('  )\n  (nets\n')
    code=1
    for net,nodes in nets.items():
        if not nodes: continue
        f.write(f'    (net (code "{code}") (name "{net}")\n')
        for ref,pin in nodes:
            f.write(f'      (node (ref "{ref}") (pin "{pin}"))\n')
        f.write('    )\n'); code+=1
    f.write('  )\n)\n')
print("wrote dial.net  (KiCad legacy netlist)")

with open("connections.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["net","ref","pin"])
    for net,nodes in nets.items():
        for ref,pin in nodes: w.writerow([net,ref,pin])
print("wrote connections.csv")

# sanity
nonempty={k:v for k,v in nets.items() if v}
print(f"nets: {len(nonempty)}  (13 CP buses + 13 MCU drive + GND + VLED)")
print(f"components: {len(comps)}  (156 LED + 13 R + 1 connector)")
