#!/usr/bin/env python3
"""
Phase 14-1b: x86-64 DLL에서 kCollageUsbInHeaderSize / kCollageTcpHeaderSize 실제값 추출
x86-64에서 상수 비교는 보통 cmp reg, imm 형태
"""

import struct, sys, re

DLL_PATH = sys.argv[1]

with open(DLL_PATH, "rb") as f:
    dll = f.read()

# 문자열 "kCollageUsbInHeaderSize"와 "kCollageTcpHeaderSize"의 오프셋 찾기
usb_str = b'kCollageUsbInHeaderSize\x00'
tcp_str = b'kCollageTcpHeaderSize\x00'

usb_offset = dll.find(usb_str)
tcp_offset = dll.find(tcp_str)

print(f"kCollageUsbInHeaderSize string @ 0x{usb_offset:08X}")
print(f"kCollageTcpHeaderSize string @ 0x{tcp_offset:08X}")

# x86-64에서 이 문자열을 참조하는 코드 주변에서 상수값 찾기
# 방법: LEA instruction이 이 문자열 주소를 로드하는 근처에서 CMP 명령어 찾기
# 또는: DLL data section에서 소수 정수(4~32)가 문자열 옆에 배치된 패턴 찾기

# 더 간단한 방법: 문자열 근처(±256바이트)에서 작은 정수 패턴 검색
def find_nearby_constants(data, offset, name, search_range=512):
    print(f"\n{name} 근처 상수 검색 (offset ±{search_range}):")
    
    start = max(0, offset - search_range)
    end = min(len(data), offset + search_range)
    region = data[start:end]
    
    # x86-64에서 자주 쓰이는 패턴:
    # 1. cmp ecx/edx/r8d, imm8 (83 F9 xx, 83 FA xx, 83 C0 xx 등)
    # 2. mov ecx/edx, imm32 (B9 xx xx xx xx, BA xx xx xx xx 등)
    # 3. sub/cmp r32, imm32 (81 xx xx xx xx xx)
    
    # 작은 상수 (4~64) 후보
    candidates = []
    for i in range(len(region) - 4):
        val_le32 = struct.unpack_from('<I', region, i)[0]
        if 4 <= val_le32 <= 64:
            # 주변에 해당 상수를 CMP나 MOV로 사용하는 명령어 패턴이 있는지
            # CMP reg32, imm8: 83 /7 ib
            # CMP reg32, imm32: 81 /7 id
            # MOV reg32, imm32: B8+rd id
            for back in range(max(0, i-2), i):
                byte0 = region[back]
                byte1 = region[back+1] if back+1 < len(region) else 0
                
                # CMP r/m32, imm8 (sign-extended)
                if byte0 == 0x83 and (byte1 & 0xF8) == 0xF8:
                    imm8 = struct.unpack_from('<b', region, i)[0]
                    if 4 <= imm8 <= 64:
                        candidates.append({
                            'offset': start + i,
                            'value': imm8,
                            'type': 'cmp_imm8',
                            'hex': region[back:i+1].hex()
                        })
                
                # CMP r/m32, imm32
                if byte0 == 0x81 and (byte1 & 0xF8) == 0xF8:
                    candidates.append({
                        'offset': start + i,
                        'value': val_le32,
                        'type': 'cmp_imm32',
                        'hex': region[back:i+4].hex()
                    })
                
                # MOV r32, imm32 (B8+r)
                if 0xB8 <= byte0 <= 0xBF:
                    candidates.append({
                        'offset': start + i,
                        'value': val_le32,
                        'type': 'mov_imm32',
                        'hex': region[back:i+4].hex()
                    })
    
    # 중복 제거
    seen = set()
    for c in candidates:
        key = (c['offset'], c['value'])
        if key not in seen:
            seen.add(key)
            print(f"  0x{c['offset']:08X}: value={c['value']} ({c['type']}) [{c['hex']}]")

find_nearby_constants(dll, usb_offset, "kCollageUsbInHeaderSize")
find_nearby_constants(dll, tcp_offset, "kCollageTcpHeaderSize")

# ─── 대안 방법: DLL의 .rdata 섹션에서 정적 상수 검색 ───
# PE 헤더에서 .rdata 섹션 찾기
pe_offset = struct.unpack_from('<I', dll, 0x3C)[0]
num_sections = struct.unpack_from('<H', dll, pe_offset + 6)[0]
opt_hdr_size = struct.unpack_from('<H', dll, pe_offset + 20)[0]
section_start = pe_offset + 24 + opt_hdr_size

print(f"\n## PE 섹션 정보")
for i in range(num_sections):
    sec_off = section_start + i * 40
    name = dll[sec_off:sec_off+8].rstrip(b'\x00').decode('ascii', errors='replace')
    vsize = struct.unpack_from('<I', dll, sec_off + 8)[0]
    vaddr = struct.unpack_from('<I', dll, sec_off + 12)[0]
    raw_size = struct.unpack_from('<I', dll, sec_off + 16)[0]
    raw_ptr = struct.unpack_from('<I', dll, sec_off + 20)[0]
    print(f"  {name:8s} VA=0x{vaddr:08X} VSize=0x{vsize:08X} Raw=0x{raw_ptr:08X} RawSize=0x{raw_size:08X}")

# ─── Protobuf 필드 번호 추출 (DataParameter 메시지 구조 추정) ───
print("\n## Protobuf DataParameter 필드 후보 (DLL 내 바이트 패턴)")
# Protobuf wire format: field_number << 3 | wire_type
# Varint (type 0), 64-bit (type 1), length-delimited (type 2), etc.
# DataParameterId 관련 패턴에서 필드 번호 추출

# Arturia.Collage.Protobuf.DataParameterId 문자열 근처 스캔
dpid_str = b'Arturia.Collage.Protobuf.DataParameterId'
pos = 0
while True:
    pos = dll.find(dpid_str, pos)
    if pos == -1:
        break
    # null terminator까지 읽기
    end = dll.find(b'\x00', pos)
    if end > 0:
        full = dll[pos:end].decode('ascii', errors='replace')
        print(f"  0x{pos:08X}: {full}")
    pos += 1

# ─── USB VID/PID 검색 ───
print("\n## Arturia USB VID/PID")
# 0x152E = Arturia VID (또는 0x1C75?)
vids = [0x152E, 0x1C75]
pids = [0x0602, 0x0601, 0x0603]
for vid in vids:
    packed = struct.pack('<H', vid)
    count = 0
    pos = 0
    while True:
        pos = dll.find(packed, pos)
        if pos == -1:
            break
        count += 1
        pos += 1
    if count > 0:
        print(f"  VID 0x{vid:04X}: {count} occurrences")

for pid in pids:
    packed = struct.pack('<H', pid)
    count = 0
    pos = 0
    while True:
        pos = dll.find(packed, pos)
        if pos == -1:
            break
        count += 1
        pos += 1
    if count > 0:
        print(f"  PID 0x{pid:04X}: {count} occurrences")

# ─── Collage USB 패킷 구조 관련 문자열 ───
print("\n## Collage 패킷/버퍼 관련 문자열")
packet_strs = set()
for m in re.finditer(rb'(?:header|payload|chunk|packet|buffer|frame)[^\x00]{0,60}', dll, re.IGNORECASE):
    s = m.group(0).decode('ascii', errors='replace').strip()
    if any(kw in s.lower() for kw in ['header size', 'payload size', 'payload max', 
                                       'max payload', 'packet max', 'chunk size',
                                       'header in packet', 'exceeds maximum']):
        packet_strs.add(s)

for s in sorted(packet_strs)[:20]:
    print(f"  {s}")

# ─── TUSBAUDIO DFU 함수 문자열 ───
print("\n## TUSBAUDIO DFU/펌웨어 함수 (DLL export 후보)")
tusb = set()
for m in re.finditer(rb'TUSBAUDIO_\w+', dll):
    tusb.add(m.group(0).decode('ascii'))
for t in sorted(tusb):
    print(f"  {t}")

print("\n완료")
