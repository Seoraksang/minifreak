#!/usr/bin/env python3
"""P13-1b: CM7 베이스 검증 + Spice/Dice LUT 재탐색"""
import struct, re

CM7_BIN = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin"
with open(CM7_BIN, "rb") as f:
    data = f.read()

print(f"CM7 size: {len(data)} bytes = 0x{len(data):X}")

# CM7 베이스 결정 — Phase 9 분석에서 사용된 주소 확인
# Phase 9에서 "CM7 지수적 확률 LUT @ 0x08067FDC" 라고 기재
# 이 주소가 파일 내에 있으려면: base <= 0x08067FDC < base + len(data)
# len(data) = 524192 = 0x7FFA0
# base = 0x08067FDC - offset, offset < 0x7FFA0
# → base >= 0x08067FDC - 0x7FFA0 = 0x07FE03C
# → base <= 0x08067FDC

# STM32H745: CM7 = Bank 1 base 0x08000000, size 1MB
# CM7 binary = 524KB → 0x08000000 + 0x7FFA0 = 0x0807FFA0

# Reset Vector 검증
reset_vec = struct.unpack_from('<I', data, 4)[0]
print(f"Reset Vector raw: 0x{reset_vec:08X}")

# 만약 base=0x08000000이면 Reset Vector=0 → 에러
# STM32 DFU 펌웨어는 첫 64바이트가 DFU header
# offset 0x40부터 벡터 테이블
print(f"\nOffset 0x00~0x4F (DFU header + vector table start):")
for i in range(0, 0x50, 4):
    val = struct.unpack_from('<I', data, i)[0]
    print(f"  0x{i:02X}: 0x{val:08X}")

# DFU header: offset 0x08 = image size
img_size = struct.unpack_from('<I', data, 8)[0]
print(f"\nDFU image size @ offset 0x08: {img_size} (0x{img_size:X})")
print(f"File size: {len(data)}")
print(f"Difference: {len(data) - img_size}")

# Vector table at offset 0x40
sp = struct.unpack_from('<I', data, 0x40)[0]
reset = struct.unpack_from('<I', data, 0x44)[0]
print(f"\nVector table @ offset 0x40:")
print(f"  Initial SP: 0x{sp:08X}")
print(f"  Reset Vector: 0x{reset:08X}")

if reset & 1:
    code_addr = reset & ~1
    print(f"  Thumb mode, code = 0x{code_addr:08X}")
    # offset = reset - base
    # base = 0x08000000 이면 offset = code_addr - 0x08000000
    if code_addr >= 0x08000000:
        offset = code_addr - 0x08000000
        print(f"  File offset (base=0x08000000): 0x{offset:X}")
        if offset < len(data):
            print(f"  ✅ Within file bounds")
        else:
            print(f"  ❌ Outside file bounds!")
    else:
        # base를 추정
        # offset은 보통 작은 값 (0x200~0x1000)
        # code_addr = base + offset
        # offset ≈ 0x200 (vector table = 0x200 bytes)
        # base = code_addr - 0x200
        for off_guess in [0x200, 0x400, 0x800, 0x1000]:
            base_guess = code_addr - off_guess
            if base_guess >= 0x08000000 and base_guess < 0x08200000:
                print(f"  Possible base (offset=0x{off_guess:X}): 0x{base_guess:08X}")

# Phase 9 CM7 분석 JSON 확인
import json
cm7_json = "/home/jth/hoon/minifreak/firmware/analysis/cm7_ghidra_dsp_funcs.json"
try:
    with open(cm7_json) as f:
        cm7_data = json.load(f)
    if isinstance(cm7_data, dict):
        # base 정보 찾기
        for k, v in cm7_data.items():
            if 'base' in str(k).lower() or 'base' in str(v).lower():
                print(f"\n  {k}: {v}")
    print(f"\nCM7 DSP JSON keys: {list(cm7_data.keys())[:10] if isinstance(cm7_data, dict) else 'N/A'}")
    if isinstance(cm7_data, list):
        print(f"  {len(cm7_data)} entries")
        if cm7_data:
            print(f"  First entry keys: {list(cm7_data[0].keys()) if isinstance(cm7_data[0], dict) else cm7_data[0]}")
except Exception as e:
    print(f"  JSON load error: {e}")

# Phase 9 CM7 deep JSON
cm7_deep = "/home/jth/hoon/minifreak/firmware/analysis/phase9_cm7_deep.json"
try:
    with open(cm7_deep) as f:
        deep = json.load(f)
    if isinstance(deep, dict):
        print(f"\nPhase 9 CM7 deep keys: {list(deep.keys())[:10]}")
        if 'base_address' in deep:
            print(f"  base_address: {deep['base_address']}")
        if 'image_base' in deep:
            print(f"  image_base: {deep['image_base']}")
        # 전체 키에서 base 관련 검색
        for k in deep:
            if 'base' in k.lower():
                print(f"  {k}: {deep[k]}")
    elif isinstance(deep, list):
        print(f"  {len(deep)} entries")
except Exception as e:
    print(f"  Phase 9 deep error: {e}")

# Walk LUT 재검증 — float32로 읽어보기
print("\n" + "="*60)
print("=== Walk LUT @ 0x080546C4 as float32 ===")
CM7_BASE = 0x08000000
offset = 0x080546C4 - CM7_BASE
chunk = data[offset:offset+64]
floats = struct.unpack(f'<{len(chunk)//4}f', chunk)
print(f"  First 16 float32: {[f'{v:.6f}' for v in floats[:16]]}")
print(f"  Are these valid floats? (reasonable audio range)")
valid_floats = [v for v in floats if 0.0001 < abs(v) < 100000 and v == v]  # not NaN/Inf
print(f"  Valid floats: {len(valid_floats)}/{len(floats)}")

# CM7 vtable 분석 JSON에서 base 확인
vtable_json = "/home/jth/hoon/minifreak/firmware/analysis/cm7_vtable_deep_analysis.json"
try:
    with open(vtable_json) as f:
        vt = json.load(f)
    if isinstance(vt, dict):
        for k in vt:
            if 'base' in k.lower():
                print(f"\n  VTable JSON {k}: {vt[k]}")
        if 'metadata' in vt and isinstance(vt['metadata'], dict):
            for k in vt['metadata']:
                if 'base' in k.lower():
                    print(f"  VTable metadata {k}: {vt['metadata'][k]}")
    print(f"\nVTable JSON keys: {list(vt.keys())[:10] if isinstance(vt, dict) else 'N/A'}")
except Exception as e:
    print(f"  VTable JSON error: {e}")

# Spice exp LUT을 float32로도 읽어보기
print("\n" + "="*60)
print("=== Spice Exp LUT @ 0x08067FDC as float32 ===")
offset2 = 0x08067FDC - CM7_BASE
chunk2 = data[offset2:offset2+64]
floats2 = struct.unpack(f'<{len(chunk2)//4}f', chunk2)
print(f"  First 16 float32: {[f'{v:.6f}' for v in floats2[:16]]}")
valid2 = [v for v in floats2 if 0.0001 < abs(v) < 100000 and v == v]
print(f"  Valid floats: {len(valid2)}/{len(floats2)}")

# byte pair 패턴 분석 — 2바이트 간격으로 읽기
print("\n  As uint16 LE (2-byte pairs):")
uint16s = struct.unpack(f'<{len(chunk2)//2}H', chunk2)
print(f"  First 16 uint16: {[f'0x{v:04X}({v})' for v in uint16s[:16]]}")
