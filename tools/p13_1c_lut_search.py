#!/usr/bin/env python3
"""P13-1c: Spice/Dice 확률 LUT 재탐색 — Walk/Mutate/RandOct 패턴 기반"""
import struct, re

CM7_BIN = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin"
CM4_BIN = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
CM7_BASE = 0x08000000
CM4_BASE = 0x08120000

with open(CM7_BIN, "rb") as f:
    cm7 = f.read()
with open(CM4_BIN, "rb") as f:
    cm4 = f.read()

print("="*60)
print("Phase 9 분석에서 Spice/Dice LUT 주소 출처 확인")
print("="*60)

# Phase 9 mod matrix JSON에서 관련 주소 검색
import json, os
for json_file in os.listdir("/home/jth/hoon/minifreak/firmware/analysis/"):
    if json_file.endswith(".json"):
        path = f"/home/jth/hoon/minifreak/firmware/analysis/{json_file}"
        try:
            with open(path) as f:
                content = f.read()
            if "0x08067FDC" in content or "0x080546C4" in content or "spice" in content.lower() or "dice" in content.lower() or "walk" in content.lower():
                print(f"\n  Found in {json_file}:")
                for keyword in ["0x08067FDC", "0x080546C4", "spice", "dice", "Spice", "Dice", "Walk", "walk", "Mutate", "mutate"]:
                    idx = content.lower().find(keyword.lower())
                    if idx >= 0:
                        ctx = content[max(0,idx-50):idx+100]
                        print(f"    ...{ctx}...")
                        break
        except:
            pass

# Phase 9 mod matrix JSON 상세
print("\n" + "="*60)
for json_file in ["phase9_mod_matrix_v2.json", "phase9_mod_matrix_v3.json", "phase9_mod_matrix_dispatch.json"]:
    path = f"/home/jth/hoon/minifreak/firmware/analysis/{json_file}"
    if os.path.exists(path):
        with open(path) as f:
            data_j = json.load(f)
        if isinstance(data_j, dict):
            for k in data_j:
                kl = k.lower()
                if any(w in kl for w in ['spice', 'dice', 'walk', 'mutate', 'random', 'prob']):
                    print(f"\n  {json_file}['{k}']:")
                    v = data_j[k]
                    if isinstance(v, (dict, list)):
                        print(f"    {json.dumps(v, indent=2)[:500]}")
                    else:
                        print(f"    {v}")

print("\n" + "="*60)
print("CM4에서 Spice/Dice 관련 문자열 검색")
print("="*60)
keywords = [b"Spice", b"Dice", b"Walk", b"Mutate", b"Rand", b"Random", b"Octave",
            b"spice", b"dice", b"walk", b"mutate", b"rand", b"octave",
            b"probability", b"weight", b"ARP_WALK", b"ARP_MUTATE", b"ARP_RAND"]
for kw in keywords:
    pos = 0
    found = []
    while True:
        pos = cm4.find(kw, pos)
        if pos == -1:
            break
        end = cm4.find(b'\x00', pos)
        if end == -1 or end - pos > 80:
            end = pos + len(kw)
        raw = cm4[pos:end]
        if all(32 <= b < 127 for b in raw) and len(raw) > 2:
            addr = CM4_BASE + pos
            found.append((addr, raw.decode('ascii')))
        pos += 1
    if found:
        print(f"\n  '{kw.decode()}' — {len(found)}개:")
        for a, s in found[:8]:
            print(f"    0x{a:08X}: \"{s}\"")

print("\n" + "="*60)
print("CM4에서 Walk/Mutate/Rand Oct 관련 enum 탐색")
print("="*60)

# Arp mode enum 근처에서 Walk/Mutate/Rand 관련 문자열
# Arp enum @ 0x081AEC3C
arp_region_start = 0x081AEC3C - CM4_BASE
arp_region_end = arp_region_start + 256
cluster = []
pos = arp_region_start
while pos < arp_region_end and pos < len(cm4):
    while pos < arp_region_end and cm4[pos] == 0:
        pos += 1
    if pos >= arp_region_end:
        break
    end = cm4.find(b'\x00', pos)
    if end == -1 or end > arp_region_end:
        break
    raw = cm4[pos:end]
    if len(raw) > 0 and all(32 <= b < 127 for b in raw):
        addr = CM4_BASE + pos
        cluster.append((addr, raw.decode('ascii')))
    pos = end + 1
print(f"\n  Arp enum 근처 (0x081AEC3C~0x081AED3C):")
for a, s in cluster:
    print(f"    0x{a:08X}: \"{s}\"")

# Arp 수식어(qualifier) 검색 — Phase 8에서 확인된 항목
# Repeat, Ratchet, Rand Oct, Mutate
print("\n  Arp 수식어 전체 검색:")
for kw in [b"Repeat", b"Ratchet", b"Rand Oct", b"Mutate", b"RandOct", b"Walk"]:
    pos = 0
    while True:
        pos = cm4.find(kw, pos)
        if pos == -1:
            break
        end = cm4.find(b'\x00', pos)
        if end == -1 or end - pos > 40:
            end = pos + len(kw)
        raw = cm4[pos:end]
        if all(32 <= b < 127 for b in raw):
            addr = CM4_BASE + pos
            ctx_before = cm4[max(0,pos-20):pos]
            ctx_after = cm4[end:min(len(cm4),end+20)]
            print(f"    0x{addr:08X}: \"{raw.decode('ascii')}\" (before: {ctx_before.hex()}, after: {ctx_after.hex()})")
        pos += 1

# CM4에서 "Walk"가 Arp Walk인지 확인
print("\n" + "="*60)
print("CM4 바이너리 전체 'Walk' 검색 + 컨텍스트")
print("="*60)
pos = 0
while True:
    pos = cm4.find(b"Walk", pos)
    if pos == -1:
        break
    end = cm4.find(b'\x00', pos)
    if end == -1 or end - pos > 60:
        end = pos + 4
    raw = cm4[pos:end]
    if all(32 <= b < 127 for b in raw):
        addr = CM4_BASE + pos
        # 주변 문자열 클러스터
        scan_start = max(0, pos - 64)
        scan_end = min(len(cm4), pos + 64)
        nearby = []
        p = scan_start
        while p < scan_end:
            while p < scan_end and cm4[p] == 0:
                p += 1
            if p >= scan_end:
                break
            e = cm4.find(b'\x00', p)
            if e == -1 or e > scan_end:
                break
            r = cm4[p:e]
            if len(r) > 1 and all(32 <= b < 127 for b in r):
                nearby.append((CM4_BASE + p, r.decode('ascii')))
            p = e + 1
        print(f"\n  0x{addr:08X}: \"{raw.decode('ascii')}\"")
        for na, ns in nearby:
            marker = " <<<" if na == addr else ""
            print(f"    0x{na:08X}: \"{ns}\"{marker}")
    pos += 1

# 매뉴얼 기준: Walk = Arp 수식어(qualifier)
# Walk 모드: 25% up, 50% same, 25% down
# Walk 8 슬롯 × 8 step 구조?
# → CM4 바이너리에서 uint8 패턴 [64, 128, 64] 또는 [63, 127, 63] 검색
print("\n" + "="*60)
print("CM4에서 Walk 25/50/25 패턴 검색 (uint8 [64,128,64] 또는 [63,127,63])")
print("="*60)
for pattern_name, pattern in [("64/128/64", [64, 128, 64]), ("63/127/63", [63, 127, 63])]:
    pat_bytes = bytes(pattern)
    pos = 0
    hits = 0
    while True:
        pos = cm4.find(pat_bytes, pos)
        if pos == -1:
            break
        addr = CM4_BASE + pos
        # 컨텍스트
        ctx = cm4[max(0,pos-8):pos+24]
        if hits < 10:
            print(f"  {pattern_name} at 0x{addr:08X}: ctx={ctx.hex()}")
        hits += 1
        pos += 1
    print(f"  {pattern_name}: 총 {hits}건")

# CM7에서도 검색
print("\nCM7에서 Walk 25/50/25 패턴 검색:")
for pattern_name, pattern in [("64/128/64", [64, 128, 64]), ("63/127/63", [63, 127, 63])]:
    pat_bytes = bytes(pattern)
    pos = 0
    hits = 0
    while True:
        pos = cm7.find(pat_bytes, pos)
        if pos == -1:
            break
        addr = CM7_BASE + pos
        if hits < 10:
            ctx = cm7[max(0,pos-8):pos+24]
            print(f"  {pattern_name} at 0x{addr:08X}: ctx={ctx.hex()}")
        hits += 1
        pos += 1
    print(f"  {pattern_name}: 총 {hits}건")

# Mutate 75/5/5/5/5/3/2 → uint8 [192,13,13,13,13,8,5] (×256/100)
# 또는 원본 [75,5,5,5,5,3,2]
print("\n" + "="*60)
print("Mutate 75/5/5/5/5/3/2 패턴 검색 (양 바이너리)")
print("="*60)
for bin_name, bin_data, base in [("CM4", cm4, CM4_BASE), ("CM7", cm7, CM7_BASE)]:
    for pattern_name, pattern in [
        ("raw 75/5/5/5/5/3/2", [75, 5, 5, 5, 5, 3, 2]),
        ("u8 192/13/13/13/13/8/5", [192, 13, 13, 13, 13, 8, 5]),
    ]:
        pat_bytes = bytes(pattern)
        pos = 0
        hits = 0
        while True:
            pos = bin_data.find(pat_bytes, pos)
            if pos == -1:
                break
            addr = base + pos
            if hits < 5:
                ctx = bin_data[pos:pos+len(pattern)+8]
                print(f"  {bin_name} {pattern_name} at 0x{addr:08X}: {list(ctx)}")
            hits += 1
            pos += 1
        if hits > 0:
            print(f"  {bin_name} {pattern_name}: 총 {hits}건")

# Rand Oct 75/15/7/3 → uint8 [192,38,18,8] (×256/100)
print("\n" + "="*60)
print("Rand Oct 75/15/7/3 패턴 검색 (양 바이너리)")
print("="*60)
for bin_name, bin_data, base in [("CM4", cm4, CM4_BASE), ("CM7", cm7, CM7_BASE)]:
    for pattern_name, pattern in [
        ("raw 75/15/7/3", [75, 15, 7, 3]),
        ("u8 192/38/18/8", [192, 38, 18, 8]),
    ]:
        pat_bytes = bytes(pattern)
        pos = 0
        hits = 0
        while True:
            pos = bin_data.find(pat_bytes, pos)
            if pos == -1:
                break
            addr = base + pos
            if hits < 5:
                ctx = bin_data[pos:pos+len(pattern)+8]
                print(f"  {bin_name} {pattern_name} at 0x{addr:08X}: {list(ctx)}")
            hits += 1
            pos += 1
        if hits > 0:
            print(f"  {bin_name} {pattern_name}: 총 {hits}건")

print("\n=== P13-1c 완료 ===")
