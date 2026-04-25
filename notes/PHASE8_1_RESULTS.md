# Phase 8-1: Critical & High Priority 검증 결과

> 2026-04-25 | 펌웨어 fw4_0_1_2229 vs 매뉴얼 v4.0.1

---

## 8-1a: MIDI CC 매핑 정정 ✅

### 확정 사실
- 펌웨어 `FUN_08166810`: **161개 CC case** 처리 (0~196 범위, 일부 gap)
- 매뉴얼 공식 41개 CC: **전부 펌웨어에 존재** 확인
- CC 처리 방식: **virtual function call** (`vtable[3](obj, eSynthParams_index)`) + `FUN_08164efc` (param setter)
- 각 CC는 고정된 `DAT_` 글로벌 → AXI SRAM 파라미터 포인터 → vtable 경유

### eSynthParams 인덱스 (확인된 것)
| CC# | vtable param idx | 매뉴얼 파라미터 |
|-----|-----------------|---------------|
| 5 | 3 | Glide |
| 14 | 13 | Osc1 Wave |
| 15 | 13 | Osc1 Timbre |
| 20 | 13 | Osc2 Timbre |
| 50 | 5 | — |
| 57 | 5 | — |
| 79 | 31 | — |
| 186 | 1 | — |

> 대부분의 CC는 indirect dispatch (lookup table 기반)로 처리되어 디컴파일에서 직접 param index 추출 불가.
> 매뉴얼 41개 CC는 정답으로 간주. 상세 매핑은 `PHASE6_MIDI_CHART_v2.md` 참조.

### 기존 PHASE6_MIDI_CHART.md 판정
**전면 폐기**. CC#→파라미터 매핑이 거의 전부 잘못됨.

---

## 8-1b: Voice Architecture ✅

### Voice Struct
| 항목 | 값 | 근거 |
|------|-----|------|
| Struct 크기 | **0x118 (280바이트)** | Phase 10 CM4 분석 |
| 슬롯 수 | **6** | VoiceAllocator lookup table |
| 버퍼 크기 | 6 × 0x118 = **0x678 (1,656바이트)** | 계산값 |
| Para 모드 | **6 voice × 2 osc = 12-note poly** | 12개 voice struct가 아님 |

### VoiceAllocator Lookup Tables
`VoiceAllocator` 문자열 @ 0x081ae1ec 바로 뒤:

**Table 1** (일반 모드): `01 FF02 FE03 FD04 FC05 FB00`
- count range: 1~5 (mono, duo, poly3, poly4, poly5)
- bitmask: `0xFF-count+1` 패턴 (voice stealing priority)

**Table 2** (유니즌 모드): `01 FF02 FE03 FD04 FC05 FB06 FA00`
- count range: 1~6 (mono~unison6)
- 추가: unison count 6 지원

### Voice Mode Enum
`Run → Loop → Unison → Uni (Poly) → Uni (Para) → Mono → Para`
@ 0x081af4f4~0x081af528

> 이 enum은 **Unison Mode** (매뉴얼: Vibrato/Unison/Duo)로 추정.
> 실제 voice allocation mode (Mono/Poly/Para)는 `Poly Allocation` (0x081af964) 문자열로 관리.

### Voice Steal Mode
@ 0x081af974: `None → Cycle → Reassign → Velocity → Aftertouch → Velo + AT`
→ 펌웨어에 6개 steal mode (매뉴얼: None/Once/Cycle/Reassign과 일치 여부 검증 필요)

### Voice-Related Edit Parameters
@ 0x081af904~0x081afa7c (eEditParams enum):
```
LFO1 Wave → LFO1 Sync En → LFO1 Sync Filter → LFO1 Retrig →
LFO2 Wave → LFO2 Sync En → LFO2 Sync Filter → LFO2 Retrig →
Macro1 dest → Macro2 dest → Macro1 amount → Macro2 amount →
Retrig Mode → Legato Mono → Unison Count → Poly Allocation →
Poly Steal Mode → Vibrato Depth → [UnisonOn DEPRECATED] →
Matrix Src VeloAT → Osc1 Mod Quant → Osc2 Mod Quant →
Release Curve → Osc Mix Non-Lin → Glide Sync →
Pitch 1 → Pitch 2 → Velo > VCF → Kbd Src →
Unison Mode → Osc Free Run → Mx Cursor → Mx Page → Mx Mode →
Osc Sel → Fx Sel → Lfo Sel
```

---

## 8-1c: Mod Matrix 구조 ✅

### Mod Sources (펌웨어 enum @ 0x081b1bcc)
| # | Source | 비고 |
|---|--------|------|
| 0 | Keyboard | Note/Glide |
| 1 | LFO | LFO1+LFO2 |
| 2 | Cycling Env | RHF envelope |
| 3 | Env / Voice | ADSR + voice params |
| 4 | Voice | Voice-specific |
| 5 | Envelope | ADSR |
| 6 | FX | Effects params |
| 7 | Sample Select | V3 추가 |
| 8 | Wavetable Select | V3 추가 |

> 매뉴얼 7소스와 대부분 일치. Sample Select / Wavetable Select는 V3에서 추가.

### Mod Destinations (펌웨어 enum @ 0x081aea94)
| # | Destination | 타입 |
|---|------------|------|
| — | Custom Assign | 사용자 지정 |
| — | -Empty- | 미할당 |
| — | Vib Rate | Vibrato Rate |
| — | Vib AM | Vibrato AM |
| — | VCA | VCA Level |
| — | LFO2 AM | LFO2 AM Depth |
| — | LFO1 AM | LFO1 AM Depth |
| — | CycEnv AM | Cycling Env AM |
| — | Uni Spread | Unison Spread |

### Assignable Slots
- **Smooth Mod 1~4** @ 0x081b1b8c: 4개 smoothing parameter
- 매뉴얼 "4 hardwired + 9 assignable (3 page × 3) = 13 destinations"
- 펌웨어는 **9개 hardwired destinations** (Vib Rate/AM, VCA, LFO1/2 AM, CycEnv AM, Uni Spread, Custom, Empty)
-Assignable slot 수: 검증 필요 (eCtrlParams enum 크기 분석 필요)

### Macro System
- **Macro 1** (CC#117) + **Macro 2** (CC#118) — 펌웨어에서 2개만 존재
- `Macro1 dest`, `Macro2 dest`: 각 매크로의 대상 파라미터
- `Macro1 amount`, `Macro2 amount`: 각 매크로의 mod 양

---

## 펌웨어 RTTI (Preset::set/get 서명)
모든 C++ 메서드 시그니처 확인:
```
Preset::set(eSynthParams, value)    @ 0x081ac735
Preset::set(eCtrlParams, value)     @ 0x081ac7e9
Preset::set(eFXParams, value)       @ 0x081ac791
Preset::set(eSeqParams, value)      @ 0x081ac845
Preset::set(eSeqStepParams, value)  @ 0x081ac8d1
Preset::set(eSeqAutomParams, value) @ 0x081ac975
Preset::set(eShaperParams, value)   @ 0x081ac9d9
MNF_Edit::set(eEditParams, value)   @ 0x081aa101
Settings::set(eSettingsParams, value) @ 0x081ad485
```

---

## NRPN Handler
- 주소: `FUN_0x081812B4`
- NRPN params: 1~6, 10~16, 20~21, 25~32, 39~41, 48~49, 54~56, 61~62 (33개)
- FX NRPN: param 0xd8 (216), sub-params 0~22
- 처리: vtable call 경유 (Preset::set 직접 호출 아님)
