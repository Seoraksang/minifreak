#!/usr/bin/env python3
"""
Phase 14-1d: "size() == 8" 문자열 근처 코드 분석으로 헤더 크기 확정
그리고 "HeaderSize): " 문자열 근처에서 실제 헤더 사이즈값 추출
"""

import struct, sys

DLL_PATH = sys.argv[1]
with open(DLL_PATH, "rb") as f:
    dll = f.read()

# ─── 1. "size() == 8" 문자열 분석 ───
print("## 1. 'size() == 8' 문자열 컨텍스트")
s = b'size() == 8'
pos = dll.find(s)
if pos > 0:
    # 앞뒤 100바이트 컨텍스트
    start = max(0, pos - 100)
    end = min(len(dll), pos + 200)
    null1 = dll.rfind(b'\x00', start, pos)
    null2 = dll.find(b'\x00', pos, end)
    if null1 >= 0 and null2 > 0:
        full = dll[null1+1:null2].decode('ascii', errors='replace')
        print(f"  @ 0x{pos:08X}:")
        for line in full.split('\n'):
            print(f"    {line}")

# ─── 2. "HeaderSize): " 문자열 분석 ───
print("\n## 2. 'HeaderSize): ' 컨텍스트")
s2 = b'HeaderSize): '
pos2 = dll.find(s2)
if pos2 > 0:
    start = max(0, pos2 - 200)
    end = min(len(dll), pos2 + 200)
    null1 = dll.rfind(b'\x00', start, pos2)
    null2 = dll.find(b'\x00', pos2, end)
    if null1 >= 0 and null2 > 0:
        full = dll[null1+1:null2].decode('ascii', errors='replace')
        print(f"  @ 0x{pos2:08X}:")
        for line in full.split('\n'):
            print(f"    {line}")

# ─── 3. Collage 소스 파일 경로에서 함수 이름 추출 ───
# "collage/src/comm/CommUsb.cpp" 근처에서 CommUsb 관련 함수 검색
print("\n## 3. CommUsb.cpp 근처 클래스/함수 이름")
commusb = b'CommUsb.cpp'
pos3 = dll.find(commusb)
if pos3 > 0:
    # 앞으로 스캔하며 C++ mangled name 찾기
    region = dll[max(0,pos3-2000):pos3+500]
    for m in __import__('re').finditer(rb'\?[\w@]+\@CommUsb\@', region):
        name = m.group(0).decode('ascii', errors='replace')
        print(f"  {name}")

# ─── 4. CommUsb 헤더/페이로드 관련 ASSERT/CHECK 문자열 ───
print("\n## 4. CommUsb assert/check 문자열")
for pat in [b'host) to 0x', b'kCollageUsbInHeaderSize', b'kCollageTcpHeaderSize',
            b'MaxSize < k', b'inPacketMaxSize < k',
            b'cannot get header', b'cannot get payload',
            b'invalid max payload', b'Invalid packet size']:
    pos = dll.find(pat)
    if pos > 0:
        null = dll.find(b'\x00', pos)
        full = dll[pos:null].decode('ascii', errors='replace')
        print(f"  [0x{pos:08X}] {full}")

# ─── 5. "host) to 0x" 문자열 — 이것이 USB 엔드포인트 주소! ───
print("\n## 5. USB 엔드포인트 주소 ('host) to 0x')")
s5 = b'host) to 0x'
pos5 = dll.find(s5)
if pos5 > 0:
    null = dll.find(b'\x00', pos5)
    full = dll[pos5:null].decode('ascii', errors='replace')
    print(f"  [0x{pos5:08X}] {full}")
    # 이 주변의 다른 문자열도 읽기
    start = max(0, pos5 - 500)
    region = dll[start:null+200]
    nulls = [i for i, b in enumerate(region) if b == 0]
    for i in range(len(nulls)-1):
        s = region[nulls[i]+1:nulls[i+1]].decode('ascii', errors='replace')
        if len(s) > 5:
            print(f"  [0x{start+nulls[i]+1:08X}] {s}")

# ─── 6. LibusbWrapper.cpp 근처에서 USB 초기화 관련 문자열 ───
print("\n## 6. LibusbWrapper USB 초기화 문자열")
libusb = b'LibusbWrapper.cpp'
pos6 = dll.find(libusb)
if pos6 > 0:
    start = max(0, pos6 - 1000)
    end = min(len(dll), pos6 + 1000)
    region = dll[start:end]
    nulls = [i for i, b in enumerate(region) if b == 0]
    for i in range(len(nulls)-1):
        s = region[nulls[i]+1:nulls[i+1]].decode('ascii', errors='replace')
        if len(s) > 10 and any(kw in s.lower() for kw in ['usb', 'endpoint', 'interface', 
            'claim', 'bulk', 'config', 'alt', 'device', 'vid', 'pid', 'speed']):
            print(f"  [0x{start+nulls[i]+1:08X}] {s}")

# ─── 7. IoTable.cpp — 입출력 테이블 (엔드포인트 매핑) ───
print("\n## 7. IoTable.cpp 근처 문자열")
iotable = b'IoTable.cpp'
pos7 = dll.find(iotable)
if pos7 > 0:
    start = max(0, pos7 - 200)
    end = min(len(dll), pos7 + 500)
    region = dll[start:end]
    nulls = [i for i, b in enumerate(region) if b == 0]
    for i in range(len(nulls)-1):
        s = region[nulls[i]+1:nulls[i+1]].decode('ascii', errors='replace')
        if len(s) > 3:
            print(f"  [0x{start+nulls[i]+1:08X}] {s}")

# ─── 8. CollageChannel/Channel.cpp 근처 문자열 ───
print("\n## 8. Channel.cpp 근처 문자열")
channel = b'Channel.cpp'
pos8 = dll.find(channel)
if pos8 > 0:
    start = max(0, pos8 - 200)
    end = min(len(dll), pos8 + 500)
    region = dll[start:end]
    nulls = [i for i, b in enumerate(region) if b == 0]
    for i in range(len(nulls)-1):
        s = region[nulls[i]+1:nulls[i+1]].decode('ascii', errors='replace')
        if len(s) > 3:
            print(f"  [0x{start+nulls[i]+1:08X}] {s}")

# ─── 9. CommUsb::open/read/write 함수에서 엔드포인트 번호 찾기 ───
# USB bulk transfer는 엔드포인트 번호를 인자로 받음
# libusb_bulk_transfer(dev_handle, ep, data, len, &transferred, timeout)
# ep 번호는 0x81(IN), 0x02(OUT) 등
print("\n## 9. USB 엔드포인트 번호 후보")
# 0x81 = EP1 IN (bulk), 0x02 = EP2 OUT (bulk) — MiniFreak 일반적 구성
for ep in [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86]:
    packed = struct.pack('<B', ep)
    # libusb_bulk_transfer 호출 근처에서 이 값이 나타나는지
    # (너무 많으므로 의미 있는 패턴만)
    pass

# 대신 TUSBAUDIO 함수 export에서 힌트
print("\n## 10. DFU 펌웨어 업데이트 플로우")
# CollageUpdater::UpdateFW 문자열 근처
upfw = b'CollageUpdater::UpdateFW'
pos10 = dll.find(upfw)
if pos10 > 0:
    start = max(0, pos10 - 300)
    end = min(len(dll), pos10 + 1000)
    region = dll[start:end]
    nulls = [i for i, b in enumerate(region) if b == 0]
    for i in range(len(nulls)-1):
        s = region[nulls[i]+1:nulls[i+1]].decode('ascii', errors='replace')
        if len(s) > 5:
            print(f"  [0x{start+nulls[i]+1:08X}] {s}")

# ─── 11. ResourceTransferer 초기화 순서 (HwVstController ↔ Collage 통신) ───
print("\n## 11. ResourceTransferer 초기화 순서")
rt = b'ResourceTransferer: '
pos11 = 0
while True:
    pos11 = dll.find(rt, pos11)
    if pos11 == -1:
        break
    null = dll.find(b'\x00', pos11)
    s = dll[pos11:null].decode('ascii', errors='replace')
    print(f"  [0x{pos11:08X}] {s}")
    pos11 += 1

# ─── 12. omnilink.connection / hwvst.connection 문자열 ───
print("\n## 12. 통신 연결 타입")
for pat in [b'omnilink.connection', b'hwvst.connection', b'hwvst.comm',
            b'usb.update', b'pc_comm', b'app_comm']:
    pos = dll.find(pat)
    if pos > 0:
        null = dll.find(b'\x00', pos)
        s = dll[pos:null].decode('ascii', errors='replace')
        print(f"  [0x{pos:08X}] {s}")

print("\n완료")
