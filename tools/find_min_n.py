#!/usr/bin/env python3
"""Find minimum N where all values map to unique valid indices with small error."""
import sys, os
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

for param_name in ENUM_PARAMS:
    vals = set()
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            vals.add(float(p.params[param_name]))
    
    if not vals:
        continue
    
    # Find minimum N where:
    # 1. All values map to valid indices (0..N)
    # 2. All indices are unique (no collisions)
    # 3. max_err < threshold
    best_n = None
    for n in range(1, 65):
        indices = []
        valid = True
        for v in vals:
            idx = round(v * n)
            if idx < 0 or idx > n:
                valid = False; break
            indices.append(idx)
        
        if not valid:
            continue
        
        # Check uniqueness
        if len(set(indices)) != len(indices):
            continue
        
        # Check error
        max_err = max(abs(v - round(v*n)/n) for v in vals)
        if max_err < 0.02:  # 2% threshold
            best_n = n
            break
    
    if best_n:
        indices = sorted(round(v * best_n) for v in vals)
        max_err = max(abs(v - round(v*best_n)/best_n) for v in vals)
        print(f"{param_name:<20s} → N={best_n}, indices={indices}, max_err={max_err:.8f}")
    else:
        print(f"{param_name:<20s} → NO MINIMAL N FOUND")
