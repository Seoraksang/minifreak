#!/usr/bin/env python3
"""P13-1d: Walk 25/50/25 히트 상세 검증 + CM7 지수 LUT 분석 + VST XML 교차검증"""
import struct, re, json, os

CM4_BIN = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
CM7_BIN = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin"
CM4_BASE = 0x08120000
CM7_BASE = 0x08000000

with open(CM4_BIN, "rb") as f:
    cm4 = f.read()
with open(CM7_BIN, "rb") as f:
    cm7 = f.read()

# ============================================================
# 1. CM4 Walk 64/128/64 히트 상세 분석
# ============================================================
print("="*60)
print("1. CM4 Walk 64/128/64 히트 상세 분석")
print("="*60)

hits = [
    (0x0816F598 - CM4_BASE, "0x0816F598"),
    (0x08196EC1 - CM4_BASE, "0x08196EC1"),
]

for off, addr_str in hits:
    print(f"\n  히트 @ {addr_str} (offset=0x{off:X}):")
    # 앞뒤 64바이트 hex dump
    region = cm4[max(0,off-32):off+64]
    for i in range(0, len(region), 16):
        hex_part = ' '.join(f'{b:02X}' for b in region[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in region[i:i+16])
        print(f"    {addr_str}{'-'+hex(off-32+i) if i < 32 else '+'+hex(i-32) if i >= 32 else ''}: {hex_part}  {ascii_part}")
    
    # float32로 읽어보기
    floats_region = cm4[off-16:off+48]
    floats = struct.unpack(f'<{len(floats_region)//4}f', floats_region)
    print(f"    As float32: {[f'{v:.6f}' for v in floats]}")

# ============================================================
# 2. CM7 Spice 지수 LUT 상세 분석
# ============================================================
print("\n" + "="*60)
print("2. CM7 Spice 지수 LUT @ 0x08067FDC 상세 분석")
print("="*60)

offset = 0x08067FDC - CM7_BASE
# float32로 읽기
chunk = cm7[offset:offset+256]
floats = struct.unpack(f'<{len(chunk)//4}f', chunk)
print(f"  Float32 values (first 32):")
for i in range(0, min(32, len(floats)), 4):
    vals = floats[i:i+4]
    print(f"    [{i:2d}..{i+3:2d}]: " + "  ".join(f"{v:12.6f}" for v in vals))

# 지수적 증가 확인
valid = [v for v in floats if v > 0 and v < 1e6]
if valid:
    ratios = [valid[i+1]/valid[i] for i in range(min(20, len(valid)-1))]
    print(f"\n  연속 비율 (first 20): {[f'{r:.3f}' for r in ratios]}")
    # 기하급수적인지 확인
    import statistics
    if len(ratios) > 2:
        mean_ratio = statistics.geometric_mean(ratios)
        print(f"  기하평균 비율: {mean_ratio:.4f}")

# uint8로도 읽기 (2바이트 간격)
print(f"\n  uint8 every-2 (address 0x08067FDC):")
chunk_u8 = cm7[offset:offset+64]
even_bytes = [chunk_u8[i] for i in range(0, len(chunk_u8), 2)]
odd_bytes = [chunk_u8[i] for i in range(1, len(chunk_u8), 2)]
print(f"  Even offsets: {even_bytes[:16]}")
print(f"  Odd offsets: {odd_bytes[:16]}")

# ============================================================
# 3. CM7에서 ARP 관련 상수 검색
# ============================================================
print("\n" + "="*60)
print("3. CM7에서 ARP/Walk/Mutate 관련 문자열 검색")
print("="*60)

keywords = [b"Walk", b"Mutate", b"Rand", b"Spice", b"Dice", b"Octave", b"arp", b"ARP",
            b"walk", b"mutate", b"rand", b"spice", b"dice"]
for kw in keywords:
    pos = 0
    found = []
    while True:
        pos = cm7.find(kw, pos)
        if pos == -1:
            break
        end = cm7.find(b'\x00', pos)
        if end == -1 or end - pos > 60:
            end = pos + len(kw)
        raw = cm7[pos:end]
        if all(32 <= b < 127 for b in raw) and len(raw) > 2:
            addr = CM7_BASE + pos
            found.append((addr, raw.decode('ascii')))
        pos += 1
    if found:
        print(f"  '{kw.decode()}' — {len(found)}개:")
        for a, s in found[:5]:
            print(f"    0x{a:08X}: \"{s}\"")

# ============================================================
# 4. VST XML에서 Spice/Dice 확률 정보 검색
# ============================================================
print("\n" + "="*60)
print("4. VST XML에서 Spice/Dice 관련 정보 검색")
print("="*60)

xml_files = []
for root, dirs, files in os.walk("/home/jth/hoon/minifreak/reference/"):
    for f in files:
        if f.endswith(".xml"):
            xml_files.append(os.path.join(root, f))

for xml_path in xml_files:
    try:
        with open(xml_path, 'r', errors='replace') as f:
            content = f.read()
        lower = content.lower()
        hits = []
        for kw in ['spice', 'dice', 'walk', 'mutate', 'rand_oct', 'ratch', 'repeat', 'probability']:
            idx = lower.find(kw)
            while idx >= 0:
                ctx = content[max(0,idx-40):idx+80]
                hits.append((kw, ctx))
                idx = lower.find(kw, idx + len(kw))
        if hits:
            print(f"\n  {os.path.basename(xml_path)}:")
            for kw, ctx in hits[:8]:
                print(f"    [{kw}] ...{ctx.strip()[:100]}...")
    except:
        pass

# ============================================================
# 5. CM4 SpiceDice 클래스 영역 상세 스캔
# ============================================================
print("\n" + "="*60)
print("5. CM4 SpiceDice 영역 (0x081B5718) 상세 스캔")
print("="*60)

# "SpiceDice" @ 0x081B5718
sd_off = 0x081B5718 - CM4_BASE
region = cm4[sd_off:sd_off+512]
# 문자열 클러스터 추출
pos = 0
cluster = []
while pos < len(region):
    while pos < len(region) and region[pos] == 0:
        pos += 1
    if pos >= len(region):
        break
    end = region.find(b'\x00', pos)
    if end == -1:
        break
    raw = region[pos:end]
    if len(raw) > 1 and all(32 <= b < 127 for b in raw):
        addr = 0x081B5718 + pos
        cluster.append((addr, raw.decode('ascii')))
    pos = end + 1

print(f"  SpiceDice 근처 문자열 {len(cluster)}개:")
for a, s in cluster:
    print(f"    0x{a:08X}: \"{s}\"")

# ============================================================
# 6. CM4에서 Spice/Dice enum 전체 클러스터 (0x081AEBF8~0x081AEC90)
# ============================================================
print("\n" + "="*60)
print("6. CM4 Spice/Dice/Arp qualifier 전체 클러스터")
print("="*60)

# Dice @ 0x081AEBF8 부터
start = 0x081AEBF0 - CM4_BASE
end = 0x081AED00 - CM4_BASE
region = cm4[start:end]
pos = 0
cluster = []
while pos < len(region):
    while pos < len(region) and region[pos] == 0:
        pos += 1
    if pos >= len(region):
        break
    e = region.find(b'\x00', pos)
    if e == -1:
        break
    raw = region[pos:e]
    if len(raw) > 0 and all(32 <= b < 127 for b in raw):
        addr = 0x081AEBF0 + pos
        cluster.append((addr, raw.decode('ascii')))
    pos = e + 1

print(f"  문자열 {len(cluster)}개:")
for a, s in cluster:
    print(f"    0x{a:08X}: \"{s}\"")
    # 간격 표시
    if len(cluster) > 1:
        idx = [ca for ca, cs in cluster].index(a)
        if idx > 0:
            prev_addr = cluster[idx-1][0]
            gap = a - prev_addr - len(cluster[idx-1][1]) - 1
            print(f"             (gap: {gap} bytes from prev)")

# ============================================================
# 7. mf_enums.py에서 Spice/Dice 관련 enum 확인
# ============================================================
print("\n" + "="*60)
print("7. mf_enums.py에서 Spice/Dice/Arp 관련 enum")
print("="*60)

mf_path = "/home/jth/hoon/minifreak/tools/mf_enums.py"
try:
    with open(mf_path) as f:
        mf_content = f.read()
    # Spice/Dice/Arp 관련 라인
    for line_num, line in enumerate(mf_content.split('\n'), 1):
        if any(kw in line.lower() for kw in ['spice', 'dice', 'walk', 'mutate', 'rand_oct', 'ratchet', 'repeat', 'arp_qual', 'arp_mode']):
            print(f"  L{line_num}: {line.rstrip()}")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================
# 8. CM4에서 확률 관련 상수 패턴 광범위 검색
# ============================================================
print("\n" + "="*60)
print("8. CM4에서 3-value 확률 패턴 광범위 검색 (합=255, 간격=4)")
print("="*60)

# Walk = 3 values: 64, 128, 64 (sum=256) at 4-byte intervals
# 또는 다른 정규화
for spacing in [1, 2, 4]:
    count = 0
    for off in range(0, len(cm4) - spacing * 3):
        v0 = cm4[off]
        v1 = cm4[off + spacing]
        v2 = cm4[off + 2 * spacing]
        s = v0 + v1 + v2
        if s == 255 and v0 > 0 and v2 > 0 and v1 > v0 and v1 > v2:
            # 3-value 패턴, 합=255, 중간값이 가장 큼 (25/50/25 형태)
            addr = CM4_BASE + off
            ratio0 = v0 / s * 100
            ratio1 = v1 / s * 100
            ratio2 = v2 / s * 100
            if 20 <= ratio0 <= 30 and 45 <= ratio1 <= 55 and 20 <= ratio2 <= 30:
                count += 1
                if count <= 10:
                    print(f"  spacing={spacing} @ 0x{addr:08X}: [{v0}, {v1}, {v2}] = {ratio0:.1f}/{ratio1:.1f}/{ratio2:.1f}%")
    print(f"  spacing={spacing}: {count}건 (25±5 / 50±5 / 25±5%)")

# ============================================================
# 9. CM7에서도 동일 검색
# ============================================================
print("\n" + "="*60)
print("9. CM7에서 3-value 확률 패턴 검색")
print("="*60)

for spacing in [1, 2, 4]:
    count = 0
    for off in range(0, len(cm7) - spacing * 3):
        v0 = cm7[off]
        v1 = cm7[off + spacing]
        v2 = cm7[off + 2 * spacing]
        s = v0 + v1 + v2
        if s == 255 and v0 > 0 and v2 > 0 and v1 > v0 and v1 > v2:
            addr = CM7_BASE + off
            ratio0 = v0 / s * 100
            ratio1 = v1 / s * 100
            ratio2 = v2 / s * 100
            if 20 <= ratio0 <= 30 and 45 <= ratio1 <= 55 and 20 <= ratio2 <= 30:
                count += 1
                if count <= 10:
                    print(f"  spacing={spacing} @ 0x{addr:08X}: [{v0}, {v1}, {v2}] = {ratio0:.1f}/{ratio1:.1f}/{ratio2:.1f}%")
    print(f"  spacing={spacing}: {count}건 (25±5 / 50±5 / 25±5%)")

print("\n=== P13-1d 완료 ===")
