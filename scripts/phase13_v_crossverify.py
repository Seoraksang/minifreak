#!/usr/bin/env python3
"""
Phase 13: V 매뉴얼 통합 재검증
VST XML + 펌웨어 바이너리 + mf_enums.py 3원 교차검증

CORR-01~10, ENH-01~12 전체 항목을 3가지 소스에서 교차 검증
"""

import struct
import os
import re
import json
import xml.etree.ElementTree as ET

BASE_DIR = os.path.expanduser("~/hoon/minifreak")
FW_CM4 = os.path.join(BASE_DIR, "reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin")
FW_CM7 = os.path.join(BASE_DIR, "reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin")
VST_XML = os.path.join(BASE_DIR, "reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/minifreak_vst_params.xml")
MF_ENUMS = os.path.join(BASE_DIR, "tools/mf_enums.py")

CM4_BASE = 0x08120000
CM7_BASE = 0x08020000

# ── Helper Functions ──

def read_string_at(fw_data, addr, base):
    """주소에서 null-terminated ASCII 문자열 읽기"""
    offset = addr - base
    if offset < 0 or offset >= len(fw_data):
        return None
    end = fw_data.find(b'\x00', offset)
    if end == -1:
        return None
    raw = fw_data[offset:end]
    if all(32 <= b < 127 for b in raw):
        return raw.decode('ascii')
    return None

def read_string_cluster(fw_data, start_addr, base, max_entries=100, gap=48):
    """주소에서 string cluster 추출"""
    results = []
    pos = start_addr - base
    prev_end = pos
    for _ in range(max_entries):
        if pos >= len(fw_data):
            break
        while pos < len(fw_data) and fw_data[pos] == 0:
            pos += 1
        if pos >= len(fw_data):
            break
        if pos > prev_end and (pos - prev_end) > gap:
            break
        null_pos = fw_data.find(b'\x00', pos)
        if null_pos == -1:
            break
        raw = fw_data[pos:null_pos]
        if len(raw) > 0 and all(32 <= b < 127 for b in raw):
            results.append((base + pos, raw.decode('ascii')))
            prev_end = null_pos
            pos = null_pos + 1
        else:
            break
    return results

def count_keyword(fw_data, keyword, base):
    """바이너리에서 키워드 출현 횟수 카운트"""
    count = 0
    pos = 0
    while True:
        pos = fw_data.find(keyword, pos)
        if pos == -1:
            break
        count += 1
        pos += 1
    return count

def verify_addr_string(fw_data, addr, base, expected):
    """특정 주소에서 문자열이 예상과 일치하는지 검증"""
    s = read_string_at(fw_data, addr, base)
    return s == expected, s

def parse_vst_xml_items(xml_path):
    """VST XML에서 모든 item_list의 name→items 매핑 추출"""
    if not os.path.exists(xml_path):
        return {}
    tree = ET.parse(xml_path)
    root = tree.getroot()
    result = {}
    for il in root.iter('item_list'):
        name = il.get('name', '')
        items = []
        for item in il.iter('item'):
            text = item.get('text', '')
            pval = item.get('processorvalue', '')
            items.append({'text': text, 'processorvalue': pval})
        if items:
            result[name] = items
    return result

def parse_vst_params(xml_path):
    """VST XML에서 모든 param 이름 추출"""
    if not os.path.exists(xml_path):
        return []
    tree = ET.parse(xml_path)
    root = tree.getroot()
    params = []
    for p in root.iter('param'):
        name = p.get('name', '')
        if name:
            params.append(name)
    return params

# ── Main ──

print("=" * 70)
print("Phase 13: V 매뉴얼 통합 재검증")
print("=" * 70)

# 바이너리 로드
with open(FW_CM4, "rb") as f:
    cm4 = f.read()
print(f"CM4 로드: {len(cm4)} bytes")

with open(FW_CM7, "rb") as f:
    cm7 = f.read()
print(f"CM7 로드: {len(cm7)} bytes")

# VST XML 파싱
vst_items = parse_vst_xml_items(VST_XML)
vst_params = parse_vst_params(VST_XML)
print(f"VST XML: {len(vst_items)} item_lists, {len(vst_params)} params")

# mf_enums.py 로드
with open(MF_ENUMS, "r") as f:
    enums_code = f.read()
print(f"mf_enums.py 로드: {len(enums_code)} bytes")
print()

# ═══════════════════════════════════════════════════════════════════
# Part 1: CORR-01~10 교차검증
# ═══════════════════════════════════════════════════════════════════

print("=" * 70)
print("Part 1: CORR (정정) 항목 교차검증")
print("=" * 70)

# ── CORR-01: Poly Steal Mode ──
print("\n--- CORR-01: Poly Steal Mode ---")
cluster = read_string_cluster(cm4, 0x081B0F70, CM4_BASE, max_entries=10, gap=24)
print(f"CM4 @ 0x081B0F70 cluster: {[s for _, s in cluster]}")
# mf_enums.py에서 POLY_STEAL_MODES 확인
steal_match = re.search(r'POLY_STEAL_MODES\s*=\s*\{([^}]+)\}', enums_code)
if steal_match:
    print(f"mf_enums.py POLY_STEAL_MODES: {steal_match.group(1)[:200]}")
# VST XML에서 Poly_Steal 검색
steal_vst = [p for p in vst_params if 'steal' in p.lower()]
print(f"VST params with 'steal': {steal_vst}")
steal_vst_items = {k: v for k, v in vst_items.items() if 'steal' in k.lower()}
print(f"VST item_lists with 'steal': {list(steal_vst_items.keys())}")

# ── CORR-02: Mod Matrix 소스 ──
print("\n--- CORR-02: Mod Matrix 소스 수량 ---")
cluster = read_string_cluster(cm4, 0x081B1BCC, CM4_BASE, max_entries=15, gap=48)
print(f"CM4 @ 0x081B1BCC cluster ({len(cluster)} items): {[s for _, s in cluster]}")
# mf_enums에서 mod source 확인
mod_match = re.findall(r'(?:MOD_SOURCES|MOD_SOURCE)\s*=\s*\{([^}]+)\}', enums_code)
for m in mod_match:
    print(f"mf_enums.py MOD_SOURCE: {m[:300]}")
# VST XML에서 Mod_Source 검색
mod_vst = [k for k in vst_items.keys() if 'mod' in k.lower() and 'source' in k.lower()]
print(f"VST item_lists with 'mod'+'source': {mod_vst}")
mod_vst2 = [k for k in vst_items.keys() if 'mod' in k.lower()]
print(f"VST item_lists with 'mod': {mod_vst2[:15]}")

# ── CORR-03: Arp 모드 ──
print("\n--- CORR-03: Arp 모드 ---")
cluster = read_string_cluster(cm4, 0x081AEC3C, CM4_BASE, max_entries=10, gap=24)
print(f"CM4 @ 0x081AEC3C cluster: {[s for _, s in cluster]}")
# mf_enums ARP_MODES
arp_match = re.search(r'ARP_MODES\s*=\s*\{([^}]+)\}', enums_code)
if arp_match:
    print(f"mf_enums.py ARP_MODES: {arp_match.group(1)[:300]}")
# VST XML Arp_Mode
arp_vst = {k: v for k, v in vst_items.items() if 'arp' in k.lower() and 'mode' in k.lower()}
for k, v in arp_vst.items():
    print(f"VST {k}: {[i['text'] for i in v]}")

# ── CORR-04: Unison 하위모드 ──
print("\n--- CORR-04: Unison 하위모드 ---")
cluster = read_string_cluster(cm4, 0x081AF500, CM4_BASE, max_entries=10, gap=24)
print(f"CM4 @ 0x081AF500 cluster: {[s for _, s in cluster]}")
# mf_enums VOICE_MODES
voice_match = re.search(r'VOICE_MODES\s*=\s*\{([^}]+)\}', enums_code)
if voice_match:
    print(f"mf_enums.py VOICE_MODES: {voice_match.group(1)[:300]}")
uni_match = re.search(r'UNISON_MODES\s*=\s*\{([^}]+)\}', enums_code)
if uni_match:
    print(f"mf_enums.py UNISON_MODES: {uni_match.group(1)[:200]}")
# VST
voice_vst = {k: v for k, v in vst_items.items() if 'voice' in k.lower() and 'mode' in k.lower()}
for k, v in voice_vst.items():
    print(f"VST {k}: {[i['text'] for i in v]}")

# ── CORR-05: LFO 파형명 ──
print("\n--- CORR-05: LFO 파형명 ---")
cluster = read_string_cluster(cm4, 0x081B0FB0, CM4_BASE, max_entries=12, gap=24)
print(f"CM4 @ 0x081B0FB0 cluster: {[s for _, s in cluster]}")
# mf_enums LFO_WAVES
lfo_match = re.search(r'LFO_WAVES\s*=\s*\{([^}]+)\}', enums_code)
if lfo_match:
    print(f"mf_enums.py LFO_WAVES: {lfo_match.group(1)[:300]}")
# VST
lfo_vst = {k: v for k, v in vst_items.items() if 'lfo' in k.lower() and 'wave' in k.lower()}
for k, v in lfo_vst.items():
    print(f"VST {k}: {[i['text'] for i in v]}")

# ── CORR-06: Tempo Subdivision ──
print("\n--- CORR-06: Tempo Subdivision ---")
cluster1 = read_string_cluster(cm4, 0x081AF0B4, CM4_BASE, max_entries=15, gap=24)
print(f"CM4 @ 0x081AF0B4 (주 테이블): {[s for _, s in cluster1]}")
cluster2 = read_string_cluster(cm4, 0x081AF564, CM4_BASE, max_entries=10, gap=24)
print(f"CM4 @ 0x081AF564 (추가 테이블): {[s for _, s in cluster2]}")
# VST
tempo_vst = {k: v for k, v in vst_items.items() if 'tempo' in k.lower() or 'sync' in k.lower() or 'subdiv' in k.lower()}
for k, v in tempo_vst.items():
    print(f"VST {k}: {[i['text'] for i in v]}")

# ── CORR-07: LFO 9파형 ──
print("\n--- CORR-07: LFO 9파형 ---")
lfo_count = len(cluster) if cluster else 0
print(f"CM4 LFO 파형 수: {lfo_count}")
# CM7에서 정수 9 카운트
nine_packed = struct.pack('<I', 9)
nine_count = count_keyword(cm7, nine_packed, CM7_BASE)
print(f"CM7 정수 9 출현: {nine_count}회")
lfo_vst2 = {k: v for k, v in vst_items.items() if 'lfo' in k.lower() and ('wave' in k.lower() or 'shape' in k.lower())}
for k, v in lfo_vst2.items():
    print(f"VST {k}: {len(v)} items = {[i['text'] for i in v]}")

# ── CORR-08: LFO Shaper 첫 항목 ──
print("\n--- CORR-08: LFO Shaper 첫 항목 ---")
shaper_match, shaper_str = verify_addr_string(cm4, 0x081AF128, CM4_BASE, "Preset Shaper")
print(f"CM4 @ 0x081AF128 = '{shaper_str}' (expected 'Preset Shaper'): {shaper_match}")
cluster = read_string_cluster(cm4, 0x081AF128, CM4_BASE, max_entries=30, gap=48)
print(f"CM4 @ 0x081AF128 cluster ({len(cluster)} items): {[s for _, s in cluster[:10]]}...")
# VST
shaper_vst = {k: v for k, v in vst_items.items() if 'shaper' in k.lower()}
for k, v in shaper_vst.items():
    items_text = [i['text'] for i in v]
    print(f"VST {k}: {len(v)} items, first='{items_text[0] if items_text else 'N/A'}', last='{items_text[-1] if items_text else 'N/A'}")

# ── CORR-09: Custom Assign 8목적지 ──
print("\n--- CORR-09: Custom Assign 8목적지 ---")
cluster = read_string_cluster(cm4, 0x081AEA94, CM4_BASE, max_entries=12, gap=32)
print(f"CM4 @ 0x081AEA94 cluster: {[s for _, s in cluster]}")
# VST
custom_vst = {k: v for k, v in vst_items.items() if 'custom' in k.lower() and 'assign' in k.lower()}
for k, v in custom_vst.items():
    print(f"VST {k}: {[i['text'] for i in v]}")

# ── CORR-10: FX 타입 CM4 12종 / VST 13종 ──
print("\n--- CORR-10: FX 타입 CM4 vs VST ---")
cluster = read_string_cluster(cm4, 0x081AF308, CM4_BASE, max_entries=15, gap=32)
cm4_fx = [s for _, s in cluster]
print(f"CM4 @ 0x081AF308 FX 타입 ({len(cm4_fx)}): {cm4_fx}")
# mf_enums FX_TYPES
fx_match = re.search(r'FX_TYPES\s*=\s*\{([^}]+)\}', enums_code)
if fx_match:
    print(f"mf_enums.py FX_TYPES: {fx_match.group(1)[:300]}")
# VST FX type
fx_vst = {k: v for k, v in vst_items.items() if 'fx' in k.lower() and 'type' in k.lower()}
for k, v in fx_vst.items():
    print(f"VST {k}: {[i['text'] for i in v]}")

print()

# ═══════════════════════════════════════════════════════════════════
# Part 2: ENH-01~12 교차검증
# ═══════════════════════════════════════════════════════════════════

print("=" * 70)
print("Part 2: ENH (보강) 항목 교차검증")
print("=" * 70)

# ── ENH-01: Mod Matrix 247 dest ──
print("\n--- ENH-01: Mod Matrix ~247 dest ---")
mod_dest_vst = {k: v for k, v in vst_items.items() if 'mod' in k.lower() and 'dest' in k.lower()}
for k, v in mod_dest_vst.items():
    print(f"VST {k}: {len(v)} items")
mod_assign_vst = {k: v for k, v in vst_items.items() if 'assign' in k.lower()}
for k, v in mod_assign_vst.items():
    print(f"VST {k}: {len(v)} items = {[i['text'] for i in v]}")

# ── ENH-02: Shaper 25종 ──
print("\n--- ENH-02: Shaper 25종 ---")
cluster = read_string_cluster(cm4, 0x081AF128, CM4_BASE, max_entries=30, gap=48)
print(f"CM4 Shaper cluster: {len(cluster)} items")
for addr, name in cluster:
    print(f"  0x{addr:08X}: {name}")
shaper_vst = {k: v for k, v in vst_items.items() if 'shaper' in k.lower()}
for k, v in shaper_vst.items():
    print(f"VST {k}: {len(v)} items")

# ── ENH-03: Deprecated 4종 ──
print("\n--- ENH-03: Deprecated 파라미터 ---")
for addr, expected in [(0x081AF994, "UnisonOn TO BE DEPRECATED"), (0x081AF70C, "old FX3 Routing"), (0x081AFB00, "obsolete Rec Count-In"), (0x081AF72C, "internal use only")]:
    ok, s = verify_addr_string(cm4, addr, CM4_BASE, expected)
    print(f"  0x{addr:08X}: '{s}' match={ok}")

# ── ENH-04: CycEnv Loop2 ──
print("\n--- ENH-04: CycEnv Loop2 ---")
cycenv_match = re.search(r'CYCENV_MODES\s*=\s*\{([^}]+)\}', enums_code)
if cycenv_match:
    print(f"mf_enums.py CYCENV_MODES: {cycenv_match.group(1)[:200]}")
# VST
cycenv_vst = {k: v for k, v in vst_items.items() if 'cyc' in k.lower() and 'env' in k.lower()}
for k, v in cycenv_vst.items():
    print(f"VST {k}: {[i['text'] for i in v]}")
# CM4에서 Loop2 검색
loop2_pos = cm4.find(b"Loop2")
if loop2_pos >= 0:
    print(f"CM4 'Loop2' found at offset 0x{loop2_pos:X} (addr 0x{CM4_BASE+loop2_pos:08X})")
else:
    print("CM4 'Loop2' NOT FOUND")
    # 대안 검색
    for alt in [b"Loop 2", b"loop2", b"LOOP2"]:
        pos = cm4.find(alt)
        if pos >= 0:
            print(f"  CM4 '{alt.decode()}' found at offset 0x{pos:X}")

# ── ENH-05: Poly Allocation 3모드 ──
print("\n--- ENH-05: Poly Allocation ---")
pa_match = re.search(r'POLY_ALLOC_MODES\s*=\s*\{([^}]+)\}', enums_code)
if pa_match:
    print(f"mf_enums.py POLY_ALLOC_MODES: {pa_match.group(1)[:200]}")
# VST
pa_vst = {k: v for k, v in vst_items.items() if 'alloc' in k.lower()}
for k, v in pa_vst.items():
    print(f"VST {k}: {[i['text'] for i in v]}")

# ── ENH-06: 161 CC ──
print("\n--- ENH-06: 161 CC ---")
cc_match = re.search(r'CC_MAP\s*=\s*\{([^}]+)\}', enums_code)
if not cc_match:
    cc_match = re.search(r'CC\b.*=\s*\{([^}]{10,})\}', enums_code)
if cc_match:
    print(f"mf_enums.py CC_MAP: {cc_match.group(1)[:200]}...")
# VST realtimemidi params
rtm_params = [p for p in vst_params if 'realtimemidi' in open(VST_XML).read() and p]
# Actually parse from XML
tree = ET.parse(VST_XML)
root = tree.getroot()
rtm_count = 0
for p in root.iter('param'):
    if p.get('realtemidi') == '1' or p.get('realtimemidi') == '1':
        rtm_count += 1
print(f"VST realtimemidi params: {rtm_count}")

# ── ENH-07: Vocoder Self vs Ext ──
print("\n--- ENH-07: Vocoder Self vs Ext ---")
# VST FX 타입에서 Vocoder 확인
fx_vst_all = {k: v for k, v in vst_items.items() if 'fx' in k.lower() and 'type' in k.lower()}
for k, v in fx_vst_all.items():
    vocoder_items = [i['text'] for i in v if 'vocoder' in i['text'].lower() or 'voc' in i['text'].lower()]
    if vocoder_items:
        print(f"VST {k}: {vocoder_items}")

# ── ENH-08: Smooth Mod 1~4 ──
print("\n--- ENH-08: Smooth Mod 1~4 ---")
cluster = read_string_cluster(cm4, 0x081B1B8C, CM4_BASE, max_entries=8, gap=24)
print(f"CM4 @ 0x081B1B8C cluster: {[s for _, s in cluster]}")
# VST
smooth_vst = [p for p in vst_params if 'smooth' in p.lower() and 'mod' in p.lower()]
print(f"VST params with 'smooth'+'mod': {smooth_vst}")

# ── ENH-09: Arp 확률 분포 ──
print("\n--- ENH-09: Arp 확률 분포 (CM7 LUT) ---")
# Walk LUT @ CM7 0x080546C4, 64 bytes (8슬롯 x 8 step)
lut_offset = 0x080546C4 - CM7_BASE
if 0 <= lut_offset < len(cm7) - 64:
    walk_lut = []
    for i in range(64):
        val = cm7[lut_offset + i]
        walk_lut.append(val)
    # 8슬롯 x 8 step 형태로 출력
    print("CM7 Walk LUT @ 0x080546C4 (8x8):")
    for row in range(8):
        row_data = walk_lut[row*8:(row+1)*8]
        print(f"  Slot {row}: {row_data}")
    # 확률 분석
    from collections import Counter
    all_vals = Counter(walk_lut)
    print(f"  값 분포: {dict(sorted(all_vals.items()))}")
else:
    print(f"LUT offset out of range: 0x{lut_offset:X} (cm7 size: {len(cm7)})")

# ── ENH-10: Custom Assign (CORR-09과 중복, 스킵) ──
print("\n--- ENH-10: Custom Assign (CORR-09 참조) ---")

# ── ENH-11: FX Singleton ──
print("\n--- ENH-11: FX Singleton ---")
singleton_match = re.search(r'FX_SINGLETONS\s*=\s*\{([^}]+)\}', enums_code)
if singleton_match:
    print(f"mf_enums.py FX_SINGLETONS: {singleton_match.group(1)}")

# ── ENH-12: Sequencer 64-step ──
print("\n--- ENH-12: Sequencer 64-step ---")
# CM7에서 64 상수 카운트
sixtyfour_packed = struct.pack('<I', 64)
sixtyfour_count = count_keyword(cm7, sixtyfour_packed, CM7_BASE)
print(f"CM7 정수 64 출현: {sixtyfour_count}회")
# VST
seq_vst = {k: v for k, v in vst_items.items() if 'seq' in k.lower() or 'step' in k.lower()}
for k, v in seq_vst.items():
    print(f"VST {k}: {len(v)} items")

print()

# ═══════════════════════════════════════════════════════════════════
# Part 3: Spice/Dice LUT 정량값 추출 시도
# ═══════════════════════════════════════════════════════════════════

print("=" * 70)
print("Part 3: Spice/Dice LUT 정량값")
print("=" * 70)

# spice_exp_lut @ CM7 0x08067FDC, 64 bytes
lut_offset = 0x08067FDC - CM7_BASE
if 0 <= lut_offset < len(cm7) - 64:
    print(f"\nCM7 spice_exp_lut @ 0x08067FDC (64 bytes, uint8):")
    lut_data = []
    for i in range(64):
        val = cm7[lut_offset + i]
        lut_data.append(val)
    # 8개씩 출력
    for row in range(8):
        row_data = lut_data[row*8:(row+1)*8]
        hex_str = " ".join(f"{v:02X}" for v in row_data)
        dec_str = " ".join(f"{v:3d}" for v in row_data)
        float_str = " ".join(f"{v/255:.3f}" for v in row_data)
        print(f"  [{row*8:2d}-{row*8+7:2d}] {hex_str} | {dec_str} | {float_str}")
    
    # 통계
    non_zero = [v for v in lut_data if v > 0]
    if non_zero:
        print(f"\n  비제로: {len(non_zero)}/64, min={min(non_zero)}, max={max(non_zero)}, avg={sum(non_zero)/len(non_zero):.1f}")
        # 지수 분포인지 확인
        sorted_vals = sorted(non_zero, reverse=True)
        ratios = [sorted_vals[i]/sorted_vals[i+1] if sorted_vals[i+1] > 0 else 0 for i in range(min(10, len(sorted_vals)-1))]
        print(f"  상위 감소비율 (top 10): {[f'{r:.2f}' for r in ratios]}")
else:
    print(f"LUT offset out of range: 0x{lut_offset:X}")

# arp_walk_lut @ CM7 0x080546C4 (already printed above)

# env_time_scale @ CM7 0x0806D330, 256 bytes (float32)
lut_offset = 0x0806D330 - CM7_BASE
if 0 <= lut_offset < len(cm7) - 256*4:
    print(f"\nCM7 env_time_scale @ 0x0806D330 (256 entries, float32):")
    import struct as st
    floats = []
    for i in range(256):
        val = st.unpack_from('<f', cm7, lut_offset + i*4)[0]
        floats.append(val)
    # 첫 16개, 중간 16개, 마지막 16개 출력
    print("  First 16:")
    for i in range(16):
        print(f"    [{i:3d}] {floats[i]:.6f}")
    print("  Middle 16 (120-135):")
    for i in range(120, 136):
        print(f"    [{i:3d}] {floats[i]:.6f}")
    print("  Last 16 (240-255):")
    for i in range(240, 256):
        print(f"    [{i:3d}] {floats[i]:.6f}")
    # 범위
    valid = [f for f in floats if 0.0 < f < 100.0]
    if valid:
        print(f"  Valid range: [{min(valid):.6f}, {max(valid):.6f}]")
else:
    print(f"env_time_scale LUT offset out of range: 0x{lut_offset:X}, cm7 size={len(cm7)}")

print()

# ═══════════════════════════════════════════════════════════════════
# Part 4: VST XML 전체 enum 카탈로그
# ═══════════════════════════════════════════════════════════════════

print("=" * 70)
print("Part 4: VST XML 전체 enum 카탈로그")
print("=" * 70)

for name, items in sorted(vst_items.items()):
    texts = [i['text'] for i in items]
    pvals = [i['processorvalue'] for i in items]
    print(f"\n{name}: {len(items)} items")
    if len(texts) <= 30:
        for t, p in zip(texts, pvals):
            print(f"  {p}: {t}")
    else:
        for t, p in zip(texts[:5], pvals[:5]):
            print(f"  {p}: {t}")
        print(f"  ... ({len(texts)-10} more)")
        for t, p in zip(texts[-5:], pvals[-5:]):
            print(f"  {p}: {t}")

print()
print("=" * 70)
print("Phase 13 분석 완료")
print("=" * 70)
