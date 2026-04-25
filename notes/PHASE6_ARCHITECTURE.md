# MiniFreak 종합 시스템 아키텍처

**Phase 6-1** | 2026-04-24 | Phase 1~5 분석 결과 통합

---

## 1. 시스템 아키텍처 (ASCII)

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                  Arturia MiniFreak — Complete System Architecture              ║
║                    Phase 1-5 Reverse Engineering Results                       ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║  ┌──────────────────────────────────────────────────────────────────────┐      ║
║  │              MiniFreak V Desktop Software (PC/Mac)                   │      ║
║  │  ┌─────────────────────┐  ┌──────────────────────────────────────┐  │      ║
║  │  │  VST3 Plugin        │  │  Firmware Updater                   │  │      ║
║  │  │  JUCE 7.7.5         │  │  ├─ DFU (TUSBAUDIO API)            │  │      ║
║  │  │  Intel IPP DSP      │  │  ├─ Rockchip (RKUpdater)           │  │      ║
║  │  │  28.9MB (.vst3)     │  │  └─ Collage (Protobuf USB Bulk)   │  │      ║
║  │  └────────┬────────────┘  └──────────────────┬───────────────────┘  │      ║
║  │           │                                  │                      │      ║
║  │  ┌────────▼──────────────────────────────────▼───────────────────┐  │      ║
║  │  │  Communication Layer                                         │  │      ║
║  │  │  ┌──────────────────┐  ┌─────────────────────────────────┐   │  │      ║
║  │  │  │  MIDI SysEx      │  │  Collage Protocol               │   │  │      ║
║  │  │  │  WinMM API       │  │  libusb (dynamically loaded)    │   │  │      ║
║  │  │  │  161 CC mappings │  │  Protobuf over USB Bulk         │   │  │      ║
║  │  │  │  msg_type 2-37   │  │  4 service domains:             │   │  │      ║
║  │  │  │  7-bit packing   │  │    Data / Resource / System /   │   │  │      ║
║  │  │  └────────┬─────────┘  │    Security                     │   │  │      ║
║  │  └───────────┼────────────└──────────────┬──────────────────┘   │  │      ║
║  └──────────────┼───────────────────────────┼──────────────────────┘  │      ║
║                 │                           │                          │      ║
║  ┌──────────────▼───────────────────────────▼──────────────────────┐  │      ║
║  │                   USB 2.0 Full-Speed                            │  │      ║
║  │              VID=0x1C75  PID=0x0602  bcdDevice=0x4001           │  │      ║
║  │  ┌──────────────┐ ┌──────────┐ ┌───────────┐ ┌───────────────┐  │  │      ║
║  │  │ IF#0 Vendor  │ │ IF#1     │ │ IF#2      │ │ IF#3 MIDI     │  │  │      ║
║  │  │ Bulk IN/OUT  │ │ WINUSB   │ │ Audio Ctrl│ │ Streaming     │  │  │      ║
║  │  │ Collage/     │ │ DFU      │ │ (header)  │ │ EP02 OUT      │  │  │      ║
║  │  │ Preset Sync  │ │ Update   │ │           │ │ EP81 IN       │  │  │      ║
║  │  └──────┬───────┘ └────┬─────┘ └───────────┘ └──────┬────────┘  │  │      ║
║  └─────────┼──────────────┼────────────────────────────┼───────────┘  │      ║
╠════════════│══════════════│════════════════════════════│══════════════╣
║            │              │                            │              ║
║  ┌─────────▼──────────────▼────────────────────────────▼───────────┐  │      ║
║  │              MiniFreak Hardware (STM32H745/747)                  │  │      ║
║  │                                                                  │  │      ║
║  │  ┌────────────────────────────┐  ┌──────────────────────────┐   │  │      ║
║  │  │  CM7 Core — Audio DSP     │  │  CM4 Core — I/O Manager  │   │  │      ║
║  │  │  (Cortex-M7 @ 480MHz)     │  │  (Cortex-M4 @ 240MHz)    │   │  │      ║
║  │  │                            │  │                          │   │  │      ║
║  │  │  ★ No peripheral access   │  │  ★ Direct HW registers   │   │  │      ║
║  │  │  (indirect only)          │  │                          │   │  │      ║
║  │  │                            │  │  FUN_08121cfc (30 inits) │   │  │      ║
║  │  │  Signal Chain:            │  │                          │   │  │      ║
║  │  │  ┌──────────────────┐     │  │  Peripherals:            │   │  │      ║
║  │  │  │  OSC Engine      │     │  │  ┌──────────────────┐   │   │  │      ║
║  │  │  │  13 types        │◄────┤──┤  │  SAI2 (48kHz)    │   │   │  │      ║
║  │  │  │  Plaits-based    │     │  │  │  ChA: PE4/5/6    │   │   │  │      ║
║  │  │  │  vtable dispatch │     │  │  │  ChB: PD11/12/13 │   │   │  │      ║
║  │  │  └────────┬─────────┘     │  │  └────────┬─────────┘   │   │  │      ║
║  │  │           │               │  │           │              │   │  │      ║
║  │  │  ┌────────▼─────────┐     │  │  ┌────────▼─────────┐   │   │  │      ║
║  │  │  │  VCF (Filter)    │     │  │  │  DMA2            │   │   │  │      ║
║  │  │  │  Multi/Surgeon/  │     │  │  │  Stream 0 (SAI2A) │   │   │  │      ║
║  │  │  │  Comb/Phaser     │     │  │  │  Stream 4 (SAI2B) │   │   │  │      ║
║  │  │  └────────┬─────────┘     │  │  │  Stream 7 (Ctrl)  │   │   │  │      ║
║  │  │           │               │  │  └────────┬─────────┘   │   │  │      ║
║  │  │  ┌────────▼─────────┐     │  │           │              │   │  │      ║
║  │  │  │  VCA → Mixer     │     │  │  ┌────────▼─────────┐   │   │  │      ║
║  │  │  │  12-voice poly   │     │  │  │  DAC/ADC (?SPI)  │   │   │  │      ║
║  │  │  └────────┬─────────┘     │  │  │  ★ Chip unknown  │   │   │  │      ║
║  │  │           │               │  │  └────────┬─────────┘   │   │  │      ║
║  │  │  ┌────────▼─────────┐     │  │           │              │   │  │      ║
║  │  │  │  FX Send Bus     │     │  │  ┌────────▼─────────┐   │   │  │      ║
║  │  │  │  3 FX slots      │────►│──┤  │  MIDI/SysEx      │   │   │  │      ║
║  │  │  └──────────────────┘     │  │  │  43-state FSM    │   │   │  │      ║
║  │  │                            │  │  │  CC→Param (161)  │   │   │  │      ║
║  │  │  Top DSP Functions:        │  │  └──────────────────┘   │   │  │      ║
║  │  │  FUN_080359f4 (18KB)      │  │                          │   │  │      ║
║  │  │  FUN_0803e6f8 (10KB)      │  │  Main Loop:              │   │  │      ║
║  │  │  FUN_080321d4 (8KB)       │  │  FUN_081a1650 (infinite) │   │  │      ║
║  │  │  float+NEON+VectorFloat   │  │                          │   │  │      ║
║  │  │  295 functions total      │  │  Sync:                   │   │  │      ║
║  │  └────────────┬───────────────┘  │  HSEM + DMB barrier     │   │  │      ║
║  │               │                  └────────────┬─────────────┘   │  │      ║
║  │         ┌─────┴──────────────┐               │                  │  │      ║
║  │         │  Shared Memory     │◄──────────────┘                  │  │      ║
║  │         │  (AXI SRAM/DTCM)  │                                  │  │      ║
║  │         │  Audio buffers     │                                  │  │      ║
║  │         │  Parameter state   │                                  │  │      ║
║  │         └────────────────────┘                                  │  │      ║
║  │                                                                │  │      ║
║  │  ┌─────────────────────────────────────────────────────────┐   │  │      ║
║  │  │  FX DSP Core (Separate Binary, 120KB)                  │   │  │      ║
║  │  │  Target: DSP56362 | No STM32 peripheral access         │   │  │      ║
║  │  │  Chorus | Phaser | Flanger | Reverb | Distortion | Delay│   │  │      ║
║  │  └──────────────────────────┬──────────────────────────────┘   │  │      ║
║  │                             │                                  │  │      ║
║  │  ┌──────────────────────────┼──────────────────────────────┐   │  │      ║
║  │  │  UI Subsystem (4 Independent MCUs)                      │   │  │      ║
║  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │  │      ║
║  │  │  │ ui_screen│ │ ui_matrix│ │ ui_ribbon│ │ ui_kbd   │   │   │  │      ║
║  │  │  │ 172KB    │ │ 68KB     │ │ 68KB     │ │ 44KB     │   │   │  │      ║
║  │  │  │ OLED     │ │ Buttons  │ │ Touch    │ │ Keybed   │   │   │  │      ║
║  │  │  │ Display  │ │ + LEDs   │ │ Strip    │ │ + Vel/AT │   │   │  │      ║
║  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │  │      ║
║  │  └─────────────────────────────────────────────────────────┘   │  │      ║
║  │                                                                │  │      ║
║  └────────────────────────────────────────────────────────────────┘  │      ║
║                                                                       │      ║
║  ┌────────────────────────────────────────────────────────────────┐  │      ║
║  │  Analog Signal Path                                           │  │      ║
║  │                                                                │  │      ║
║  │  Osc (Digital) ──► DAC ──► VCF (Analog, Curtis?) ──► VCA     │  │      ║
║  │                                                  │            │  │      ║
║  │  Audio Out ◄─────────────────────────────────────┘            │  │      ║
║  │                                                                │  │      ║
║  │  ★ DAC/ADC chip: NOT identified (no chip names in firmware)  │  │      ║
║  │  ★ VCF type: Curtis CEM3372/3379 suspected (physical inspect)│  │      ║
║  └────────────────────────────────────────────────────────────────┘  │      ║
║                                                                       │      ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 2. 바이너리 맵

| # | 파일 | 크기 | 코어 | 역할 | 함수 수 |
|---|------|------|------|------|---------|
| 0 | `main_CM4` | 608KB | Cortex-M4 | 페리페럴 관리, DMA, GPIO, MIDI SysEx FSM, SAI 48kHz | ~수백개 |
| 1 | `main_CM7` | 512KB | Cortex-M7 | 오디오 DSP (float/NEON), 오실레이터 엔진, 필터, VCA | 295개 |
| 2 | `fx` | 120KB | DSP56362? | 디지털 FX 처리 (Chorus, Phaser, Reverb, Delay 등) | 별도 |
| 3 | `ui_screen` | 172KB | 별도 MCU | OLED 디스플레이 컨트롤 | 소형 |
| 4 | `ui_matrix` | 68KB | 별도 MCU | 버튼 매트릭스 + LED | 소형 |
| 5 | `ui_ribbon` | 68KB | 별도 MCU | 터치스트립 | 소형 |
| 6 | `ui_kbd` | 44KB | 별도 MCU | 키베드 스캔 + 벨로시티/애프터터치 | 소형 |

**Base Address:** CM4 = `0x08120000` (Flash Bank 2), CM7 = `0x08000000` (Flash Bank 1)

---

## 3. USB 인터페이스 맵

| IF# | Class | Endpoints | 용도 | 프로토콜 |
|-----|-------|-----------|------|----------|
| 0 | 0xFF (Vendor) | EP83 IN (Bulk), EP04 OUT (Bulk) | Collage 프리셋/펌웨어 전송 | Protobuf over USB Bulk |
| 1 | 0xFE (WINUSB) | None | DFU 펌웨어 업데이트 | TUSBAUDIO API |
| 2 | 0x01 (Audio Ctrl) | None | UAC1 헤더 | MIDI_HEADER bcdMSC=0x0901 |
| 3 | 0x01/0x03 (MIDI) | EP02 OUT, EP81 IN | USB MIDI | Class-Compliant MIDI |

**Device:** VID=0x1C75 (Arturia), PID=0x0602 (MiniFreak), bcdDevice=0x4001

---

## 4. 통신 프로토콜 스택

### 4.1 MIDI SysEx (실시간 파라미터 제어)

```
Wire:  F0 00 20 6B [DevID] [MsgType] [ParamIdx] [ValueLo] [ValueHi?] [Payload...] F7
       │  │  │  │   │         │         │           │           │
       │  Arturia Mfr ID   0x02=MF   2-37       0-127       7-bit packed
       │                                      │
       │  Two handler categories:             └─ Types 3,4,7,11,12,13 = 2-byte
       │  Standard (3-9,11,13-32,34) → payload collection
       │  Counter-based (2,10,12,33,35) → ACK sequence
       │
       └─ 43-state FSM (0x08157278), byte-by-byte parser
```

**SysEx Builder (HW→Host):**
```
6-Param:  F0 00 20 6B [dev] [counter] 0x48 0x03 [sign] [p0..p5&0x7F] F7
Alt:      F0 00 20 6B [dev] [counter] 0x10 0x03 [sign] [p0..p5&0x7F] F7
Minimal:  F0 03 06 00 06 02 [d1] [d2] F7
```

**MIDI CC → Parameter (161개):**

| CC 범위 | 파라미터 그룹 | 예시 |
|---------|-------------|------|
| 1-6 | OSC1 | Type, Shape, Unison, Detune, Octave, Semitone |
| 10-16 | OSC2 | Type, Shape, Unison, Detune, Octave, Semitone, Mix |
| 20-21 | Mixer | Osc1 Level, Osc2 Level |
| 24-32 | Filter | Cutoff, Resonance, EnvAmt, KeyTrack, Type, Drive |
| 38-50 | Envelopes | Env1/2 A/D/S/R, Time, Loop, Velocity |
| 53-62 | LFOs | LFO1/2 Rate, Shape, Amount, Phase, Sync |
| 71-79 | FX A | Type, Param1-8 |
| 86-186 | FX Extended | 101개 FX 파라미터 (CC-86 인덱스) |
| 193-204 | Macros | Macro 1-7 |

### 4.2 Collage Protocol (대용량 전송)

```
┌─────────────────────────────────────────┐
│  MiniFreak V Plugin                     │
│  ┌──────────────────────────────────┐   │
│  │  Collage Framework               │   │
│  │  ├─ Data Service                 │   │
│  │  │  ParameterGet/Set/Reset/      │   │
│  │  │  Subscribe/Unsubscribe/       │   │
│  │  │  Notification                 │   │
│  │  ├─ Resource Service             │   │
│  │  │  Store/Retrieve/Remove/List   │   │
│  │  ├─ System Service               │   │
│  │  │  Version/Command/Restart/     │   │
│  │  │  Shutdown/Memory/CPU/Storage  │   │
│  │  └─ Security Service             │   │
│  │     Authentication/Encryption    │   │
│  └──────────────┬───────────────────┘   │
│                 │ libusb                │
│                 ▼                       │
│  USB Bulk Transfer (EP83/EP04)          │
└─────────────────────────────────────────┘
```

**초기화 시퀀스:** 10단계 (comm channel → command manager → data handler → resource handler → resource control → security → system → system sync → add handlers → start reception thread)

---

## 5. 오디오 신호 경로

### 5.1 디지털 신호 경로 (CM7 DSP)

```
                    ┌──────────────────────────────────────────┐
                    │         CM7 Audio DSP Engine             │
                    │                                          │
  MIDI Note ──────► │  ┌──────────────────────────────────┐   │
  CC / SysEx ─────►│  │  Voice Allocator (12-voice poly)  │   │
                    │  └──────────────┬───────────────────┘   │
                    │                 │                         │
                    │  ┌──────────────▼───────────────────┐   │
                    │  │  OSC Engine (vtable dispatch)     │   │
                    │  │  13 types, Plaits-based           │   │
                    │  │  ┌──────────┐  ┌──────────┐      │   │
                    │  │  │  OSC 1   │  │  OSC 2   │      │   │
                    │  │  │ 11 types │  │ 30 types │      │   │
                    │  │  └────┬─────┘  └────┬─────┘      │   │
                    │  └───────┼──────────────┼────────────┘   │
                    │          └──────┬───────┘                │
                    │                 │                         │
                    │  ┌──────────────▼───────────────────┐   │
                    │  │  VCF (Digital Filter)            │   │
                    │  │  Multi / Surgeon / Comb / Phaser │   │
                    │  │  Cutoff · Resonance · EnvAmt     │   │
                    │  └──────────────┬───────────────────┘   │
                    │                 │                         │
                    │  ┌──────────────▼───────────────────┐   │
                    │  │  VCA + Mixer                    │   │
                    │  │  Velocity · Amp Env             │   │
                    │  └──────────────┬───────────────────┘   │
                    │                 │                         │
                    │  ┌──────────────▼───────────────────┐   │
                    │  │  FX Send Bus (3 slots)          │   │
                    │  │  FX1 · FX2 · FX3                │   │
                    │  │  Dry/Wet mix                    │   │
                    │  └──────────────┬───────────────────┘   │
                    │                 │                         │
                    └─────────────────┼─────────────────────────┘
                                      │ Shared SRAM
                                      │
                    ┌─────────────────┼─────────────────────────┐
                    │  CM4 I/O        │                         │
                    │  ┌──────────────▼───────────────────┐   │
                    │  │  SAI2 (48kHz, I2S/TDM)          │   │
                    │  │  ChA: PE4(MCLK) PE5(SCK) PE6(SD)│   │
                    │  │  ChB: PD11(SD) PD12(FS) PD13(SCK)│   │
                    │  └──────────────┬───────────────────┘   │
                    │                 │                         │
                    │  ┌──────────────▼───────────────────┐   │
                    │  │  DMA2 (Double-buffer)           │   │
                    │  │  Stream 0 → SAI2 ChA            │   │
                    │  │  Stream 4 → SAI2 ChB            │   │
                    │  │  Stream 7 → Monitor/Ctrl        │   │
                    │  └──────────────┬───────────────────┘   │
                    │                 │                         │
                    │  ┌──────────────▼───────────────────┐   │
                    │  │  DAC/ADC Codec (?SPI controlled)│   │
                    │  │  ★ Chip NOT identified          │   │
                    │  └──────────────────────────────────┘   │
                    └─────────────────────────────────────────┘
```

### 5.2 오실레이터 엔진 (vtable 기반)

```
Engine Base Class (Plaits-derived):
  vtable[2] Init()      — 초기화
  vtable[3] Reset()     — 상태 리셋
  vtable[4] LoadUserData() — 프리셋 로드
  vtable[5] Render()    — 오디오 렌더링

13 Oscillator Types (VTable @ 0x37CB4~0x386D4):
  ┌──────┬───────────────┬────────┬───────────────────────┐
  │ Idx  │ Name          │ Group  │ Plaits Equivalent     │
  ├──────┼───────────────┼────────┼───────────────────────┤
  │  0   │ VAnalog       │ —      │ VirtualAnalogEngine   │
  │  1   │ SuperWave     │ A      │ SwarmEngine           │
  │  2   │ KarplusStr    │ A      │ StringEngine          │
  │  3   │ Waveshaper    │ A      │ WaveshapingEngine     │
  │  4   │ Two Op. FM    │ A      │ FMEngine              │
  │  5   │ Noise         │ A      │ NoiseEngine           │
  │  6   │ Wavetable     │ B      │ WavetableEngine       │
  │  7   │ Sample        │ B      │ Custom (Arturia)      │
  │  8   │ Audio In      │ B      │ Custom (Arturia)      │
  │  9   │ Granular      │ B      │ GrainEngine           │
  │ 10   │ Chord         │ B      │ ChordEngine           │
  │ 11   │ Speech        │ C      │ SpeechEngine          │
  │ 12   │ Strings       │ C      │ StringEngine (ext)    │
  └──────┴───────────────┴────────┴───────────────────────┘

  Group A: Simple param fill (analog/math)
  Group B: Complex init with config flags (digital/sample)
  Group C: Table-lookup init with formant data (speech)
```

### 5.3 FX 프로세서

```
FX DSP Core (Separate Binary, 120KB)
├── Chorus
├── Phaser
├── Flanger
├── Reverb
├── Distortion
├── Delay (with routing options)
└── Stereo Processing

FX Types per slot (from .mnfx params):
  FX1_Type: 13 types (float 0~1, quantized)
  FX2_Type: 13 types
  FX3_Type: 13 types
  Each FX: Type + Param1-3 + Opt1-3 + Enable (11 params)
```

---

## 6. 프리셋 포맷

### 6.1 하드웨어 프리셋 (펌웨어 내부)
- **포맷:** 커스텀 바이너리, **0xD00 바이트 고정 크기**
- **구조:** uint16 파라미터 + CRC8 + 매직 `0x410F`
- **저장:** 펌웨어 내부 플래시 (512 프리셋 슬롯)

### 6.2 VST 프리셋 (.mnfx)
- **포맷:** boost::serialization text archive (version 10)
- **시그니처:** `22 serialization::archive 10`
- **인코딩:** ASCII, CRLF 종료, 단일 행

```
Header:  [version] [build] [name_len] [name] [author_len] [author] 
         [category_len] [category] [metadata...] [subtype] [type] [padding]
Data:    [name_char_count] [param_name] [value]  (2,362 params)
```

### 6.3 파라미터 스페이스 (2,362개)

| 그룹 | 수 | 설명 |
|------|-----|------|
| Pitch_S* | 384 | 64스텝 × 6인덱스 피치 시퀀서 |
| Length_S* | 384 | 64스텝 × 6인덱스 길이 시퀀서 |
| Velo_S* | 384 | 64스텝 × 6인덱스 벨로시티 시퀀서 |
| Mod_S* | 257 | 모듈레이션 매트릭스 (64×4) |
| Mx_* | 101 | 모듈레이션 라우팅 (Dots, Assign, Col) |
| Shp1_*, Shp2_* | 130 | LFO 쉐이퍼 (2×16×4) |
| Gate_S* | 64 | 게이트 시퀀서 |
| Reserved* | 256 | 예약 (4×64) |
| Osc1_*, Osc2_* | 22 | 오실레이터 |
| Vcf_* | 5 | 필터 |
| Env_*, CycEnv_* | 17 | ADSR + 사이클릭 엔벨로프 |
| LFO1_*, LFO2_* | 14 | LFO |
| FX1_*, FX2_*, FX3_* | 33 | 이펙트 (3×11) |
| Seq_*, Arp_* | 28 | 시퀀서/아르페지에이터 |
| Gen_* | 12 | 제너럴 (Poly, Unison, Legato) |
| 기타 | ~270 | Vibrato, Delay, Dice, Tempo, VST3 등 |

---

## 7. 펌웨어 업데이트 3경로

```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│ DFUUpdater  │    │ RKUpdater   │    │ CollageUpdater  │
│             │    │             │    │                 │
│ IF#1 WINUSB │    │ Serial Port │    │ IF#0 Vendor Bulk│
│ TUSBAUDIO   │    │ Rockchip    │    │ Protobuf        │
│ DFU API     │    │ Bootloader  │    │                 │
│ 10 functions│    │             │    │                 │
└──────┬──────┘    └──────┬──────┘    └────────┬────────┘
       │                  │                    │
       │  Commands:       │                    │
       │  checkhash       │                    │
       │  install         │                    │
       │  reboot          │                    │
       │  rebootloader    │                    │
       │  set_master_vers │                    │
       └──────────────────┼────────────────────┘
                          │
                   ┌──────▼──────┐
                   │ MiniFreak   │
                   │ STM32H745   │
                   └─────────────┘
```

---

## 8. 소스 코드 구조 (DLL 디버그 경로에서 추정)

```
minifreakv/
├── arturiausblib/src/          # USB 추상화
│   └── LibusbImpl, LibusbWrapper
├── collage/src/                # Collage 프로토콜
│   ├── comm/CommUsb.cpp        # USB 전송
│   ├── comm/CommTcp.cpp        # TCP (디버그)
│   ├── protocol/ProtocolProtobuf.cpp
│   └── protocol/control/       # Data, Resource, System, Security
├── hwvsttools/src/             # HW↔VST 브릿지
│   ├── HwVstController.cpp
│   └── UpdateComponent.cpp
├── jucearturialib/src/         # JUCE 확장
│   ├── Midi/, Preset/, PresetBrowser/, SampleBrowser/
├── minifreakv/src/             # MiniFreak 특화
│   ├── controller/MiniFreakController.cpp
│   ├── controller/MiniFreakPresetHwVstConverter.cpp
│   ├── gui/MiniFreakFirmwareUpdateComponent.cpp
│   └── hardware/StorageController.cpp, CommandQueue.cpp
├── wrapperlib/src/Midi/        # VST 래퍼
├── protobuf/                   # Google Protobuf
├── boost/                      # Boost serialization
└── ziptool/                    # ZIP (.mnf 패키지)
```

---

## 9. 미해결 과제

| 과제 | 상태 | 필요한 것 |
|------|------|-----------|
| DAC/ADC 칩 식별 | ❌ | 물리 보드 분석 (칩 사진) |
| CM4↔CM7 인터코어 통신 | ⚠️ 간접 참조 | JTAG/SWD 런타임 트레이싱 |
| UI MCU 통신 프로토콜 | ❌ | 간접 포인터 추적 불가 |
| SPI 페리페럴 | ❌ | 런타임 분석 필요 |
| SIBP 상세 명령 | ❌ | DLL에서 Protobuf .proto 재구성 |
| 캘리브레이션 9종 | ❌ | SysEx 캡처 + 비교 |
| Protobuf .proto 정의 | ❌ | DLL 바이너리에서 재구성 |
| 파라미터 ID ↔ SysEx 바이트 매핑 | ⚠️ 부분 | DLL 분석 필요 |

---

## 10. Phase별 산출물 인덱스

| Phase | 문서 | 데이터 |
|-------|------|--------|
| 0 | `minifreak_technical_summary.md` | — |
| 1 | `*_triage.json`, `*_strings.txt`, `*_functions.csv` | 7 바이너리 |
| 2 | `phase2_engine_analysis.md`, `phase2-5_preset_analysis.md` | `cm4_engine_analysis.json` |
| 3 | `phase3_midi_usb_analysis.md` | `cm4_midi_handlers.json` |
| 4 | `PHASE4_HARDWARE_ANALYSIS.md` | `phase4_*.json` (9개) |
| 5 | `PHASE5_SOFTWARE_ANALYSIS.md`, `PHASE5_DLL_ANALYSIS.md`, `PHASE5_XML_RESOURCES.md`, `PHASE5_MNFX_FORMAT.md` | `phase5_*.json` (3개) |
| 6 | `PHASE6_ARCHITECTURE.md` (본 문서) | — |
