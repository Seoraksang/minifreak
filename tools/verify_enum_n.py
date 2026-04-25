#!/usr/bin/env python3
"""Verify enum N values by reverse-engineering from .mnfx float32 data."""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from pathlib import Path

base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory')
files = sorted(base.glob('*.mnfx'))

ENUM_PARAMS = {
    'Osc1_Type': 24, 'Osc2_Type': 30,
    'FX1_Type': 13, 'FX2_Type': 13, 'FX3_Type': 13,
    'LFO1_Wave': 9, 'LFO2_Wave': 9,
    'Arp_Mode': 8, 'CycEnv_Mode': 4, 'Vcf_Type': 3,
}

for param_name, expected_count in ENUM_PARAMS.items():
    vals = set()
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            vals.add(float(p.params[param_name]))
    if not vals:
        print(f"{param_name}: NO VALUES")
        continue

    best_n = None
    for n in range(1, 60):
        ok = True
        for v in vals:
            idx = round(v * n)
            if idx < 0 or idx > n:
                ok = False; break
            recon = struct.unpack('f', struct.pack('f', idx / n))[0]
            if abs(v - recon) > 1.5e-7:
                ok = False; break
        if ok:
            best_n = n; break

    if best_n:
        indices = sorted(round(v * best_n) for v in vals)
        status = "✅" if best_n + 1 >= expected_count else "⚠️"
        print(f"{status} {param_name}: N={best_n} slots(0..{best_n}), {len(indices)} values used, XML has {expected_count} items")
    else:
        print(f"❌ {param_name}: no clean N (count={len(vals)}, max={max(vals):.6f})")
