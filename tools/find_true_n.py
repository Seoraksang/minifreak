#!/usr/bin/env python3
"""
Find the TRUE N for each enum by testing all possible N values.
The correct N gives: round(v*N) produces valid unique indices for all values,
AND the mapping is unambiguous (no two values map to same index).
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from pathlib import Path

base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory')
files = sorted(base.glob('*.mnfx'))

ENUM_PARAMS = [
    'Osc1_Type', 'Osc2_Type',
    'FX1_Type', 'FX2_Type', 'FX3_Type',
    'LFO1_Wave', 'LFO2_Wave',
    'Arp_Mode', 'Gen_NoteMode', 'CycEnv_Mode', 'Vcf_Type',
]

print("Finding TRUE N for each enum parameter\n")
print(f"{'Param':<20s} {'True N':>6s} {'Slots':>6s} {'Used':>5s} {'Max Err':>10s} {'All diff?':>10s}")
print("-" * 70)

for param_name in ENUM_PARAMS:
    vals = []
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            vals.append(float(p.params[param_name]))
    
    if not vals:
        print(f"{param_name:<20s} NO VALUES")
        continue
    
    unique_vals = set(vals)
    
    best_n = None
    best_score = float('inf')
    
    for n in range(1, 65):
        indices = []
        valid = True
        max_err = 0
        
        for v in unique_vals:
            idx = round(v * n)
            if idx < 0 or idx > n:
                valid = False; break
            expected = idx / n
            err = abs(v - expected)
            max_err = max(max_err, err)
            indices.append(idx)
        
        if not valid:
            continue
        
        # Score: prefer lower max_err, then fewer duplicate indices
        unique_indices = len(set(indices))
        duplicates = len(indices) - unique_indices
        score = max_err * 1000 + duplicates * 10
        
        if score < best_score:
            best_score = score
            best_n = n
            best_max_err = max_err
            best_unique = unique_indices
            best_indices = sorted(set(indices))
    
    if best_n:
        all_diff = "✅" if best_unique == len(unique_vals) else f"❌ ({len(unique_vals)} vals → {best_unique} idx)"
        print(f"{param_name:<20s} {best_n:>6d} {best_n+1:>6d} {best_unique:>5d} {best_max_err:>10.8f} {all_diff:>10s}")
        print(f"  Indices: {best_indices}")
    else:
        print(f"{param_name:<20s} NO VALID N FOUND")
