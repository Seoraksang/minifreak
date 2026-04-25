#!/usr/bin/env python3
"""
Phase 5: Analyze the SysEx BUILDER function at 0x3D8C4 and related functions.
Also analyze the function at 0x37BE0 (SysEx sender) in detail.
And the 0x38D38 function (MIDI dispatcher).
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
# 1. SysEx sender function at 0x8157BB8
# ====================================================================
print("=" * 80)
print("SYSEX SENDER FUNCTION at 0x8157BB8")
print("=" * 80)

# This function builds and sends a SysEx message
# It loads the Arturia ID and constructs the message

# Get the literal pool values
lit_pool_off = 0x37BE0
print(f"\nLiteral pool at 0x{IMAGE_BASE+lit_pool_off:08X}:")
for i in range(8):
    val = read_u32(data, lit_pool_off + i*4)
    print(f"  [{i}] 0x{val:08X}")

# The function:
# push {r4, r5, lr}
# ldr r2, [pc, #0x20]  -> literal at 0x37BE0 + some offset (pointer to counter)
# ldr r4, [pc, #0x20]  -> literal (Arturia ID: 0x096B2000 or 0x036B2000)
# ldr r1, [pc, #0x24]  -> literal (something else)
# sub sp, #0x14
# movw r5, #0x206      -> value 0x0206
# strd r1, r2, [sp, #8]  -> store on stack
# ldrd r0, r3, [r0, #4]   -> r0 = object->send_buf, r3 = object->send_func
# strd r5, r4, [sp]       -> store 0x206 and Arturia ID on stack
# mov r1, sp              -> r1 = pointer to stack buffer
# blx r3                  -> call send function
# add sp, #0x14
# pop {r4, r5, pc}

# So the message on the stack would be:
# sp[0..1] = 0x0206 (this is the message size? or 0x06, 0x02 bytes?)
# sp[4..7] = Arturia ID bytes (0x00, 0x20, 0x6B, 0x03 or 0x09)
# sp[8..11] = additional data (the literal at r1)
# sp[12..15] = counter pointer (r2)

# Wait - strd r5, r4, [sp] stores r5 at [sp] and r4 at [sp+4]
# So: [sp+0] = 0x206 (as 32-bit: 0x00000206), [sp+4] = 0x096B2000 or 0x036B2000

# Actually in little-endian:
# sp[0] = 0x06, sp[1] = 0x02, sp[2] = 0x00, sp[3] = 0x00
# sp[4] = 0x00, sp[5] = 0x20, sp[6] = 0x6B, sp[7] = 0x09 or 0x03

# This looks like the beginning of a SysEx header:
# F0 06 02 00 20 6B 09 ... (or with 0x03)

# But wait - the F0 isn't here. The caller must add it.
# The message buffer starts with:
# Byte 0: 0x06 (device ID?) 
# Byte 1: 0x02 (model ID?)
# Bytes 2-4: 0x00 0x20 0x6B (Arturia manufacturer ID)
# Byte 5: 0x09 or 0x03 (message operation?)

# Actually the literal at 0x37BE0 is 0x036B2000
# In bytes: 00 20 6B 03
# And movw r5, #0x206 gives: 06 02 00 00

# So the constructed buffer is:
# [0x06, 0x02, 0x00, 0x20, 0x6B, 0x03, ...]

# But wait - 0x206 as a halfword at sp[0] would be bytes 06 02
# And the 32-bit value at sp[4] = 0x036B2000 would be bytes 00 20 6B 03

# Combined 8 bytes: 06 02 00 20 6B 03 [ptr_low] [ptr_high]

# Actually looking at it differently:
# strd r5, r4, [sp] -> str r5, [sp]; str r4, [sp+4]
# r5 = 0x206 (stored as bytes: 06 02 00 00)  
# r4 = 0x036B2000 (stored as bytes: 00 20 6B 03)

# strd r1, r2, [sp, #8] -> str r1, [sp+8]; str r2, [sp+12]

print("""
SysEx message construction:
  Buffer at sp:
  [0x00]: 0x06 0x02 0x00 0x00  (movw r5 = 0x206)
  [0x04]: 0x00 0x20 0x6B 0x03  (Arturia ID + msg type)
  [0x08]: <r1 literal>          (additional param)
  [0x0C]: <r2 literal>          (counter pointer)
  
  Then called via: blx r3 where r3 = object->send_callback
  
  The full SysEx message would be:
  F0 [06 02] 00 20 6B 03 [params] F7
  where 06 = device ID, 02 = model/type, 00 20 6B = Arturia, 03 = operation
""")

# ====================================================================
# 2. SysEx BUILDER at 0x3D8C4 (builds outgoing SysEx messages)
# ====================================================================
print("=" * 80)
print("SYSEX MESSAGE BUILDER at 0x813D8C4")
print("=" * 80)

# This is the large function at 0x3D8C4 that builds SysEx messages
# with the Arturia ID, 7-bit MIDI encoding, etc.

insns = disasm(data, 0x3D8C4, 0x300)
print("\nKey sections of the SysEx builder function:")
for i, insn in enumerate(insns):
    annotation = ""
    if insn.mnemonic == 'ldr' and '[pc' in insn.op_str:
        annotation = " ; LITERAL POOL"
    elif insn.mnemonic == 'bl':
        annotation = " ; CALL"
    elif insn.mnemonic == 'blx':
        annotation = " ; INDIRECT CALL"
    elif insn.mnemonic == 'movw' and '#' in insn.op_str:
        annotation = " ; SET CONSTANT"
    elif insn.mnemonic == 'strb' and insn.op_str.startswith('[sp'):
        annotation = " ; STORE BYTE TO MSG BUF"
    elif insn.mnemonic == 'strh' and insn.op_str.startswith('[sp'):
        annotation = " ; STORE HALFWORD TO MSG BUF"
    elif '0x7f' in insn.op_str:
        annotation = " ; 7-BIT MASK (MIDI encoding)"
    elif 'lsl #7' in insn.op_str or 'lsl #8' in insn.op_str:
        annotation = " ; BYTE PACKING"
    elif 'lsr' in insn.op_str and '#7' in insn.op_str:
        annotation = " ; BYTE UNPACKING"
    elif insn.mnemonic == 'push' and 'lr' in insn.op_str:
        annotation = " ; FUNCTION ENTRY"
    
    print(f"  0x{insn.address:08X}: {insn.mnemonic:8s} {insn.op_str}{annotation}")

# ====================================================================
# 3. MIDI Dispatcher at 0x388AC (referenced from 0x38D38)
# ====================================================================
print("\n" + "=" * 80)
print("MIDI MESSAGE DISPATCHER at 0x81388AC")
print("=" * 80)

# This function handles incoming MIDI messages and routes them
# It checks MIDI status bytes (0xEF-0xF7 range = channel messages, system messages)

insns = disasm(data, 0x388AC, 0x120)
print("\nMIDI dispatcher function:")
for insn in insns:
    annotation = ""
    if insn.mnemonic == 'cmp' and '#' in insn.op_str:
        try:
            val = int(insn.op_str.split('#')[1].strip(), 0)
            if val == 0xEF:
                annotation = " ; Note On / highest channel voice msg"
            elif val == 0xF7:
                annotation = " ; SysEx End (F7)"
            elif val == 0xF2:
                annotation = " ; Song Position Pointer"
            elif val == 0xF1:
                annotation = " ; MIDI Time Code"
            elif val == 0x8000000:
                annotation = " ; flag bit (27)"
        except:
            pass
    elif insn.mnemonic == 'blx':
        annotation = " ; CALLBACK"
    elif insn.mnemonic == 'bl':
        annotation = " ; CALL"
    
    print(f"  0x{insn.address:08X}: {insn.mnemonic:8s} {insn.op_str}{annotation}")

# ====================================================================
# 4. Look at the function that handles preset parameters at 0x3501C
# ====================================================================
print("\n" + "=" * 80)
print("PARAMETER SET FUNCTION at 0x813501C")
print("=" * 80)

insns = disasm(data, 0x3501C, 0xA0)
print("\nParameter set function (called from SysEx handler):")
for insn in insns:
    annotation = ""
    if insn.mnemonic == 'cmp' and 'r4' in insn.op_str and '#' in insn.op_str:
        try:
            val = int(insn.op_str.split('#')[1].strip(), 0)
            annotation = f" ; check param index <= {val}"
        except:
            pass
    elif insn.mnemonic == 'bl':
        annotation = " ; CALL"
    elif insn.mnemonic == 'ldr' and '[pc' in insn.op_str:
        annotation = " ; LITERAL"
    
    print(f"  0x{insn.address:08X}: {insn.mnemonic:8s} {insn.op_str}{annotation}")

# ====================================================================
# 5. Analyze what the large SysEx parser function at 0x81572FC does
# after parsing - the dispatch on [r0+8] (message type)
# ====================================================================
print("\n" + "=" * 80)
print("MESSAGE TYPE DISPATCH (after SysEx header parsed)")
print("=" * 80)

# In state 9, after receiving the message type byte, the code at 0x81572FC
# dispatches based on the value in [r0+8] (which was stored in state 6)
# This is the main message type handler

# State 6 stores the message type byte in [r0+8] via: strb r1, [r0, #8]
# The message type value is the byte after F0 00 20 6B [dev_id] [msg_type]

# State 9 then checks [r0+8] to determine how to parse the rest:
# cmp r3, #0x0F -> type 0x0F (15)
# cmp r3, #0x23 -> type 0x23 (35)  
# cmp r3, #0x21 -> type 0x21 (33)
# sub r2, r3, #0x20; cmp r2, #1 -> type 0x20 or 0x21 (32 or 33)

# And there are more branches deeper in the state machine
# Let's look at the TBB tables for the inner dispatches

# The TBB at 0x81574CA and 0x8157638 are also interesting
# Let's decode the TBB table for state 12 (offset 0x375CA)

# State 12 has a TBB at 0x81575CA
# PC = 0x81575CE (address + 4)
# r2 = r3 - 2, where r3 is the message type from [r0+8]

print("\nTBB table analysis for state 12 (at 0x81575CA):")
tbb_base = 0x375CE  # PC + 4 for TBB at 0x81575CA
for idx in range(0x24):  # up to 0x23
    target_byte = data[tbb_base + idx]
    target = 0x81575CA + target_byte * 2  # TBB offset from TBB insn
    # Actually TBB targets are: TBB_insn_addr + 4 + target_byte*2? No...
    # TBB [pc, r2]: PC = insn_addr + 4, target = PC + table[r2]*2
    # But PC is aligned to 4 for TBB
    tbb_pc = (0x81575CA + 4) & ~3  # = 0x81575CC
    # Actually for TBB, PC = (insn_addr + 4) & ~3 only for PC-relative
    # The table is right after the TBB instruction
    target_addr = 0x81575CA + target_byte * 2
    print(f"  type {idx+2} (0x{idx+2:02X}): table[{idx}] = 0x{target_byte:02X} -> 0x{target_addr:08X}")

# State 10 also has a TBB at 0x8157606
print("\nTBB table analysis for state 10 (at 0x8157606):")
tbb_base = 0x3760A  # table starts after TBB
for idx in range(0x24):
    target_byte = data[tbb_base + idx]
    target_addr = 0x8157606 + target_byte * 2
    print(f"  type {idx+2} (0x{idx+2:02X}): table[{idx}] = 0x{target_byte:02X} -> 0x{target_addr:08X}")
