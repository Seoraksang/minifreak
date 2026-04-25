# Phase 8: 펌웨어 vs 매뉴얼 대조 검증 완료 보고서

> **2026-04-25** | fw4_0_1_2229 vs 매뉴얼 v4.0.1
> **산출물**: `PHASE8_1_RESULTS.md`, `PHASE6_MIDI_CHART_v2.md`, `PHASE8_CC_VALIDATION.md`

---

## Executive Summary

| 카테고리 | 항목 수 | 상태 |
|----------|--------|------|
| **8-1a** CC 매핑 정정 | 41 CC | ✅ 전면 재작성 |
| **8-1b** Voice 구조 | 6슬롯 확정 | ✅ |
| **8-1c** Mod Matrix | 소스 9 / Dest 7 | ✅ |
| **8-2** 누락 기능 | 8개 영역 | ✅ 전부 펌웨어에 존재 |
| **8-3** 명칭 정정 | 3개 항목 | ✅ |

---

## 8-2: 누락 기능 검증 (전부 펌웨어에 존재)

### 그래뉼러 엔진 7종 ✅
펌웨어 Oscillator Type enum (0x081af474):
```
...Wavetable → Sample → Cloud Grains → Hit Grains → Frozen → Skan → Particle → Lick → Raster
```
7종 전부 존재. Osc type index 14~20.

### Sample 엔진 ✅
- Osc type #13 = "Sample"
- Mod Source enum에 "Sample Select" 포함
- 펌웨어에 Sample 관련 파라미터 존재

### Wavetable 엔진 ✅
- Osc type #12 = "Wavetable"  
- Mod Source enum에 "Wavetable Select" 포함
- "Wavetables" (복수형) 문자열도 존재

### Vibrato (제3의 LFO) ✅
- `Vibrato Depth` @ eEditParams
- `Vib Rate`, `Vib AM` @ Mod Destinations
- `Vibrato On`, `Vibrato Off` 문자열 존재
- **별도의 Vibrato LFO**가 펌웨어에 구현됨

### Snapshots 시스템 ✅
- `View Snapshots` @ UI 메뉴 (0x081b1b6c)
- 시간 기반 자동 스냅샷 기능

### Favorites Panel ✅
- `Favorites Panel` @ 0x081ae414
- 64슬롯 (매뉴얼 명시, 펌웨어에서 확인 불가 — UI 제한)

### Mod Sequencer ✅
- `Seq Mods` @ 0x081aed6c
- 4 lane modulation sequencer

### Arpeggiator 8모드 + 4수정자 ✅
**수정자 (4)**: `Arp Repeat, Arp Ratchet, Arp Rand Oct, Arp Mutate`
**모드 (8)**: `Arp Up, Arp Down, Arp UpDown, Arp Rand, Arp Walk, Arp Pattern, Arp Order, Arp Poly`

---

## 8-3: 명칭 정정

### 1. Envelope 명칭
| 기존 (오류) | 정정 | 펌웨어 근거 |
|------------|------|-----------|
| Env1 | **Envelope (ADSR)** | `Envelope` 문자열 3개, `Env1` 없음 |
| Env2 | **Cycling Env (RHF)** | `Cycling Env` + `CycEnv` 문자열, `Env2` 없음 |
| Env1 ADSR CC#38~41 | **CC#80~83** | 매뉴얼 확인 |

### 2. Filter 위치 정정
| 기존 (오류) | 정정 | 펌웨어 근거 |
|------------|------|-----------|
| Multi/Surgeon/Comb/Phaser = VCF 서브타입 | **Osc 2 Audio Processor의 디지털 필터** | Osc Type enum 내 포함 (type 5~9) |
| VCF = SEM-style LP/BP/HP | ✅ 확인 | `VCF` + `Cutoff` + `Resonance` 별도 존재 |
|| VCF 필터 타입 | **LP, BP, HP** (SEM-style 12dB/oct) | ✅ 확인 | `VCF` + `Cutoff` + `Resonance` 별도 존재 |
|| 디지털 필터 (Osc2 Processor) | **LP, BP, HP, Notch, LP1, HP1, Notch2** (7종) | enum @ 0x081af4d0 — Osc 2 Audio Processor 전용 |

### 3. Mod Matrix Destination 수
|| 기존 (오류) | 정정 | 펌웨어 근거 ||
||------------|------|-----------| 
|| "140 destinations" | **7 hardwired + assignable slots** | enum: Vib Rate/AM, VCA, LFO1/2 AM, CycEnv AM, Uni Spread |
|| "7×13" 구조 | **7 sources × 7 hardwired destinations** | Source enum 9개 (incl. V3), Dest enum 7개 |

### 4. VCF Filter Type 수 정정
|| 기존 (오류) | 정정 | 매뉴얼 근거 ||
||------------|------|-----------|
|| "LP, BP, HP, Notch, LP1, HP1, Notch2 (7종)" | **아날로그 VCF: LP, BP, HP (3종, 12dB/oct 고정)** | 매뉴얼 5장 |
|| 7종 enum | **디지털 Osc2 Processor enum (별도)** | Multi/Surgeon/Comb/Phaser/Destroy는 Osc 2 Audio Processor |

---

## Oscillator Type 전체 enum (21종)

```
 0: Noise
 1: Bass
 2: SawX
 3: Harm
 4: FM / RM
 5: Multi Filter     ← Osc 2 Audio Processor
 6: Surgeon Filter   ← Osc 2 Audio Processor
 7: Comb Filter      ← Osc 2 Audio Processor
 8: Phaser Filter    ← Osc 2 Audio Processor
 9: Destroy
10: Dummy
11: Audio In
12: Wavetable        ← V3
13: Sample           ← V3
14: Cloud Grains     ← V3 (그래뉼러)
15: Hit Grains       ← V3 (그래뉼러)
16: Frozen           ← V3 (그래뉼러)
17: Skan             ← V3 (그래뉼러)
18: Particle         ← V3 (그래뉼러)
19: Lick             ← V3 (그래뉼러)
20: Raster           ← V3 (그래뉼러)
```

---

## Voice Mode / Unison Mode enum

```
 0: Run      ← Arp/Seq mode?
 1: Loop     ← Arp/Seq mode?
 2: Unison
 3: Uni (Poly)
 4: Uni (Para)
 5: Mono
 6: Para
```

## Filter Type enum (아날로그 VCF + 디지털)

**아날로그 VCF**: LP, BP, HP (SEM-style 12dB/oct)
**디지털 (Osc Processor)**: LP, BP, HP, Notch, LP1, HP1, Notch2

## Arpeggiator

**Modifiers (4)**: Repeat, Ratchet, Rand Oct, Mutate
**Modes (8)**: Up, Down, UpDown, Rand, Walk, Pattern, Order, Poly

## 펌웨어 C++ 클래스 계층

```
Preset
  ├── set/get(eSynthParams)    ← 신디사이저 파라미터 (ADSR, Filter, Osc...)
  ├── set/get(eCtrlParams)     ← 컨트롤 파라미터 (Mod Matrix)
  ├── set/get(eFXParams)       ← FX 파라미터
  ├── set/get(eSeqParams)      ← 시퀀서 파라미터
  ├── set/get(eSeqStepParams)  ← 시퀀서 스텝
  ├── set/get(eSeqAutomParams) ← 시퀀서 오토메이션
  └── set/get(eShaperParams)   ← 쉐이퍼 파라미터

MNF_Edit
  └── set/get(eEditParams)     ← 에디트 파라미터 (Macro, Voice, Unison...)

Settings
  └── set/get(eSettingsParams) ← 글로벌 설정
```
