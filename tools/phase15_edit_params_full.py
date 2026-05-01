#!/usr/bin/env python3
"""
Phase 15-1d: eEditParams 포인터 테이블 완전 추출
두 개의 동일한 포인터 테이블 (0x081B014C, 0x081B1620)에서 enum 인덱스 확정
"""

import struct, os

FW_DIR = "reference/firmware_extracted"
CM4_BIN = os.path.join(FW_DIR, "minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin")
BASE_CM4 = 0x08120000

with open(CM4_BIN, "rb") as f:
    cm4 = f.read()

def read_cstr(data, offset):
    if offset < 0 or offset >= len(data):
        return None
    end = data.find(b'\x00', offset)
    if end == -1 or end == offset:
        return None
    raw = data[offset:end]
    if all(32 <= b < 127 for b in raw):
        return raw.decode('ascii')
    return None

# 포인터 테이블 1: 0x081B014C에서 시작 (앞에 10개 filler)
# filler = 0x081AEFE4 ("  ") = 빈 문자열 = unused slot
TABLE1_START = 0x081B0124 - BASE_CM4  # 첫 filler부터

print("=== eEditParams 포인터 테이블 #1 추출 ===")
print(f"시작: 0x081B0124, Unison Count @ index 10\n")

entries = []
idx = 0
pos = TABLE1_START
FILLER = 0x081AEFE4

while pos < len(cm4) - 3:
    v = struct.unpack_from('<I', cm4, pos)[0]
    
    if v == FILLER:
        entries.append((idx, 0x081AEFE4, "", True))
        idx += 1
        pos += 4
        continue
    
    # 유효한 flash 주소인지 확인
    if 0x08120000 <= v <= 0x081C0000:
        s = read_cstr(cm4, v - BASE_CM4)
        if s is not None and len(s) >= 1:
            entries.append((idx, v, s, False))
            idx += 1
            pos += 4
            continue
    
    # flash 주소가 아니면 테이블 종료
    break

# 결과 출력
print(f"총 {len(entries)} 엔트리 추출\n")

deprecated_indices = []
ui_only_indices = []
active_params = []

for i, addr, name, is_filler in entries:
    marker = ""
    if is_filler:
        marker = " [FILLER/UNUSED]"
        ui_only_indices.append(i)
    elif "DEPRECATED" in name.upper():
        marker = " ★★★ DEPRECATED"
        deprecated_indices.append(i)
    elif "obsolete" in name.lower():
        marker = " ★★★ OBSOLETE"
        deprecated_indices.append(i)
    elif name in ["Cursor", "Mx Cursor", "Mx Page", "Mx Mode", "PlayState", "RecState", "RecMode",
                  "Osc Sel", "Fx Sel", "Lfo Sel", "VST_IsConnected", "MetronomeBeat", "Preset filter",
                  "Favorites Page", "Seq Page", "Seq Transpose", "Playing Tempo"]:
        marker = " [UI-only]"
        ui_only_indices.append(i)
    else:
        active_params.append((i, name))
    
    # 짧은 문자열은 앞의 긴 문자열의 일부일 수 있음
    if len(name) <= 3 and not is_filler:
        marker += " [FRAGMENT?]"
    
    print(f"  [{i:3d}] 0x{addr:08X}: \"{name}\"{marker}")

# Deprecated/사용슬롯 요약
print("\n" + "=" * 70)
print("분류 요약")
print("=" * 70)
print(f"\n활성 파라미터 (패치 후보): {len(active_params)}개")
for i, name in active_params:
    print(f"  [{i:3d}] {name}")

print(f"\nDeprecated/Obsolute: {len(deprecated_indices)}개")
for i in deprecated_indices:
    _, addr, name, _ = entries[i]
    print(f"  [{i:3d}] 0x{addr:08X}: \"{name}\"")

print(f"\nUI-only/상태 플래그: {len(ui_only_indices)}개")
for i in ui_only_indices:
    _, addr, name, is_filler = entries[i]
    if is_filler:
        print(f"  [{i:3d}] 0x{addr:08X}: (empty/filler)")
    else:
        print(f"  [{i:3d}] 0x{addr:08X}: \"{name}\"")

# 안전한 패치 슬롯 후보
print(f"\n{'=' * 70}")
print("안전한 패치 슬롯 (최우선 후보)")
print(f"{'=' * 70}")
safe_slots = []
for i in deprecated_indices + ui_only_indices:
    _, addr, name, is_filler = entries[i]
    if is_filler:
        safe_slots.append((i, addr, "(empty filler)", "빈 슬롯 — 아무 동작 없음, 완전 안전"))
    elif "DEPRECATED" in name.upper():
        safe_slots.append((i, addr, name, "명시적 deprecated — 기존 기능 유지 불필요"))
    elif "obsolete" in name.lower():
        safe_slots.append((i, addr, name, "명시적 obsolete — 더 이상 사용 안 됨"))
    elif name == "VST_IsConnected":
        safe_slots.append((i, addr, name, "VST 연결 상태 플래그 — 프리셋 미저장"))
    elif name in ["PlayState", "RecState", "RecMode", "Cursor", "Mx Cursor", "Mx Page", "Mx Mode"]:
        safe_slots.append((i, addr, name, "UI 상태 플래그 — 프리셋 미저장"))
    elif name == "MetronomeBeat":
        safe_slots.append((i, addr, name, "메트로놈 비트 상태 — 프리셋 미저장"))
    elif name in ["Osc Sel", "Fx Sel", "Lfo Sel"]:
        safe_slots.append((i, addr, name, "UI 선택 상태 — 프리셋 미저장"))

for i, addr, name, reason in safe_slots:
    print(f"  ★ [{i:3d}] 0x{addr:08X}: \"{name}\" — {reason}")

# 첫 번째 패치 슬롯 상세
if safe_slots:
    slot_idx, slot_addr, slot_name, slot_reason = safe_slots[0]
    print(f"\n{'=' * 70}")
    print(f"추천 패치 슬롯: [{slot_idx}] \"{slot_name}\"")
    print(f"{'=' * 70}")
    print(f"  주소: 0x{slot_addr:08X}")
    print(f"  이유: {slot_reason}")
    print(f"  활용법:")
    print(f"    1. 해당 enum 인덱스의 switch/case에서 새 동작 추가")
    print(f"    2. 프리셋에 저장되지 않으므로 부작용 없음")
    print(f"    3. VST 연동에 영향 없음 (savedinpreset=0)")
