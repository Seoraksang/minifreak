# Phase 10: 하드웨어 + MiniFreak V 매뉴얼 통합 대조 검증 계획

> **2026-04-26** | fw4_0_1_2229 + MiniFreak V 4.0.2.6369 vs **양쪽 공식 매뉴얼 v4.0.1**
> **이전 산출물**: `PHASE8_MANUAL_GAP_ANALYSIS-2.md`, `PHASE8_COMPLETE_REPORT.md`, `PHASE8_1_RESULTS.md`, `PHASE8_FX_OSC_ENUMS.md`, `PHASE8_SEQ_ARP_MOD.md`, `PHASE9_RESULTS.md`
> **신규 입력**: MiniFreak V User Manual v4.0.1 (151p, 2025-07-04 개정)

---

## 0. 본 문서의 목적과 범위

이전 `PHASE8_MANUAL_GAP_ANALYSIS-2.md`(이하 "Phase 8 갭")는 **하드웨어 매뉴얼만**을 기준으로 작성되었음. 이번 Phase 10에서는:

1. **Phase 8 갭 처리 진척도**를 정량화 (✅/⚠️/❌)
2. **MiniFreak V 매뉴얼 신규 영역**을 추가 (Phase 8 갭에 없던 부분)
3. **두 매뉴얼 간 충돌 항목** 식별 및 펌웨어/플러그인 어느 쪽이 옳은지 판정 절차 정의
4. **Phase 8 갭에 있으나 Phase 10에서 누락된 항목**을 보완 (§1.5)
5. **두 매뉴얼이 일치하나 분석에 누락된 영역**을 정리 (§5)
6. **남은 미완료 항목** 우선순위 재조정

---

## 1. Phase 8 갭 처리 진척도 (요약)

### 1.1 Critical (🔴) — 모두 완료 ✅

| Phase 8 갭 항목 | 상태 | 근거 산출물 |
|----------------|------|-------------|
| MIDI CC 매핑 정정 (Cutoff 24→74, Resonance 25→71 등) | ✅ **완료** | `PHASE6_MIDI_CHART_v2.md` — 매뉴얼 41 CC 모두 펌웨어 case에 존재 확인 |
| Voice 수 (12→6) | ✅ **완료** | `PHASE9_RESULTS.md` §9-7 — `FUN_0812D0DC` switch/case 0~7, voice struct 0x118 / stride 0x250 |
| Voicing Mode (Poly2Mono/Legato → Mono/Poly/Para/Uni) | ✅ **완료** | `PHASE8_1_RESULTS.md` — Voice Mode enum @ 0x081af4f4 |
| Mod Matrix 구조 (140 dest → 7×13) | ✅ **완료** | `PHASE8_1_RESULTS.md` — Source enum 9 (V3 Sample/Wavetable Select 추가), Dest enum 9 hardwired |
| Aftertouch (mono/poly 명확화) | ✅ **완료** | `PHASE6_MIDI_CHART_v2.md` §6 |
| Bend Range (±2 default → ±1~±12 가변) | ✅ **완료** | `PHASE6_MIDI_CHART_v2.md` §7 |
| 신호 경로 (Multi/Surgeon/Comb/Phaser → Osc 2 Audio Processor) | ✅ **완료** | `PHASE8_COMPLETE_REPORT.md` §8-3.2 |

### 1.2 High (🟠) — 대부분 완료, 일부 검증 단계

| Phase 8 갭 항목 | 상태 | 근거 / 미흡 사유 |
|----------------|------|------------------|
| 그래뉼러 7 엔진 (Cloud/Hit/Frozen/Skan/Particle/Lick/Raster) | ✅ **확인** | Osc Type enum index 14~20 @ `0x081af474` |
| Sample 엔진 | ✅ **확인** | Osc Type #13, "Sample Select" mod source |
| Wavetable 엔진 | ✅ **확인** | Osc Type #12, "Wavetable Select" mod source |
| Vibrato (제3 LFO) | ✅ **확인** | `Vibrato Depth` (eEditParams), `Vib Rate`/`Vib AM` (Mod Dest) |
| Arpeggiator 8 모드 + 4 Modifier | ✅ **확인** | 8 모드 + 4 modifier 문자열 모두 존재 (`PHASE8_SEQ_ARP_MOD.md` §1) |
| Mod Sequencer 4 lane | ✅ **확인** | `Seq Mods` @ 0x081aed6c, `Smooth Mod 1~4` |
| Snapshots / Favorites Panel | ✅ **확인** | UI 문자열 식별 |
| Spice/Dice 확률 LUT | ✅ **발견** | CM7 @ `0x08067FDC` 지수 분포 테이블 (`PHASE9_RESULTS.md` §9-5) |
| Arp Walk 확률 분포 | ✅ **발견** | CM7 @ `0x080546C4` 8슬롯 × 8 step LUT |
| LFO Triggering 8 모드 | ⚠️ **부분 완료** | `LFO1 Retrig` enum 식별, 그러나 8 모드 분기 함수 미식별 |
| LFO Shaper 라이브러리 (16F+8U+2P) | ⚠️ **부분 완료** | Shaper 파라미터는 식별, factory 16개 메모리 레이아웃 미확정 |
| Cycling Envelope 모드 (Env/Run/Loop) + Stage Order | ⚠️ **부분 완료** | enum 문자열 식별, 분기 코드 미디컴파일 |
| Audio In Mode (Line/Mic) | ⚠️ **부분 완료** | Audio In은 OSC type #11 식별, Mic vs Line 분기 미확정 |
| Reset Out 잭 (5ms +5V 펄스) | ❌ **미완료** | GPIO 매핑 미식별 |
| Clock PPQ 옵션 (1PP4Q 등) | ❌ **미완료** | Clock 분주기 코드 미식별 |
| Knob Catch 3 모드 (Jump/Hook/Scale) | ❌ **미완료** | Settings enum에 항목 존재 추정, 분기 미확인 |
| Touch Strip 3 모드 (UI Ribbon MCU) | ❌ **미완료** | UI MCU 펌웨어 자체는 분석되었으나 모드 분기 미식별 |
| AT Curve / AT Sensitivity | ⚠️ **부분 완료** | eSettingsParams 추정 |

### 1.3 Medium (🟡) — 명칭/카운트 정정 모두 완료

| Phase 8 갭 항목 | 상태 |
|----------------|------|
| Env1/Env2 → Envelope + Cycling Env | ✅ **완료** |
| FX 11종 → 13종 (Bit Crusher, Peak EQ 추가) | ✅ **완료** — `PHASE8_FX_OSC_ENUMS.md` 13개 모두 식별 + 서브프로세서 매핑 |
| OSC1 / OSC2 type 카운트 | ✅ **완료** — OSC1 24종, OSC2 21종 (Phase 8 FX/OSC enum 문서) |

### 1.4 신규 발견 사항 (Phase 8 갭에 없던 보너스)

| 발견 | 위치 / 가치 |
|------|------------|
| eSynthParams 145개 파라미터 정리 | `PHASE8_ESYNTHPARAMS_ENUM.md` |
| FX 13종 + 7 서브프로세서 매핑 | `PHASE8_FX_OSC_ENUMS.md` — Chorus → SP6 등 |
| FX subtype 63종 enum | VST XML 교차 검증 |
| Smoothing IIR 20개 함수 + NEON SIMD 패턴 | `PHASE9_RESULTS.md` §9-5 |
| Envelope time scale 64-entry LUT (1/n 패턴) | `0x0806D330` |
| FX Singleton 제약 (Reverb/Delay/MultiComp 슬롯당 1개) | `PHASE8_FX_OSC_ENUMS.md` §1-4 |
| Voice Steal 5-tick timeout 메커니즘 | `PHASE9_RESULTS.md` §9-7 |
| Preset load 체인: FUN_081639bc → FUN_0816f748 → FUN_08158a38 (197 param) | `PHASE9_RESULTS.md` §9-8 |
| Q15 고정소수점 스케일링 (0x7FFF = 1.0) | `PHASE9_RESULTS.md` §9-8 |
| Mod depth NRPN 채널 0xAE~0xB1 | `PHASE9_RESULTS.md` §9-8 |
| 13-column int16 대각선 슬라이딩 윈도우 배열 (Mod Matrix 템플릿) | `PHASE9_RESULTS.md` §9-8 |
| CC→Param indirect dispatch: vtable 기반 간접 호출 (런타임 다형성) | `PHASE9_RESULTS.md` §9-8 |

### 1.5 Phase 8 갭에 있었으나 Phase 10에서 누락된 High 항목 (보완)

Phase 8 갭 분석(`PHASE8_MANUAL_GAP_ANALYSIS-2.md`)에 존재했으나 초안 Phase 10에서 빠져 있던 항목들:

| Phase 8 갭 항목 | Phase 10 초안 상태 | 근거 / 보완 필요 |
|----------------|-------------------|------------------|
| **Scale 9종** (Off/Major/Minor/Dorian/Mixolydian/Blues/Pentatonic/Global/User) + Root 12 semitone | ❌ **누락** | Phase 8 갭 §2.8.5. CM4 문자열 스캔에서 Scale 9개 확인됨 (Phase 8-4g). Scale LUT(12-bit mask per mode) 미식별 |
| **Chord Mode 11 interval** (Octave/5th/sus4/m/m7/m9/m11/69/M9/M7/M) | ❌ **누락** | Phase 8 갭 §2.8.5. CM4에서 Chord 12 문자열 확인됨. Chord interval 테이블 미식별 |
| **Mod Quantize 10종** (Chromatic/Octaves/Fifths/Minor/Major/PhrygDom/Min9th/Maj9th/MinPent/MajPent) | ❌ **누락** | Phase 8 갭 §2.8.5. CM4에서 ModQuant 10개 확인됨. Pitch quantize LUT 미식별 |
| **Sequencer 64-step 구조** (Step Rec/Real-time Rec/Overdub, Hold/Tie, Page nav) | ❌ **누락** | Phase 8 갭 §2.5.1. `FUN_08029390` state machine (6 cases)은 Phase 9에서 발견. Step buffer 레이아웃 미확정 |
| **MIDI Routing 4 Configuration** (Local On/Off × MIDI > Synth/ArpSeq) | ❌ **누락** | Phase 8 갭 §2.7. MIDI routing 문자열은 CM4에서 확인, 4가지 라우팅 case 분기 미식별 |
| **Velocity Curve** (Linear/Log/Expo) | ❌ **누락** | Phase 8 갭 §2.7.4. AT Curve와 별도. UI Kbd MCU 또는 CM4의 velocity response LUT |
| **FX Insert/Send 라우팅** (Delay/Reverb만 Insert↔Send 전환, Dry/Wet→Send Level) | ❌ **누락** | Phase 8 갭 §2.6. FX 슬롯 제한(Reverb/Delay/MultiComp=1개)은 확인, Insert/Send 분기 미식별 |
| **Panel 버튼 동작** (Save 옆 Panel = 모든 파라미터를 현재 물리 위치로 강제 점프) | ❌ **누락** | Phase 8 갭 §2.8.4. Knob Catch와 연동. UI Matrix MCU에서 처리 추정 |
| **Spice/Dice 랜덤 시퀀스 생성기** (5 영역: Velocity/Octave/Gate/StepOnOff/EnvDecay+Release) | ❌ **누락** | Phase 8 갭 §2.5.4. 확률 LUT은 발견(Phase 9), 실제 마스크+변형 로직 미식별 |
| **Preset Type Dispatcher** (`FUN_081639bc`, 20 cases) | ⚠️ **간접 언급** | Phase 9 §9-8에서 발견했으나 Phase 10에 별도 항목으로 누락. 20 type × 197 param 처리 구조 |
| **Oscillator Type enum 전체 21종 명칭** | ⚠️ **부분** | §3.1에서 카운트만 언급. Phase 8 COMPLETE_REPORT에 0~20 전체 명칭 있으나 Phase 10에는 반영 안 됨 |

> **종합**: Phase 8 갭의 **Critical/Medium은 100% 처리**, **High는 ~60% 처리** (초안에서 누락된 11항목 포함 시 재산정).
> 잔여 항목은 **runtime/HW 분기 코드** 영역과 **Phase 8 갭에서 식별했으나 Phase 10 초안에 미반영된 항목**들임.

---

## 2. MiniFreak V 매뉴얼 신규 영역 (Phase 8 갭에 없던 부분)

이전 분석은 펌웨어 중심이었으므로, **소프트웨어(VST/AU) 측 영역**은 누락되어 있음. 펌웨어 분석 단독으로는 도달할 수 없는 V 전용 영역과, 펌웨어-V 간 통신을 통해 식별해야 할 영역이 다수 존재.

### 2.1 V 전용 기능 (펌웨어와 무관)

| 영역 | V 매뉴얼 명시 | 분석 기존 상태 | 액션 |
|------|--------------|---------------|------|
| **플러그인 형식** | VST2 / VST3 / AU / AAX (Win10+, macOS 10.13+, Apple Silicon) | Phase 5에서 JUCE 7.7.5 + Intel IPP 식별 | OK — 매뉴얼과 일치 |
| **Standalone 모드** | 별도 Audio MIDI Settings 다이얼로그 (Device/Output/Input/Buffer/Sample Rate/Tempo) | 미분석 | ⚪ 우선순위 낮음 — JUCE AudioDeviceManager 표준 동작 |
| **Sidebar 3 탭** | Settings / MIDI / Tutorials | 미분석 | ⚪ 우선순위 낮음 |
| **MIDI Learn 시스템** | per-control 매핑, Min/Max scaling, Absolute/Relative, Add Control 메뉴 | 미분석 | 🟢 추가 분석 — JUCE midiLearnManager 패턴 |
| **MIDI Configurations** | `.mnfxmidi` 파일 export/import, 컨트롤러별 프로파일 | **신규 파일 형식** | 🟢 포맷 리버싱 필요 |
| **4개 소프트웨어 Macro** | M1/M2 (HW와 동일) + M3=Brightness, M4=Timbre (V 전용 기본값) | 펌웨어는 Macro 1/2만 식별 | 🔴 **충돌 — §3.4 참조** |
| **Tutorials 시스템** | 인터랙티브 단계별 튜토리얼 + Tutorial Preset 자동 로드 | 미분석 | ⚪ 우선순위 낮음 |
| **In-app Sound Store** | Sound Bank 구매/설치 | 미분석 | ⚪ 우선순위 낮음 |
| **Resize Window** | 50%~200%, Cmd/Ctrl ± 단축키 | 미분석 | ⚪ 우선순위 낮음 — JUCE setResizeLimits |

### 2.2 V ↔ HW 통신 (Link 시스템)

V 매뉴얼 §2.5와 §8.5는 **Link button** 누른 후 V와 HW가 "brain to brain" 동기화된다고 명시. 이는 Phase 5에서 식별된 **Collage protocol over USB Bulk** (libusb, Vendor Interface #0)에 해당.

| 영역 | V 매뉴얼 명시 | 분석 기존 상태 |
|------|--------------|---------------|
| **Link button** | V → HW 양방향 sync, "brain to brain" | Phase 5 Collage protocol 식별, 4 service domain (Data/Resource/System/Security) |
| **Backup To Computer** | 512 프리셋 전체 백업, 시간 기반 명명 (YYYYMMDDHHMMSS) | Phase 5 boost::serialization 프리셋 포맷 식별 |
| **Send to MiniFreak / Init / Copy / Paste / Rename** | V에서 HW 프리셋 슬롯 직접 조작 | Collage Data domain 추정, 명령 코드 미식별 |
| **HW knob/buttons → V UI 실시간 반영** | HW 컨트롤 변경이 V UI에 즉시 반영 | SysEx 또는 Collage control message 추정 |
| **Hardware Transposition** | preset별 transposition을 HW에 저장 | eEditParams 추정 |
| **FW Update from V** | V 하단 툴바 FW Update 버튼 → HW 펌웨어 갱신 | Phase 5 DFU/Rockchip/Collage 3 경로 식별 |

**우선순위**: 🟢 **High** — Collage protocol의 **command opcode 매핑**을 완성하면 V 외부에서도 HW 제어 가능. MNFX Editor 도구 확장에 직결.

### 2.3 Side-chain Vocoder 라우팅

V 매뉴얼 §1.4.1.1: "For the Minifreak V, the Ext In requires you to route the audio from the audio channel desired to the side-chain input of the Minifreak V in your DAW."

→ **HW 매뉴얼에는 없는 V 전용 동작**. HW는 Audio In 잭을 사용, V는 DAW의 side-chain 입력을 사용.

**액션**: V 플러그인 내부에서 side-chain 버스를 어떻게 carrier/modulator 분리에 라우팅하는지는 Phase 5의 JUCE side-chain bus 분석으로 별도 진행 가능. JUCE `juce::AudioProcessor::getBus` 패턴으로 side-chain bus index 식별.

### 2.4 In-app Preset Browser 메타데이터

V 매뉴얼 §8 (Preset Browser):

| 메타데이터 | 펌웨어 기존 분석 |
|-----------|---------------|
| **Type** (14종 카테고리: Bass, Brass, E.Piano 등) | HW 매뉴얼과 동일 — 부분 식별 |
| **Style** (Genres, Styles, Characteristics 3 sub) | V 전용 상세 분류 |
| **Bank** (Factory + User) | Phase 5 .mnfx 포맷 |
| **Liked Presets** (heart icon) | V 전용 |
| **MY FAVORITES** (color-coded groups) | V 전용 |
| **Comments / Designer name** | 부분 식별 (eSettingsParams의 `Sound Designer`) |

**우선순위**: 🟢 .mnfx 메타데이터 포맷 추가 분석으로 Phase 5 결과 보강 가능.

---

## 3. 두 매뉴얼 간 충돌 항목 (검증 필요)

매뉴얼 간 명시 사양이 다른 항목들. 어느 쪽이 펌웨어/V 실측과 일치하는지 결정해야 함.

### 3.1 OSC Type 카운트

| 출처 | OSC1 | OSC2 |
|------|------|------|
| HW 매뉴얼 §1.1 | "16 different oscillator types" | "21 different modes" |
| HW 매뉴얼 §5.2 (도입부) | "Osc 1 has two of its own (Audio In & Wavetables)" + V3 7 Granular + Sample = **24** | "21 (Osc 2 has six unique Types... as well as an additional chord Engine)" |
| **V 매뉴얼 §1.1** | **"24 different oscillator types"** ✅ | **"21 different modes"** ✅ |
| 펌웨어 enum (Phase 8) | 24종 ✅ | 21종 ✅ |

**펌웨어 enum 상세** (`PHASE8_COMPLETE_REPORT.md`):
```
 0: Noise          7: Comb Filter (AP)    14: Cloud Grains
 1: Bass           8: Phaser Filter (AP)  15: Hit Grains
 2: SawX           9: Destroy             16: Frozen
 3: Harm           10: Dummy              17: Skan
 4: FM / RM        11: Audio In           18: Particle
 5: Multi Filter   12: Wavetable ← V3     19: Lick
 6: Surgeon Filter 13: Sample ← V3        20: Raster
```
> Osc1은 index 0~20 중 type 4(FM/RM)와 5~9(Audio Processor) 제외 → 24종. Osc2는 21종 (Phase 8 enum에서 Dummy 항목 처리 논의 있음).

**판정**: V 매뉴얼이 정확. HW 매뉴얼 §1.1의 "16"은 도입부 요약에서 V3 추가 엔진을 누락한 표기.

**액션**: ✅ 분석 문서에 "HW 매뉴얼 §1.1의 '16'은 V3 이전 카운트, 실제는 24" 메모 추가.

### 3.2 Cycling Envelope: 3-stage vs 4-stage

| 출처 | 표기 |
|------|------|
| HW 매뉴얼 §3.1.8 | "extra **three-stage** envelope or as a looping waveform" |
| V 매뉴얼 §1.1 | "extra **4-stage** envelope or as a looping waveform" |
| HW 매뉴얼 §10.4.1 (Env mode) | "ADSD envelope" (=4-stage), Rise=Attack, Fall=Decay+Release, Hold=Sustain |
| V 매뉴얼 §4.4.3.1 | "ADSD envelope" (=4-stage) |

**판정**: 두 매뉴얼이 **자체적으로 모순**. 도입부에서 HW=3, V=4로 다르나, 상세 설명은 둘 다 ADSD(=A,D,S,D 4-stage)로 동일. 실제 펌웨어 동작은 **Run/Loop 모드는 3-stage RHF, Env 모드는 4-stage ADSD**로 보임.

**판정 근거**: 매뉴얼 §10.4.2 (HW), §4.4.3.2 (V) 모두 "Run mode: a **3-stage** envelope, with Rise, Fall, and Hold times" 명시.

**펌웨어 측 보강**: 펌웨어 파라미터는 Rise/Fall/Hold 3개 (CC#76/77/78) + Rise Shape/Fall Shape 2개 (CC#68/69). Env 모드에서 Sustain이 추가로 활성화되는지, 아니면 Hold가 Sustain 역할을 겸하는지는 분기 코드 분석 필요 (Phase 10-4-2).

**액션**: 분석 문서에 "Env mode = 4-stage ADSD, Run/Loop mode = 3-stage RHF" 명확히 정정.

### 3.3 Filter Cutoff 범위

| 출처 | 범위 |
|------|------|
| HW 매뉴얼 §6.2.2 | "roughly **20 Hz to 20 kHz**" |
| V 매뉴얼 §3.2.3 | "roughly **30 Hz to 15 kHz**" |

**판정**: 차이의 가능성:
- HW = 아날로그 필터의 이론적 가청 범위 (20 Hz~20 kHz)
- V = 디지털 모델링 필터의 실제 동작 범위 (30 Hz~15 kHz, 안티앨리어싱 마진)
- 또는 단순 매뉴얼 편집 오류

**액션**: 펌웨어 CV calibration 분석에서 Cutoff DAC 코드 → 주파수 매핑의 실제 lo/hi 한계 확인. `CvCalib` 클래스의 `getCalibCutValue` 함수에서 DAC value 범위 추출.

### 3.4 Macro 개수 (충돌 — 핵심 이슈)

| 출처 | Macro 개수 |
|------|-----------|
| HW 매뉴얼 §13 | **2개** (M1, M2), Touch Strip 매핑 |
| V 매뉴얼 §4.7.1 | **2개** (M1, M2), Touch Strip 매핑 |
| V 매뉴얼 §7.2.3 (Side Panel Macros) | **4개** (M1, M2 + Brightness, Timbre 추가), 자유 라우팅 |
| 분석 펌웨어 enum | **2개** (`Macro1 dest`, `Macro2 dest`, `Macro1 amount`, `Macro2 amount`) |

**판정**:
- **HW + 펌웨어**: 2 Macro만 존재 (M1=CC117, M2=CC118)
- **V 추가 Macro 3, 4 (Brightness, Timbre)**: V 플러그인 내부에서만 동작하는 추가 매크로. HW에는 없음.
- 즉 V는 HW 매크로 2개를 그대로 미러링하면서, **소프트웨어 전용 매크로 2개**를 따로 보유.

**펌웨어 측 검증 포인트**: `eEditParams` enum에 `[UnisonOn DEPRECATED]` 항목이 존재함 (Phase 8 확인). 사용 중단된 슬롯이 Macro 3/4 용도로 재활용되었을 가능성은 낮음 (DEPRECATED 마크가 명시되어 있음).

**액션**:
- 분석 문서에 "Macro 1/2는 HW + V 양쪽, Macro 3/4 (Brightness/Timbre)는 V 전용" 명시
- V 측의 Macro 3/4 destination 라우팅이 HW로 전송되는지 (즉 V → HW Collage protocol을 통해 HW의 어떤 파라미터로 매핑되는지) 검증

### 3.5 Audio In 처리 파라미터

| 출처 | 파라미터 |
|------|---------|
| HW 매뉴얼 §5.2.16 | Fold / Decimate / **Noise** |
| V 매뉴얼 §3.1.3.16 | Fold / Decimate / **BitCrush** |

**판정**: V 매뉴얼이 더 최신/정확할 가능성. 매뉴얼 표기는 "Noise"(HW) vs "BitCrush"(V). 그러나 두 동작이 완전히 다른 DSP인지, 아니면 동일 DSP의 명칭 변경인지는 펌웨어 분석 필요.

**주의**: "Destroy" type (enum #9)에도 Wavefolder + Decimator + Bitcrusher가 포함되어 있음 (`PHASE8_FX_OSC_ENUMS.md`). Audio In의 BitCrush/Noise가 Destroy type과 동일한 DSP 체인을 재사용하는지 확인 필요.

**액션**: Osc Type #11 (Audio In)의 실제 DSP 처리 함수에서 Param3이 어떤 DSP를 호출하는지 추적.

### 3.6 키보드 옥타브

| 출처 | 표기 |
|------|------|
| HW 매뉴얼 §3.1.5 | Octave 버튼 ±3 옥타브 |
| HW 매뉴얼 §1.1 | "37-note Arturia Slim Keys keybed" |
| V 매뉴얼 §4.5 | "37-note onscreen keyboard" + Z/X 키로 옥타브 시프트 |

**판정**: 일치. HW=물리 ±3, V=가상 ±n.

### 3.7 Filter Type "All Pass"

V 매뉴얼 §3.2.2:
> "All Pass: A filter that lets all frequencies through. Believe it or not, this kind of filter is quite useful! ... it doesn't remove any audio, passing through an AP filter will shift the phase"

HW 매뉴얼은 All Pass를 **Phaser Filter (Osc 2)**의 구성 요소로만 언급, primary VCF에는 LP/BP/HP만.

**판정**: V는 학술적 설명용으로 All Pass를 언급한 것. primary VCF에는 두 매뉴얼 모두 LP/BP/HP만 명시 (일치). 펌웨어 enum에서도 아날로그 VCF는 LP/BP/HP 3종만.

### 3.8 Oscillator Type enum 명칭 불일치 (신규 충돌)

| Phase 8 COMPLETE_REPORT | HW 매뉴얼 §5.2 대조 |
|------------------------|---------------------|
| `0: Noise` | BasicWaves (Noise 포함) |
| `1: Bass` | Noise Engineering BASS |
| `2: SawX` | Noise Engineering SAWX |
| `3: Harm` | Noise Engineering HARM |
| `4: FM / RM` | 2OpFM / RingMod |

**주의**: Phase 8 COMPLETE_REPORT의 enum은 **Osc Type enum (공통 21 entry)**이고, 이것이 Osc1의 24종과 어떻게 대응되는지 명확하지 않음. Osc1의 BasicWaves/SuperWave/Harmo/KarplusStr/VAnalog/Waveshaper/Formant/Speech/Modal 등은 enum에서 어떻게 분리되는가?

**액션**: Phase 8 enum 21 entry ↔ Osc1 24종 ↔ Osc2 21종의 정확한 대응표 작성. enum index가 Osc1과 Osc2에서 같은 type을 가리키는지, 아니면 별도 인덱싱인지 확인.

---

## 4. 미완료 항목 우선순위 재조정

Phase 8에서 완료되지 않은 ⚠️/❌ 항목 + §1.5에서 누락된 항목 + 본 Phase 10에서 신규 식별된 V 영역을 재정렬.

### 4.1 우선순위 매트릭스 (재정렬)

```
영향도
 high │
      │  1️⃣ Collage protocol opcode      3️⃣ MIDI Learn 시스템
      │     매핑 완성                       (V 전용)
      │  1️⃣ V Macro 3/4 → HW 매핑       3️⃣ .mnfxmidi 포맷
      │  1️⃣ CC#86~186 정확한 매핑       3️⃣ Sound Bank 메타데이터
      │  1️⃣ Osc Type enum 대응표        3️⃣ Sequencer 64-step buffer
      │
  med │  2️⃣ LFO Triggering 8 모드       4️⃣ Knob Catch 3 모드
      │  2️⃣ Cycling Env 모드 분기      4️⃣ AT Curve / Sensitivity
      │  2️⃣ Audio In Mode (Line/Mic)   4️⃣ Touch Strip 3 모드
      │  2️⃣ Cutoff 실제 범위 검증      4️⃣ Velocity Curve
      │  2️⃣ Scale/Chord/ModQuant LUT   4️⃣ MIDI Routing 4 Config
      │
  low │                                  5️⃣ Reset Out, Clock PPQ
      │                                  5️⃣ Standalone Audio MIDI Settings
      │                                  5️⃣ Tutorials/Sound Store
      │                                  5️⃣ FX Insert/Send 라우팅
      └──────────────────────────────────────────────→
        low           med            high     난이도
```

### 4.2 Phase 10 실행 일정 (제안)

#### Phase 10-1: Collage Protocol 완성 (가장 큰 가치)
**근거**: V ↔ HW 통신을 완전히 디코드하면 외부 도구에서 HW 직접 제어 가능. MNFX Editor 도구 확장과 직결.

- [ ] **10-1-1** USB Bulk 패킷 캡처
  - **환경 제약**: USBPcap은 Windows 전용. 현재 Linux 환경에서는 `usbmon` + Wireshark Linux 빌드 또는 `tshark -i usbmonN` 사용
  - 대안: MiniFreak V가 설치된 Windows/macOS 머신에서 캡처 후 pcap 파일 전달
  - 캡처 시나리오: V Link 클릭 / Backup 클릭 / V에서 노브 조작 / Send to MiniFreak
- [ ] **10-1-2** Phase 5 Collage opcode 풀에서 명령 코드 매핑
  - 4 service domain (Data/Resource/System/Security) 각각의 opcode → action 매핑
  - Phase 5에서 `libusb` + Vendor Interface #0 Bulk EP 사용 확인. opcode 추출은 펌웨어 CM4 바이너리의 Collage handler에서 가능
- [ ] **10-1-3** `tools/collage_client.py` 도구 작성
  - V 없이 HW와 직접 통신, 프리셋 sync, FW update
  - Linux에서 `pyusb` 사용 (VID:0x1C75, PID:0x0602, Interface #0)
- [ ] 산출물: `PHASE10_COLLAGE_PROTOCOL.md`

#### Phase 10-2: V Macro 3/4 → HW 동작 분석
**근거**: V Macro 1/2 = HW Macro 1/2 미러. Macro 3 (Brightness) / Macro 4 (Timbre)는 V 전용이지만, HW에 데이터를 전송할 때 어떤 파라미터로 매핑되는지가 흥미로운 포인트.

- [ ] **10-2-1** V 플러그인의 .mnfx 프리셋 export (Macro 3/4 포함)
  - 기존 `tools/mnfx_editor.py`로 .mnfx 읽기 → Macro 3/4 필드 검색
- [ ] **10-2-2** HW로 Send to MiniFreak 했을 때 HW 메모리 상태 검증
  - 가설 A: Macro 3/4가 mod matrix slot으로 변환되어 저장
  - 가설 B: V 전용으로 .mnfx에 저장되지만 HW에서는 무시
  - 가설 C: 펌웨어에 hidden Macro slot 3/4 존재 (eEditParams에 deprecated 항목 있음 — 해당 가능성)
- [ ] **10-2-3** 펌웨어 `eEditParams` 재분석: `[UnisonOn DEPRECATED]`처럼 사용 중단된 슬롯 외에 Macro 3/4 후보 식별
- [ ] 산출물: `PHASE10_MACRO_HW_V_MAPPING.md`

#### Phase 10-3: CC#86~186 정확한 매핑 (Phase 8 이월)
**근거**: 펌웨어 내부 161 CC ↔ 매뉴얼 41 CC 차이의 정체 확정. 가장 큰 미해결 항목.

- [ ] **10-3-1** `FUN_08166810` 분기 테이블 정확한 추출 (현재 `phase8_cc_param_lookup.json`은 부분 추출)
- [ ] **10-3-2** 각 CC case의 `vtable[3](obj, eSynthParams_index)` 호출 시 param index 추출
  - indirect dispatch 한계: lookup table 기반은 디컴파일 직접 추출 불가
  - 대안 1: V 매뉴얼 §6.1.1.5 MIDI Learn 기능으로 V 측 CC → 파라미터 매핑 추출 후 펌웨어 case와 대조
  - 대안 2: Phase 9에서 발견한 `FUN_08184cd8` (Modulation Depth Calculator)의 vtable dispatch 활용 — param_2=9/5/0xd/0x1d로 4개 param 추출 가능
- [ ] **10-3-3** NRPN handler와 교차 검증
  - Phase 9 §9-8에서 NRPN 0xAE~0xB1 (Mod depth)와 0x9E~0xAD (Param route, 16ch) 발견
  - 이것이 CC#86~186과 어떻게 대응되는지 매핑
- [ ] 산출물: `PHASE10_CC_FULL_MAPPING.md` (161 CC × 145 eSynthParams 매트릭스)

#### Phase 10-4: 미완료 High 항목 보완 (Phase 8 이월 + §1.5 누락분)
- [ ] **10-4-1** LFO Triggering 8 모드 분기 함수 식별
  - `LFO1 Retrig` enum (Free/Poly Kbd/Mono Kbd/Legato Kb/One/LFO/CycEnv/Seq Start) 의 8 case 분기
- [ ] **10-4-2** Cycling Envelope Mode (Env/Run/Loop) + Stage Order (RHF/RFH/HRF) 분기
  - §3.2에서 논의한 ADSD vs RHF 모드 전환 코드
- [ ] **10-4-3** Audio In Mode (Line/Mic) 게인 스테이지 분기
  - eSettingsParams 또는 eEditParams에 `Audio In Mode` 항목 검색
  - Line vs Mic 게인 차이 펌웨어 상수 추출
- [ ] **10-4-4** Cutoff 범위 검증 (HW 20Hz-20kHz vs V 30Hz-15kHz)
  - `CvCalib::getCalibCutValue`에서 DAC value → 주파수 매핑의 lo/hi 한계
- [ ] **10-4-5** Scale LUT + Chord interval 테이블 + Mod Quantize LUT (§1.5 누락분)
  - Scale 9종 × 12-bit mask, Chord 11 interval × semitone offset, ModQuant 10종 × pitch snap LUT
- [ ] **10-4-6** Sequencer 64-step buffer 레이아웃 (§1.5 누락분)
  - `FUN_08029390` (6 cases) state machine + step structure: Pitch[6] + Length + Velocity + flags
- [ ] **10-4-7** MIDI Routing 4 Configuration (§1.5 누락분)
  - Local On/Off × MIDI > Synth/ArpSeq의 4 case 분기 코드
- [ ] **10-4-8** Velocity Curve (Linear/Log/Expo) (§1.5 누락분)
  - UI Kbd MCU 또는 CM4의 velocity response LUT
- [ ] 산출물: `PHASE10_LFO_CYCENV_AUDIOIN.md`

#### Phase 10-5: V 전용 영역 분석 (낮은 우선순위, 도구화 가치)
- [ ] **10-5-1** `.mnfxmidi` MIDI Configuration 포맷 리버싱
  - V에서 export한 .mnfxmidi 파일을 16진수 분석
  - JSON / boost::serialization / 커스텀 바이너리 판별
- [ ] **10-5-2** V Sound Bank 포맷 (Factory vs User Bank)
  - Phase 5 .mnfx 분석을 Bank 단위로 확장
- [ ] **10-5-3** V Backup 포맷 (`YYYYMMDDHHMMSS` 시리얼라이즈)
- [ ] 산출물: `PHASE10_V_FILE_FORMATS.md`

#### Phase 10-6: 잔여 Low 우선순위
- [ ] **10-6-1** Reset Out 5ms 펄스 GPIO
- [ ] **10-6-2** Clock In/Out PPQ 분주기
- [ ] **10-6-3** Knob Catch 3 모드 (Jump/Hook/Scale) 분기 — 매뉴얼 §15.2.4
- [ ] **10-6-4** AT Curve (Linear/Log/Expo) + AT Start/End Sensitivity LUT
- [ ] **10-6-5** Touch Strip 3 모드 (UI Ribbon MCU)
- [ ] **10-6-6** FX Insert/Send 라우팅 (Delay/Reverb만 Insert↔Send 전환) — §1.5 누락분
- [ ] **10-6-7** Panel 버튼 동작 (모든 파라미터 물리 위치 강제 점프) — §1.5 누락분
- [ ] **10-6-8** Spice/Dice 랜덤 시퀀스 생성기 (5 영역 마스크 + 변형 로직) — §1.5 누락분

---

## 5. 두 매뉴얼이 일치하나 분석에 누락된 영역

본 Phase 10 검토에서 **두 매뉴얼 모두 명시했지만** 펌웨어 분석에서 누락된 항목:

### 5.1 Hardware Transposition (per-preset)

V 매뉴얼 §7.1.2: "Hardware Transposition: allows you to set the preset transposition to be recalled on the hardware unit."

→ V에서 설정한 transposition이 HW 프리셋에 저장됨. eEditParams 또는 별도 슬롯 추정.

**액션**: eSynthParams 또는 .mnfx 포맷에서 transposition 필드 검색. XML resource의 "Transposition" 문자열 검색.

### 5.2 Auto Play (시퀀서 ↔ DAW transport sync)

V 매뉴얼 §5.3.1: "Auto Play: makes the Sequencer respond to your DAW's transport controls"

→ V 전용. Plug-in host transport ↔ V Sequencer 동기화. 펌웨어 분석 무관.

### 5.3 Stereo to Mono

V 매뉴얼 §7.1.5 + HW 매뉴얼 §15.2.3 모두 명시: "changes the Left and right + headphones outputs to be Mono"

→ HW에서는 Utility 메뉴, V에서는 Side Panel. eSettingsParams 추정.

**액션**: `Stereo to Mono` 문자열 펌웨어 검색.

### 5.4 VCF Calibration (Calib Cutoff / Calib Analog)

HW 매뉴얼 §15.2.3 / V 매뉴얼 §7.1.5 (V는 더 상세):
> "Calibrate Analog (all analog elements), Resonance minimum and maximum, Calibrate Cutoff, VCA minimum and maximum, **VCA offset, and VCA offset reset**"

→ 분석에서 `CvCalib` 클래스 부분 식별 (Phase 4). **VCA offset / VCA offset reset**은 누락.

**액션**: CvCalib 클래스의 추가 메서드 식별. Phase 4에서 29회 호출 확인, VCA offset 관련 메서드 추가 탐색.

### 5.5 Knob Catch 모드 디테일

V 매뉴얼 §7.1.6의 Knob Catch 설명이 HW 매뉴얼보다 상세:
> "Scale: MiniFreak calculates the difference between the physical and software knob settings, and as the physical knob is turned, it gradually scales the software knob value until the two match up."

→ 단순히 "Scale" 모드 존재만이 아닌 *알고리즘*까지 명시. 펌웨어 분석에 정확한 스케일링 코드 식별 필요.

### 5.6 FX Insert/Send 라우팅 (두 매뉴얼 일치)

두 매뉴얼 모두 명시: Delay와 Reverb만 Insert/Send 선택 가능. Send 모드 시 Dry/Wet → Send Level로 의미 변경.

→ Phase 8 갭 §2.6에서 언급되었으나 펌웨어 분석에서 누락. FX 슬롯 제한(Reverb/Delay/MultiComp=1개)은 Phase 8에서 확인.

### 5.7 Unison Mode 디테일 (두 매뉴얼 일치)

두 매뉴얼 모두 명시:
- Unison Count: 2~6
- Unison Spread: 1/1000 semitone ~ 1 octave
- Unison Mode: Mono/Poly/Para (Unison이 어떤 voicing 모드에서 활성되는지)
- Legato Mono: Mono/Uni 모드에서 retrigger 여부

→ Phase 9 §9-7에서 `case 8: 루프 uVar7=0..5 (6 voice unison init)` 확인. Unison Count/Spread/Mode의 펌웨어 상수 미식별.

---

## 6. 검증 도구 (이번 Phase 10에서 활용)

| 도구 | 용도 | 상태 | 비고 |
|------|------|------|------|
| Ghidra 12.0.4 + PyGhidra | 디컴파일 / 분기 추출 | ✅ | 기존 |
| **Wireshark (Linux + usbmon)** | V ↔ HW USB Bulk 캡처 | 🆕 | USBPcap(Windows) 대신 `tshark -i usbmonN` 사용. 또는 Windows 머신에서 캡처 후 전달 |
| **pyusb** | Linux에서 USB Bulk 직접 읽기/쓰기 | 🆕 | `tools/collage_client.py` 기반. VID:0x1C75 PID:0x0602 |
| **DAW (Live/Logic/Reaper)** | V 플러그인 + .mnfxmidi export | 🆕 | Phase 10-5 |
| **MIDI Monitor (Linux: midisnoop)** | CC/SysEx 트래픽 모니터 | 🆕 | MIDI-OX(Windows) 대신 |
| MiniFreak V XML resource | Phase 5 식별, 파라미터 풀 | ✅ | 기존 |
| Plaits source (MIT) | Osc 알고리즘 대조 | ✅ | 기존 |
| Mutable Instruments Blades | Multi/Surgeon/Comb 알고리즘 대조 | ✅ | 기존 |
| `tools/mnfx_editor.py` | .mnfx 프리셋 읽기/쓰기 | ✅ | 기존 — Phase 10-2/10-3에서 활용 |

---

## 7. 산출물 (Phase 10 완료 시)

| 문서 | 변경 유형 | 우선순위 |
|------|-----------|---------|
| `PHASE10_COLLAGE_PROTOCOL.md` | 신규 — V↔HW USB Bulk 명령 매핑 | 🔴 최우선 |
| `PHASE10_MACRO_HW_V_MAPPING.md` | 신규 — Macro 3/4 V 전용 vs HW 매핑 | 🔴 |
| `PHASE10_CC_FULL_MAPPING.md` | 신규 — 161 CC × 145 param 매트릭스 | 🔴 |
| `PHASE10_LFO_CYCENV_AUDIOIN.md` | 신규 — Phase 8 잔여 분기 + Scale/Chord/Seq/Velocity/MIDI Routing | 🟡 |
| `PHASE10_V_FILE_FORMATS.md` | 신규 — .mnfxmidi / Bank / Backup | 🟢 |
| `PHASE10_MANUAL_CONFLICTS.md` | 본 문서의 §3을 별도 정리 | 🟢 |
| `PHASE6_MIDI_CHART_v2.md` | 부분 갱신 — CC#86~186 결과 반영 | 🟡 |
| `PHASE8_FX_OSC_ENUMS.md` | 부분 갱신 — Audio In BitCrush/Noise 정정, Osc Type enum 대응표 | 🟢 |
| `PHASE8_COMPLETE_REPORT.md` | 부분 갱신 — Phase 9 신규 발견 반영 | 🟢 |
| `tools/collage_client.py` | 신규 — V 없이 HW 직접 제어 (Linux pyusb) | 🟢 |

---

## 8. 검증 체크리스트 (Phase 10 완료 기준)

- [ ] Collage protocol 4 service domain의 핵심 opcode 식별 (최소: Link, Backup, Send Preset, Init Preset)
- [ ] V Macro 3/4 (Brightness, Timbre) HW 저장 여부 확정
- [ ] CC#86~186 (101개) 의 90% 이상 파라미터 매핑
- [ ] Osc Type enum 21 entry ↔ Osc1 24종 ↔ Osc2 21종 대응표 완성
- [ ] LFO Triggering 8 모드 분기 함수 식별
- [ ] Cycling Envelope Env/Run/Loop 분기 + Stage Order 분기 식별
- [ ] Audio In Line/Mic 게인 분기 식별
- [ ] Cutoff 실제 동작 범위 (DAC LUT 검증)
- [ ] Scale 9종 LUT + Chord 11 interval + ModQuant 10종 LUT
- [ ] Sequencer 64-step buffer 레이아웃
- [ ] MIDI Routing 4 Configuration 분기
- [ ] Velocity Curve LUT
- [ ] `.mnfxmidi` 포맷 1차 디코드
- [ ] 매뉴얼 충돌 7항 (Cutoff 범위, Macro 개수, Cycling Env stage, OSC type 카운트, Audio In 파라미터, All Pass, **Osc Type enum 명칭**) 모두 명확화

---

## 9. Hallucination 방지 원칙 (계속)

이전 Phase 8에서 사용자가 지적한 hallucination 위험성을 의식하여, Phase 10에서도 다음을 엄수:

- 모든 분석 항목에 **추정** vs **확인된 사실** 명시
- 휴리스틱 분석 (vtable 카운트, audio_score, RTTI 매칭)은 **참고 지표**일 뿐
- 매뉴얼 충돌 시 V 매뉴얼은 V3/V4 시점 최신 정보일 가능성 높음 → 두 매뉴얼이 다르면 V를 우선 참조 (단 펌웨어 실제 동작과 추가 검증)
- USB 캡처 / .mnfxmidi 분석 등 **실제 동작 관찰**을 정적 분석보다 우선
- Collage opcode 매핑은 **확인된 명령 / 추정된 명령**을 명확히 구분 (관찰된 패킷이 없으면 "추정")
- Phase 9에서 발견한 **vtable 기반 간접 호출** 한계 인지: `FUN_08184cd8`의 param_2=9/5/0xd/0x1d만 직접 추출 가능, 나머지는 runtime 분석 필요

---

## 10. 후속 단계

Phase 10 완료 후:

- **Phase 11** (실제 패치 — HW 필요): Collage protocol을 활용한 안전한 HW 백업 후 패치 실험
- **Phase 12** (도구 통합): `tools/collage_client.py` + 기존 `mnfx_editor.py` + `minifreak_sysex.py` 통합
- **MNFX Editor 도구 확장**: V Backup 포맷 임포트, Bank 관리 기능
- **CC 매핑 매트릭스의 외부 컨트롤러 자동 매핑 도구**

---

*이 문서는 Phase 10 진행에 따라 각 항목의 완료 상태가 업데이트되며, 완료 후 `PHASE10_FINAL_VERIFICATION.md`로 정리되어 Phase 11의 입력이 됨.*
