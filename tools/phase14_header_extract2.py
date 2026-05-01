#!/usr/bin/env python3
"""
Phase 14-1c: DLL 내 Protobuf FileDescriptorProto 바이너리에서 
kCollageUsbInHeaderSize, kCollageTcpHeaderSize 실제값 추출

Protobuf는 FileDescriptorProto를 바이너리로 DLL에 포함함.
각 메시지/필드의 옵션에 상수가 있을 수 있음.
또한 string literal로 "Header size in packet (" 근처에서 헤더 사이즈 문자열 포맷팅 코드 찾기.
"""

import struct, sys, re

DLL_PATH = sys.argv[1]

with open(DLL_PATH, "rb") as f:
    dll = f.read()

# ─── 1. "Header size in packet (" 문자열 근처에서 포맷 인자 찾기 ───
# 이 문자열은 오류 메시지로, 포맷 인자로 실제 헤더 크기값이 들어감
# 예: "Header size in packet (%d) exceeds maximum payload size(%d)"
# 이 문자열을 참조하는 LEA 명령어 근처에서 CMP 상수를 찾으면 됨

hdr_str = b'Header size in packet ('
pos = 0
while True:
    pos = dll.find(hdr_str, pos)
    if pos == -1:
        break
    end = dll.find(b'\x00', pos)
    full = dll[pos:end].decode('ascii', errors='replace')
    print(f"[0x{pos:08X}] {full}")
    pos += 1

# ─── 2. "cannot get header size" / "cannot get payload max size" 근처 ───
for pat in [b'cannot get header size', b'cannot get payload max size', 
            b'failed to get payload']:
    pos = 0
    while True:
        pos = dll.find(pat, pos)
        if pos == -1:
            break
        end = dll.find(b'\x00', pos)
        full = dll[pos:end].decode('ascii', errors='replace')
        print(f"[0x{pos:08X}] {full}")
        pos += 1

# ─── 3. x86-64 RIP-relative addressing으로 kCollageUsbInHeaderSize 참조 찾기 ───
# DLL의 .rdata에서 문자열 "kCollageUsbInHeaderSize"의 RVA를 계산
# PE ImageBase = 0x180000000 (typical for x86-64 DLL)
image_base = 0x180000000

usb_str = b'kCollageUsbInHeaderSize\x00'
usb_raw_off = dll.find(usb_str)
tcp_str = b'kCollageTcpHeaderSize\x00'
tcp_raw_off = dll.find(tcp_str)

# RVA = VA - ImageBase, VA = rdata_VA + (raw_offset - rdata_raw_ptr)
# .rdata VA=0x013D1000, Raw=0x013CFA00
rdata_va = 0x013D1000
rdata_raw = 0x013CFA00

usb_rva = rdata_va + (usb_raw_off - rdata_raw)
tcp_rva = rdata_va + (tcp_raw_off - rdata_raw)
usb_va = image_base + usb_rva
tcp_va = image_base + tcp_rva

print(f"\nkCollageUsbInHeaderSize VA=0x{usb_va:016X} RVA=0x{usb_rva:08X}")
print(f"kCollageTcpHeaderSize  VA=0x{tcp_va:016X} RVA=0x{tcp_rva:08X}")

# ─── 4. .text 섹션에서 이 주소를 참조하는 LEA/명령어 찾기 ───
# x86-64 LEA reg, [rip+disp32]: 48 8D 0D/05/15/1D/25/2D/35/3D disp32
# 또는 CMP/MOV reg, [rip+disp32] 등
# 우리는 헤더 크기 상수값을 찾는 게 목적이므로, 
# 문자열 참조 주변에서 정수 상수를 찾는 대신
# DLL의 data 영역에서 인라인 상수를 직접 검색

# Arturia Collage 라이브러리에서 헤더 사이즈는 보통 소수 정수
# 일반적인 USB 프로토콜 헤더: 4~16바이트
# TCP 프로토콜 헤더: 4~16바이트

# ─── 5. Protobuf FileDescriptorSet 바이너리에서 enum 정수 추출 ───
# Protobuf .proto 소스 파일에 정의된 상수는 FileDescriptorProto에 포함됨
# "DATA_PARAMETER_STATUS_UNKNOWN" 등의 enum value 근처에서 정수 매핑 추출

print("\n## Protobuf DataParameterStatus enum values")
# DLL에서 이 영역의 raw bytes를 읽어서 protobuf wire format 디코딩
# 0x01587275 근처의 FileDescriptorProto 바이너리

# 전체 FileDescriptorProto 영역 추출 (0x01580000~0x01590000)
fd_start = 0x01587000
fd_end = 0x01588000
fd_region = dll[fd_start:fd_end]

# Protobuf field decoder (simplified)
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

def decode_protobuf_fields(data, max_depth=3, indent=0):
    """Recursively decode protobuf wire format"""
    pos = 0
    fields = []
    while pos < len(data):
        tag, pos = decode_varint(data, pos)
        field_number = tag >> 3
        wire_type = tag & 0x07
        
        if field_number == 0 or wire_type > 5:
            break
            
        prefix = "  " * indent
        
        if wire_type == 0:  # Varint
            value, pos = decode_varint(data, pos)
            fields.append((field_number, wire_type, value))
        elif wire_type == 1:  # 64-bit
            value = struct.unpack_from('<Q', data, pos)[0]
            pos += 8
            fields.append((field_number, wire_type, value))
        elif wire_type == 2:  # Length-delimited
            length, pos = decode_varint(data, pos)
            value = data[pos:pos+length]
            pos += length
            # Try to decode as string
            try:
                s = value.decode('utf-8')
                if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in s):
                    fields.append((field_number, wire_type, s))
                else:
                    fields.append((field_number, wire_type, value))
            except:
                fields.append((field_number, wire_type, value))
        elif wire_type == 5:  # 32-bit
            value = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            fields.append((field_number, wire_type, value))
        else:
            break
    
    return fields

# DataParameterStatus enum 영역 찾기
dpstatus = b'DATA_PARAMETER_STATUS'
dp_pos = dll.find(dpstatus, fd_start)
if dp_pos > 0:
    # 이 영역의 protobuf 메시지 구조 디코딩
    # FileDescriptorProto의 enumvalue 필드(field 2)에 각 enum entry가 있음
    region = dll[dp_pos:dp_pos+512]
    fields = decode_protobuf_fields(region)
    print("  DataParameterStatus field entries:")
    for fn, wt, val in fields:
        if isinstance(val, str):
            print(f"    field {fn} (wire {wt}): \"{val}\"")
        elif isinstance(val, int):
            print(f"    field {fn} (wire {wt}): {val}")
        else:
            print(f"    field {fn} (wire {wt}): {len(val)} bytes")

# ─── 6. 더 넓은 영역에서 Protobuf descriptor 전체를 스캔 ───
# Protobuf FileDescriptorProto는 보통 field 4(name)에 proto 파일 이름,
# field 5(package)에 패키지명, field 6(message_type)에 메시지 정의를 가짐

# DLL 전체에서 FileDescriptorProto 시작 패턴 찾기
# field 4 (name), wire type 2 (length-delimited): tag = 0x22
# "collage.proto"를 field 4 값으로 가지는 proto descriptor 찾기
print("\n## Protobuf FileDescriptorProto (collage.proto)")
proto_name = b'collage.proto'
pos = 0
fd_protos = []
while True:
    pos = dll.find(proto_name, pos)
    if pos == -1:
        break
    # 이전 바이트에서 protobuf field tag 확인
    if pos > 0 and dll[pos-1] == 0x22:  # field 4, wire type 2
        fd_protos.append(pos - 1)
        print(f"  Found collage.proto descriptor @ 0x{pos-1:08X}")
    pos += 1

# ─── 7. CommUsb.cpp 근처에서 USB 헤더 관련 상수 문자열 검색 ───
print("\n## USB 헤더 크기 후보 문자열 (포맷 스트링)")
# USB 헤더 사이즈는 런타임에 계산되거나 하드코딩됨
# 포맷 스트링 "%d bytes" 또는 "size=%d" 패턴
for pat in [b'usb.*header.*size', b'header.*%d.*byte', b'size.*header',
            b'USB.*header', b'inPacketMaxSize', b'MaxSize',
            b'kCollageUsb', b'kCollageTcp']:
    for m in re.finditer(pat, dll, re.IGNORECASE):
        start = max(0, m.start() - 10)
        end = min(len(dll), m.end() + 60)
        null = dll.find(b'\x00', m.start())
        if null > m.start():
            s = dll[m.start():null].decode('ascii', errors='replace')
            if len(s) > 3 and len(s) < 100:
                print(f"  0x{m.start():08X}: {s}")

# ─── 8. DLL에서 "inPacketMaxSize" 문자열을 참조하는 코드에서 
#      근처 정수 상수(헤더 크기)를 찾기 위해 
#      .data 섹션에서 전역 변수로 저장된 상수 검색 ───
# Arturia 코드에서 kCollageUsbInHeaderSize는 보통 
# static const 또는 constexpr으로 컴파일 타임에 결정됨
# 헤더 구조 추정:
#   USB In Header: [msg_type(1)] [flags(1)] [sequence(2)] [payload_length(4)] = 8 bytes?
#   TCP Header:    [length(4)] [msg_type(1)] [flags(1)] [sequence(4)] = 10 bytes?
# 또는 더 간단하게:
#   USB In Header: [payload_length(4)] = 4 bytes
#   TCP Header:    [length(4)] = 4 bytes

# 일반적인 Arturia Collage USB 프로토콜 헤더 구조 (다른 기기 참고):
#   [magic(2)] [sequence(2)] [payload_length(4)] [msg_type(1)] = 9 bytes?
# 또는:
#   [sync(1)] [msg_type(1)] [sequence(2)] [payload_length(4)] = 8 bytes

print("\n## 헤더 크기 추정 (Collage 프로토콜 분석 기반)")
print("  참고: Arturia Collage는 Protobuf 기반 프로토콜")
print("  USB 전송 = [CollageHeader][ProtobufPayload]")
print("  TCP 전송 = [Length-Prefix][CollageHeader][ProtobufPayload]")
print("  ")
print("  USB In Header 후보:")
print("    - 4 bytes (payload length only)")
print("    - 8 bytes (type + seq + length)")  
print("    - 12 bytes (type + seq + length + checksum)")
print("  TCP Header 후보:")
print("    - 4 bytes (length prefix only)")
print("    - 8 bytes (length + type)")
print("  ")
print("  USB In > TCP 인 이유: USB에는 패킷 동기화/시퀀싱이 추가됨")

# ─── 9. 최종 접근: DLL의 초기화 코드에서 전역 변수에 쓰여지는 상수값 검색 ───
# kCollageUsbInHeaderSize는 #define 또는 constexpr로 정의됨
# 컴파일러 최적화로 인라인된 경우, 여러 곳에 동일한 imm 값이 나타남
# 가장 흔하게 나타나는 패턴: CMP reg, 8 또는 CMP reg, 12 (USB header size)

# .text 섹션에서 가장 빈번하게 비교되는 작은 정수 (4~32) 카운트
print("\n## .text에서 자주 비교되는 상수값 (상위 20)")
text_start = 0x00000400
text_size = 0x01332600
text_end = text_start + text_size

const_counts = {}
for i in range(text_start, text_end - 2):
    # CMP r/m32, imm8: 83 /7 ib
    if dll[i] == 0x83 and (dll[i+1] & 0xF8) == 0xF8:
        imm = struct.unpack_from('<b', dll, i+2)[0]
        if 4 <= imm <= 64:
            const_counts[imm] = const_counts.get(imm, 0) + 1

# 정렬해서 상위 출력
for val, count in sorted(const_counts.items(), key=lambda x: -x[1])[:20]:
    print(f"  CMP imm8 = {val:3d}: {count:6d} occurrences")

print("\n완료")
