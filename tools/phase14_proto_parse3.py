#!/usr/bin/env python3
"""
Phase 14-1h: protobuf FileDescriptorProto field 1(name) 시작점 기반 파싱
각 .proto 파일별로 독립적인 FileDescriptorProto 블록으로 파싱
"""

from google.protobuf.descriptor_pb2 import FileDescriptorProto
import sys

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

# field 1(name) 시작점: 0x0A + length + filename.proto
proto_starts = [
    0x01583952,  # collage_message_control_system.proto
    0x01584902,  # collage_message_control_resource.proto
    0x01585422,  # collage_message_control.proto
    0x01585592,  # collage_message_control_system_command.proto
    0x01585D32,  # collage_message_control_system_status.proto
    0x015863F2,  # collage_message_data_application.proto
    0x01586592,  # collage_message_data.proto
    0x01587132,  # collage_message_data_parameter.proto
    0x01587A42,  # collage_message_security.proto
    0x01587F82,  # collage_message_control_system_common.proto
    0x015883C2,  # collage_message_test.proto
    0x01588472,  # collage_message_test_chunk.proto
]

# 정렬
proto_starts.sort()

# 각 FileDescriptorProto의 끝은 다음 FileDescriptorProto의 시작 직전
# 마지막 것은 proto descriptor 영역의 끝까지

print("=" * 70)
print("Arturia Collage Protobuf — FileDescriptorProto 파싱")
print("=" * 70)

all_results = []

for i, start in enumerate(proto_starts):
    # FileDescriptorProto 시작 = field 1(name) 태그 위치
    # 0x0A = field 1, wire type 2
    tag_pos = start - 2  # 0x0A + length_byte
    
    # 다음 FileDescriptorProto의 끝
    if i + 1 < len(proto_starts):
        end = proto_starts[i + 1] - 2  # 다음의 tag_pos 바로 앞
    else:
        end = start + 20000  # 마지막은 충분히 크게
    
    fd_data = dll[tag_pos:end]
    
    # google.protobuf로 파싱
    try:
        fd = FileDescriptorProto()
        fd.ParseFromString(fd_data)
        
        if not fd.name:
            # field 1이 첫 필드가 아닐 수 있음 - 앞쪽 데이터 포함 시도
            for extra in range(2, 100):
                try:
                    fd2 = FileDescriptorProto()
                    fd2.ParseFromString(dll[tag_pos-extra:end])
                    if fd2.name:
                        fd = fd2
                        break
                except:
                    continue
        
        result = {
            'name': fd.name,
            'package': fd.package,
            'dependencies': list(fd.dependency),
            'messages': [],
            'enums': [],
        }
        
        for mt in fd.message_type:
            msg = {
                'name': mt.name,
                'full': f"{fd.package}.{mt.name}" if fd.package else mt.name,
                'fields': [(f.type_name or f'type_{f.type}', f.name, f.number) for f in mt.field],
                'enums': [(ne.name, [(ev.name, ev.number) for ev in ne.value]) for ne in mt.enum_type],
                'nested': [],
            }
            for nmt in mt.nested_type:
                nmsg = {
                    'name': nmt.name,
                    'full': f"{msg['full']}.{nmt.name}",
                    'fields': [(f.type_name or f'type_{f.type}', f.name, f.number) for f in nmt.field],
                    'enums': [(ne.name, [(ev.name, ev.number) for ev in ne.value]) for ne in nmt.enum_type],
                }
                msg['nested'].append(nmsg)
            result['messages'].append(msg)
        
        for et in fd.enum_type:
            result['enums'].append((et.name, [(ev.name, ev.number) for ev in et.value]))
        
        all_results.append(result)
        
        # 출력
        print(f"\n### {fd.name}")
        if fd.package:
            print(f"    package: {fd.package}")
        if fd.dependency:
            print(f"    deps: {', '.join(fd.dependency)}")
        
        for msg in result['messages']:
            if msg['fields']:
                print(f"\n  message {msg['full']}")
                for typ, fname, fnum in msg['fields']:
                    print(f"    {typ} {fname} = {fnum}")
            for ename, values in msg['enums']:
                if values:
                    print(f"\n  enum {msg['full']}.{ename}")
                    for vn, vv in values:
                        print(f"    {vn} = {vv}")
            for nmsg in msg['nested']:
                if nmsg['fields']:
                    print(f"\n  message {nmsg['full']}")
                    for typ, fname, fnum in nmsg['fields']:
                        print(f"    {typ} {fname} = {fnum}")
                for ename, values in nmsg['enums']:
                    if values:
                        print(f"\n  enum {nmsg['full']}.{ename}")
                        for vn, vv in values:
                            print(f"    {vn} = {vv}")
        
        for ename, values in result['enums']:
            if values:
                print(f"\n  enum {ename}")
                for vn, vv in values:
                    print(f"    {vn} = {vv}")
    
    except Exception as e:
        print(f"\n### PARSE FAILED @ 0x{tag_pos:08X}: {e}")
        # raw hex dump
        print(f"    First 50 bytes: {fd_data[:50].hex()}")

# ─── 통계 ───
total_msgs = sum(len(r['messages']) for r in all_results)
total_enums = sum(len(r['enums']) for r in all_results)
for r in all_results:
    for m in r['messages']:
        total_enums += len(m['enums'])
        total_msgs += len(m['nested'])

print(f"\n{'=' * 70}")
print(f"총 {len(all_results)} .proto 파일, {total_msgs} 메시지, {total_enums} enum")
print(f"{'=' * 70}")

# DataParameterId 상세
print("\n## DataParameterId 필드 (핵심)")
for r in all_results:
    for m in r['messages']:
        if 'DataParameterId' in m['full']:
            print(f"\n  {m['full']}:")
            for typ, fname, fnum in m['fields']:
                print(f"    {typ} {fname} = {fnum}")
        for nm in m.get('nested', []):
            if 'DataParameterId' in nm['full']:
                print(f"\n  {nm['full']}:")
                for typ, fname, fnum in nm['fields']:
                    print(f"    {typ} {fname} = {fnum}")

print("\n완료")
