#!/usr/bin/env python3
"""
MiniFreak CM4 SysEx Protocol Handler Analysis
Analyzes Arturia SysEx ID (0x00 0x20 0x6B) references in the firmware binary.
"""

import struct
from capstone import *

BINARY_PATH = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
IMAGE_BASE = 0x08120000

# Known literal pool offsets containing [0x00, 0x20, 0x6B]
SYSEX_ID_OFFSETS = [
    0x0A7E8,
    0x152B8,
    0x18D38,
    0x1DA24,
    0x377C8,
    0x37BE0,
]

def load_binary():
    with open(BINARY_PATH, "rb") as f:
        return f.read()

def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]

def read_u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]

def disasm_range(data, start_offset, end_offset, base_addr=None):
    """Disassemble a range of bytes as Thumb-2 code."""
    if base_addr is None:
        base_addr = IMAGE_BASE + start_offset
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    md.skipdata = True
    code = data[start_offset:end_offset]
    results = []
    for insn in md.disasm(code, base_addr):
        results.append(insn)
    return results

def find_function_start(data, ref_offset, max_scan_back=0x400):
    """
    Scan backwards from ref_offset to find function entry point.
    Look for PUSH {rX, ...} or similar prologue patterns.
    Also look for the literal pool reference (LDR Rx, [PC, #imm]).
    """
    # ARM Thumb functions are typically 2-byte aligned
    # Function prologues often start with PUSH
    # Also look for preceding literal pool markers or alignment
    
    candidates = []
    start = max(0, ref_offset - max_scan_back)
    
    # Ensure even alignment
    if start % 2 != 0:
        start -= 1
    
    # Scan for PUSH instructions and literal pool references
    insns = disasm_range(data, start, ref_offset + 4)
    
    push_addrs = []
    ldr_refs = []
    
    for i, insn in enumerate(insns):
        # Look for PUSH instructions (function prologues)
        if insn.mnemonic == 'push':
            push_addrs.append((i, insn))
        # Look for LDR Rx, [PC, #imm] that references our target
        if insn.mnemonic == 'ldr' and '[pc' in insn.op_str.lower():
            ldr_refs.append((i, insn))
    
    return insns, push_addrs, ldr_refs

def find_literal_reference(data, target_offset, search_range=0x200):
    """
    Find instructions that reference the literal at target_offset via PC-relative LDR.
    In Thumb mode, LDR Rx, [PC, #imm] where PC = (current_addr + 4) & ~3
    """
    start = max(0, target_offset - search_range)
    results = []
    
    insns = disasm_range(data, start, target_offset)
    
    for insn in insns:
        if insn.mnemonic == 'ldr' and 'pc' in insn.op_str.lower():
            # Calculate PC value (Thumb: PC = insn_addr + 4, aligned to 4)
            pc_val = (insn.address + 4) & ~3
            # Parse the offset
            try:
                op_str = insn.op_str.lower()
                # Format: rx, [pc, #offset]
                parts = op_str.split('#')
                if len(parts) >= 2:
                    offset_str = parts[1].strip().rstrip(']').strip()
                    if offset_str.startswith('0x'):
                        pc_offset = int(offset_str, 16)
                    else:
                        pc_offset = int(offset_str)
                    effective_addr = pc_val + pc_offset
                    effective_file_offset = effective_addr - IMAGE_BASE
                    if effective_file_offset == target_offset:
                        results.append(insn)
            except (ValueError, IndexError):
                pass
    
    return results

def scan_for_function_prologue(data, from_offset, max_back=0x600):
    """
    Scan backwards from from_offset looking for function prologues.
    Returns the most likely function start.
    """
    start = max(0, from_offset - max_back)
    if start % 2 != 0:
        start -= 1
    
    insns = disasm_range(data, start, from_offset + 4)
    
    best_push = None
    # Look for PUSH with LR (typical function entry)
    for i, insn in enumerate(insns):
        if insn.mnemonic == 'push':
            # Prefer push that includes lr (function entry)
            if 'lr' in insn.op_str.lower():
                best_push = (i, insn)
            elif best_push is None:
                best_push = (i, insn)
    
    return insns, best_push

def find_function_end(data, start_offset, max_forward=0x800):
    """
    Find function end by looking for POP or BX LR.
    """
    end = min(len(data), start_offset + max_forward)
    insns = disasm_range(data, start_offset, end)
    
    for i, insn in enumerate(insns):
        if insn.mnemonic == 'pop' and 'pc' in insn.op_str.lower():
            return insn.address + insn.size - IMAGE_BASE, insns[:i+1]
        if insn.mnemonic == 'bx' and 'lr' in insn.op_str.lower():
            # Check if this is likely the function return
            return insn.address + insn.size - IMAGE_BASE, insns[:i+1]
    
    return end, insns

def analyze_branch_targets(insns, func_start_addr):
    """Analyze branch targets to find switch/case patterns."""
    branches = {}
    for insn in insns:
        if insn.mnemonic in ('b', 'bne', 'beq', 'bgt', 'blt', 'bge', 'ble', 'bhi', 'blo', 'bhs', 'bls', 'bne', 'cbz', 'cbnz'):
            try:
                target = int(insn.op_str.replace('#', ''), 0) if insn.op_str.startswith('#') or insn.op_str.startswith('0') else None
                if insn.mnemonic == 'b' and insn.op_str.startswith('0x'):
                    target = int(insn.op_str, 16)
                if target:
                    branches.setdefault(target, []).append(insn)
            except:
                pass
    return branches

def format_insn(insn):
    return f"  0x{insn.address:08X}:  {insn.mnemonic:8s} {insn.op_str}"

def main():
    data = load_binary()
    print(f"Binary size: {len(data)} bytes (0x{len(data):X})")
    print(f"Image base: 0x{IMAGE_BASE:08X}")
    print()
    
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    md.skipdata = True
    
    # ========================================
    # Phase 1: Find literal references
    # ========================================
    print("=" * 80)
    print("PHASE 1: Finding instructions that reference SysEx ID literals")
    print("=" * 80)
    
    ref_info = []
    
    for offset in SYSEX_ID_OFFSETS:
        addr = IMAGE_BASE + offset
        # Read the literal pool value(s) at this offset
        val = read_u32(data, offset)
        print(f"\n--- Literal at offset 0x{offset:05X} (addr 0x{addr:08X}) ---")
        print(f"  Literal value: 0x{val:08X}")
        
        # Check surrounding bytes for context
        context = data[offset:offset+16]
        print(f"  Context bytes: {' '.join(f'{b:02X}' for b in context)}")
        
        # Find instructions referencing this literal
        refs = find_literal_reference(data, offset, search_range=0x200)
        
        if refs:
            for ref in refs:
                print(f"  Referenced by: {format_insn(ref)}")
                ref_info.append((offset, ref))
        else:
            # Try wider search
            refs = find_literal_reference(data, offset, search_range=0x400)
            if refs:
                for ref in refs:
                    print(f"  Referenced by (wide): {format_insn(ref)}")
                    ref_info.append((offset, ref))
            else:
                print(f"  No direct PC-relative LDR reference found - checking MOVW/MOVT...")
                # Search for MOVW/MOVT pairs
                start = max(0, offset - 0x400)
                insns = disasm_range(data, start, offset)
                for insn in insns:
                    if insn.mnemonic in ('movw', 'movt'):
                        print(f"  Candidate: {format_insn(insn)}")
                        ref_info.append((offset, insn))
    
    # ========================================
    # Phase 2: Analyze each reference site
    # ========================================
    print("\n" + "=" * 80)
    print("PHASE 2: Disassembling functions around each reference")
    print("=" * 80)
    
    for lit_offset in SYSEX_ID_OFFSETS:
        lit_addr = IMAGE_BASE + lit_offset
        
        # Find the referencing instruction
        refs = find_literal_reference(data, lit_offset, search_range=0x300)
        if not refs:
            refs = find_literal_reference(data, lit_offset, search_range=0x500)
        
        if not refs:
            print(f"\n### Offset 0x{lit_offset:05X}: No reference found, scanning area directly ###")
            # Just disassemble around the area
            area_start = max(0, lit_offset - 0x100)
            insns = disasm_range(data, area_start, lit_offset + 0x100)
            print(f"Disassembly around 0x{lit_offset:05X}:")
            # Find the closest push to our literal
            for i, insn in enumerate(insns):
                if insn.address >= lit_addr - 0x100 and insn.address <= lit_addr + 0x50:
                    marker = " <<<" if insn.address == lit_addr else ""
                    print(f"  0x{insn.address:08X}: {insn.mnemonic:8s} {insn.op_str}{marker}")
            continue
        
        ref_insn = refs[0]
        ref_offset = ref_insn.address - IMAGE_BASE
        
        print(f"\n### Offset 0x{lit_offset:05X} (referenced at 0x{ref_insn.address:08X}) ###")
        
        # Find function prologue
        insns, best_push = scan_for_function_prologue(data, ref_offset, max_back=0x400)
        
        if best_push:
            func_start_i, func_start_insn = best_push
            func_start_offset = func_start_insn.address - IMAGE_BASE
            print(f"  Function prologue at 0x{func_start_insn.address:08X}: {func_start_insn.mnemonic} {func_start_insn.op_str}")
            
            # Find function end
            end_offset, func_insns = find_function_end(data, func_start_offset, max_forward=0x1000)
            end_addr = IMAGE_BASE + end_offset
            print(f"  Function range: 0x{func_start_insn.address:08X} - 0x{end_addr:08X} ({end_offset - func_start_offset} bytes)")
            print(f"  Instructions: {len(func_insns)}")
            
            # Print the full disassembly
            print(f"\n  Full disassembly:")
            for insn in func_insns:
                marker = ""
                if insn.address == ref_insn.address:
                    marker = "  <<< SYSEX ID REF"
                elif insn.address == lit_addr:
                    marker = "  <<< LITERAL POOL"
                print(f"    0x{insn.address:08X}: {insn.mnemonic:8s} {insn.op_str}{marker}")
            
            # Analyze for comparison/dispatch patterns
            print(f"\n  Comparison/dispatch analysis:")
            for insn in func_insns:
                # Look for comparison with constants (message type checks)
                if insn.mnemonic in ('cmp', 'cmn') and ('#' in insn.op_str or '0x' in insn.op_str):
                    print(f"    {format_insn(insn)}  <<< possible message type check")
                # Look for conditional branches
                if insn.mnemonic in ('beq', 'bne', 'blt', 'bgt', 'ble', 'bge', 'bhi', 'blo', 'bhs', 'bls'):
                    print(f"    {format_insn(insn)}  <<< conditional branch")
                # Look for BL (function calls)
                if insn.mnemonic == 'bl':
                    print(f"    {format_insn(insn)}  <<< function call")
                # Look for TBB/TBH (table branch - switch statements)
                if insn.mnemonic in ('tbb', 'tbh'):
                    print(f"    {format_insn(insn)}  <<< TABLE BRANCH (switch/case)")
                # Look for byte loads that might be parsing SysEx
                if insn.mnemonic == 'ldrb':
                    print(f"    {format_insn(insn)}")
        else:
            print(f"  No clear function prologue found. Disassembling area around reference:")
            area_start = max(0, ref_offset - 0x80)
            area_end = min(len(data), ref_offset + 0x100)
            insns = disasm_range(data, area_start, area_end)
            for insn in insns:
                marker = ""
                if insn.address == ref_insn.address:
                    marker = "  <<< REF"
                print(f"    0x{insn.address:08X}: {insn.mnemonic:8s} {insn.op_str}{marker}")
    
    # ========================================
    # Phase 3: Search for relevant strings
    # ========================================
    print("\n" + "=" * 80)
    print("PHASE 3: Searching for MIDI/SysEx/preset strings")
    print("=" * 80)
    
    search_terms = [b'MIDI', b'SysEx', b'sysex', b'SYSEX', b'preset', b'Preset', b'PRESET',
                    b'Midi', b'midi', b'firmware', b'Firmware']
    
    for term in search_terms:
        pos = 0
        found = []
        while True:
            pos = data.find(term, pos)
            if pos == -1:
                break
            # Get context
            ctx_start = max(0, pos - 4)
            ctx_end = min(len(data), pos + len(term) + 32)
            ctx = data[ctx_start:ctx_end]
            # Check if it's a printable string
            try:
                # Extract the full string
                str_start = pos
                while str_start > 0 and data[str_start-1] >= 0x20 and data[str_start-1] < 0x7f:
                    str_start -= 1
                str_end = pos
                while str_end < len(data) and data[str_end] >= 0x20 and data[str_end] < 0x7f:
                    str_end += 1
                full_str = data[str_start:str_end].decode('ascii', errors='replace')
                addr = IMAGE_BASE + str_start
                found.append((pos, addr, full_str))
            except:
                pass
            pos += 1
        
        if found:
            print(f"\n  '{term.decode()}' occurrences:")
            seen = set()
            for offset, addr, s in found:
                if s not in seen and len(s) > 3:
                    seen.add(s)
                    # Truncate long strings
                    display = s[:80] + ('...' if len(s) > 80 else '')
                    print(f"    0x{offset:05X} (0x{addr:08X}): \"{display}\"")

    # ========================================
    # Phase 4: Deeper analysis of SysEx dispatch
    # ========================================
    print("\n" + "=" * 80)
    print("PHASE 4: SysEx message type dispatch analysis")
    print("=" * 80)
    
    # For each reference site, look more carefully at the byte-level parsing
    for lit_offset in SYSEX_ID_OFFSETS:
        lit_addr = IMAGE_BASE + lit_offset
        
        refs = find_literal_reference(data, lit_offset, search_range=0x300)
        if not refs:
            refs = find_literal_reference(data, lit_offset, search_range=0x500)
        if not refs:
            continue
        
        ref_insn = refs[0]
        ref_offset = ref_insn.address - IMAGE_BASE
        
        # Get a wider function context
        insns_all, best_push = scan_for_function_prologue(data, ref_offset, max_back=0x600)
        
        if not best_push:
            continue
        
        func_start_offset = best_push[1].address - IMAGE_BASE
        end_offset, func_insns = find_function_end(data, func_start_offset, max_forward=0x2000)
        
        print(f"\n--- Dispatch analysis for function at 0x{best_push[1].address:08X} ---")
        
        # Look for byte comparisons that would be checking SysEx message type byte
        # Typical pattern: load byte from buffer at offset 5 (after F0 00 20 6B dev type)
        cmp_values = []
        for insn in func_insns:
            if insn.mnemonic == 'cmp' and '#' in insn.op_str:
                try:
                    val_str = insn.op_str.split('#')[1].strip()
                    if val_str.startswith('0x'):
                        val = int(val_str, 16)
                    else:
                        val = int(val_str)
                    cmp_values.append((insn, val))
                except:
                    pass
        
        if cmp_values:
            print(f"  Comparison values (potential message types):")
            for insn, val in cmp_values:
                print(f"    0x{insn.address:08X}: CMP with 0x{val:02X} ({val}) - {insn.op_str}")

if __name__ == "__main__":
    main()
