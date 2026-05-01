#!/usr/bin/env python3
"""
Phase 14-1: VST DLL Collage 프로토콜 상세 분석
- USB 헤더 구조 추출 (kCollageUsbInHeaderSize, kCollageTcpHeaderSize)
- Protobuf 메시지 타입 완전 추출
- BulkInterface USB 엔드포인트/인터페이스 분석
- HwVstController 통신 플로우
"""

import struct
import re
import sys
from collections import defaultdict

DLL_PATH = sys.argv[1]  # "reference/minifreak_v_extracted/code$GetSharedVstDir/MiniFreak V.dll"

with open(DLL_PATH, "rb") as f:
    dll = f.read()

print(f"DLL 크기: {len(dll):,} bytes ({len(dll)/1024/1024:.1f} MB)")
print("=" * 70)

# ─── 1. Collage Protobuf 메시지 타입 완전 추출 ───
print("\n## 1. Arturia.Collage.Protobuf 메시지 타입\n")

proto_msgs = set()
proto_enums = set()
for m in re.finditer(rb'Arturia\.Collage\.Protobuf\.(\w+)', dll):
    name = m.group(1).decode('ascii', errors='replace')
    if name.endswith('H'):
        proto_msgs.add(name[:-1])
    else:
        proto_msgs.add(name)

# Enum 타입 추출
for m in re.finditer(rb'Arturia\.Collage\.Protobuf\.(\w+)', dll):
    name = m.group(1).decode('ascii', errors='replace')
    # Enum 보통 짧은 이름
    proto_msgs.add(name)

proto_msgs_sorted = sorted(proto_msgs)
for msg in proto_msgs_sorted:
    print(f"  {msg}")

print(f"\n  총 {len(proto_msgs_sorted)}개 Protobuf 타입")

# ─── 2. Protobuf .proto 파일 목록 ───
print("\n## 2. Protobuf .proto 소스 파일\n")

proto_files = set()
for m in re.finditer(rb'([\w_]+\.proto)', dll):
    fname = m.group(1).decode('ascii', errors='replace')
    proto_files.add(fname)

for pf in sorted(proto_files):
    if 'collage' in pf.lower() or 'Collage' in pf:
        print(f"  ★ {pf}")
    else:
        print(f"    {pf}")

# ─── 3. USB 헤더 크기 상수 검색 ───
print("\n## 3. USB/TCP 헤더 크기 상수\n")

# kCollageUsbInHeaderSize 문자열 주변에서 상수값 추출
for keyword in [b'kCollageUsbInHeaderSize', b'kCollageTcpHeaderSize']:
    pos = 0
    while True:
        pos = dll.find(keyword, pos)
        if pos == -1:
            break
        # 주변 64바이트 hex dump
        start = max(0, pos - 32)
        end = min(len(dll), pos + len(keyword) + 32)
        context = dll[start:end]
        hex_str = ' '.join(f'{b:02X}' for b in context)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in context)
        print(f"  [{keyword.decode()}] @ offset 0x{pos:08X}")
        print(f"    HEX: {hex_str}")
        print(f"    ASC: {ascii_str}")
        pos += 1

# x86-64에서 상수 로딩 패턴: mov ecx/edx, imm32 또는 mov r32, imm32
# 작은 상수는 cmp/mov에 직접 사용됨
# USB 헤더 사이즈는 보통 4~16바이트 범위
# DLL에서 mov reg, <small_constant> 패턴으로 검색

# ─── 4. Collage 통신 계층 문자열 ───
print("\n## 4. Collage 통신 계층\n")

comm_layers = set()
for m in re.finditer(rb'collage\.comm(\.\w+)*', dll):
    layer = m.group(0).decode('ascii', errors='replace')
    comm_layers.add(layer)

for layer in sorted(comm_layers):
    print(f"  {layer}")

# ─── 5. USB 엔드포인트 관련 문자열 ───
print("\n## 5. USB Bulk/Endpoint 관련\n")

usb_patterns = [
    rb'bulk.*endpoint', rb'endpoint.*bulk', rb'BULK_EP', rb'EP_IN', rb'EP_OUT',
    rb'interface.*\d+', rb'usb.*\d+\.\d+', rb'claim_interface',
    rb'set_interface', rb'set_alt', rb'altsetting',
    rb'libusb_claim_interface', rb'libusb_release_interface',
    rb'libusb_set_interface', rb'libusb_bulk_transfer',
    rb'libusb_control_transfer',
    rb'BulkInterface', rb'GenericInterface', rb'TUsbInterface',
    rb'CommUsb', rb'LibusbWrapper',
    rb'libusb_init', rb'libusb_open', rb'libusb_close',
    rb'VID', rb'PID', rb'0x1[Cc]75', rb'0x152[Ee]',
    rb'USB.*speed', rb'USB.*timeout', rb'packet.*max', rb'max.*packet',
    rb'transfer.*timeout', rb'timeout.*transfer',
    rb'write.*timeout', rb'read.*timeout',
]

found_usb = set()
for pat in usb_patterns:
    for m in re.finditer(pat, dll, re.IGNORECASE):
        start = max(0, m.start() - 20)
        end = min(len(dll), m.end() + 40)
        # null-terminated string 추출
        region = dll[m.start():min(len(dll), m.start() + 200)]
        null_pos = region.find(b'\x00')
        if null_pos > 0:
            s = region[:null_pos].decode('ascii', errors='replace')
            if len(s) > 3:
                found_usb.add(s)

for s in sorted(found_usb):
    print(f"  {s}")

# ─── 6. HwVstController 통신 로그 문자열 ───
print("\n## 6. HwVst 통신 로그/디버그 문자열\n")

hwvst_strings = set()
for m in re.finditer(rb'(?:(?:HwVst|hwvst|SendParam|ParamRecv|ResourceTransfer|FirmwareUpdate|CollageUpdater)\w*[:\s]\s*)([^\x00\n]{10,200})', dll):
    s = m.group(0).decode('ascii', errors='replace').strip()
    if len(s) > 5:
        hwvst_strings.add(s)

for s in sorted(hwvst_strings)[:30]:
    print(f"  {s}")

# ─── 7. DFU/펌웨어 업데이트 관련 문자열 ───
print("\n## 7. DFU/펌웨어 업데이트 관련\n")

dfu_strings = set()
for m in re.finditer(rb'(?:dfu|firmware.*update|bootloader|reboot|install.*image|hash.*check|master.*vers|progression)[^\x00]{0,100}', dll, re.IGNORECASE):
    s = m.group(0).decode('ascii', errors='replace').strip()
    if len(s) > 5:
        dfu_strings.add(s)

for s in sorted(dfu_strings)[:20]:
    print(f"  {s}")

# ─── 8. DLL 소스 경로에서 Collage 모듈 구조 추출 ───
print("\n## 8. Collage 소스 모듈 구조 (DLL 내부 경로)\n")

collage_paths = set()
for m in re.finditer(rb'[A-Z]:[/\\]jenkins[/\\].*?collage.*?\.(?:cpp|h|hpp)\x00', dll, re.IGNORECASE):
    path = m.group(0).decode('ascii', errors='replace').rstrip('\x00')
    collage_paths.add(path)

for p in sorted(collage_paths):
    # 간단한 경로 축약
    short = p.replace('\\', '/').split('minifreakv/')[-1] if 'minifreakv/' in p.replace('\\', '/') else p.replace('\\', '/')
    print(f"  {short}")

print(f"\n  총 {len(collage_paths)}개 Collage 소스 파일")

# ─── 9. Protobuf AckType, Control 등 enum 후보 ───
print("\n## 9. Protobuf Enum 후보\n")

# AckType 등 짧은 이름 = enum
enum_candidates = set()
for m in re.finditer(rb'Arturia\.Collage\.Protobuf\.(\w{3,30})\x00', dll):
    name = m.group(1).decode('ascii', errors='replace')
    # 긴 이름(20+문자)은 보통 message, 짧은 건 enum
    if len(name) < 25 and not any(x in name for x in ['Request', 'Response', 'Notify']):
        enum_candidates.add(name)

for e in sorted(enum_candidates):
    print(f"  {e}")

print("\n" + "=" * 70)
print("분석 완료")
