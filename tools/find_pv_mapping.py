#!/usr/bin/env python3
"""
For each mnfx value, find which XML processorvalue it's closest to (as pv/N for various N).
This reveals the true N used for normalization.
"""
import sys, os, struct, math
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from pathlib import Path

xml_path = 'reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/minifreak_vst_params.xml'
tree = ET.parse(xml_path)
root = tree.getroot()

item_lists = {}
for el in root:
    if el.tag == 'item_list':
        name = el.get('name', '')
        items = [(item.get('text', ''), int(item.get('processorvalue', '0'))) for item in el]
        item_lists[name] = items

enum_params = {}
for el in root:
    if el.tag == 'param' and len(el) > 0:
        il_ref = el[-1]
        il_name = il_ref.get('name', '')
        if il_name and il_name in item_lists:
            enum_params[el.get('name')] = item_lists[il_name]

base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory')
files = sorted(base.glob('*.mnfx'))

for param_name, xml_items in sorted(enum_params.items()):
    pvs = [pv for _, pv in xml_items]
    max_pv = max(pvs)
    
    # Get mnfx unique float values
    mnfx_vals = set()
    for f in files:
        p = MnfxParser(f.read_bytes())
        if param_name in p.params:
            mnfx_vals.add(float(p.params[param_name]))
    
    # For each mnfx value, find which PV it maps to using round(v * N)
    # Try all N from max_pv to max_pv+10
    print(f"\n{param_name}: {len(mnfx_vals)} mnfx values, {len(xml_items)} XML items, max_pv={max_pv}")
    
    for n in [max_pv, max_pv + 1]:
        print(f"\n  Testing N={n}:")
        mappings = {}  # mnfx_val -> (pv, name)
        ambiguous = 0
        unmapped = 0
        
        for v in sorted(mnfx_vals):
            idx = round(v * n)
            if idx < 0 or idx > n:
                unmapped += 1
                continue
            
            # Find XML item with this processorvalue
            found = None
            for text, pv in xml_items:
                if pv == idx:
                    found = (pv, text)
                    break
            
            if found:
                mappings[v] = found
            else:
                # No XML item with this PV — might be a Dummy slot
                mappings[v] = (idx, "???")
        
        # Check: are all mappings unambiguous?
        used_pvs = [pv for _, (pv, _) in mappings.items()]
        unique_pvs = set(used_pvs)
        
        if len(used_pvs) == len(unique_pvs):
            print(f"    ✅ All {len(mappings)} values mapped to unique PVs")
            for v in sorted(mappings.keys()):
                pv, name = mappings[v]
                err = abs(v - pv/n)
                print(f"      {v:+.10f} → PV {pv:2d} ({name:<20s}) err={err:.8f}")
        else:
            print(f"    ❌ Collisions: {len(used_pvs)} values → {len(unique_pvs)} unique PVs")
