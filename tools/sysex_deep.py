#!/usr/bin/env python3
"""
Phase 2: Deep dive into the SysEx handler functions identified in Phase 1.
Focus on:
1. The large dispatcher at 0x377C8 (0x81572xx area)
2. The SysEx builder at 0x1DA24 (0x813D8xx area)
3. The function at 0x152B8 (0x81350xx) - parameter handler
4. The function at 0x37BE0 (0x8157BB8) - SysEx sender
"""

import struct
from capstone import *

BINARY_PATH = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
IMAGE_BASE = 0x08120000

def load_binary():
    with open(BINARY_PATH, "rb") as f:
        return f.read()

def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]

def disasm(data, start_offset, length, base=None):
    if base is None:
        base = IMAGE_BASE + start_offset
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    md.skipdata = True
    return list(md.disasm(data[start_offset:start_offset+length], base))

data = load_binary()

# ====================================================================
# 1. Main SysEx dispatcher - scan around 0x377C8
# The literal pool is at the end of a large function. Let's find its start.
# From the first pass, the area around 0x5770C has many state machine transitions
# with constants like 0x0B, 0x15, 0x1C, 0x1F, 0x22, 0x23, 0x25, 0x26, 0x2B, etc.
# These look like state IDs for a SysEx parser state machine.
# ====================================================================

print("=" * 80)
print("1. MAIN SYSEX DISPATCHER (around 0x377C8)")
print("=" * 80)

# Find the function that contains the 0x377C8 reference
# From phase 1, the ref instruction is at 0x0815770E
# Let's scan further back to find the actual function entry
# The code at 0x81572F8 is a common branch target (loop back)
# Let's look for a PUSH instruction much earlier

for scan_back in [0x600, 0x800, 0xA00, 0xC00, 0xE00, 0x1000]:
    start = 0x3770E - scan_back  # 0x5770E is the ref instruction offset
    if start < 0:
        start = 0
    if start % 2 != 0:
        start -= 1
    
    insns = disasm(data, start, 0x3770E - start + 4)
    
    # Find all PUSH instructions with LR
    pushes_lr = [(i, insn) for i, insn in enumerate(insns) 
                 if insn.mnemonic == 'push' and 'lr' in insn.op_str.lower()]
    
    if pushes_lr:
        # The last PUSH with LR before our reference is likely the function start
        last_push_i, last_push = pushes_lr[-1]
        print(f"Scan back {scan_back}: Found PUSH with LR at 0x{last_push.address:08X}")
        print(f"  {last_push.mnemonic} {last_push.op_str}")

# Let's try a larger scan
print("\nScanning 0x1400 bytes back from 0x5770E:")
insns = disasm(data, 0x3770E - 0x1400, 0x1400 + 0x400)
pushes_lr = [(i, insn) for i, insn in enumerate(insns) 
             if insn.mnemonic == 'push' and 'lr' in insn.op_str.lower()]
for i, insn in pushes_lr:
    print(f"  0x{insn.address:08X}: {insn.mnemonic} {insn.op_str}")

# The large state machine function seems to start around 0x81572F8
# Let's disassemble a wide range from the earliest reasonable PUSH
print("\n\nDisassembling the main SysEx handler function:")

# Let's look at the function starting from a reasonable point
# The branch target 0x81572F8 is where all the "b" instructions loop back to
# This suggests a state machine. Let's find the enclosing function.

# Try from 0x37000 (0x8157000) area
func_candidates_start = []
for offset in range(0x37000, 0x3770E, 2):
    # Check for PUSH instruction pattern (Thumb: 0xB5xx or 0xE92Dxxxx for PUSH.W)
    hw = read_u32(data, offset) & 0xFFFF
    hw2 = read_u32(data, offset) 
    if (hw & 0xFF00) == 0xB500:  # PUSH {reglist}
        insns_check = disasm(data, offset, 4)
        if insns_check and insns_check[0].mnemonic == 'push' and 'lr' in insns_check[0].op_str.lower():
            func_candidates_start.append(offset)

print(f"\nPUSH with LR instructions in range 0x37000-0x3770E:")
for off in func_candidates_start:
    insns_check = disasm(data, off, 4)
    print(f"  0x{IMAGE_BASE+off:08X}: {insns_check[0].mnemonic} {insns_check[0].op_str}")

# The biggest function containing 0x3770E likely starts at one of these
# Let's pick the most likely one and disassemble it

# Let's use a different approach - scan for the function boundary by looking
# at the literal pool references and the "b 0x81572F8" pattern
print("\n\nLooking for the main loop at 0x81572F8:")
# Disassemble from 0x81572F8
loop_insns = disasm(data, 0x372F8, 0x500)
for insn in loop_insns[:80]:
    print(f"  0x{insn.address:08X}: {insn.mnemonic:8s} {insn.op_str}")
