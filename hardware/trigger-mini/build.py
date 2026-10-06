#!/usr/bin/env python3
"""Генерирует out/bom.csv (формат JLCPCB), out/netlist.json, out/nets.md из design.py."""
import json, collections
from design import *

# BOM
groups = collections.OrderedDict()
for ref, d in PARTS.items():
    if "pad" in d["flags"]:
        continue
    key = (d["val"], d["fp"], d["lcsc"])
    groups.setdefault(key, []).append(ref)
def refkey(r):
    import re
    m = re.match(r"([A-Za-z]+)(\d*)", r); return (m.group(1), int(m.group(2) or 0))
with open("out/bom.csv", "w", encoding="utf-8") as f:
    f.write("Comment,Designator,Footprint,LCSC Part #,Notes\n")
    for (val, fp, lcsc), refs in groups.items():
        refs.sort(key=refkey)
        notes = "; ".join(sorted({PARTS[r]["note"] for r in refs if PARTS[r]["note"]})).replace('"', "'")
        tbd = " [TBD]" if any("tbd" in PARTS[r]["flags"] for r in refs) else ""
        f.write(f'"{val}","{" ".join(refs)}","{fp}","{lcsc}","{notes}{tbd}"\n')

# netlist
with open("out/netlist.json", "w", encoding="utf-8") as f:
    json.dump({"version": "1.2", "parts": {r: {k: (sorted(v) if isinstance(v, set) else v) for k, v in d.items()} for r, d in PARTS.items()},
               "nets": NETS}, f, ensure_ascii=False, indent=1)

# nets.md
with open("out/nets.md", "w", encoding="utf-8") as f:
    f.write("# Цепи v1.2 (авто-генерация из design.py)\n\n| Цепь | Пины |\n|---|---|\n")
    for net in sorted(NETS):
        f.write(f"| {net} | {', '.join(NETS[net])} |\n")
print("ok:", len(groups), "позиций BOM,", len(NETS), "цепей")
