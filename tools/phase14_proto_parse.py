#!/usr/bin/env python3
"""
Phase 14-1e: DLL 내 Protobuf FileDescriptorSet 바이너리 직접 파싱
- DataParameterStatus enum 값 추출
- DataParameter 필드 정의 추출
- 전체 proto 메시지 구조 역추적
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

def decode_length_delimited(data, pos):
    length, pos = decode_varint(data, pos)
    return data[pos:pos+length], pos + length

def decode_protobuf(data, indent=0, max_depth=6):
    """Decode protobuf wire format recursively"""
    if indent > max_depth:
        return
    prefix = "  " * indent
    pos = 0
    while pos < len(data):
        try:
            tag, new_pos = decode_varint(data, pos)
        except:
            break
        field_number = tag >> 3
        wire_type = tag & 0x07
        
        if field_number == 0 or wire_type > 5:
            break
        
        if wire_type == 0:  # Varint
            value, pos = decode_varint(data, new_pos)
            if field_number in [3, 4, 5]:  # enum type, label, number
                type_names = {1: 'TYPE_DOUBLE', 2: 'TYPE_FLOAT', 3: 'TYPE_INT64',
                             4: 'TYPE_UINT64', 5: 'TYPE_INT32', 8: 'TYPE_BOOL',
                             9: 'TYPE_STRING', 11: 'TYPE_MESSAGE'}
                if field_number == 3 and value in type_names:
                    print(f"{prefix}  field {field_number}: {type_names.get(value, value)}")
                else:
                    print(f"{prefix}  field {field_number}: {value}")
            elif field_number == 1:  # name
                pass  # will be string
            else:
                print(f"{prefix}  field {field_number}: {value}")
        elif wire_type == 1:  # 64-bit
            value = struct.unpack_from('<Q', data, new_pos)[0]
            pos = new_pos + 8
            print(f"{prefix}  field {field_number}: {value} (64-bit)")
        elif wire_type == 2:  # Length-delimited
            value, pos = decode_length_delimited(data, new_pos)
            try:
                s = value.decode('utf-8')
                if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in s) and len(s) > 0:
                    print(f"{prefix}  field {field_number}: \"{s}\"")
                    # If this looks like a nested protobuf message descriptor, try to decode
                    if field_number in [6, 7] and len(value) > 10:
                        print(f"{prefix}    [nested protobuf message]")
                else:
                    # Try as nested protobuf
                    if len(value) > 5:
                        try:
                            decode_protobuf(value, indent + 2)
                        except:
                            print(f"{prefix}  field {field_number}: {len(value)} bytes")
                    else:
                        print(f"{prefix}  field {field_number}: {len(value)} bytes")
            except:
                if len(value) > 5:
                    try:
                        decode_protobuf(value, indent + 2)
                    except:
                        print(f"{prefix}  field {field_number}: {len(value)} bytes")
                else:
                    print(f"{prefix}  field {field_number}: {value.hex() if len(value) < 20 else f'{len(value)} bytes'}")
        elif wire_type == 5:  # 32-bit
            value = struct.unpack_from('<I', data, new_pos)[0]
            pos = new_pos + 4
            print(f"{prefix}  field {field_number}: {value} (32-bit)")
        else:
            break

# Protobuf FileDescriptorSet을 찾기 위해 "Arturia.Collage.Protobuf" 문자열 근처 스캔
# FileDescriptorProto는 field 5(package)에 "Arturia.Collage.Protobuf"를 가짐
# field 5, wire type 2: tag = (5 << 3) | 2 = 0x2A

print("## Protobuf FileDescriptorProto 구조 역추적\n")

# DLL의 .rdata 섹션에서 Arturia.Collage.Protobuf 패키지명을 가진 
# FileDescriptorProto를 찾기
pkg = b'Arturia.Collage.Protobuf'
pos = 0
fds_offsets = []
while True:
    pos = dll.find(pkg, pos)
    if pos == -1:
        break
    # 앞에 0x2A (field 5, wire type 2) 태그가 있는지 확인
    if pos > 2 and dll[pos-1] == len(pkg) and dll[pos-2] == 0x2A:
        fds_offsets.append(pos - 2)
    pos += 1

print(f"FileDescriptorProto 후보 {len(fds_offsets)}개 발견")
for off in fds_offsets[:3]:
    print(f"  @ 0x{off:08X}")

# 가장 첫 번째 FDS에서 패키지명 바로 앞의 전체 FileDescriptorProto 추출 시도
if fds_offsets:
    # FileDescriptorProto는 field 1(name), 2(dependency), 3(public_dependency),
    # 4(weak_dependency), 5(package), 6(message_type), 7(enum_type),
    # 8(service), 9(extension) 등을 가짐
    # 우리가 찾은 위치는 field 5(package)의 시작점
    # field 5 앞에 field 1~4가 있을 수 있으므로 앞쪽으로 스캔
    
    off = fds_offsets[0]
    
    # 앞으로 스캔하여 FileDescriptorProto의 시작점 찾기
    # FileDescriptorProto는 field 1(name)로 시작하는 것이 일반적
    # field 1, wire type 2: tag = 0x0A
    # 또는 field 6(message_type), field 7(enum_type) 등이 먼저 올 수 있음
    
    # field 5가 시작하는 위치이므로, 앞쪽에서 field 1~4를 스캔
    scan_start = max(0, off - 500)
    scan_region = dll[scan_start:off]
    
    # 역방향으로 protobuf fields 파싱
    # 각 field는 [tag_varint][value] 구조
    # 가장 간단한 방법: 앞에서부터 파싱해서 field 5까지 도달하는지 확인
    
    best_start = off
    for test_off in range(len(scan_region)):
        test_pos = test_off
        try:
            while test_pos < len(scan_region):
                tag, new_pos = decode_varint(scan_region, test_pos)
                fn = tag >> 3
                wt = tag & 0x07
                if fn == 0 or fn > 20:
                    break
                if wt == 0:
                    _, test_pos = decode_varint(scan_region, new_pos)
                elif wt == 2:
                    _, test_pos = decode_length_delimited(scan_region, new_pos)
                elif wt == 1:
                    test_pos = new_pos + 8
                elif wt == 5:
                    test_pos = new_pos + 4
                else:
                    break
                
                # field 5에 도달하면 성공
                if fn == 5:
                    val, _ = decode_length_delimited(scan_region, new_pos)
                    if val == pkg:
                        best_start = scan_start + test_off
                        break
            if best_start != off:
                break
        except:
            continue
    
    print(f"\nFileDescriptorProto 시작점 추정: 0x{best_start:08X}")
    
    # 전체 FileDescriptorProto 읽기 (최대 200KB)
    fd_region = dll[best_start:best_start + 200000]
    
    # Protobuf 파싱
    print("\n--- FileDescriptorProto 내용 ---")
    pos = 0
    while pos < min(len(fd_region), 50000):
        try:
            tag, new_pos = decode_varint(fd_region, pos)
            fn = tag >> 3
            wt = tag & 0x07
            if fn == 0 or fn > 20:
                break
            if wt == 0:
                val, pos = decode_varint(fd_region, new_pos)
                print(f"  field {fn} (varint): {val}")
            elif wt == 2:
                val, pos = decode_length_delimited(fd_region, new_pos)
                try:
                    s = val.decode('utf-8')
                    if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in s):
                        if len(s) > 200:
                            print(f"  field {fn} (string): \"{s[:100]}...\" ({len(s)} chars)")
                        else:
                            print(f"  field {fn} (string): \"{s}\"")
                    else:
                        # Nested protobuf message
                        if fn in [6, 7]:  # message_type, enum_type
                            print(f"  field {fn} (nested message, {len(val)} bytes):")
                            # Parse as DescriptorProto (field 6) or EnumDescriptorProto (field 7)
                            parse_descriptor(val, fn == 7)
                        else:
                            print(f"  field {fn} (bytes): {len(val)} bytes")
                except:
                    print(f"  field {fn} (bytes): {len(val)} bytes")
            elif wt == 1:
                pos = new_pos + 8
            elif wt == 5:
                pos = new_pos + 4
            else:
                break
        except:
            break

def parse_descriptor(data, is_enum=False):
    """Parse DescriptorProto or EnumDescriptorProto"""
    prefix = "    "
    pos = 0
    name = ""
    fields = []
    enum_values = []
    
    while pos < len(data):
        try:
            tag, new_pos = decode_varint(data, pos)
            fn = tag >> 3
            wt = tag & 0x07
            if fn == 0 or fn > 20:
                break
            if wt == 0:
                val, pos = decode_varint(data, new_pos)
                if fn == 3 and is_enum:  # enum value number
                    enum_values.append(val)
            elif wt == 2:
                val, pos = decode_length_delimited(data, new_pos)
                try:
                    s = val.decode('utf-8')
                    if fn == 1:  # name
                        name = s
                    elif fn == 2 and is_enum:  # enum value name
                        enum_values.append(s)
                    elif fn == 2 and not is_enum:  # field
                        # Parse FieldDescriptorProto
                        parse_field(val, fields)
                except:
                    pass
            elif wt == 1:
                pos = new_pos + 8
            elif wt == 5:
                pos = new_pos + 4
            else:
                break
        except:
            break
    
    if name:
        if is_enum:
            print(f"{prefix}  enum {name}")
            # enum_values에 이름과 번호가 교대로 들어감
            i = 0
            while i < len(enum_values):
                if i + 1 < len(enum_values):
                    vname = enum_values[i]
                    vnum = enum_values[i+1]
                    if isinstance(vname, str) and isinstance(vnum, int):
                        print(f"{prefix}    {vname} = {vnum}")
                    i += 2
                else:
                    i += 1
        else:
            print(f"{prefix}  message {name}")
            for f in fields:
                if len(f) >= 3:
                    type_name = f[0]
                    field_name = f[1]
                    field_num = f[2]
                    print(f"{prefix}    {type_name} {field_name} = {field_num}")

def parse_field(data, fields):
    """Parse FieldDescriptorProto"""
    pos = 0
    name = ""
    number = 0
    type_name = ""
    
    while pos < len(data):
        try:
            tag, new_pos = decode_varint(data, pos)
            fn = tag >> 3
            wt = tag & 0x07
            if fn == 0 or fn > 20:
                break
            if wt == 0:
                val, pos = decode_varint(data, new_pos)
                if fn == 3:  # number
                    number = val
                elif fn == 5:  # type (1=double, 2=float, 5=int32, 8=bool, 9=string, 11=message)
                    type_map = {1:'double', 2:'float', 3:'int64', 4:'uint64', 5:'int32',
                               8:'bool', 9:'string', 11:'message', 13:'uint32', 14:'enum'}
                    type_name = type_map.get(val, f'type{val}')
            elif wt == 2:
                val, pos = decode_length_delimited(data, new_pos)
                try:
                    s = val.decode('utf-8')
                    if fn == 1:  # name
                        name = s
                    elif fn == 6:  # type_name
                        type_name = s
                except:
                    pass
            elif wt == 1:
                pos = new_pos + 8
            elif wt == 5:
                pos = new_pos + 4
            else:
                break
        except:
            break
    
    if name and number:
        fields.append((type_name, name, number))

print("\n완료")
