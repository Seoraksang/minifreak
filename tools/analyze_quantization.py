#!/usr/bin/env python3
"""Analyze enum parameter quantization patterns from .mnfx presets."""
import sys, os, collections, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from pathlib import Path

# Key enum params and their max unique values
ENUM_PARAMS = {
    'Osc1_Type': 16, 'Osc2_Type': 23,
    'Vcf_Type': 3, 'FX1_Type': 11, 'FX2_Type': 10, 'FX3_Type': 11,
    'LFO1_Wave': 9, 'LFO2_Wave': 10,
    'Gen_NoteMode': 5, 'Gen_UnisonMode': 3, 'Gen_PolyAlloc': 3,
    'Gen_PolySteal': 3, 'Gen_LegatoMode': 2, 'Gen_RetrigMode': 2,
    'CycEnv_Mode': 4, 'Arp_Mode': 7,
}

base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks')
mnfx_files = sorted(base.rglob('*.mnfx'))

for param, max_vals in ENUM_PARAMS.items():
    vals = set()
    for f in mnfx_files:
        with open(f, 'rb') as fh:
            p = MnfxParser(fh.read())
        if param in p.params:
            vals.add(float(p.params[param]))
    
    sorted_vals = sorted(vals)
    
    # Try to find quantization: index = round(value * N) for some N
    # For most params, value is in [0, 1] range
    if sorted_vals and sorted_vals[-1] <= 1.0:
        # Find N such that index = round(v * N) gives unique integers 0..N
        for N in range(max_vals - 1, max_vals + 5):
            indices = set()
            for v in sorted_vals:
                idx = round(v * N)
                indices.add(idx)
            if len(indices) == len(sorted_vals) and max(indices, default=0) <= N:
                mapping = {}
                for v in sorted_vals:
                    idx = round(v * N)
                    mapping[v] = idx
                print(f"{param}: N={N}, {len(sorted_vals)} values → indices {sorted(indices)}")
                for v in sorted_vals:
                    print(f"  {v:.8f} → {mapping[v]}")
                break
        else:
            print(f"{param}: NO CLEAN QUANTIZATION FOUND ({len(sorted_vals)} values)")
            for v in sorted_vals:
                print(f"  {v:.8f}")
    else:
        print(f"{param}: values exceed 1.0, raw:")
        for v in sorted_vals:
            print(f"  {v:.8f}")
    print()
