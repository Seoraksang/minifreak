# Arturia MiniFreak — MIDI Implementation Chart

**Phase 6-3** | 2026-04-24 | 펌웨어 역공학 기반

---

## 1. MIDI Device Identity

| 항목 | 값 |
|------|-----|
| **Manufacturer** | Arturia (`0x00 0x20 0x6B` / USB short `0x1C 0x75`) |
| **Device Name** | "MiniFreak" |
| **Family** | Synthesizer |
| **Model ID** | `0x02` (SysEx), `0x0602` (USB PID) |
| **Firmware** | 4.0.1 (`0x4001`) |
| **USB VID** | `0x1C75` |
| **USB PID** | `0x0602` |
| **USB MIDI Jacks** | IN: Embedded#1, External#2 / OUT: Embedded#3, External#4 |

---

## 2. Channel Messages

### 2.1 Note Messages

| Status | Data 1 | Data 2 | 기능 | 비고 |
|--------|--------|--------|------|------|
| `0x9n` | Key (0-127) | Velocity (1-127) | **Note On** | 12-voice poly, vel→VCA+filter |
| `0x8n` | Key (0-127) | Velocity (0) | **Note Off** | Release envelope triggers |
| `0xAn` | Key (0-127) | Pressure (0-127) | **Poly Aftertouch** | Per-note pressure → mod matrix |
| `0xDn` | — | Pressure (0-127) | **Channel Aftertouch** | Global AT → mod matrix |

### 2.2 Control Change

| CC# | Hex | 파라미터 | 범위 | 기본 | 비고 |
|-----|-----|----------|------|------|------|
| **0** | 0x00 | Bank Select MSB | 0-127 | — | 프리셋 뱅크 선택 |
| **1** | 0x01 | Osc1 Type/Waveform | 0-127 | — | 11 타입 |
| **2** | 0x02 | Osc1 Shape/PWM | 0-127 | — | |
| **3** | 0x03 | Osc1 Unison | 0-127 | — | |
| **4** | 0x04 | Osc1 Unison Detune | 0-127 | — | |
| **5** | 0x05 | Osc1 Octave | 0-127 | — | |
| **6** | 0x06 | Osc1 Semitone | 0-127 | — | |
| **10** | 0x0A | Osc2 Type/Waveform | 0-127 | — | 30 타입 |
| **11** | 0x0B | Osc2 Shape/PWM | 0-127 | — | |
| **12** | 0x0C | Osc2 Unison | 0-127 | — | |
| **13** | 0x0D | Osc2 Unison Detune | 0-127 | — | |
| **14** | 0x0E | Osc2 Octave | 0-127 | — | |
| **15** | 0x0F | Osc2 Semitone | 0-127 | — | |
| **16** | 0x10 | Osc2 Amount/Mix | 0-127 | — | |
| **20** | 0x14 | Osc1 Level | 0-127 | — | Mixer |
| **21** | 0x15 | Osc2 Level | 0-127 | — | Mixer |
| **24** | 0x18 | Filter Cutoff | 0-127 | — | |
| **25** | 0x19 | Filter Resonance | 0-127 | — | |
| **26** | 0x1A | Filter Env Amount | 0-127 | — | |
| **27** | 0x1B | Filter Key Tracking | 0-127 | — | |
| **29** | 0x1D | Filter Type | 0-127 | — | Multi/Surgeon/Comb/Phaser |
| **30** | 0x1E | Filter Drive | 0-127 | — | |
| **31** | 0x1F | Filter Env Velocity | 0-127 | — | |
| **32** | 0x20 | Filter Cutoff 2 | 0-127 | — | |
| **38** | 0x26 | Env1 Attack | 0-127 | — | |
| **39** | 0x27 | Env1 Decay | 0-127 | — | |
| **40** | 0x28 | Env1 Sustain | 0-127 | — | |
| **41** | 0x29 | Env1 Release | 0-127 | — | |
| **42** | 0x2A | Env1 Time | 0-127 | — | |
| **43** | 0x2B | Env1 Loop | 0-127 | — | |
| **44** | 0x2C | Env1 Velocity | 0-127 | — | |
| **45** | 0x2D | Env2 Attack | 0-127 | — | |
| **46** | 0x2E | Env2 Decay | 0-127 | — | |
| **47** | 0x2F | Env2 Sustain | 0-127 | — | |
| **48** | 0x30 | Env2 Release | 0-127 | — | |
| **49** | 0x31 | Env2 Time | 0-127 | — | |
| **50** | 0x32 | Env2 Velocity | 0-127 | — | |
| **53** | 0x35 | LFO1 Rate | 0-127 | — | |
| **54** | 0x36 | LFO1 Shape | 0-127 | — | |
| **55** | 0x37 | LFO1 Amount | 0-127 | — | |
| **56** | 0x38 | LFO1 Phase | 0-127 | — | |
| **57** | 0x39 | LFO1 Sync | 0-127 | — | |
| **60** | 0x3C | LFO2/Mod Rate | 0-127 | — | |
| **61** | 0x3D | LFO2/Mod Shape | 0-127 | — | |
| **62** | 0x3E | LFO2/Mod Amount | 0-127 | — | |
| **64** | 0x40 | Sustain Pedal | 0-63/64-127 | — | <64=off, ≥64=on |
| **65** | 0x41 | Portamento | 0-127 | — | |
| **66** | 0x42 | Sostenuto | 0-63/64-127 | — | |
| **71** | 0x47 | FX A Type | 0-127 | — | |
| **72** | 0x48 | FX A Param 1 | 0-127 | — | |
| **73** | 0x49 | FX A Param 2 | 0-127 | — | |
| **74** | 0x4A | FX A Param 3 | 0-127 | — | |
| **75** | 0x4B | FX A Param 4 | 0-127 | — | |
| **76** | 0x4C | FX A Param 5 | 0-127 | — | |
| **77** | 0x4D | FX A Param 6 | 0-127 | — | |
| **78** | 0x4E | FX A Param 7 | 0-127 | — | |
| **79** | 0x4F | FX A Param 8 | 0-127 | — | |
| **85** | 0x55 | FX B Type | 0-127 | — | |
| **86-186** | 0x56-0xBA | FX Extended | 0-127 | — | 101개 FX 파라미터 (CC-86 인덱스) |
| **193** | 0xC1 | Macro 1 | 0-127 | — | |
| **195** | 0xC3 | Macro 2 | 0-127 | — | |
| **196** | 0xC4 | Macro 3 | 0-127 | — | |
| **197** | 0xC5 | Macro 4 | 0-127 | — | |
| **198** | 0xC6 | Macro 5 | 0-127 | — | |
| **202** | 0xCA | Macro 6 | 0-127 | — | |
| **204** | 0xCC | Macro 7 | 0-127 | — | |
| **120** | 0x78 | All Sound Off | — | — | |
| **121** | 0x79 | Reset All Controllers | — | — | |
| **123** | 0x7B | All Notes Off | — | — | |

**총 CC 파라미터: 161개**

### 2.3 Pitch Bend

| Status | Data | 범위 | 기능 |
|--------|------|------|------|
| `0xE0` | LSB, MSB | -2~+2 반음 (default) | 피치 벤드 (Bend Range 조절 가능) |

### 2.4 Program Change

| Status | Data | 기능 |
|--------|------|------|
| `0xCn` | 0-127 | 프리셋 선택 (512 슬롯 중 128) |

### 2.5 NRPN

| MSB CC | LSB CC | Data Entry CC | 기능 |
|--------|--------|---------------|------|
| 0x63 | 0x62 | 0x06 | NRPN 파라미터 제어 (14-bit) |
| — | — | 0x26 | Data Increment |
| — | — | 0x26 | Data Decrement |

NRPN handler: `FUN_0x081812B4` (CM4 펌웨어)

---

## 3. SysEx Messages

### 3.1 Arturia SysEx Header

```
F0 00 20 6B [DeviceID] [MsgType] [ParamIdx] [ValueLo] [ValueHi?] [Payload...] F7
│  └Arturia Mfr ID─┘
```

| 바이트 | 의미 | 값 |
|--------|------|-----|
| `0xF0` | SysEx Start | — |
| `0x00 0x20 0x6B` | Arturia Manufacturer ID | 고정 |
| `[DeviceID]` | 디바이스 ID | `0x02` = MiniFreak, `0x7F` = Broadcast |
| `[MsgType]` | 메시지 타입 | 2-37 (하단 표 참조) |
| `[ParamIdx]` | 파라미터 인덱스 | 0-127 |
| `[ValueLo]` | 값 하위 7비트 | 0-127 |
| `[ValueHi]` | 값 상위 7비트 | 타입 3,4,7,11,12,13에서만 사용 |
| `0xF7` | SysEx End | — |

### 3.2 SysEx Message Types

| Type | Handler | 카테고리 | 설명 |
|------|---------|----------|------|
| **2** | Counter-based | ACK | 시퀀스 번호 저장 |
| **3** | Standard | Param | 2바이트 값 파라미터 |
| **4** | Standard | Param | 2바이트 값 파라미터 |
| **5** | Standard | Param | 파라미터 데이터 |
| **6** | Standard | Param | 7-bit 언패킹 알고리즘 (8→7비트 변환) |
| **7** | Standard | Param | 2바이트 값 파라미터 |
| **8** | Standard | Param | 파라미터 대체 채널 |
| **9** | Standard | Param | 파라미터 |
| **10** | Counter-based | ACK | 특수 카운터 |
| **11** | Standard | Param | 2바이트 값 파라미터 |
| **12** | Counter-based | ACK | 2바이트 값 카운터 |
| **13** | Standard | Param | 2바이트 값 파라미터 |
| **14-32** | Standard | Param | 페이로드 수집 |
| **33** | Counter-based | ACK | 카운터 |
| **34** | Standard | Param | 페이로드 |
| **35** | Counter-based | ACK | 카운터 |
| **36-37** | Mixed | — | 교차 핸들러 |
| **0x42** | Override | Request | 요청/쿼리 (→type 0x26 확장) |

### 3.3 SysEx Builder (HW → Host)

```
6-Parameter Format (FUN_0x0813D8C4):
  F0 00 20 6B [dev] [counter] 0x48 0x03 [sign_bits] [p0&0x7F] [p1&0x7F] [p2&0x7F] [p3&0x7F] [p4&0x7F] [p5&0x7F] F7
  sign_bits: bit6=p0, bit5=p1, bit4=p2, bit3=p3, bit2=p4, bit1=p5

Alternative Format (FUN_0x08135100):
  F0 00 20 6B [dev] [counter] 0x10 0x03 [sign_bits] [p0..p5] F7

Minimal (FUN_0x08157BB8):
  F0 03 06 00 06 02 [d1] [d2] F7
```

### 3.4 Universal SysEx

| ID | 기능 |
|----|------|
| `0x7E` | Universal SysEx (state 0x1F) |
| `0x7F` | Broadcast Device ID |

### 3.5 Special Messages

| 기능 | 설명 |
|------|------|
| Device ID `0x09` | Extended data collection (47 bytes max) |
| Type `0x42` | Request → overrides to type `0x26` |
| Byte `0x5A` | Firmware chunk counter (state 0x25) |
| Byte[7] == `0x49` | Secondary Arturia check in MIDI input |

---

## 4. System Exclusive (대분류)

### 4.1 DLL에서 식별된 SysEx Groups

| Group | Hex | 설명 | Phase 5 DLL 분석 |
|-------|-----|------|-------------------|
| Parameter | 0x02 | 파라미터 Get/Set | Targeted (dev=0x02) |
| RPN/NRPN | 0x03 | RPN 파라미터 | — |
| System | 0x04 | 시스템 파라미터 | — |
| Extended/FW | 0x0A | 펌웨어/확장 | — |

### 4.2 DLL에서 식별된 SysEx Types

| Type | Hex | 설명 |
|------|-----|------|
| Parameter Set | 0x02 | 파라미터 설정 |
| Parameter Alt | 0x08 | 대체 채널 |
| Request | 0x42 | 요청/쿼리 (broadcast) |

---

## 5. MIDI Clock & Sync

| 메시지 | Status | 기능 |
|--------|--------|------|
| Clock | 0xF8 | MIDI 클럭 (24 PPQN) |
| Start | 0xFA | 시퀀서 시작 |
| Continue | 0xFB | 시퀀서 계속 |
| Stop | 0xFC | 시퀀서 정지 |
| Song Pos | 0xF2 | 곡 위치 포인터 |

**MIDI 라우팅 모드:**
- "USB Only"
- "MIDI DIN Only"
- "USB and MIDI DIN"

**관련 문자열:**
- "MIDI>Syn", "MNF_MidiOut", "MIDI Seq/Synth"
- "MIDI To", "MIDI From"
- "SyncMidiIn", "SyncMidiOut"
- "MiniFreak MIDI 3 In/Out", "MiniFreak MIDI 4 In/Out"

---

## 6. USB MIDI Endpoints

| EP | 방향 | Type | 크기 | 기능 |
|----|------|------|------|------|
| EP 0x02 | OUT | Bulk | 64B | MIDI Out → Host (Embedded TX) |
| EP 0x81 | IN | Bulk | 64B | MIDI In ← Host (External RX) |

**MIDI Jack 매핑:**
- Cable 0: Embedded Out → Host In (EP 0x02)
- Cable 1: External In → Host In (EP 0x81)

---

## 7. MIDI Handler Functions (펌웨어 주소)

| 주소 | 이름 | 설명 |
|------|------|------|
| `0x08157278` | `sysex_state_machine` | 43-state 바이트 단위 SysEx 파서 |
| `0x0815770C` | `sysex_dev9_handler` | Device ID=9 확장 모드 |
| `0x0815747A` | `sysex_dispatch` | msg_type 2-37 PC-relative 디스패치 |
| `0x08157810` | `midi_input_handler` | SysEx 수신 (0x49 체크) |
| `0x0813D8C4` | `sysex_builder_6param` | 6-param SysEx 빌드 (0x4003) |
| `0x08135100` | `sysex_builder_alt` | 대체 SysEx 빌드 (0x1003) |
| `0x08157BB8` | `sysex_send_minimal` | 최소 SysEx 전송 |
| `0x0813D4E0` | `sysex_data_unpack` | 파라미터 언패킹 (TBB) |
| `0x08166810` | `midi_cc_handler` | CC → 파라미터 매핑 (161 CCs) |
| `0x08158A38` | `midi_handler_2` | 보조 파라미터 핸들러 |
| `0x081812B4` | `nrpn_handler` | NRPN 파라미터 핸들러 |
| `0x08189904` | `seq_arp_handler` | 시퀀서/아르페지에이터 핸들러 |
