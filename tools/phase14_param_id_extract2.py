#!/usr/bin/env python3
"""
Phase 14-2b: PE 섹션 파싱 후 .text 영역에서만 RIP-relative 참조 검색 (최적화)
"""

import struct, sys, mmap

DLL_PATH = sys.argv[1]

with open(DLL_PATH, 'rb') as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    pe_sig_off = struct.unpack_from('<I', mm, 0x3C)[0]
    # COFF header
    num_sections = struct.unpack_from('<H', mm, pe_sig_off + 6)[0]
    opt_hdr_size = struct.unpack_from('<H', mm, pe_sig_off + 20)[0]
    # Optional header
    opt_off = pe_sig_off + 24
    magic = struct.unpack_from('<H', mm, opt_off)[0]
    if magic == 0x20B:  # PE32+
        image_base = struct.unpack_from('<Q', mm, opt_off + 24)[0]
    else:
        image_base = 0x180000000
    
    # Sections
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
        print(f"  {name:<10} VA={vaddr:#010x} VSize={vsize:#010x} Raw={raw_ptr:#010x} RawSize={raw_size:#010x}")

text_section = None
for name, vaddr, vsize, raw_ptr, raw_size in sections:
    if name == '.text':
        text_section = (vaddr, vsize, raw_ptr, raw_size)
        break

if not text_section:
    print("ERROR: .text section not found")
    sys.exit(1)

text_va, text_vsize, text_raw, text_raw_size = text_section
print(f"\nImage base: {image_base:#x}")
print(f".text: VA={text_va:#x} VSize={text_vsize:#x} Raw={text_raw:#x}")

# 파라미터 이름 오프셋 찾기 (RVA 기준)
TARGET_PARAMS = [
    "Osc1_Type", "Osc2_Type", "Osc1_Volume", "LFO1_Wave", "LFO2_Wave",
    "Cutoff", "Resonance", "Env_Attack", "Seq_Mode", "Arp_Mode",
    "RootNote", "Transpose", "VOLUME", "Pitch_Wheel", "Mod_Wheel",
    "AMOUNT_FM1_FILTRE1", "Chorus", "Delay", "Reverb",
    "Mod_S0_I0", "Gate_S0", "StepState_S0",
]

# 파일 오프셋 → RVA 변환
def raw_to_rva(raw_off):
    for name, vaddr, vsize, raw_ptr, raw_size in sections:
        if raw_ptr <= raw_off < raw_ptr + raw_size:
            return vaddr + (raw_off - raw_ptr)
    return None

# RVA → 파일 오프셋 변환
def rva_to_raw(rva):
    for name, vaddr, vsize, raw_ptr, raw_size in sections:
        if vaddr <= rva < vaddr + vsize:
            return raw_ptr + (rva - vaddr)
    return None

# 문자열 찾기 (raw offset 반환)
def find_string_raw(data, s):
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

# .text 영역에서 RIP-relative LEA 참조 검색
def find_lea_refs_in_text(mm, text_raw, text_raw_size, text_va, target_rva, image_base):
    results = []
    end = text_raw + text_raw_size
    i = text_raw
    while i < end - 7:
        b0 = mm[i]
        # LEA reg, [rip+disp32]
        if b0 in (0x48, 0x4C) and mm[i+1] == 0x8D:
            modrm = mm[i+2]
            mod = (modrm >> 6) & 3
            rm = modrm & 7
            if mod == 0 and rm == 5:
                disp = struct.unpack_from('<i', mm, i+3)[0]
                cmd_rva = text_va + (i - text_raw)
                next_rva = cmd_rva + 7
                target = next_rva + disp
                if target == target_rva:
                    results.append((i, cmd_rva, 'LEA'))
                i += 7
                continue
        i += 1
    return results

# 근처 MOV imm32 추출
def extract_nearby_imm32(mm, ref_raw, window=100):
    constants = []
    start = max(text_raw, ref_raw - window)
    end = min(text_raw + text_raw_size, ref_raw + window)
    for i in range(start, end - 4):
        b0 = mm[i]
        # MOV reg32, imm32 (B8-BF)
        if 0xB8 <= b0 <= 0xBF:
            val = struct.unpack_from('<I', mm, i+1)[0]
            if 0 < val < 0x10000:
                constants.append((i, val, 'MOV'))
        # MOV R8D-R15D, imm32 (41 B8-BF)
        elif b0 == 0x41 and 0xB8 <= mm[i+1] <= 0xBF and i + 5 < end:
            val = struct.unpack_from('<I', mm, i+2)[0]
            if 0 < val < 0x10000:
                constants.append((i, val, 'MOV_R'))
        # CMP reg, imm32 (81 /7)
        elif b0 == 0x81:
            modrm = mm[i+1]
            reg = (modrm >> 3) & 7
            if reg == 7 and i + 5 < end:
                val = struct.unpack_from('<I', mm, i+2)[0]
                if 0 < val < 0x10000:
                    constants.append((i, val, 'CMP'))
        # 3D = CMP EAX, imm32
        elif b0 == 0x3D and i + 4 < end:
            val = struct.unpack_from('<I', mm, i+1)[0]
            if 0 < val < 0x10000:
                constants.append((i, val, 'CMP_EAX'))
    return constants

# 메인
print(f"\n{'='*70}")
print("파라미터 이름 → LEA 참조 → 근처 상수 추출")
print(f"{'='*70}\n")

for param_name in TARGET_PARAMS:
    raw_offsets = find_string_raw(mm, param_name)
    if not raw_offsets:
        print(f"  {param_name}: NOT FOUND")
        continue
    
    raw_off = raw_offsets[0]
    rva = raw_to_rva(raw_off)
    if rva is None:
        print(f"  {param_name}: RVA conversion failed")
        continue
    
    refs = find_lea_refs_in_text(mm, text_raw, text_raw_size, text_va, rva, image_base)
    
    if refs:
        for ref_raw, ref_rva, ref_type in refs[:2]:
            nearby = extract_nearby_imm32(mm, ref_raw, window=80)
            before = [(c[1], c[0] - ref_raw) for c in nearby if c[0] < ref_raw]
            after = [(c[1], c[0] - ref_raw) for c in nearby if c[0] >= ref_raw]
            
            before_str = ', '.join([f'{v:#x}({d:+d})' for v, d in before[:5]])
            after_str = ', '.join([f'{v:#x}({d:+d})' for v, d in after[:5]])
            print(f"  {param_name}: str@{raw_off:#x} RVA@{rva:#x} → LEA@{ref_raw:#x}(RVA@{ref_rva:#x})")
            if before_str:
                print(f"    BEFORE: {before_str}")
            if after_str:
                print(f"    AFTER:  {after_str}")
    else:
        print(f"  {param_name}: str@{raw_off:#x} RVA@{rva:#x} → no LEA ref in .text")

mm.close()
print("\n완료")
