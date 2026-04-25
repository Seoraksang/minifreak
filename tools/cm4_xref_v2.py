#!/usr/bin/env python3
"""
MiniFreak CM4 XRef 추적 — 정확한 이미지 베이스(0x08100000) 기반
"""
import json, struct
from capstone import *

BINARY = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
STRINGS_JSON = "/home/jth/hoon/minifreak/firmware/analysis/cm4_all_strings.json"
OUTPUT = "/home/jth/hoon/minifreak/firmware/analysis/cm4_xref_map.json"

IMAGE_BASE = 0x08100000

with open(BINARY, "rb") as f:
    binary = f.read()

with open(STRINGS_JSON) as f:
    strings = json.load(f)

# Create: real_address -> string mapping
# Ghidra loaded at base 0, so string addr 0x89da0 = real addr IMAGE_BASE + 0x89da0
addr_to_string = {}
for s in strings:
    offset = int(s["address"], 16)
    real_addr = IMAGE_BASE + offset
    addr_to_string[real_addr] = s["string"]

print(f"String address range: 0x{min(addr_to_string):08x} - 0x{max(addr_to_string):08x}")
print(f"Total strings: {len(addr_to_string)}")

# Disassemble code section in Thumb mode
# Code is roughly from vector table (offset 0x40) to start of rodata (~offset 0x89000)
CODE_START = 0x40  
CODE_END = 0x88000  # approximate code/rodata boundary

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

refs_found = {}

print(f"\nScanning code region 0x{IMAGE_BASE + CODE_START:08x} - 0x{IMAGE_BASE + CODE_END:08x}...")

for insn in md.disasm(binary[CODE_START:CODE_END], IMAGE_BASE + CODE_START):
    if insn.mnemonic != 'ldr':
        continue
    
    op_str = insn.op_str.lower()
    if '[pc' not in op_str or '#' not in op_str:
        continue
    
    # Parse: ldr rn, [pc, #offset]
    try:
        # Extract PC-relative offset
        parts = op_str.split('#')
        offset_str = parts[-1].rstrip(']').rstrip().rstrip(',')
        offset = int(offset_str, 0)
        
        # PC in Thumb = current + 4, word-aligned
        pc = insn.address + 4
        pc_aligned = pc & ~3
        literal_addr = pc_aligned + offset
        
        # Read 32-bit value from literal pool
        lit_offset = literal_addr - IMAGE_BASE
        if 0 <= lit_offset <= len(binary) - 4:
            loaded_value = struct.unpack_from('<I', binary, lit_offset)[0]
            
            if loaded_value in addr_to_string:
                code_addr = insn.address
                if code_addr not in refs_found:
                    refs_found[code_addr] = {
                        "code_addr": hex(code_addr),
                        "string_addr": hex(loaded_value),
                        "string": addr_to_string[loaded_value][:120],
                    }
    except (ValueError, IndexError, struct.error):
        pass

print(f"\n=== Found {len(refs_found)} string references! ===")

# Categorize
categories = {
    "rtti_class": [],
    "preset": [],
    "oscillator": [],
    "fx": [],
    "filter": [],
    "midi": [],
    "usb": [],
    "protobuf": [],
    "calibration": [],
    "other": [],
}

for code_addr, ref in sorted(refs_found.items()):
    s = ref["string"]
    sl = s.lower()
    
    if "::" in s and ("void " in s or "bool " in s or "uint" in s):
        categories["rtti_class"].append(ref)
    elif "preset" in sl or "synthparams" in sl or "fxparams" in sl or "ctrlparams" in sl:
        categories["preset"].append(ref)
    elif any(x in sl for x in ["basic wave", "superwave", "karplus", "waveshaper", "two op", "noise", "wavetable", "sample", "granular", "audio in", "multi filter", "surgeon", "comb filter", "phaser filter"]):
        categories["oscillator"].append(ref)
    elif any(x in sl for x in ["chorus", "phaser", "flanger", "reverb", "distortion"]):
        categories["fx"].append(ref)
    elif any(x in sl for x in ["cutoff", "resonance", "filter", "wavefold"]):
        categories["filter"].append(ref)
    elif any(x in sl for x in ["midi", "knob send cc"]):
        categories["midi"].append(ref)
    elif any(x in sl for x in ["minifreak", "vst", "audio", "usb"]):
        categories["usb"].append(ref)
    elif any(x in sl for x in ["varint", "wire_type", "field", "tag", "proto"]):
        categories["protobuf"].append(ref)
    elif any(x in sl for x in ["calib", "median", "sma", "hysteresis"]):
        categories["calibration"].append(ref)
    else:
        categories["other"].append(ref)

for cat, entries in categories.items():
    if entries:
        print(f"\n--- {cat.upper()} ({len(entries)} refs) ---")
        for e in entries[:20]:
            print(f"  code@{e['code_addr']} → [{e['string_addr']}] \"{e['string'][:70]}\"")
        if len(entries) > 20:
            print(f"  ... +{len(entries)-20} more")

# Save
output = {
    "image_base": hex(IMAGE_BASE),
    "total_refs": len(refs_found),
    "categories": categories,
}
with open(OUTPUT, "w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\nSaved to {OUTPUT}")
