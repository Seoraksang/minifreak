#!/usr/bin/env python3
"""
Phase 14-2c: InitSwFwParamIds 함수 근처 상수 배열 추출
전략: LEA 참조 밀집 영역에서 MOV/CMP 상수 배열을 대량 추출
"""

import struct, sys, mmap

DLL_PATH = sys.argv[1]

with open(DLL_PATH, 'rb') as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    dll_data = bytes(mm)

pe_sig_off = struct.unpack_from('<I', mm, 0x3C)[0]
num_sections = struct.unpack_from('<H', mm, pe_sig_off + 6)[0]
opt_hdr_size = struct.unpack_from('<H', mm, pe_sig_off + 20)[0]
opt_off = pe_sig_off + 24
image_base = struct.unpack_from('<Q', mm, opt_off + 24)[0]

sections = []
sec_off = opt_off + opt_hdr_size
for i in range(num_sections):
    s = sec_off + i * 40
    name = mm[s:s+8].rstrip(b'\x00').decode('ascii', errors='replace')
    vsize = struct.unpack_from('<I', mm, s + 8)[0]
    vaddr = struct.unpack_from('<I', mm, s + 12)[0]
    raw_size = struct.unpack_from('<I', mm, s + 16)[0]
    raw_ptr = struct.unpack_from('<I', mm, s + 20)[0]
    sections.append((name, vaddr, vsize, raw_ptr, raw_size))

def rva_to_raw(rva):
    for name, vaddr, vsize, raw_ptr, raw_size in sections:
        if vaddr <= rva < vaddr + vsize:
            return raw_ptr + (rva - vaddr)
    return None

def raw_to_rva(raw_off):
    for name, vaddr, vsize, raw_ptr, raw_size in sections:
        if raw_ptr <= raw_off < raw_ptr + raw_size:
            return vaddr + (raw_off - raw_ptr)
    return None

text_raw = rva_to_raw(0x1000)
text_size = rva_to_raw(0x1000 + 0x133250c) - text_raw if rva_to_raw(0x1000 + 0x133250c) else 0x1332600

# 모든 MiniFreak 파라미터 이름에 대한 LEA ref 찾기
import re, subprocess
result = subprocess.run(['strings', DLL_PATH], capture_output=True, text=True)
all_strings = result.stdout.split('\n')

param_patterns = [
    r'^Osc[12]_', r'^Osc_', r'^LFO[12]_', r'^Lfo[123]_',
    r'^Cutoff$', r'^Resonance$', r'^Env_', r'^CycEnv_', r'^ModEnvelope_',
    r'^Seq_', r'^ArpSeq_', r'^Arp_', r'^Gate_S\d+$', r'^StepState_S\d+$',
    r'^Mod_S\d+_I\d+$', r'^Pitch_S\d+_I\d+$', r'^Velo_S\d+_I\d+$',
    r'^AMOUNT_', r'^RootNote$', r'^Transpose$', r'^VOLUME$',
    r'^Pitch_Wheel$', r'^Mod_Wheel$', r'^Aftertouch',
    r'^Gen_', r'^Vca_', r'^VCA_', r'^Spread$',
    r'^Chord_', r'^DistoType$', r'^FilterType$',
    r'^VeloMod_', r'^Chorus$', r'^Delay$', r'^Reverb$', r'^Phaser$',
    r'^Flanger$', r'^Distortion$', r'^Bitcrusher$', r'^Octaver$',
    r'^Slot[12]_', r'^AutomReserved', r'^Sustain_Polarity$',
    r'^SUSTAIN_TIME$', r'^Panic$', r'^Panel_Mode$',
    r'^DEPTH_CHORUS$', r'^Delay_Routing$', r'^Reverb_Routing$',
    r'^Pitch1_Mod_On$', r'^Pitch2_Mod_On$', r'^PitchReset$',
    r'^MATRIX_AMOUNT', r'^MATRIX_LINE',
]

param_names = set()
for s in all_strings:
    s = s.strip()
    if not s or len(s) > 60:
        continue
    for pat in param_patterns:
        if re.match(pat, s):
            param_names.add(s)
            break

print(f"파라미터 이름 {len(param_names)}개 발견")

# 문자열 오프셋 맵 구축
def find_str_raw(s):
    needle = s.encode('utf-8') + b'\x00'
    idx = dll_data.find(needle)
    return idx if idx >= 0 else None

str_offsets = {}
for name in sorted(param_names):
    raw_off = find_str_raw(name)
    if raw_off:
        rva = raw_to_rva(raw_off)
        if rva:
            str_offsets[name] = (raw_off, rva)

print(f"문자열 RVA 매핑 {len(str_offsets)}개 완료")

# .text에서 LEA 참조 대량 검색
def find_all_lea_refs(target_rvas):
    """여러 타겟 RVA에 대한 LEA 참조를 한 번에 검색"""
    target_set = set(target_rvas)
    results = {}  # target_rva → [(raw_off, cmd_rva)]
    
    end = text_raw + text_size
    i = text_raw
    
    while i < end - 7:
        b0 = mm[i]
        if b0 in (0x48, 0x4C) and mm[i+1] == 0x8D:
            modrm = mm[i+2]
            if (modrm >> 6) == 0 and (modrm & 7) == 5:
                disp = struct.unpack_from('<i', mm, i+3)[0]
                cmd_rva = raw_to_rva(i) if raw_to_rva(i) else (0x1000 + (i - text_raw))
                next_rva = cmd_rva + 7
                target = next_rva + disp
                if target in target_set:
                    if target not in results:
                        results[target] = []
                    results[target].append(i)
                i += 7
                continue
        i += 1
    
    return results

all_rvas = {rva for _, (_, rva) in str_offsets.items()}
print(f"\nLEA 참조 검색 중... ({len(all_rvas)} 타겟)")
lea_results = find_all_lea_refs(all_rvas)
print(f"참조된 문자열: {len(lea_results)}개")

# InitSwFwParamIds 영역 집중 분석
# 앞서 발견: Osc1_Type LEA@0x3b598b, Mod_Wheel LEA@0x3b62c4 → 이 영역이 InitSwFwParamIds
# 더 넓은 영역에서 연속 상수 패턴 찾기

# 영역 1: 0x3b5000 ~ 0x3c0000 (InitSwFwParamIds 후보)
# 영역 2: 0x3d5000 ~ 0x3e2000 (또 다른 매핑 영역)

regions = [
    (0x3b5000, 0x3c0000, "InitSwFwParamIds-A"),
    (0x3d5000, 0x3e3000, "InitSwFwParamIds-B"),
]

print(f"\n{'='*70}")
print("집중 영역 상수 배열 추출")
print(f"{'='*70}")

for rva_start, rva_end, region_name in regions:
    raw_start = rva_to_raw(rva_start)
    raw_end = rva_to_raw(rva_end)
    if not raw_start or not raw_end:
        continue
    
    print(f"\n### {region_name}: RVA {rva_start:#x} ~ {rva_end:#x}")
    
    # MOV reg32, imm32 패턴 대량 추출
    constants = []
    i = raw_start
    while i < raw_end - 4:
        b0 = mm[i]
        # MOV reg32, imm32
        if 0xB8 <= b0 <= 0xBF:
            val = struct.unpack_from('<I', mm, i+1)[0]
            constants.append((i, val))
            i += 5
            continue
        # MOV R8D-R15D, imm32
        elif b0 == 0x41 and 0xB8 <= mm[i+1] <= 0xBF:
            val = struct.unpack_from('<I', mm, i+2)[0]
            constants.append((i, val))
            i += 6
            continue
        # CMP reg, imm32
        elif b0 == 0x81:
            modrm = mm[i+1]
            reg = (modrm >> 3) & 7
            if reg == 7:
                val = struct.unpack_from('<I', mm, i+2)[0]
                constants.append((i, val))
                i += 6
                continue
        i += 1
    
    # 연속된 상수 패턴 찾기 (5바이트 간격 MOV = 매핑 테이블)
    runs = []
    current_run = []
    for off, val in constants:
        if val <= 0xFFFF:  # 합리적인 범위
            if current_run and off - current_run[-1][0] <= 30:  # 연속 (명령어 길이 고려)
                current_run.append((off, val))
            else:
                if len(current_run) >= 3:
                    runs.append(current_run)
                current_run = [(off, val)]
        else:
            if len(current_run) >= 3:
                runs.append(current_run)
            current_run = []
    if len(current_run) >= 3:
        runs.append(current_run)
    
    print(f"  총 상수: {len(constants)}, 연속 런: {len(runs)}")
    
    # 주요 런 출력
    for run in runs:
        if len(run) >= 5:
            vals = [v for _, v in run]
            start_rva = raw_to_rva(run[0][0])
            print(f"\n  Run @ RVA {start_rva:#x} ({len(run)}개):")
            # 줄당 16개
            for row in range(0, len(vals), 16):
                chunk = vals[row:row+16]
                hex_str = ', '.join([f'{v:#06x}' for v in chunk])
                print(f"    [{row:3d}] {hex_str}")

mm.close()
print("\n완료")
