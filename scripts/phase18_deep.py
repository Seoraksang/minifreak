#!/usr/bin/env python3
"""
Phase 18 심층: UI MCU UART/USART 컨텍스트, CM4 RCC, CM4↔UI MCU 연결 추론
"""
import struct
import os

FW_DIR = os.path.expanduser("~/hoon/minifreak/reference/firmware_extracted")

BINS = {
    "CM4": "minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin",
    "CM7": "minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin",
    "ui_screen": "minifreak_ui_screen__fw1_0_0_2229__2025_06_18.bin",
    "ui_matrix": "minifreak_ui_matrix__fw1_0_0_2229__2025_06_18.bin",
    "ui_ribbon": "minifreak_ui_ribbon__fw1_0_0_2229__2025_06_18.bin",
    "ui_kbd": "minifreak_ui_kbd__fw1_0_0_2229__2025_06_18.bin",
}

def load_bin(name):
    path = os.path.join(FW_DIR, BINS[name])
    with open(path, "rb") as f:
        return f.read()

def find_pattern(data, pattern_bytes):
    results = []
    start = 0
    while True:
        idx = data.find(pattern_bytes, start)
        if idx == -1:
            break
        results.append(idx)
        start = idx + 1
    return results

def find_strings(data, min_len=4):
    results = []
    current = b""
    start = 0
    for i, b in enumerate(data):
        if 0x20 <= b < 0x7f:
            if not current:
                start = i
            current += bytes([b])
        else:
            if len(current) >= min_len:
                results.append((start, current.decode("ascii", errors="replace")))
            current = b""
    if len(current) >= min_len:
        results.append((start, current.decode("ascii", errors="replace")))
    return results

# ============================================================
# 1. UI MCU: USART/UART 레지스터 참조 상세 분석
# ============================================================
print("=" * 70)
print("1. UI MCU UART/USART 레지스터 참조 상세 분석")
print("=" * 70)

ui_mcus = ["ui_screen", "ui_matrix", "ui_ribbon", "ui_kbd"]

for mcu in ui_mcus:
    data = load_bin(mcu)
    print(f"\n--- {mcu} ---")
    
    # Check USART2 (0x40004400) - likely UI MCU ↔ CM4 communication
    # USART1 is likely for debug/programming
    periph_regs = {
        "USART1_CR1": 0x40013800,
        "USART1_BRR": 0x4001380C,
        "USART1_ISR": 0x4001381C,
        "USART1_TDR": 0x40013828,
        "USART1_RDR": 0x40013824,
        "USART2_CR1": 0x40004400,
        "USART2_BRR": 0x4000440C,
        "USART2_ISR": 0x4000441C,
        "USART2_TDR": 0x40004428,
        "USART2_RDR": 0x40004424,
        "USART3_CR1": 0x40004800,
        "USART3_BRR": 0x4000480C,
        "USART3_ISR": 0x4000481C,
        "UART4_CR1": 0x40004C00,
        "UART4_BRR": 0x40004C0C,
        "UART4_ISR": 0x40004C1C,
    }
    
    for name, addr in periph_regs.items():
        addr_bytes = struct.pack("<I", addr)
        offsets = find_pattern(data, addr_bytes)
        if offsets:
            for off in offsets[:2]:
                ctx_start = max(0, off - 8)
                ctx_end = min(len(data), off + 8)
                ctx = data[ctx_start:ctx_end]
                print(f"  {name} @ 0x{off:06X}: ...{ctx.hex(' ')}...")

# ============================================================
# 2. CM4: USART/UART 할당 테이블 분석
# ============================================================
print("\n" + "=" * 70)
print("2. CM4 UART 주소 할당 테이블 분석")
print("=" * 70)

cm4 = load_bin("CM4")

# The USART addresses at 0x095A84-0x095AEC form a lookup table
# Let's dump the full table
print("\n--- CM4 0x095A84~0x095B10 UART 테이블 ---")
table_start = 0x095A84
table_end = 0x095B20
for i in range(table_start, table_end, 16):
    hex_bytes = cm4[i:i+16].hex(" ")
    # Try to decode as 4x uint32
    vals = struct.unpack_from("<4I", cm4, i)
    addr_str = " ".join(f"0x{v:08X}" if 0x40000000 <= v <= 0x60000000 else f"0x{v:08X}" for v in vals)
    print(f"  0x{i:06X}: {hex_bytes}  | {addr_str}")

# ============================================================
# 3. CM4: I2C 상세 레지스터 참조
# ============================================================
print("\n" + "=" * 70)
print("3. CM4 I2C1 상세 레지스터 참조")
print("=" * 70)

i2c1_regs = {
    "I2C1_CR1": 0x40005400,
    "I2C1_CR2": 0x40005404,
    "I2C1_OAR1": 0x40005408,
    "I2C1_TIMINGR": 0x4000540C,
    "I2C1_ISR": 0x40005418,
    "I2C1_ICR": 0x4000541C,
    "I2C1_RXDR": 0x40005424,
    "I2C1_TXDR": 0x40005428,
}

for name, addr in i2c1_regs.items():
    addr_bytes = struct.pack("<I", addr)
    offsets = find_pattern(cm4, addr_bytes)
    if offsets:
        print(f"  {name} (0x{addr:08X}): {len(offsets)}개")
        for off in offsets[:3]:
            ctx_start = max(0, off - 8)
            ctx_end = min(len(cm4), off + 8)
            ctx = cm4[ctx_start:ctx_end]
            print(f"    0x{off:06X}: {ctx.hex(' ')}")
    else:
        print(f"  {name} (0x{addr:08X}): 없음")

# ============================================================
# 4. CM4: EXTI 컨텍스트 (GPIO 기반 인터럽트)
# ============================================================
print("\n" + "=" * 70)
print("4. CM4 EXTI (0x58000000) 참조 컨텍스트")
print("=" * 70)

exti_base = 0x58000000
addr_bytes = struct.pack("<I", exti_base)
offsets = find_pattern(cm4, addr_bytes)
for off in offsets:
    ctx_start = max(0, off - 16)
    ctx_end = min(len(cm4), off + 32)
    ctx = cm4[ctx_start:ctx_end]
    print(f"  0x{off:06X}: {ctx.hex(' ')}")

# ============================================================
# 5. CM4: RCC_BASE (0x58024400) 참조 분석
# ============================================================
print("\n" + "=" * 70)
print("5. CM4 RCC_BASE (0x58024400) 참조 분석")
print("=" * 70)

rcc_base = 0x58024400
addr_bytes = struct.pack("<I", rcc_base)
offsets = find_pattern(cm4, addr_bytes)
for off in offsets[:5]:
    ctx_start = max(0, off - 16)
    ctx_end = min(len(cm4), off + 48)
    ctx = cm4[ctx_start:ctx_end]
    print(f"  0x{off:06X}: {ctx.hex(' ')}")

# ============================================================
# 6. CM4에서 I2C OLED 관련 문자열 검색
# ============================================================
print("\n" + "=" * 70)
print("6. CM4 OLED/디스플레이 관련 문자열")
print("=" * 70)

strings = find_strings(cm4, min_len=4)
oled_patterns = ["OLED", "oled", "SSD", "SH110", "SSD13", "display", "screen",
                  "render", "font", "bitmap", "framebuf", "gfx", "ugfx", "lvgl",
                  "ST77", "ILI93", "TFT"]
for offset, s in strings:
    for pat in oled_patterns:
        if pat.lower() in s.lower():
            print(f"  0x{offset:06X}: {s[:100]}")
            break

# ============================================================
# 7. CM4: 모든 UART 레지스터 상세
# ============================================================
print("\n" + "=" * 70)
print("7. CM4 USART3 레지스터 상세 (CR1, CR2, CR3, BRR, ISR, TDR, RDR)")
print("=" * 70)

usart3_regs = {
    "USART3_CR1": 0x40004800,
    "USART3_CR2": 0x40004804,
    "USART3_CR3": 0x40004808,
    "USART3_BRR": 0x4000480C,
    "USART3_GTPR": 0x40004810,
    "USART3_RTOR": 0x40004814,
    "USART3_RQR": 0x40004818,
    "USART3_ISR": 0x4000481C,
    "USART3_ICR": 0x40004820,
    "USART3_RDR": 0x40004824,
    "USART3_TDR": 0x40004828,
    "USART3_PRESC": 0x4000482C,
}

for name, addr in usart3_regs.items():
    addr_bytes = struct.pack("<I", addr)
    offsets = find_pattern(cm4, addr_bytes)
    if offsets:
        print(f"  {name} (0x{addr:08X}): {len(offsets)}개 @ {[f'0x{o:06X}' for o in offsets]}")
    else:
        print(f"  {name} (0x{addr:08X}): 없음")

# ============================================================
# 8. CM4에서 SPI 관련 레지스터 (DMA+SPI 조합 탐색)
# ============================================================
print("\n" + "=" * 70)
print("8. CM4 DMA + SPI 관련 레지스터 오프셋 검색")
print("=" * 70)

# SPI might be accessed through offset from RCC or structure pointers
# Let's check if any code uses SPI register offsets relative to a base
# Common SPI register offsets: 0x00(CR1), 0x04(CR2), 0x08(SR), 0x0C(DR)
# Let's search for RCC SPI enable bit patterns
# APB1LENR bit 14 = SPI2EN, bit 15 = SPI3EN
# APB2ENR bit 12 = SPI1EN, bit 13 = SPI4EN, bit 20 = SPI5EN

# Search for SPI enable bitmask patterns
spi_en_masks = {
    "SPI2EN (bit14 APB1LENR)": 0x0000C000,  # bits 14,15
    "SPI1EN (bit12 APB2ENR)": 0x00003000,   # bits 12,13
    "SPI1EN_only (bit12)": 0x00001000,
    "SPI2EN_only (bit14)": 0x00004000,
}

for name, mask in spi_en_masks.items():
    mask_bytes = struct.pack("<I", mask)
    offsets = find_pattern(cm4, mask_bytes)
    if offsets:
        print(f"  {name} (0x{mask:08X}): {len(offsets)}개")
        for off in offsets[:5]:
            ctx_start = max(0, off - 8)
            ctx_end = min(len(cm4), off + 8)
            ctx = cm4[ctx_start:ctx_end]
            print(f"    0x{off:06X}: {ctx.hex(' ')}")

print("\n\n=== 심층 분석 완료 ===")
