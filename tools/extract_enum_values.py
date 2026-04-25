#!/usr/bin/env python3
"""Extract all enum-type parameter values from 512 factory presets."""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from pathlib import Path

# Parameters that are enum selectors (discrete values, not continuous)
ENUM_PARAMS = [
    # Oscillators
    'Osc1_Type', 'Osc2_Type',
    # Filters
    'Vcf_Type',
    # FX
    'FX1_Type', 'FX2_Type', 'FX3_Type',
    # LFO
    'LFO1_Wave', 'LFO2_Wave',
    # Voice
    'Gen_NoteMode', 'Gen_UnisonMode', 'Gen_PolyAlloc', 'Gen_PolySteal',
    'Gen_LegatoMode', 'Gen_RetrigMode',
    # Envelope
    'CycEnv_Mode',
    # Arp
    'Arp_Mode',
    # Sequencer
    'Seq_Autom_Dest_1', 'Seq_Autom_Dest_2', 'Seq_Autom_Dest_3', 'Seq_Autom_Dest_4',
]

base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks')
mnfx_files = sorted(base.rglob('*.mnfx'))
print(f"Total presets: {len(mnfx_files)}\n")

results = {}
for param in ENUM_PARAMS:
    vals = collections.OrderedDict()  # value -> list of preset names
    count = 0
    for f in mnfx_files:
        with open(f, 'rb') as fh:
            p = MnfxParser(fh.read())
        if param in p.params:
            v = p.params[param]
            if v not in vals:
                vals[v] = []
            vals[v].append(f.stem)
            count += 1
    results[param] = (count, vals)

# Print results
for param, (count, vals) in results.items():
    print(f"=== {param} ({count} presets have this) ===")
    # Sort by float value
    sorted_vals = sorted(vals.keys(), key=lambda x: float(x))
    for v in sorted_vals:
        names = vals[v]
        # Show first 3 example preset names
        examples = names[:3]
        print(f"  {v:>10s} ({len(names):>3d} presets) e.g. {examples}")
    print()
