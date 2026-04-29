#!/usr/bin/env python3
"""P13-4: Voice Mode Poly/Dual 위치 결정"""
import struct, re

CM4_BIN = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
CM4_BASE = 0x08120000

with open(CM4_BIN, "rb") as f:
    cm4 = f.read()

# ============================================================
# 1. "Poly" 독립 문자열 검색
# ============================================================
print("="*60)
print("1. 'Poly' null-terminated 문자열 전체 검색")
print("="*60)

for kw in [b"Poly\x00"]:
    pos = 0
    while True:
        pos = cm4.find(kw, pos)
        if pos == -1:
            break
        addr = CM4_BASE + pos
        # 컨텍스트: 주변 128B에서 문자열 클러스터 추출
        scan_start = max(0, pos - 64)
        scan_end = min(len(cm4), pos + 128)
        cluster = []
        p = scan_start
        while p < scan_end:
            while p < scan_end and cm4[p] == 0:
                p += 1
            if p >= scan_end:
                break
            e = cm4.find(b'\x00', p)
            if e == -1 or e > scan_end:
                break
            raw = cm4[p:e]
            if len(raw) > 0 and all(32 <= b < 127 for b in raw):
                cluster.append((CM4_BASE + p, raw.decode('ascii')))
            p = e + 1
        
        print(f"\n  'Poly' @ 0x{addr:08X}:")
        for ca, cs in cluster:
            marker = " <<<" if ca == addr else ""
            print(f"    0x{ca:08X}: \"{cs}\"{marker}")
        pos += 1

# ============================================================
# 2. "Dual" 독립 문자열 검색
# ============================================================
print("\n" + "="*60)
print("2. 'Dual' null-terminated 문자열 전체 검색")
print("="*60)

pos = 0
while True:
    pos = cm4.find(b"Dual\x00", pos)
    if pos == -1:
        break
    addr = CM4_BASE + pos
    scan_start = max(0, pos - 64)
    scan_end = min(len(cm4), pos + 128)
    cluster = []
    p = scan_start
    while p < scan_end:
        while p < scan_end and cm4[p] == 0:
            p += 1
        if p >= scan_end:
            break
        e = cm4.find(b'\x00', p)
        if e == -1 or e > scan_end:
            break
        raw = cm4[p:e]
        if len(raw) > 0 and all(32 <= b < 127 for b in raw):
            cluster.append((CM4_BASE + p, raw.decode('ascii')))
        p = e + 1
    
    print(f"\n  'Dual' @ 0x{addr:08X}:")
    for ca, cs in cluster:
        marker = " <<<" if ca == addr else ""
        print(f"    0x{ca:08X}: \"{cs}\"{marker}")
    pos += 1

# ============================================================
# 3. Voice Mode enum 영역 상세 스캔 (Mono/Unison/Para 확인)
# ============================================================
print("\n" + "="*60)
print("3. Voice Mode enum 영역 상세 스캔")
print("="*60)

# Phase 11: Mono @ 0x081AF520, Unison @ 0x081AF500, Para @ 0x081AF528
# → 범위: 0x081AF4F0 ~ 0x081AF560
vm_start = 0x081AF4E0 - CM4_BASE
vm_end = 0x081AF580 - CM4_BASE
region = cm4[vm_start:vm_end]

print("  Hex dump (0x081AF4E0 ~ 0x081AF580):")
for i in range(0, len(region), 16):
    addr = 0x081AF4E0 + i
    hex_part = ' '.join(f'{region[i+j]:02X}' if i+j < len(region) else '  ' for j in range(16))
    ascii_part = ''.join(chr(region[i+j]) if i+j < len(region) and 32 <= region[i+j] < 127 else '.' for j in range(16))
    print(f"    {addr:08X}: {hex_part}  {ascii_part}")

# 문자열 추출
print("\n  문자열 클러스터:")
p = 0
cluster = []
while p < len(region):
    while p < len(region) and region[p] == 0:
        p += 1
    if p >= len(region):
        break
    e = region.find(b'\x00', p)
    if e == -1:
        break
    raw = region[p:e]
    if len(raw) > 0 and all(32 <= b < 127 for b in raw):
        addr = 0x081AF4E0 + p
        cluster.append((addr, raw.decode('ascii')))
    p = e + 1

for a, s in cluster:
    print(f"    0x{a:08X}: \"{s}\"")

# ============================================================
# 4. mf_enums.py VOICE_MODES 구조 확인
# ============================================================
print("\n" + "="*60)
print("4. mf_enums.py VOICE_MODES")
print("="*60)

mf_path = "/home/jth/hoon/minifreak/tools/mf_enums.py"
try:
    with open(mf_path) as f:
        mf = f.read()
    in_voicemode = False
    for line_num, line in enumerate(mf.split('\n'), 1):
        if 'VOICE_MODE' in line.upper() or 'voice_mode' in line:
            in_voicemode = True
        if in_voicemode:
            print(f"  L{line_num}: {line.rstrip()}")
            if line.strip() == '' or line.strip().startswith('}'):
                if 'VOICE_MODE' not in line:
                    in_voicemode = False
except Exception as e:
    print(f"  Error: {e}")

# ============================================================
# 5. "Para" 문자열도 검색 (Para-phase?)
# ============================================================
print("\n" + "="*60)
print("5. 'Para' null-terminated 전체 검색")
print("="*60)

pos = 0
while True:
    pos = cm4.find(b"Para\x00", pos)
    if pos == -1:
        break
    addr = CM4_BASE + pos
    scan_start = max(0, pos - 32)
    scan_end = min(len(cm4), pos + 64)
    cluster = []
    p = scan_start
    while p < scan_end:
        while p < scan_end and cm4[p] == 0:
            p += 1
        if p >= scan_end:
            break
        e = cm4.find(b'\x00', p)
        if e == -1 or e > scan_end:
            break
        raw = cm4[p:e]
        if len(raw) > 0 and all(32 <= b < 127 for b in raw):
            cluster.append((CM4_BASE + p, raw.decode('ascii')))
        p = e + 1
    
    print(f"\n  'Para' @ 0x{addr:08X}:")
    for ca, cs in cluster:
        marker = " <<<" if ca == addr else ""
        print(f"    0x{ca:08X}: \"{cs}\"{marker}")
    pos += 1

# ============================================================
# 6. Voice Mode pointer table 검색
# ============================================================
# Phase 11에서 Mono/Unison/Para가 서로 다른 주소에 존재
# → 이들은 pointer table이 아니라 독립 enum 항목
# Voice Mode = [Poly, ?, Mono, Unison, Para, Dual] 인덱스 구조?
# VST processorvalue 확인

print("\n" + "="*60)
print("6. Voice Mode pointer table 검색")
print("="*60)

# Phase 11 검증에서 Voice Mode 관련 주소들:
# Mono @ 0x081AF520, Unison @ 0x081AF500, Para @ 0x081AF528
# 이 주소들이 포인터 테이블의 항목인지, 아니면 독립 문자열인지 확인

# pointer table이면: 어떤 주소 N에서 [ptr0, ptr1, ptr2, ...] 형태
# 각 ptr이 Mono/Unison/Para/Poly/Dual 문자열을 가리킴
# CM4 Thumb2: pointer = LDR Rx, [PC, #offset] 또는 직접 주소

# Mono 문자열 주소 0x081AF520을 참조하는 코드 검색
mono_addr_bytes = struct.pack('<I', 0x081AF520)
print(f"  Mono ptr (0x081AF520) bytes LE: {mono_addr_bytes.hex()}")
pos = 0
mono_refs = 0
while True:
    pos = cm4.find(mono_addr_bytes, pos)
    if pos == -1:
        break
    addr = CM4_BASE + pos
    if mono_refs < 10:
        print(f"    Mono ptr ref @ 0x{addr:08X}")
    mono_refs += 1
    pos += 1
print(f"  Mono ptr refs: {mono_refs}")

unison_addr_bytes = struct.pack('<I', 0x081AF500)
pos = 0
unison_refs = 0
while True:
    pos = cm4.find(unison_addr_bytes, pos)
    if pos == -1:
        break
    addr = CM4_BASE + pos
    if unison_refs < 10:
        print(f"    Unison ptr ref @ 0x{addr:08X}")
    unison_refs += 1
    pos += 1
print(f"  Unison ptr refs: {unison_refs}")

para_addr_bytes = struct.pack('<I', 0x081AF528)
pos = 0
para_refs = 0
while True:
    pos = cm4.find(para_addr_bytes, pos)
    if pos == -1:
        break
    addr = CM4_BASE + pos
    if para_refs < 10:
        print(f"    Para ptr ref @ 0x{addr:08X}")
    para_refs += 1
    pos += 1
print(f"  Para ptr refs: {para_refs}")

# ============================================================
# 7. VST XML에서 Voice Mode 항목 확인
# ============================================================
print("\n" + "="*60)
print("7. VST XML Voice Mode 관련")
print("="*60)

import os
for xml_dir in ["/home/jth/hoon/minifreak/reference/"]:
    for root, dirs, files in os.walk(xml_dir):
        for f in files:
            if f.endswith(".xml"):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', errors='replace') as fh:
                        content = fh.read()
                    if 'voice_mode' in content.lower() or 'voice mode' in content.lower() or '"Poly"' in content or '"Dual"' in content:
                        for line in content.split('\n'):
                            if any(k in line.lower() for k in ['voice_mode', 'voice mode', '"poly"', '"dual"', '"mono"', '"unison"', '"para']):
                                print(f"  {f}: {line.strip()[:120]}")
                except:
                    pass

# ============================================================
# 8. CM4 전체에서 "Polyphony" 또는 "Polyphonic" 검색
# ============================================================
print("\n" + "="*60)
print("8. 'Poly' 관련 문자열 전체 (Polyphony 등 포함)")
print("="*60)

for kw in [b"Polyph", b"Polyphon", b"Poly Mode", b"Polymod", b"Polymod"]:
    pos = 0
    while True:
        pos = cm4.find(kw, pos)
        if pos == -1:
            break
        end = cm4.find(b'\x00', pos)
        if end == -1 or end - pos > 60:
            end = pos + len(kw)
        raw = cm4[pos:end]
        if all(32 <= b < 127 for b in raw):
            addr = CM4_BASE + pos
            print(f"    0x{addr:08X}: \"{raw.decode('ascii')}\"")
        pos += 1

# ============================================================
# 9. Voice Mode enum 인덱스 재구성
# ============================================================
print("\n" + "="*60)
print("9. Voice Mode 인덱스 구조 분석")
print("="*60)

# VST XML에서 Voice Mode 항목의 processorvalue 확인
import xml.etree.ElementTree as ET

for xml_path in ["/home/jth/hoon/minifreak/reference/minifreak_vst_params.xml",
                 "/home/jth/hoon/minifreak/reference/minifreak_internal_params.xml"]:
    if not os.path.exists(xml_path):
        continue
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for param in root.iter('param'):
            name = param.get('name', '')
            if 'voice' in name.lower() or 'mode' in name.lower():
                print(f"\n  {os.path.basename(xml_path)}: param '{name}'")
                for item in param.iter('item'):
                    print(f"    text=\"{item.get('text', '')}\" processorvalue=\"{item.get('processorvalue', '')}\"")
    except Exception as e:
        print(f"  XML parse error ({xml_path}): {e}")

print("\n=== P13-4 완료 ===")
