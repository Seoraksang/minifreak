#!/usr/bin/env python3
"""P13-1e: CM4 Walk LUT cluster 상세 분석 @ 0x081AD9E9"""
import struct

CM4_BIN = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
CM4_BASE = 0x08120000

with open(CM4_BIN, "rb") as f:
    cm4 = f.read()

# 핵심 cluster: spacing=2에서 [64, 127, 64] 패턴이 5건 cluster됨
# 0x081AD9F1, 0x081AD9FD, 0x081ADA01, 0x081ADA7F, 0x081ADB6F

print("="*60)
print("CM4 Walk LUT cluster 상세 hex dump")
print("="*60)

# 전체 영역 hex dump: 0x081AD9E0 ~ 0x081ADB80
start_addr = 0x081AD9E0
end_addr = 0x081ADB80
start_off = start_addr - CM4_BASE
end_off = end_addr - CM4_BASE
region = cm4[start_off:end_off]

for i in range(0, len(region), 16):
    addr = start_addr + i
    hex_part = ' '.join(f'{region[i+j]:02X}' if i+j < len(region) else '  ' for j in range(16))
    ascii_part = ''.join(chr(region[i+j]) if i+j < len(region) and 32 <= region[i+j] < 127 else '.' for j in range(16))
    print(f"  {addr:08X}: {hex_part}  {ascii_part}")

# [64, 127, 64] 패턴을 spacing=2로 추출 — 연속된 8슬롯×3값 Walk LUT인지 확인
print("\n" + "="*60)
print("spacing=2로 연속 [64, 127, 64] 패턴 추출")
print("="*60)

off = 0x081AD9E9 - CM4_BASE
# 8개 슬롯 × 3개 값 = 24 values, spacing=2
# 총 24×2 = 48 bytes
lut_region = cm4[off:off+48]
print(f"  Raw bytes: {lut_region.hex()}")

# spacing=2로 읽기
values = [lut_region[i] for i in range(0, len(lut_region), 2)]
print(f"  spacing=2 values: {values}")

# 3개씩 그룹화
for slot in range(8):
    if slot*3+2 < len(values):
        triple = values[slot*3:slot*3+3]
        s = sum(triple)
        if s > 0:
            pct = [v/s*100 for v in triple]
            print(f"  Slot {slot}: {triple} (sum={s}) → {pct[0]:.1f}/{pct[1]:.1f}/{pct[2]:.1f}%")

# float32로 읽기
print("\n  As float32:")
floats = struct.unpack(f'<{len(lut_region)//4}f', lut_region)
print(f"  {[f'{v:.6f}' for v in floats]}")

# 0x081AD9E9 앞뒤 256바이트에서 문자열 클러스터 확인
print("\n" + "="*60)
print("Walk LUT cluster 근처 문자열 (±256B)")
print("="*60)

wide_start = max(0, 0x081AD9E0 - CM4_BASE - 256)
wide_end = min(len(cm4), 0x081ADB80 - CM4_BASE + 256)
wide_region = cm4[wide_start:wide_end]

pos = 0
strings = []
while pos < len(wide_region):
    while pos < len(wide_region) and wide_region[pos] == 0:
        pos += 1
    if pos >= len(wide_region):
        break
    end = wide_region.find(b'\x00', pos)
    if end == -1:
        break
    raw = wide_region[pos:end]
    if len(raw) > 2 and all(32 <= b < 127 for b in raw):
        addr = CM4_BASE + wide_start + pos
        strings.append((addr, raw.decode('ascii')))
    pos = end + 1

print(f"  {len(strings)}개 문자열:")
for a, s in strings:
    marker = ""
    if 0x081AD9E0 <= a <= 0x081ADB80:
        marker = " <<< LUT 영역"
    print(f"    0x{a:08X}: \"{s}\"{marker}")

# Walk 8슬롯 구조 검증 — 매뉴얼: Walk mode는 8개 슬롯, 각 슬롯이 up/same/down 방향
# LUT가 8슬롯 × 3값(up%, same%, down%) = 24 values 인지 확인
# spacing=2면 48 bytes, 각 슬롯 = 6 bytes

print("\n" + "="*60)
print("매뉴얼 Walk 8슬롯 구조 가정 검증")
print("="*60)
print("  매뉴얼: Walk mode는 이전 음에서 up/same/down 방향 선택")
print("  확률: up=25%, same=50%, down=25% (각 슬롯 동일)")
print("  [64, 127, 64] = 25.1/49.8/25.1% ← 매뉴얼 25/50/25에 근사!")
print("  합=255가 아니라 255여야 함 (uint8 256-scale = 64/128/64, 합=256)")
print("  64+127+64=255 ← off-by-one? 또는 127이 128이어야 하나 컴파일러 최적화?")

# 더 넓은 영역에서 모든 [64, 127/128, 64] 패턴 검색
print("\n" + "="*60)
print("CM4 전체에서 [64, 127|128, 64] 패턴 (spacing=2)")
print("="*60)
count_127 = 0
count_128 = 0
for off in range(0, len(cm4) - 4):
    v0 = cm4[off]
    v1 = cm4[off + 2]
    v2 = cm4[off + 4]
    if v0 == 64 and v2 == 64 and v1 in (127, 128):
        addr = CM4_BASE + off
        if v1 == 127:
            count_127 += 1
        else:
            count_128 += 1
        if count_127 + count_128 <= 20:
            ctx = cm4[off:off+12]
            print(f"  0x{addr:08X}: [{v0}, {v1}, {v2}] ctx={ctx.hex()}")

print(f"\n  [64, 127, 64] 총 {count_127}건")
print(f"  [64, 128, 64] 총 {count_128}건")

# Arp Walk 관련 — Walk mode의 step 수가 8인지 확인
# 매뉴얼: Walk mode는 8 steps
# LUT가 8슬롯이면 각 슬롯이 1 step에 대한 up/same/down 확률
print("\n" + "="*60)
print("Walk LUT 구조 요약")
print("="*60)

# 0x081AD9F1부터 8개 [64,127,64] 패턴 읽기
off = 0x081AD9F1 - CM4_BASE
walk_lut = []
for i in range(8):
    o = off + i * 6  # spacing=2, 3 values per slot
    if o + 4 < len(cm4):
        v0 = cm4[o]
        v1 = cm4[o+2]
        v2 = cm4[o+4]
        walk_lut.append((v0, v1, v2))

print("  Walk LUT (8 slots × 3 values, spacing=2):")
for i, (a, b, c) in enumerate(walk_lut):
    s = a + b + c
    print(f"    Slot {i}: [{a}, {b}, {c}] sum={s}")

# Mutate LUT도 같은 영역 근처에 있을 가능성
# Mutate: 7 values (75, 5, 5, 5, 5, 3, 2)
# uint8: [192, 13, 13, 13, 13, 8, 5] (합=257) 또는 [191, 13, 13, 13, 13, 8, 5] (합=256)
print("\n" + "="*60)
print("Mutate LUT 탐색 — 같은 영역 근처")
print("="*60)

# Walk LUT 바로 뒤를 검색
off_after = 0x081AD9F1 - CM4_BASE + 48  # Walk 8 slots × 6 bytes
region_after = cm4[off_after:off_after+128]
print(f"  Walk LUT 직후 (0x{CM4_BASE + off_after:08X}):")
print(f"  Raw: {region_after[:64].hex()}")

# float32로 읽기
floats_after = struct.unpack(f'<{len(region_after)//4}f', region_after)
print(f"  Float32: {[f'{v:.6f}' for v in floats_after[:16]]}")

# 7-value uint8 패턴 검색 (spacing=2)
print("\n  7-value patterns (spacing=2) after Walk LUT:")
for start in range(0, len(region_after) - 14, 2):
    vals = [region_after[start + i*2] for i in range(7)]
    s = sum(vals)
    if s > 200 and s < 300 and vals[0] > 100:  # 첫 값이 크고 (75%)
        addr = CM4_BASE + off_after + start
        pct = [v/s*100 for v in vals]
        print(f"    0x{addr:08X}: {vals} sum={s} → {[f'{p:.1f}%' for p in pct]}")

# Rand Oct도 탐색
# 4 values (75, 15, 7, 3) → uint8 [192, 38, 18, 8] (합=256)
print("\n" + "="*60)
print("Rand Oct LUT 탐색 — Walk LUT 근처")
print("="*60)

for start in range(0, len(region_after) - 8, 2):
    vals = [region_after[start + i*2] for i in range(4)]
    s = sum(vals)
    if 240 <= s <= 270 and vals[0] > 150:  # 첫 값이 크고
        addr = CM4_BASE + off_after + start
        pct = [v/s*100 for v in vals]
        print(f"    0x{addr:08X}: {vals} sum={s} → {[f'{p:.1f}%' for p in pct]}")

# 더 넓은 범위에서 Rand Oct 패턴 검색
print("\n  전체 CM4에서 4-value uint8 패턴 (spacing=2, 첫값>150, 합~256):")
for off in range(0, len(cm4) - 8):
    vals = [cm4[off + i*2] for i in range(4)]
    s = sum(vals)
    if s == 256 and vals[0] >= 180:  # 75% = 192
        addr = CM4_BASE + off
        pct = [v/s*100 for v in vals]
        # Rand Oct: 75/15/7/3 → 192/38/18/8
        if vals[0] >= 185 and vals[1] >= 30 and vals[1] <= 45:
            print(f"    0x{addr:08X}: {vals} sum={s} → {[f'{p:.1f}%' for p in pct]}")

print("\n=== P13-1e 완료 ===")
