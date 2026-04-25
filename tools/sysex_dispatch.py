#!/usr/bin/env python3
"""
Phase 4: Complete SysEx state machine mapping with TBH dispatch table.
The function at 0x8157278 uses TBH [pc, r3, lsl #1] to dispatch on the state byte.
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

def read_u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]

data = load_binary()

print("=" * 80)
print("SYSEX STATE MACHINE TBH DISPATCH TABLE")
print("=" * 80)

# The function entry at 0x8157278:
#   push {r4, lr}
#   ldrb r3, [r0]        ; load current state from struct
#   subs r3, #1           ; state - 1 (state 0 is "idle/return")
#   sub sp, #0x10
#   cmp r3, #0x2a         ; max state = 42 (0x2A)
#   bhi return            ; if state > 42, bail
#   tbh [pc, r3, lsl #1]  ; table branch using halfword table at PC+4

# The TBH instruction is at 0x8157284
# PC in Thumb = instruction address + 4 = 0x8157288
# The table starts at 0x8157288 (file offset 0x37288)
# Each entry is 2 bytes (halfword), so for state s, offset = (s-1)*2

tbh_pc = 0x8157288
tbh_file_offset = tbh_pc - IMAGE_BASE  # 0x37288

print(f"\nTBH table at offset 0x{tbh_file_offset:05X} (addr 0x{tbh_pc:08X})")
print(f"Max state index: 42 (0x2A)")
print(f"Table size: 43 entries * 2 bytes = 86 bytes")
print()

# Read the dispatch table
print("State dispatch table:")
for state_idx in range(43):
    state = state_idx + 1  # actual state value
    entry_offset = tbh_file_offset + state_idx * 2
    # TBH entries are offsets from the table base (PC+4 of TBH insn = table start)
    # Actually, TBH offsets are from the table start
    half = read_u16(data, entry_offset)
    # The offset is a halfword offset from the table base, in halfwords
    # Target = table_base + half * 2
    target = tbh_pc + half * 2
    target_file_offset = target - IMAGE_BASE
    
    print(f"  State {state:3d} (0x{state:02X}): table[{state_idx:2d}] = 0x{half:04X} -> 0x{target:08X}")

print("\n" + "=" * 80)
print("STATE MACHINE FLOW RECONSTRUCTION")
print("=" * 80)

# Now let's trace the complete SysEx message parsing flow
# The initial state when a new SysEx message starts would be state 1
# F0 (SysEx Start) would trigger the state machine

# From the dispatch analysis and code inspection:
# State 0: Idle (initial state)
# When F0 is received -> State 1 (or the first byte after F0)

# Let's trace the byte-by-byte parsing:
# SysEx format: F0 00 20 6B [dev_id] [msg_type] [data...] F7

# State transitions from the code:

# State 1: Expect 0x00 (first byte of Arturia ID)
#   cmp r1, #0x00 -> if match -> State 2
#   else -> error/reset

# State 2: Expect 0x20 (second byte of Arturia ID)  
# State 3: Expect 0x6B (third byte of Arturia ID)
# State 4: Device ID received
# State 5: ?
# etc.

# Let me build this from the actual code
print("""
SYSEX PARSING STATE MACHINE RECONSTRUCTION:
=============================================

State values used in the state machine (stored at r0[0]):
""")

# Map from the TBH targets to the actual code blocks
state_targets = {}
for state_idx in range(43):
    state = state_idx + 1
    entry_offset = tbh_file_offset + state_idx * 2
    half = read_u16(data, entry_offset)
    target = tbh_pc + half * 2
    state_targets[state] = target

# Now disassemble each target to understand the transition
from capstone import *
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True
md.skipdata = True

def disasm_at(offset, length=64):
    return list(md.disasm(data[offset:offset+length], IMAGE_BASE + offset))

print(f"{'State':>5} {'Target':>12}   {'Code':50s}  {'Transition'}")
print("-" * 120)

for state in range(1, 44):
    target = state_targets[state]
    target_off = target - IMAGE_BASE
    insns = disasm_at(target_off, 48)
    
    code_str = ""
    transition = ""
    input_check = ""
    new_state = "?"
    
    for insn in insns[:8]:
        if insn.mnemonic == 'cmp' and 'r1,' in insn.op_str:
            try:
                val = int(insn.op_str.split('#')[1].strip(), 0)
                input_check = f"byte==0x{val:02X}"
            except:
                pass
        if insn.mnemonic == 'bne':
            pass
        if insn.mnemonic == 'movs' and insn.op_str.startswith('r3,') and '#' in insn.op_str:
            try:
                val = int(insn.op_str.split('#')[1].strip(), 0)
                new_state = f"{val} (0x{val:02X})"
            except:
                pass
        if insn.mnemonic == 'strb' and insn.op_str == '[r0]':
            transition = f"-> state {new_state}"
        if insn.mnemonic == 'strh' and insn.op_str == '[r0]':
            transition = f"-> states {new_state}"
        code_str += f"{insn.mnemonic} {insn.op_str}; "
    
    print(f"  {state:3d}  0x{target:08X}   {code_str[:70]:70s}  {input_check} {transition}")

# ================================================================
# Now let's trace the ACTUAL SysEx parsing flow
# ================================================================
print("\n" + "=" * 80)
print("SYSEX BYTE-BY-BYTE PARSING FLOW")
print("=" * 80)

# Let's carefully analyze each state handler
# by looking at what byte value (r1) each state checks

# State 1 -> checks r1 for specific byte
# From the dispatch table and code:
# State 1 target = look at code

print("\nDetailed state analysis:")
for state in range(1, 44):
    target = state_targets[state]
    target_off = target - IMAGE_BASE
    insns = disasm_at(target_off, 80)
    
    print(f"\n  State {state} (0x{state:02X}) @ 0x{target:08X}:")
    
    for i, insn in enumerate(insns[:15]):
        annotation = ""
        if insn.mnemonic == 'cmp' and 'r1,' in insn.op_str:
            try:
                val = int(insn.op_str.split('#')[1].strip(), 0)
                annotation = f"  ; check input byte == 0x{val:02X} ({val})"
            except:
                pass
        if insn.mnemonic == 'cmp' and 'r3,' in insn.op_str:
            try:
                val = int(insn.op_str.split('#')[1].strip(), 0)
                annotation = f"  ; compare with 0x{val:02X}"
            except:
                pass
        if insn.mnemonic == 'movs' and 'r3,' in insn.op_str and '#' in insn.op_str:
            try:
                val = int(insn.op_str.split('#')[1].strip(), 0)
                annotation = f"  ; r3 = {val} (0x{val:02X})"
            except:
                pass
        if insn.mnemonic == 'strb' and insn.op_str == '[r0]':
            annotation = "  ; SET STATE"
        if insn.mnemonic == 'strb' and insn.op_str.startswith('[r0'):
            annotation = "  ; store byte"
        if insn.mnemonic == 'b' and insn.op_str.startswith('0x'):
            annotation = f"  ; goto handler"
        if insn.mnemonic == 'bl':
            annotation = f"  ; CALL"
        if insn.mnemonic == 'blx':
            annotation = f"  ; INDIRECT CALL"
        
        print(f"    0x{insn.address:08X}: {insn.mnemonic:8s} {insn.op_str}{annotation}")
        
        if insn.mnemonic == 'b' and not insn.op_str.startswith('#'):
            break
        if insn.mnemonic == 'pop' and 'pc' in insn.op_str:
            break
