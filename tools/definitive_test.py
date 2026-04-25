#!/usr/bin/env python3
"""
DEFINITIVE TEST: Use VST XML processorvalue directly.
For each enum param, compute float(processorvalue / max_processorvalue)
and compare with actual mnfx float32 hex values.
"""
import sys, os, struct
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from pathlib import Path

# Load VST XML
xml_path = 'reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/minifreak_vst_params.xml'
tree = ET.parse(xml_path)
root = tree.getroot()

item_lists = {}
for el in root:
    if el.tag == 'item_list':
        name = el.get('name', '')
        items = []
        for item in el:
            items.append((item.get('text', ''), int(item.get('processorvalue', '0'))))
        item_lists[name] = items

# Enum params in XML (those with item_lists)
enum_params = {}
for el in root:
    if el.tag == 'param' and len(el) > 0:
        il_ref = el[-1]  # latest version
        il_name = il_ref.get('name', '')
        if il_name and il_name in item_lists:
            enum_params[el.get('name')] = item_lists[il_name]

# Get mnfx values
base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory')
files = sorted(base.glob('*.mnfx'))

for param_name, xml_items in sorted(enum_params.items()):
    max_pv = max(pv for _, pv in xml_items)
    
    # Collect unique mnfx float32 hex values
    mnfx_hexes = {}
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            v = float(p.params[param_name])
            h = struct.pack('f', v).hex()
            if h not in mnfx_hexes:
                mnfx_hexes[h] = (v, f.stem)
    
    print(f"\n{'='*70}")
    print(f"{param_name}: XML has {len(xml_items)} items, max_pv={max_pv}")
    print(f"mnfx has {len(mnfx_hexes)} unique hex values")
    
    # For each XML item, compute expected float and compare
    print(f"\n  {'PV':>3s} {'Name':<20s} {'Expected hex':>12s} {'Expected val':>14s} {'Found?':>8s}")
    for text, pv in xml_items:
        # Try: float(pv / max_pv)
        expected_f = pv / max_pv
        expected_hex = struct.pack('f', expected_f).hex()
        found = expected_hex in mnfx_hexes
        
        marker = "✅" if found else "  "
        print(f"  {pv:>3d} {text:<20s} {expected_hex:>12s} {expected_f:>14.10f} {marker:>8s}")
    
    # Also try: float(pv / (max_pv - 1))
    print(f"\n  --- Alternative: pv/(max_pv-1) ---")
    for text, pv in xml_items:
        expected_f = pv / (max_pv - 1) if max_pv > 1 else 0
        expected_hex = struct.pack('f', expected_f).hex()
        found = expected_hex in mnfx_hexes
        marker = "✅" if found else "  "
        print(f"  {pv:>3d} {text:<20s} {expected_hex:>12s} {expected_f:>14.10f} {marker:>8s}")
