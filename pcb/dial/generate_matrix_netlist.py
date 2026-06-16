#!/usr/bin/env python3
"""KiCad netlist + connections for the IS31FL3743A matrix dial."""
import json,csv,datetime
d=json.load(open("repo/pcb/dial/dial_matrix.json")); leds=d["leds"]
SW=d["matrix"]["sw"]; CS=d["matrix"]["cs"]
nets={}
def add(net,ref,pin): nets.setdefault(net,[]).append((ref,pin))
# each LED: anode -> SW line, cathode -> CS line (driver sources SW, sinks CS)
for L in leds:
    ref=f"D{L['idx']+1}"
    add(L["net_sw"],ref,"1")   # anode to SW
    add(L["net_cs"],ref,"2")   # cathode to CS
# driver pins
for i in range(1,SW+1): add(f"SW{i}","U2",f"SW{i}")
for i in range(1,CS+1): add(f"CS{i}","U2",f"CS{i}")
# driver support
add("SDA","U2","SDA"); add("SCL","U2","SCL"); add("VLED","U2","VCC")
add("GND","U2","GND"); add("REXT","U2","R_EXT"); add("SDB","U2","SDB")
add("SDA","J1","1"); add("SCL","J1","2"); add("VLED","J1","3"); add("GND","J1","4")
add("REXT","R1","1"); add("GND","R1","2")

ts=datetime.datetime.now().isoformat()
comps=[(f"D{L['idx']+1}","LED_0201","LED") for L in leds]
comps+=[("U2","QFN_IS31FL3743A","IS31FL3743A"),("R1","R_0402","R_EXT"),("J1","Conn_4","B2B")]
with open("repo/pcb/dial/dial_matrix.net","w") as f:
    f.write('(export (version D)\n')
    f.write(f'  (design (source "dial_matrix.json") (date "{ts}") (tool "dial_matrix_net.py"))\n  (components\n')
    for ref,fp,val in comps:
        f.write(f'    (comp (ref "{ref}") (value "{val}") (footprint "watch:{fp}"))\n')
    f.write('  )\n  (nets\n'); code=1
    for net,nodes in nets.items():
        f.write(f'    (net (code "{code}") (name "{net}")\n')
        for ref,pin in nodes: f.write(f'      (node (ref "{ref}") (pin "{pin}"))\n')
        f.write('    )\n'); code+=1
    f.write('  )\n)\n')
with open("repo/pcb/dial/connections_matrix.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["net","ref","pin"])
    for net,nodes in nets.items():
        for ref,pin in nodes: w.writerow([net,ref,pin])
print(f"nets: {len(nets)} (11 SW + 18 CS + power/I2C)")
print(f"components: {len(comps)} (132 LED + driver + R_EXT + connector)")
print("wrote dial_matrix.net / connections_matrix.csv")
