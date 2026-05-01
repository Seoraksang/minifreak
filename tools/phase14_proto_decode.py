#!/usr/bin/env python3
"""Phase 14-1i: Raw protobuf decode of descriptor region"""

from google.protobuf.descriptor_pb2 import FileDescriptorSet, FileDescriptorProto
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

# ─── Raw protobuf decode (protoc --decode_raw 스타일) ───
print("## Raw protobuf decode: 0x01583950 (첫 .proto filename)")
data = dll[0x01583950:0x01583950+500]
pos = 0
count = 0
while pos < len(data) and count < 60:
    tag, new_pos = decode_varint(data, pos)
    fn = tag >> 3
    wt = tag & 0x07
    if fn == 0 or fn > 30:
        break
    count += 1
    
    if wt == 0:
        val, pos = decode_varint(data, new_pos)
        print(f"  field {fn} (varint): {val}")
    elif wt == 2:
        length, pos = decode_varint(data, new_pos)
        val = data[pos:pos+length]
        pos += length
        try:
            s = val.decode('utf-8')
            if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in s) and len(s) > 0:
                if len(s) > 80:
                    print(f"  field {fn} (string): \"{s[:60]}...\" ({len(s)} chars)")
                else:
                    print(f"  field {fn} (string): \"{s}\"")
            else:
                print(f"  field {fn} (bytes): [{length} bytes]")
        except:
            print(f"  field {fn} (bytes): [{length} bytes]")
    elif wt == 1:
        pos = new_pos + 8
        print(f"  field {fn} (64-bit)")
    elif wt == 5:
        pos = new_pos + 4
        print(f"  field {fn} (32-bit)")
    else:
        break

# ─── FDS 파싱: 전체 영역을 하나의 blob으로 ───
print("\n## FileDescriptorSet 파싱 시도 (다양한 경계)")
for label, start, end in [
    ("0x01583950 ~ 0x01588600", 0x01583950, 0x01588600),
    ("0x01583940 ~ 0x01588600", 0x01583940, 0x01588600),
    ("0x01583950 ~ 0x01589000", 0x01583950, 0x01589000),
]:
    try:
        fds = FileDescriptorSet()
        fds.ParseFromString(dll[start:end])
        if fds.file:
            print(f"  [{label}] OK: {len(fds.file)} files")
            for f in fds.file[:3]:
                print(f"    - {f.name} ({len(f.message_type)} msgs)")
        else:
            print(f"  [{label}] OK but 0 files")
    except Exception as e:
        print(f"  [{label}] FAILED: {e}")

# ─── 단일 FileDescriptorProto로 직접 파싱 ───
print("\n## 단일 FileDescriptorProto 직접 파싱")
# 0x01583950부터 다음 null terminator까지?
# 아니면 더 정확한 경계를 찾아야 함

# 각 field 1(name) 사이의 간격이 크기가 다름
# 첫 번째와 두 번째 사이: 0x01584902 - 0x01583952 = 0xFB0 = 4016 bytes
# 두 번째와 세 번째: 0x01585422 - 0x01584902 = 0xB80 = 2944 bytes

# 하지만 "collage_message_control_system.proto" @ 0x01583952는
# 다른 FileDescriptorProto의 dependency로도 참조될 수 있음!

# 정확한 경계: FileDescriptorProto는 field 6(message_type)을 포함하며
# 각 message_type은 field 1(name)으로 시작하는 DescriptorProto
# ServiceDescriptorProto는 field 6(service)에 저장됨

# 더 나은 접근: 전체 영역을 하나의 FileDescriptorSet으로 간주하고
# FileDescriptorSet.field = repeated FileDescriptorProto

# FileDescriptorSet field 1 tag = 0x0A (same as FileDescriptorProto field 1!)
# 구별: FileDescriptorSet.field[0]의 FileDescriptorProto가 field 1(name)로 시작하면
# FDS tag 0x0A → length → FileDescriptorProto 0x0A → length → name

# 즉 0x01583950의 0x0A가 FDS field 1이면,
# 다음 바이트 0x24 (36)은 FileDescriptorProto 전체 길이
# FileDescriptorProto는 36바이트 안에 name(36)만 들어가므로 모순

# 결론: 0x01583950의 0x0A는 FileDescriptorProto field 1(name)의 태그
# FileDescriptorSet wrapper 없이 각 FileDescriptorProto가 연속으로 저장됨

# 그렇다면 각 FileDescriptorProto의 끝을 어떻게 알 수 있나?
# → 끝에 field 1(name)이 없는 마지막 필드까지 읽고 다음 0x0A가 나오면 종료

# 실제로 각 FileDescriptorProto를 개별적으로 파싱하기 위해
# field 1(name)으로 시작해서 전체를 읽고 다음 FileDescriptorProto의 field 1(name) 전까지

# 하지만 "collage_message_control_system.proto"는 다른 파일의 dependency로도 인용됨
# → 각 field 1(name) 앞의 0x0A가 항상 FileDescriptorProto의 시작은 아닐 수 있음

# 가장 확실한 방법: 0x01583950부터 하나의 거대한 FileDescriptorProto로 파싱 시도
# (모든 .proto 파일이 하나의 FileDescriptorProto에 통합되었을 가능성)

print("  단일 통합 FileDescriptorProto 파싱...")
for end_offset in [0x01588600, 0x01589000, 0x0158A000, 0x01590000]:
    try:
        fd = FileDescriptorProto()
        fd.ParseFromString(dll[0x01583950:end_offset])
        if fd.name:
            print(f"    OK @ 0x{end_offset:08X}: name={fd.name}, {len(fd.message_type)} msgs, {len(fd.enum_type)} enums")
            for mt in fd.message_type:
                print(f"      msg: {mt.name} ({len(mt.field)} fields)")
            break
    except:
        pass

# ─── 마지막 수단: decode_raw으로 전체 구조 파악 ───
print("\n## Full raw decode (첫 2000 bytes from 0x01583950)")
data = dll[0x01583950:0x01583950+2000]
pos = 0
depth = 0
max_items = 200
items = 0

while pos < len(data) and items < max_items:
    tag, new_pos = decode_varint(data, pos)
    fn = tag >> 3
    wt = tag & 0x07
    if fn == 0 or fn > 30:
        pos += 1
        continue
    items += 1
    
    if wt == 0:
        val, pos = decode_varint(data, new_pos)
        print(f"{'  '*depth}{fn}:{val}")
    elif wt == 2:
        length, pos = decode_varint(data, new_pos)
        val = data[pos:pos+length]
        pos += length
        try:
            s = val.decode('utf-8')
            if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in s) and len(s) > 0:
                print(f"{'  '*depth}{fn}:\"{s[:80]}\"")
            else:
                print(f"{'  '*depth}{fn}:[{length}B]")
        except:
            print(f"{'  '*depth}{fn}:[{length}B]")
    elif wt == 1:
        pos = new_pos + 8
        print(f"{'  '*depth}{fn}:[64b]")
    elif wt == 5:
        pos = new_pos + 4
        print(f"{'  '*depth}{fn}:[32b]")
    else:
        pos += 1

print("\n완료")
