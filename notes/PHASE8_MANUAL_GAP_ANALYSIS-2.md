# Phase 8: 매뉴얼 대조 검증 및 수정 계획

> **대조 대상**: 사용자 리포지토리(`Seoraksang/minifreak`) ↔ Arturia 공식 매뉴얼 v4.0.1 (2025-07-04 개정)
> **펌웨어 버전**: fw4_0_1_2229 (2025-06-18 빌드)
> **작성일**: 2026-04-25
> **목적**: 펌웨어 리버싱 결과를 공식 매뉴얼 사양에 맞춰 검증·정정·보강

---

## 0. 요약 (Executive Summary)

리버싱 결과를 매뉴얼에 대조한 결과, **세 가지 층위의 격차**가 확인됨:

1. **사실 오류** (Critical, 즉시 수정 필요)
   - 폴리포니 보이스 수: `12 voices` → 실제는 **6 voices** (Para 모드에서 12)
   - MIDI CC 매핑: 분석된 30+개 CC 중 **10개 이상이 매뉴얼 차트와 불일치** (Cutoff/Resonance/Envelope/LFO/Macro 등 핵심 CC 번호 모두 틀림)
   - Modulation Matrix 소스: 분석은 10+ 소스, 매뉴얼은 **7 row × 13 column** 구조
   - 폴리포니 모드: `Poly2Mono/Legato` → 매뉴얼은 **Mono/Poly/Para/Uni**
   - Aftertouch: 분석은 Poly AT 표시, 키베드는 **mono AT만 (외부 MIDI 입력은 Poly 처리 가능)**

2. **누락된 영역** (High, 보강 필요)
   - **그래뉼러 엔진 7종** (Cloud Grains/Hit Grains/Frozen/Skan/Particles/Lick/Raster) — V3에서 추가됨, 분석 누락
   - **Sample 엔진** — V3에서 추가됨, 분석 누락
   - **Wavetable 엔진** — V3에서 추가됨, 분석 누락
   - **Vibrato (제3의 LFO)** — 매뉴얼은 명시, 분석은 LFO1/LFO2만
   - **Snapshots 시스템** — 시간 기반 자동 스냅샷, 분석 누락
   - **Favorites Panel** (V2 추가) — 64 슬롯, 분석 누락
   - **Mod Sequencer 4 lane** — 매뉴얼에 명시된 4 modulation lane, 분석은 일반 시퀀서만
   - **Arpeggiator 8 모드 + 4 Modifier** — Up/Down/UpDown/Random/Order/Walk/Poly/Pattern + Repeat/Ratchets/Rand Oct/Mutate

3. **개념 혼동** (Medium, 명칭 정정)
   - `Env1 / Env2` → 실제 명칭 **Envelope (ADSR) + Cycling Envelope (RHF)**
   - 분석에서 Multi/Surgeon/Comb/Phaser를 **VCF 아래** 배치 → 실제는 **Osc 2 Audio Processor**의 디지털 필터. 아날로그 VCF는 SEM-style **LP/BP/HP 단일 12dB/oct**만.
   - "Mod Matrix 140 destinations" → 실제 destination 슬롯 수는 **4 hardwired + 9 assignable (3 page × 3) = 13** (전체 가능 destination 풀이 약 140일 수는 있음, 명확화 필요)

---

## 1. 격차 매트릭스 (Gap Matrix)

### 1.1 Critical — 사실 오류 (Severity: 🔴)

| 영역 | 분석 문서 기재 | 매뉴얼 기재 | 위치 (분석 문서) | 비고 |
|------|---------------|-------------|------------------|------|
| **폴리포니 보이스 수** | 12-voice poly | **6 voices** (Para 시 12) | `PHASE6_SOUND_ENGINE.md` 9행, `REVERSE_MASTER_PLAN.md` | Voice struct 0x118×280B의 실측이 **12** 슬롯이라면, 6 voice × 2 (오실레이터?) 또는 Para용 voice pair 구조 가능성. 재검증 필요. |
| **Voicing Mode 명칭** | Poly / Poly2Mono / Legato / Unison(1-16) | **Mono / Poly / Para / Uni** | `PHASE6_SOUND_ENGINE.md` Voice Architecture | "Poly2Mono"는 매뉴얼에 없음. Unison Count는 **2~6**까지(매뉴얼). Legato는 별도 `Legato Mono` 옵션이 Mono/Uni 모드 안에 존재. |
| **MIDI CC: Filter Cutoff** | CC#24 | **CC#74** | `PHASE6_MIDI_CHART.md` 53행 | 매뉴얼: CC#24 = "VCF Env Amt" |
| **MIDI CC: Filter Resonance** | CC#25 | **CC#71** | `PHASE6_MIDI_CHART.md` 54행 | |
| **MIDI CC: VCF Env Amount** | CC#26 ("Filter Env Amount") | **CC#24** | `PHASE6_MIDI_CHART.md` 55행 | 분석의 CC#24 매핑과 충돌 |
| **MIDI CC: Envelope ADSR** | CC#38~41 (Env1) / CC#45~50 (Env2) | **CC#80(A) / 81(D) / 82(S) / 83(R)** | `PHASE6_MIDI_CHART.md` 61~73행 | Envelope는 단일. Env1/Env2 분리는 펌웨어 내부 다른 의미일 가능성. |
| **MIDI CC: LFO1 Rate** | CC#53 | **CC#85** | `PHASE6_MIDI_CHART.md` 74행 | |
| **MIDI CC: LFO2 Rate** | CC#60 | **CC#87** | `PHASE6_MIDI_CHART.md` 79행 | |
| **MIDI CC: FX Time/Intensity/Amount** | FX A: CC#71~74, FX B: CC#85+ (101개 확장) | **FX1: 22/23/25, FX2: 26/27/28, FX3: 29/30/31** | `PHASE6_MIDI_CHART.md` 85~95행 | 완전히 다른 매핑 |
| **MIDI CC: Macro 1/2** | Macro1=193, Macro2=195 (~Macro7=204) | **Macro M1=117, M2=118** | `PHASE6_MIDI_CHART.md` 96~102행 | Macro는 매뉴얼상 **2개만 (M1/M2)**. 매크로 7개 분석은 오류. |
| **MIDI CC: Cycling Envelope** | (분석 누락) | **CC#68(RiseShape)/76(Rise)/77(Fall)/78(Hold)/69(FallShape)** | `PHASE6_MIDI_CHART.md` | CycEnv 전체 CC 누락 |
| **MIDI CC: Mod Wheel** | (분석 누락) | **CC#1** | `PHASE6_MIDI_CHART.md` | Standard MIDI CC지만 분석 차트에 없음 |
| **MIDI CC: Glide** | CC#65 (Portamento) | **CC#5** (Glide), CC#65는 별개 | `PHASE6_MIDI_CHART.md` 83행 | CC#5 = Portamento Time = Glide |
| **MIDI CC: Seq Gate/Spice** | (분석 누락) | **CC#115(Gate) / 116(Spice)** | — | |
| **MIDI CC: Velocity Env Mod** | (분석 누락) | **CC#94** | — | |
| **Aftertouch (키베드)** | "Per-note pressure → mod matrix" (Poly AT 시사) | **Mono AT만 송신** (외부 입력은 Poly AT 수용) | `PHASE6_MIDI_CHART.md` 30행 | MicroFreak는 capacitive로 Poly AT, MiniFreak 슬림키는 Mono AT. 명확히 구분 필요. |
| **Modulation Matrix 구조** | "7 sources × 13 columns, 140 destinations" | **7 row × 13 column** (4 hardwired + 9 assignable across 3 pages) | `PHASE6_SOUND_ENGINE.md` Mod Matrix | 13 column이 destination 슬롯. Assignable 9개에 들어갈 수 있는 destination **풀**은 매뉴얼에 약 30+ 항목 명시 (실제 펌웨어 풀이 140이면 별도 이슈). |
| **Mod Matrix Sources (7 row)** | LFO1/LFO2/Env1/Env2/Velocity/ModWheel/PitchWheel/AT/Macro1/Macro2/SeqStep (10+) | **CycEnv / LFO1 / LFO2 / Velo+AT (1 row) / Wheel / Keyboard / Mod Seq** = 7 row | `PHASE6_SOUND_ENGINE.md` Mod Matrix | Macro/PitchWheel은 source가 아님. Velo와 AT는 **하나의 row**로 통합 (`Sound Edit > Keyboard > Matrix Src VeloAT`로 선택). Env1/Env2 분리도 잘못 — 매뉴얼 source는 **CycEnv**가 row 1, **Envelope (ADSR)**는 hardwired (Mod Matrix row 아님). |
| **Bend Range** | "-2~+2 반음 (default)" | **±1 ~ ±12 반음 가변** (default 표기 없음, Sound Edit > Keyboard > Bend Range) | `PHASE6_MIDI_CHART.md` 113행 | 가변 범위 명시 누락 |
| **아날로그 필터 슬로프** | (분석 누락) | **고정 12 dB/oct** (SEM-style) | `PHASE6_SOUND_ENGINE.md` VCF 블록 | 분석에 슬로프 정보 없음. Multi Filter(Osc 2)는 6/12/24/36 dB/oct 가변 — 별도. |
| **아날로그 필터 타입** | "Multi Filter, Surgeon Filter, Comb Filter, Phaser Filter" | **Analog VCF는 LP / BP / HP만** (SEM-style 12 dB/oct), Multi/Surgeon/Comb/Phaser는 **Osc 2 Audio Processor** | `PHASE6_SOUND_ENGINE.md` 60~64행 | 핵심 구조 혼동. Analog VCF와 Digital Multi-mode는 별개 신호 경로. |

### 1.2 High — 누락된 영역 (Severity: 🟠)

| 영역 | 매뉴얼 명시 | 분석 누락 사항 | 추정 펌웨어 위치 |
|------|-------------|----------------|------------------|
| **Granular Engines (V3 추가)** | 7종: Cloud Grains, Hit Grains, Frozen, Skan, Particles, Lick, Raster (Osc 1 only) | 모두 누락 — Osc 타입 카운트가 13으로만 식별됨 | OSC1 vtable (`0x37CB4` 인근) — 추가 vtable entry 13~20 추정 |
| **Sample Engine (V3 추가)** | Osc 1 only, Start/Length/Loop 파라미터 | 누락 | 동일 vtable, 별도 sample buffer 영역 필요 |
| **Wavetable Engine (V3 추가)** | Osc 1 only, factory wavetable 라이브러리 + Sound Edit 브라우저 | 누락 | XML resources에 wavetable 데이터 영역 식별 필요 |
| **Osc 1 Type 총 16종** (매뉴얼 1.1) vs 분석의 **11종** | BasicWaves/SuperWave/Harmo/KarplusStr/VAnalog/Waveshaper/2OpFM/Formant/Speech/Modal/Noise/Bass/SawX/Harm + Audio In + Wavetable + Sample + 7 Granular | 4종 + 7 Granular = 11종 누락 | OSC1 vtable 재카운트 |
| **Osc 2 Type 총 21종** (매뉴얼 1.1) vs 분석의 **30종** | 공통 14 + Chords + FM/RM + Multi Filter + Surgeon + Comb + Phaser + Destroy = 21종 | 분석 30종은 과다 카운트 가능성 — 매뉴얼 21종과 차이 검증 필요 | OSC2 vtable 재카운트 |
| **Vibrato LFO** (매뉴얼 9.3) | 제3의 free-running triangle LFO, Touch Strip 직접 제어 또는 Mod Matrix Assign | 누락 — LFO1/LFO2만 분석됨 | `Vib AM`, `Vib Rate` 파라미터 검색 필요 |
| **LFO Triggering 모드 (8종)** | Free / Poly Kbd / Mono Kbd / Legato Kb / One / LFO / CycEnv / Seq Start | 누락 — Sync 모드만 일부 식별 | LFO retrigger state machine 식별 필요 |
| **LFO Shaper 라이브러리** | 16 Factory + 8 User + 2 Preset (LFO1/LFO2 별도) | 분석은 `Shp1_*/Shp2_*` 130개 파라미터로만 표기 | XML resources에 Factory shaper wave 16개 식별 필요 |
| **Cycling Envelope 모드** | Env / Run / Loop (3 mode) + Stage Order (RHF / RFH / HRF) | 누락 — `CycEnv: Cycling envelope`로만 표기 | Mode/Stage 분기 코드 식별 필요 |
| **Snapshots 시스템** | 자동 시간 기반 (예: "1:22:26"), Sound Edit > View Snapshots | 누락 | 별도 RAM 버퍼 + 메타데이터 |
| **Favorites Panel (V2)** | 64 슬롯, Shift+Panel 진입, 스텝 버튼에 프리셋 저장 | 누락 | UI 모드 분기 + 프리셋 인덱스 매핑 |
| **Sequencer 모드** | Up to 64 step, Step Recording vs Real-time Recording, Overdub, Hold/Tie, Page navigation | 부분 식별 (`seq_arp_handler 0x08189904`만) | Seq state machine 상세 분석 필요 |
| **Mod Sequencer 4 Lanes** | 4개 별도 modulation lane, 각 destination 식별 가능, smoothing 옵션 | 누락 — 일반 Seq Step만 분석 | 4 modulation track buffer + smoothing IIR |
| **Arpeggiator 8 모드** | Up / Down / UpDown / Random / Order / Walk / Poly / Pattern | 누락 — `arp_handler`만 식별 | 모드 분기 + 확률 테이블 (Walk: 25/50/25, RandOct: 75/15/7/3, Mutate: 75/5/5/5/5/3/2) |
| **Arpeggiator 4 Modifier** | Repeat / Ratchets / Rand Oct / Mutate | 누락 | 모디파이어별 변환 함수 |
| **Spice & Dice** | 5 파라미터 (Velocity/Octave/Gate/StepOnOff/EnvDecay+Release) 랜덤 변형 | 누락 | 랜덤 시퀀스 생성기 + 마스크 |
| **Scale Quantization** | 6 factory + Off + Global + User scale (Major/Minor/Dorian/Mixolydian/Blues/Pentatonic) | 누락 | Scale 테이블 (12-bit per octave) + User scale RAM 슬롯 |
| **Mod Quantize (Osc Pitch)** | 10종: Chromatic/Octaves/Fifths/Minor/Major/PhrygianDom/Min9th/Maj9th/MinPent/MajPent | 누락 | Pitch 처리 함수 내 quantize LUT |
| **Chord Mode** | 11 interval (Octave/5th/sus4/m/m7/m9/m11/69/M9/M7/M) | 누락 | Chord interval 매핑 + Scale 적용 |
| **Audio In Mode** | Line / Microphone (Dynamic Mic용 게인 부스트) | 누락 (Audio In 자체는 식별됨) | 입력 게인 스테이지 분기 |
| **Touch Strip 3 Mode** | Keyboard Bend/Wheel(Vibrato) / Macros M1/M2(Assign) / Seq/Arp Gate/Spice(Dice) | UI MCU 식별만 됨, 모드 분기 없음 | UI Ribbon MCU 펌웨어 분석 필요 |
| **Knob Catch Mode** | Jump / Hook / Scale (3 mode) | 누락 | Utility 메뉴 항목 |
| **Velocity / Aftertouch Curve** | Linear / Log / Expo + AT Start/End Sensitivity (Low/Mid/High) | 누락 | UI Kbd MCU 또는 CM4 메인 |
| **MIDI Routing 4 Configuration** | Local On/Off × MIDI > Synth/ArpSeq | 부분 식별 (문자열만) | 4가지 라우팅 케이스 분기 |
| **Reset Out 잭 동작** | Arp/Seq 시작 시 +5V 5ms 펄스 (3.5mm TS) | 누락 | GPIO + 타이머 펄스 |
| **Clock In/Out PPQ** | In: 2/4/24/48 PPQ — Out: 2/4/24/48 PPQ + 1PPQ/1PP2Q/1PP4Q | 누락 | Clock 분주기 |
| **Mod Quantize on User Scale** | User scale의 octave당 12 노트 토글 | 누락 | RAM scale buffer |

### 1.3 Medium — 개념·명칭 혼동 (Severity: 🟡)

| 영역 | 분석 문서 표현 | 매뉴얼 표준 명칭 | 정정 사유 |
|------|---------------|------------------|-----------|
| `Env1 / Env2` | 두 개의 ADSR | **Envelope** (4-stage ADSR, VCA hardwired) + **Cycling Envelope** (3-stage RHF, mod source) | 매뉴얼에 envelope는 공식적으로 두 개이며 명칭 분리. 펌웨어 내부 `FUN_080321d4` "Envelope Generator"가 두 envelope를 하나의 함수로 처리할 가능성 있음 — 실제 분리 검증 필요. |
| `MainAudioRender 12-voice poly` | 분석 표기 | **6 voice (Poly/Mono/Uni) / 12 voice (Para)** | Para 모드의 voice pair 구조 (6 pair × 2 = 12) 와 polyphonic 6 voice를 구분해야 함. |
| `VCF Filter Types: Multi/Surgeon/Comb/Phaser` | 분석 표기 | Analog VCF: **LP/BP/HP** (SEM 12dB/oct) — Multi/Surgeon/Comb/Phaser/Destroy: **Osc 2 Audio Processor** (별도 디지털 신호경로) | 신호경로 분리. Osc 2가 "필터로 사용"될 때 Volume = Dry/Wet. 매뉴얼 5.3 명확. |
| `MIDI CC 161개 매핑` | 분석 결과 | 매뉴얼 차트 약 50+ 명시 | 161개는 펌웨어 internal CC 핸들러 카운트일 수 있음. 매뉴얼은 "사용자 노출" CC만 게재. **internal CC 핸들러 161 ↔ 매뉴얼 차트 ~50** 간 매핑표 필요. |
| `Modulation Matrix 140 destinations` | 분석 표기 | 13 column (4 hardwired + 9 assignable). Assignable 풀은 약 30+ destination | 13 슬롯 구조 + destination 풀 개념 분리. "140"이 실제 펌웨어 destination ID 수라면 별도 표기. |
| `eFXParams: FX1_*/FX2_*/FX3_*` | 분석 RTTI 식별 | OK — 매뉴얼과 일치 | 정정 불요 |
| `vtable 0x37CB4 / 0x37D70 / ~0x386D4` | OSC1: 11 + 13 + 96 instr / OSC2: 동일 | Osc 1 = 16 type, Osc 2 = 21 type | vtable 카운트 재검증 |

---

## 2. 영역별 수정 계획

### 2.1 사운드 엔진 — `PHASE6_SOUND_ENGINE.md` 정정

#### 2.1.1 Voice Architecture 수정

**현재 (오류)**:
```
12-voice polyphonic
Voice Allocator: Max 12 voices
Modes: Poly (steal) / Poly2Mono / Legato / Unison (1-16)
```

**정정안**:
```
6-voice polyphonic (Para 시 12 voice = 6 pair × 2)
Voice Allocator: Max 6 voices in Mono/Poly/Uni, 12 in Para
Modes: Mono / Poly / Para / Uni
  - Mono: 1 voice, 이전 노트 envelope cut-off
  - Poly: 노트당 1 voice (allocation: Cycle/Reassign/Reset)
  - Para: Osc 2 deactivated, 12 voice 활성, voice pair 구조
        - Voice Envelope (개별, ADSR) — Mod Matrix source
        - Master Envelope (pair 공유, AHR)
  - Uni: 단일 노트로 다중 voice 트리거
        - Unison Count: 2~6
        - Unison Spread: 1/1000 semitone ~ 1 octave
        - Unison Mode: Mono/Poly/Para
        - Legato Mono: Mono/Uni 모드에서 retrigger 여부
```

**액션 아이템**:
- [x] Voice struct 0x118(280B)/voice 의 **실제 슬롯 수** Ghidra로 재카운트 — 6 슬롯 확정 (Phase 9-7: FUN_0812d0dc)
- [ ] Voice Allocator 함수 식별 → Cycle/Reassign/Reset 분기 매핑 (기기 필요)
- [ ] Voice Pair 구조체 (Para 모드) 식별 — Master Envelope vs Voice Envelope 분리 (기기 필요)

#### 2.1.2 신호 경로 정정

**현재 (혼동)**:
```
VCF — Digital Filter
  Filter Types:
    ├─ Multi Filter
    ├─ Surgeon Filter
    ├─ Comb Filter
    └─ Phaser Filter
```

**정정안**:
```
신호 경로 (정정):
  Osc 1 ─┬─→ Osc Mix (level/pan)
         │           │
  Osc 2 ─┴─→ ────────┤   ← Osc 2가 'Audio Processor 모드'일 때
                     │      Osc 1을 입력으로 받음
                     ▼
        ┌────────────────────────────┐
        │ Analog VCF (SEM-style)     │
        │ - 12 dB/oct 고정 슬로프    │
        │ - LP / BP / HP 3타입       │
        │ - Cutoff: 20Hz~20kHz       │
        │ - Self-oscillation 가능    │
        └────────┬───────────────────┘
                 ▼
        ┌────────────────────────────┐
        │ Analog VCA                 │
        │ - Envelope (ADSR) hardwired│
        └────────┬───────────────────┘
                 ▼
            Voice Sum
                 ▼
            Mod Matrix (post-VCA processing)
                 ▼
            FX Send (3 슬롯)


Osc 2 'Audio Processor' 모드 (매뉴얼 5.3):
  - Multi Filter: LP/Mid/BP/Notch + 6/12/24/36 dB/oct
  - Surgeon Filter: 파라메트릭 EQ-style (LP/BP/HP/Notch)
  - Comb Filter: 키보드 트래킹 hardwired
  - Phaser Filter: 2~12 pole, all-pass 체인
  - Destroy: Wavefolder + Decimator + Bitcrusher
  → 이들은 Osc 2 vtable의 'audio processor' 분기로 처리,
    Osc 1을 입력으로 받아 처리한 결과를 출력.
    Osc 2 Volume 노브 = Dry/Wet 밸런스.
```

**액션 아이템**:
- [x] Osc 2 vtable에서 audio processor 모드 vs oscillator 모드 분기 식별 — Phase 8: enum @ 0x081af4d0 (type 5~9 = Audio Processor)
- [x] Osc 1 → Osc 2 input 라우팅 코드 식별 (audio processor 모드 시) — Phase 8: Osc2 Volume = Dry/Wet
- [ ] Analog VCF 의 LP/BP/HP 타입 선택 코드 — `Vcf_Type` 파라미터 분기 (기기에서 캘리브레이션 필요)

#### 2.1.3 Oscillator Type 재카운트

**현재**: Osc 1 = 11 type, Osc 2 = 30 type

**정정 목표**:
- Osc 1 = 16 type (BasicWaves, SuperWave, Harmo, KarplusStr, VAnalog, Waveshaper, 2OpFM, Formant, Speech, Modal, Noise, Bass, SawX, Harm, **Audio In, Wavetable**) + V3 추가 (**Sample**, **Cloud Grains**, **Hit Grains**, **Frozen**, **Skan**, **Particles**, **Lick**, **Raster**) = **24 type**
- Osc 2 = 14 공통 + 7 Osc2 전용 (**Chords**, **FM/RM**, **Multi Filter**, **Surgeon**, **Comb**, **Phaser**, **Destroy**) = **21 type**

매뉴얼 1.1 도입부의 "Osc 1 16 + Osc 2 21" 표기는 V4 시점 기준일 수 있음. V3 그래뉼러 추가 후 정확한 카운트 재확인 필요.

**액션 아이템**:
- [x] OSC1 vtable @ 0x37CB4 부터 정확한 entry 카운트 — Phase 8: enum 0~20 (21 entries, shared Osc1+Osc2)
- [x] OSC2 vtable @ 0x37D70 부터 정확한 entry 카운트 — Phase 8: Osc2 전용 type 4,9,20 + Chords
- [x] vtable 각 entry → 매뉴얼 타입명 매핑표 작성 — Phase 8 COMPLETE_REPORT에 enum 21종 기재
- [x] V3에서 추가된 그래뉼러/Sample 코드 영역 식별 — Phase 8: enum index 12~20

#### 2.1.4 Envelope 명명 정정

**현재**:
```
Env1: A/D/S/R + Loop + Curve
Env2: A/D/S/R + Velocity
CycEnv: Cycling envelope
```

**정정안**:
```
Envelope (1개): 4-stage ADSR
  - VCA hardwired (default)
  - Mod Matrix source (assignable)
  - Sound Edit 옵션:
    * Velo > VCA / VCF / Env / Time
    * Retrig Mode: Env Reset / Env Continue
    * Attack Curve: Default / Quick
    * Decay Curve: Default / Percussive
    * Release Curve: Default / Percussive
  - Para 모드 시 Voice Envelope (개별) + Master Envelope (pair 공유, AHR)

Cycling Envelope (1개): 3-stage Rise/Hold/Fall + Sustain
  - Mode 3종: Env / Run / Loop
    * Env: Rise=Attack, Fall=Decay+Release, Hold=Sustain (ADSD 등가)
    * Run: 모노포닉, MIDI Start만 retrig
    * Loop: 폴리포닉, retrigger source 선택 가능
  - Stage Order: RHF / RFH / HRF
  - Retrig Source: Poly Kbd / Mono Kbd / Legato Kb / LFO 1 / LFO 2
  - Tempo Sync 옵션
  - Rise Shape / Fall Shape: -50 ~ +50 (linear @ 0)
```

**액션 아이템**:
- [x] `FUN_080321d4` (Envelope Generator) 내부 분기 — Phase 9-5: switch(5 cases, 1~5) 아프레지에이터 패턴 생성기. Envelope는 별도 함수 가능성 높음
- [ ] Cycling Envelope의 Mode 분기 코드 (Env/Run/Loop) (기기 필요)
- [ ] Stage Order (RHF/RFH/HRF) 분기 코드 (기기 필요)
- [ ] Para 모드의 Voice Envelope vs Master Envelope 분기 (기기 필요)

### 2.2 LFO — `PHASE6_SOUND_ENGINE.md` 보강

**누락 사항**:
1. **Vibrato (제3 LFO)**
   - Free-running triangle wave
   - Rate: Sound Edit > Pitch > Vib Rate
   - Depth: Sound Edit > Pitch > Vibrato Depth
   - Touch Strip 직접 제어 (Shift-touch Keyboard Bend/Wheel pad)
   - `Vib AM`, `Vib Rate` 파라미터 (Custom Assign)

2. **LFO Triggering 8 모드**
   - Free, Poly Kbd, Mono Kbd, Legato Kb, One (단일 사이클 후 정지, sawtooth/square가 unipolar로 변환), LFO (다른 LFO 트리거), CycEnv, Seq Start

3. **LFO Sync Filter**
   - Sound Edit > LFO > LFO Sync Filter: 12bar dotted ~ 1/32T 중 선별 (straight only / triplet only / dotted only)

4. **Shaper 라이브러리 구조**
   - 16 Factory waves (펌웨어 내장)
   - 8 User waves (글로벌 슬롯)
   - 2 Preset Shaper Waves (LFO1용 1, LFO2용 1, 프리셋별 저장)
   - Shaper Pattern: 최대 16 step, 각 step별 Amplitude/Slope/Curve
     * Slope: Rise / Fall / Triangle / Join
     * Curve: Exponential ~ Linear ~ Logarithmic (-100 ~ +100)

5. **Shaper Rate 모드**
   - Per-step: 16-step shaper @ 1/16 = 전체 1 bar
   - All-steps: 16-step shaper @ 1/16 = 전체 1/16 (16배 빠름)

**액션 아이템**:
- [x] Vibrato LFO 핸들러 함수 식별 — Phase 8: `Vibrato Depth` @ eEditParams, `Vib AM`/`Vib Rate` @ Mod Destinations
- [ ] LFO Triggering state machine 식별 (8 mode 분기) (기기 필요)
- [ ] Shaper Wave RAM 영역 — 16 factory + 8 user + 2 preset 의 메모리 레이아웃 (기기 필요)
- [ ] Shaper Pattern step structure (Amplitude/Slope/Curve) 식별 (기기 필요)
- [ ] Sync subdivision 테이블 (12bar dotted ~ 1/32T) 식별 (기기 필요)

### 2.3 Modulation Matrix — 구조 정정

**현재 (오류)**:
```
SOURCES (분석)              DESTINATIONS (140)
─────────                   ──────────────────
LFO1, LFO2, Env1, Env2,     Osc1 Pitch, Osc1 Shape, ...
Velocity, ModWheel,         (140 total)
PitchWheel, AfterTouch,
Macro1, Macro2, Seq Step
```

**정정안**:
```
SOURCES (7 row, 매뉴얼 명시):
  Row 1: Cycling Envelope
  Row 2: LFO 1
  Row 3: LFO 2
  Row 4: Velocity / Aftertouch  (Sound Edit > Keyboard > Matrix Src VeloAT 로 선택)
         - Velocity / AT / Both 3 모드
  Row 5: Wheel (Mod Wheel 또는 Touch Strip Wheel)
  Row 6: Keyboard (Sound Edit > Keyboard > Kbd Src 4 모드)
         - Linear / S Curve / Random / Voices
  Row 7: Mod Seq (Sequencer Mod lane)

DESTINATIONS (13 column):
  Hardwired (4):
    Col 1: Osc 1+2 Pitch (CycEnv default)
    Col 2: Osc 1+2 Shape (또는 비슷한 hardwired)
    Col 3: VCF Cutoff
    Col 4: VCA
  Assignable (9 = 3 page × 3 column):
    Page 1: Assign 1, 2, 3
    Page 2: Assign 4, 5, 6
    Page 3: Assign 7, 8, 9

  Assignable Destination 풀 (매뉴얼 8.5.5):
    Glide / Osc X Type/Wave/Timbre/Shape/Volume / Filter Cutoff/Resonance/Env Amt
    / VCA / FX X Time/Intensity/Amount
    / Envelope ADSR / CycEnv Rise/Fall/Sustain/Amp
    / LFO X Rate/Wave/Amp / Macro 1/2 / Matrix Mod Amount

  Custom (no physical control) Destinations (매뉴얼 8.5.4):
    Uni Spread / CycEnv AM / LFO1 AM / LFO2 AM / VCA / Vib AM / Vib Rate / -Empty-

매트릭스 구조 (7×13 = 최대 91 routing 동시 가능):
  Mx_Dots[91]    ── Boolean enable per routing
  Mx_Assign[91]  ── Source/Destination 인덱스 (Assignable 슬롯의 destination ID)
  Mx_Col[91]     ── Amount/depth (-100 ~ +100, bipolar)
```

**Modulating modulation amount (sidechaining)**:
- Assign 슬롯에 `LFO1 AM` / `CycEnv AM` 같은 "AM" destination 가능
- Mod Matrix의 다른 routing의 amount를 modulate하는 메타-모듈레이션
- Macro Assign에서 `Matrix Mod Amount` 가능

**액션 아이템**:
- [ ] Mod Matrix 7 row × 13 column 의 RAM 레이아웃 (`Mx_Dots`, `Mx_Assign`, `Mx_Col`) 정확히 식별
- [ ] Assignable destination 풀의 ID enum 추출 (XML resources 또는 코드 내 LUT)
- [ ] Velo/AT 통합 row 의 Matrix Src VeloAT 분기 코드
- [ ] Kbd Src 4 모드 (Linear/S Curve/Random/Voices) 의 LUT
- [ ] AM destination의 sidechaining 처리 코드
- [ ] "140 destination"이 펌웨어 내부 enum 카운트인지, 매트릭스 슬롯인지 명확화

### 2.4 MIDI 구현 — `PHASE6_MIDI_CHART.md` 전면 정정

#### 2.4.1 매뉴얼 공식 MIDI Implementation Chart

| Section | Parameter | CC# |
|---------|-----------|-----|
| MIDI | Mod Wheel | 1 |
| Pedals | Sustain | 64 |
|   | Glide | 5 |
| OSC 1 | Tune | 70 |
|   | Wave | 14 |
|   | Timbre | 15 |
|   | Shape | 16 |
|   | Volume | 17 |
| OSC 2 | Tune | 73 |
|   | Wave | 18 |
|   | Timbre | 19 |
|   | Shape | 20 |
|   | Volume | 21 |
| Analog Filter | Cutoff | 74 |
|   | Resonance | 71 |
|   | VCF Env Amt | 24 |
|   | Velocity Env Mod | 94 |
| Cycling Env | Rise Shape | 68 |
|   | Rise | 76 |
|   | Fall | 77 |
|   | Hold | 78 |
|   | Fall Shape | 69 |
| Envelope | Attack | 80 |
|   | Decay | 81 |
|   | Sustain | 82 |
|   | Release | 83 |
| LFO 1 | Rate | 85 |
| LFO 2 | Rate | 87 |
| Effects | FX1 Time / Intensity / Amount | 22 / 23 / 25 |
|   | FX2 Time / Intensity / Amount | 26 / 27 / 28 |
|   | FX3 Time / Intensity / Amount | 29 / 30 / 31 |
| Sequencer | Gate / Spice | 115 / 116 |
| Macros | M1 / M2 | 117 / 118 |

총 약 **41개 사용자 노출 CC**.

#### 2.4.2 펌웨어 내부 161개 CC 핸들러 ↔ 매뉴얼 41개 의 관계 가설

가설 A: **161 = 매뉴얼 41 + extended FX (FX1/2/3 각 ~30+ 파라미터)**
- 매뉴얼은 FX당 Time/Intensity/Amount **3 파라미터만** 노출
- 펌웨어는 각 FX에 더 많은 internal 파라미터 처리 (subtype에 따른 hidden 파라미터)
- 41 + (3 × FX 슬롯) × ~40 internal = 161 가능

가설 B: **161 = 매뉴얼 + NRPN handler 다수 + 미사용 슬롯**
- NRPN으로 14-bit 정밀도 파라미터 다수
- 분석에서 발견된 `0x081812B4` NRPN handler가 키

**액션 아이템**:
- [ ] `0x08166810` `midi_cc_handler` 의 분기 테이블 추출 — 161 entry 의 정확한 CC# → 파라미터 매핑
- [ ] 매뉴얼 41 CC 와 비교, 차이 분석
- [ ] FX subtype별 hidden 파라미터의 CC# 매핑 확인 (subtype은 매뉴얼상 미노출이지만 펌웨어는 처리)
- [ ] CC#86~186 "FX Extended 101개" 의 실제 매핑 — FX1/2/3 hidden parameter pool 가능성

#### 2.4.3 SysEx 프로토콜 보강

분석된 부분 (`F0 00 20 6B [DevID] [MsgType] [ParamIdx] [Value] F7`)은 매뉴얼에 명시되지 않은 영역. 매뉴얼은 MIDI 구현 차트만 있음. 분석이 매뉴얼보다 깊으므로 정정 불필요, 단 다음 보강:

- [ ] SysEx로 접근 가능한 파라미터 풀 식별 (펌웨어 내부 `eSynthParams` enum)
- [ ] Universal SysEx Identity Reply 응답 검증 (매뉴얼 명시 안 됨, 펌웨어 분석)

### 2.5 Sequencer & Arpeggiator — 신규 분석 필요

#### 2.5.1 Sequencer 구조

**매뉴얼 명시**:
```
- 최대 64 step (4 page × 16 step)
- Step Recording (Stop 모드, 단일 step 정밀)
  - 노트당 6 voice 까지
  - Hold/Tie 버튼: silent step 또는 step 연장
  - Overdub ON/OFF
- Real-time Recording (Play 모드, 자유 입력)
- Page navigation: Last Step + Page button
- Quick Edit: 스텝 hold + slider/encoder
- Edit per-note: Length / Velocity / 개별 note 제거

저장 데이터 (per preset):
  - Pitch (per step, up to 6 notes)
  - Note length
  - Velocity
  - Tempo
  - Time Division
  - Swing (50%~75%)
  - Gate
  - Spice
```

#### 2.5.2 Mod Sequencer 4 Lanes

**매뉴얼 명시**:
- 4 modulation track per preset
- Recordable parameter 풀 (매뉴얼 14.4.5):
  ```
  Glide / Pitch X / Osc X Type/Wave/Timbre/Shape/Volume
  / Filter Cutoff/Resonance/Env Amt / FX X Time/Intensity/Amount
  / Envelope ADSR / CycEnv Rise/Fall/Sustain
  / LFO Rate / Macro 1/2 / Pitch Bend / Mod Wheel
  ```
- Smoothing 옵션 (Sound Edit > Seq > Smooth Mod 1/2/3/4)
- Step 단위 offset 저장, real-time 녹음 시 knob 이동량 기록

#### 2.5.3 Arpeggiator

**매뉴얼 명시 8 모드**:
| 모드 | 동작 |
|------|------|
| Up | 낮은 음 → 높은 음 |
| Down | 높은 음 → 낮은 음 |
| UpDown | Up 후 Down |
| Random | uniform random pick |
| Order | 누른 순서대로 |
| Walk | 25% 이전 / 25% 현재 / 50% 다음 |
| Poly | 모든 누른 음 동시 |
| Pattern | legato 시 N step 시퀀서 자동 생성 |

**4 Modifier**:
- **Repeat**: 각 노트 2회씩
- **Ratchets**: 트리거 2배 (held)
- **Rand Oct**: 75% 정상 / 15% +1oct / 7% -1oct / 3% +2oct (ON/OFF 토글)
- **Mutate**: 75% 유지 / 5% +5th / 5% -4th / 5% +oct / 5% -oct / 3% 다음 노트와 swap / 2% 두 번째 다음과 swap (누적)

**Octave Range**: 1~4

#### 2.5.4 Spice & Dice

**매뉴얼 명시 5 영향 파라미터**:
- Velocity / Octave (±1) / Gate length / Step On/Off / Envelope Decay+Release time

Spice = 글로벌 amount, Dice = 새 랜덤 시퀀스 생성. 비파괴적 (재생 데이터에만 적용).

**액션 아이템**:
- [ ] Sequencer state machine 식별 — Step Rec / Real-time Rec / Play 모드 분기
- [ ] 64 step buffer 레이아웃 (page/step 인덱스)
- [ ] Step structure: Pitch[6] + Length + Velocity + Tie flag + On/Off flag
- [ ] Mod Sequencer 4 lane buffer + Recordable param ID enum
- [ ] Smoothing IIR (Sound Edit > Seq > Smooth Mod) 코드
- [ ] Arpeggiator 8 모드 분기 함수
- [ ] Walk 확률 LUT (25/25/50)
- [ ] Mutate 확률 LUT (75/5/5/5/5/3/2)
- [ ] Rand Oct 확률 LUT (75/15/7/3)
- [ ] Spice/Dice 랜덤 시퀀스 생성기
- [ ] Pattern 모드의 root note 가중치 (× 2) 코드

### 2.6 FX 분석 — `PHASE7-3_FX_CORE_ANALYSIS.md` 정정

**현재 11종 → 정정 13종**:

| # | FX 타입 | 매뉴얼 Subtypes | 분석 누락 |
|---|---------|----------------|-----------|
| 1 | Chorus | Default/Lush/Dark/Shaded/Single | OK |
| 2 | Phaser | Default/DefaultSync/Space/SpaceSync/SnH/SnHSync | OK |
| 3 | Flanger | Default/DefaultSync/Silly/SillySync | OK |
| 4 | Super Unison | Classic/Ravey/Soli/Slow/SlowTrig/WideTrig/MonoTrig/Wavy | OK |
| 5 | Reverb | Default/Long/Hall/Echoes/Room/DarkRoom | OK (단, 슬롯당 1개 제한) |
| 6 | Delay | Digital/Stereo/PingPong/Mono/Filtered/FilteredPingPong + Sync 변형 | OK (단, 슬롯당 1개 제한) |
| 7 | Distortion | Classic/SoftClip/Germanium/DualFold/Climb/Tape | OK |
| 8 | **Bit Crusher** | (Subtype 없음) | **누락** |
| 9 | **3 Bands EQ** | Default/Wide/Mid 1K | **누락** |
| 10 | **Peak EQ** | (Subtype 없음, Frequency/Gain/Width 직접 제어) | **누락** |
| 11 | Multi Comp | OPP/BassCtrl/HighCtrl/Tighter (분석은 5, 매뉴얼은 4 + AllUp 차이) | 슬롯당 1개 제한 |
| 12 | Vocoder Ext In | Clean/Vintage/Narrow/Gated | 부분 OK |
| 13 | Vocoder Self | Clean/Vintage/Narrow/Gated | 부분 OK |

**Insert vs Send Routing**:
- Delay와 Reverb만 Insert/Send 선택 가능
- Send 모드 시 Dry/Wet → Send Level 로 의미 변경
- Sound Edit > FX > Delay Routing / Reverb Routing

**FX 슬롯 제한**: Reverb / Delay / Multi Comp 는 한 프리셋 내 1개만 가능

**액션 아이템**:
- [ ] FX 타입 enum 재카운트 (현재 11 → 13)
- [ ] **Bit Crusher** DSP 함수 식별 — 디시메이터 + 비트 크러셔 (Destroy와 구분)
- [ ] **3 Bands EQ** vs **Peak EQ** DSP 분리 — 분석에서 EQ3만 식별, Peak EQ 누락
- [ ] Insert/Send 라우팅 분기 코드 (Sound Edit > FX 메뉴 처리)
- [ ] FX 슬롯 단일 제한 enforce 코드 (Reverb 두 개 동시 불가)
- [ ] Multi Comp Subtype 4 vs 5 매뉴얼 차이 검증

### 2.7 Hardware & I/O 보강

#### 2.7.1 Audio In Mode

**누락**:
- Line / Microphone 2 모드 (Utility > Audio > Audio In Mode)
- Microphone 모드 = Dynamic Mic용 추가 게인
- Phantom Power 미지원 (Condenser Mic 불가)
- Audio In Gain: -9 dB ~ +24 dB

**액션 아이템**:
- [ ] Audio In 게인 스테이지 분기 코드 식별
- [ ] Line vs Mic 모드 게인 차이 측정 (펌웨어 상수)

#### 2.7.2 Reset Out 잭

**누락**:
- 3.5mm TS 잭 (Clock In/Out과 별개)
- +5V 5ms 펄스 발사
- Trigger: Arp/Seq 시작 시 (internal play 또는 external start)

**액션 아이템**:
- [ ] Reset Out GPIO 식별
- [ ] 5ms 펄스 타이머 코드

#### 2.7.3 Clock PPQ 옵션

**매뉴얼**:
- Clock In: 2 / 4 / 24 / 48 PPQ
- Clock Out: 2 / 4 / 24 / 48 PPQ + 1PPQ / 1PP2Q / 1PP4Q
  - 1PP2Q = 1 pulse per half note
  - 1PP4Q = 1 pulse per whole note (LFO 트리거 등에 활용)

**액션 아이템**:
- [ ] Clock 분주기 코드 식별 (Utility > Sync > Clock In/Out Type)

#### 2.7.4 Aftertouch 명확화

**매뉴얼 (12.2)**:
> "The keyboard sends monophonic aftertouch messages, where all sounding voices are modulated by the same amount."
> "When receiving external MIDI, the MiniFreak's sound engine is compatible with polyphonic aftertouch MIDI messages"
> "The MicroFreak's touch keyboard can produce polyphonic aftertouch data due to its unique design."

**정정**: 분석 문서의 "Per-note pressure → mod matrix" 표기는 **외부 MIDI 입력 경로**에서만 유효. 키베드 자체는 mono AT.

**AT Curve 옵션**: Linear / Log / Expo
**AT Sensitivity**: Start (Low/Mid/High) + End (Low/Mid/High)

**액션 아이템**:
- [ ] AT 처리 분기: 키베드 mono AT 경로 vs 외부 MIDI Poly AT 경로
- [ ] AT Curve LUT (Linear/Log/Expo)
- [ ] AT Start/End Sensitivity 임계값 상수

### 2.8 UI/UX 시스템 — 신규 분석

#### 2.8.1 Snapshots

**매뉴얼 (4.5)**:
- 시간 기반 자동 스냅샷 (예: "1:22:26" = 부팅 후 1시간 22분 26초)
- Sound Edit > View Snapshots에서 복원
- 프리셋의 이전 편집 상태 복구용

**액션 아이템**:
- [ ] Snapshot RAM 영역 식별
- [ ] 자동 스냅샷 트리거 조건 (편집 이벤트?)
- [ ] 타임스탬프 처리 (부팅 후 millis)
- [ ] Snapshot 슬롯 수, 회전 정책

#### 2.8.2 Favorites Panel (V2)

**매뉴얼 (4.6.4)**:
- 64 슬롯 (스텝 버튼에 매핑, 여러 페이지)
- Shift + Panel 진입
- Hold Save + Step button = 저장
- Erase + Step button = 삭제
- LED: blue (저장됨) / red (현재 로드)
- Default: ON (Utility > Preset Operation > Panel Mode = Favorite Panel)
- 동일 프리셋이 여러 슬롯에 있으면 모두 red 표시

**액션 아이템**:
- [ ] Favorites RAM 영역 (64 × preset 인덱스)
- [ ] Panel Mode 분기: Favorite vs Original Panel
- [ ] LED 상태 처리 (UI Matrix MCU)

#### 2.8.3 Touch Strip 3 Mode

**매뉴얼 (3.2 / 12.7)**:
| Mode | LED 색상 | 기능 |
|------|----------|------|
| Keyboard Bend/Wheel | white | Bend (snap-to-center) + Mod Wheel |
| Keyboard + Vibrato | top blue | Bend + Vibrato (rate/depth via shift+touch) |
| Macros M1/M2 | blue | Macro 1 + Macro 2 (unipolar) |
| Macros + Assign | white pulse | Macro Assign 모드 |
| Seq/Arp Gate/Spice | orange | Gate length + Spice amount |
| Seq/Arp + Dice | shift-touch | Dice 발동 |

**액션 아이템**:
- [ ] UI Ribbon MCU 펌웨어의 모드 state machine
- [ ] Touch Strip 좌/우 매핑 변경 코드
- [ ] Vibrato Rate/Depth 의 Touch Strip 직접 매핑

#### 2.8.4 Knob Catch Modes

**매뉴얼 (15.2.4)**:
- **Jump**: 노브 만지면 즉시 노브 위치 값으로 점프
- **Hook**: 노브가 저장값 통과해야 잡힘
- **Scale**: 부드러운 비례 보정 (저장값 → 물리 위치까지 점진적)

이 모드는 **아날로그 노브 (Glide, Cutoff, Resonance, Env, Rise/Fall, Hold/Sustain, Attack, Decay, Sustain, Release)** 에만 적용. 디지털 인코더는 자동.

**Panel** 버튼 (Save 옆) = 모든 파라미터 값을 현재 물리 위치로 강제 점프 (영구).

**액션 아이템**:
- [ ] Knob Catch state machine — 각 노브별 (저장값, 물리값, 모드) 추적
- [ ] Hook/Scale 모드의 트래킹 알고리즘
- [ ] Panel 버튼 동작 코드

#### 2.8.5 Scale & Chord & Mod Quantize

**Scale (Sound Edit > Scale Config)**:
- Off / Major / Minor / Dorian / Mixolydian / Blues / Pentatonic / Global / User
- Root: C ~ B (12 semitone)
- User Scale: octave당 12 노트 토글

**Chord Mode**:
- 11 interval: Octave / 5th / sus4 / m / m7 / m9 / m11 / 69 / M9 / M7 / M
- Hold Chord + 키 = 새 코드 저장
- Mono mode에서도 작동
- Unison 모드와 호환 (각 노트가 unison spread)

**Mod Quantize (Sound Edit > Osc > Osc1/2 Mod Quant)**:
- 10 옵션: Chromatic / Octaves / Fifths / Minor / Major / Phrygian Dominant / Minor 9th / Major 9th / minor pentatonic / Major pentatonic
- Osc 1과 Osc 2 별도 설정
- Pitch modulation에만 적용 (smooth → quantized step)

**액션 아이템**:
- [ ] Scale LUT (각 모드의 12-bit mask)
- [ ] User Scale RAM 슬롯
- [ ] Chord interval 테이블 (11 interval × interval bits)
- [ ] Mod Quantize 10 모드 LUT
- [ ] Scale + Chord 조합 처리 (Chord 노트가 Scale에 맞춰짐)

---

## 3. 우선순위와 일정

### 우선순위 매트릭스

```
        영향도
         high
          │
   1️⃣ MIDI CC 정정         3️⃣ 그래뉼러/Sample/WT 분석
   1️⃣ Voice 수 정정        3️⃣ Mod Seq 4 lane
   1️⃣ Voicing Mode 정정    3️⃣ Vibrato LFO
   1️⃣ Mod Matrix 구조     3️⃣ Snapshots/Favorites
                          
         med │
   2️⃣ Envelope 명명       4️⃣ Knob Catch
   2️⃣ FX 13종 (Bit Crush) 4️⃣ Touch Strip mode
   2️⃣ Cycling Env 모드    4️⃣ Scale/Chord/ModQuant
   2️⃣ LFO Trigger 8모드   4️⃣ Audio In mode
                          
         low │
                          5️⃣ Reset Out 잭
                          5️⃣ Clock PPQ
                          5️⃣ Aftertouch 명확화
          ─┼─────────────────────────────→
            low      med      high   난이도
```

### Phase 8 실행 일정 (제안)

#### Phase 8-1: Critical 정정 (즉시)
- [ ] **MIDI CC 차트 전면 재작성** (`PHASE6_MIDI_CHART.md`)
  - 매뉴얼 41 CC 표 작성 → 우선
  - `0x08166810` midi_cc_handler 분기 테이블 추출 → 161 CC 매핑
  - 매뉴얼 41 ↔ 펌웨어 161 의 매핑 분석
- [ ] **Voice 수 / Voicing Mode 정정** (`PHASE6_SOUND_ENGINE.md`)
  - Voice struct 슬롯 카운트 검증
  - Mono/Poly/Para/Uni 분기 코드 식별
- [ ] **Mod Matrix 7×13 구조 정정** (`PHASE6_SOUND_ENGINE.md`)
  - Mx_Dots/Assign/Col 의 정확한 크기
  - 7 source row 매핑 (Velo+AT 통합 등)

#### Phase 8-2: V3/V4 신규 기능 분석 (다음)
- [ ] Granular 7 engine 분석 (Cloud/Hit/Frozen/Skan/Particles/Lick/Raster)
- [ ] Sample engine + Wavetable engine 분석
- [ ] Vocoder Ext In / Self DSP 분리 식별
- [ ] OSC1/OSC2 vtable 재카운트 → 정확한 type 수

#### Phase 8-3: 시퀀서 / 아르페지에이터 심층 분석
- [ ] Sequencer state machine + 64 step buffer 레이아웃
- [ ] Mod Sequencer 4 lane 분석
- [ ] Arpeggiator 8 모드 + 4 Modifier 분기
- [ ] Spice/Dice 랜덤 생성기

#### Phase 8-4: UI/UX 시스템 분석
- [ ] Snapshots / Favorites Panel 데이터 구조
- [ ] Touch Strip 3 모드 (UI Ribbon MCU)
- [ ] Knob Catch 모드 (Jump/Hook/Scale)
- [ ] Scale / Chord / Mod Quantize LUT

#### Phase 8-5: 보조 시스템 정정
- [ ] FX 13종 (Bit Crusher / Peak EQ 추가)
- [ ] Envelope vs Cycling Envelope 명명 정정
- [ ] LFO Triggering 8 모드 + Vibrato
- [ ] Audio In Mode + Reset Out + Clock PPQ + AT Curve

---

## 4. 검증 방법론

### 4.1 코드 ↔ 매뉴얼 대조 절차

각 영역 검증 시 다음 단계 수행:

1. **매뉴얼 정확 인용**: 매뉴얼의 해당 섹션 페이지/번호 기록
2. **펌웨어 코드 식별**: Ghidra 함수 주소 + 디스어셈블 발췌
3. **RTTI/문자열 증거**: 관련 enum 명, RTTI string 인용
4. **MIDI Implementation chart 대조**: 공식 차트 ↔ midi_cc_handler 분기 결과
5. **MiniFreak V Editor 대조** (선택): XML resource의 파라미터 정의 ↔ 코드 동작
6. **하드웨어 검증** (Phase 9 이후): MIDI Monitor로 실제 송수신 캡처

### 4.2 Hallucination 방지 원칙

Phase 7의 마지막에 사용자가 지적한 hallucination 위험을 의식하여:

- **추정**과 **확인된 사실**을 명확 분리
- 추정 근거 기록 (예: "X 패턴이 Plaits 코드와 95% 일치, 따라서 ~"). Plaits 외 코드는 함수 크기·문자열·외부 호출만으로 추정 — 별도 표기.
- 매뉴얼이 명시한 사항은 **최우선 정확 정보**로 취급. 펌웨어 분석이 매뉴얼과 충돌 시 매뉴얼이 정답에 가까울 가능성이 높음 (단, 매뉴얼이 internal/hidden 동작을 누락할 수도 있으므로 차이의 *원인*을 분석)
- 함수 명명 시 `FUN_080xxxxx` 원본 주소 보존 + 추정 명칭 병기
- 휴리스틱 분석의 한계 인지: vtable 카운트, audio_score, RTTI 매칭 등은 **참고 지표**이며 정답이 아님

### 4.3 우선 검증 도구

| 도구 | 용도 |
|------|------|
| Ghidra 12.0.4 + PyGhidra | 디컴파일 / 분기 테이블 추출 / vtable 카운트 |
| MIDI-OX / MidiPipe | 실제 펌웨어 ↔ MiniFreak V 통신 캡처 |
| MiniFreak V XML resource | 파라미터 enum / destination 풀 / FX subtype 매핑 |
| Plaits source (MIT) | OSC type 알고리즘 대조 |
| Mutable Instruments Blades | Multi/Surgeon/Comb/Phaser 알고리즘 대조 |
| RBJ Audio EQ Cookbook | EQ3 / Peak EQ 계수 대조 |
| Pedalboard / Audio-Effects | FX (Chorus/Phaser/Flanger/Delay/Reverb) 알고리즘 대조 |

---

## 5. 산출물 (Deliverables)

Phase 8 완료 시 다음 문서들이 정정/생성되어야 함:

| 문서 | 변경 유형 | 비고 |
|------|-----------|------|
| `PHASE6_MIDI_CHART.md` | 전면 재작성 | 매뉴얼 41 CC + 펌웨어 161 CC 매핑 |
| `PHASE6_SOUND_ENGINE.md` | 대폭 정정 | Voice 수, Mod Matrix 구조, Envelope 명칭, 신호 경로 |
| `PHASE7-3_FX_CORE_ANALYSIS.md` | 11→13 FX 추가 | Bit Crusher, Peak EQ 분석 추가 |
| `PHASE6_ARCHITECTURE.md` | 부분 정정 | Voice 6/12, Filter 분리 |
| `PHASE8_GRANULAR_ENGINES.md` | 신규 | V3 추가 7 그래뉼러 + Sample + Wavetable |
| `PHASE8_SEQUENCER_DEEP.md` | 신규 | Sequencer + Mod Seq 4 lane + Arp 8 mode + Spice/Dice |
| `PHASE8_UI_SYSTEMS.md` | 신규 | Snapshots / Favorites / Touch Strip / Knob Catch |
| `PHASE8_LFO_DEEP.md` | 신규 | LFO Trigger 8 모드 + Shaper 라이브러리 + Vibrato |
| `PHASE8_SCALE_CHORD.md` | 신규 | Scale / Chord / Mod Quantize LUT |
| `PHASE8_MANUAL_GAP_ANALYSIS.md` | 본 문서 | Phase 8 진행에 따라 갭 항목 체크 |

### 검증 체크리스트

Phase 8 완료 기준:

- [ ] 매뉴얼 모든 챕터 (1~16) 가 분석 문서에 1:1 대응
- [ ] MIDI CC 차트 41/41 매뉴얼 ↔ 펌웨어 매핑 검증
- [ ] OSC1 16+ type / OSC2 21 type vtable 식별
- [ ] FX 13 type DSP 함수 식별
- [ ] Mod Matrix 7×13 구조 메모리 레이아웃 확정
- [ ] Voice struct 6 (또는 12) slot 확정
- [ ] V3 그래뉼러 7 engine + Sample + Wavetable 코드 식별
- [ ] V4 Vocoder Ext In/Self DSP 식별
- [ ] Snapshots / Favorites RAM 영역 식별
- [ ] Sequencer + Mod Seq + Arp 모드 분기 식별

---

## 6. 후속 단계 연결

Phase 8 완료 후:

- **Phase 9** (실제 패치 시도, 하드웨어 필요): 정정된 매핑 기반으로 안전하게 패치 시도
- **Phase 10** (물리 분석): UI MCU 통신 프로토콜, SPI 페리페럴 (CM7), Audio Codec 칩 식별 — UI Ribbon MCU의 Touch Strip 3 모드 분석은 Phase 10과 연동
- **MNFX Editor 도구 확장**: 정확한 destination 풀 / FX subtype 매핑으로 편집 도구 보강
- **MIDI SysEx 도구 확장**: 161 CC 핸들러 매핑 기반으로 외부 컨트롤러 매핑 자동화

---

## 부록 A: 매뉴얼 인용 및 펌웨어 분석 충돌 케이스

분석에서 **매뉴얼과 다르지만 분석이 옳을 가능성**이 있는 케이스 (검증 필요):

1. **VID/PID `0x1C75 / 0x0602`** — 매뉴얼 미명시, 분석은 펌웨어에서 추출. 신뢰도 ⭐⭐⭐⭐⭐
2. **STM32H745/747 듀얼코어** — 매뉴얼 미명시, 분석은 RTOS 메시지 + 페리페럴 매핑으로 추정. 신뢰도 ⭐⭐⭐⭐⭐
3. **FX 코어 ARM (DSP56362 아님)** — 분석에서 정정됨. 신뢰도 ⭐⭐⭐⭐⭐
4. **161 CC handler** — 매뉴얼 41 CC와의 차이는 hidden parameter 가능성. 검증 필요.
5. **eSeqAutomParams: AutomReserved*** — 매뉴얼은 4 mod sequence lane만 명시. 펌웨어 자동화 reserved 슬롯이 더 많을 수 있음.
6. **Plaits 7종 + Noise Engineering 3종 (BASS/SAWX/HARM)** — 매뉴얼 5장 도입부 명시. 분석과 일치.
7. **펌웨어 CRC 부재** — 매뉴얼 미명시 (사용자 입장에서 무관). 분석 결과 패치 가능성 시사.

---

*이 문서는 Phase 8 진행에 따라 각 갭 항목 옆 체크박스가 채워지며,
완료 후 `PHASE8_FINAL_VERIFICATION.md`로 정리되어 Phase 9의 입력이 됨.*