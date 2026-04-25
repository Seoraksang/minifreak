#!/usr/bin/env python3
"""Verify enum quantization by finding best N for each unique value independently."""
import sys, os, struct, math
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

def find_best_n(val, max_n=60):
    """For a single float32 value, find the N that gives cleanest i/N reconstruction."""
    candidates = []
    for n in range(1, max_n + 1):
        idx = round(val * n)
        if idx < 0 or idx > n:
            continue
        recon = struct.unpack('f', struct.pack('f', idx / n))[0]
        err = abs(val - recon)
        candidates.append((n, idx, err))
    # Sort by error, return best
    candidates.sort(key=lambda x: x[2])
    return candidates[:5]

for param_name, expected_count in ENUM_PARAMS.items():
    vals = set()
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            vals.add(float(p.params[param_name]))
    if not vals:
        print(f"\n{param_name}: NO VALUES")
        continue

    print(f"\n{'='*60}")
    print(f"{param_name}: {len(vals)} unique values, XML expects {expected_count} items")
    print(f"{'='*60}")

    # For each value, find best (N, idx) with error < 1e-6
    all_best = {}  # val -> [(n, idx, err)]
    for v in sorted(vals):
        bests = find_best_n(v)
        all_best[v] = bests
        n, idx, err = bests[0]
        print(f"  {v:.8f} → best: idx={idx}/{n} (err={err:.2e})")

    # Find consensus N across all values
    from collections import Counter
    n_votes = Counter()
    for v, bests in all_best.items():
        n, idx, err = bests[0]
        n_votes[n] += 1

    print(f"\n  N consensus: {n_votes.most_common(5)}")

    # Check if all values agree on a single N
    if n_votes:
        top_n, top_count = n_votes.most_common(1)[0]
        if top_count == len(vals):
            indices = sorted(round(v * top_n) for v in vals)
            status = "✅" if top_n + 1 >= expected_count else "⚠️"
            print(f"  {status} Consensus N={top_n}, indices={indices}")
        else:
            print(f"  ⚠️ No consensus N. Checking per-value best N with error < 1e-6:")
            # Try to find a single N that works for ALL values with relaxed tolerance
            for n in range(1, 60):
                ok = True
                idx_list = []
                for v in vals:
                    idx = round(v * n)
                    if idx < 0 or idx > n:
                        ok = False; break
                    recon = struct.unpack('f', struct.pack('f', idx / n))[0]
                    if abs(v - recon) > 1e-5:  # relaxed
                        ok = False; break
                    idx_list.append(idx)
                if ok:
                    idx_list = sorted(set(idx_list))
                    status = "✅" if n + 1 >= expected_count else "⚠️"
                    print(f"  {status} Relaxed N={n} works! indices={idx_list}")
                    break
            else:
                print(f"  ❌ No N found even with relaxed tolerance")
