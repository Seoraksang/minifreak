#!/usr/bin/env python3
"""
Phase 15-1b + Audio Routing 2: 
1. CM4 바이너리에서 eEditParams enum 인덱스 추출 (deprecated/사용슬롯 분류)
2. CM7→FX 오디오 버퍼: AXI SRAM 오프셋 상세 분석
3. FX 코어 SPI/UART/SAI 통신 프로토콜 상세 분석
"""

import struct, os, re
from collections import OrderedDict

FW_DIR = "reference/firmware_extracted"
CM4_BIN = os.path.join(FW_DIR, "minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin")
CM7_BIN = os.path.join(FW_DIR, "minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin")
FX_BIN = os.path.join(FW_DIR, "minifreak_fx__fw1_0_0_2229__2025_06_18.bin")

BASE_CM4 = 0x08120000
BASE_CM7 = 0x08020000

def load_binary(path):
    with open(path, "rb") as f:
        return f.read()

def find_refs(data, addr):
    """4바이트 LE 패턴 검색"""
    packed = struct.pack('<I', addr)
    refs = []
    pos = 0
    while True:
        pos = data.find(packed, pos)
        if pos == -1:
            break
        refs.append(pos)
        pos += 4
    return refs

cm4 = load_binary(CM4_BIN)
cm7 = load_binary(CM7_BIN)
fx = load_binary(FX_BIN)


# ═══════════════════════════════════════════════════════════════════
# PART 1: eEditParams enum 포인터 테이블 분석
# ═══════════════════════════════════════════════════════════════════

print("=" * 70)
print("PART 1: eEditParams 포인터 테이블 → enum 인덱스 확정")
print("=" * 70)

# MNF_Edit::set(eEditParams, val) RTTI 주소 = 0x081aa101
# 이 주소 근처에서 eEditParams enum 문자열 포인터 테이블을 찾기
# 이미 확인: 문자열 클러스터 0x081AF904~0x081AFC34
# 포인터 테이블이 이 문자열들을 가리키는지 확인

edit_params = [
    ("Macro1 dest", 0x081AF904),
    ("Macro2 dest", 0x081AF910),
    ("Macro1 amount", 0x081AF91C),
    ("Macro2 amount", 0x081AF92C),
    ("Retrig Mode", 0x081AF93C),
    ("Legato Mono", 0x081AF948),
    ("Unison Count", 0x081AF954),
    ("Poly Allocation", 0x081AF964),
    ("Poly Steal Mode", 0x081AF974),
    ("Vibrato Depth", 0x081AF984),
    ("UnisonOn TO BE DEPRECATED", 0x081AF994),
    ("Matrix Src VeloAT", 0x081AF9B0),
    ("Osc1 Mod Quant", 0x081AF9C4),
    ("Osc2 Mod Quant", 0x081AF9D4),
    ("Release Curve", 0x081AF9E4),
    ("Osc Mix Non-Lin", 0x081AF9F4),
    ("Glide Sync", 0x081AFA04),
    ("Pitch 1", 0x081AFA10),
    ("Pitch 2", 0x081AFA18),
    ("Velo > VCF", 0x081AFA20),
    ("Kbd Src", 0x081AFA2C),
    ("Unison Mode", 0x081AFA34),
    ("Osc Free Run", 0x081AFA40),
    ("Mx Cursor", 0x081AFA50),
    ("Mx Page", 0x081AFA5C),
    ("Mx Mode", 0x081AFA64),
    ("Osc Sel", 0x081AFA6C),
    ("Fx Sel", 0x081AFA74),
    ("Lfo Sel", 0x081AFA7C),
    ("Octave Tune", 0x081AFA84),
    ("Tempo Div", 0x081AFA90),
    ("Seq Page", 0x081AFA9C),
    ("PlayState", 0x081AFAB4),
    ("RecState", 0x081AFAC0),
    ("RecMode", 0x081AFAC8),
    ("Cursor", 0x081AFAD0),
    ("MetronomeBeat", 0x081AFAD0),
    ("Playing Tempo", 0x081AFAE0),
    ("Seq Transpose", 0x081AFAF0),
    ("obsolete Rec Count-In", 0x081AFB00),
    ("Preset filter", 0x081AFB18),
    ("VST_IsConnected", 0x081AFB28),
    ("Pre Master Volume", 0x081AFB38),
    ("Favorites Page", 0x081AFB4C),
]

# 각 문자열 주소가 포인터 테이블에서 참조되는지 확인
print("\n--- eEditParams 문자열 참조(포인터 테이블) 검색 ---")
for name, addr in edit_params:
    refs = find_refs(cm4, addr)
    # 파일 오프셋으로 변환
    file_refs = [r for r in refs if r < len(cm4) - 4]
    if file_refs:
        print(f"  [{len(file_refs)} refs] 0x{addr:08X}: \"{name}\"")
        for r in file_refs[:3]:
            # 주변 데이터 읽기 (포인터 테이블인지 확인)
            ctx_start = max(0, r - 16)
            ctx_end = min(len(cm4), r + 20)
            ctx_bytes = cm4[ctx_start:ctx_end]
            ptrs = []
            for i in range(0, len(ctx_bytes) - 3, 4):
                v = struct.unpack_from('<I', ctx_bytes, i)[0]
                ptrs.append(f"0x{v:08X}")
            print(f"    → table context: {' '.join(ptrs)}")

# MNF_Edit::set RTTI 주소 (0x081aa101) 근처의 코드에서 eEditParams switch/case 패턴 찾기
print("\n--- MNF_Edit::set (0x081aa101) RTTI → 코드 영역 추적 ---")
rtti_refs = find_refs(cm4, 0x081aa101)
print(f"  RTTI 0x081aa101 참조: {len(rtti_refs)}개")
for r in rtti_refs:
    # 이 RTTI를 참조하는 코드 근처에서 상수 패턴 검색
    # eEditParams enum은 switch/case로 디스패치됨
    print(f"    at file offset 0x{r:06X} (vaddr 0x{r+BASE_CM4:08X})")


# ═══════════════════════════════════════════════════════════════════
# PART 2: AXI SRAM 오디오 버퍼 상세 분석
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PART 2: AXI SRAM 오디오 버퍼 오프셋 상세 분석")
print("=" * 70)

# 세 코어에서 AXI SRAM(0x24000000+) 오프셋 참조 수집
print("\n--- AXI SRAM 오프셋 참조 수집 ---")

for name, data, base in [("CM4", cm4, BASE_CM4), ("CM7", cm7, BASE_CM7), ("FX", fx, 0x08000000)]:
    offsets = {}
    for off in range(0, 0x40000, 4):
        target = 0x24000000 + off
        packed = struct.pack('<I', target)
        pos = 0
        count = 0
        while True:
            pos = data.find(packed, pos)
            if pos == -1:
                break
            count += 1
            pos += 4
        if count > 0:
            offsets[off] = count
    
    if offsets:
        sorted_offsets = sorted(offsets.items(), key=lambda x: -x[1])
        print(f"\n  {name} — AXI SRAM 오프셋 ({len(offsets)}개):")
        for off, cnt in sorted_offsets[:30]:
            addr = 0x24000000 + off
            print(f"    0x{addr:08X} (+0x{off:05X}): {cnt} refs")


# ═══════════════════════════════════════════════════════════════════
# PART 3: FX 코어 입출력 분석 — SPI/SAI/DMA
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PART 3: FX 코어 오디오 입출력 분석")
print("=" * 70)

# FX 코어에서 SAI2 참조 상세
print("\n--- FX SAI2 (0x40015800) 상세 오프셋 ---")
for off in range(0, 0x100, 4):
    target = 0x40015800 + off
    packed = struct.pack('<I', target)
    pos = fx.find(packed)
    if pos >= 0:
        print(f"  0x{target:08X}: file offset 0x{pos:06X}")

# FX 코어에서 DMA1 참조 상세
print("\n--- FX DMA1 (0x40020000) 상세 오프셋 ---")
dma_offsets = []
for off in range(0, 0x200, 4):
    target = 0x40020000 + off
    packed = struct.pack('<I', target)
    pos = 0
    count = 0
    while True:
        pos = fx.find(packed, pos)
        if pos == -1:
            break
        count += 1
        pos += 4
    if count > 0:
        dma_offsets.append((off, count))
        print(f"  0x{0x40020000+off:08X} (+0x{off:03X}): {count} refs")

# FX 코어에서 UART3 참조 상세
print("\n--- FX UART3 (0x40004800) 상세 오프셋 ---")
for off in range(0, 0x100, 4):
    target = 0x40004800 + off
    packed = struct.pack('<I', target)
    pos = fx.find(packed)
    if pos >= 0:
        print(f"  0x{target:08X}: file offset 0x{pos:06X}")

# FX 코어 BDMA 상세
print("\n--- FX BDMA (0x58020000) 상세 오프셋 ---")
for off in range(0, 0x200, 4):
    target = 0x58020000 + off
    packed = struct.pack('<I', target)
    pos = 0
    count = 0
    while True:
        pos = fx.find(packed, pos)
        if pos == -1:
            break
        count += 1
        pos += 4
    if count > 0:
        print(f"  0x{0x58020000+off:08X} (+0x{off:03X}): {count} refs")


# ═══════════════════════════════════════════════════════════════════
# PART 4: CM4→FX UART3/SPI 통신 프로토콜 분석
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PART 4: CM4↔FX 통신 프로토콜 분석")
print("=" * 70)

# Phase 4에서 확인: CM4↔FX = UART3(커맨드) + SPI(파라미터 스트림) + HSEM(동기화)
# CM4의 UART3 상세 오프셋
print("\n--- CM4 UART3 (0x40004800) 상세 오프셋 ---")
for off in range(0, 0x100, 4):
    target = 0x40004800 + off
    packed = struct.pack('<I', target)
    pos = 0
    count = 0
    while True:
        pos = cm4.find(packed, pos)
        if pos == -1:
            break
        count += 1
        pos += 4
    if count > 0:
        reg_name = ""
        if off == 0x00: reg_name = "CR1"
        elif off == 0x04: reg_name = "CR2"
        elif off == 0x08: reg_name = "CR3"
        elif off == 0x0C: reg_name = "BRR"
        elif off == 0x10: reg_name = "GTPR"
        elif off == 0x14: reg_name = "RTOR"
        elif off == 0x18: reg_name = "RQR"
        elif off == 0x1C: reg_name = "ISR"
        elif off == 0x20: reg_name = "ICR"
        elif off == 0x24: reg_name = "RDR"
        elif off == 0x28: reg_name = "TDR"
        print(f"  0x{target:08X} (USART_{reg_name}): {count} refs")

# CM4 SPI 참조 (SPI1/2/3)
print("\n--- CM4 SPI 상세 ---")
for spi_name, spi_base in [("SPI1", 0x40013000), ("SPI2", 0x40013400), ("SPI3", 0x40003800)]:
    total = 0
    for off in range(0, 0x40, 4):
        target = spi_base + off
        packed = struct.pack('<I', target)
        pos = 0
        count = 0
        while True:
            pos = cm4.find(packed, pos)
            if pos == -1:
                break
            count += 1
            pos += 4
        total += count
    if total > 0:
        print(f"  {spi_name} ({hex(spi_base)}): {total} total refs")

# FX 코어 SPI 참조
print("\n--- FX 코어 SPI 상세 ---")
for spi_name, spi_base in [("SPI1", 0x40013000), ("SPI2", 0x40013400), ("SPI3", 0x40003800)]:
    total = 0
    for off in range(0, 0x40, 4):
        target = spi_base + off
        packed = struct.pack('<I', target)
        pos = 0
        count = 0
        while True:
            pos = fx.find(packed, pos)
            if pos == -1:
                break
            count += 1
            pos += 4
        total += count
    if total > 0:
        print(f"  {spi_name} ({hex(spi_base)}): {total} total refs")


# ═══════════════════════════════════════════════════════════════════
# PART 5: CM7→FX 오디오 데이터 경로 추론
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PART 5: 오디오 데이터 경로 추론 요약")
print("=" * 70)

# CM7에서 오디오 출력이 어디로 가는지 추적
# CM7은 SAI/DAC 참조가 없음 → 오디오를 공유 메모리(AXI SRAM)에 씀
# CM4가 AXI SRAM에서 읽어서 SAI2/DAC로 출력

# CM7에서 공유 메모리 쓰기 패턴 검색 (STR 명령어 → AXI SRAM 주소)
# Thumb2 STR: 다양한 인코딩, 바이너리 직접 스캔은 어려움
# 대신 AXI SRAM 주소 범위를 참조하는 코드 위치를 찾기

print("\n--- CM7 AXI SRAM 참조 위치 (코드 분석용) ---")
for off in range(0, 0x40000, 4):
    target = 0x24000000 + off
    packed = struct.pack('<I', target)
    pos = 0
    while True:
        pos = cm7.find(packed, pos)
        if pos == -1:
            break
        # 이 참조가 코드 섹션에 있는지 확인 (CM7 코드: ~0x08021000~0x080A0000)
        if pos < 0x80000:  # 대략 코드 영역
            print(f"  0x{target:08X} ref at file offset 0x{pos:06X} (vaddr ~0x{pos+BASE_CM7:08X})")
        pos += 4

# Phase 4 기존 분석과 크로스체크
# Phase 4: CM4 SAI2 ChA/B → DMA2 Stream 0/4/7, 48kHz
# Phase 4: CM4↔FX 통신 = UART3(커맨드) + SPI(파라미터) + HSEM(동기화)
# Phase 7: FX 코어 SPI1/2/3, USART3, HSEM, DMA1/2

print("\n" + "=" * 70)
print("오디오 경로 추론")
print("=" * 70)
print("""
[CM7 DSP 코어]
  오실레이터/필터/VCA 렌더링 (float/NEON)
       ↓
  AXI SRAM 오디오 버퍼에 쓰기 (HSEM 동기화)
       ↓
[CM4 I/O 코어]
  AXI SRAM에서 오디오 버퍼 읽기
       ↓
  ┌──→ SAI2 (I2S) → Audio Codec → 아날로그 출력 (MAIN OUT)
  │
  └──→ UART3/SPI → FX 코어에 오디오 샘플 전송?
       ↓
[FX 코어]
  UART3로 커맨드 수신
  SPI로 파라미터 스트림 수신
  DMA1/BDMA로 오디오 버퍼 처리
  SAI2로 오디오 출력? 또는 CM4로 반환?

핵심 질문:
1. CM7→FX 오디오는 AXI SRAM 경유인가, UART/SPI 직접 전송인가?
2. FX 코어 SAI2 참조(3개) = FX 자체 출력인가, 아니면 CM4 SAI2와 동일한 물리 핀인가?
3. FX 코어 BDMA(7 refs) = 어떤 데이터 전송에 사용되는가?
""")

print("\n--- 분석 완료 ---")
