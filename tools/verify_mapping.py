#!/usr/bin/env python3
"""Verify _nearest_enum mapping accuracy against ALL 512 presets."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser, _nearest_enum
from tools.mf_enums import (
    OSC1_ENGINES, OSC2_ENGINES, FX_TYPES, LFO_WAVES,
    ARP_MODES, VOICE_MODES, CYCENV_MODES, VCF_TYPES,
)
from pathlib import Path

base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory')
files = sorted(base.glob('*.mnfx'))

# Define which params map to which enums
PARAM_ENUMS = {
    'Osc1_Type': OSC1_ENGINES,
    'Osc2_Type': OSC2_ENGINES,
    'FX1_Type': FX_TYPES,
    'FX2_Type': FX_TYPES,
    'FX3_Type': FX_TYPES,
    'LFO1_Wave': LFO_WAVES,
    'LFO2_Wave': LFO_WAVES,
    'Arp_Mode': ARP_MODES,
    'Gen_NoteMode': VOICE_MODES,
    'CycEnv_Mode': CYCENV_MODES,
    'Vcf_Type': VCF_TYPES,
}

errors = 0
warnings = 0
total = 0

for param_name, enum_dict in PARAM_ENUMS.items():
    vals_found = set()
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            v = float(p.params[param_name])
            total += 1
            result = _nearest_enum(str(v), enum_dict)
            vals_found.add(result)

    # Check: are all found values valid enum entries?
    for result in vals_found:
        if 'Unknown' in result:
            errors += 1
            print(f"  ❌ {param_name}: {result}")
    
    # Check: are there duplicate index mappings?
    reverse_map = {v: k for k, v in enum_dict.items()}
    indices_used = set()
    for result in vals_found:
        idx = reverse_map.get(result)
        if idx is not None:
            if idx in indices_used:
                warnings += 1
            indices_used.add(idx)
    
    # Summary
    n_items = len(enum_dict)
    n_used = len(indices_used)
    status = "✅" if errors == 0 else "❌"
    print(f"{status} {param_name}: {n_used}/{n_items} indices used, {len(vals_found)} unique values, {total} total lookups")

print(f"\n{'='*60}")
if errors == 0:
    print(f"✅ ALL {total} enum lookups successful, 0 errors")
else:
    print(f"❌ {errors} errors in {total} lookups")
if warnings:
    print(f"⚠️  {warnings} duplicate index warnings")
