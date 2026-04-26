"""
Phase 11: Gap Fill Scan — MANUAL_VS_FIRMWARE_MATCH.md에서 누락된 항목의 펌웨어 증거 추출
대상: CM4 바이너리 (문자열/enum 스캔), FX 코어 바이너리

누락 항목:
1. LFO 9파형 문자열 (Sin, Tri, Saw, Sqr, SnH, SlewSNH, ExpSaw, ExpRamp, Shaper)
2. Voice Mode enum (Mono, Poly, Unison, Para, Dual)
3. Arp 8모드 펌웨어 enum (Up, Down, UpDown, Rand, Walk, Pattern, Order, Poly)
4. Sequencer 64-step + 4 lane 증거
5. FX 13타입 (Delay, Vocoder Ext In 포함)
"""

import struct
import os

# ============ CONFIG ============
CM4_PATH = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
FX_PATH = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_fx__fw1_0_0_2229__2025_06_18.bin"
CM7_PATH = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin"
CM4_BASE = 0x08120000
FX_BASE = 0x08000000
CM7_BASE = 0x08000000

def load_binary(path):
    with open(path, "rb") as f:
        return f.read()

def extract_full_cluster(fw, start_off, max_entries=200, gap_threshold=48):
    results = []
    pos = start_off
    prev_end = start_off
    for _ in range(max_entries):
        if pos >= len(fw):
            break
        while pos < len(fw) and fw[pos] == 0:
            pos += 1
        if pos >= len(fw):
            break
        if pos > prev_end and (pos - prev_end) > gap_threshold:
            break
        null_pos = fw.find(b'\x00', pos)
        if null_pos == -1:
            break
        raw = fw[pos:null_pos]
        if len(raw) > 0 and all(32 <= b < 127 for b in raw):
            results.append((pos, raw.decode('ascii')))
            prev_end = null_pos
            pos = null_pos + 1
        else:
            break
    return results

def find_all_strings(fw, search_str, min_before=256, min_after=256):
    results = []
    pos = 0
    while True:
        pos = fw.find(search_str.encode('ascii'), pos)
        if pos == -1:
            break
        # Get context: extract cluster around this position
        cluster_before = extract_full_cluster(fw, max(0, pos - min_before), max_entries=100, gap_threshold=32)
        cluster_after = extract_full_cluster(fw, pos, max_entries=100, gap_threshold=32)
        # Combine and deduplicate
        all_entries = {}
        for off, name in cluster_before + cluster_after:
            all_entries[off] = name
        sorted_entries = sorted(all_entries.items())
        results.append({
            "search": search_str,
            "file_offset": pos,
            "address": "0x{:08X}".format(pos + CM4_BASE),
            "cluster": [(off + CM4_BASE, name) for off, name in sorted_entries]
        })
        pos += 1
    return results

def search_multiple_targets(fw, targets):
    for target in targets:
        results = find_all_strings(fw, target, min_before=128, min_after=128)
        for r in results:
            print("=== Found '{}' @ {} ===".format(r["search"], r["address"]))
            for addr, name in r["cluster"]:
                print("  0x{:08X}: {}".format(addr, name))
            print()

# ============ MAIN ============
print("=" * 70)
print("PHASE 11: GAP FILL SCAN")
print("=" * 70)

cm4 = load_binary(CM4_PATH)
fx = load_binary(FX_PATH)
cm7 = load_binary(CM7_PATH)

print("\nCM4 size: {} bytes".format(len(cm4)))
print("FX size: {} bytes".format(len(fx)))
print("CM7 size: {} bytes".format(len(cm7)))

# ============ 1. LFO WAVEFORMS ============
print("\n" + "=" * 70)
print("1. LFO WAVEFORMS")
print("=" * 70)

lfo_targets = ["Sin", "SlewSNH", "ExpSaw", "ExpRamp", "Shaper"]
search_multiple_targets(cm4, lfo_targets)

# Also search for LFO-related clusters
print("\n--- LFO Wave enum cluster search ---")
for keyword in [b"LFO1 Wave", b"LFO2 Wave", b"Lfo Wave"]:
    pos = cm4.find(keyword)
    if pos >= 0:
        cluster = extract_full_cluster(cm4, max(0, pos - 64), max_entries=50, gap_threshold=32)
        print("Found '{}' @ 0x{:08X}:".format(keyword.decode('ascii', errors='replace'), pos + CM4_BASE))
        for off, name in cluster:
            print("  0x{:08X}: {}".format(off + CM4_BASE, name))
        print()

# ============ 2. VOICE MODE ============
print("\n" + "=" * 70)
print("2. VOICE MODE")
print("=" * 70)

voice_targets = ["Poly", "Mono", "Unison", "Para", "Dual"]
# Search near the known Voice Mode enum address
vm_addr = 0x081AF4F4
vm_off = vm_addr - CM4_BASE
if 0 < vm_off < len(cm4):
    cluster = extract_full_cluster(cm4, vm_off, max_entries=30, gap_threshold=48)
    print("Voice Mode enum @ 0x081AF4F4 (from PHASE8_SEQ_ARP_MOD.md):")
    for off, name in cluster:
        print("  0x{:08X}: {}".format(off + CM4_BASE, name))

# Also search for Voice Mode strings
print("\n--- Voice Mode string search ---")
for keyword in [b"Voice Mode", b"Unison Mode", b"Unison Count", b"Poly Alloc"]:
    pos = 0
    while True:
        pos = cm4.find(keyword, pos)
        if pos == -1:
            break
        cluster = extract_full_cluster(cm4, pos, max_entries=20, gap_threshold=32)
        print("Found '{}' @ 0x{:08X}:".format(keyword.decode('ascii', errors='replace'), pos + CM4_BASE))
        for off, name in cluster:
            print("  0x{:08X}: {}".format(off + CM4_BASE, name))
        print()
        pos += 1

# ============ 3. ARP MODES ============
print("\n" + "=" * 70)
print("3. ARPEGGIATOR MODES")
print("=" * 70)

arp_addr = 0x081AED6C
arp_off = arp_addr - CM4_BASE
if 0 < arp_off < len(cm4):
    cluster = extract_full_cluster(cm4, arp_off, max_entries=30, gap_threshold=48)
    print("Arp Mode enum @ 0x081AED6C (from PHASE8_SEQ_ARP_MOD.md):")
    for off, name in cluster:
        print("  0x{:08X}: {}".format(off + CM4_BASE, name))

# Search for Arp enum strings
print("\n--- Arp Mode string search ---")
for keyword in [b"Arp Up", b"Arp Down", b"Arp Rand", b"Arp Walk", b"Arp Pattern", b"Arp Order", b"Arp Poly"]:
    pos = 0
    while True:
        pos = cm4.find(keyword, pos)
        if pos == -1:
            break
        print("  Found '{}' @ 0x{:08X}".format(keyword.decode('ascii', errors='replace'), pos + CM4_BASE))
        pos += 1

# ============ 4. SEQUENCER ============
print("\n" + "=" * 70)
print("4. SEQUENCER")
print("=" * 70)

seq_keywords = [b"64 Step", b"64 step", b"Mod Lane", b"Mod Seq", b"Step Seq", b"Seq Step", b"Smooth Mod"]
for keyword in seq_keywords:
    pos = 0
    count = 0
    while True:
        pos = cm4.find(keyword, pos)
        if pos == -1:
            break
        count += 1
        if count <= 3:
            cluster = extract_full_cluster(cm4, max(0, pos - 32), max_entries=10, gap_threshold=32)
            print("Found '{}' @ 0x{:08X} (count={})".format(keyword.decode('ascii', errors='replace'), pos + CM4_BASE, count))
            for off, name in cluster:
                print("  0x{:08X}: {}".format(off + CM4_BASE, name))
        pos += 1
    if count > 3:
        print("  ... ({} total occurrences)".format(count))
    if count == 0:
        print("  '{}' NOT FOUND".format(keyword.decode('ascii', errors='replace')))
    print()

# eSeqParams enum scan
print("--- eSeqParams enum (RTTI-based) ---")
rtti = b"set(eSeqParams"
pos = 0
while True:
    pos = cm4.find(rtti, pos)
    if pos == -1:
        break
    print("  Found '{}' @ 0x{:08X}".format(rtti.decode('ascii', errors='replace'), pos + CM4_BASE))
    pos += 1

# eSeqStepParams enum scan
rtti2 = b"set(eSeqStepParams"
pos = 0
while True:
    pos = cm4.find(rtti2, pos)
    if pos == -1:
        break
    print("  Found '{}' @ 0x{:08X}".format(rtti2.decode('ascii', errors='replace'), pos + CM4_BASE))
    pos += 1

# eSeqAutomParams enum scan
rtti3 = b"set(eSeqAutomParams"
pos = 0
while True:
    pos = cm4.find(rtti3, pos)
    if pos == -1:
        break
    print("  Found '{}' @ 0x{:08X}".format(rtti3.decode('ascii', errors='replace'), pos + CM4_BASE))
    pos += 1

# ============ 5. FX TYPES (FX core) ============
print("\n" + "=" * 70)
print("5. FX TYPES (FX core binary)")
print("=" * 70)

fx_keywords = [b"Chorus", b"Phaser", b"Flanger", b"Reverb", b"Delay", b"Distortion",
               b"BitCrusher", b"Bit Crusher", b"3 Bands", b"Peak EQ", b"Multi Comp",
               b"SuperUnison", b"Super Unison", b"Vocoder", b"Vocoder Self", b"Vocoder Ext"]

for keyword in fx_keywords:
    pos = fx.find(keyword)
    if pos >= 0:
        cluster = extract_full_cluster(fx, max(0, pos - 64), max_entries=30, gap_threshold=48)
        print("FX core: Found '{}' @ 0x{:08X}:".format(keyword.decode('ascii', errors='replace'), pos + FX_BASE))
        for off, name in cluster:
            print("  0x{:08X}: {}".format(off + FX_BASE, name))
        print()
    else:
        print("FX core: '{}' NOT FOUND".format(keyword.decode('ascii', errors='replace')))

# ============ 6. CM7 - Arp/LFO/Seq related constants ============
print("\n" + "=" * 70)
print("6. CM7 - Arp dispatch & LFO render confirmation")
print("=" * 70)

# Search CM7 for float constants related to LFO (PI, 2PI, phase wrapping)
# Already confirmed: PI x16, 2PI x6, 440Hz x12, 48000 x1
# Check for Arp-related: octave multipliers (0.5, 2.0), step patterns
# Check for Seq-related: step count constants (64), lane count (4)

import struct as st

# Count specific float constants in CM7
float_targets = {
    0x3f000000: "0.5 (-6dB/octave, half-note)",
    0x40000000: "2.0 (octave up)",
    0x40400000: "3.0 (3-voice avg)",
    0x40800000: "4.0 (4th, octave range max)",
    0x40a00000: "5.0 (5-case switch = arp)",
    0x41200000: "10.0",
    0x41a00000: "20.0",
    0x41c80000: "25.0 (Walk 25%)",
    0x42c80000: "100.0 (percent)",
    0x447a0000: "1000.0 (millisec)",
}

print("Float constants in CM7:")
for fval, desc in float_targets.items():
    packed = st.pack('<I', fval)
    count = 0
    pos = 0
    while True:
        pos = cm7.find(packed, pos)
        if pos == -1:
            break
        count += 1
        pos += 1
    if count > 0:
        print("  {} ({}) : {} occurrences".format(fval, desc, count))

# Integer constants: 64 (steps), 4 (lanes), 8 (arp modes), 9 (LFO waves), 6 (voices)
int_targets = {
    64: "64 (sequencer steps)",
    4: "4 (mod lanes, or octave range)",
    8: "8 (arp modes, LFO retrig)",
    9: "9 (LFO waveforms)",
    6: "6 (voices, unison max)",
    12: "12 (para voices)",
}

print("\nInteger constants (as 32-bit LE) in CM7:")
for ival, desc in int_targets.items():
    packed = st.pack('<I', ival)
    count = 0
    pos = 0
    while True:
        pos = cm7.find(packed, pos)
        if pos == -1:
            break
        count += 1
        pos += 1
    # Filter: only report if count is in a reasonable range (not too common)
    if 0 < count < 50:
        print("  {} ({}): {} occurrences".format(ival, desc, count))
    elif count >= 50:
        print("  {} ({}): {} occurrences (too common, filtered)".format(ival, desc, count))

# ============ 7. Smooth Mod Lane ============
print("\n" + "=" * 70)
print("7. MOD SEQ SMOOTH MOD (4 lanes)")
print("=" * 70)

smooth_addr = 0x081B1B8C
smooth_off = smooth_addr - CM4_BASE
if 0 < smooth_off < len(cm4):
    cluster = extract_full_cluster(cm4, smooth_off, max_entries=20, gap_threshold=48)
    print("Smooth Mod @ 0x081B1B8C (from PHASE8):")
    for off, name in cluster:
        print("  0x{:08X}: {}".format(off + CM4_BASE, name))

# ============ 8. CycEnv Stage Order ============
print("\n" + "=" * 70)
print("8. CYCENV STAGE ORDER")
print("=" * 70)

for keyword in [b"RHF", b"RFH", b"HRF", b"Rise", b"Fall", b"Hold", b"CycEnv", b"Cycling Env"]:
    pos = 0
    count = 0
    while True:
        pos = cm4.find(keyword, pos)
        if pos == -1:
            break
        count += 1
        pos += 1
    if count > 0:
        print("  '{}': {} occurrences".format(keyword.decode('ascii', errors='replace'), count))

print("\n--- CycEnv Mode enum cluster ---")
for keyword in [b"CycEnv Mode", b"Cyc Env Mode"]:
    pos = cm4.find(keyword)
    if pos >= 0:
        cluster = extract_full_cluster(cm4, pos, max_entries=20, gap_threshold=32)
        print("Found '{}' @ 0x{:08X}:".format(keyword.decode('ascii', errors='replace'), pos + CM4_BASE))
        for off, name in cluster:
            print("  0x{:08X}: {}".format(off + CM4_BASE, name))
        print()

# ============ SUMMARY ============
print("\n" + "=" * 70)
print("SCAN COMPLETE")
print("=" * 70)
