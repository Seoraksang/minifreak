#!/usr/bin/env python3
"""
Phase 15-1 + Audio Routing: CM4 eEditParams deprecated 슬롯 식별 + CM7→FX 오디오 라우팅 추적
두 분석을 하나의 스크립트에서 수행 (Ghidra 불필요, 바이너리 직접 스캔)
"""

import struct, sys, os, re
from collections import OrderedDict, defaultdict

FW_DIR = "reference/firmware_extracted"

# 펌웨어 파일 (전체버전파일명)
CM4_BIN = os.path.join(FW_DIR, "minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin")
CM7_BIN = os.path.join(FW_DIR, "minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin")
FX_BIN = os.path.join(FW_DIR, "minifreak_fx__fw1_0_0_2229__2025_06_18.bin")

BASE_CM4 = 0x08120000
BASE_CM7 = 0x08020000
BASE_FX = 0x08000000  # FX 코어 베이스 (추정, 나중에 확인)

def load_binary(path):
    with open(path, "rb") as f:
        return f.read()

def read_cstring(data, offset):
    """null-terminated ASCII 문자열 읽기"""
    if offset < 0 or offset >= len(data):
        return None
    end = data.find(b'\x00', offset)
    if end == -1:
        return None
    raw = data[offset:end]
    if all(32 <= b < 127 for b in raw):
        return raw.decode('ascii')
    return None

def extract_string_cluster(data, start_offset, max_entries=200, gap=48):
    """start_offset 근처에서 null-terminated string cluster 추출"""
    results = []
    pos = start_offset
    prev_end = start_offset
    for _ in range(max_entries):
        if pos >= len(data):
            break
        # null 스킵
        while pos < len(data) and data[pos] == 0:
            pos += 1
        if pos >= len(data):
            break
        if pos > prev_end and (pos - prev_end) > gap:
            break
        null_pos = data.find(b'\x00', pos)
        if null_pos == -1:
            break
        raw = data[pos:null_pos]
        if len(raw) > 0 and all(32 <= b < 127 for b in raw):
            results.append((pos, raw.decode('ascii')))
            prev_end = null_pos
            pos = null_pos + 1
        else:
            break
    return results

def find_literal_pool_refs(data, target_addr, base):
    """바이너리에서 target_addr의 4바이트 LE 패턴 검색"""
    packed = struct.pack('<I', target_addr)
    refs = []
    pos = 0
    while True:
        pos = data.find(packed, pos)
        if pos == -1:
            break
        refs.append(pos)
        pos += 4
    return refs

def count_peripheral_refs(data, addr, tolerance=0xFF):
    """특정 페리페럴 주소 범위의 참조 카운트"""
    packed_base = struct.pack('<I', addr)
    count = 0
    pos = 0
    while True:
        pos = data.find(packed_base, pos)
        if pos == -1:
            break
        count += 1
        pos += 4
    # 오프셋 참조도 검색 (주요 offset들)
    for off in [0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24, 0x28]:
        packed = struct.pack('<I', addr + off)
        pos = 0
        while True:
            pos = data.find(packed, pos)
            if pos == -1:
                break
            count += 1
            pos += 4
    return count


# ═══════════════════════════════════════════════════════════════════
# PART 1: eEditParams deprecated 슬롯 식별
# ═══════════════════════════════════════════════════════════════════

print("=" * 70)
print("PART 1: eEditParams Enum 분석 (CM4)")
print("=" * 70)

cm4 = load_binary(CM4_BIN)

# eEditParams enum 영역: 0x081af904~0x081afa7c
edit_param_start = 0x081af904 - BASE_CM4
edit_param_end = 0x081afa7c - BASE_CM4

print(f"\neEditParams 범위: 0x081af904~0x081afa7c ({edit_param_end - edit_param_start} bytes)")

# 문자열 클러스터 추출
edit_cluster = extract_string_cluster(cm4, edit_param_start, max_entries=100, gap=48)
print(f"발견된 문자열 수: {len(edit_cluster)}")

for off, name in edit_cluster:
    addr = off + BASE_CM4
    print(f"  0x{addr:08X}: \"{name}\" (offset {off})")

# 더 넓은 영역에서 deprecated/dummy 관련 문자열 검색
print("\n--- Deprecated/Dummy 키워드 검색 ---")
for keyword in [b"deprecated", b"Deprecated", b"dummy", b"Dummy", b"unused", b"Unused",
                b"legacy", b"Legacy", b"old_", b"Old_", b"_old", b"_OLD",
                b"reserved", b"Reserved", b"placeholder", b"Placeholder"]:
    pos = 0
    while True:
        pos = cm4.find(keyword, pos)
        if pos == -1:
            break
        # 주변 ctx 읽기
        ctx_start = max(0, pos - 20)
        ctx_end = min(len(cm4), pos + len(keyword) + 40)
        ctx = cm4[ctx_start:ctx_end]
        printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx)
        print(f"  offset 0x{pos:06X} (0x{pos+BASE_CM4:08X}): \"{printable}\"")
        pos += 1

# UI/Deprecated 카테고리 파라미터 - VST에서는 존재하지만 펌웨어에서 더미인 것들
# VST XML에서 savedinpreset=0인 파라미터들
print("\n--- VST XML savedinpreset=0 파라미터 (deprecated 후보) ---")
xml_path = "reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/minifreak_vst_params.xml"
if os.path.exists(xml_path):
    with open(xml_path, 'r') as f:
        xml_content = f.read()
    # savedinpreset=0 인 param 추출
    for m in re.finditer(r'<param\s+name="([^"]+)"[^>]*savedinpreset="0"[^>]*>', xml_content):
        pname = m.group(1)
        print(f"  {pname}")


# ═══════════════════════════════════════════════════════════════════
# PART 2: CM7→FX 오디오 라우팅 경로 추적
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PART 2: CM7→FX 오디오 라우팅 경로 추적")
print("=" * 70)

cm7 = load_binary(CM7_BIN)
fx = load_binary(FX_BIN)

# FX 코어 베이스 주소 확인 - 벡터 테이블에서 Reset Vector 읽기
reset_vec = struct.unpack_from('<I', fx, 0x04)[0]
code_addr = reset_vec & ~1
print(f"\nFX Reset Vector: 0x{reset_vec:08X} → Code addr: 0x{code_addr:08X}")
if code_addr > len(fx):
    print(f"  → FX 베이스 = 0x{code_addr - 0x1000:08X} (추정)")
    fx_base = code_addr - 0x1000
else:
    fx_base = 0x08000000  # 기본값
    print(f"  → FX 베이스 = 0x{fx_base:08X} (기본값)")

# Phase 4에서 확인된 페리페럴 매핑 사용
PERIPHERALS = {
    "SAI1": 0x40015400,
    "SAI2": 0x40015800,
    "SPI1": 0x40013000,
    "SPI2": 0x40013400,
    "SPI3": 0x40003800,
    "SPI4": 0x40013400,
    "SPI5": 0x40015000,
    "SPI6": 0x58004000,
    "UART3/USART3": 0x40004800,
    "HSEM": 0x4C000000,
    "IPCC": 0x4C001000,
    "AXI_SRAM": 0x24000000,
    "DTCM": 0x20000000,
    "DMA1": 0x40020000,
    "DMA2": 0x40020400,
    "BDMA": 0x58020000,
    "TIM1": 0x40012C00,
    "TIM2": 0x40000000,
}

print("\n--- CM7 페리페럴 참조 카운트 ---")
cm7_periphs = {}
for name, addr in PERIPHERALS.items():
    count = count_peripheral_refs(cm7, addr)
    if count > 0:
        cm7_periphs[name] = count
        print(f"  {name} ({hex(addr)}): {count} refs")

print("\n--- FX 코어 페리페럴 참조 카운트 ---")
fx_periphs = {}
for name, addr in PERIPHERALS.items():
    count = count_peripheral_refs(fx, addr)
    if count > 0:
        fx_periphs[name] = count
        print(f"  {name} ({hex(addr)}): {count} refs")

print("\n--- CM4 페리페럴 참조 카운트 ---")
cm4_periphs = {}
for name, addr in PERIPHERALS.items():
    count = count_peripheral_refs(cm4, addr)
    if count > 0:
        cm4_periphs[name] = count
        print(f"  {name} ({hex(addr)}): {count} refs")

# 오디오 관련 키워드 스캔
print("\n--- CM7 오디오 라우팅 키워드 스캔 ---")
audio_keywords = [
    b"audio", b"Audio", b"AUDIO",
    b"sample", b"Sample",
    b"buffer", b"Buffer",
    b"render", b"Render",
    b"process", b"Process",
    b"fx_send", b"FX_Send", b"FxSend",
    b"fx_route", b"FX_Route", b"FxRoute",
    b"send_level", b"SendLevel",
    b"mix", b"Mix",
    b"dry", b"Dry",
    b"wet", b"Wet",
    b"output", b"Output",
    b"input", b"Input",
    b"main_out", b"MainOut",
    b"aux", b"AUX",
    b"insert", b"Insert",
    b"bypass", b"Bypass",
    b"spi_tx", b"SPI_TX", b"SPI_Tx",
    b"spi_rx", b"SPI_RX", b"SPI_Rx",
    b"uart_tx", b"UART_TX", b"UART_Tx",
    b"uart_rx", b"UART_RX", b"UART_Rx",
    b"stream", b"Stream",
    b"dma", b"DMA",
    b"sai", b"SAI",
    b"i2s", b"I2S",
    b"intercore", b"InterCore",
    b"shared_mem", b"SharedMem",
    b"ping_pong", b"PingPong",
    b"ring_buf", b"RingBuf",
    b"circular", b"Circular",
    b"fifo", b"FIFO",
]

cm7_audio_strings = []
for kw in audio_keywords:
    pos = 0
    while True:
        pos = cm7.find(kw, pos)
        if pos == -1:
            break
        # 주변 문자열 읽기
        s = read_cstring(cm7, max(0, pos - 30))
        if s and len(s) > 3:
            cm7_audio_strings.append((pos + BASE_CM7, s))
        pos += 1

# 중복 제거
seen = set()
unique_audio = []
for addr, s in cm7_audio_strings:
    if s not in seen:
        seen.add(s)
        unique_audio.append((addr, s))

unique_audio.sort(key=lambda x: x[0])
print(f"발견된 오디오 관련 문자열: {len(unique_audio)}")
for addr, s in unique_audio[:50]:
    print(f"  0x{addr:08X}: \"{s}\"")

print("\n--- FX 코어 오디오 관련 키워드 스캔 ---")
fx_audio_strings = []
for kw in audio_keywords:
    pos = 0
    while True:
        pos = fx.find(kw, pos)
        if pos == -1:
            break
        s = read_cstring(fx, max(0, pos - 30))
        if s and len(s) > 3:
            fx_audio_strings.append((pos, s))
        pos += 1

seen = set()
unique_fx_audio = []
for addr, s in fx_audio_strings:
    if s not in seen:
        seen.add(s)
        unique_fx_audio.append((addr, s))

unique_fx_audio.sort(key=lambda x: x[0])
print(f"발견된 오디오 관련 문자열: {len(unique_fx_audio)}")
for addr, s in unique_fx_audio[:50]:
    print(f"  offset 0x{addr:06X}: \"{s}\"")

# CM4→FX 통신 관련 (UART3, SPI)
print("\n--- CM4→FX 통신 프로토콜 키워드 ---")
comm_keywords = [
    b"uart", b"UART", b"serial", b"Serial",
    b"spi", b"SPI",
    b"cmd", b"CMD", b"command", b"Command",
    b"packet", b"Packet",
    b"frame", b"Frame",
    b"sync", b"Sync",
    b"handshake", b"Handshake",
    b"ready", b"Ready",
    b"ack", b"ACK",
    b"nack", b"NACK",
    b"tx_done", b"TX_Done",
    b"rx_done", b"RX_Done",
    b"transfer", b"Transfer",
    b"send", b"Send",
    b"receive", b"Receive",
    b"hal_spi", b"HAL_SPI",
    b"hal_uart", b"HAL_UART",
    b"mx_spi", b"MX_SPI",
    b"mx_usart", b"MX_USART",
    b"hspi", b"HSPI",
    b"huart", b"HUART",
    b"SPI_HandleTypeDef", b"UART_HandleTypeDef",
]

for kw in comm_keywords:
    pos = cm4.find(kw)
    if pos >= 0:
        s = read_cstring(cm4, max(0, pos - 20))
        if s and len(s) > 3:
            print(f"  CM4 0x{pos+BASE_CM4:08X}: \"{s}\"")
    pos = fx.find(kw)
    if pos >= 0:
        s = read_cstring(fx, max(0, pos - 20))
        if s and len(s) > 3:
            print(f"  FX  offset 0x{pos:06X}: \"{s}\"")

# HSEM (하드웨어 세마포어) 참조 분석 — 코어간 동기화
print("\n--- HSEM (0x4C000000) 상세 참조 ---")
for name, data, base in [("CM4", cm4, BASE_CM4), ("CM7", cm7, BASE_CM7), ("FX", fx, fx_base)]:
    hsem_refs = find_literal_pool_refs(data, 0x4C000000, base)
    if hsem_refs:
        print(f"  {name}: {len(hsem_refs)} refs")
        for r in hsem_refs[:10]:
            print(f"    file offset 0x{r:06X} (vaddr 0x{r+base:08X})")

# AXI SRAM 공유 메모리 주소 범위 참조
print("\n--- AXI SRAM (0x24000000) 참조 ---")
for name, data, base in [("CM4", cm4, BASE_CM4), ("CM7", cm7, BASE_CM7), ("FX", fx, fx_base)]:
    refs = find_literal_pool_refs(data, 0x24000000, base)
    if refs:
        print(f"  {name}: {len(refs)} refs")
    # AXI SRAM 내 특정 오프셋 참조 (오디오 버퍼 후보)
    for off in range(0, 0x20000, 0x1000):
        target = 0x24000000 + off
        r = find_literal_pool_refs(data, target, base)
        if r and len(r) >= 3:
            print(f"    {name} 0x{target:08X}: {len(r)} refs (오디오 버퍼 후보)")

# IPCC (인터코어 통신 컨트롤러) 참조
print("\n--- IPCC (0x4C001000) 참조 ---")
for name, data, base in [("CM4", cm4, BASE_CM4), ("CM7", cm7, BASE_CM7), ("FX", fx, fx_base)]:
    refs = find_literal_pool_refs(data, 0x4C001000, base)
    if refs:
        print(f"  {name}: {len(refs)} refs")

print("\n--- 분석 완료 ---")
