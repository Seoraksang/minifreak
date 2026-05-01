#!/usr/bin/env python3
"""
Phase 15-1e: eEditParams 전체 enum 문자열 클러스터 재분석
0x081AF904~0x081AFC34 영역의 모든 문자열을 올바르로 읽고
포인터 테이블이 아닌 직접 enum 인덱스 매핑 수행
"""

import struct, os

FW_DIR = "reference/firmware_extracted"
CM4_BIN = os.path.join(FW_DIR, "minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin")
BASE_CM4 = 0x08120000

with open(CM4_BIN, "rb") as f:
    cm4 = f.read()

# 전체 eEditParams 문자열 클러스터: 0x081AF904~0x081AFC34+
# Phase 8에서 이미 추출했던 79개 문자열을 정확히 읽기
# null-terminated string array로 가정

CLUSTER_START = 0x081AF904 - BASE_CM4
CLUSTER_END = 0x081AFC40 - BASE_CM4  # 여유있게

print("=== eEditParams 문자열 클러스터 정밀 추출 ===\n")

# 연속된 null-terminated 문자열 읽기
entries = []
pos = CLUSTER_START
while pos < CLUSTER_END:
    if cm4[pos] == 0:
        pos += 1
        continue
    # 문자열 끝 찾기
    null = cm4.find(b'\x00', pos)
    if null == -1 or null > CLUSTER_END:
        break
    raw = cm4[pos:null]
    if len(raw) > 0 and all(32 <= b < 127 for b in raw):
        addr = pos + BASE_CM4
        entries.append((addr, raw.decode('ascii')))
        pos = null + 1
    else:
        pos += 1

# Filler(0x081AEFE4 = "  ")는 이미 위에서 스킵됨
print(f"총 {len(entries)}개 문자열 추출:\n")

# 분류
DEPRECATED_KEYWORDS = ['deprecated', 'obsolete']
UI_STATE_KEYWORDS = ['Cursor', 'Mx ', 'Sel', 'PlayState', 'RecState', 'RecMode',
                     'MetronomeBeat', 'Preset filter', 'VST_IsConnected', 
                     'Favorites Page', 'Seq Page', 'Playing Tempo']
SHORT_NAMES = ['C', 'C#', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A#', 'B',  # 음이름
               'L1', 'L2', 'V/A', 'W', 'K', 'LFO 1', 'LFO 2']  # UI 라벨

print("┌─────┬──────────────┬─────────────────────────────────────────┬──────────┐")
print("│ idx │ 주소         │ 이름                                    │ 분류     │")
print("├─────┼──────────────┼─────────────────────────────────────────┼──────────┤")

deprecated = []
ui_state = []
active = []
note_names = []
ui_labels = []

for i, (addr, name) in enumerate(entries):
    # 분류
    cat = "활성 파라미터"
    
    if any(kw in name for kw in DEPRECATED_KEYWORDS):
        cat = "★ DEPRECATED"
        deprecated.append((i, addr, name))
    elif any(kw in name for kw in UI_STATE_KEYWORDS):
        cat = "UI 상태"
        ui_state.append((i, addr, name))
    elif name in SHORT_NAMES:
        cat = "UI 라벨"
        ui_labels.append((i, addr, name))
    elif name.startswith('Asgn') or name in ['Pitch', 'Wave', 'Timb', 'CycEnv',
                                              'Velo/AT', 'Keyb', 'Timbre',
                                              'Assign1', 'Assign2', 'Assign3']:
        cat = "UI 라벨"
        ui_labels.append((i, addr, name))
    else:
        active.append((i, addr, name))
    
    print(f"│ {i:3d} │ 0x{addr:08X} │ {name:<40s} │ {cat:<8s} │")

print("└─────┴──────────────┴─────────────────────────────────────────┴──────────┘")

# 요약
print(f"\n{'='*70}")
print("분류 요약")
print(f"{'='*70}")
print(f"  활성 파라미터:  {len(active)}개")
print(f"  ★ DEPRECATED:   {len(deprecated)}개")
print(f"  UI 상태 플래그: {len(ui_state)}개")
print(f"  UI 라벨/상수:   {len(ui_labels)}개")

print(f"\n--- 활성 파라미터 ---")
for i, addr, name in active:
    print(f"  [{i:3d}] 0x{addr:08X}: {name}")

print(f"\n--- ★ DEPRECATED ---")
for i, addr, name in deprecated:
    print(f"  [{i:3d}] 0x{addr:08X}: {name}")

print(f"\n--- UI 상태 플래그 (프리셋 미저장) ---")
for i, addr, name in ui_state:
    print(f"  [{i:3d}] 0x{addr:08X}: {name}")

# 안전한 패치 슬롯 최종 선정
print(f"\n{'='*70}")
print("안전한 패치 슬롯 (우선순위순)")
print(f"{'='*70}")

safe = []
# 1순위: 명시적 DEPRECATED/OBSOLETE
for i, addr, name in deprecated:
    safe.append((1, i, addr, name, f"명시적 deprecated — 기존 기능 무, 프리셋 미저장"))

# 2순위: UI 상태 플래그
for i, addr, name in ui_state:
    reason = "UI 상태 플래그 — 프리셋 미저장"
    if name == "VST_IsConnected":
        reason = "VST 연결 상태 — 프리셋 미저장, 독립적 동작"
    safe.append((2, i, addr, name, reason))

# 3순위: UI 라벨 (enum 값이지만 프리셋 파라미터 아님)
for i, addr, name in ui_labels:
    safe.append((3, i, addr, name, "UI 표시용 라벨 — 프리셋 미저장"))

safe.sort(key=lambda x: (x[0], x[1]))
for priority, i, addr, name, reason in safe:
    p = "1순위" if priority == 1 else "2순위" if priority == 2 else "3순위"
    print(f"  [{p}] [{i:3d}] 0x{addr:08X}: \"{name}\"")
    print(f"       → {reason}")

# 최종 추천
print(f"\n{'='*70}")
print("★ 최종 추천: 안전한 펌웨어 패치 슬롯")
print(f"{'='*70}")
print("""
1. "UnisonOn TO BE DEPRECATED" (idx 10)
   - Arturia 개발자가 명시적으로 DEPRECATED로 표시
   - 기존 기능 유지 불필요 → 새 기능으로 대체 가능
   - switch/case에서 해당 case를 찾아 패치하면 됨

2. "obsolete Rec Count-In" (idx 40)
   - "obsolete" 명시 → 더 이상 사용되지 않음
   
3. "VST_IsConnected" (idx 42)
   - VST 연결 상태 플래그 → 하드웨어 독립 동작 가능

4. "Cursor" / "Mx Cursor" / "PlayState" 등 UI 상태 (idx 24~36)
   - 프리셋에 저장되지 않는 상태값
   - UI 디스플레이 용도로만 사용됨

⚠ 주의: idx는 문자열 클러스터 내 순서이며, 실제 eEditParams enum 값과 다를 수 있음
   실제 enum 인덱스는 Ghidra에서 MNF_Edit::set() 함수의 switch/case를 분석해야 확정
""")

# VST XML과 크로스체크
print("=== VST XML savedinpreset=0 파라미터 (deprecated 후보) ===")
import re
xml_path = "reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/minifreak_vst_params.xml"
if os.path.exists(xml_path):
    with open(xml_path, 'r') as f:
        xml = f.read()
    for m in re.finditer(r'<param\s+name="([^"]+)"[^>]*savedinpreset="0"[^>]*>', xml):
        print(f"  {m.group(1)}")
