#!/usr/bin/env python3
"""
Phase 15-1c: eEditParams 포인터 테이블 완전 추출 + deprecated 슬롯 분류
포인터 테이블 주소를 기준으로 enum 인덱스 확정
"""

import struct, os

FW_DIR = "reference/firmware_extracted"
CM4_BIN = os.path.join(FW_DIR, "minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin")
BASE_CM4 = 0x08120000

with open(CM4_BIN, "rb") as f:
    cm4 = f.read()

# 스캔 1에서 발견: 포인터 테이블이 0x081AF954("Unison Count")를 참조
# table context: 0x081AEFE4 0x081AEFE4 0x081AEFE4 0x081AEFE4 0x081AF954 0x081AF970 0x081AF984 0x081AF994 0x081AF9A4
# → 포인터 테이블 주소를 찾아야 함

# "Unison Count"(0x081AF954)의 패킹값을 검색하여 포인터 테이블 위치를 찾기
target = struct.pack('<I', 0x081AF954)
pos = 0
table_locs = []
while True:
    pos = cm4.find(target, pos)
    if pos == -1:
        break
    table_locs.append(pos)
    pos += 4

print("=== eEditParams 포인터 테이블 후보 ===")
print(f"'Unison Count'(0x081AF954) 참조: {len(table_locs)}개")

# 각 참조 위치에서 포인터 배열을 읽기
for loc in table_locs:
    vaddr = loc + BASE_CM4
    # 앞뒤로 포인터 배열 읽기
    start = max(0, loc - 40)
    end = min(len(cm4), loc + 40)
    print(f"\n--- table at file offset 0x{loc:06X} (vaddr 0x{vaddr:08X}) ---")
    
    ptrs = []
    for i in range(start, end - 3, 4):
        v = struct.unpack_from('<I', cm4, i)[0]
        ptrs.append((i, v))
    
    for off, v in ptrs:
        # 유효한 CM4 flash 주소인지 확인
        if 0x08120000 <= v <= 0x081C0000:
            # 해당 주소의 문자열 읽기
            str_off = v - BASE_CM4
            if 0 <= str_off < len(cm4):
                null = cm4.find(b'\x00', str_off)
                if null > str_off:
                    s = cm4[str_off:null]
                    if all(32 <= b < 127 for b in s):
                        print(f"  0x{off+BASE_CM4:08X}: 0x{v:08X} → \"{s.decode('ascii')}\"")
                        continue
        # 그 외
        if v != 0x081AEFE4:  # 반복되는 의미없는 값 스킵
            marker = ""
            if v == 0x081AEFE4:
                marker = " [FILLER]"
            print(f"  0x{off+BASE_CM4:08X}: 0x{v:08X}{marker}")

# 스캔 결과의 두 번째 테이블 패턴 분석
# 0x081AF9A4, 0x081AEA78, 0x081AEF74, 0x081AF9B4, 0x081AF9C4, 0x081AF9D0, 0x081AF9D8, 0x081AF9E0, 0x081AEA8C
# 이것도 포인터 테이블!

# 더 체계적으로: 모든 eEditParams 문자열 주소에 대해 연속된 포인터 테이블 검색
print("\n\n=== eEditParams 포인터 테이블 체계적 탐색 ===")

edit_param_names = {
    0x081AF904: "Macro1 dest",
    0x081AF910: "Macro2 dest",
    0x081AF91C: "Macro1 amount",
    0x081AF92C: "Macro2 amount",
    0x081AF93C: "Retrig Mode",
    0x081AF948: "Legato Mono",
    0x081AF954: "Unison Count",
    0x081AF964: "Poly Allocation",
    0x081AF974: "Poly Steal Mode",
    0x081AF984: "Vibrato Depth",
    0x081AF994: "UnisonOn TO BE DEPRECATED",
    0x081AF9A4: "??? (unknown param)",
    0x081AF9B4: "??? (unknown param)",
    0x081AF9C4: "Matrix Src VeloAT",
    0x081AF9D4: "Osc1 Mod Quant",
    0x081AF9E4: "Release Curve",
    0x081AF9F4: "Osc Mix Non-Lin",
    0x081AFA04: "Glide Sync",
    0x081AFA10: "Pitch 1",
    0x081AFA18: "Pitch 2",
    0x081AFA20: "Velo > VCF",
    0x081AFA2C: "Kbd Src",
    0x081AFA34: "Unison Mode",
    0x081AFA40: "Osc Free Run",
    0x081AFA50: "Mx Cursor",
    0x081AFA5C: "Mx Page",
    0x081AFA64: "Mx Mode",
    0x081AFA6C: "Osc Sel",
    0x081AFA74: "Fx Sel",
    0x081AFA7C: "Lfo Sel",
    0x081AFA84: "Octave Tune",
    0x081AFA90: "Tempo Div",
    0x081AFA9C: "Seq Page",
    0x081AFAB4: "PlayState",
    0x081AFAC0: "RecState",
    0x081AFAC8: "RecMode",
    0x081AFAD0: "Cursor",
    0x081AFB00: "obsolete Rec Count-In",
    0x081AFB18: "Preset filter",
    0x081AFB28: "VST_IsConnected",
    0x081AFB38: "Pre Master Volume",
    0x081AFB4C: "Favorites Page",
}

# 첫 번째 확실한 포인터 테이블 (from 스캔 1)
# table context: ...0x081AF954 0x081AF970 0x081AF984 0x081AF994 0x081AF9A4...
# 0x081AF970 → 읽어보기
test_addrs = [0x081AF970, 0x081AF9A4, 0x081AF9B4, 0x081AF9D0, 0x081AF9D8, 0x081AF9E0,
              0x081AFA00, 0x081AEA78, 0x081AEF74, 0x081AEA8C, 0x081AEA84, 0x081AEA94,
              0x081AEA6C, 0x081AF9EC, 0x081AF5D8, 0x081AF5E4, 0x081AF5F0, 0x081B0F70,
              0x081B0F74, 0x081B0DB4, 0x081AE290, 0x081B1B24, 0x081AF4F8, 0x081AF500,
              0x081AFA1C, 0x081AFA24, 0x081AFA3C, 0x081AFA44, 0x081AFAFC, 0x081AFA68,
              0x081AFA80, 0x081AFA88, 0x081AFAB0, 0x081AFAD8, 0x081AFAE8, 0x081AFAF8,
              0x081AFB1C, 0x081AFB20, 0x081AFB24, 0x081AFB2C, 0x081AFB30, 0x081AFB34,
              0x081AFB3C, 0x081B34A4, 0x081B3298, 0x081B33E8, 0x081B0FC0,
              0x081AFB88, 0x081AFB90, 0x081AFB98, 0x081AFBA0, 0x081AFBA4, 0x081AFBA8, 0x081AFBAC]

print("\n--- 포인터 테이블 내 미확인 주소의 문자열 확인 ---")
for addr in test_addrs:
    off = addr - BASE_CM4
    if 0 <= off < len(cm4):
        null = cm4.find(b'\x00', off)
        if null > off and null - off < 100:
            s = cm4[off:null]
            if all(32 <= b < 127 for b in s) and len(s) > 1:
                name = s.decode('ascii')
                known = edit_param_names.get(addr, "")
                extra = f" [known: {known}]" if known else " [NEW]"
                print(f"  0x{addr:08X}: \"{name}\"{extra}")
            else:
                # 데이터 확인
                if addr in edit_param_names:
                    print(f"  0x{addr:08X}: [non-string data] (known: {edit_param_names[addr]})")
        else:
            if addr in edit_param_names:
                print(f"  0x{addr:08X}: [out of range or long] (known: {edit_param_names[addr]})")


# VST_IsConnected 근처 테이블 분석 (세 번째 컨텍스트)
# 0x081AFB1C 0x081AFB20 0x081B34A4 0x081AFB24 0x081AFB28 0x081AFB2C 0x081AFB30 0x081AFB34 0x081AFB38
# 이것은 [속성주소, 속성값] 쌍으로 보임!
print("\n\n=== VST_IsConnected 근처 속성 테이블 분석 ===")
# [주소, 값] 쌍으로 읽기
pairs_start = 0x081AFB1C - BASE_CM4
for i in range(0, 48, 8):
    addr1 = struct.unpack_from('<I', cm4, pairs_start + i)[0]
    val1 = struct.unpack_from('<I', cm4, pairs_start + i + 4)[0]
    
    # addr1이 문자열 주소면 읽기
    s1 = ""
    if 0x08120000 <= addr1 <= 0x081C0000:
        off = addr1 - BASE_CM4
        if 0 <= off < len(cm4):
            null = cm4.find(b'\x00', off)
            if null > off:
                raw = cm4[off:null]
                if all(32 <= b < 127 for b in raw):
                    s1 = raw.decode('ascii')
    
    if s1:
        print(f"  0x{addr1:08X} (\"{s1}\") = {val1} (0x{val1:08X})")
    else:
        print(f"  0x{addr1:08X} = {val1} (0x{val1:08X})")


# Osc Mix Non-Lin 근처 테이블도 [주소, 값] 쌍 분석
print("\n\n=== Osc Mix Non-Lin 근처 속성 테이블 분석 ===")
pairs_loc2 = 0x081AF6DC - BASE_CM4  # from: 0x0000000D 0x081AF6DC 0x001B0004
for i in range(-16, 32, 4):
    off = pairs_loc2 + i
    if 0 <= off < len(cm4) - 3:
        v = struct.unpack_from('<I', cm4, off)[0]
        marker = ""
        if v in edit_param_names:
            marker = f" → \"{edit_param_names[v]}\""
        elif 0x08120000 <= v <= 0x081C0000:
            str_off = v - BASE_CM4
            null = cm4.find(b'\x00', str_off)
            if null > str_off and null - str_off < 50:
                raw = cm4[str_off:null]
                if all(32 <= b < 127 for b in raw):
                    marker = f" → \"{raw.decode('ascii')}\""
        print(f"  0x{off+BASE_CM4:08X}: 0x{v:08X}{marker}")

print("\n--- 완료 ---")
