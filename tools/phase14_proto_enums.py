#!/usr/bin/env python3
"""Phase 14: Extract enum definitions from protobuf descriptor (field 5)"""

from google.protobuf.internal.decoder import _DecodeVarint
import sys

with open('/tmp/collage_descriptor.bin', 'rb') as f:
    data = f.read()

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

def decode_raw_fields(data, pos=0, max_fields=500):
    fields = []
    while pos < len(data) and len(fields) < max_fields:
        tag, new_pos = decode_varint(data, pos)
        fn = tag >> 3
        wt = tag & 0x07
        if fn == 0 or fn > 30:
            break
        if wt == 0:
            val, pos = decode_varint(data, new_pos)
            fields.append((fn, 'varint', val))
        elif wt == 2:
            length, pos = decode_varint(data, new_pos)
            val = data[pos:pos+length]
            pos += length
            fields.append((fn, 'bytes', val))
        elif wt == 1:
            pos = new_pos + 8
            fields.append((fn, 'fixed64', None))
        elif wt == 5:
            pos = new_pos + 4
            fields.append((fn, 'fixed32', None))
        else:
            break
    return fields, pos

def try_str(val):
    try:
        s = val.decode('utf-8')
        if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in s):
            return s
    except:
        pass
    return None

proto_starts = [
    (0x0000, "collage_message_control_system.proto"),
    (0x0FB0, "collage_message_control_resource.proto"),
    (0x1AD0, "collage_message_control.proto"),
    (0x1C40, "collage_message_control_system_command.proto"),
    (0x23E0, "collage_message_control_system_status.proto"),
    (0x2750, "collage.proto"),
    (0x2AA0, "collage_message_data_application.proto"),
    (0x2C40, "collage_message_data.proto"),
    (0x37E0, "collage_message_data_parameter.proto"),
    (0x40F0, "collage_message_security.proto"),
    (0x4630, "collage_message_control_system_common.proto"),
    (0x4A70, "collage_message_test.proto"),
    (0x4B20, "collage_message_test_chunk.proto"),
]

print("=" * 70)
print("Protobuf Enum 정의 추출")
print("=" * 70)

all_enums = {}

for idx, (start, proto_name) in enumerate(proto_starts):
    end = proto_starts[idx + 1][0] if idx + 1 < len(proto_starts) else len(data)
    block = data[start:end]
    
    fields, _ = decode_raw_fields(block)
    
    package = ""
    for fn, ft, val in fields:
        if fn == 2 and ft == 'bytes':
            s = try_str(val)
            if s:
                package = s
    
    # field 4 = message_type (already extracted), field 5 = enum_type
    enum_types = []
    for fn, ft, val in fields:
        if fn == 5 and ft == 'bytes':
            enum_types.append(val)
    
    if not enum_types:
        # enum이 message 안에 nested되어 있을 수도 있음
        # field 4 (message_type) 안의 nested enum도 확인
        for fn, ft, val in fields:
            if fn == 4 and ft == 'bytes':
                mt_fields, _ = decode_raw_fields(val)
                for mfn, mft, mval in mt_fields:
                    if mfn == 4 and mft == 'bytes':
                        # Nested enum inside message
                        enum_types.append(mval)
    
    for enum_data in enum_types:
        e_fields, _ = decode_raw_fields(enum_data)
        e_name = ""
        e_values = []
        
        for efn, eft, eval_ in e_fields:
            if efn == 1 and eft == 'bytes':
                s = try_str(eval_)
                if s:
                    e_name = s
            elif efn == 2 and eft == 'bytes':
                # EnumValueDescriptorProto: field 1=name, field 3=number
                ev_fields, _ = decode_raw_fields(eval_)
                ev_name = ""
                ev_num = 0
                for evfn, evft, evval in ev_fields:
                    if evfn == 1 and evft == 'bytes':
                        s = try_str(evval)
                        if s:
                            ev_name = s
                    elif evfn == 3 and evft == 'varint':
                        ev_num = evval
                if ev_name:
                    e_values.append((ev_name, ev_num))
        
        if e_name and e_values:
            full_name = f"{package}.{e_name}" if package else e_name
            all_enums[full_name] = e_values
            print(f"\nenum {full_name}")
            for vn, vv in e_values:
                print(f"  {vn} = {vv}")

# ─── 핵심 enum 요약 ───
print(f"\n{'=' * 70}")
print(f"총 {len(all_enums)} enum 정의 발견")
print(f"{'=' * 70}")

for name in sorted(all_enums.keys()):
    values = all_enums[name]
    short_name = name.split('.')[-1]
    print(f"  {short_name}: {len(values)} values")

print("\n완료")
