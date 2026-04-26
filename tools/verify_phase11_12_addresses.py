#!/usr/bin/env python3
"""
Verify all firmware address claims from Phase 11/12 documents against actual CM4 binary.
"""
import struct
import sys

BIN_PATH = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"

def load_bin(path):
    with open(path, "rb") as f:
        return f.read()

def extract_string(data, offset, max_len=80):
    """Extract null-terminated ASCII string at offset."""
    if offset >= len(data):
        return None, "OFFSET OUT OF RANGE"
    end = data.index(b'\x00', offset) if b'\x00' in data[offset:offset+max_len] else offset + max_len
    raw = data[offset:end]
    try:
        return raw.decode('ascii'), "OK"
    except UnicodeDecodeError:
        return repr(raw), "NOT ASCII"

def extract_strings_in_range(data, start, end):
    """Extract all null-terminated strings in a byte range."""
    strings = []
    pos = start
    while pos < end:
        if data[pos] == 0:
            pos += 1
            continue
        # Found start of a string
        null_pos = data.find(b'\x00', pos)
        if null_pos == -1 or null_pos > end:
            break
        raw = data[pos:null_pos]
        if len(raw) >= 1:
            try:
                s = raw.decode('ascii')
                if all(32 <= ord(c) < 127 for c in s):
                    strings.append((pos, s))
            except:
                pass
        pos = null_pos + 1
    return strings

def check_pointer(data, ptr_offset, target_strings):
    """Check if 32-bit little-endian pointer at ptr_offset points to any of target_strings."""
    if ptr_offset + 4 > len(data):
        return None
    val = struct.unpack_from('<I', data, ptr_offset)[0]
    for addr, s in target_strings:
        if val == addr:
            return (val, s)
    return (val, None)

def main():
    data = load_bin(BIN_PATH)
    size = len(data)
    print(f"CM4 binary size: {size} bytes ({size/1024:.1f} KB)")
    print(f"ARM vector table check: SP=0x{struct.unpack_from('<I', data, 0)[0]:08X}, Reset=0x{struct.unpack_from('<I', data, 4)[0]:08X}")
    print()
    
    # Check base address assumption
    # CM4 binary starts at file offset 0, but addresses like 0x081AEC3C suggest
    # the binary is loaded at some base address in memory.
    # File offset = address - base_address
    # We need to find the base address.
    # The reset vector is 0x00097678, suggesting code starts around 0x08000000 region
    # but the binary file is only 620KB. 
    # 0x081AEC3C - if base = 0x08000000, file offset = 0x001AEC3C = 1,767,676 > 620KB
    # That's too large. Let's try: the binary might be loaded at a different base.
    # File size = 620224 = 0x00097720
    # So addresses 0x081xxxxx can't be file offsets directly.
    # If the firmware is at 0x08000000, then offset in file = addr - 0x08000000
    # 0x081AEC3C - 0x08000000 = 0x001AEC3C = 1,767,676 > 620,224. Still too big.
    
    # Let's check: maybe the address space wraps differently.
    # Actually for STM32H7 (CM4), flash is at 0x08100000 for bank2 or 0x08000000 for bank1
    # Let's try base = 0x08100000:
    # 0x081AEC3C - 0x08100000 = 0x000AEC3C = 714,172 > 620,224. Still too big.
    
    # Hmm. Let's try to find a string in the binary and compute the offset.
    print("=" * 80)
    print("FINDING BASE ADDRESS")
    print("=" * 80)
    
    # Search for known strings in the binary
    test_strings = [b"Arp Up", b"Unison", b"Chorus", b"Sin", b"Tri"]
    for ts in test_strings:
        pos = data.find(ts)
        if pos != -1:
            print(f"  '{ts.decode()}' found at file offset 0x{pos:08X}")
    
    print()
    
    # Let's figure out the mapping. If "Arp Up" is claimed at 0x081AEC3C
    arp_pos = data.find(b"Arp Up\x00")
    if arp_pos != -1:
        claimed = 0x081AEC3C
        base = claimed - arp_pos
        print(f"  'Arp Up' at file offset 0x{arp_pos:08X}, claimed address 0x{claimed:08X}")
        print(f"  Implied base address: 0x{base:08X}")
        print()
        
        # Verify with another string
        uni_pos = data.find(b"Unison\x00")
        if uni_pos != -1:
            implied_addr = base + uni_pos
            print(f"  'Unison' at file offset 0x{uni_pos:08X}, implied address 0x{implied_addr:08X}")
            print(f"  Claimed address: 0x081AF500")
            if implied_addr == 0x081AF500:
                print(f"  ✅ MATCHES!")
            else:
                print(f"  ❌ MISMATCH (diff=0x{implied_addr - 0x081AF500:X})")
    
    print()
    print("=" * 80)
    print("SYSTEMATIC VERIFICATION OF ALL CLAIMED ADDRESSES")
    print("=" * 80)
    print()
    
    base = 0x081AEC3C - data.find(b"Arp Up\x00")
    
    def addr_to_offset(addr):
        off = addr - base
        if 0 <= off < len(data):
            return off
        return None
    
    def check_string_at_addr(claimed_addr, expected_str, tolerance=0):
        """Check if expected_str exists at claimed_addr."""
        off = addr_to_offset(claimed_addr)
        if off is None:
            return f"❌ OUT OF RANGE (file offset would be 0x{claimed_addr - base:08X}, file size=0x{len(data):08X})"
        actual, status = extract_string(data, off)
        if actual == expected_str:
            return f"✅ MATCH: '{actual}' @ file offset 0x{off:08X}"
        else:
            # Check nearby
            if tolerance > 0:
                for delta in range(-tolerance, tolerance+1):
                    if delta == 0:
                        continue
                    off2 = addr_to_offset(claimed_addr + delta)
                    if off2 is not None:
                        actual2, _ = extract_string(data, off2)
                        if actual2 == expected_str:
                            return f"⚠️ OFF BY {delta:+d}: '{actual2}' @ 0x{claimed_addr+delta:08X} (actual file offset 0x{off2:08X})"
            return f"❌ MISMATCH: expected '{expected_str}', got '{actual}' @ file offset 0x{off:08X}"
    
    # ========================================
    # 1. Arp Mode enum @ 0x081AEC3C
    # ========================================
    print("1. ARP MODE ENUM (claimed 0x081AEC3C ~ 0x081AEC8C)")
    print("-" * 60)
    arp_claims = [
        (0x081AEC3C, "Arp Up", 0),
        (0x081AEC44, "Arp Down", 1),
        (0x081AEC50, "Arp Up", 2),  # Phase 11 says "Up reused" for UpDown
        (0x081AEC5C, "Arp Rand", 3),
        (0x081AEC68, "Arp Walk", 4),
        (0x081AEC74, "Arp Pattern", 5),
        (0x081AEC80, "Arp Order", 6),
        (0x081AEC8C, "Arp Poly", 7),
    ]
    
    # Also check if "Arp UpDown" exists somewhere
    arp_upd_pos = data.find(b"Arp UpDown")
    if arp_upd_pos != -1:
        print(f"  NOTE: 'Arp UpDown' found at file offset 0x{arp_upd_pos:08X} (addr 0x{base + arp_upd_pos:08X})")
    else:
        print(f"  NOTE: 'Arp UpDown' NOT FOUND in binary (document claims 'Arp Up' reused for index 2)")
    
    for addr, expected, idx in arp_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  [{idx}] 0x{addr:08X} expected='{expected}': {result}")
    
    # Also dump what's actually in the range
    print()
    start_off = addr_to_offset(0x081AEC3C)
    end_off = addr_to_offset(0x081AECA0)
    if start_off and end_off:
        strs = extract_strings_in_range(data, start_off, end_off)
        print(f"  All strings in range 0x081AEC3C~0x081AECA0:")
        for off, s in strs:
            print(f"    0x{base + off:08X} (file 0x{off:08X}): '{s}'")
    
    # ========================================
    # 2. LFO Waveform enum @ 0x081B0FB0
    # ========================================
    print()
    print("2. LFO WAVEFORM ENUM (claimed 0x081B0FB0 ~ 0x081B0FDB)")
    print("-" * 60)
    lfo_claims = [
        (0x081B0FB0, "Sin", 0),
        (0x081B0FB4, "Tri", 1),
        # Saw at 0x081B0FB6 - shared
        (0x081B0FB8, "Sqr", 3),
        # SnH shared
        (0x081B0FBC, "SlewSNH", 5),
        (0x081B0FC4, "ExpSaw", 6),
        (0x081B0FCC, "ExpRamp", 7),
        (0x081B0FD4, "Shaper", 8),
    ]
    for addr, expected, idx in lfo_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  [{idx}] 0x{addr:08X} expected='{expected}': {result}")
    
    # Check for Saw and SnH
    for ts in [b"Saw\x00", b"SnH\x00"]:
        pos = data.find(ts)
        if pos != -1:
            print(f"  NOTE: '{ts.decode().strip(chr(0))}' found at file offset 0x{pos:08X} (addr 0x{base + pos:08X})")
    
    start_off = addr_to_offset(0x081B0FB0)
    end_off = addr_to_offset(0x081B0FE0)
    if start_off and end_off:
        strs = extract_strings_in_range(data, start_off, end_off)
        print(f"  All strings in range 0x081B0FB0~0x081B0FE0:")
        for off, s in strs:
            print(f"    0x{base + off:08X} (file 0x{off:08X}): '{s}'")
    
    # ========================================
    # 3. LFO Retrig modes @ 0x081B0E7C~0x081B0E88
    # ========================================
    print()
    print("3. LFO RETRIG MODES (claimed 0x081B0E3C ~ 0x081B0E88)")
    print("-" * 60)
    retrig_claims = [
        (0x081B0E7C, "Free", 0),
        (0x081B0E3C, "Poly Kbd", 1),
        (0x081B0E48, "Mono Kbd", 2),
        (0x081B0E54, "Legato Kbd", 3),
        (0x081B0E84, "One", 4),
        (0x081B0E60, "LFO1", 5),  # Note: Phase 11 says "LFO" but LFO1
        (0x081B0E70, "RHF", 6),   # Note: Phase 11 says "CycEnv (RHF cycle sync)" but actual string is "RHF"
        (0x081B0E88, "Seq Start", 7),
    ]
    for addr, expected, idx in retrig_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  [{idx}] 0x{addr:08X} expected='{expected}': {result}")
    
    start_off = addr_to_offset(0x081B0E3C)
    end_off = addr_to_offset(0x081B0E90)
    if start_off and end_off:
        strs = extract_strings_in_range(data, start_off, end_off)
        print(f"  All strings in range 0x081B0E3C~0x081B0E90:")
        for off, s in strs:
            print(f"    0x{base + off:08X} (file 0x{off:08X}): '{s}'")
    
    # ========================================
    # 4. Voice Mode @ 0x081AF500~0x081AF528
    # ========================================
    print()
    print("4. VOICE MODE (claimed 0x081AF500 ~ 0x081AF528)")
    print("-" * 60)
    voice_claims = [
        (0x081AF500, "Unison", "Voice Mode index 3"),
        (0x081AF508, "Uni (Poly)", "Unison 하위모드"),
        (0x081AF514, "Uni (Para)", "Unison 하위모드"),
        (0x081AF520, "Mono", "Voice Mode index 2"),
        (0x081AF528, "Para", "Voice Mode index 4"),
    ]
    for addr, expected, desc in voice_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}' ({desc}): {result}")
    
    # Check for Poly and Dual
    for ts in [b"Poly\x00", b"Dual\x00"]:
        pos = data.find(ts)
        count = 0
        positions = []
        search_from = 0
        while True:
            p = data.find(ts, search_from)
            if p == -1:
                break
            positions.append(p)
            count += 1
            search_from = p + 1
        if count > 0:
            print(f"  NOTE: '{ts.decode().strip(chr(0))}' found {count} times, first at file offset 0x{positions[0]:08X}")
        else:
            print(f"  NOTE: '{ts.decode().strip(chr(0))}' NOT FOUND in binary")
    
    # ========================================
    # 5. Poly Steal Mode @ 0x081B0F70~0x081B0FA4
    # ========================================
    print()
    print("5. POLY STEAL MODE (claimed 0x081B0F70 ~ 0x081B0FA4)")
    print("-" * 60)
    steal_claims = [
        (0x081B0F70, "None"),
        (0x081B0F78, "Cycle"),
        (0x081B0F80, "Reassign"),
        (0x081B0F8C, "Velocity"),
        (0x081B0F98, "Aftertouch"),
        (0x081B0FA4, "Velo + AT"),
    ]
    for addr, expected in steal_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    # Check for "Once" (manual mentions None/Once/Cycle/Reassign)
    once_pos = data.find(b"Once\x00")
    if once_pos != -1:
        print(f"  NOTE: 'Once' found at file offset 0x{once_pos:08X} (addr 0x{base + once_pos:08X})")
    
    # ========================================
    # 6. FX 13 type enum @ 0x081AF308~0x081AF37C
    # ========================================
    print()
    print("6. FX TYPE ENUM (claimed 0x081AF308 ~ 0x081AF37C)")
    print("-" * 60)
    fx_claims = [
        (0x081AF308, "Chorus", 0),
        (0x081AF310, "Phaser", 1),
        (0x081AF318, "Flanger", 2),
        (0x081AF320, "Reverb", 3),
        # Stereo Delay is separate at 0x081AE368
        (0x081AF328, "Distortion", 5),
        (0x081AF334, "Bit Crusher", 6),
        (0x081AF340, "3 Bands EQ", 7),
        (0x081AF34C, "Peak EQ", 8),
        (0x081AF354, "Multi Comp", 9),
        (0x081AF360, "SuperUnison", 10),
        (0x081AF36C, "Vocoder Self", 11),
        (0x081AF37C, "Vocoder Ext", 12),
    ]
    # Also check "Delay" at 0x081AE368
    delay_result = check_string_at_addr(0x081AE368, "Delay", tolerance=16)
    print(f"  [4] 0x081AE368 expected='Delay': {delay_result}")
    
    for addr, expected, idx in fx_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  [{idx}] 0x{addr:08X} expected='{expected}': {result}")
    
    # ========================================
    # 7. Shaper presets @ 0x081AF128~0x081AF288
    # ========================================
    print()
    print("7. SHAPER PRESETS (claimed 0x081AF128 ~ 0x081AF288, 20 types)")
    print("-" * 60)
    start_off = addr_to_offset(0x081AF128)
    end_off = addr_to_offset(0x081AF290)
    if start_off and end_off:
        strs = extract_strings_in_range(data, start_off, end_off)
        print(f"  Found {len(strs)} strings in range:")
        for i, (off, s) in enumerate(strs):
            print(f"    [{i}] 0x{base + off:08X} (file 0x{off:08X}): '{s}'")
    else:
        print(f"  ❌ Cannot map address range to file offsets")
    
    # ========================================
    # 8. CycEnv parameters @ 0x081AF840~0x081AF880
    # ========================================
    print()
    print("8. CYCENV PARAMETERS (claimed 0x081AF840 ~ 0x081AF880)")
    print("-" * 60)
    cycenv_claims = [
        (0x081AF840, "Mode"),
        (0x081AF848, "Hold"),
        (0x081AF850, "Rise Curve"),
        (0x081AF85C, "Fall Curve"),
        (0x081AF868, "Stage Order"),
        (0x081AF874, "Tempo Sync"),
        (0x081AF880, "Retrig Src"),
    ]
    for addr, expected in cycenv_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    # ========================================
    # 9. Mod Matrix sources @ 0x081B1BCC~0x081B1C1C
    # ========================================
    print()
    print("9. MOD MATRIX SOURCES (claimed 0x081B1BCC ~ 0x081B1C1C, 9 types)")
    print("-" * 60)
    mod_claims = [
        (0x081B1BCC, "Keyboard"),
        (0x081B1BD8, "LFO"),
        (0x081B1BDC, "Cycling Env"),
        (0x081B1BE8, "Env / Voice"),
        (0x081B1BF4, "Voice"),
        (0x081B1BFC, "Envelope"),
        (0x081B1C08, "FX"),
        (0x081B1C0C, "Sample Select"),
        (0x081B1C1C, "Wavetable Select"),
    ]
    for addr, expected in mod_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    start_off = addr_to_offset(0x081B1BC0)
    end_off = addr_to_offset(0x081B1C30)
    if start_off and end_off:
        strs = extract_strings_in_range(data, start_off, end_off)
        print(f"  All strings in range 0x081B1BC0~0x081B1C30:")
        for off, s in strs:
            print(f"    0x{base + off:08X} (file 0x{off:08X}): '{s}'")
    
    # ========================================
    # 10. Custom Assign destinations @ 0x081AEA94
    # ========================================
    print()
    print("10. CUSTOM ASSIGN DESTINATIONS (claimed around 0x081AEA94)")
    print("-" * 60)
    start_off = addr_to_offset(0x081AEA90)
    end_off = addr_to_offset(0x081AEB00)
    if start_off and end_off:
        strs = extract_strings_in_range(data, start_off, end_off)
        print(f"  All strings in range 0x081AEA90~0x081AEB00:")
        for off, s in strs:
            print(f"    0x{base + off:08X} (file 0x{off:08X}): '{s}'")
    
    # ========================================
    # 11. Tempo subdivisions @ 0x081AF0B4~0x081AF0FC
    # ========================================
    print()
    print("11. TEMPO SUBDIVISIONS (claimed 0x081AF0B4 ~ 0x081AF0FC)")
    print("-" * 60)
    start_off = addr_to_offset(0x081AF0B0)
    end_off = addr_to_offset(0x081AF100)
    if start_off and end_off:
        strs = extract_strings_in_range(data, start_off, end_off)
        print(f"  All strings in range 0x081AF0B0~0x081AF100:")
        for i, (off, s) in enumerate(strs):
            print(f"    [{i}] 0x{base + off:08X} (file 0x{off:08X}): '{s}'")
    
    # Additional tempo subdivisions @ 0x081AF564~0x081AF58C
    print()
    print("  Additional tempo subdivisions (claimed 0x081AF564 ~ 0x081AF58C):")
    start_off = addr_to_offset(0x081AF560)
    end_off = addr_to_offset(0x081AF590)
    if start_off and end_off:
        strs = extract_strings_in_range(data, start_off, end_off)
        for i, (off, s) in enumerate(strs):
            print(f"    [{i}] 0x{base + off:08X} (file 0x{off:08X}): '{s}'")
    
    # ========================================
    # 12. Multi Filter 14 modes @ 0x081B0D90~0x081B0DE8
    # ========================================
    print()
    print("12. MULTI FILTER 14 MODES (claimed 0x081B0D90 ~ 0x081B0DE8)")
    print("-" * 60)
    filter_claims = [
        (0x081B0D90, "LP36"),
        (0x081B0D98, "LP24"),
        (0x081B0DA0, "LP12"),
        (0x081B0DA8, "LP6"),
        (0x081B0DAC, "HP6"),
        (0x081B0DB0, "HP12"),
        (0x081B0DB8, "HP24"),
        (0x081B0DC0, "HP36"),
        (0x081B0DC8, "BP12"),
        (0x081B0DD0, "BP24"),
        (0x081B0DD8, "BP36"),
        (0x081B0DE0, "N12"),
        (0x081B0DE4, "N24"),
        (0x081B0DE8, "N36"),
    ]
    for addr, expected in filter_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    # ========================================
    # 13. Poly2Mono @ 0x081AE128
    # ========================================
    print()
    print("13. POLY2MONO (claimed 0x081AE128)")
    print("-" * 60)
    result = check_string_at_addr(0x081AE128, "Poly2Mono", tolerance=16)
    print(f"  0x081AE128 expected='Poly2Mono': {result}")
    
    # ========================================
    # 14. Multi Filter pointer table @ 0x081B1850
    # ========================================
    print()
    print("14. MULTI FILTER POINTER TABLE (claimed 0x081B1850 ~ 0x081B188C)")
    print("-" * 60)
    ptr_start = addr_to_offset(0x081B1850)
    ptr_end = addr_to_offset(0x081B1890)
    if ptr_start and ptr_end:
        # Read 32-bit pointers
        filter_target_addrs = [0x081B0D90, 0x081B0D98, 0x081B0DA0, 0x081B0DA8,
                               0x081B0DAC, 0x081B0DB0, 0x081B0DB8, 0x081B0DC0,
                               0x081B0DC8, 0x081B0DD0, 0x081B0DD8, 0x081B0DE0,
                               0x081B0DE4, 0x081B0DE8]
        print(f"  Reading {ptr_end - ptr_start} bytes of pointer data:")
        num_ptrs = (ptr_end - ptr_start) // 4
        matched = 0
        for i in range(num_ptrs):
            poff = ptr_start + i * 4
            val = struct.unpack_from('<I', data, poff)[0]
            # Check if this pointer points to any of our known filter strings
            target = None
            for fa in filter_target_addrs:
                if val == fa:
                    target = fa
                    break
            if target:
                off = addr_to_offset(val)
                s, _ = extract_string(data, off)
                matched += 1
                print(f"    [{i:2d}] 0x{base + poff:08X} -> 0x{val:08X} = '{s}' ✅")
            else:
                # Check if it points to a readable string
                if val >= base and val < base + len(data):
                    foff = val - base
                    if foff < len(data) and 32 <= data[foff] < 127:
                        s, _ = extract_string(data, foff)
                        print(f"    [{i:2d}] 0x{base + poff:08X} -> 0x{val:08X} = '{s}' (not a filter mode)")
                    else:
                        print(f"    [{i:2d}] 0x{base + poff:08X} -> 0x{val:08X} (not a string pointer)")
                else:
                    print(f"    [{i:2d}] 0x{base + poff:08X} -> 0x{val:08X} (out of binary range)")
        print(f"  Pointer match: {matched}/{len(filter_target_addrs)}")
    
    # ========================================
    # Additional Phase 12 specific claims
    # ========================================
    print()
    print("=" * 80)
    print("PHASE 12 SPECIFIC CLAIMS")
    print("=" * 80)
    
    # Vibrato claims
    print()
    print("VIBRATO STRINGS:")
    vib_claims = [
        (0x081AE3F8, "Vibrato On"),
        (0x081AE404, "Vibrato Off"),
        (0x081AEFB4, "Vibrato"),
        (0x081AF984, "Vibrato Depth"),
        (0x081AEAAC, "Vib Rate"),
        (0x081AEAB8, "Vib AM"),
    ]
    for addr, expected in vib_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    # Vibrato panel context
    print()
    print("VIBRATO PANEL CONTEXT (claimed 0x081AEFB4 area):")
    start_off = addr_to_offset(0x081AEFB0)
    end_off = addr_to_offset(0x081AEFE0)
    if start_off and end_off:
        strs = extract_strings_in_range(data, start_off, end_off)
        for off, s in strs:
            print(f"    0x{base + off:08X}: '{s}'")
    
    # Voice Envelope params
    print()
    print("VOICE ENVELOPE eEditParams (claimed 0x081AF7E0 ~ 0x081AF834):")
    env_claims = [
        (0x081AF7E0, "Env Amt"),
        (0x081AF7E8, "Attack"),
        (0x081AF7F0, "Decay"),
        (0x081AF7F8, "Release"),
        (0x081AF800, "Attack Curve"),
        (0x081AF810, "Decay Curve"),
        (0x081AF81C, "Velo > VCA"),
        (0x081AF828, "Velo > Env"),
        (0x081AF834, "Velo > Time"),
    ]
    for addr, expected in env_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    # VCF modes
    print()
    print("VCF MODES (claimed 0x081AF4D0 ~ 0x081AF4EC):")
    vcf_claims = [
        (0x081AF4D0, "LP"),
        (0x081AF4D4, "BP"),
        (0x081AF4D8, "HP"),
        (0x081AF4DC, "Notch"),
        (0x081AF4E4, "LP1"),
        (0x081AF4E8, "HP1"),
        (0x081AF4EC, "Notch2"),
    ]
    for addr, expected in vcf_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    # Deprecated params
    print()
    print("DEPRECATED PARAMS:")
    dep_claims = [
        (0x081AF994, "UnisonOn TO BE DEPRECATED"),
        (0x081AF70C, "old FX3 Routing"),
        (0x081AFB00, "obsolete Rec Count-In"),
        (0x081AF72C, "internal use only"),
    ]
    for addr, expected in dep_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    # LFO eEditParams
    print()
    print("LFO eEditParams (claimed 0x081AF88C ~ 0x081AF8F8):")
    lfo_params = [
        (0x081AF88C, "LFO1 Wave"),
        (0x081AF898, "LFO1 Sync En"),
        (0x081AF8A8, "LFO1 Sync Filter"),
        (0x081AF8BC, "LFO1 Retrig"),
        (0x081AF8C8, "LFO2 Wave"),
        (0x081AF8D4, "LFO2 Sync En"),
        (0x081AF8E4, "LFO2 Sync Filter"),
        (0x081AF8F8, "LFO2Retrig"),
    ]
    for addr, expected in lfo_params:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    # Sustain string
    print()
    print("SUSTAIN STRING (claimed 0x081AEBB8):")
    result = check_string_at_addr(0x081AEBB8, "Sustain", tolerance=16)
    print(f"  0x081AEBB8 expected='Sustain': {result}")
    # Also check "Percussive" nearby
    result2 = check_string_at_addr(0x081AEBA4, "Percussive", tolerance=16)
    print(f"  0x081AEBA4 expected='Percussive': {result2}")
    
    # Smooth Mod
    print()
    print("SMOOTH MOD (claimed 0x081B1B8C ~ 0x081B1BBC):")
    smooth_claims = [
        (0x081B1B8C, "Smooth Mod 4"),
        (0x081B1B9C, "Smooth Mod 3"),
        (0x081B1BAC, "Smooth Mod 2"),
        (0x081B1BBC, "Smooth Mod 1"),
    ]
    for addr, expected in smooth_claims:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    # Shaper Rate
    print()
    print("SHAPER RATE PARAMS:")
    for addr, expected in [(0x081AF544, "Shaper 1 Rate"), (0x081AF554, "Shaper 2 Rate")]:
        result = check_string_at_addr(addr, expected, tolerance=16)
        print(f"  0x{addr:08X} expected='{expected}': {result}")
    
    print()
    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
