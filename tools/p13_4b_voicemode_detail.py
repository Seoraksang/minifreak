#!/usr/bin/env python3
"""P13-4b: Voice Mode VST XML 상세 + pointer table 분석"""
import struct, xml.etree.ElementTree as ET, os

CM4_BIN = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
CM4_BASE = 0x08120000

with open(CM4_BIN, "rb") as f:
    cm4 = f.read()

# ============================================================
# 1. VST XML Voice Mode 항목 상세 추출
# ============================================================
print("="*60)
print("1. Voice Mode VST XML 상세")
print("="*60)

# internal_params에서 Voice Mode 관련 param 전체 추출
xml_path = "/home/jth/hoon/minifreak/reference/minifreak_internal_params.xml"
tree = ET.parse(xml_path)
root = tree.getroot()

for param in root.iter('param'):
    name = param.get('name', '')
    if 'voice' in name.lower():
        print(f"\n  param: {name}")
        print(f"    display_name: {param.get('display_name', '')}")
        print(f"    type: {param.get('type', '')}")
        for child in param:
            if child.tag == 'item':
                print(f"    item: text=\"{child.get('text', '')}\" processorvalue=\"{child.get('processorvalue', '')}\"")
            else:
                print(f"    {child.tag}: {dict(child.attrib)}")

# vst_params에서도
xml_path2 = "/home/jth/hoon/minifreak/reference/minifreak_vst_params.xml"
tree2 = ET.parse(xml_path2)
root2 = tree2.getroot()

for param in root2.iter('param'):
    name = param.get('name', '')
    if 'voice' in name.lower() or 'poly' in name.lower() or 'dual' in name.lower():
        print(f"\n  [VST] param: {name}")
        print(f"    display_name: {param.get('display_name', '')}")
        for child in param:
            if child.tag == 'item':
                print(f"    item: text=\"{child.get('text', '')}\" processorvalue=\"{child.get('processorvalue', '')}\"")

# ============================================================
# 2. Unison pointer table 상세 분석
# ============================================================
print("\n" + "="*60)
print("2. Unison pointer table 상세 (33 refs)")
print("="*60)

unison_addr_bytes = struct.pack('<I', 0x081AF500)
pos = 0
refs = []
while True:
    pos = cm4.find(unison_addr_bytes, pos)
    if pos == -1:
        break
    addr = CM4_BASE + pos
    refs.append(addr)
    pos += 1

# cluster 분석
print(f"  총 {len(refs)}개 참조")
for i, a in enumerate(refs):
    off = a - CM4_BASE
    ctx = cm4[off:off+8]
    # 앞뒤 주소도 확인
    if i > 0:
        prev_addr = refs[i-1]
        gap = a - prev_addr
        print(f"    0x{a:08X} (gap={gap} from prev)")
    else:
        print(f"    0x{a:08X} (first)")

# 연속된 영역 확인
if len(refs) > 5:
    # 첫 5개와 마지막 5개의 간격
    first_gap = refs[1] - refs[0]
    last_gap = refs[-1] - refs[-2]
    print(f"\n  첫 gap: {first_gap}, 마지막 gap: {last_gap}")
    
    # pointer table 영역 hex dump
    start = refs[0] - CM4_BASE - 8
    end = refs[-1] - CM4_BASE + 8
    region = cm4[start:end]
    print(f"\n  Pointer table region (0x{refs[0]:08X} ~ 0x{refs[-1]:08X}):")
    for i in range(0, len(region), 4):
        addr = refs[0] - 8 + i
        val = struct.unpack_from('<I', region, i)[0]
        # 이 값이 CM4 문자열 주소 범위인지 확인
        marker = ""
        if 0x081A0000 <= val <= 0x08200000:
            # 문자열 읽기
            str_off = val - CM4_BASE
            if 0 <= str_off < len(cm4):
                end_str = cm4.find(b'\x00', str_off)
                if end_str == -1:
                    end_str = str_off + 20
                s = cm4[str_off:end_str]
                if all(32 <= b < 127 for b in s):
                    marker = f' → "{s.decode("ascii")}"'
        print(f"    0x{addr:08X}: 0x{val:08X}{marker}")

# ============================================================
# 3. Voice Mode enum pointer table 후보 탐색
# ============================================================
# mf_enums.py: {0:Poly, 2:Mono, 3:Unison, 4:Para, 5:Dual}
# VST internal: {0:Mono, 1:Unison, 2:Poly, 3:Para}
# → 인덱스 체계가 다름!
# 펌웨어는 VST internal 기준

# VST internal 인덱스로 pointer table 탐색:
# [Mono_ptr, Unison_ptr, Poly_ptr, Para_ptr]
# Mono @ 0x081AF520, Unison @ 0x081AF500
# 인접 pointer table에서 이 두 주소가 나란히 있는지 확인

print("\n" + "="*60)
print("3. Voice Mode pointer table 탐색")
print("="*60)

mono_addr = 0x081AF520
unison_addr = 0x081AF500

# Mono 바로 뒤에 Unison가 있는지 (4-byte 간격)
mono_bytes = struct.pack('<I', mono_addr)
# Unison이 Mono 바로 앞에 있는지
# → pointer table: [Unison, Mono, ?, ?] 인접?

# Mono_ptr 뒤에 오는 주소 확인
mono_off = mono_addr - CM4_BASE
for search_off in range(0, len(cm4) - 8):
    v0 = struct.unpack_from('<I', cm4, search_off)[0]
    v1 = struct.unpack_from('<I', cm4, search_off + 4)[0]
    if v0 == unison_addr and v1 == mono_addr:
        addr = CM4_BASE + search_off
        print(f"  [Unison, Mono] 연속 @ 0x{addr:08X}")
        # 뒤에 더 있는지
        for j in range(2, 6):
            if search_off + j*4 + 4 <= len(cm4):
                vn = struct.unpack_from('<I', cm4, search_off + j*4)[0]
                if 0x081A0000 <= vn <= 0x08200000:
                    str_off = vn - CM4_BASE
                    if 0 <= str_off < len(cm4):
                        end_s = cm4.find(b'\x00', str_off)
                        if end_s == -1:
                            end_s = str_off + 20
                        s = cm4[str_off:end_s]
                        if all(32 <= b < 127 for b in s):
                            print(f"    [{j}]: 0x{vn:08X} → \"{s.decode('ascii')}\"")
    # Mono 뒤에 Unison
    if v0 == mono_addr and v1 == unison_addr:
        addr = CM4_BASE + search_off
        print(f"  [Mono, Unison] 연속 @ 0x{addr:08X}")

# ============================================================
# 4. Unison pointer cluster 상세 — Voice Mode vtable
# ============================================================
print("\n" + "="*60)
print("4. Unison pointer cluster — Voice Mode vtable 분석")
print("="*60)

# 33개 참조 중 연속 영역 찾기
if len(refs) >= 10:
    # 가장 밀집한 영역 찾기
    max_cluster = []
    current_cluster = [refs[0]]
    for i in range(1, len(refs)):
        if refs[i] - refs[i-1] <= 16:  # 16바이트 이내 = 연속
            current_cluster.append(refs[i])
        else:
            if len(current_cluster) > len(max_cluster):
                max_cluster = current_cluster
            current_cluster = [refs[i]]
    if len(current_cluster) > len(max_cluster):
        max_cluster = current_cluster
    
    print(f"  최대 연속 cluster: {len(max_cluster)}개")
    if len(max_cluster) >= 4:
        start = max_cluster[0] - CM4_BASE
        end = max_cluster[-1] - CM4_BASE + 4
        region = cm4[start:end]
        print(f"  영역: 0x{max_cluster[0]:08X} ~ 0x{max_cluster[-1]+4:08X} ({len(region)} bytes)")
        print(f"  Hex dump:")
        for i in range(0, min(len(region), 256), 4):
            addr = max_cluster[0] + i
            if i + 4 <= len(region):
                val = struct.unpack_from('<I', region, i)[0]
                marker = ""
                if 0x081A0000 <= val <= 0x08200000:
                    str_off = val - CM4_BASE
                    if 0 <= str_off < len(cm4):
                        end_s = cm4.find(b'\x00', str_off)
                        if end_s == -1 or end_s - str_off > 30:
                            end_s = str_off + 30
                        s = cm4[str_off:end_s]
                        if all(32 <= b < 127 for b in s):
                            marker = f' → "{s.decode("ascii")}"'
                print(f"    0x{addr:08X}: 0x{val:08X}{marker}")

# ============================================================
# 5. CM4에서 모든 Voice Mode 관련 문자열 주소 수집
# ============================================================
print("\n" + "="*60)
print("5. Voice Mode 관련 모든 문자열 수집")
print("="*60)

vm_strings = {
    "Mono": [],
    "Unison": [],
    "Para": [],
    "Poly": [],
    "Dual": [],
}

for name in vm_strings:
    pattern = name.encode('ascii') + b'\x00'
    pos = 0
    while True:
        pos = cm4.find(pattern, pos)
        if pos == -1:
            break
        addr = CM4_BASE + pos
        vm_strings[name].append(addr)
        pos += 1

for name, addrs in vm_strings.items():
    print(f"  '{name}': {len(addrs)}개 {[hex(a) for a in addrs]}")

# ============================================================
# 6. "Uni (Poly)"와 "Uni (Para)" — Unison의 하위 모드
# ============================================================
print("\n" + "="*60)
print("6. Unison 하위 모드 분석")
print("="*60)

# "Uni (Poly)" @ 0x081AF508, "Uni (Para)" @ 0x081AF514
# 이것은 Unison 모드의 변형: Poly 기반 Unison vs Para 기반 Unison
# Unison = 2~6 voices 동시 발음
# Uni (Poly) = Poly voice allocation + unison detune
# Uni (Para) = Para voice allocation + unison detune

# pointer refs 확인
for label, addr in [("Uni (Poly)", 0x081AF508), ("Uni (Para)", 0x081AF514)]:
    addr_bytes = struct.pack('<I', addr)
    pos = 0
    count = 0
    while True:
        pos = cm4.find(addr_bytes, pos)
        if pos == -1:
            break
        count += 1
        pos += 1
    print(f"  '{label}' (0x{addr:08X}): {count}개 pointer ref")

# ============================================================
# 7. VST vst_params에서 Voice Mode 항목 완전 추출
# ============================================================
print("\n" + "="*60)
print("7. VST Voice Mode 완전 매핑")
print("="*60)

# vst_params에서 모든 item이 있는 param 추출
xml_path2 = "/home/jth/hoon/minifreak/reference/minifreak_vst_params.xml"
with open(xml_path2, 'r') as f:
    content = f.read()

# Voice_Mode param 찾기
import re
# <param name="Voice_Mode" ...> block 추출
vm_match = re.search(r'<param name="Voice_Mode"[^>]*>(.*?)</param>', content, re.DOTALL)
if vm_match:
    block = vm_match.group(1)
    items = re.findall(r'<item text="([^"]+)" processorvalue="([^"]+)"/>', block)
    print(f"  Voice_Mode items ({len(items)}):")
    for text, pv in items:
        print(f"    processorvalue={pv}: \"{text}\"")
else:
    print("  Voice_Mode param not found in vst_params.xml")
    # 다른 이름으로 검색
    for line in content.split('\n'):
        if 'voice' in line.lower() and 'mode' in line.lower() and 'param' in line.lower():
            print(f"  Candidate: {line.strip()[:150]}")

# internal_params에서도
xml_path1 = "/home/jth/hoon/minifreak/reference/minifreak_internal_params.xml"
with open(xml_path1, 'r') as f:
    content1 = f.read()

vm_match1 = re.search(r'<param name="Voice_Mode"[^>]*>(.*?)</param>', content1, re.DOTALL)
if vm_match1:
    block = vm_match1.group(1)
    items = re.findall(r'<item text="([^"]+)" processorvalue="([^"]+)"/>', block)
    print(f"\n  [Internal] Voice_Mode items ({len(items)}):")
    for text, pv in items:
        print(f"    processorvalue={pv}: \"{text}\"")

# ============================================================
# 8. 최종 결론
# ============================================================
print("\n" + "="*60)
print("8. 결론")
print("="*60)

print("""
  발견 사항:
  1. CM4 바이너리에 "Poly" 독립 문자열 없음
     → "Arp Poly" (0x081AEC8C)와 "Uni (Poly)" (0x081AF508)만 존재
  2. CM4 바이너리에 "Dual" 독립 문자열 없음
  3. Voice Mode enum 문자열 (CM4):
     - Unison @ 0x081AF500 ★★★★★
     - Uni (Poly) @ 0x081AF508 ★★★★★
     - Uni (Para) @ 0x081AF514 ★★★★★
     - Mono @ 0x081AF520 ★★★★★
     - Para @ 0x081AF528 ★★★★★
  4. VST internal processorvalue:
     - 0=Mono, 1=Unison, 2=Poly, 3=Para
  5. VST vst_params processorvalue:
     - Poly=7 (다른 인덱스 체계)
  
  해석:
  - "Poly"와 "Dual"은 CM4에 독립 enum 문자열로 존재하지 않음
  - Poly = default voice mode (index 0 또는 2), 별도 UI 표시 문자열 불필요?
  - Dual = index 5 (mf_enums.py), 펌웨어에서 deprecated이거나 VST 전용
  
  또는:
  - Poly/Dual은 다른 enum 영역(예: Mod Source의 "Poly" LFO 등)과 포인터 공유
  - mf_enums.py의 {0:Poly, 5:Dual}은 VST plugin index이며, 하드웨어 펌웨어와는 다름
""")

print("=== P13-4b 완료 ===")
