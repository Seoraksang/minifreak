# MiniFreak 통신 프로토콜 종합 문서

**Phase 6-4** | 2026-04-24 | Phase 3 (펌웨어) + Phase 5 (DLL) 병합

---

## 1. 통신 프로토콜 개요

MiniFreak는 **3개의 독립적인 통신 채널**을 사용합니다. 각 채널은 목적과 대역폭이 다릅니다.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MiniFreak Communication Stack                     │
│                                                                     │
│  ┌───────────────┐  ┌──────────────────┐  ┌─────────────────────┐  │
│  │  CH 1: MIDI   │  │  CH 2: Collage   │  │  CH 3: DFU/RK      │  │
│  │  SysEx + CC   │  │  USB Bulk        │  │  Firmware Update    │  │
│  │               │  │  (Protobuf)      │  │                     │  │
│  │  실시간 파라   │  │  대용량 전송     │  │  펌웨어 플래싱     │  │
│  │  미터 제어     │  │  프리셋/샘플     │  │  부트로더          │  │
│  │               │  │  시스템 정보     │  │                     │  │
│  │  IF#3 MIDI    │  │  IF#0 Vendor     │  │  IF#1 WINUSB       │  │
│  │  EP02/EP81    │  │  EP83/EP04       │  │  (no endpoints)    │  │
│  │  64B/packet   │  │  64B/packet      │  │  Control xfer      │  │
│  │  ~3.1 KB/s    │  │  ~3.1 KB/s       │  │  variable          │  │
│  └───────┬───────┘  └────────┬─────────┘  └──────────┬──────────┘  │
│          │                   │                       │              │
│          │    USB 2.0 Full-Speed (12 Mbps, VID=0x1C75 PID=0x0602) │
│          └───────────────────┼───────────────────────┘              │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   MiniFreak HW     │
                    │   CM4 (MIDI/SysEx) │
                    │   CM7 (DSP)        │
                    └───────────────────┘
```

### 채널 비교

| 속성 | MIDI SysEx | Collage USB Bulk | DFU/RK |
|------|-----------|------------------|--------|
| **USB IF** | #3 (MIDI Streaming) | #0 (Vendor) | #1 (WINUSB) |
| **Endpoints** | EP02 OUT, EP81 IN | EP83 IN, EP04 OUT | Control |
| **프로토콜** | Arturia SysEx | Protobuf | TUSBAUDIO / Rockchip |
| **목적** | 실시간 파라미터 | 대용량 전송 | 펌웨어 업데이트 |
| **대역폭** | ~3.1 KB/s | ~3.1 KB/s | 펌웨어 크기에 따름 |
| **라이브러리** | WINMM.dll | libusb (dynamically loaded) | TUSBAUDIO.dll |
| **암호화** | 없음 | Security service (optional) | Hash 검증 |

---

## 2. 채널 1: MIDI SysEx 프로토콜

### 2.1 Arturia SysEx 기본 포맷

Phase 3 (펌웨어 역공학)과 Phase 5 (DLL 분석)이 **동일한 포맷**을 확인:

```
F0 00 20 6B [DeviceID] [MsgType] [Group/ParamIdx] [ValueLo] [ValueHi?] [Payload...] F7
│  └Arturia Mfr ID─┘  │           │               │           │           │
                      │           │               │           └─ 2-byte 타입만
                      │           │               └─ 0-127
                      │           └─ 메시지 타입 (2-37 또는 DLL 타입)
                      └─ 0x02=MiniFreak, 0x7F=Broadcast, 0x09=Extended
```

### 2.2 펌웨어 측 상태 머신 (Phase 3 — 상세)

**주소:** `FUN_0x08157278` (CM4)  
**구조:** 43-state TBH (Table Byte Handler) dispatch  
**처리:** 바이트 단위, 인터럽트 또는 폴링 기반

```
State Machine Flow:
  IDLE ──F0──→ S1 ──0x00──→ S2 ──0x20──→ S3 ──0x6B──→ S4
                                                          │
  S4 ──devID──→ S5 ──msgType──→ S6 ──paramIdx──→ S7 ──valueLo──→ S8
       │                              │                         │
       ├── devID=0x09 → Extended     └── type=0x42 →          └── valueHi → S9
       │    (47 bytes max)              override to 0x26           (types 3,4,7,11,12,13)
       │
       └── devID=0x7F → Broadcast

  S8/S9 → Dispatch by msg_type:
    ├── Standard (3-9,11,13-32,34) → state 0x21 (payload collection)
    ├── Counter (2,10,12,33,35) → store counter, reset (ACK)
    └── Mixed (36-37) → alternating handler
```

**State Struct 레이아웃 (Phase 3에서 확인):**

| Offset | 크기 | 필드 | 설명 |
|--------|------|------|------|
| +0x00 | 1 | state | 현재 FSM 상태 |
| +0x01 | 1 | sub_state | 4 = 2바이트 값 필요 |
| +0x02 | 1 | expected_dev_id | 기대 디바이스 ID |
| +0x04 | 2 | buffer_pos | 버퍼 위치 / 데이터 길이 |
| +0x06 | 2 | seq_counter | 시퀀스 카운터 |
| +0x08 | 1 | msg_type | 메시지 타입 (signed) |
| +0x09 | 1 | param_idx | 파라미터 인덱스 |
| +0x0A | 1 | value_byte | 값 바이트 |
| +0x0C | 2 | value_16 | 16비트 값 |
| +0x0E | 1 | bank_offset | 뱅크/오프셋 |
| +0x11-0x14 | 4 | data_bytes | 데이터 바이트 |
| +0x15.. | ~96B | buffer | 페이로드 버퍼 |
| +0x7A | 4 | arturia_id | `0x096B2000` (magic) |
| +0xAA | 1 | fw_data_count | 펌웨어 데이터 카운트 |
| +0xAB | 1 | fw_chunk_ctr | 펌웨어 청크 카운터 |
| +0xB4 | 4 | callback_ptr | MIDI 송신 콜백 포인터 |

### 2.3 메시지 타입: Phase 3 vs Phase 5 대조

Phase 3 (펌웨어)에서 36개 타입(2-37)을 식별했고, Phase 5 (DLL)에서는 3개 타입만 식별. **둘은 호환됨 — DLL은 상위 레벨 래퍼이므로 모든 타입을 사용하지 않음.**

| 타입 | Phase 3 (FW) | Phase 5 (DLL) | 통합 설명 |
|------|-------------|--------------|-----------|
| `0x02` | Counter-based ACK | **Parameter Get/Set** | ★ DLL에서 파라미터 제어에 사용. 펌웨어에서는 ACK 시퀀스. 양쪽 모두 dev=0x02 사용 |
| `0x03` | Standard (2-byte) | **RPN Group** | RPN/NRPN 파라미터, group=0x03 |
| `0x04` | Standard (2-byte) | **System Group** | 시스템 파라미터, group=0x04 |
| `0x06` | 7-bit unpacking | — | 8→7비트 변환 알고리즘 |
| `0x08` | Standard payload | **Parameter Alt** | 대체 채널 파라미터 |
| `0x0A` | Extended/FW | **Extended/FW** | 펌웨어/확장 그룹 (양쪽 일치) |
| `0x42` | Override → 0x26 | **Request/Query** | Broadcast(dev=0x7F) 요청. 양쪽 모두 확인 |
| 2-37 나머지 | 다양한 handler | — | 펌웨어 내부용. DLL에서 미사용 |

**핵심 발견:** DLL의 "Group" 필드는 펌웨어의 "ParamIdx" 필드와 **동일한 바이트 위치**에 매핑됨. DLL은 단지 상위레벨 추상화일 뿐, 바이너리 프로토콜은 동일.

### 2.4 DLL SysEx 템플릿 (Phase 5 — 코드에서 추출)

Phase 5에서 DLL x86-64 머신코드에서 직접 추출한 실제 SysEx 템플릿:

```
// 1. RPN Parameter Request
F0 00 20 6B 02 02 03 [param] F7
   │          │  │  └── group=0x03 (RPN)
   │          │  └── type=0x02 (Parameter)
   │          └── dev=0x02 (MiniFreak)

// 2. Broadcast Request
F0 00 20 6B 7F 42 02 [param_id] F7
   │          │  │  │  └── parameter ID
   │          │  │  └── group=0x02 (Parameter)
   │          │  └── type=0x42 (Request)
   │          └── dev=0x7F (Broadcast)

// 3. System Request
F0 00 20 6B 7F 42 04 [sys_param] F7
                  └── group=0x04 (System)

// 4. Extended/FW Request
F0 00 20 6B 7F 42 0A [ext_param] F7
                  └── group=0x0A (Extended)

// 5. Parameter Alternate Channel
F0 00 20 6B 02 08 03 [param] [value] F7
               │  │  └── group=0x03
               │  └── type=0x08 (Alt Channel)
               └── dev=0x02
```

### 2.5 7-bit 언패킹 알고리즘 (Phase 3 — msg_type 6 전용)

```
// 펌웨어 내부 8→7비트 변환 (MIDI 바이트 페이로드 → 8비트 값)
// FUN_0x0813D4E0 기반 재구성

void unpack_7bit(uint8_t* out, const uint8_t* midi_bytes, int count) {
    uint8_t sign_bits = midi_bytes[0];  // 첫 바이트 = 상위 비트 모음
    
    for (int i = 0; i < count && i < 6; i++) {
        uint8_t lo = midi_bytes[i + 1] & 0x7F;           // 하위 7비트
        uint8_t hi = (sign_bits >> (6 - i)) & 0x01;      // 상위 1비트
        out[i] = (hi << 7) | lo;                         // 8비트 값 복원
    }
}

// 예: sign_bits=0b11000000, bytes=[0x40, 0x7F, 0x00]
// → out[0] = (1<<7)|0x40 = 0xC0, out[1] = (1<<7)|0x7F = 0xFF, out[2] = 0x00
```

### 2.6 SysEx Builder (HW → Host, Phase 3)

```
// Builder 1: 6-Parameter (FUN_0x0813D8C4)
// F0 00 20 6B [dev] [counter] 0x48 0x03 [sign_bits] [p0&7F] [p1&7F] [p2&7F] [p3&7F] [p4&7F] [p5&7F] F7
// sign_bits packing: bit6=p0_sign, bit5=p1_sign, bit4=p2_sign, bit3=p3_sign, bit2=p4_sign, bit1=p5_sign

// Builder 2: Alternative (FUN_0x08135100)
// F0 00 20 6B [dev] [counter] 0x10 0x03 [sign_bits] [p0..p5] F7

// Builder 3: Minimal (FUN_0x08157BB8)
// F0 03 06 00 06 02 [d1] [d2] F7
// ★ Arturia 헤더 없는 최소 포맷 — 내부용?
```

### 2.7 MIDI CC 매핑 (Phase 3 — 161개, 펌웨어 주소 포함)

| CC# | 파라미터 | 펌웨어 핸들러 | Phase 5 DLL 대응 |
|-----|----------|-------------|-----------------|
| 0 | Bank Select MSB | `FUN_08166810` | Program Change |
| 1-6 | OSC1 (Type/Shape/Unison/Detune/Oct/Semi) | `FUN_08166810` | SysEx type=0x02 |
| 10-16 | OSC2 (Type/Shape/Unison/Detune/Oct/Semi/Mix) | `FUN_08166810` | SysEx type=0x02 |
| 20-21 | Mixer (Osc1/Osc2 Level) | `FUN_08166810` | SysEx type=0x02 |
| 24-32 | Filter (Cutoff/Reso/Env/KT/Type/Drive/Vel/Cutoff2) | `FUN_08166810` | SysEx type=0x02 |
| 38-50 | Env1+2 (A/D/S/R/Time/Loop/Vel) | `FUN_08166810` | SysEx type=0x02 |
| 53-62 | LFO1+2 (Rate/Shape/Amount/Phase/Sync) | `FUN_08166810` | SysEx type=0x02 |
| 64-66 | Pedals (Sustain/Portamento/Sostenuto) | `FUN_08166810` | — |
| 71-79 | FX A (Type + Params 1-8) | `FUN_08166810` | SysEx type=0x02 |
| 85 | FX B Type | `FUN_0817c670(CC-0x57)` | SysEx type=0x02 |
| 86-186 | FX Extended (101 params) | `FUN_0817c670(CC-0x57)` | SysEx type=0x02 |
| 193-204 | Macro 1-7 | `FUN_08166810` | SysEx type=0x02 |
| 120-123 | Mode (AllSoundOff/Reset/AllNotesOff) | `FUN_08166810` | — |

**CC 핸들러 함수:** `FUN_08166810` — 161개 CC를 switch/case 또는 테이블로 디스패치  
**FX 디스패처:** `FUN_0817c670(state, CC - 0x57)` — FX 전용 서브디스패처  
**NRPN 핸들러:** `FUN_081812B4` — 14-bit CC (MSB+LSB) 파라미터

### 2.8 MIDI 라우팅 (Phase 3 문자열 기반)

```
                 ┌─────────────┐
                 │  MIDI IN    │
                 │  (DIN/USB)  │
                 └──────┬──────┘
                        │
            ┌───────────▼───────────┐
            │  MIDI Router          │
            │  Modes:               │
            │  • USB Only           │
            │  • MIDI DIN Only      │
            │  • USB and MIDI DIN   │
            └───┬───────────────┬───┘
                │               │
        ┌───────▼──────┐ ┌─────▼──────┐
        │ "MIDI>Syn"   │ │ "SyncMidiIn"│
        │ Note/CC/SysEx│ │ Clock/Start│
        │ → DSP Engine │ │ → Sequencer│
        └──────────────┘ └────────────┘

        ┌──────────────┐ ┌──────────────┐
        │ "MNF_MidiOut"│ │ "SyncMidiOut"│
        │ MIDI THRU    │ │ Clock Output │
        └──────────────┘ └──────────────┘
```

---

## 3. 채널 2: Collage USB Bulk 프로토콜

### 3.1 아키텍처 (Phase 5 DLL 분석)

```
┌──────────────────────────────────────────────────────┐
│  MiniFreak V (Desktop)                               │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  Application Layer                             │  │
│  │  Preset Transfer / Firmware Update / Param Sync│  │
│  └──────────────────────┬─────────────────────────┘  │
│                         │                            │
│  ┌──────────────────────▼─────────────────────────┐  │
│  │  Collage Framework (Arturia::Collage)          │  │
│  │                                                │  │
│  │  ┌──────────────────────────────────────────┐  │  │
│  │  │  Protocol Layer                          │  │  │
│  │  │  ProtocolProtobuf  │  ProtocolRaw        │  │  │
│  │  │  (Google Protobuf) │  (Raw binary)       │  │  │
│  │  └──────────────────────────────────────────┘  │  │
│  │                         │                        │  │
│  │  ┌──────────────────────▼──────────────────┐   │  │
│  │  │  Service Layer (4 domains)              │   │  │
│  │  │  ┌──────────┐ ┌──────────────────────┐  │   │  │
│  │  │  │ Data     │ │ Resource            │  │   │  │
│  │  │  │ Service  │ │ Service             │  │   │  │
│  │  │  │          │ │                     │  │   │  │
│  │  │  │ ParamGet │ │ Store/Retrieve/     │  │   │  │
│  │  │  │ ParamSet │ │ Remove/List         │  │   │  │
│  │  │  │ Subscribe│ │                     │  │   │  │
│  │  │  └──────────┘ └──────────────────────┘  │   │  │
│  │  │  ┌──────────┐ ┌──────────────────────┐  │   │  │
│  │  │  │ System   │ │ Security            │  │   │  │
│  │  │  │ Service  │ │ Service             │  │   │  │
│  │  │  │          │ │                     │  │   │  │
│  │  │  │ Version  │ │ Authentication      │  │   │  │
│  │  │  │ Command  │ │ Encryption          │  │   │  │
│  │  │  │ Restart  │ │                     │  │   │  │
│  │  │  └──────────┘ └──────────────────────┘  │   │  │
│  │  └──────────────────────────────────────────┘  │  │
│  │                         │                        │  │
│  │  ┌──────────────────────▼──────────────────┐   │  │
│  │  │  Channel + Command Manager               │   │  │
│  │  │  Channel (multiplex)                     │   │  │
│  │  │  CollageCommandManager (dispatch)        │   │  │
│  │  │  BufferPriorityQueue (threaded I/O)      │   │  │
│  │  └──────────────────────────────────────────┘  │  │
│  │                         │                        │  │
│  │  ┌──────────────────────▼──────────────────┐   │  │
│  │  │  Transport Layer                         │   │  │
│  │  │  CommUsb (primary) │ CommTcp (debug)    │   │  │
│  │  └──────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────┘  │
│                         │                            │
│  ┌──────────────────────▼─────────────────────────┐  │
│  │  libusb (dynamically loaded)                   │  │
│  │  libusb_bulk_transfer(EP83/EP04, 64B)          │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
                         │
              USB Bulk (IF#0)
                         │
              ┌──────────▼──────────┐
              │  MiniFreak CM4      │
              │  (Collage handler)  │
              └─────────────────────┘
```

### 3.2 Protobuf 서비스 상세 (Phase 5)

#### Data Service — 실시간 파라미터 동기화

| 메시지 | 방향 | 설명 |
|--------|------|------|
| `DataParameterGetRequest` | VST→HW | 파라미터 값 요청 |
| `DataParameterGetResponse` | HW→VST | 파라미터 값 응답 |
| `DataParameterSetRequest` | VST→HW | 파라미터 값 설정 |
| `DataParameterSetResponse` | HW→VST | 설정 확인 |
| `DataParameterResetRequest` | VST→HW | 파라미터 기본값 리셋 |
| `DataParameterSubscribeRequest` | VST→HW | 변경 구독 |
| `DataParameterNotification` | HW→VST | 변경 알림 (push) |
| `DataApplicationSubscribeRequest` | VST→HW | 앱 데이터 구독 |
| `DataApplicationNotify` | HW→VST | 앱 상태 알림 |

#### Resource Service — 대용량 전송 (프리셋, 샘플)

| 메시지 | 방향 | 설명 |
|--------|------|------|
| `ResourceStoreRequest` | VST→HW | 리소스 저장 (프리셋/샘플) |
| `ResourceRetrieveRequest` | VST→HW | 리소스 조회 |
| `ResourceRemoveRequest` | VST→HW | 리소스 삭제 |
| `ResourceListRequest` | VST→HW | 목록 요청 |
| `ResourceItemInfo` | 양방향 | 메타데이터 |
| `ResourceItemType` | — | 타입 enum |
| `ResourceLocation` | — | 위치 정보 |
| `ResourceResult` | HW→VST | 작업 결과 |

#### System Service — 디바이스 관리

| 메시지 | 방향 | 설명 |
|--------|------|------|
| `SystemVersionRequest` | VST→HW | 펌웨어 버전 요청 |
| `SystemVersionInfo` | HW→VST | 버전 정보 |
| `SystemCommandExecuteRequest` | VST→HW | 시스템 명령 실행 |
| `SystemRestartRequest` | VST→HW | 디바이스 재부팅 |
| `SystemShutdownRequest` | VST→HW | 디바이스 종료 |
| `SystemStatusMemoryRequest` | VST→HW | 메모리 상태 |
| `SystemStatusStorageRequest` | VST→HW | 스토리지 상태 |
| `SystemStatusProcessorRequest` | VST→HW | CPU 상태 |

#### Security Service

| 메시지 | 방향 | 설명 |
|--------|------|------|
| `SecurityAuthenticationRequest` | VST→HW | 디바이스 인증 |
| `SecurityEncryption` | 양방향 | 암호화 설정 |
| `SecurityResult` | HW→VST | 인증 결과 |

### 3.3 Resource Transfer 초기화 시퀀스 (Phase 5)

DLL에서 `ResourceTransferer`가 사용하는 10단계 초기화:

```
  1. init communication channel       ── CommUsb 열기
  2. init command manager channel     ── CollageCommandManager 생성
  3. init data handler                ── Data Service 핸들러 등록
  4. init resource handler            ── Resource Service 핸들러 등록
  5. init resource control            ── Resource 컨트롤러 초기화
  6. init security handler            ── Security Service (optional)
  7. init system handler              ── System Service 등록
  8. init system handler sync         ── System 버전 확인
  9. add resource handler to msg handlers  ── 메시지 라우팅 등록
 10. start reception thread           ── 수신 스레드 시작
```

### 3.4 USB 디바이스 탐지 (Phase 5)

DLL의 USB 경로 패턴:
```
\\?\%*3[USBusb]#%*3[VIDvid]_%4hx&%*3[PIDpid]_%4hx&%s
```

libusb 함수 사용 목록:
```
libusb_init → libusb_get_device_list → libusb_get_device_descriptor
→ libusb_get_config_descriptor → libusb_open → libusb_claim_interface
→ libusb_bulk_transfer (EP83 IN / EP04 OUT)
→ libusb_hotplug_register_callback (hotplug 감지)
```

### 3.5 Collage vs MIDI SysEx — 언제 어떤 것을 사용하는가?

| 작업 | 프로토콜 | 이유 |
|------|----------|------|
| 파라미터 트위킹 (노브 돌리기) | MIDI CC | 낮은 지연, 실시간 |
| 프리셋 로드/세이브 | Collage Resource | 대용량 (0xD00바이트 × N) |
| 샘플 업로드 | Collage Resource | 메가바이트 단위 |
| 펌웨어 업데이트 | DFU/RKUpdater | 독립 채널 |
| 버전 확인 | Collage System | 구조화된 응답 |
| 파라미터 구독 (실시간 동기화) | Collage Data | Push 알림 |
| 프리셋 요청 (broadcast) | MIDI SysEx 0x42 | 단순 요청 |
| 디바이스 인증 | Collage Security | 암호화 필요 |

---

## 4. 채널 3: 펌웨어 업데이트 프로토콜

### 4.1 3가지 업데이트 경로 (Phase 5)

```
┌──────────────────────────────────────────────────────────────┐
│                    Firmware Update Paths                      │
│                                                              │
│  Path A: DFU (TUSBAUDIO)         Path B: Rockchip           │
│  ┌──────────────────────┐        ┌──────────────────┐       │
│  │ DFUUpdater           │        │ RKUpdater        │       │
│  │ IF#1 WINUSB          │        │ Serial Port      │       │
│  │ TUSBAUDIO API        │        │ Rockchip Loader  │       │
│  │                      │        │                  │       │
│  │ Commands:            │        │ Flow:            │       │
│  │  checkhash           │        │ 1. Find serial   │       │
│  │  install             │        │ 2. Reboot loader │       │
│  │  reboot              │        │ 3. Wait reboot   │       │
│  │  rebootloader        │        │ 4. Send commands │       │
│  │  reset_fw_from_dfu   │        │ 5. Finalize      │       │
│  │  set_master_vers     │        └──────────────────┘       │
│  └──────────────────────┘                                    │
│                                                              │
│  Path C: Collage                                             │
│  ┌──────────────────────┐                                    │
│  │ CollageUpdater       │                                    │
│  │ IF#0 Vendor Bulk     │                                    │
│  │ Protobuf Resource    │                                    │
│  │ Service              │                                    │
│  └──────────────────────┘                                    │
│                                                              │
│  공통:                                                       │
│  • Firmware package: info.json (productid 검증)              │
│  • Hash verification: "[dfu].checkhash"                      │
│  • ASC 통합: Protection::Onboarding::FirmwareUpdateFlowHandler│
│  • Factory reset: TUSBAUDIO_StartDfuRevertToFactoryImage    │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 TUSBAUDIO DFU API (Phase 5 — DLL import)

```c
// TUSBAUDIO.dll 함수 (10개)
TUSBAUDIO_GetDfuStatus(handle, &status);
TUSBAUDIO_GetFirmwareImage(handle, &image);
TUSBAUDIO_GetFirmwareImageSize(handle, &size);
TUSBAUDIO_LoadFirmwareImageFromBuffer(handle, buf, size);
TUSBAUDIO_LoadFirmwareImageFromFile(handle, path);
TUSBAUDIO_StartDfuDownload(handle);            // 펌웨어 다운로드 시작
TUSBAUDIO_StartDfuRevertToFactoryImage(handle); // 공장 초기화
TUSBAUDIO_StartDfuUpload(handle);              // 펌웨어 업로드
TUSBAUDIO_UnloadFirmwareImage(handle);
TUSBAUDIO_EndDfuProc(handle);
```

### 4.3 RKUpdater 시퀀스 (Phase 5)

```
1. RKUpdater::UpdateSetup
   ├─ Windows 레지스트리에서 시리얼 디바이스 검색
   ├─ 이미 로더 모드인지 확인
   └─ 필요시 로더 모드로 재부팅

2. RKUpdater::WaitRebootInLoader
   └─ 로더 디바이스 나타날 때까지 대기

3. RKUpdater::SendCommand
   └─ Collage 프로토콜로 업데이트 명령 전송

4. RKUpdater::UpdateTearDown
   └─ 업데이트 종료 처리
```

---

## 5. 프리셋 전송 프로토콜

### 5.1 프리셋 포맷 (Phase 2 + Phase 5)

| 포맷 | 크기 | 위치 | 프로토콜 |
|------|------|------|----------|
| HW Binary | 0xD00 바이트 (고정) | 펌웨어 플래시 | Collage Resource |
| .mnfx | 가변 (~10-50KB) | PC 디스크 | boost::serialization |
| .mnfdump | 가변 | PC 디스크 | 덤프 포맷 |

### 5.2 프리셋 변환 파이프라인 (Phase 5)

```
┌─────────────┐     HW Binary      ┌─────────────┐
│  MiniFreak  │ ◄═════════════════ │  MiniFreak  │
│  Hardware   │   Collage Resource │  V (VST)    │
│  0xD00 bin  │                    │  .mnfx      │
└─────────────┘                    └──────┬──────┘
                                          │
                          MiniFreakPresetHwVstConverter
                          ├─ ConvertPresetFromDataToSDK()  HW→VST
                          └─ ConvertPresetFromSDKToData()  VST→HW
                                          │
                                   ┌──────▼──────┐
                                   │  Local File  │
                                   │  System      │
                                   │  .mnfx files │
                                   └─────────────┘
```

### 5.3 프리셋 관련 DLL 클래스 (Phase 5)

| 클래스 | 역할 |
|--------|------|
| `MiniFreakPresetBrowserController` | HW 프리셋 브라우저 (뱅크 로드/업데이트/백업) |
| `MiniFreakPresetHwVstConverter` | HW ↔ VST 프리셋 변환 |
| `MiniFreakHardwarePresetsView` | HW 프리셋 GUI |
| `MiniFreakHardwareBackupsList` | 백업 관리 GUI |
| `MFVPresetConverter` | 프리셋 포맷 변환 |
| `LocalPresetManager` | 로컬 프리셋 관리 |
| `StorageController` | 샘플/웨이브테이블 스토리지 |

### 5.4 뱅크 관리 JSON (Phase 5)

```cpp
// DLL에서 사용하는 뱅크 메타데이터
struct HardwareBank {
    // JsonFile<HardwareBank>로 직렬화
    // 뱅크 이름, 프리셋 목록, 메타데이터
};
```

---

## 6. 통신 플로우 시나리오

### 6.1 VST ↔ HW 초기 연결

```
VST Plugin Start
│
├─ [1] USB Device Scan (libusb)
│   └─ VID=0x1C75, PID=0x0602 탐지
│
├─ [2] MIDI Port Open (WINMM)
│   └─ midiInOpen / midiOutOpen
│
├─ [3] Collage Init (10-step sequence)
│   ├─ CommUsb open (claim IF#0)
│   ├─ CollageCommandManager create
│   ├─ Data/Resource/System/Security handlers register
│   └─ Reception thread start
│
├─ [4] System Version Request (Collage)
│   └─ SystemVersionRequest → SystemVersionResponse
│       → firmware 4.0.1 확인
│
├─ [5] Security Authentication (Collage)
│   └─ SecurityAuthenticationRequest → SecurityResult
│
├─ [6] Parameter Subscribe (Collage)
│   └─ DataParameterSubscribeRequest (전체 파라미터)
│       → DataParameterNotification (push)
│
└─ [7] Preset Sync (Collage)
    └─ ResourceRetrieveRequest (현재 프리셋)
        → ResourceRetrieveResponse (0xD00 binary)
```

### 6.2 실시간 파라미터 편집 (VST 노브 → HW)

```
User turns VST knob (e.g., Cutoff)
│
├─ 방식 A: MIDI CC (빠름, 지연 ~1ms)
│   └─ midiOutShortMsg(hMidiOut, 0x091 | CC#24 | value)
│       → USB EP02 → HW MIDI handler FUN_08166810
│       → Shared SRAM → CM7 DSP reads next frame
│
└─ 방식 B: Collage DataParameterSet (구조화, 지연 ~10ms)
    └─ DataParameterSetRequest(param_id, value)
        → USB EP04 → HW Collage handler
        → Shared SRAM → CM7 DSP reads next frame
```

### 6.3 프리셋 전송 (VST → HW)

```
User clicks "Send to Hardware"
│
├─ [1] MiniFreakPresetHwVstConverter::ConvertPresetFromSDKToData()
│   └─ .mnfx (boost::serialization) → 0xD00 binary
│
├─ [2] ResourceStoreRequest(binary_data)
│   └─ USB EP04 → HW Collage Resource handler
│
├─ [3] ResourceStoreResponse(success)
│   └─ USB EP83 → VST
│
└─ [4] DataParameterNotification (프리셋 변경 알림)
    └─ VST UI 업데이트
```

### 6.4 펌웨어 업데이트

```
User clicks "Update Firmware"
│
├─ [1] Firmware download from Arturia server
│   └─ WININET.dll HTTP GET
│
├─ [2] info.json productid 검증
│
├─ [3] Path 선택 (DFU / RK / Collage)
│   ├─ DFU: TUSBAUDIO_LoadFirmwareImageFromFile()
│   │   → TUSBAUDIO_StartDfuDownload()
│   │   → TUSBAUDIO_EndDfuProc()
│   │   → Device reboot
│   │
│   ├─ Rockchip: Registry scan → Serial reboot → Commands
│   │
│   └─ Collage: ResourceStoreRequest(firmware_data)
│
└─ [4] Verification
    └─ [dfu].checkhash → SystemVersionRequest → confirm
```

---

## 7. 미해결 프로토콜 질문

| 질문 | 상태 | 필요한 것 |
|------|------|-----------|
| Collage Protobuf .proto 파일 | ❌ | DLL에서 Protobuf field numbers 재구성 필요 |
| 파라미터 ID ↔ SysEx 바이트 정확한 매핑 | ⚠️ 부분 | MIDI 캡처 + SysEx 로그 비교 |
| SIBP (Serial Interface Binary Protocol) 상세 | ❌ | DLL 바이너리에서 Protobuf 정의 추출 |
| 9종 캘리브레이션 SysEx | ❌ | MIDI 캡처 필요 |
| UI MCU 통신 프로토콜 | ❌ | I2C/SPI 프로브 또는 JTAG 트레이스 |
| Security Service 암호화 방식 | ❌ | CRYPT32.dll 사용 분석 |
| nanopb 사용 위치 | ❌ | 펌웨어 내부 통신 (USB SysEx 아님) |

---

## 8. Phase 3 ↔ Phase 5 데이터 일치성 검증

| 항목 | Phase 3 (FW) | Phase 5 (DLL) | 일치? |
|------|-------------|--------------|-------|
| Arturia Mfr ID | `0x00 0x20 0x6B` | `0x00 0x20 0x6B` (84 occurrences) | ✅ |
| Device ID | `0x02` | `0x02` | ✅ |
| Broadcast ID | `0x7F` | `0x7F` | ✅ |
| SysEx Wire Format | `F0 00 20 6B dev type param val F7` | 동일 | ✅ |
| Message Type 0x42 | Override → 0x26 | Request/Query | ✅ (양쪽 관점) |
| Type 0x02 | Counter ACK | Parameter Get/Set | ✅ (양쪽 관점) |
| Type 0x08 | Standard payload | Parameter Alt | ✅ |
| Group 0x03 | — | RPN/NRPN | ✅ |
| Group 0x04 | — | System | ✅ |
| Group 0x0A | — | Extended/FW | ✅ |
| MIDI CC 161개 | FUN_08166810 switch | — | ✅ (FW만) |
| NRPN | FUN_081812B4 | — | ✅ (FW만) |
| 43-state FSM | FUN_08157278 | — | ✅ (FW만) |
| Collage Protocol | — | 4 service domains | ✅ (DLL만) |
| DFU/RKUpdater | — | 3 update paths | ✅ (DLL만) |
