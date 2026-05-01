#!/usr/bin/env python3
"""
Phase 18: UI MCU 통신 프로토콜 + CM7 SPI 페리페럴 정적 분석
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

def find_strings(data, min_len=4, encoding="ascii"):
    """Extract printable ASCII strings of at least min_len characters."""
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

def find_string_matches(data, patterns, min_len=3):
    """Find all strings matching any of the given regex patterns."""
    strings = find_strings(data, min_len=min_len)
    matches = {}
    for pat in patterns:
        matches[pat] = []
        for offset, s in strings:
            if re.search(pat, s, re.IGNORECASE):
                matches[pat].append((offset, s))
    return matches

def find_pattern_in_binary(data, pattern_bytes):
    """Find all occurrences of a byte pattern in binary data."""
    results = []
    start = 0
    while True:
        idx = data.find(pattern_bytes, start)
        if idx == -1:
            break
        results.append(idx)
        start = idx + 1
    return results

def find_arm_ldr_address(data, base_addr, tolerance=4):
    """
    Search for ARM LDR instructions that load an address close to base_addr.
    LDR Rn, [PC, #imm] or MOV/MOVW pattern that constructs base_addr.
    For Thumb2: LDR Rt, [PC, #imm] encoding = 1111 1000 U10w Rn Rt 1111 imm8
    """
    results = []
    for i in range(len(data) - 3):
        # Thumb2 LDR literal: F8DF xxxx or F8CF xxxx (PC-relative)
        hw = struct.unpack_from("<H", data, i)[0]
        if (hw & 0xFF7F) == 0xF85F:  # LDR Rt, [PC, #imm] (word)
            hw2 = struct.unpack_from("<H", data, i+2)[0]
            rt = (hw2 >> 12) & 0xF
            imm12 = ((hw & 0x00FF) << 2) | ((hw2 >> 6) & 0x3)
            # PC is aligned to 4, plus 4 ahead
            pc_val = (i & ~3) + 4
            addr = pc_val + imm12
            if abs(addr - base_addr) < tolerance * 4:
                results.append((i, addr, "LDR.literal"))
    return results

def analyze_ui_mcu_comm():
    """Task 2: UI MCU binaries - communication protocol strings"""
    print("=" * 70)
    print("TASK 2: UI MCU 통신 관련 문자열 검색")
    print("=" * 70)
    
    comm_patterns = [
        r"SPI", r"I2C", r"IIC", r"UART", r"USART", r"DMA",
        r"HSEM", r"IPCC", r"USB",
        r"command", r"cmd", r"request", r"response", r"sync",
        r"master", r"slave", r"host",
        r"receive", r"transmit", r"send", r"write", r"read",
        r"interrupt", r"IRQ", r"ISR",
        r"GPIO", r"TIM\d?", r"ADC",
        r"baud", r"clock", r"speed",
        r"buffer", r"queue", r"mailbox",
        r"SSP", r"MSSP",
    ]
    
    ui_mcus = ["ui_screen", "ui_matrix", "ui_ribbon", "ui_kbd"]
    for mcu in ui_mcus:
        print(f"\n--- {mcu} ({os.path.getsize(os.path.join(FW_DIR, BINS[mcu]))} bytes) ---")
        data = load_bin(mcu)
        
        # All strings for context
        all_strings = find_strings(data, min_len=4)
        print(f"  총 문자열 수 (>=4자): {len(all_strings)}")
        
        # Communication-related strings
        matches = find_string_matches(data, comm_patterns, min_len=3)
        found_any = False
        for pat, items in sorted(matches.items()):
            if items:
                found_any = True
                print(f"\n  [{pat}] ({len(items)}개):")
                for offset, s in items[:15]:  # limit output
                    print(f"    0x{offset:06X}: {s[:80]}")
                if len(items) > 15:
                    print(f"    ... 외 {len(items)-15}개")
        if not found_any:
            print("  통신 관련 문자열 없음")
        
        # Also print all strings for UI MCUs (they're small)
        print(f"\n  === 전체 문자열 목록 ===")
        for offset, s in all_strings:
            print(f"    0x{offset:06X}: {s[:100]}")

def analyze_cm4_ui_refs():
    """Task 3: CM4 - UI MCU related string references"""
    print("\n" + "=" * 70)
    print("TASK 3: CM4에서 UI MCU 관련 문자열 검색")
    print("=" * 70)
    
    ui_patterns = [
        r"screen", r"matrix", r"ribbon", r"keyboard", r"kbd",
        r"ui_", r"UI_", r"display", r"LED", r"button",
        r"encoder", r"touch", r"strip", r"slider",
        r"OLED", r"LCD", r"TFT",
    ]
    
    data = load_bin("CM4")
    matches = find_string_matches(data, ui_patterns, min_len=4)
    for pat, items in sorted(matches.items()):
        if items:
            print(f"\n[{pat}] ({len(items)}개):")
            for offset, s in items[:20]:
                print(f"  0x{offset:06X}: {s[:100]}")
            if len(items) > 20:
                print(f"  ... 외 {len(items)-20}개")
        else:
            print(f"[{pat}] - 없음")

def analyze_cm7_spi():
    """Task 4: CM7 - SPI/I2C/DMA register references"""
    print("\n" + "=" * 70)
    print("TASK 4: CM7에서 SPI/I2C/DMA 관련 분석")
    print("=" * 70)
    
    data = load_bin("CM7")
    
    # 4a: String search
    print("\n--- 4a: 문자열 검색 ---")
    hw_patterns = [r"SPI", r"I2C", r"DMA", r"UART", r"USART", r"S AI", r"HAL_"]
    matches = find_string_matches(data, hw_patterns, min_len=3)
    for pat, items in sorted(matches.items()):
        if items:
            print(f"\n[{pat}] ({len(items)}개):")
            for offset, s in items[:15]:
                print(f"  0x{offset:06X}: {s[:100]}")
        else:
            print(f"[{pat}] - 없음")
    
    # 4b: SPI register addresses search (little-endian 32-bit)
    print("\n--- 4b: SPI 레지스터 주소 직접 참조 ---")
    spi_addrs = {
        "SPI1": 0x40013000,
        "SPI2": 0x40003800,
        "SPI3": 0x40003C00,
        "SPI4": 0x40013400,
        "SPI5": 0x40015000,
        "SPI6": 0x54005000,
    }
    for name, addr in spi_addrs.items():
        # Search for the base address as 32-bit LE
        addr_bytes = struct.pack("<I", addr)
        offsets = find_pattern_in_binary(data, addr_bytes)
        if offsets:
            print(f"  {name} (0x{addr:08X}): {len(offsets)}개 참조")
            for off in offsets[:10]:
                # Show context
                ctx_start = max(0, off - 4)
                ctx_end = min(len(data), off + 8)
                ctx = data[ctx_start:ctx_end]
                print(f"    0x{off:06X}: ...{ctx.hex()}...")
        else:
            print(f"  {name} (0x{addr:08X}): 없음")
    
    # Also search for addresses + offsets (e.g., CR1 at +0x00, CR2 at +0x04, etc.)
    print("\n--- 4b-2: SPI 레지스터 오프셋 주소 검색 ---")
    spi_specific = {
        "SPI1_CR1": 0x40013000,
        "SPI1_SR": 0x40013008,
        "SPI1_DR": 0x4001300C,
        "SPI2_CR1": 0x40003800,
        "SPI2_SR": 0x40003808,
        "SPI2_DR": 0x4000380C,
        "SPI3_CR1": 0x40003C00,
        "SPI3_SR": 0x40003C08,
        "SPI4_CR1": 0x40013400,
        "SPI5_CR1": 0x40015000,
        "SPI6_CR1": 0x54005000,
    }
    for name, addr in spi_specific.items():
        addr_bytes = struct.pack("<I", addr)
        offsets = find_pattern_in_binary(data, addr_bytes)
        if offsets:
            print(f"  {name} (0x{addr:08X}): {len(offsets)}개 @ {[f'0x{o:06X}' for o in offsets[:5]]}")
    
    # 4c: I2C register addresses
    print("\n--- 4c: I2C 레지스터 주소 검색 ---")
    i2c_addrs = {
        "I2C1": 0x40005400,
        "I2C2": 0x40005800,
        "I2C3": 0x40005C00,
        "I2C4": 0x58001C00,
    }
    for name, addr in i2c_addrs.items():
        addr_bytes = struct.pack("<I", addr)
        offsets = find_pattern_in_binary(data, addr_bytes)
        if offsets:
            print(f"  {name} (0x{addr:08X}): {len(offsets)}개")
            for off in offsets[:5]:
                print(f"    0x{off:06X}")
        else:
            print(f"  {name} (0x{addr:08X}): 없음")
    
    # 4d: DMA register addresses
    print("\n--- 4d: DMA 레지스터 주소 검색 ---")
    dma_addrs = {
        "DMA1": 0x40020000,
        "DMA2": 0x40020400,
        "BDMA": 0x58025400,
        "DMAMUX1": 0x40020800,
        "DMAMUX2": 0x58025800,
    }
    for name, addr in dma_addrs.items():
        addr_bytes = struct.pack("<I", addr)
        offsets = find_pattern_in_binary(data, addr_bytes)
        if offsets:
            print(f"  {name} (0x{addr:08X}): {len(offsets)}개")
            for off in offsets[:5]:
                print(f"    0x{off:06X}")
        else:
            print(f"  {name} (0x{addr:08X}): 없음")
    
    # 4e: RCC SPI clock enable bits (APB1ENR1, APB1ENR2, APB2ENR)
    print("\n--- 4e: RCC 클럭 활성화 관련 SPI 비트 검색 ---")
    # RCC base = 0x58024400
    # APB1LENR = RCC + 0x060 = 0x58024460 (SPI2EN=bit14, SPI3EN=bit15)
    # APB2ENR = RCC + 0x080 = 0x58024480 (SPI1EN=bit12, SPI4EN=bit13, SPI5EN=bit20)
    rcc_spi_bits = {
        "APB1LENR@RCC": 0x58024460,
        "APB2ENR@RCC": 0x58024480,
        "APB4ENR@RCC": 0x580245A0,  # SPI6EN
    }
    for name, addr in rcc_spi_bits.items():
        addr_bytes = struct.pack("<I", addr)
        offsets = find_pattern_in_binary(data, addr_bytes)
        if offsets:
            print(f"  {name} (0x{addr:08X}): {len(offsets)}개")
            for off in offsets[:5]:
                print(f"    0x{off:06X}")

def analyze_fx_comm():
    """Task 5: FX core - communication strings"""
    print("\n" + "=" * 70)
    print("TASK 5: FX 코어 CM4↔FX 통신 관련 문자열 검색")
    print("=" * 70)
    
    data = load_bin("FX")
    comm_patterns = [
        r"UART", r"SPI", r"HSEM", r"IPCC",
        r"command", r"cmd", r"param", r"parameter",
        r"receive", r"transmit", r"send",
        r"master", r"slave", r"host",
        r"DMA", r"interrupt", r"ISR",
        r"sync", r"lock", r"semaphore",
        r"buffer", r"queue", r"mailbox",
        r"dsp56", r"DSP56",
    ]
    
    matches = find_string_matches(data, comm_patterns, min_len=3)
    for pat, items in sorted(matches.items()):
        if items:
            print(f"\n[{pat}] ({len(items)}개):")
            for offset, s in items[:15]:
                print(f"  0x{offset:06X}: {s[:100]}")
        else:
            print(f"[{pat}] - 없음")
    
    # Also dump all strings from FX
    print(f"\n=== FX 전체 문자열 목록 ===")
    all_strings = find_strings(data, min_len=4)
    for offset, s in all_strings:
        print(f"  0x{offset:06X}: {s[:100]}")

def analyze_cm4_spi_i2c():
    """Bonus: CM4에서도 SPI/I2C 레지스터 참조 확인"""
    print("\n" + "=" * 70)
    print("BONUS: CM4에서 SPI/I2C/UART 레지스터 주소 참조")
    print("=" * 70)
    
    data = load_bin("CM4")
    
    # SPI
    print("\n--- SPI 레지스터 ---")
    spi_addrs = {
        "SPI1": 0x40013000, "SPI2": 0x40003800, "SPI3": 0x40003C00,
        "SPI4": 0x40013400, "SPI5": 0x40015000, "SPI6": 0x54005000,
    }
    for name, addr in spi_addrs.items():
        addr_bytes = struct.pack("<I", addr)
        offsets = find_pattern_in_binary(data, addr_bytes)
        if offsets:
            print(f"  {name} (0x{addr:08X}): {len(offsets)}개")
            for off in offsets[:8]:
                ctx_start = max(0, off - 4)
                ctx_end = min(len(data), off + 8)
                ctx = data[ctx_start:ctx_end]
                print(f"    0x{off:06X}: ...{ctx.hex()}...")
        else:
            print(f"  {name} (0x{addr:08X}): 없음")
    
    # UART/USART
    print("\n--- UART/USART 레지스터 ---")
    uart_addrs = {
        "USART1": 0x40011000, "USART2": 0x40004400, "USART3": 0x40004800,
        "UART4": 0x40004C00, "UART5": 0x40005000,
        "USART6": 0x40011400, "UART7": 0x40007800, "UART8": 0x40007C00,
    }
    for name, addr in uart_addrs.items():
        addr_bytes = struct.pack("<I", addr)
        offsets = find_pattern_in_binary(data, addr_bytes)
        if offsets:
            print(f"  {name} (0x{addr:08X}): {len(offsets)}개")
            for off in offsets[:5]:
                print(f"    0x{off:06X}")
        else:
            print(f"  {name} (0x{addr:08X}): 없음")
    
    # I2C
    print("\n--- I2C 레지스터 ---")
    i2c_addrs = {
        "I2C1": 0x40005400, "I2C2": 0x40005800, "I2C3": 0x40005C00,
        "I2C4": 0x58001C00,
    }
    for name, addr in i2c_addrs.items():
        addr_bytes = struct.pack("<I", addr)
        offsets = find_pattern_in_binary(data, addr_bytes)
        if offsets:
            print(f"  {name} (0x{addr:08X}): {len(offsets)}개")
            for off in offsets[:5]:
                print(f"    0x{off:06X}")
        else:
            print(f"  {name} (0x{addr:08X}): 없음")
    
    # CM4 communication-related strings
    print("\n--- CM4 통신 관련 문자열 ---")
    cm4_comm = [r"SPI", r"I2C", r"UART", r"USART", r"DMA", r"HSEM", r"IPCC",
                r"slave", r"master", r"host", r"screen", r"matrix", r"ribbon",
                r"keyboard", r"ui_", r"UI_", r"display", r"LED", r"button",
                r"encoder", r"OLED"]
    matches = find_string_matches(data, cm4_comm, min_len=3)
    for pat, items in sorted(matches.items()):
        if items:
            print(f"\n[{pat}] ({len(items)}개):")
            for offset, s in items[:10]:
                print(f"  0x{offset:06X}: {s[:100]}")

if __name__ == "__main__":
    analyze_ui_mcu_comm()
    analyze_cm4_ui_refs()
    analyze_cm7_spi()
    analyze_fx_comm()
    analyze_cm4_spi_i2c()
    print("\n\n=== 분석 완료 ===")
