#!/usr/bin/env python3
"""
Build accurate float32 → enum mapping by reading VST preset files.
VST presets store processorvalue as text, mnfx stores as float32.
Match them by preset name to build the ground truth mapping.
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from pathlib import Path

# Find VST preset files (.vstpreset or .preset)
vst_base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets')
mnfx_base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory')

# List available preset formats
print("Looking for VST preset files...")
for ext in ['*.vstpreset', '*.preset', '*.fxp', '*.fxb']:
    found = list(vst_base.rglob(ext))
    if found:
        print(f"  {ext}: {len(found)} files")
        for f in found[:3]:
            print(f"    {f}")
    else:
        print(f"  {ext}: none")

# Check what's in HardwarePresets
print(f"\nHardwarePresets contents:")
for d in sorted(vst_base.iterdir()):
    if d.is_dir():
        print(f"  {d.name}/")
        for d2 in sorted(d.iterdir()):
            if d2.is_dir():
                count = len(list(d2.iterdir()))
                print(f"    {d2.name}/ ({count} files)")
