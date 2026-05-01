#!/usr/bin/env python3
"""Phase 14: Extract header size constants from x86-64 code near LEA instruction"""
import struct, sys

DLL_PATH = sys.argv[1]
with open(DLL_PATH, "rb") as f:
    dll = f.read()

LEA_RAW = 0x00FBDEA2
TEXT_RAW_START = 0x400

start = max(TEXT_RAW_START, LEA_RAW - 200)
end = min(len(dll), LEA_RAW + 200)

# hex dump around LEA
print(f"=== Hex dump around LEA @ 0x{LEA_RAW:08X} ===")
for i in range(start, end, 16):
    hex_part = ' '.join(f'{dll[i+j]:02X}' for j in range(min(16, end-i)))
    ascii_part = ''.join(chr(dll[i+j]) if 32 <= dll[i+j] < 127 else '.' for j in range(min(16, end-i)))
    print(f"  {i:08X}: {hex_part:<48s} {ascii_part}")

print()

# Find all immediate constants
print("=== Immediate constants (CMP/MOV/ADD/SUB, range 4-64) ===")
for i in range(start, end - 5):
    delta = i - LEA_RAW
    b0, b1 = dll[i], dll[i+1]
    
    # CMP r/m32, imm8 (83 /7 ib)
    if b0 == 0x83 and (b1 & 0xF8) == 0xF8:
        imm = struct.unpack_from('<b', dll, i+2)[0]
        if 2 <= abs(imm) <= 64:
            print(f"  CMP imm8={imm:3d} @ 0x{i:08X} (delta={delta:+4d})")
    
    # CMP r/m32, imm32 (81 /7 id)
    elif b0 == 0x81 and (b1 & 0xF8) == 0xF8:
        imm = struct.unpack_from('<I', dll, i+2)[0]
        if 2 <= imm <= 64:
            print(f"  CMP imm32={imm} @ 0x{i:08X} (delta={delta:+4d})")
    
    # MOV r32, imm32 (B8+rd id)
    elif 0xB8 <= b0 <= 0xBF:
        imm = struct.unpack_from('<I', dll, i+1)[0]
        if 2 <= imm <= 64:
            reg = b0 - 0xB8
            print(f"  MOV r{reg}, {imm} @ 0x{i:08X} (delta={delta:+4d})")
    
    # SUB reg, imm8 (83 /5 ib)
    elif b0 == 0x83 and (b1 & 0xF8) == 0xE8:
        imm = struct.unpack_from('<b', dll, i+2)[0]
        if 2 <= abs(imm) <= 64:
            print(f"  SUB imm8={imm:3d} @ 0x{i:08X} (delta={delta:+4d})")

# ─── 더 넓은 범위: 같은 함수 내에서 kCollageUsbInHeaderSize 상수 사용 찾기 ───
# 함수 경계 추정: LEA 앞쪽에서 RET(0xC3) 또는 다른 함수의 끝을 찾기
print("\n=== 같은 함수 내 헤더 크기 관련 상수 (wider scan) ===")

# 함수 시작점 추정 (LEA 앞쪽으로 가장 가까운 push rbp / sub rsp 패턴)
func_start = LEA_RAW
for i in range(LEA_RAW, max(TEXT_RAW_START, LEA_RAW - 2000), -1):
    # function prologue: push rbp (0x55) or sub rsp, imm (48 83 EC xx) or (48 81 EC xx xx xx xx)
    if dll[i] == 0x55 and i > 0 and dll[i-1] in (0x40, 0x48, 0xCC, 0xC3, 0x90):
        func_start = i
        break
    if dll[i] == 0xC3:  # ret
        func_start = i + 1
        break

print(f"  Estimated function start: 0x{func_start:08X}")

# 함수 끝 추정
func_end = LEA_RAW
for i in range(LEA_RAW + 7, min(len(dll), LEA_RAW + 2000)):
    if dll[i] == 0xC3:  # ret
        func_end = i + 1
        break

print(f"  Estimated function end: 0x{func_end:08X}")
print(f"  Function size: {func_end - func_start} bytes")

# 함수 전체에서 상수값 추출
print("\n  Constants in function:")
for i in range(func_start, func_end - 5):
    b0, b1 = dll[i], dll[i+1]
    
    if b0 == 0x83 and (b1 & 0xF8) == 0xF8:  # CMP r/m32, imm8
        imm = struct.unpack_from('<b', dll, i+2)[0]
        if 2 <= abs(imm) <= 128:
            print(f"    CMP imm8={imm:4d} @ 0x{i:08X}")
    
    elif b0 == 0x81 and (b1 & 0xF8) == 0xF8:  # CMP r/m32, imm32
        imm = struct.unpack_from('<I', dll, i+2)[0]
        if 2 <= imm <= 128:
            print(f"    CMP imm32={imm:4d} @ 0x{i:08X}")
    
    elif 0xB8 <= b0 <= 0xBF:  # MOV r32, imm32
        imm = struct.unpack_from('<I', dll, i+1)[0]
        if 2 <= imm <= 128:
            print(f"    MOV r32={imm:4d} @ 0x{i:08X}")

# ─── "Size < kCollageTcpHeaderSize" 참조 코드도 분석 ───
IMAGE_BASE = 0x180000000
RDATA_VA = 0x013D1000
RDATA_RAW = 0x013CFA00

tcp_err = b'Size < kCollageTcpHeaderSize\x00'
tcp_err_raw = dll.find(tcp_err)
if tcp_err_raw > 0:
    tcp_err_va = IMAGE_BASE + RDATA_VA + (tcp_err_raw - RDATA_RAW)
    print(f"\n=== TCP Header Size error string ===")
    print(f"  String raw=0x{tcp_err_raw:08X}, VA=0x{tcp_err_va:016X}")
    
    # LEA 참조 찾기
    for i in range(TEXT_RAW_START, min(len(dll), 0x01332A00) - 7):
        if dll[i] in (0x48, 0x4C) and dll[i+1] == 0x8D:
            modrm = dll[i+2]
            if (modrm >> 6) == 0 and (modrm & 7) == 5:
                disp = struct.unpack_from('<i', dll, i+3)[0]
                instr_va = IMAGE_BASE + 0x1000 + (i - TEXT_RAW_START)
                target_va = instr_va + 7 + disp
                if target_va == tcp_err_va:
                    print(f"  LEA @ raw=0x{i:08X}, VA=0x{instr_va:016X}")
                    
                    # 근처 상수값
                    for j in range(max(TEXT_RAW_START, i-200), min(len(dll), i+200)):
                        if dll[j] == 0x83 and (dll[j+1] & 0xF8) == 0xF8:
                            imm = struct.unpack_from('<b', dll, j+2)[0]
                            if 2 <= abs(imm) <= 64:
                                print(f"    CMP imm8={imm} @ 0x{j:08X} (delta={j-i:+4d})")
                        elif 0xB8 <= dll[j] <= 0xBF:
                            imm = struct.unpack_from('<I', dll, j+1)[0]
                            if 2 <= imm <= 64:
                                print(f"    MOV imm32={imm} @ 0x{j:08X} (delta={j-i:+4d})")
                    break

print("\n완료")
