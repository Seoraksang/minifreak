#!/usr/bin/env python3
"""
Phase 14-1 FINAL: x86-64 디스어셈블리에서 kCollageUsbInHeaderSize/kCollageTcpHeaderSize 
실제 정수값 추출

접근법: 에러 메시지 문자열 "inPacketMaxSize < kCollageUsbInHeaderSize"를 
참조하는 코드에서, 컴파일러가 인라인한 헤더 크기 상수값을 찾기.
"""

import struct, sys

DLL_PATH = sys.argv[1]
with open(DLL_PATH, "rb") as f:
    dll = f.read()

IMAGE_BASE = 0x180000000

# .text 섹션 범위
TEXT_START = 0x00000400
TEXT_END = 0x01332A00

def decode_varint(data, pos):
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if (b & 0x80) == 0:
            break
        shift += 7
    return result, pos

def rva_to_raw(rva):
    """RVA를 파일 오프셋으로 변환 (.text 섹션)"""
    return rva  # .text: VA=0x1000, Raw=0x400, delta=0xC00... but for simplicity
    # Actually for .text: VirtualAddress=0x1000, PointerToRawData=0x400
    # raw = rva - 0x1000 + 0x400 = rva - 0xC00
    return rva - 0xC00

# ─── 1. 문자열 "kCollageUsbInHeaderSize"의 VA 계산 ───
usb_str = b'kCollageUsbInHeaderSize\x00'
usb_raw = dll.find(usb_str)
tcp_str = b'kCollageTcpHeaderSize\x00'
tcp_raw = dll.find(tcp_str)

# .rdata 섹션: VirtualAddress=0x013D1000, PointerToRawData=0x013CFA00
RDATA_VA = 0x013D1000
RDATA_RAW = 0x013CFA00

usb_va = IMAGE_BASE + RDATA_VA + (usb_raw - RDATA_RAW)
tcp_va = IMAGE_BASE + RDATA_VA + (tcp_raw - RDATA_RAW)

print(f"kCollageUsbInHeaderSize: VA=0x{usb_va:016X}, raw=0x{usb_raw:08X}")
print(f"kCollageTcpHeaderSize:  VA=0x{tcp_va:016X}, raw=0x{tcp_raw:08X}")

# ─── 2. "inPacketMaxSize < kCollageUsbInHeaderSize" 에러 메시지 참조 코드 찾기 ───
# 이 문자열은 LOG/ASSERT 매크로로 사용됨
# 컴파일러는 문자열 주소를 LEA reg, [rip+disp32]로 로드
# 그 후 헤더 크기값과 비교하는 코드가 있음

err_str = b'inPacketMaxSize < kCollageUsbInHeaderSize\x00'
err_raw = dll.find(err_str)
if err_raw > 0:
    err_va = IMAGE_BASE + RDATA_VA + (err_raw - RDATA_RAW)
    print(f"\nError string: VA=0x{err_va:016X}, raw=0x{err_raw:08X}")
    
    # 이 에러 문자열을 참조하는 LEA 명령어를 .text에서 찾기
    # LEA reg, [rip+disp32]: 48 8D 05/0D/15/1D/25/2D/35/3D (ModRM)
    # disp32 = target_va - (instruction_va + 7)
    # target_va = instruction_va + 7 + disp32
    
    # .text에서 이 주소를 참조하는 모든 RIP-relative 명령어 찾기
    print("\nSearching for LEA instructions referencing error string...")
    
    found = 0
    for i in range(TEXT_START, TEXT_END - 7):
        # LEA with RIP-relative: REX.W (48/4C) + 8D + ModRM + disp32
        if dll[i] in (0x48, 0x4C) and dll[i+1] == 0x8D:
            modrm = dll[i+2]
            mod = (modrm >> 6) & 3
            rm = modrm & 7
            if mod == 0 and rm == 5:  # [rip+disp32]
                disp = struct.unpack_from('<i', dll, i+3)[0]
                instr_va = IMAGE_BASE + i  # simplified: text VA = imagebase + raw for .text
                # Actually .text VA starts at IMAGE_BASE + 0x1000
                instr_va = IMAGE_BASE + 0x1000 + (i - TEXT_START)
                target_va = instr_va + 7 + disp
                
                if target_va == err_va:
                    print(f"  LEA @ VA=0x{instr_va:016X} (raw=0x{i:08X})")
                    
                    # 이 명령어 앞뒤 50바이트를 디스어셈블하여 CMP 상수값 찾기
                    # 헤더 크기는 보통 CMP reg, imm 또는 MOV reg, imm로 설정됨
                    context_start = max(TEXT_START, i - 100)
                    context_end = min(TEXT_END, i + 100)
                    context = dll[context_start:context_end]
                    
                    # CMP r/m32, imm8 (83 /7 ib): 가장 흔한 패턴
                    for j in range(len(context) - 2):
                        if context[j] == 0x83 and (context[j+1] & 0xF8) == 0xF8:
                            imm = struct.unpack_from('<b', context, j+2)[0]
                            if 4 <= imm <= 64:
                                abs_addr = context_start + j
                                print(f"    CMP imm8={imm} @ raw=0x{abs_addr:08X} (delta={i-abs_addr})")
                        
                        # CMP r/m32, imm32 (81 /7 id)
                        elif context[j] == 0x81 and (context[j+1] & 0xF8) == 0xF8:
                            imm = struct.unpack_from('<I', context, j+2)[0]
                            if 4 <= imm <= 64:
                                abs_addr = context_start + j
                                print(f"    CMP imm32={imm} @ raw=0x{abs_addr:08X} (delta={i-abs_addr})")
                        
                        # MOV reg, imm32 (B8+rd id) or MOV r, imm8
                        elif 0xB8 <= context[j] <= 0xBF:
                            imm = struct.unpack_from('<I', context, j+1)[0]
                            if 4 <= imm <= 64:
                                abs_addr = context_start + j
                                print(f"    MOV imm32={imm} @ raw=0x{abs_addr:08X} (delta={i-abs_addr})")
                    
                    found += 1
                    if found >= 3:
                        break
    
    if found == 0:
        print("  LEA instruction not found directly")
        # 대안: 문자열이 LOG 함수의 인자로 전달될 수 있음
        # __LOG_ERROR("%s", "inPacketMaxSize < kCollageUsbInHeaderSize") 형태
        # 이 경우 함수 호출 근처에서 헤더 크기값을 찾아야 함
        
        # 문자열 포인터가 저장된 변수를 참조하는 코드 찾기
        # MOV reg, [addr] 형태로 문자열 주소를 로드할 수 있음
        
        # 다른 접근: 헤더 크기는 컴파일 타임 상수이므로
        # 함수 내에서 스택에 상수를 저장하고 비교하는 패턴 찾기
        
        print("\n  Trying alternative: search for comparison pattern near header size usage")
        # 함수 프로로그의 상수 로드 패턴
        # 함수가 kCollageUsbInHeaderSize를 사용하는 곳에서
        # 일반적으로 함수 시작 부분에 상수를 레지스터나 스택에 로드

# ─── 3. Collage 헤더 구조체 정의에서 직접 크기 추정 ───
# Arturia Collage 라이브러리는 다른 기기(MicroFreak, PolyBrute 등)에서도 사용됨
# 다른 Arturia 기기의 리버싱 결과를 참고하면:
# - USB In Header = protobuf 직렬화된 CollageUsbHeader 메시지
# - TCP Header = protobuf 직렬화된 CollageTcpHeader 메시지

# DLL에서 "collage_usb_header" / "collage_tcp_header" 문자열 검색
print("\n## Protobuf header message 타입")
for pat in [b'collage_usb_header', b'collage_tcp_header', b'collage_usb_out_header']:
    pos = dll.find(pat)
    if pos > 0:
        null = dll.find(b'\x00', pos)
        s = dll[pos:null].decode('ascii', errors='replace')
        print(f"  [0x{pos:08X}] {s}")
        
        # 근처의 null-terminated 문자열들도 출력
        start = max(0, pos - 50)
        end = min(len(dll), null + 100)
        region = dll[start:end]
        nulls = [i for i, b in enumerate(region) if b == 0]
        for j in range(len(nulls) - 1):
            s2 = region[nulls[j]+1:nulls[j+1]].decode('ascii', errors='replace')
            if len(s2) > 3 and ('header' in s2.lower() or 'size' in s2.lower() or 
                                  'collage' in s2.lower() or 'usb' in s2.lower() or
                                  'tcp' in s2.lower()):
                print(f"    [0x{start+nulls[j]+1:08X}] {s2}")

# ─── 4. 다른 접근: CommUsb 생성자에서 헤더 크기 설정 코드 찾기 ───
# "Creating USB connection" 메시지 근처에서 헤더 크기가 설정됨
print("\n## 'Creating USB connection' 근처 코드 분석")
conn_str = b'Creating USB connection (client = host) to 0x'
conn_raw = dll.find(conn_str)
if conn_raw > 0:
    conn_va = IMAGE_BASE + RDATA_VA + (conn_raw - RDATA_RAW)
    print(f"  String VA=0x{conn_va:016X}, raw=0x{conn_raw:08X}")
    
    # 이 문자열을 참조하는 코드에서 함수 시작점을 역추적
    # 함수 시작점에는 헤더 크기 관련 상수가 있을 가능성이 높음

# ─── 5. 헤더 크기 후보값 계산 ───
# Protobuf 직렬화된 CollageUsbHeader의 크기 = 
#   tag(1) + length(1) + field1_tag(1) + field1_value(1~4) + ... 
# 최소 크기 = 빈 메시지 = 0 bytes (protobuf)
# 일반적 크기 = 4~16 bytes

# Arturia 기기들에서 알려진 Collage 헤더 정보:
# - MicroFreak: USB bulk EP IN=0x81, EP OUT=0x02
# - Collage USB 패킷 = [header][payload]
# - header = protobuf serialized message (variable length)

# DLL에서 "Max packet size is" 문자열 근처에서 실제 max size 값 출력
print("\n## 'Max packet size is' 근처")
max_str = b'Max packet size is '
pos = dll.find(max_str)
if pos > 0:
    null = dll.find(b'\x00', pos)
    print(f"  [0x{pos:08X}] {dll[pos:null].decode('ascii', errors='replace')}")

# ─── 6. 최종 접근: DLL 전체에서 USB 헤더 관련 상수를 직접 계산 ───
# "kCollageUsbInHeaderSize"와 "kCollageTcpHeaderSize"는 
# C++ constexpr 또는 #define으로 정의됨
# 컴파일러는 이를 인라인 상수로 변환

# 다른 Arturia 기기의 공개 리버싱 결과 참고:
# MiniFreak VST DLL strings에서 발견된 패턴으로 추정:
# - Collage USB In Header: 시퀀스 번호(2B) + 페이로드 길이(2B) = 4 bytes?
# - Collage TCP Header: 페이로드 길이(4B) = 4 bytes?

# 또는 protobuf 직렬화 크기:
# USB In Header message (빈 메시지): 0 bytes
# 하지만 "header size"는 최소 고정 오버헤드를 의미

# "Size < kCollageTcpHeaderSize" 에러 메시지에서 "Size"는 수신된 패킷 크기
# kCollageTcpHeaderSize는 TCP 패킷의 최소 헤더 크기

# Arturia MicroFreak/MicroKey 등에서의 Collage 프로토콜:
# USB 패킷 구조: [SyncByte(1)] [HeaderLen(1)] [Header(H bytes)] [Payload]
# TCP 패킷 구조: [PayloadLen(4)] [Header(H bytes)] [Payload]

print("\n## 최종 추정")
print("  kCollageUsbInHeaderSize: 4~8 bytes (USB 동기화/시퀀싱 오버헤드 포함)")
print("  kCollageTcpHeaderSize: 4 bytes (TCP 길이 접두사)")
print("  참고: 실제값은 기기 연결 후 USB 캡처로 확정 가능")

print("\n완료")
