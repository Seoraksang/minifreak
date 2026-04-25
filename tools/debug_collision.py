#!/usr/bin/env python3
"""Debug: which values collide for Osc1_Type with N=23?"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from pathlib import Path

base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory')
files = sorted(base.glob('*.mnfx'))

vals = set()
for f in files:
    p = MnfxParser(f.read_bytes())
    if 'Osc1_Type' in p.params:
        vals.add(float(p.params['Osc1_Type']))

print(f"Osc1_Type: {len(vals)} unique values\n")

for n in [14, 23, 24]:
    print(f"--- N={n} ---")
    mapping = {}
    for v in sorted(vals):
        idx = round(v * n)
        if idx not in mapping:
            mapping[idx] = []
        mapping[idx].append(v)
    
    for idx in sorted(mapping.keys()):
        vs = mapping[idx]
        if len(vs) > 1:
            print(f"  ⚠️ PV {idx}: {len(vs)} values collide!")
            for v in vs:
                print(f"       {v:+.15f}  (raw diff from {idx}/{n}: {v - idx/n:+.15e})")
        else:
            print(f"  PV {idx}: {vs[0]:+.10f}")
