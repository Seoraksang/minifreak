#!/usr/bin/env python3
"""
Phase 14: Arturia 커스텀 protobuf descriptor 포맷 파싱
field 1=name, field 2=package, field 3=dependency, field 4=message_type
"""

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

def decode_raw_fields(data, pos=0, max_fields=200):
    """Decode raw protobuf fields, return (fields, end_pos)"""
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

# 각 FileDescriptorProto 블록의 field 4 (message_type) 추출
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
print("Arturia Collage Protobuf — 커스텀 디스크립터 파싱")
print("=" * 70)

all_messages = {}
all_enums = {}

for idx, (start, proto_name) in enumerate(proto_starts):
    end = proto_starts[idx + 1][0] if idx + 1 < len(proto_starts) else len(data)
    block = data[start:end]
    
    fields, _ = decode_raw_fields(block)
    
    name = ""
    package = ""
    deps = []
    msg_types = []
    
    for fn, ft, val in fields:
        if fn == 1 and ft == 'bytes':
            s = try_str(val)
            if s:
                name = s
        elif fn == 2 and ft == 'bytes':
            s = try_str(val)
            if s:
                package = s
        elif fn == 3 and ft == 'bytes':
            s = try_str(val)
            if s:
                deps.append(s)
        elif fn == 4 and ft == 'bytes':
            msg_types.append(val)
    
    if not msg_types:
        continue
    
    print(f"\n### {name} (pkg: {package})")
    if deps:
        print(f"    deps: {', '.join(deps[:3])}{'...' if len(deps) > 3 else ''}")
    
    for mt_data in msg_types:
        # DescriptorProto: field 1=name, field 2=field, field 3=nested_type, field 4=enum_type, field 5=extension_range
        mt_fields, _ = decode_raw_fields(mt_data)
        
        msg_name = ""
        msg_fields = []
        msg_enums = []
        msg_nested = []
        
        for fn, ft, val in mt_fields:
            if fn == 1 and ft == 'bytes':
                s = try_str(val)
                if s:
                    msg_name = s
            elif fn == 2 and ft == 'bytes':
                # FieldDescriptorProto: field 1=name, field 3=number, field 4=type, field 5=label, field 6=type_name
                f_fields, _ = decode_raw_fields(val)
                f_name = ""
                f_num = 0
                f_type = ""
                f_type_name = ""
                
                type_map = {1:'double', 2:'float', 3:'int64', 4:'uint64', 5:'int32',
                           8:'bool', 9:'string', 11:'message', 13:'uint32', 14:'enum'}
                
                for ffn, fft, fval in f_fields:
                    if ffn == 1 and fft == 'bytes':
                        s = try_str(fval)
                        if s:
                            f_name = s
                    elif ffn == 3 and fft == 'varint':
                        f_num = fval
                    elif ffn == 4 and fft == 'varint':
                        f_type = type_map.get(fval, f'type_{fval}')
                    elif ffn == 6 and fft == 'bytes':
                        s = try_str(fval)
                        if s:
                            f_type_name = s
                
                if f_name and f_num:
                    actual_type = f_type_name if f_type_name else f_type
                    msg_fields.append((actual_type, f_name, f_num))
            
            elif fn == 3 and ft == 'bytes':
                # Nested DescriptorProto
                n_fields, _ = decode_raw_fields(val)
                n_name = ""
                n_msg_fields = []
                n_enums = []
                
                for nfn, nft, nval in n_fields:
                    if nfn == 1 and nft == 'bytes':
                        s = try_str(nval)
                        if s:
                            n_name = s
                    elif nfn == 2 and nft == 'bytes':
                        # nested field
                        nf_fields, _ = decode_raw_fields(nval)
                        nf_name = ""
                        nf_num = 0
                        nf_type = ""
                        nf_type_name = ""
                        for nffn, nfft, nfval in nf_fields:
                            if nffn == 1 and nfft == 'bytes':
                                s = try_str(nfval)
                                if s:
                                    nf_name = s
                            elif nffn == 3 and nfft == 'varint':
                                nf_num = nfval
                            elif nffn == 4 and nfft == 'varint':
                                nf_type = type_map.get(nfval, f'type_{nfval}')
                            elif nffn == 6 and nfft == 'bytes':
                                s = try_str(nfval)
                                if s:
                                    nf_type_name = s
                        if nf_name and nf_num:
                            actual = nf_type_name if nf_type_name else nf_type
                            n_msg_fields.append((actual, nf_name, nf_num))
                    elif nfn == 4 and nft == 'bytes':
                        # nested enum
                        ne_fields, _ = decode_raw_fields(nval)
                        ne_name = ""
                        ne_values = []
                        for nefn, neft, neval in ne_fields:
                            if nefn == 1 and neft == 'bytes':
                                s = try_str(neval)
                                if s:
                                    ne_name = s
                            elif nefn == 2 and neft == 'bytes':
                                # EnumValueDescriptorProto: field 1=name, field 3=number
                                evf, _ = decode_raw_fields(neval)
                                ev_name = ""
                                ev_num = 0
                                for evfn, evft, evval in evf:
                                    if evfn == 1 and evft == 'bytes':
                                        s = try_str(evval)
                                        if s:
                                            ev_name = s
                                    elif evfn == 3 and evft == 'varint':
                                        ev_num = evval
                                if ev_name:
                                    ne_values.append((ev_name, ev_num))
                        if ne_name and ne_values:
                            n_enums.append((ne_name, ne_values))
                
                if n_name:
                    full_nested = f"{package}.{msg_name}.{n_name}" if package and msg_name else n_name
                    msg_nested.append((full_nested, n_msg_fields, n_enums))
            
            elif fn == 4 and ft == 'bytes':
                # EnumDescriptorProto: field 1=name, field 2=value (repeated EnumValueDescriptorProto)
                e_fields, _ = decode_raw_fields(val)
                e_name = ""
                e_values = []
                
                for efn, eft, eval_ in e_fields:
                    if efn == 1 and eft == 'bytes':
                        s = try_str(eval_)
                        if s:
                            e_name = s
                    elif efn == 2 and eft == 'bytes':
                        # EnumValueDescriptorProto
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
                    msg_enums.append((e_name, e_values))
        
        if msg_name and (msg_fields or msg_enums or msg_nested):
            full_name = f"{package}.{msg_name}" if package else msg_name
            all_messages[full_name] = msg_fields
            
            print(f"\n  message {full_name}")
            for typ, fname, fnum in msg_fields:
                print(f"    {typ} {fname} = {fnum}")
            for ename, values in msg_enums:
                print(f"\n  enum {full_name}.{ename}")
                for vn, vv in values:
                    print(f"    {vn} = {vv}")
            for nfull, nfields, nenums in msg_nested:
                all_messages[nfull] = nfields
                if nfields:
                    print(f"\n  message {nfull}")
                    for typ, fname, fnum in nfields:
                        print(f"    {typ} {fname} = {fnum}")
                for ename, values in nenums:
                    all_enums[f"{nfull}.{ename}"] = values
                    print(f"\n  enum {nfull}.{ename}")
                    for vn, vv in values:
                        print(f"    {vn} = {vv}")

# 통계
print(f"\n{'=' * 70}")
print(f"총 {len(all_messages)} 메시지 타입 발견")
print(f"{'=' * 70}")

# 핵심 구조 요약
print("\n## 핵심 메시지 구조 요약")
for name in sorted(all_messages.keys()):
    fields = all_messages[name]
    if any(kw in name for kw in ['Parameter', 'Header', 'Control', 'Resource', 'System', 'Security']):
        print(f"  {name} ({len(fields)} fields)")

print("\n완료")
