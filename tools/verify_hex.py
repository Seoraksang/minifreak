#!/usr/bin/env python3
"""Direct float32 hex comparison: does mnfx store i/N or something else?"""
import sys, os, struct, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from pathlib import Path

base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory')
files = sorted(base.glob('*.mnfx'))

# For each enum param, get the raw float32 bytes and compare with i/N
ENUM_PARAMS = {
    'LFO1_Wave': 9,   # Simple, clean case
    'LFO2_Wave': 9,   # Has the 0.5 split issue
    'Vcf_Type': 3,    # Simple
    'CycEnv_Mode': 4,
    'Arp_Mode': 8,
    'FX1_Type': 13,
}

print("=== Direct float32 hex comparison ===\n")

for param_name, expected_count in ENUM_PARAMS.items():
    # Collect (float_val, hex_bytes, preset_name) tuples
    samples = []
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            v = float(p.params[param_name])
            h = struct.pack('f', v).hex()
            samples.append((v, h, f.stem))
    
    # Deduplicate by hex
    seen_hex = {}
    for v, h, name in samples:
        if h not in seen_hex:
            seen_hex[h] = (v, name)
    
    print(f"{param_name} ({len(seen_hex)} unique hex values):")
    
    # For each unique hex, try to find matching i/N
    for h in sorted(seen_hex.keys()):
        v, name = seen_hex[h]
        # Try N = expected_count - 1 (number of intervals)
        n = expected_count - 1
        idx = round(v * n)
        if 0 <= idx <= n:
            expected_hex = struct.pack('f', idx / n).hex()
            match = "✅" if expected_hex == h else "❌"
            print(f"  {h} = {v:+.10f}  (preset: {name})  → idx={idx}/{n}  expected_hex={expected_hex} {match}")
        else:
            print(f"  {h} = {v:+.10f}  (preset: {name})  → OUT OF RANGE for N={n}")
    
    # Also check: does the VST XML processorvalue match?
    # XML processorvalue is an integer index. If stored as i/(count-1):
    n2 = expected_count - 1
    print(f"  --- If N={n2} (count-1):")
    for i in range(expected_count):
        hex_i = struct.pack('f', i / n2).hex()
        found = hex_i in seen_hex
        print(f"    idx={i}: {hex_i} {'✅ found' if found else '⬜ not in presets'}")
    print()
