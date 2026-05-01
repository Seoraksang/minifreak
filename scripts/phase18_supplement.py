#!/usr/bin/env python3
"""
Phase 18补充: UI MCU C++ 클래스 이름 분석, CM4 UART context, I2C context
"""
import struct
import os
import re

FW_DIR = os.path.expanduser("~/hoon/minifreak/reference/firmware_extracted")

BINS = {
    "CM4": "minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin",
    "CM7": "minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin",
    "FX":  "minifreak_fx__fw1_0_0_2229__2025_06_18.bin",
    "ui_screen": "minifreak_ui_screen__fw1_0_0_2229__2025_06_18.bin",
    "ui_matrix": "minifreak_ui_matrix__fw1_0_0_2229__2025_06_18.bin",
    "ui_ribbon": "minifreak_ui_ribbon__fw1_0_0_2229__2025_06_18.bin",
    "ui_kbd": "minifreak_ui_kbd__fw1_0_0_2229__2025_06_18.bin",
}

def load_bin(name):
    path = os.path.join(FW_DIR, BINS[name])
    with open(path, "rb") as f:
        return f.read()

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

# ============================================================
# 1. UI MCU: C++ mangled / RTTI / 클래스 이름 추출
# ============================================================
print("=" * 70)
print("1. UI MCU C++ 클래스/RTTI 이름 (통신 관련)")
print("=" * 70)

ui_mcus = ["ui_screen", "ui_matrix", "ui_ribbon", "ui_kbd"]
for mcu in ui_mcus:
    data = load_bin(mcu)
    strings = find_strings(data, min_len=5)
    
    # Filter for C++ class names, RTTI, meaningful identifiers
    interesting = []
    for offset, s in strings:
        # C++ templates
        if any(x in s for x in ["<", ">", "::", "Filter", "Scan", "Led", "PWM",
                                  "Button", "Adc", "Gpio", "Debounce", "Slew",
                                  "Gamma", "Intensity", "Pot", "Chain", "Median",
                                  "Scheduler", "Segmentation", "build version",
                                  "IIR", "SMA", "Hysteresis", "Basic", "Scheduler"]):
            interesting.append((offset, s))
    
    if interesting:
        print(f"\n--- {mcu} ({os.path.getsize(os.path.join(FW_DIR, BINS[mcu]))} bytes) ---")
        for offset, s in interesting:
            print(f"  0x{offset:06X}: {s[:100]}")

# ============================================================
# 2. CM4: UART context around found addresses
# ============================================================
print("\n" + "=" * 70)
print("2. CM4 UART 레지스터 참조 컨텍스트 분석")
print("=" * 70)

cm4 = load_bin("CM4")

uart_addrs = {
    "USART1": 0x40011000,
    "USART2": 0x40004400,
    "USART3": 0x40004800,
}

for name, addr in uart_addrs.items():
    addr_bytes = struct.pack("<I", addr)
    offsets = find_pattern(cm4, addr_bytes)
    print(f"\n--- {name} (0x{addr:08X}) ---")
    for off in offsets:
        # Show surrounding 64 bytes
        ctx_start = max(0, off - 32)
        ctx_end = min(len(cm4), off + 32)
        print(f"\n  0x{off:06X} (file offset):")
        for i in range(ctx_start, ctx_end, 16):
            hex_bytes = cm4[i:i+16].hex(" ")
            print(f"    0x{i:06X}: {hex_bytes}")

# ============================================================
# 3. CM4: I2C context around found addresses
# ============================================================
print("\n" + "=" * 70)
print("3. CM4 I2C 레지스터 참조 컨텍스트 분석")
print("=" * 70)

i2c_addrs = {
    "I2C1": 0x40005400,
}

for name, addr in i2c_addrs.items():
    addr_bytes = struct.pack("<I", addr)
    offsets = find_pattern(cm4, addr_bytes)
    print(f"\n--- {name} (0x{addr:08X}) ---")
    for off in offsets:
        ctx_start = max(0, off - 32)
        ctx_end = min(len(cm4), off + 32)
        print(f"\n  0x{off:06X} (file offset):")
        for i in range(ctx_start, ctx_end, 16):
            hex_bytes = cm4[i:i+16].hex(" ")
            print(f"    0x{i:06X}: {hex_bytes}")

# ============================================================
# 4. CM4: SPI 관련 주소 (GPIO AF 매핑에서 SPI AF 탐색)
# ============================================================
print("\n" + "=" * 70)
print("4. CM4 SPI 관련 추가 분석")
print("=" * 70)

# SPI is NOT found as base addresses. Let's search for SPI clock enable bits in RCC
# RCC base for H745 = 0x58024400
# APB1LENR (offset 0x060) = 0x58024460, SPI2EN=bit14, SPI3EN=bit15
# APB2ENR (offset 0x080) = 0x58024480, SPI1EN=bit12, SPI4EN=bit13, SPI5EN=bit20
# APB4ENR (offset 0x1A0) = 0x580245A0, SPI6EN=bit0

# Search for RCC register addresses
rcc_regs = {
    "RCC_BASE": 0x58024400,
    "APB1LENR": 0x58024460,
    "APB2ENR": 0x58024480,
    "APB4ENR": 0x580245A0,
    "AHB1ENR": 0x58024438,
    "AHB2ENR": 0x5802443C,
    "AHB3ENR": 0x58024440,
    "AHB4ENR": 0x580245A4,
}

print("\n--- RCC 레지스터 주소 참조 ---")
for name, addr in rcc_regs.items():
    addr_bytes = struct.pack("<I", addr)
    offsets = find_pattern(cm4, addr_bytes)
    if offsets:
        print(f"  {name} (0x{addr:08X}): {len(offsets)}개")
        for off in offsets[:5]:
            print(f"    0x{off:06X}")
    else:
        print(f"  {name} (0x{addr:08X}): 없음")

# ============================================================
# 5. CM4: USART context - what code references these?
# ============================================================
print("\n" + "=" * 70)
print("5. CM4에서 USART3 주변 코드 분석 (CM4↔FX 통신)")
print("=" * 70)

# USART3 = 0x40004800, known CM4↔FX communication
# Let's check what other addresses near USART3 are referenced
usart3_periph = {
    "USART3_ISR": 0x4000481C,  # ISR register
    "USART3_ICR": 0x40004820,  # ICR register
    "USART3_TDR": 0x40004828,  # TDR register
    "USART3_RDR": 0x40004824,  # RDR register
    "USART3_BRR": 0x4000480C,  # BRR register
    "USART3_CR1": 0x40004800,
    "USART3_CR2": 0x40004804,
    "USART3_CR3": 0x40004808,
}

for name, addr in usart3_periph.items():
    addr_bytes = struct.pack("<I", addr)
    offsets = find_pattern(cm4, addr_bytes)
    if offsets:
        print(f"  {name} (0x{addr:08X}): {len(offsets)}개")
        for off in offsets[:3]:
            print(f"    0x{off:06X}")

# ============================================================
# 6. CM4: HSEM 주소 검색
# ============================================================
print("\n" + "=" * 70)
print("6. CM4 HSEM 관련 주소 검색")
print("=" * 70)

# HSEM base = 0x5802C000 on STM32H7
hsem_base = 0x5802C000
addr_bytes = struct.pack("<I", hsem_base)
offsets = find_pattern(cm4, addr_bytes)
print(f"  HSEM_BASE (0x{hsem_base:08X}): {len(offsets)}개")
for off in offsets[:10]:
    print(f"    0x{off:06X}")

# IPCC base = 0x5802C800
ipcc_base = 0x5802C800
addr_bytes = struct.pack("<I", ipcc_base)
offsets = find_pattern(cm4, addr_bytes)
print(f"  IPCC_BASE (0x{ipcc_base:08X}): {len(offsets)}개")
for off in offsets[:10]:
    print(f"    0x{off:06X}")

# ============================================================
# 7. CM4: EXTI/GPIO external interrupt for UI MCU communication
# ============================================================
print("\n" + "=" * 70)
print("7. CM4 EXTI/EXTI_MPU 주소 검색")
print("=" * 70)

# EXTI base = 0x58000000 (EXTI for CM4) or 0x58000200
exti_addrs = {
    "EXTI_BASE": 0x58000000,
    "EXTI_CPU1": 0x58000200,
    "EXTI_CPU2": 0x58000280,
    "SYSCFG": 0x58000800,
}
for name, addr in exti_addrs.items():
    addr_bytes = struct.pack("<I", addr)
    offsets = find_pattern(cm4, addr_bytes)
    if offsets:
        print(f"  {name} (0x{addr:08X}): {len(offsets)}개")
        for off in offsets[:5]:
            print(f"    0x{off:06X}")
    else:
        print(f"  {name} (0x{addr:08X}): 없음")

# ============================================================
# 8. UI MCU: CRC/SPI/I2C peripheral register addresses
# ============================================================
print("\n" + "=" * 70)
print("8. UI MCU에서 페리페럴 레지스터 주소 검색")
print("=" * 70)

# UI MCUs are likely STM32G0 or STM32F0 series
# STM32G0 SPI1=0x40013000, SPI2=0x40003800, I2C1=0x40005400, I2C2=0x40005800
# STM32F0 SPI1=0x40013000, SPI2=0x40003800, I2C1=0x40005400, I2C2=0x40005800
# USART1=0x40013800, USART2=0x40004400, USART3=0x40004800

periph_addrs = {
    "SPI1": 0x40013000,
    "SPI2": 0x40003800,
    "I2C1": 0x40005400,
    "I2C2": 0x40005800,
    "USART1": 0x40013800,
    "USART2": 0x40004400,
    "USART3": 0x40004800,
    "UART4": 0x40004C00,
    "TIM1": 0x40012C00,
    "TIM2": 0x40000000,
    "TIM3": 0x40000400,
    "TIM6": 0x40001000,
    "TIM7": 0x40001400,
    "ADC": 0x40012400,
    "DMA1": 0x40020000,
    "DMA2": 0x40020400,
    "RCC": 0x40021000,  # STM32F0/G0 RCC
    "GPIOA": 0x40020000,  # F0: GPIOA
    "GPIOA_G0": 0x50000000,  # G0: GPIOA
}

for mcu in ui_mcus:
    data = load_bin(mcu)
    print(f"\n--- {mcu} ---")
    found_any = False
    for name, addr in periph_addrs.items():
        addr_bytes = struct.pack("<I", addr)
        offsets = find_pattern(data, addr_bytes)
        if offsets:
            found_any = True
            print(f"  {name} (0x{addr:08X}): {len(offsets)}개 @ {[f'0x{o:06X}' for o in offsets[:3]]}")
    if not found_any:
        print("  페리페럴 레지스터 주소 직접 참조 없음")
    
    # Also check for "i2C" string context found in ui_screen at 0x005E45
    if mcu == "ui_screen":
        print("\n  [ui_screen] 'i2C' 문자열 컨텍스트:")
        off = 0x005E45
        ctx = data[off-16:off+32]
        print(f"    hex: {ctx.hex(' ')}")
        # Try to find it as a function name reference
        # Also check for C++ mangled names containing "i2c" or "I2C"
        strings = find_strings(data, min_len=3)
        for soff, s in strings:
            if "i2c" in s.lower() or "iic" in s.lower() or "spi" in s.lower():
                print(f"    0x{soff:06X}: {s}")

print("\n\n=== 보충 분석 완료 ===")
