#!/usr/bin/env python3
"""
Phase 14-2b: MiniFreak DLL에서 InitSwFwParamIds 관련 상수 추출
VST param index ↔ HW firmware param id 매핑 상수를 DLL 바이너리에서 직접 찾는다.

전략: 
1. "Osc1_Type" 같은 파라미터 이름 문자열의 DLL 오프셋 찾기
2. 그 오프셋를 참조하는 LEA/RIP-relative 명령어 찾기
3. 그 근처에서 MOV/MOVZX로 로드되는 정수 상수 추출 (→ HW param ID)
4. 연속된 상수 블록 = 매핑 테이블
"""

import re, struct, sys

DLL_PATH = sys.argv[1]

with open(DLL_PATH, 'rb') as f:
    dll_data = f.read()

dll_size = len(dll_data)
print(f"DLL 크기: {dll_size:,} bytes")

# MiniFreak 핵심 파라미터 이름 (HW에도 존재하는 것들)
TARGET_PARAMS = [
    # Oscillator
    "Osc1_Type", "Osc1_Volume", "Osc1_CoarseTune", "Osc1_FineTune",
    "Osc2_Type", "Osc2_Volume", "Osc2_CoarseTune", "Osc2_FineTune",
    "Osc_BendRange", "Osc_Glide", "Osc_GlideMode", "Osc_Mixer_NonLinearity",
    # LFO
    "LFO1_Wave", "LFO1_Rate", "LFO1_RateSync", "LFO1_SyncEn", "LFO1_Retrig", "LFO1_Loop", "LFO1_SyncFilter",
    "LFO2_Wave", "LFO2_Rate", "LFO2_RateSync", "LFO2_SyncEn", "LFO2_Retrig", "LFO2_Loop", "LFO2_SyncFilter",
    # Filter/Env
    "Cutoff", "Resonance", "Env_Attack", "Env_Decay", "Env_Sustain", "Env_Release",
    "Env_AttackCurve", "Env_DecayCurve", "Env_ReleaseCurve",
    # Sequencer
    "Seq_Mode", "Seq_Length", "Seq_Gate", "Seq_Swing", "Seq_TimeDiv",
    "Arp_Mode", "Arp_Oct", "Arp_Ratchet", "Arp_Repeat",
    # General
    "RootNote", "Transpose", "VOLUME", "Pitch_Wheel", "Mod_Wheel",
    "Aftertouch", "Gen_UnisonOn", "Gen_UnisonCount", "Gen_UnisonSpread",
    "Gen_PolyAlloc", "Gen_LegatoMode",
    # FM routing
    "AMOUNT_FM1_FILTRE1", "AMOUNT_FM2_FILTER", "AMOUNT_FM3_OSC1",
    "AMOUNT_AM_EXP_VCA", "AMOUNT_RES_FILTRE1",
    # CycEnv
    "CycEnv_Mode", "CycEnv_Rise", "CycEnv_Fall", "CycEnv_Hold",
    # FX
    "Chorus", "Delay", "Reverb", "Phaser", "Flanger", "Distortion", "Bitcrusher",
    "Delay_Routing", "Reverb_Routing",
    # Matrix (샘플)
    "Mod_S0_I0", "Mod_S0_I1", "Mod_S0_I2", "Mod_S0_I3",
    "Pitch_S0_I0", "Pitch_S0_I1", "Pitch_S0_I2", "Pitch_S0_I3", "Pitch_S0_I4", "Pitch_S0_I5",
    "Velo_S0_I0", "Velo_S0_I1",
    "Gate_S0", "StepState_S0",
]

# UTF-8 null-terminated 문자열 검색
def find_string(data, s):
    """바이너리에서 null-terminated UTF-8 문자열의 오프셋 반환"""
    needle = s.encode('utf-8') + b'\x00'
    offsets = []
    pos = 0
    while True:
        idx = data.find(needle, pos)
        if idx == -1:
            break
        offsets.append(idx)
        pos = idx + 1
    return offsets

# RIP-relative LEA 참조 검색
def find_rip_refs_to(data, target_offset, image_base=0x180000000):
    """x86-64 RIP-relative addressing에서 target_offset를 참조하는 명령어 위치 찾기"""
    results = []
    text_start = 0  # .text section 시작 (대략)
    text_end = min(dll_size, 0x01800000)
    
    for i in range(text_start, text_end - 7):
        # LEA reg, [rip+disp32] = [48|4C] 8D [05-3F, 40-7F] xx xx xx xx
        b0 = data[i]
        if b0 in (0x48, 0x4C) and i + 1 < dll_size and data[i+1] == 0x8D:
            modrm = data[i+2]
            mod = (modrm >> 6) & 3
            rm = modrm & 7
            if mod == 0 and rm == 5:  # RIP-relative
                if i + 6 < dll_size:
                    disp = struct.unpack_from('<i', data, i+3)[0]
                    rip_va = image_base + i + 7  # 다음 명령어 VA
                    effective_va = rip_va + disp
                    effective_offset = effective_va - image_base
                    if effective_offset == target_offset:
                        results.append((i, 'LEA', f"RIP+{disp:+#x}"))
        # MOV reg, [rip+disp32] (다양한 형태)
        elif b0 in (0x48, 0x4C, 0x8B) and i + 1 < dll_size:
            # 8B /mod = MOV r, [rip+disp]
            if b0 == 0x8B:
                modrm = data[i+1]
                mod = (modrm >> 6) & 3
                rm = modrm & 7
                if mod == 0 and rm == 5 and i + 5 < dll_size:
                    disp = struct.unpack_from('<i', data, i+2)[0]
                    rip_va = image_base + i + 6
                    effective_va = rip_va + disp
                    effective_offset = effective_va - image_base
                    if effective_offset == target_offset:
                        results.append((i, 'MOV', f"RIP+{disp:+#x}"))
    
    return results

# MOV dword [rip+disp] 또는 상수 로드 근처 분석
def extract_nearby_constants(data, ref_offset, window=200):
    """명령어 참조 위치 근처에서 정수 상수 추출"""
    start = max(0, ref_offset - window)
    end = min(dll_size, ref_offset + window)
    region = data[start:end]
    
    constants = []
    for i in range(len(region) - 4):
        # MOV EDX/ECX/EAX/R8D.., imm32
        # B8+rd imm32, B9+rd imm32, BA+rd imm32, BB+rd imm32
        # 41 B8+rd imm32 (R8D~R15D)
        b0 = region[i]
        b1 = region[i+1] if i+1 < len(region) else 0
        
        # MOV reg32, imm32 (B8-BF)
        if 0xB8 <= b0 <= 0xBF:
            val = struct.unpack_from('<I', region, i+1)[0]
            if 0 < val < 0x10000:  # 합리적인 param ID 범위
                constants.append((start + i, val, f'MOV reg, #{val:#x}'))
        
        # MOV R8D-R15D, imm32 (41 B8-BF)
        elif b0 == 0x41 and 0xB8 <= b1 <= 0xBF and i + 5 < len(region):
            val = struct.unpack_from('<I', region, i+2)[0]
            if 0 < val < 0x10000:
                constants.append((start + i, val, f'MOV r8d+, #{val:#x}'))
        
        # CMP reg, imm32 (81 /7 imm32 or 3D imm32)
        elif b0 == 0x3D and i + 4 < len(region):
            val = struct.unpack_from('<I', region, i+1)[0]
            if 0 < val < 0x10000:
                constants.append((start + i, val, f'CMP EAX, #{val:#x}'))
        elif b0 == 0x81:
            modrm = b1
            reg = (modrm >> 3) & 7
            if reg == 7 and i + 5 < len(region):  # CMP
                val = struct.unpack_from('<I', region, i+2)[0]
                if 0 < val < 0x10000:
                    constants.append((start + i, val, f'CMP reg, #{val:#x}'))
    
    return constants

# 메인 분석
print(f"\n{'='*70}")
print(f"파라미터 문자열 → RIP 참조 → 상수 추출")
print(f"{'='*70}")

IMAGE_BASE = 0x180000000

found_params = {}
ref_count = 0

for param_name in TARGET_PARAMS:
    offsets = find_string(dll_data, param_name)
    if not offsets:
        continue
    
    # 첫 번째 오프셋 사용 (보통 .rdata)
    str_offset = offsets[0]
    
    # RIP-relative 참조 찾기
    refs = find_rip_refs_to(dll_data, str_offset, IMAGE_BASE)
    
    if refs:
        for ref_off, ref_type, ref_desc in refs[:3]:  # 최대 3개 참조
            ref_count += 1
            # 근처 상수 추출
            nearby = extract_nearby_constants(dll_data, ref_off, window=150)
            
            # 참조 위치 바로 근처 (앞쪽)의 상수 찾기
            before_constants = [c for c in nearby if c[0] < ref_off and ref_off - c[0] < 60]
            after_constants = [c for c in nearby if c[0] >= ref_off and c[0] - ref_off < 60]
            
            if param_name not in found_params:
                found_params[param_name] = {
                    'str_offset': str_offset,
                    'refs': [],
                    'before_constants': [],
                    'after_constants': [],
                }
            
            found_params[param_name]['refs'].append((ref_off, ref_type))
            found_params[param_name]['before_constants'].extend(before_constants)
            found_params[param_name]['after_constants'].extend(after_constants)

print(f"\nRIP 참조 발견: {ref_count}개")
print(f"파라미터 매핑 후보: {len(found_params)}개\n")

# 결과 정리
print(f"{'Param Name':<30} {'Str Offset':>12} {'Ref Offset':>12} {'Before Const':>20} {'After Const':>20}")
print("-" * 100)

for param_name, info in sorted(found_params.items()):
    for ref_off, ref_type in info['refs'][:1]:
        before = [str(c[1]) for c in info['before_constants'][:3]]
        after = [str(c[1]) for c in info['after_constants'][:3]]
        print(f"{param_name:<30} {info['str_offset']:>12#x} {ref_off:>12#x} {','.join(before):<20} {','.join(after):<20}")

# 상수 블록 분석: 연속된 오프셋에 있는 상수 배열 찾기
print(f"\n{'='*70}")
print("상수 블록 분석 (연속 매핑 테이블 탐색)")
print(f"{'='*70}")

all_constant_regions = []
for param_name, info in found_params.items():
    for c in info['before_constants']:
        all_constant_regions.append((c[0], c[1], param_name, 'before'))
    for c in info['after_constants']:
        all_constant_regions.append((c[0], c[1], param_name, 'after'))

# 오프셋으로 정렬
all_constant_regions.sort(key=lambda x: x[0])

# 연속된 상수 찾기
if all_constant_regions:
    print(f"\n총 {len(all_constant_regions)}개 상수 후보")
    for off, val, name, pos in all_constant_regions[:50]:
        print(f"  {off:#12x}: {val:>6} ({name}, {pos})")

print("\n완료")
