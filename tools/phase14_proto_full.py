#!/usr/bin/env python3
"""
Phase 14-1g: Protobuf FileDescriptorSet 영역(0x01583978~0x01588566) 정밀 파싱
enum 정의, 메시지 필드 번호, 패키지 구조 완전 추출
"""

import struct, sys

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

def try_parse_string(data):
    try:
        s = data.decode('utf-8')
        if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in s):
            return s
    except:
        pass
    return None

def parse_protobuf_fields(data):
    """Parse protobuf wire format, return list of (field_number, wire_type, value)"""
    fields = []
    pos = 0
    while pos < len(data):
        try:
            tag, new_pos = decode_varint(data, pos)
            fn = tag >> 3
            wt = tag & 0x07
            if fn == 0 or fn > 30:
                break
            if wt == 0:
                val, pos = decode_varint(data, new_pos)
                fields.append((fn, wt, val))
            elif wt == 1:
                val = struct.unpack_from('<Q', data, new_pos)[0]
                pos = new_pos + 8
                fields.append((fn, wt, val))
            elif wt == 2:
                val, pos = decode_ld(data, new_pos)
                fields.append((fn, wt, val))
            elif wt == 5:
                val = struct.unpack_from('<I', data, new_pos)[0]
                pos = new_pos + 4
                fields.append((fn, wt, val))
            else:
                break
        except:
            break
    return fields

def extract_enum(data, name=""):
    """Extract enum values from EnumDescriptorProto binary"""
    fields = parse_protobuf_fields(data)
    enum_name = name
    values = []
    
    for fn, wt, val in fields:
        if fn == 1 and wt == 2:  # name
            s = try_parse_string(val)
            if s:
                enum_name = s
        elif fn == 2 and wt == 2:  # enumvalue (repeated EnumValueDescriptorProto)
            ev_fields = parse_protobuf_fields(val)
            ev_name = ""
            ev_num = 0
            for efn, ewt, eval_ in ev_fields:
                if efn == 1 and ewt == 2:
                    s = try_parse_string(eval_)
                    if s:
                        ev_name = s
                elif efn == 3 and ewt == 0:
                    ev_num = eval_
            if ev_name:
                values.append((ev_name, ev_num))
    
    return enum_name, values

def extract_message(data, name=""):
    """Extract message fields from DescriptorProto binary"""
    fields = parse_protobuf_fields(data)
    msg_name = name
    msg_fields = []
    nested_enums = []
    nested_messages = []
    
    for fn, wt, val in fields:
        if fn == 1 and wt == 2:  # name
            s = try_parse_string(val)
            if s:
                msg_name = s
        elif fn == 2 and wt == 2:  # field (repeated FieldDescriptorProto)
            f_fields = parse_protobuf_fields(val)
            f_name = ""
            f_number = 0
            f_type = ""
            f_label = ""
            f_type_name = ""
            
            type_map = {1:'double', 2:'float', 3:'int64', 4:'uint64', 5:'int32',
                       8:'bool', 9:'string', 11:'message', 13:'uint32', 14:'enum'}
            label_map = {1:'optional', 2:'required', 3:'repeated'}
            
            for ffn, fwt, fval in f_fields:
                if ffn == 1 and fwt == 2:
                    s = try_parse_string(fval)
                    if s:
                        f_name = s
                elif ffn == 3 and fwt == 0:
                    f_number = fval
                elif ffn == 4 and fwt == 0:
                    f_type = type_map.get(fval, f'type_{fval}')
                elif ffn == 5 and fwt == 0:
                    f_label = label_map.get(fval, f'label_{fval}')
                elif ffn == 6 and fwt == 2:
                    s = try_parse_string(fval)
                    if s:
                        f_type_name = s
            
            actual_type = f_type_name if f_type_name else f_type
            if f_name and f_number:
                msg_fields.append((f_label, actual_type, f_name, f_number))
        
        elif fn == 4 and wt == 2:  # nested enum (repeated EnumDescriptorProto)
            ename, evalues = extract_enum(val)
            if ename:
                nested_enums.append((ename, evalues))
        
        elif fn == 3 and wt == 2:  # nested message (repeated DescriptorProto)
            mname, mfields, m_enums, _ = extract_message(val)
            if mname:
                nested_messages.append((mname, mfields, m_enums))
    
    return msg_name, msg_fields, nested_enums, nested_messages

# Protobuf FileDescriptorSet 바이너리 영역
# FileDescriptorSet = repeated FileDescriptorProto
# FileDescriptorProto field 6 = repeated DescriptorProto (message types)
# FileDescriptorProto field 7 = repeated EnumDescriptorProto (enum types)

# 영역: 0x01583978 ~ 0x01588566
FDS_START = 0x01583978
FDS_END = 0x01588566
fds_data = dll[FDS_START:FDS_END]

print("=" * 70)
print("Arturia Collage Protobuf FileDescriptorSet 분석")
print("=" * 70)

# FileDescriptorSet 파싱
fds_fields = parse_protobuf_fields(fds_data)
print(f"\nFileDescriptorSet: {len(fds_fields)} top-level fields")

all_enums = []
all_messages = []

for fn, wt, val in fds_fields:
    if fn == 1 and wt == 2:  # FileDescriptorProto (repeated)
        fd_fields = parse_protobuf_fields(val)
        proto_name = ""
        package = ""
        
        for ffn, fwt, fval in fd_fields:
            if ffn == 1 and fwt == 2:  # name (.proto filename)
                s = try_parse_string(fval)
                if s:
                    proto_name = s
            elif ffn == 5 and fwt == 2:  # package
                s = try_parse_string(fval)
                if s:
                    package = s
            elif ffn == 6 and fwt == 2:  # message_type (repeated DescriptorProto)
                mname, mfields, m_enums, m_nested = extract_message(fval)
                if mname:
                    all_messages.append((f"{package}.{mname}" if package else mname, mfields))
                    for ne_name, ne_vals in m_enums:
                        all_enums.append((f"{package}.{ne_name}" if package else ne_name, ne_vals))
                    for nm_name, nm_fields, nm_enums in m_nested:
                        all_messages.append((f"{package}.{nm_name}" if package else nm_name, nm_fields))
                        for ne2_name, ne2_vals in nm_enums:
                            all_enums.append((f"{package}.{ne2_name}" if package else ne2_name, ne2_vals))
            elif ffn == 7 and fwt == 2:  # enum_type (repeated EnumDescriptorProto)
                ename, evalues = extract_enum(fval)
                if ename:
                    all_enums.append((f"{package}.{ename}" if package else ename, evalues))

# ─── 결과 출력 ───

print(f"\n## Enums ({len(all_enums)}개)\n")
for ename, values in sorted(all_enums):
    if values:
        print(f"  enum {ename}")
        for vname, vnum in values:
            print(f"    {vname} = {vnum}")
        print()

print(f"\n## Messages ({len(all_messages)}개)\n")
for mname, fields in sorted(all_messages):
    if fields:
        print(f"  message {mname}")
        for label, typ, fname, fnum in fields:
            print(f"    {label + ' ' if label else ''}{typ} {fname} = {fnum}")
        print()

# ─── DataParameterId 구조 상세 분석 ───
print("\n## DataParameterId 필드 구조 (핵심)")
for mname, fields in all_messages:
    if 'DataParameterId' in mname:
        print(f"\n  {mname}:")
        for label, typ, fname, fnum in fields:
            print(f"    {label + ' ' if label else ''}{typ} {fname} = {fnum}")

# ─── DataParameter 구조 ───
print("\n## DataParameter 필드 구조")
for mname, fields in all_messages:
    if mname.endswith('.DataParameter') or mname == 'DataParameter':
        print(f"\n  {mname}:")
        for label, typ, fname, fnum in fields:
            print(f"    {label + ' ' if label else ''}{typ} {fname} = {fnum}")

# ─── DataParameterValue 구조 ───
print("\n## DataParameterValue 필드 구조")
for mname, fields in all_messages:
    if 'DataParameterValue' in mname:
        print(f"\n  {mname}:")
        for label, typ, fname, fnum in fields:
            print(f"    {label + ' ' if label else ''}{typ} {fname} = {fnum}")

print("\n완료")
