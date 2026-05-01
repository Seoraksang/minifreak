#!/usr/bin/env python3
"""
Phase 14-1g: protobuf FileDescriptorProto 영역 정밀 파싱
google.protobuf 라이브러리 사용
"""

from google.protobuf.descriptor_pb2 import FileDescriptorProto, FileDescriptorSet
import sys, struct

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

# ─── 접근법 1: 각 FileDescriptorProto를 개별 블록으로 파싱 ───
# field 5(package) = "Arturia.Collage.Protobuf" 태그(0x2A) + 길이(0x1A) + 데이터
# 이 시그니처로 각 FileDescriptorProto의 시작점을 정확히 찾기

pkg_sig = b'\x2A\x1AArturia.Collage.Protobuf'
print("## FileDescriptorProto 블록 탐색 (field 5 package 시그니처)\n")

fd_blocks = []
pos = 0
while True:
    pos = dll.find(pkg_sig, pos)
    if pos == -1:
        break
    fd_start = pos  # 0x2A tag 위치
    # field 5 이후의 모든 protobuf 필드를 읽어서 전체 FileDescriptorProto 크기 계산
    scan = pos + 2 + 26  # tag(1) + length(1) + package(26)
    while scan < len(dll):
        tag = dll[scan]
        fn = tag >> 3
        wt = tag & 0x07
        if fn == 0 or fn > 10:
            break
        if wt == 2:  # length-delimited
            if scan + 1 >= len(dll):
                break
            length, new_scan = decode_varint(dll, scan + 1)
            scan = new_scan + length
        elif wt == 0:  # varint
            _, scan = decode_varint(dll, scan + 1)
        elif wt == 1:  # 64-bit
            scan += 9
        elif wt == 5:  # 32-bit
            scan += 5
        else:
            break
    
    fd_blocks.append((fd_start, scan))
    pos = scan

print(f"FileDescriptorProto 블록 {len(fd_blocks)}개 발견:")
for start, end in fd_blocks:
    print(f"  0x{start:08X} ~ 0x{end:08X} ({end-start:,} bytes)")

# ─── 각 블록을 FileDescriptorProto로 파싱 ───
print("\n" + "=" * 70)
print("파싱 결과")
print("=" * 70)

all_enums = {}
all_messages = {}

for idx, (start, end) in enumerate(fd_blocks):
    fd_data = dll[start:end]
    try:
        fd = FileDescriptorProto()
        fd.ParseFromString(fd_data)
        
        print(f"\n### [{idx+1}] {fd.name} (package: {fd.package})")
        print(f"    dependencies: {list(fd.dependency)}")
        
        for mt in fd.message_type:
            full_name = f"{fd.package}.{mt.name}" if fd.package else mt.name
            fields = []
            for f in mt.field:
                type_name = f.type_name if f.type_name else f'type_{f.type}'
                label = {1:'optional', 2:'required', 3:'repeated'}.get(f.label, f'label_{f.label}')
                fields.append((label, type_name, f.name, f.number))
            
            all_messages[full_name] = fields
            
            if fields:
                print(f"\n  message {full_name}")
                for label, typ, fname, fnum in fields:
                    print(f"    {label + ' ' if label else ''}{typ} {fname} = {fnum}")
            
            for ne in mt.enum_type:
                ename = f"{full_name}.{ne.name}"
                values = [(ev.name, ev.number) for ev in ne.value]
                all_enums[ename] = values
                if values:
                    print(f"\n  enum {ename}")
                    for vname, vnum in values:
                        print(f"    {vname} = {vnum}")
            
            # Nested messages
            for nmt in mt.nested_type:
                nfull = f"{full_name}.{nmt.name}"
                nfields = []
                for f in nmt.field:
                    type_name = f.type_name if f.type_name else f'type_{f.type}'
                    label = {1:'optional', 2:'required', 3:'repeated'}.get(f.label, f'label_{f.label}')
                    nfields.append((label, type_name, f.name, f.number))
                all_messages[nfull] = nfields
                if nfields:
                    print(f"\n  message {nfull}")
                    for label, typ, fname, fnum in nfields:
                        print(f"    {label + ' ' if label else ''}{typ} {fname} = {fnum}")
                
                for ne in nmt.enum_type:
                    ename2 = f"{nfull}.{ne.name}"
                    values2 = [(ev.name, ev.number) for ev in ne.value]
                    all_enums[ename2] = values2
                    if values2:
                        print(f"\n  enum {ename2}")
                        for vname, vnum in values2:
                            print(f"    {vname} = {vnum}")
        
        for et in fd.enum_type:
            ename = f"{fd.package}.{et.name}" if fd.package else et.name
            values = [(ev.name, ev.number) for ev in et.value]
            all_enums[ename] = values
            if values:
                print(f"\n  enum {ename}")
                for vname, vnum in values:
                    print(f"    {vname} = {vnum}")
    
    except Exception as e:
        # protobuf 파싱 실패 — field 5가 첫 필드가 아닐 수 있음
        # 앞쪽에 다른 필드가 있을 수 있으므로 앞으로 확장 시도
        for extra in [2, 4, 6, 8, 10, 20, 50]:
            try:
                extended = dll[start-extra:end]
                fd = FileDescriptorProto()
                fd.ParseFromString(extended)
                if fd.name:
                    print(f"\n### [{idx+1}] {fd.name} (offset -{extra})")
                    for mt in fd.message_type:
                        full_name = f"{fd.package}.{mt.name}" if fd.package else mt.name
                        fields = [(f.type_name or f'type_{f.type}', f.name, f.number) for f in mt.field]
                        all_messages[full_name] = fields
                        if fields:
                            print(f"\n  message {full_name}")
                            for typ, fname, fnum in fields:
                                print(f"    {typ} {fname} = {fnum}")
                    break
            except:
                continue
        else:
            print(f"\n### [{idx+1}] PARSE FAILED @ 0x{start:08X}: {e}")

# ─── 요약 ───
print("\n" + "=" * 70)
print(f"총 {len(all_messages)} 메시지, {len(all_enums)} enum 발견")
print("=" * 70)

# 핵심 메시지 구조 요약
for name in sorted(all_messages.keys()):
    if any(kw in name for kw in ['DataParameter', 'Header', 'Control', 'System', 'Resource']):
        fields = all_messages[name]
        print(f"\n  {name} ({len(fields)} fields)")

print("\n완료")
