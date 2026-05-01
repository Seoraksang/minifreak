#!/usr/bin/env python3
"""
Phase 14-1f: Protobuf FileDescriptorProto 영역 직접 스캔
DLL에 내장된 protobuf descriptor pool에서 enum 정의와 상수 추출
"""

import struct, sys, re

DLL_PATH = sys.argv[1]
with open(DLL_PATH, "rb") as f:
    dll = f.read()

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

def decode_ld(data, pos):
    length, pos = decode_varint(data, pos)
    return data[pos:pos+length], pos + length

# Protobuf FileDescriptorProto 바이너리 영역을 찾기 위해
# "collage_message_data_parameter.proto" 문자열을 포함하는 영역 스캔
# FileDescriptorProto field 2 (dependency)에 .proto 파일 이름이 들어감

proto_names = [
    b'collage_message_data_parameter.proto',
    b'collage_message_control_system.proto',
    b'collage.proto',
    b'collage_message_data.proto',
]

print("## Protobuf descriptor 영역 스캔\n")

for pname in proto_names:
    pos = 0
    while True:
        pos = dll.find(pname, pos)
        if pos == -1:
            break
        # 앞쪽에서 length prefix 바이트 찾기
        plen = len(pname)
        for back in range(1, 6):
            if pos - back >= 0:
                check_len, _ = decode_varint(dll, pos - back)
                if check_len == plen:
                    # 이전 바이트가 field 2 (dependency), wire type 2: tag = 0x12
                    if pos - back - 1 >= 0 and dll[pos - back - 1] == 0x12:
                        print(f"  [{pname.decode()[:30]}...] field 2 dependency @ 0x{pos-back-1:08X}")
        pos += 1

# 다른 방법: DLL에서 "DataParameterStatus" enum 정의 영역을 직접 스캔
# Protobuf descriptor에서 enum value는 field 2 (enumvalue)에 저장됨
# EnumValueDescriptorProto = { name (field 1), number (field 3) }
# 전체 EnumDescriptorProto = { name (field 1), value (field 2) }

# DataParameterStatus의 enum value 후보
# DLL에서 이미 "DATA_PARAMETER_STATUS_UNKNOWN" 문자열을 확인했음
# 이 문자열이 포함된 protobuf descriptor 바이너리를 찾기

print("\n## DataParameterStatus enum 추출")
dpstatus = b'DATA_PARAMETER_STATUS_UNKNOWN'
pos = dll.find(dpstatus)
if pos > 0:
    # 이 문자열이 field 1 (name)로 들어간 EnumValueDescriptorProto의 시작점을 찾기
    # field 1, wire type 2: tag = 0x0A, length = len(dpstatus) = 30
    # 앞에 0x0A 0x1E 가 있어야 함 (0x1E = 30)
    if dll[pos-2] == 0x0A and dll[pos-1] == len(dpstatus):
        ev_start = pos - 2
        print(f"  EnumValueDescriptorProto start @ 0x{ev_start:08X}")
        
        # field 3 (number)도 읽기: tag = 0x18, varint
        after_name = pos + len(dpstatus)
        if after_name < len(dll) and dll[after_name] == 0x18:
            val, _ = decode_varint(dll, after_name + 1)
            print(f"    DATA_PARAMETER_STATUS_UNKNOWN = {val}")
        
        # 이 EnumValueDescriptorProto의 앞쪽에 더 많은 enum value가 있을 수 있음
        # 앞으로 스캔하여 EnumDescriptorProto 전체를 찾기
        # EnumDescriptorProto field 2 (value)의 tag = 0x12
        # 각 value는 length-delimited EnumValueDescriptorProto
        
        # 뒤쪽으로도 스캔하여 다른 enum value 찾기
        scan_pos = after_name + 5  # UNKNOWN 다음
        for _ in range(20):
            if scan_pos >= len(dll):
                break
            if dll[scan_pos] == 0x12:  # field 2, wire type 2
                ev_data, scan_pos = decode_ld(dll, scan_pos + 1)
                # Parse EnumValueDescriptorProto
                ev_pos = 0
                ev_name = ""
                ev_num = 0
                while ev_pos < len(ev_data):
                    try:
                        tag, new_pos = decode_varint(ev_data, ev_pos)
                        fn = tag >> 3
                        wt = tag & 0x07
                        if wt == 0:
                            val, ev_pos = decode_varint(ev_data, new_pos)
                            if fn == 3:
                                ev_num = val
                        elif wt == 2:
                            val, ev_pos = decode_ld(ev_data, new_pos)
                            if fn == 1:
                                ev_name = val.decode('utf-8', errors='replace')
                        elif wt == 1:
                            ev_pos = new_pos + 8
                        elif wt == 5:
                            ev_pos = new_pos + 4
                        else:
                            break
                    except:
                        break
                if ev_name and ev_num != 0:
                    print(f"    {ev_name} = {ev_num}")
                elif not ev_name:
                    break
            elif dll[scan_pos] == 0x0A:  # field 1 (name) of EnumDescriptorProto
                name_data, scan_pos = decode_ld(dll, scan_pos + 1)
                name = name_data.decode('utf-8', errors='replace')
                print(f"\n  enum {name}")
            elif dll[scan_pos] == 0x22:  # field 4 (options) — skip
                _, scan_pos = decode_ld(dll, scan_pos + 1)
            elif dll[scan_pos] == 0x00:  # end of message
                break
            else:
                scan_pos += 1

# 같은 방식으로 다른 enum도 추출
print("\n## 모든 Protobuf enum 추출")
# EnumDescriptorProto의 field 1 (name)은 보통 대문자 + _ 로 구성된 이름
# "TYPE_", "STATUS_", "RESULT_" 등의 패턴

# DLL에서 protobuf descriptor가 모여있는 영역을 찾기 위해
# 여러 proto 관련 문자열이 밀집된 영역 스캔
print("\n## Protobuf descriptor 밀집 영역 탐색")

# "Arturia.Collage.Protobuf" 패키지명 근처
pkg = b'Arturia.Collage.Protobuf'
pos = 0
regions = []
while True:
    pos = dll.find(pkg, pos)
    if pos == -1:
        break
    regions.append(pos)
    pos += 1

print(f"  'Arturia.Collage.Protobuf' 출현 {len(regions)}회")
if regions:
    # 가장 밀집된 영역 찾기
    clusters = []
    cluster_start = regions[0]
    for i in range(1, len(regions)):
        if regions[i] - regions[i-1] > 10000:
            clusters.append((cluster_start, regions[i-1]))
            cluster_start = regions[i]
    clusters.append((cluster_start, regions[-1]))
    
    for start, end in clusters:
        span = end - start
        if span > 1000:
            print(f"  Cluster: 0x{start:08X} ~ 0x{end:08X} ({span:,} bytes, {sum(1 for r in regions if start <= r <= end)} refs)")

# 가장 큰 클러스터에서 protobuf descriptor 파싱
if regions:
    biggest_cluster = max(clusters, key=lambda x: x[1] - x[0])
    cs, ce = biggest_cluster
    print(f"\n  가장 큰 클러스터: 0x{cs:08X} ~ 0x{ce:08X} ({ce-cs:,} bytes)")
    
    # 이 영역에서 null-terminated 문자열만 추출
    region = dll[cs:ce+1000]
    proto_strings = []
    pos = 0
    while pos < len(region):
        null = region.find(b'\x00', pos)
        if null == -1:
            break
        s = region[pos:null].decode('ascii', errors='replace')
        if len(s) > 3 and ('Collage' in s or 'protobuf' in s.lower() or 
                           'proto' in s.lower() or s.isupper() and '_' in s):
            proto_strings.append((cs + pos, s))
        pos = null + 1
    
    for off, s in proto_strings[:50]:
        if len(s) < 100:
            print(f"    0x{off:08X}: {s}")

print("\n완료")
