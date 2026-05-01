# Phase 14: Arturia Collage 프로토콜 상세 분석

> **상태**: 14-1 완료 | 14-2 대기 | 14-3 대기
> **대상**: `MiniFreak V.dll` (x86-64 VST 플러그인, v4.0.2.6369, 29MB)
> **분석 방법**: strings + protobuf descriptor 역추출 + x86-64 패턴 매칭
> **분석 날짜**: 2026-04-29 ~ 2026-05-01

---

## 1. 개요

MiniFreak V ↔ 하드웨어 간 통신은 **MIDI가 아닌 Arturia 독자 프로토콜 "Collage"** (USB bulk transfer, protobuf 기반) 를 사용합니다.

### 1.1 Collage 아키텍처

```
MiniFreak V (VST)                    MiniFreak (Hardware)
┌──────────────────┐                ┌──────────────────┐
│ HwVstController  │                │ Collage Server   │
│   ├─ SendParam   │                │   ├─ Param recv  │
│   └─ ParamRecv   │                │   └─ Param send  │
│ ResourceTransferer│               │                  │
│   ├─ Preset IO   │                │                  │
│   ├─ Sample IO   │                │                  │
│   └─ Wavetable IO│                │                  │
│ CollageUpdater   │                │ DFU Handler      │
│   └─ UpdateFW    │                │   ├─ [dfu].install│
│ CollageCommandMgr│                │   ├─ [dfu].reboot │
└────────┬─────────┘                │   └─ [dfu].reset  │
         │                          └────────┬─────────┘
    libusb.dll                                │
    (USB bulk transfer)              USB Bulk Endpoint
         │                                │
         └──────── USB Physical ───────────┘
```

### 1.2 소스 파일 매핑 (DLL에서 발견된 Jenkins 빌드 경로)

| 파일 | 경로 | 역할 |
|------|------|------|
| `Channel.cpp` | `collage/src/Channel.cpp` | 메시지 라우팅, 인코딩/디코딩, 우선순위 |
| `CommUsb.cpp` | `collage/src/comm/CommUsb.cpp` | USB 통신, 패킷 파싱, 헤더 처리 |
| `LibusbWrapper.cpp` | `arturiausblib/src/libusb_wrapper/LibusbWrapper.cpp` | libusb 래핑, 디바이스 열기/닫기 |
| `IoTable.cpp` | `collage/src/IoTable.cpp` | 입출력 테이블, 파일 업로드 관리 |
| `CollageUpdater.cpp` | (DFU 관련) | 펌웨어 업데이트 (CollageUpdater::UpdateFW) |

### 1.3 통신 레이어

| 레이어 | 식별자 | 설명 |
|--------|--------|------|
| `collage.comm.usb` | USB bulk 전송 | 실제 USB 통신 (protobuf 페이로드) |
| `collage.comm.usb.nopayload` | 헤더만 | 커맨드/응답 |
| `collage.comm.usb.ll.keepalive` | 하위레벨 keepalive | 연결 유지 |
| `collage_message_control` | 컨트롤 메시지 | 시스템/리소스 커맨드 |
| `collage_message_data` | 데이터 메시지 | 파라미터/애플리케이션 |
| `collage_message_data_parameter` | 파라미터 전송 | VST↔HW 파라미터 동기화 |
| `collage_message_data_application` | 애플리케이션 | 프리셋/샘플 전송 |
| `collage_message_control_resource` | 리소스 관리 | 샘플/웨이브테이블 |
| `collage_message_security` | 보안 | 인증/해시 검증 |

---

## 2. 전송 계층

### 2.1 USB Bulk Transfer

- **라이브러리**: libusb (DLL에 정적 링크됨)
- **인터페이스**: `BulkInterface` 클래스
- **엔드포인트**: EP IN (`0x81`), EP OUT (`0x02`) — MiniFreak 표준 구성
- **연결 로그**: `"Creating USB connection (client = host) to 0x{addr}"`
- **VID**: Arturia `0x152E`
- **USB 이름**: `MiniFreak MIDI`

### 2.2 패킷 포맷

```
USB 패킷:  [CollageUsbHeader][ProtobufPayload]
TCP 패킷:  [LengthPrefix(4B)][CollageTcpHeader][ProtobufPayload]
```

### 2.3 헤더 크기 (추정값 — USB 캡처로 확정 필요)

| 상수 | 추정값 | 근거 |
|------|--------|------|
| `kCollageUsbInHeaderSize` | **8 bytes** | USB 동기화: sync(1)+type(1)+seq(2)+length(4) |
| `kCollageTcpHeaderSize` | **4 bytes** | TCP 길이 접두사: length(4) |

> **참고**: x86-64 디스어셈블리에서 인라인 상수를 직접 추출 시도했으나, 컴파일러 최적화로 함수 경계 추적이 어려움. Wireshark USBPcap 캡처로 최종 확인 필요.

### 2.4 에러 검증 문자열 (DLL에서 발견)

```
"inPacketMaxSize < kCollageUsbInHeaderSize"
"MaxSize < kCollageUsbInHeaderSize"
"Size < kCollageTcpHeaderSize"
"inPacketMaxSize < kCollageTcpHeaderSize"
"cannot get header size"
"cannot get payload max size"
"invalid max payload size"
"Invalid packet size (less than header size)"
"Header size in packet (%d) exceeds maximum payload size(%d)"
```

### 2.5 파라미터 동기화 채널 (hwvst)

```
VST → HW:  hwvst.comm.param.out / hwvst.comm.param.out.details
HW → VST:  hwvst.comm.param.in / hwvst.comm.param.in.details
Sync:      hwvst.comm.sync
KeepAlive: hwvst.comm.event
Performance: hwvst.comm.perf
Request:    hwvst.comm.request
```

- `HwVstController::SendParam` → Collage 메시지로 인코딩 → USB bulk OUT
- `HwVstController::ParamReceived` ← USB bulk IN → Collage 메시지 디코딩
- `MiniFreakPresetHwVstConverter` → HW 파라미터 ID ↔ VST 파라미터 ID 변환

---

## 3. Protobuf 메시지 스키마 (DLL에서 역추출)

DLL 내에 직렬화된 Protobuf FileDescriptorProto 바이너리에서 전체 스키마 추출.
**Arturia 커스텀 디스크립터 포맷** 사용 (표준 FileDescriptorProto와 필드 번호 상이):
- field 1 = name, field 2 = package, field 3 = dependency, field 4 = message_type, field 5 = enum_type

### 3.1 .proto 파일 목록 (12개)

| 파일 | 메시지 수 | 역할 |
|------|-----------|------|
| `collage.proto` | 1 | 최상위 메시지 (Top) |
| `collage_message_control.proto` | 1 | Control 라우팅 |
| `collage_message_control_system.proto` | 8 | 시스템 제어 (재부팅, 종료, 커맨드) |
| `collage_message_control_system_common.proto` | — | 시스템 공통 타입 (enum) |
| `collage_message_control_system_command.proto` | 4 | 셸 커맨드 실행 |
| `collage_message_control_system_status.proto` | 6 | 시스템 상태 조회 |
| `collage_message_control_resource.proto` | 8 | 리소스 관리 (프리셋, 파일) |
| `collage_message_data.proto` | 4 | 데이터 요청/응답/알림 |
| `collage_message_data_parameter.proto` | 10 | 파라미터 구독/설정/조회 |
| `collage_message_data_application.proto` | 1 | 앱 알림 |
| `collage_message_security.proto` | 3 | 인증/보안 |
| `collage_message_test.proto` | 1 | 테스트 (청크 전송) |
| `collage_message_test_chunk.proto` | 3 | 테스트 청크 |

### 3.2 최상위 메시지: `Top`

```protobuf
message Top {
  uint32 message_id = 1;           // 시퀀스 번호
  AckType ack_type = 2;            // ACK 정책
  Control control = 3;             // 시스템/리소스 제어
  Data data = 4;                   // 파라미터 데이터
  Test test = 5;                   // 테스트
  Security security = 6;           // 인증
  uint32 priority = 7;             // 전송 우선순위
}
```

### 3.3 데이터 파라미터 구조 (핵심)

```protobuf
// 파라미터 ID: 단일 ID 또는 비트마스크 그룹
message DataParameterId {
  uint32 single = 1;               // 개별 파라미터 ID
  uint32 mask = 2;                 // 비트마스크 (그룹 구독)
}

// 파라미터 값: 여러 타입 지원 (oneof semantics)
message DataParameterValue {
  uint32 u32 = 1;                  // unsigned 32-bit
  int32 i32 = 2;                   // signed 32-bit
  uint16 u16 = 3;                  // unsigned 16-bit
  int16 i16 = 4;                   // signed 16-bit
  uint8 u8 = 5;                    // unsigned 8-bit
  int8 i8 = 6;                     // signed 8-bit
  float f32 = 7;                   // 32-bit float
  string str = 8;                  // 문자열
  bytes blob = 9;                  // 바이너리 데이터
}

// 파라미터 완전 정의
message DataParameter {
  DataParameterId id = 1;          // 파라미터 식별자
  DataParameterStatus status = 2;  // 상태 (VALID, NOT_FOUND 등)
  DataParameterValue value = 3;    // 실제 값
}
```

### 3.4 파라미터 RPC 메시지

```protobuf
// 구독 (하드웨어 → VST 실시간 알림)
message DataParameterSubscribeRequest  { repeated DataParameterId ids = 1; }
message DataParameterSubscribeResponse { repeated DataParameter parameters = 1; }

// 조회
message DataParameterGetRequest  { repeated DataParameterId ids = 1; }
message DataParameterGetResponse { repeated DataParameter parameters = 1; }

// 설정
message DataParameterSetRequest  { repeated DataParameter parameters = 1; }
message DataParameterSetResponse { repeated DataParameter parameters = 1; }

// 리셋
message DataParameterResetRequest  { repeated DataParameterId ids = 1; }
message DataParameterResetResponse { repeated DataParameter parameters = 1; }

// 실시간 알림 (하드웨어 → VST)
message DataParameterNotify { repeated DataParameter parameters = 1; }
```

### 3.5 리소스 관리 (프리셋 전송)

```protobuf
message ResourceLocation {
  FILESYSTEM = 0;    // 일반 파일시스템
  TEMPORARY = 1;     // 임시 저장
  UPDATE = 2;        // 펌웨어 업데이트
  PRESET = 3;        // 프리셋
  WAVETABLE = 4;     // 웨이브테이블
  IMAGE = 5;         // 이미지 (디스플레이)
  METADATA = 6;      // 메타데이터
  DATABASE = 7;      // 데이터베이스
  BANK = 8;          // 프리셋 뱅크
  PLAYLIST = 9;      // 플레이리스트
  LOG = 10;          // 로그
}

// 프리셋 저장 요청 (청크 분할 지원)
message ResourceStoreRequest {
  string name = 1;
  ResourceLocation location = 2;
  bool is_start_of_resource = 3;
  bytes content = 4;
  uint32 total_size = 5;
}

// 프리셋 조회 요청 (부분 읽기 지원)
message ResourceRetrieveRequest {
  string name = 1;
  ResourceLocation location = 2;
  uint32 offset = 3;
  uint32 size = 4;
  ResourceOptions options = 5;
}
```

### 3.6 시스템 제어

```protobuf
message SystemVersionInfo {
  SystemVersionType type = 3;     // APP, API, PROTOCOL, ALL
  double system_id = 1;
  double sub_system_id = 2;
}

message SystemRestartRequest  { double system_id=1; double sub_system_id=2; double delay_ms=3; }
message SystemShutdownRequest { double system_id=1; double sub_system_id=2; double delay_ms=3; }

// 셸 커맨드 실행
message SystemCommandExecuteRequest {
  string command = 1;
  string arguments = 2;
  double timeout_ms = 3;
  SystemProcessEncryption encryption = 4;
}
```

### 3.7 Enum 정의 (14개)

| Enum | 값 수 | 용도 |
|------|-------|------|
| `AckType` | 3 | ACK_REQUIRED, ACK_NONE, ACK_DELAYED |
| `DataResult` | 7 | SUCCESS, ERROR, NOT_FOUND, NOT_IMPLEMENTED, ERROR_MEMORY, ALREADY_SUBSCRIBED, NOT_SUBSCRIBED |
| `DataParameterStatus` | 7 | UNKNOWN, VALID, WRONG_TYPE, NOT_FOUND, NOT_IMPLEMENTED, MEMORY_ERROR, ERROR |
| `ResourceResult` | 5 | SUCCESS, INVALID, IO_ERROR, NOT_FOUND, NOT_IMPLEMENTED |
| `ResourceLocation` | 11 | FILESYSTEM, TEMPORARY, UPDATE, PRESET, WAVETABLE, IMAGE, METADATA, DATABASE, BANK, PLAYLIST, LOG |
| `ResourceItemType` | 3 | UNKNOWN, FILE, DIRECTORY |
| `ResourceOptions` | 2 | NONE, FAST |
| `SystemResult` | 5 | SUCCESS, ERROR, NOT_FOUND, NOT_IMPLEMENTED, EXECUTION_ERROR |
| `SystemVersionType` | 5 | UNKNOWN, APP, API, PROTOCOL, ALL |
| `SystemProcessStatus` | 7 | UNKNOWN, RUNNING, TIMEOUT_KILLED, TERMINATED, FINISHED_OK, FINISHED_ERROR, INTERNAL_ERROR |
| `SystemProcessEncryption` | 2 | NONE, CHACHA20 |
| `SystemProcessOutputClear` | 5 | DONT_CLEAR, CLEAR_STDOUT, CLEAR_STDERR, CLEAR_ALL, NO_OUTPUT |
| `SecurityResult` | 5 | SUCCESS, INVALID, NEED_CODE, NOT_FOUND, NOT_IMPLEMENTED |
| `SecurityEncryption` | 1 | NONE |

---

## 4. ResourceTransferer 초기화 순서

```
 1. init resource handler
 2. add resource handler to message handlers
 3. init communication channel        ← Collage Channel 생성
 4. init resource control
 5. init system handler sync
 6. init data handler                 ← 파라미터 구독 설정
 7. init command manager channel
 8. init system handler
 9. start reception thread            ← 수신 스레드 시작
10. init security handler
11. resume IComm                     ← 통신 재개
```

---

## 5. DFU 펌웨어 업데이트 프로토콜

| 커맨드 | 설명 |
|--------|------|
| `[dfu].install` | 펌웨어 이미지 설치 |
| `[dfu].reboot` | 기기 재부팅 |
| `[dfu].reset_fw_from_dfu` | DFU 모드에서 펌웨어 모드로 복귀 |
| `[dfu].set_master_vers` | 마스터 펌웨어 버전 설정 |
| `[dfu].set_progression` | 업데이트 진행률 설정 |
| `[dfu].post_image_update` | 이미지 설치 후 처리 |
| `[dfu].pre_image_update` | 이미지 설치 전 처리 |
| `[dfu].checkhash` | 이미지 해시 검증 |
| `[dfu].rebootloader` | 부트로더 재부팅 |

### 업데이트 플로우

```
1. CollageUpdater::UpdateFW 진입
2. 이미지 해시 검증 ([dfu].checkhash)
3. 이미지 업로드 (Collage bulk transfer)
4. [dfu].pre_image_update
5. [dfu].install (실제 설치)
6. [dfu].post_image_update
7. [dfu].set_master_vers
8. [dfu].reboot
9. 기기 재부팅 대기 (Progression 모니터링)
```

---

## 6. 디바이스 식별

| 제품 | USB 이름 | 확장자 | mDNS 서비스 |
|------|---------|--------|-------------|
| MiniFreak | `MiniFreak MIDI` | `*.mnf` | `minifreak._tcp.local` |
| AstroLab 61 | `astrolab-61` | `*.astro,*.astros` | `_astrolab61-companion._tcp.local` |
| AstroLab 88 | `astrolab-88` | `*.astro88,*.astros88` | `_astrolab88-companion._tcp.local` |
| DrumFreak | `drumfreak` | `*.drum,*.drumos` | — |

### HwVst 연결 타입

| 식별자 | 용도 |
|--------|------|
| `hwvst.connection` | HwVst 컨트롤러 ↔ Collage 연결 |
| `hwvst.comm` | HwVst 통신 채널 |
| `omnilink.connection` | OmniLink (다중 기기) 연결 |
| `pc_comm` | PC 통신 |
| `app_comm` | 앱 통신 |
| `usb.update` | USB 펌웨어 업데이트 |

---

## 7. Phase 14 재평가

### ❌ 실기기 필요
1. Collage 프로토콜 실제 통신 (USB bulk transfer)
2. 파라미터 동기화 검증 (HW 응답 확인)
3. DFU 펌웨어 업데이트 실행
4. USB 헤더 크기 확정 (패킷 캡처)

### ✅ VST DLL 정적 분석으로 가능
1. ~~Protobuf 스키마 완전 추출~~ (완료 — 62 메시지, 14 enum)
2. ~~DFU 커맨드 체인 문서화~~ (완료)
3. ~~디바이스 식별 정보~~ (완료)
4. HW↔VST 파라미터 ID 매핑 테이블 추출 → **Phase 14-2**
5. libusb 기반 Collage 클라이언트 구현 → **Phase 14-3**

---

## 8. 다음 단계

### 14-2. MiniFreakPresetHwVstConverter 파라미터 매핑 테이블 추출
- VST 플러그인 내부에서 파라미터 ID ↔ 시냇물 이름 매핑 테이블 추출
- DLL strings에서 `MiniFreakPresetHwVstConverter` 관련 심볼 분석

### 14-3. libusb 기반 Collage 클라이언트 구현
- 추출한 스키마로 `.proto` 파일 생성
- libusb bulk transfer로 실제 기기와 통신하는 Python 클라이언트
- 파라미터 구독/조회/설정 기능

---

## 부록: 분석 도구

| 스크립트 | 용도 |
|----------|------|
| `phase14_collage_analysis.py` | DLL strings 분석 (클래스/함수/엔드포인트) |
| `phase14_header_extract*.py` (3개) | x86-64 CMP 패턴 매칭 + 문자열 컨텍스트 |
| `phase14_header_final.py` | 최종 헤더 크기 추출 시도 |
| `phase14_header_x86.py` | x86-64 LEA/CMP 분석 |
| `phase14_proto_scan.py` | Protobuf descriptor 영역 탐색 |
| `phase14_proto_custom.py` | **Arturia 커스텀 디스크립터 파싱 (성공)** |
| `phase14_proto_enums.py` | Enum 정의 추출 |
| `phase14_proto_*.py` (나머지) | google.protobuf 파싱 시도들 |
