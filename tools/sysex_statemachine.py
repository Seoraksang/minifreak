#!/usr/bin/env python3
"""
Phase 3: Complete SysEx state machine mapping.
The function at 0x81572F8 is actually the function EPILOGUE (pop r4,pc).
The real loop body is at 0x81572FC onwards.

The code appears to be a state machine where r0->state_byte (offset 0) stores the current state,
and transitions happen based on received bytes in r1.

States are stored at r0 offsets:
- r0[0]: current state (byte)
- r0[1]: sub-state
- r0[2]: device ID / match byte
- r0[4]: buffer length / data offset
- r0[6]: counter
- r0[8]: type byte (signed)
- r0[9]: param index
- r0[0xA]: value
- r0[0xC]: 16-bit value
- r0[0xE]: byte
- r0[0x11]: byte
- r0[0x12]: 16-bit
- r0[0x14]: byte
- r0[0x15..]: data buffer
- r0[0xAA]: byte
- r0[0xAB]: byte
- r0[0xAC,0xB0]: function pointers
- r0[0x7A]: literal pool pointer (Arturia ID)
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

print("=" * 80)
print("COMPLETE SYSEX STATE MACHINE at 0x81572FC")
print("=" * 80)

# Disassemble the entire state machine function
# From 0x81572FC to the literal pool at 0x81577C8
insns = disasm(data, 0x372FC, 0x580)  # 0x372FC to ~0x3787C

# First, let's map all the state transitions
# The pattern is:
#   ldrsb.w r3, [r0, #8]   ; load current type/sub-state
#   cmp r3, #STATE_VALUE
#   beq/bne/bgt TARGET
#   ...
#   movs r3, #NEW_STATE
#   strb r3, [r0]          ; set new state
#   b #0x81572F8           ; return/loop

# Let's identify all state values that are written to [r0]
print("\nState transitions (strb r3, [r0] = new state):")
states = {}
for i, insn in enumerate(insns):
    if insn.mnemonic == 'strb' and insn.op_str.endswith('[r0]'):
        # Find the preceding movs/strb that sets r3
        for j in range(i-1, max(i-5, 0), -1):
            prev = insns[j]
            if prev.mnemonic == 'movs' and prev.op_str.startswith('r3,'):
                try:
                    val_str = prev.op_str.split('#')[1].strip()
                    val = int(val_str, 0)
                    new_state = val
                    # Find the cmp that led here
                    # Look back further for the condition
                    states.setdefault(new_state, [])
                    states[new_state].append(insn.address)
                    print(f"  0x{insn.address:08X}: State -> {new_state} (0x{new_state:02X})")
                except:
                    pass
                break
            elif prev.mnemonic == 'mov' and prev.op_str.startswith('r3,'):
                try:
                    val_str = prev.op_str.split('#')[1].strip()
                    val = int(val_str, 0)
                    new_state = val
                    states.setdefault(new_state, [])
                    states[new_state].append(insn.address)
                    print(f"  0x{insn.address:08X}: State -> {new_state} (0x{new_state:02X}) [mov]")
                except:
                    pass
                break

# Now let's build a complete picture by tracing the state machine
print("\n" + "=" * 80)
print("FULL STATE MACHINE TRACE")
print("=" * 80)

# Let's just print all the instructions with annotations
print("\nFull annotated disassembly (states in [brackets]):")

current_section = None
for i, insn in enumerate(insns):
    annotation = ""
    
    # Mark state reads
    if insn.mnemonic == 'ldrsb.w' and '#8]' in insn.op_str:
        annotation = " ; READ state/type from [r0+8]"
    elif insn.mnemonic == 'ldrsb.w' and '#4]' in insn.op_str:
        annotation = " ; READ buf_len from [r0+4]"
    
    # Mark state writes
    if insn.mnemonic == 'strb' and insn.op_str == '[r0]':
        # Look for the value being stored
        for j in range(i-1, max(i-4, 0), -1):
            prev = insns[j]
            if prev.mnemonic == 'movs' and prev.op_str.startswith('r3,'):
                try:
                    val = int(prev.op_str.split('#')[1].strip(), 0)
                    annotation = f" ; SET STATE = {val} (0x{val:02X})"
                except:
                    pass
                break
    
    # Mark comparisons with r1 (input byte)
    if insn.mnemonic == 'cmp' and insn.op_str.startswith('r1,'):
        try:
            val = int(insn.op_str.split('#')[1].strip(), 0)
            annotation = f" ; INPUT byte == 0x{val:02X} ({val})?"
        except:
            pass
    
    # Mark comparisons with r3 from [r0+8]
    if insn.mnemonic == 'cmp' and insn.op_str.startswith('r3,'):
        try:
            val = int(insn.op_str.split('#')[1].strip(), 0)
            annotation = f" ; compare state/type with 0x{val:02X} ({val})"
        except:
            pass
    
    # Mark function calls
    if insn.mnemonic == 'blx':
        annotation = " ; INDIRECT CALL"
    elif insn.mnemonic == 'bl':
        annotation = " ; FUNCTION CALL"
    
    # Mark returns
    if insn.mnemonic == 'pop' and 'pc' in insn.op_str:
        annotation = " ; RETURN"
    
    # Mark literal pool loads
    if insn.mnemonic == 'ldr' and '[pc' in insn.op_str:
        annotation = " ; LOAD FROM LITERAL POOL"
    
    print(f"  0x{insn.address:08X}: {insn.mnemonic:8s} {insn.op_str}{annotation}")

# ====================================================================
# Now let's also look at the function that CALLS this state machine
# to understand how bytes are fed to it
# ====================================================================
print("\n" + "=" * 80)
print("CALLER ANALYSIS - Who calls the state machine?")
print("=" * 80)

# Look for BL instructions targeting the function
func_addr = IMAGE_BASE + 0x372FC  # Approximate
# But the function entry is at 0x81572FC... no, let's find the actual entry

# The state machine has a "return" at 0x81572F8 (add sp, pop r4,pc)
# So the function prologue must be before that
# From our scan, PUSH {r4, lr} at 0x8157278 is the entry point
func_entry = 0x37278
func_entry_addr = IMAGE_BASE + func_entry

print(f"\nFunction entry point: 0x{func_entry_addr:08X}")

# Disassemble the entry
entry_insns = disasm(data, func_entry, 0x100)
for insn in entry_insns[:30]:
    annotation = ""
    if insn.mnemonic == 'bl':
        annotation = " ; CALL"
    print(f"  0x{insn.address:08X}: {insn.mnemonic:8s} {insn.op_str}{annotation}")

# Now search for BL to this function
print(f"\nSearching for calls to 0x{func_entry_addr:08X}...")
target_bytes = struct.pack("<I", func_entry_addr)
# BL in Thumb encodes the target differently - need to search through disassembly
# Let's search in a wider range for references

# Search for the function address in the binary
for match_offset in range(0, len(data) - 4):
    if data[match_offset:match_offset+4] == b'\x00\x20\x6b':
        pass  # Already known

# Instead, search for BL instructions targeting 0x8157278
# BL encoding in Thumb: first halfword = 0xF000 | ((offset>>12) & 0x7FF)
#                        second halfword = 0xD000 | ((offset>>1) & 0x7FF)
# But it's easier to just disassemble large chunks and look for BL

# Let's search for cross-references by scanning the whole binary
print("Scanning for BL instructions targeting the state machine...")
found_callers = []
for scan_start in range(0, len(data) - 4, 0x2000):
    chunk_insns = disasm(data, scan_start, min(0x2000, len(data) - scan_start))
    for insn in chunk_insns:
        if insn.mnemonic == 'bl' and insn.op_str == f'0x{func_entry_addr:08x}':
            found_callers.append(insn)
            print(f"  CALLER at 0x{insn.address:08X}")

# Also look for calls to 0x81572FC (the loop entry)
loop_entry_addr = IMAGE_BASE + 0x372FC
for scan_start in range(0, len(data) - 4, 0x2000):
    chunk_insns = disasm(data, scan_start, min(0x2000, len(data) - scan_start))
    for insn in chunk_insns:
        if insn.mnemonic == 'bl' and insn.op_str == f'0x{loop_entry_addr:08x}':
            found_callers.append(insn)
            print(f"  CALLER to loop at 0x{insn.address:08X}")

# Also check for BX to these addresses indirectly

print(f"\nTotal callers found: {len(found_callers)}")
