# MiniFreak 사운드 엔진 — 코드 레벨 블록 다이어그램

**Phase 6-2** | 2026-04-24 | Ghidra 분석 기반

---

## 1. CM7 DSP 함수 호출 그래프

```
                         FUN_080359f4 (18,232B)
                    ╔══════════════════════════╗
                    ║   MAIN AUDIO RENDER LOOP ║
                    ║   6-voice poly (Para: 12) ║
                    ║   float/NEON/VectorFloat ║
                    ╚════╤═══════════╤═════════╝
                         │           │
              ┌──────────▼──┐  ┌─────▼──────────┐
              │ Voice Alloc │  │ Parameter State│
              │ (poly/mono) │  │ (shared SRAM)  │
              └──────┬──────┘  └────────────────┘
                     │
          ┌──────────▼──────────────────────────────┐
          │  Per-Voice Processing (×12 voices)       │
          │                                          │
          │  ┌───────────────────────────────────┐   │
          │  │  OSC Engine (vtable dispatch)     │   │
          │  │  Osc1: 16+ types, Osc2: 21 types  │   │
          │  │                                   │   │
          │  │  ┌─────────────┐ ┌─────────────┐ │   │
          │  │  │  OSC 1      │ │  OSC 2      │ │   │
          │  │  │  16+ types  │ │  21 types   │ │   │
          │  │  │             │ │             │ │   │
          │  │  │  Init:      │ │  Init:      │ │   │
          │  │  │  G-A:78 instr│ │  G-A:78 instr│ │  │
          │  │  │  G-B:123 ins│ │  G-B:123 ins│ │  │
          │  │  │  G-C:96 instr│ │  G-C:96 instr│ │  │
          │  │  │             │ │             │ │   │
          │  │  │  VTable     │ │  VTable     │ │   │
          │  │  │  0x37CB4    │ │  0x37D70    │ │   │
          │  │  │  ~0x386D4   │ │             │ │   │
          │  │  └──────┬──────┘ └──────┬──────┘ │   │
          │  └─────────┼────────────────┼────────┘   │
          │            └────────┬───────┘            │
          │                     │                    │
          │  ┌──────────────────▼────────────────┐   │
          │  │  Oscillator Mix                    │   │
          │  │  FUN_0803e6f8 (10,332B)            │   │
          │  │  float + short + VectorFloat       │   │
          │  │  Mix level, crossfade, detune      │   │
          │  │  audio_score = 12                  │   │
          │  └──────────────────┬────────────────┘   │
          │                     │                    │
          │  ┌──────────────────▼────────────────┐   │
          │  │  Analog VCF (SEM-style)            │   │
          │  │  FUN_0803c2bc (9,250B)             │   │
          │  │  float + short, struct pointers    │   │
          │  │  audio_score = 6                   │   │
          │  │                                    │   │
          │  │  Filter Types (3):                 │   │
          │  │  ├─ LP (Low Pass)                  │   │
          │  │  ├─ BP (Band Pass)                 │   │
          │  │  └─ HP (High Pass)                 │   │
          │  │  고정 12 dB/oct 슬로프             │   │
          │  │  Self-oscillation 가능             │   │
          │  │                                    │   │
          │  │  Parameters:                       │   │
          │  │  Cutoff (CC#74), Resonance (CC#71) │   │
          │  │  VCF Env Amt (CC#24)               │   │
          │  │  Velocity Env Mod (CC#94)          │   │
          │  └──────────────────┬────────────────┘   │
          │                     │                    │
          │  ┌──────────────────▼────────────────┐   │
          │  │  Osc 2 Audio Processor (디지털)    │   │
          │  │  (Osc 2를 필터/이펙터로 사용 시)  │   │
          │  │                                    │   │
          │  │  Types:                            │   │
          │  │  ├─ Multi Filter (LP/BP/HP/Notch   │   │
          │  │  │   + 6/12/24/36 dB/oct)         │   │
          │  │  ├─ Surgeon Filter (Parametric EQ) │   │
          │  │  ├─ Comb Filter (KB tracking)      │   │
          │  │  ├─ Phaser Filter (2~12 pole)      │   │
          │  │  └─ Destroy (Wavefolder+Crusher)   │   │
          │  │  Osc 2 Volume = Dry/Wet 밸런스     │   │
          │  └──────────────────┬────────────────┘   │
          │                     │                    │
          │  ┌──────────────────▼────────────────┐   │
          │  │  Envelope Generator                │   │
          │  │  FUN_080321d4 (8,350B)             │   │
          │  │  float + short + VectorFloat       │   │
          │  │  audio_score = 11                  │   │
          │  │                                    │   │
          │  │  Envelope (ADSR): VCA hardwired    │   │
          │  │    CC#80(A) / 81(D) / 82(S) / 83(R)│   │
          │  │  Cycling Envelope (RHF): 3-stage   │   │
          │  │    Rise/Fall/Hold + Sustain        │   │
          │  │    CC#68(RiseShape) / 76(Rise) /   │   │
          │  │    77(Fall) / 78(Hold) / 69(FallShp)│   │
          │  │  Vibrato LFO (제3 LFO, 별도 구현)  │   │
          │  └──────────────────┬────────────────┘   │
          │                     │                    │
          │  ┌──────────────────▼────────────────┐   │
          │  │  VCA + Voice Output               │   │
          │  │  FUN_0803a490 (7,610B)             │   │
          │  │  float + short + VectorFloat       │   │
          │  │  9 global variables               │   │
          │  │  audio_score = 12                  │   │
          │  └──────────────────┬────────────────┘   │
          │                     │                    │
          └─────────────────────┼────────────────────┘
                                │
                    ┌───────────▼───────────────┐
                    │  Voice Summing Bus         │
                    │  6 voices → stereo mix     │
                    │  (12 in Para mode)          │
                    └───────────┬───────────────┘
                                │
          ┌─────────────────────▼─────────────────────┐
          │  Modulation Matrix                        │
          │  FUN_08054708 (7,480B)                    │
          │  float + short + VectorFloat              │
          │  audio_score = 12                         │
          │                                           │
          │  7 Source Rows:                           │
          │    CycEnv, LFO1, LFO2, Velo+AT,          │
          │    Wheel, Keyboard, Mod Seq               │
          │                                           │
          │  13 Columns (destinations):               │
          │    4 hardwired + 9 assignable             │
          │    (3 pages × 3 assignable)               │
          │  Dest enum: ~30+ assignable destinations  │
          │  Mx_Dots, Mx_Assign, Mx_Col (101 params) │
          └─────────────────────┬─────────────────────┘
                                │
          ┌─────────────────────▼─────────────────────┐
          │  LFO Processors                           │
          │                                           │
          │  LFO1: FUN_08056528 (2,276B) score=12    │
          │  LFO2: FUN_0801b8b0 (2,260B) score=12    │
          │  Shaper: Shp1_*/Shp2_* (130 params)      │
          │  Rate, Shape, Amount, Phase, Sync         │
          └─────────────────────┬─────────────────────┘
                                │
          ┌─────────────────────▼─────────────────────┐
          │  FX Send Bus (3 slots)                    │
          │  FUN_0805c408 (2,700B) score=10           │
          │  10 parameters — complex DSP chain        │
          │                                           │
          │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
          │  │  FX1     │ │  FX2     │ │  FX3     │ │
          │  │ 11 params│ │ 11 params│ │ 11 params│ │
          │  │ Type     │ │ Type     │ │ Type     │ │
          │  │ Param1-3 │ │ Param1-3 │ │ Param1-3 │ │
          │  │ Opt1-3   │ │ Opt1-3   │ │ Opt1-3   │ │
          │  │ Enable   │ │ Enable   │ │ Enable   │ │
          │  └────┬─────┘ └────┬─────┘ └────┬─────┘ │
          └───────┼────────────┼────────────┼───────┘
                  │            │            │
          ┌───────▼────────────▼────────────▼───────┐
          │  FX DSP Core (CM7 내부 함수, 524KB)
          │  Target: STM32H745 CM7 코어
          │
          │  ┌──────────────────────────────────┐
          │  │  FX Types (10+2 per slot):       │
          │  │  Chorus, Phaser, Flanger,         │
          │  │  Reverb, Delay, Distortion,       │
          │  │  BitCrusher, 3 Bands EQ,          │
          │  │  Peak EQ, Multi Comp,              │
          │  │  Vocoder EXT In, Vocoder Self     │
          │  └──────────────────────────────────┘
          │
          │  Routing:
          │  ├─ Delay/Reverb: Send 모드 가능
          │  └─ 기타 FX: Insert 라우팅
          └──────────────────┬───────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Master Output  │
                    │  → Shared SRAM  │
                    │  → CM4 DMA      │
                    │  → SAI2 → DAC   │
                    └─────────────────┘
```

---

## 2. CM7 DSP 함수 분석

### 2.1 Top Functions by Audio Score

| 함수 | 크기 | Score | 특징 | 추정 역할 |
|------|------|-------|------|-----------|
| `FUN_080359f4` | 18,232B | ? | CM7 최대 함수 | **Main Audio Render** (6-voice poly, 12-voice Para) |
| `FUN_0803e6f8` | 10,332B | 12 | float+short+VectorFloat | **Oscillator Mix / Voice Body** |
| `FUN_080321d4` | 8,350B | 11 | float+short+VectorFloat | **Envelope Generator** |
| `FUN_0803c2bc` | 9,250B | 6 | float+short, struct ptrs | **VCF Filter Coeff / Osc2 Processor** |
| `FUN_0803a490` | 7,610B | 12 | float+short+VectorFloat, 9 globals | **VCA / Voice Output** |
| `FUN_08054708` | 7,480B | 12 | float+short+VectorFloat | **Modulation Matrix** |
| `FUN_0805a040` | 3,840B | 10 | float+VectorFloat, 23 globals | **LFO + Shaper** |
| `FUN_08034338` | 5,046B | 6 | float+short, 15 globals | **Filter Coefficients / Waveshaper** |
| `FUN_08056ed0` | 2,766B | 12 | float+short+VectorFloat | **Arp/Seq Step Processing** |
| `FUN_0805c408` | 2,700B | 10 | 10 params | **FX Send Routing** |
| `FUN_08016968` | 2,334B | 13 | `0x3f800000` (1.0f) | **Normalization / Quantization** |
| `FUN_08056528` | 2,276B | 12 | float+short+VectorFloat | **LFO1 Processing** |
| `FUN_0801b8b0` | 2,260B | 12 | float+short+VectorFloat | **LFO2 Processing** |
| `FUN_08029390` | 2,748B | 4 | float, 9 globals | **Pitch / Detune Processing** |

### 2.2 DSP 함수 클러스터 분석

```
                ┌─────────────────────────────────┐
                │     CLUSTER 1: VOICE CORE       │
                │     (highest audio scores)       │
                │                                  │
                │  FUN_080359f4  ─── Main Render   │
                │       │                          │
                │  FUN_0803e6f8  ─── Osc Mix       │
                │  FUN_080321d4  ─── Envelopes     │
                │  FUN_0803c2bc  ─── VCF Filter    │
                │  FUN_0803a490  ─── VCA Output    │
                │  FUN_08029390  ─── Pitch/Detune  │
                │                                  │
                │  특징: 전부 float+short+VF        │
                │  score: 6~13                     │
                └─────────────────────────────────┘

                ┌─────────────────────────────────┐
                │     CLUSTER 2: MODULATION        │
                │                                  │
                │  FUN_08054708  ─── Mod Matrix    │
                │  FUN_0805a040  ─── LFO+Shaper   │
                │  FUN_08056528  ─── LFO1          │
                │  FUN_0801b8b0  ─── LFO2          │
                │  FUN_08056ed0  ─── Arp/Seq       │
                │                                  │
                │  특징: 다수 전역변수 (state)       │
                │  score: 10~12                    │
                └─────────────────────────────────┘

                ┌─────────────────────────────────┐
                │     CLUSTER 3: POST-PROCESSING   │
                │                                  │
                │  FUN_0805c408  ─── FX Routing    │
                │  FUN_08034338  ─── WaveShaper    │
                │  FUN_08016968  ─── Normalization │
                │                                  │
                │  특징: 낮은 score (4~10)          │
                │  정수+혼합 연산                   │
                └─────────────────────────────────┘
```

---

## 3. CM4 페리페럴 초기화 트리

```
FUN_08121cfc()  ─── CM4 MAIN INIT (30 calls + infinite loop)
│
├── FUN_08124600()  ─── DataMemoryBarrier(0x1f) + register init
│   └── 멀티코어 부트 동기화
│
├── FUN_08124644()  ─── ???
├── FUN_08124620(4) ─── ???
├── FUN_081277e0()  ─── ???
├── FUN_08123850()  ─── ???
├── FUN_0812192c()  ─── ???
├── FUN_081216b0()  ─── ???
├── FUN_08121e00()  ─── ???
│
├── [Peripheral Init Block — 16 functions]
│   ├── FUN_08122010()  ─── ??? (SPI? I2C?)
│   ├── FUN_08122080()  ─── ???
│   ├── FUN_08123214()  ─── ???
│   ├── FUN_081233a8()  ─── ???
│   ├── FUN_0812353c()  ─── ???
│   ├── FUN_081236c0()  ─── ???
│   ├── FUN_081210e0()  ─── ???
│   ├── FUN_08121240()  ─── ???
│   ├── FUN_08121b40()  ─── ???
│   ├── FUN_08121e24()  ─── ???
│   ├── FUN_081226f8()  ─── ???
│   ├── FUN_08122cc8()  ─── ???
│   ├── FUN_08122da4()  ─── ???
│   ├── FUN_08122e98()  ─── ???
│   ├── FUN_08122f8c()  ─── ???
│   └── FUN_081230a4()  ─── ???
│
├── FUN_08122840()  ─── ???
├── FUN_08121590()  ─── ???
│
├── ★ FUN_081220f4()  ─── SAI CONFIG (48kHz)
│   │
│   └── ★ FUN_08129a98()  ─── SAI PERIPHERAL INIT (922B)
│       │                      SAI1~SAI4 multi-instance
│       │
│       ├── FUN_0812215c()  ─── SAI CLOCK + GPIO + DMA (~1200B)
│       │   ├── FUN_0812853c()  ─── RCC clock enable
│       │   ├── FUN_081259e0()  ─── GPIO pin config
│       │   │   ├── PE4 (AF6) → SAI2_MCLK_A
│       │   │   ├── PE5 (AF6) → SAI2_SCK_A
│       │   │   ├── PE6 (AF6) → SAI2_SD_A
│       │   │   ├── PD1 (AF10) → SAI2_SD_A (alt)
│       │   │   ├── PD11 (AF10) → SAI2_SD_B
│       │   │   ├── PD12 (AF10) → SAI2_FS_B
│       │   │   └── PD13 (AF10) → SAI2_SCK_B
│       │   └── FUN_08124990()  ─── DMA stream config
│       │       ├── DMA2 Stream0 → SAI2 ChA
│       │       ├── DMA2 Stream4 → SAI2 ChB
│       │       └── DMA2 Stream7 → Monitor
│       │
│       ├── FUN_081293f4()  ─── SAI STATUS/IRQ (704B)
│       ├── FUN_08129144()  ─── Clock divider calc (FP)
│       └── FUN_08128fec()  ─── Clock divider calc v2
│
├── FUN_08123150()  ─── ???
├── FUN_081228b8()  ─── ???
├── FUN_08121c4c()  ─── ???
│
├── FUN_081a1558()  ─── Build version print
│
└── do { FUN_081a1650() } while(true)  ─── ★ CM4 MAIN LOOP
```

---

## 4. MIDI→DSP 파라미터 라우팅

```
USB MIDI IN (EP02)
       │
       ▼
┌─────────────────────────────────────┐
│  MIDI Input Router (CM4)            │
│  0x08157810 (midi_input_handler)    │
│                                     │
│  ┌───────────┐  ┌───────────────┐  │
│  │ Note On/Off│  │ CC Handler    │  │
│  │ → Voice    │  │ 0x08166810    │  │
│  │   Alloc    │  │ 161 CCs       │  │
│  └─────┬─────┘  └──────┬────────┘  │
│        │               │            │
│  ┌─────▼───────────────▼────────┐  │
│  │ SysEx State Machine          │  │
│  │ 0x08157278 (43 states)       │  │
│  │ F0 00 20 6B [DevID] [Type]  │  │
│  │ [ParamIdx] [Value] F7        │  │
│  └─────────────┬────────────────┘  │
│                │                    │
│  ┌─────────────▼────────────────┐  │
│  │ NRPN Handler                 │  │
│  │ 0x081812B4                   │  │
│  │ 14-bit CC (MSB+LSB)          │  │
│  └─────────────┬────────────────┘  │
└────────────────┼────────────────────┘
                 │
         ┌───────▼───────┐
         │ Parameter     │
         │ State Buffer  │
         │ (Shared SRAM) │
         └───────┬───────┘
                 │
    ┌────────────▼────────────┐
    │  CM7 DSP reads params  │
    │  each render cycle     │
    │  (indirect via ptrs)   │
    └─────────────────────────┘
```

---

## 5. 프리셋 파라미터 ↔ 코드 매핑

### 5.1 Preset Enum Types (RTTI)

| Enum | Getter | Setter | 설명 | .mnfx prefix |
|------|--------|--------|------|-------------|
| `eSynthParams` | `Preset::get()` | `Preset::set()` | OSC, Filter, Env | `Osc*`, `Vcf_*`, `Env_*` |
| `eFXParams` | `Preset::get()` | `Preset::set()` | FX 프로세서 | `FX1_*`, `FX2_*`, `FX3_*` |
| `eCtrlParams` | `Preset::get()` | `Preset::set()` | 컨트롤 서피스 | `Gen_*`, `Kbd_*` |
| `eSeqParams` | `Preset::get()` | `Preset::set()` | 시퀀서 | `Seq_*`, `Arp_*` |
| `eSeqAutomParams` | `Preset::get()` | `Preset::set()` | 오토메이션 | `AutomReserved*` |
| `eSeqStepParams` | `Preset::get()` | `Preset::set()` | 스텝 데이터 | `Pitch_S*`, `Length_S*`, `Velo_S*` |
| `eShaperParams` | `Preset::get()` | `Preset::set()` | LFO 쉐이퍼 | `Shp1_*`, `Shp2_*` |

### 5.2 파라미터 흐름

```
.mnfx (Desktop)              Firmware (0xD00 binary)
    │                               │
    │  boost::serialization         │  uint16 + CRC8
    │  text → parse                 │  binary → memcpy
    │         │                     │         │
    └─────────┼─────────────────────┼─────────┘
              │                     │
         ┌────▼─────────────────────▼────┐
         │  Preset Object (Preset class) │
         │  get(eSynthParams, idx)       │
         │  set(eFXParams, idx, val)     │
         └────────────┬──────────────────┘
                      │
         ┌────────────▼────────────┐
         │  DSP Parameter State   │
         │  (float normalized 0~1)│
         │  Shared SRAM           │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │  DSP Functions read     │
         │  each audio frame      │
         └─────────────────────────┘
```

---

## 6. 보이스 아키텍처

```
                    Note On Event
                         │
              ┌──────────▼──────────┐
              │  Voice Allocator    │
              │  6 voices (Poly/Mono/Uni) │
              │  12 voices (Para)   │
              │  Modes:             │
              │  ├─ Mono (1 voice)  │
              │  ├─ Poly (6 voice)  │
              │  ├─ Para (12 voice) │
              │  │  (Osc2 비활성,  │
              │  │   6 pair × 2)   │
              │  └─ Uni (2-6 voice)│
              │     + Legato 옵션  │
              │  FUN_0812d0dc      │
              │  Voice steal: 5-tick│
              │  timeout           │
              └──────────┬──────────┘
                         │
         ┌───────────────▼───────────────┐
         │  Voice Pool (×6 max, ×12 Para)      │
         │                               │
         │  Each Voice:                 │
         │  ┌─────────────────────┐     │
         │  │ OSC1 → (optional)   │     │
         │  │   → Osc2 Processor  │     │
         │  │ Osc Mix (level/pan) │     │
         │  │   ↓                 │     │
         │  │ Analog VCF (SEM)    │     │
         │  │ LP/BP/HP 12dB/oct   │     │
         │  │   ↓                 │     │
         │  │ Analog VCA (ADSR)   │     │
         │  │   ↓                 │     │
         │  │ Voice Output        │     │
         │  └─────────────────────┘     │
         │                               │
         │  All voices → Sum Bus        │
         │  Sum Bus → FX Send (3 slots) │
         │  FX → Master Out             │
         └───────────────────────────────┘
```

---

## 7. 모듈레이션 매트릭스

> ⚠️ Phase 8 정정: 이 섹션의 source/destination 목록은 Phase 8에서 재검증됨.
> 아래는 정정된 내용.

```
    7 SOURCE ROWS              13 COLUMNS (destinations)
    ─────────                  ──────────────────────────
    CycEnv ──────┐             4 hardwired:
    LFO1 ────────┤               Vib Rate, Vib AM, VCA,
    LFO2 ────────┤               LFO1 AM, LFO2 AM,
    Velo+AT ─────┤               CycEnv AM, Uni Spread
    Wheel ───────┤             9 assignable (3 pages × 3):
    Keyboard ────┤               ~30+ destination 풀에서 선택
    Mod Seq ─────┘

    Macro M1/M2는 Mod Matrix source가 아님.
    PitchWheel은 Mod Matrix source가 아님.
    Envelope (ADSR)은 Mod Matrix row가 아님 (VCA hardwired).
    Macro는 터치스트립 또는 CC#117/118로 직접 제어.

    Mx_Dots[N]    ── Boolean enable per routing
    Mx_Assign[N]  ── Source assignment
    Mx_Col[N]     ── Amount/depth
```
