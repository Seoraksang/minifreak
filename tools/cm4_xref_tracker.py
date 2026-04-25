#!/usr/bin/env python3
"""
MiniFreak CM4 바이너리 직접 분석 — Capstone 기반 문자열 XRef 추적
Ghidra 없이 빠르게 함수→문자열 매핑 수행
"""
import json
import struct
from capstone import *

BINARY = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
STRINGS_JSON = "/home/jth/hoon/minifreak/firmware/analysis/cm4_all_strings.json"
OUTPUT = "/home/jth/hoon/minifreak/firmware/analysis/cm4_xref_map.json"

# Load binary
with open(BINARY, "rb") as f:
    binary = f.read()

# Load strings
with open(STRINGS_JSON) as f:
    strings = json.load(f)

# Create address → string mapping
addr_to_string = {}
for s in strings:
    addr_to_string[int(s["address"], 16)] = s["string"]

# ARM Thumb2 disassembler
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# Find all LDR instructions that load from literal pool
# In Thumb2, LDR Rn, [PC, #imm] has encoding: 
#   32-bit: 1111 1001 U101 1111 Rt imm12  (F8DF + Rt<<12 + imm12)
#   16-bit: 01001 Rt imm8                  (48-4F)

literal_pool_refs = {}  # addr_loaded -> list of (code_addr, register)

# Scan code region (skip first 64 bytes = DFU header)
CODE_START = 0x40
CODE_END = len(binary)

print("Scanning {} bytes for LDR literal pool references...".format(CODE_END - CODE_START))

for insn in md.disasm(binary[CODE_START:CODE_END], CODE_START):
    if insn.mnemonic == 'ldr' and '[pc' in insn.op_str.lower():
        # Parse operand to get offset
        # ldr r0, [pc, #offset]
        try:
            parts = insn.op_str.split('#')
            if len(parts) >= 2:
                offset_str = parts[-1].rstrip(']').strip()
                offset = int(offset_str, 0)
                # PC in Thumb mode = current_addr + 4, aligned to 4
                pc = insn.address + 4
                pc_aligned = pc & ~3
                target = pc_aligned + offset
                
                if 0 <= target < len(binary):
                    # Read the 32-bit value from literal pool
                    val = struct.unpack_from('<I', binary, target)[0]
                    
                    if val in addr_to_string:
                        if val not in literal_pool_refs:
                            literal_pool_refs[val] = []
                        literal_pool_refs[val].append({
                            "code_addr": hex(insn.address),
                            "register": insn.op_str.split(',')[0].strip(),
                            "string_addr": hex(val),
                            "string_preview": addr_to_string[val][:80]
                        })
        except (ValueError, IndexError):
            pass

# Also check for ADR instructions (PC-relative address computation)
print("\nScanning for ADR instructions...")
for insn in md.disasm(binary[CODE_START:CODE_END], CODE_START):
    if insn.mnemonic == 'adr':
        try:
            # ADR Rd, label — target is PC-relative
            # This is handled differently, check op_str
            pass
        except:
            pass

# Results
print(f"\n=== Found {len(literal_pool_refs)} string references via literal pool ===")

# Categorize
categories = {
    "preset": [],
    "cv_calib": [],
    "midi": [],
    "oscillator": [],
    "fx": [],
    "usb": [],
    "protobuf": [],
    "other": [],
}

for str_addr, refs in sorted(literal_pool_refs.items()):
    string = addr_to_string[str_addr]
    
    entry = {
        "string_address": hex(str_addr),
        "string": string[:100],
        "referenced_from": [r["code_addr"] for r in refs],
    }
    
    s_lower = string.lower()
    if "preset" in s_lower or "synthparams" in s_lower or "fxparams" in s_lower:
        categories["preset"].append(entry)
    elif "calib" in s_lower or "cvcalib" in s_lower:
        categories["cv_calib"].append(entry)
    elif "midi" in s_lower:
        categories["midi"].append(entry)
    elif any(x in s_lower for x in ["wave", "osc", "basic", "super", "karplus", "fm", "noise", "wavetable", "sample"]):
        categories["oscillator"].append(entry)
    elif any(x in s_lower for x in ["chorus", "phaser", "flanger", "reverb", "distortion", "delay"]):
        categories["fx"].append(entry)
    elif any(x in s_lower for x in ["minifreak", "vst", "audio", "usb"]):
        categories["usb"].append(entry)
    elif any(x in s_lower for x in ["varint", "wire_type", "field", "tag", "proto"]):
        categories["protobuf"].append(entry)
    else:
        categories["other"].append(entry)

for cat, entries in categories.items():
    if entries:
        print(f"\n--- {cat.upper()} ({len(entries)} refs) ---")
        for e in entries[:15]:
            print(f"  [{e['string_address']}] \"{e['string'][:60]}\" ← from {e['referenced_from']}")
        if len(entries) > 15:
            print(f"  ... +{len(entries)-15} more")

# Save
output = {
    "total_string_refs": len(literal_pool_refs),
    "categories": categories,
}

with open(OUTPUT, "w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\nSaved to {OUTPUT}")
