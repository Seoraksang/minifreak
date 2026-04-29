#!/usr/bin/env python3
"""P13-1: Spice/Dice 확률 LUT 정량값 추출"""
import struct, json, re, sys

CM7_BIN = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin"

with open(CM7_BIN, "rb") as f:
    data = f.read()

print(f"CM7 binary size: {len(data)} bytes ({len(data)/1024:.1f} KB)")

# Step 1: CM7 베이스 주소 검증
# STM32H745: CM7 = Bank 1 = 0x08000000
# 첫 4바이트 = 초기 SP, offset 0x04 = Reset Vector
initial_sp = struct.unpack_from('<I', data, 0)[0]
reset_vector = struct.unpack_from('<I', data, 4)[0]
print(f"Initial SP: 0x{initial_sp:08X}")
print(f"Reset Vector: 0x{reset_vector:08X}")

# Reset Vector가 Thumb mode(bit0=1)인지 확인
if reset_vector & 1:
    code_addr = reset_vector & ~1
    print(f"Thumb mode, code addr: 0x{code_addr:08X}")
    # code_addr가 파일 크기보다 크면 베이스 != 0
    if code_addr > len(data):
        print(f"  → code_addr > file size → image base != 0x00000000")
        # 베이스 추정: code_addr = base + offset
        # offset은 보통 0x200~0x1000 (vector table + some code)
        # base = code_addr - offset
        print(f"  → Possible base: 0x{code_addr - 0x200:08X} ~ 0x{code_addr:08X}")

# Phase 9에서 CM7 베이스는 0x08000000으로 사용됨 (LUT 주소 0x08067FDC 기준)
# 오프셋 = 0x08067FDC - 0x08000000 = 0x67FDC
# 파일 크기 524192 = 0x80000 → 0x67FDC는 파일 내에 존재
CM7_BASE = 0x08000000
print(f"\n=== CM7_BASE = 0x{CM7_BASE:08X} (assumed) ===")
print(f"File size = 0x{len(data):X} = {len(data)} bytes")
print(f"Max address = 0x{CM7_BASE + len(data):08X}")

# Step 2: LUT dump
LUT_TARGETS = [
    {"name": "spice_exp_lut", "addr": 0x08067FDC, "size": 64, "fmt": "uint8"},
    {"name": "arp_walk_lut", "addr": 0x080546C4, "size": 64, "fmt": "uint8"},
    {"name": "env_time_scale", "addr": 0x0806D330, "size": 256, "fmt": "float32"},
]

results = []
for t in LUT_TARGETS:
    offset = t["addr"] - CM7_BASE
    if offset < 0 or offset + t["size"] > len(data):
        results.append({**t, "error": f"out of range (offset=0x{offset:X}, file_size=0x{len(data):X})"})
        continue
    chunk = data[offset:offset + t["size"]]

    if t["fmt"] == "uint8":
        values = list(chunk)
    elif t["fmt"] == "float32":
        n = t["size"] // 4
        values = list(struct.unpack(f"<{n}f", chunk))

    results.append({**t, "offset": hex(offset), "raw_hex": chunk.hex(), "values": values})

# JSON 저장
out_json = "/home/jth/hoon/minifreak/firmware/analysis/spice_dice_lut_dump.json"
with open(out_json, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nJSON saved: {out_json}")

# Step 3: Walk LUT 분석
print("\n" + "="*60)
print("=== Walk LUT (매뉴얼: 25/50/25 = 64/128/64 in uint8) ===")
walk_result = results[1]
if "error" in walk_result:
    print(f"ERROR: {walk_result['error']}")
else:
    walk = walk_result["values"]
    print(f"Address: 0x{walk_result['addr']:08X}")
    print(f"Raw hex: {walk_result['raw_hex']}")
    for i in range(8):
        row = walk[i*8:(i+1)*8]
        row_sum = sum(row)
        if row_sum > 0:
            pct = [f"{v/row_sum*100:.1f}%" for v in row]
        else:
            pct = ["0%"] * 8
        print(f"  slot {i}: {row} (sum={row_sum}) → {pct}")

    # 25/50/25 패턴 검색
    # 매뉴얼 Walk: Up=25%, Same=50%, Down=25%
    # uint8 정규화: 64/128/64 (합=256) 또는 63/127/63 (합=253)
    print("\n  [25/50/25 패턴 검색]")
    for i in range(8):
        row = walk[i*8:(i+1)*8]
        # 다양한 3-값 패턴 검색 (값이 3개만 non-zero인 경우)
        nonzero = [(j, v) for j, v in enumerate(row) if v > 0]
        if len(nonzero) == 3:
            vals = [v for _, v in nonzero]
            total = sum(vals)
            if total > 0:
                ratios = [v/total for v in vals]
                print(f"  slot {i}: positions={[j for j,_ in nonzero]}, values={vals}, ratios={[f'{r*100:.1f}%' for r in ratios]}")

# Step 4: Spice Exp LUT 분석
print("\n" + "="*60)
print("=== Spice Exp LUT (매뉴얼 명시 없음, 분포 형태 확인) ===")
spice_result = results[0]
if "error" in spice_result:
    print(f"ERROR: {spice_result['error']}")
else:
    spice = spice_result["values"]
    print(f"Address: 0x{spice_result['addr']:08X}")
    nonzero = [(i, v) for i, v in enumerate(spice) if v > 0]
    print(f"Non-zero entries: {len(nonzero)} / {len(spice)}")
    if nonzero:
        print(f"Range: [{nonzero[0][1]}..{nonzero[-1][1]}]")
        total = sum(v for _, v in nonzero)
        print(f"Sum: {total}")
        print("Values:")
        for idx, val in nonzero:
            pct = val/total*100 if total > 0 else 0
            print(f"  [{idx:2d}] = {val:3d} ({pct:.1f}%)")

# Step 5: Env Time Scale
print("\n" + "="*60)
print("=== Env Time Scale (float32, 매뉴얼 관련 없음) ===")
env_result = results[2]
if "error" in env_result:
    print(f"ERROR: {env_result['error']}")
else:
    env_vals = env_result["values"]
    print(f"Address: 0x{env_result['addr']:08X}")
    print(f"First 16 values: {env_vals[:16]}")
    # 범위 확인
    valid = [v for v in env_vals if v > 0 and v < 1e6]
    if valid:
        print(f"Range: {min(valid):.4f} ~ {max(valid):.4f}")

# Step 6: CM7 전체에서 Spice/Dice 관련 문자열 검색
print("\n" + "="*60)
print("=== CM7에서 Spice/Dice 관련 문자열 검색 ===")
keywords = [b"Walk", b"Mutate", b"Rand", b"Spice", b"Dice", b"Octave",
            b"probability", b"weight", b"random", b"arp_walk", b"arp_rand"]
for kw in keywords:
    pos = 0
    found = []
    while True:
        pos = data.find(kw, pos)
        if pos == -1:
            break
        addr = CM7_BASE + pos
        # null-terminated string 읽기
        end = data.find(b'\x00', pos)
        if end == -1 or end - pos > 80:
            end = pos + len(kw)
        raw = data[pos:end]
        if all(32 <= b < 127 for b in raw):
            found.append((addr, raw.decode('ascii')))
        pos += 1
    if found:
        print(f"\n  '{kw.decode()}' — {len(found)}개 발견:")
        for a, s in found[:10]:
            print(f"    0x{a:08X}: \"{s}\"")

# Step 7: Walk LUT 근처(±512바이트) 상세 스캔
print("\n" + "="*60)
print("=== Walk LUT 근처 상세 스캔 (0x080544C4 ~ 0x080548C4) ===")
walk_offset = 0x080546C4 - CM7_BASE
scan_start = max(0, walk_offset - 512)
scan_end = min(len(data), walk_offset + 512)

# 문자열 클러스터 추출
pos = scan_start
cluster = []
while pos < scan_end:
    while pos < scan_end and data[pos] == 0:
        pos += 1
    if pos >= scan_end:
        break
    end = data.find(b'\x00', pos)
    if end == -1 or end > scan_end:
        break
    raw = data[pos:end]
    if len(raw) > 1 and all(32 <= b < 127 for b in raw):
        addr = CM7_BASE + pos
        cluster.append((addr, raw.decode('ascii')))
        pos = end + 1
    else:
        pos += 1

if cluster:
    print(f"  문자열 {len(cluster)}개 발견:")
    for a, s in cluster[:30]:
        print(f"    0x{a:08X}: \"{s}\"")
else:
    print("  문자열 없음 — 순수 데이터 영역")

# Step 8: Mutate/Rand Oct LUT 탐색 — 매뉴얼 확률과 일치할 만한 byte 패턴 검색
print("\n" + "="*60)
print("=== Mutate (75/5/5/5/5/3/2) / Rand Oct (75/15/7/3) LUT 탐색 ===")

# Mutate: 7 values, 합=100, 패턴 75/5/5/5/5/3/2
# uint8 scale: 192/13/13/13/13/8/5 (합=257) 또는 원본 75/5/5/5/5/3/2 (합=100)
# Rand Oct: 4 values, 합=100, 75/15/7/3
# uint8 scale: 192/38/18/8 (합=256)

def search_pattern(data, pattern, name, min_align=1):
    """pattern의 bytes를 data에서 검색 (연속 배치 가정)"""
    # 원본 scale
    total = sum(pattern)
    # uint8 정규화
    if total <= 256:
        u8_pattern = pattern
    else:
        u8_pattern = [round(v * 256 / total) for v in pattern]
    
    found = []
    # 정확한 패턴 검색
    pat_bytes = bytes(u8_pattern)
    pos = 0
    while True:
        pos = data.find(pat_bytes, pos)
        if pos == -1:
            break
        addr = CM7_BASE + pos
        found.append((addr, u8_pattern))
        pos += 1
    
    # 근사 패턴 검색 (±2 오차)
    if not found:
        for align in range(min_align, 4):
            for start_pos in range(0, len(data) - len(pattern) * align, align):
                match = True
                vals = []
                for i, expected in enumerate(u8_pattern):
                    actual = data[start_pos + i * align]
                    vals.append(actual)
                    if abs(actual - expected) > 3:
                        match = False
                        break
                if match and len(vals) == len(u8_pattern):
                    addr = CM7_BASE + start_pos
                    found.append((addr, vals))
                    if len(found) >= 5:
                        break
            if found:
                break
    
    return found

mutate_pattern = [75, 5, 5, 5, 5, 3, 2]
rand_oct_pattern = [75, 15, 7, 3]

print(f"\n  Mutate 패턴 검색 ({mutate_pattern}, 합={sum(mutate_pattern)}):")
mutate_hits = search_pattern(data, mutate_pattern, "Mutate")
if mutate_hits:
    for addr, vals in mutate_hits[:5]:
        print(f"    FOUND at 0x{addr:08X}: {vals}")
else:
    print("    NOT FOUND (exact match)")
    # uint8 정규화 시도
    total = sum(mutate_pattern)
    u8 = [round(v * 256 / total) for v in mutate_pattern]
    print(f"    uint8 normalized: {u8} (합={sum(u8)})")
    pat = bytes(u8)
    pos = 0
    while True:
        pos = data.find(pat, pos)
        if pos == -1:
            break
        addr = CM7_BASE + pos
        ctx = data[pos:pos+32]
        print(f"    FOUND (u8) at 0x{addr:08X}: {list(ctx[:7])}")
        pos += 1

print(f"\n  Rand Oct 패턴 검색 ({rand_oct_pattern}, 합={sum(rand_oct_pattern)}):")
ro_hits = search_pattern(data, rand_oct_pattern, "RandOct")
if ro_hits:
    for addr, vals in ro_hits[:5]:
        print(f"    FOUND at 0x{addr:08X}: {vals}")
else:
    print("    NOT FOUND (exact match)")
    total = sum(rand_oct_pattern)
    u8 = [round(v * 256 / total) for v in rand_oct_pattern]
    print(f"    uint8 normalized: {u8} (합={sum(u8)})")

# Step 9: 0x080546C4 근처에서 Walk 관련 확률 데이터 더 넓게 스캔
print("\n" + "="*60)
print("=== Walk LUT 주변 ±1024바이트 분석 ===")
walk_off = 0x080546C4 - CM7_BASE
region = data[max(0,walk_off-1024):walk_off+1024]
print(f"  Walk LUT offset: 0x{walk_off:X}")
print(f"  Scan region: 0x{max(0,walk_off-1024):X} ~ 0x{walk_off+1024:X}")

# non-zero byte 카운트
nonzero_count = sum(1 for b in region if b != 0)
print(f"  Non-zero bytes: {nonzero_count}/{len(region)}")

# 8-byte aligned blocks에서 확률 패턴(합~255) 검색
print("\n  8-value blocks with sum near 255:")
for off in range(0, len(region) - 8, 4):
    block = list(region[off:off+8])
    block_sum = sum(block)
    if 200 <= block_sum <= 300 and all(v <= 255 for v in block):
        addr = CM7_BASE + max(0, walk_off-1024) + off
        if 0x080546C0 <= addr <= 0x08054700:  # Walk LUT 근처만
            nonzero_in_block = [(i,v) for i,v in enumerate(block) if v > 0]
            if 3 <= len(nonzero_in_block) <= 5:
                print(f"    0x{addr:08X}: {block} (sum={block_sum})")

print("\n=== P13-1 LUT dump 완료 ===")
