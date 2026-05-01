#!/usr/bin/env python3
"""Phase 14: Parse protobuf descriptor from DLL using FileDescriptorSet"""

from google.protobuf import descriptor_pb2
from google.protobuf.internal.decoder import _DecodeVarint
import sys

with open('/tmp/collage_descriptor.bin', 'rb') as f:
    data = f.read()

print(f"Data size: {len(data)} bytes")
print(f"First 4 bytes: {data[:4].hex()}")

# Check if this starts with field 1 tag (0x0A) of FileDescriptorSet
# or field 1 tag (0x0A) of FileDescriptorProto
# Both have the same tag! Distinguish by content.

# If it's FDS field 1: tag(1) + length_varint + FileDescriptorProto_binary
# The FileDescriptorProto should start with its own tag (0x0A for field 1 name)
# So we'd see: 0x0A <len1> 0x0A <len2> "filename.proto"

# If it's FileDescriptorProto field 1: tag(1) + length + "filename.proto"
# We'd see: 0x0A <len> "filename.proto"

# At 0x01583950: 0x0A 0x24 "collage_message_control_system.proto"
# 0x24 = 36 = len("collage_message_control_system.proto")
# So this is FileDescriptorProto field 1 (name), NOT FileDescriptorSet field 1

# This means the data is NOT wrapped in FileDescriptorSet
# It might be multiple FileDescriptorProto entries concatenated

# Try parsing each separately
# Find all occurrences of 0x0A <len> "*.proto" pattern
import re

proto_positions = []
pos = 0
while pos < len(data):
    # Look for 0x0A followed by a length byte then ".proto"
    if data[pos] == 0x0A and pos + 1 < len(data):
        length = data[pos + 1]
        if 10 < length < 80 and pos + 2 + length <= len(data):
            candidate = data[pos + 2:pos + 2 + length]
            if candidate.endswith(b'.proto') and all(32 <= b < 127 for b in candidate):
                name = candidate.decode('ascii')
                # Check if this looks like a FileDescriptorProto start
                # by trying to parse from here to the next similar pattern
                proto_positions.append((pos, name, length))
    pos += 1

print(f"\nFound {len(proto_positions)} .proto name entries")
for off, name, length in proto_positions:
    print(f"  0x{off:08X}: {name} (len={length})")

# For each position, try to parse a FileDescriptorProto
# The end boundary is the next .proto name entry OR end of data
print("\n## Individual FileDescriptorProto parsing")
for i, (off, name, length) in enumerate(proto_positions):
    # Find end boundary
    if i + 1 < len(proto_positions):
        end = proto_positions[i + 1][0]
    else:
        end = len(data)
    
    # Try parsing from off to end
    # The FileDescriptorProto starts at 'off' with field 1(name)
    # But there might be fields before it in the actual binary
    # Let's try from 'off' directly first
    fd_data = data[off:end]
    
    try:
        fd = descriptor_pb2.FileDescriptorProto()
        fd.ParseFromString(fd_data)
        if fd.name:
            print(f"\n[{i+1}] {fd.name} ({len(fd.message_type)} msgs, {len(fd.enum_type)} enums)")
            for mt in fd.message_type:
                print(f"  msg: {mt.name} ({len(mt.field)} fields)")
                for fld in mt.field:
                    t = fld.type_name or f'type_{fld.type}'
                    lbl = {1:'optional',2:'required',3:'repeated'}.get(fld.label, '')
                    print(f"    {lbl} {t} {fld.name} = {fld.number}")
                for ne in mt.enum_type:
                    print(f"  enum: {ne.name}")
                    for ev in ne.value:
                        print(f"    {ev.name} = {ev.number}")
                for nmt in mt.nested_type:
                    print(f"  nested: {nmt.name} ({len(nmt.field)} fields)")
                    for fld in nmt.field:
                        t = fld.type_name or f'type_{fld.type}'
                        print(f"    {t} {fld.name} = {fld.number}")
                    for ne2 in nmt.enum_type:
                        print(f"  enum: {ne2.name}")
                        for ev in ne2.value:
                            print(f"    {ev.name} = {ev.number}")
            for et in fd.enum_type:
                print(f"  enum: {et.name}")
                for ev in et.value:
                    print(f"    {ev.name} = {ev.number}")
            continue
    except Exception as e:
        pass
    
    # If parsing from 'off' fails, the FileDescriptorProto might start before
    # Try including some prefix bytes
    for extra in [2, 4, 6, 8, 10, 20, 30, 50]:
        try:
            start = max(0, off - extra)
            fd_data2 = data[start:end]
            fd = descriptor_pb2.FileDescriptorProto()
            fd.ParseFromString(fd_data2)
            if fd.name:
                print(f"\n[{i+1}] {fd.name} (offset -{extra}, {len(fd.message_type)} msgs, {len(fd.enum_type)} enums)")
                for mt in fd.message_type:
                    print(f"  msg: {mt.name} ({len(mt.field)} fields)")
                    for fld in mt.field:
                        t = fld.type_name or f'type_{fld.type}'
                        print(f"    {t} {fld.name} = {fld.number}")
                    for ne in mt.enum_type:
                        print(f"  enum: {ne.name}")
                        for ev in ne.value:
                            print(f"    {ev.name} = {ev.number}")
                break
        except:
            continue
    else:
        print(f"\n[{i+1}] PARSE FAILED: {name}")

print("\n완료")
