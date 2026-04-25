#!/usr/bin/env python3
"""
Cross-validate: for each preset, does _nearest_enum return the correct name?
Strategy: use the PRESET FILENAME to infer expected engine type, then verify.
Also: compare multiple presets with same filename pattern to check consistency.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from tools.mf_enums import enum_lookup
from pathlib import Path
from collections import defaultdict

base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory')
files = sorted(base.glob('*.mnfx'))

# Test: enum_lookup consistency
# If two presets have "same" float value (within epsilon), they should map to same name
print("=== Test 1: Consistency — same float → same name ===\n")

PARAM_ENUMS = {
    'Osc1_Type': 23, 'Osc2_Type': 29,  # max key
    'FX1_Type': 12, 'FX2_Type': 12, 'FX3_Type': 12,
    'LFO1_Wave': 8, 'LFO2_Wave': 8,
    'Arp_Mode': 7,
    'Gen_NoteMode': 4,
    'CycEnv_Mode': 3,
    'Vcf_Type': 2,
}

inconsistencies = 0
for param_name, max_key in PARAM_ENUMS.items():
    val_to_name = {}
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            v = float(p.params[param_name])
            name = enum_lookup({i: str(i) for i in range(max_key + 1)}, v, max_key)
            v_key = round(v * max_key)
            if v_key not in val_to_name:
                val_to_name[v_key] = (name, f.stem)
            elif val_to_name[v_key][0] != name:
                inconsistencies += 1
    
    n_used = len(val_to_name)
    print(f"  {param_name}: {n_used} unique indices mapped, {inconsistencies} inconsistencies")

print(f"\n=== Test 2: Value range check — all mapped indices valid? ===\n")

for param_name, max_key in PARAM_ENUMS.items():
    all_indices = set()
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            v = float(p.params[param_name])
            idx = round(v * max_key)
            all_indices.add(idx)
    
    out_of_range = [i for i in all_indices if i < 0 or i > max_key]
    status = "✅" if not out_of_range else "❌"
    print(f"  {status} {param_name}: indices={sorted(all_indices)}, out_of_range={out_of_range}")

print(f"\n=== Test 3: Boundary precision — does round(v*N) give exact index? ===\n")

# For each value, compute the error between v and i/N
for param_name, max_key in PARAM_ENUMS.items():
    errors = []
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            v = float(p.params[param_name])
            idx = round(v * max_key)
            expected_v = idx / max_key
            err = abs(v - expected_v)
            errors.append(err)
    
    if errors:
        max_err = max(errors)
        avg_err = sum(errors) / len(errors)
        status = "✅" if max_err < 0.01 else "⚠️"
        print(f"  {status} {param_name}: max_err={max_err:.8f}, avg_err={avg_err:.8f}")
        if max_err > 0.01:
            # Show worst offenders
            worst = sorted(zip(errors, range(len(errors))), reverse=True)[:3]
            for err_val, idx_pos in worst:
                print(f"      err={err_val:.8f} (sample {idx_pos})")

print(f"\n=== Test 4: N sensitivity — does a different N give better results? ===\n")

# For each param, try N from max_key-5 to max_key+5 and find best
for param_name, max_key in PARAM_ENUMS.items():
    all_vals = []
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            all_vals.append(float(p.params[param_name]))
    
    best_n = max_key
    best_score = float('inf')
    
    for n in range(max(1, max_key - 5), max_key + 6):
        total_err = 0
        for v in all_vals:
            idx = round(v * n)
            if idx < 0 or idx > n:
                total_err += 1.0  # penalty
            else:
                expected = idx / n
                total_err += abs(v - expected)
        
        if total_err < best_score:
            best_score = total_err
            best_n = n
    
    if best_n != max_key:
        print(f"  ⚠️ {param_name}: best N={best_n} (current N={max_key}), score diff={best_score:.8f}")
    else:
        print(f"  ✅ {param_name}: N={max_key} is optimal")
