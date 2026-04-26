# Phase 8: 시퀀서 / 아르페지에이터 / 모듈레이션 매트릭스 정리

> **2026-04-25** | fw4_0_1_2229 vs 매뉴얼 v4.0.1
> **출처**: Phase 8 펌웨어 리버싱 결과 + Arturia 공식 매뉴얼 교차 검증
> **관련 산출물**: `PHASE8_COMPLETE_REPORT.md`, `PHASE8_MANUAL_GAP_ANALYSIS-2.md`, `PHASE8_1_RESULTS.md`, `mf_enums.py`

---

## 목차

1. [아르페지에이터 (Arpeggiator)](#1-아르페지에이터-arpeggiator)
2. [스케일 (Scale)](#2-스케일-scale)
3. [코드 모드 (Chord Mode)](#3-코드-모드-chord-mode)
4. [모듈레이션 퀀타이즈 (Mod Quant)](#4-모듈레이션-퀀타이즈-mod-quant)
5. [LFO 트리거 모드 (LFO Trigger)](#5-lfo-트리거-모드-lfo-trigger)
6. [사이클링 엔벨로프 (CycEnv)](#6-사이클링-엔벨로프-cycenv)
7. [모듈레이션 매트릭스 (Mod Matrix)](#7-모듈레이션-매트릭스-mod-matrix)
8. [보이스 스틸 (Voice Steal)](#8-보이스-스틸-voice-steal)
9. [폴리 할당 (Poly Allocation)](#9-폴리-할당-poly-allocation)
10. [글로벌 설정 파라미터 (Settings)](#10-글로벌-설정-파라미터-settings)
11. [유틸리티 Enum](#11-유틸리티-enum)

---

## 1. 아르페지에이터 (Arpeggiator)

### 1.1 아르페지에이터 모드 (8종)

펌웨어 문자열 @ `0x081aed6c` 인근, 매뉴얼 §13 명시.

| 인덱스 | 모드 | 동작 설명 | 비고 |
|:------:|------|-----------|------|
| 0 | **Up** | 낮은 음 → 높은 음 순서 | 가장 기본 |
| 1 | **Down** | 높은 음 → 낮은 음 순서 | Up의 역순 |
| 2 | **UpDown** | Up 후 Down (ping-pong) | 최고/최저음 중복 없음 |
| 3 | **Random** | 균일(uniform) 무작위 선택 | 매 트리거마다 재추첨 |
| 4 | **Walk** | 확률적 인접 음 이동 | 25% 이전 / 25% 현재 / 50% 다음 |
| 5 | **Pattern** | Legato 시 N-step 시퀀서 자동 생성 | Root note 가중치 ×2 |
| 6 | **Order** | 누른 순서대로 재생 | FIFO 큐 |
| 7 | **Poly** | 모든 누른 음 동시 재생 | 화음 모드 |

**펌웨어 enum 확인**: `Arp Up, Arp Down, Arp UpDown, Arp Rand, Arp Walk, Arp Pattern, Arp Order, Arp Poly`

### 1.2 아르페지에이터 수식어 (4종)

펌웨어 문자열 @ `0x081aed6c` 인근, 매뉴얼 §13.3 명시.

| 수식어 | 동작 | 세부 확률 | ON/OFF |
|--------|------|-----------|--------|
| **Repeat** | 각 노트 2회씩 반복 | — | 토글 |
| **Ratchet** | 트리거 2배 (held 상태에서) | — | 토글 |
| **Rand Oct** | 옥타브 무작위 변형 | 75% 정상 / 15% +1oct / 7% -1oct / 3% +2oct | 토글 |
| **Mutate** | 음정 무작위 변형 (누적) | 75% 유지 / 5% +5th / 5% -4th / 5% +oct / 5% -oct / 3% 다음 노트와 swap / 2% 두 번째 다음과 swap | 토글 (누적) |

> **펌웨어 근거**: `Arp Repeat, Arp Ratchet, Arp Rand Oct, Arp Mutate` 문자열 존재.

### 1.3 옥타브 범위

| 파라미터 | 범위 | 기본값 |
|----------|------|--------|
| Octave Range | 1~4 | — |

### 1.4 펌웨어 핸들러

- `seq_arp_handler` @ `0x08189904` (CM4)
- Arp/Seq 공통 핸들러 내에서 모드별 분기 처리

---

## 2. 스케일 (Scale)

**위치**: Sound Edit > Scale Config

### 2.1 스케일 모드 (7종 + 2 유틸리티)

| 인덱스 | 스케일 | 음계 구성 | 비고 |
|:------:|--------|-----------|------|
| — | **Off** | 크로마틱 (전체 12음) | 스케일 적용 없음 |
| 0 | **Major** | W-W-H-W-W-W-H | C D E F G A B |
| 1 | **Minor** (Natural) | W-H-W-W-H-W-W | C D Eb F G Ab Bb |
| 2 | **Dorian** | W-H-W-W-W-H-W | C D Eb F G A Bb |
| 3 | **Mixolydian** | W-W-H-W-W-H-W | C D E F G A Bb |
| 4 | **Blues** | — | C Eb F F# G Bb |
| 5 | **Pentatonic** (Major) | — | C D E G A |
| — | **Global** | 글로벌 스케일 설정 사용 | 프리셋별 오버라이드 불가 |
| — | **User** | 사용자 정의 (12음 토글) | Root ~ B 사이 각 음 On/Off |

> **총 9 옵션**: 7 음악적 스케일 + Off + Global + User. 매뉴얼 명시.

### 2.2 Root Note

| 파라미터 | 범위 |
|----------|------|
| Root | C ~ B (12 semitone) |

### 2.3 User Scale

- Octave당 12개 노트 개별 토글
- RAM에 저장 (프리셋별 또는 글로벌)
- 펌웨어: 12-bit mask per octave

---

## 3. 코드 모드 (Chord Mode)

### 3.1 코드 인터벌 (12종)

펌웨어에서 chord interval 매핑으로 처리. 매뉴얼 §7 명시.

| 인덱스 | 코드 | 구성 (C 기준) | 인터벌 |
|:------:|------|---------------|--------|
| 0 | **Octave** | C C | 0 |
| 1 | **5th** | C G | 7 |
| 2 | **sus4** | C F | 5 |
| 3 | **m** (minor) | C Eb | 3 |
| 4 | **m7** (minor 7th) | C Eb Bb | 3, 10 |
| 5 | **m9** (minor 9th) | C Eb Bb D | 3, 10, 14 |
| 6 | **m11** (minor 11th) | C Eb Bb D F | 3, 10, 14, 17 |
| 7 | **69** (six-nine) | C E A D | 4, 9, 14 |
| 8 | **M9** (major 9th) | C E B D | 4, 11, 14 |
| 9 | **M7** (major 7th) | C E B | 4, 11 |
| 10 | **M** (major) | C E | 4 |
| 11 | **User** | 사용자 정의 | Hold Chord + 키 = 저장 |

> **총 12종**: 11 프리셋 인터벌 + 1 User 코드.

### 3.2 코드 모드 특성

- **Mono 모드**에서도 작동
- **Unison 모드**와 호환 (각 노트가 unison spread 적용)
- 코드 노트가 활성 스케일에 맞춰 퀀타이즈됨
- `Hold Chord` + 키 → 새 사용자 코드 저장

---

## 4. 모듈레이션 퀀타이즈 (Mod Quant)

**위치**: Sound Edit > Osc > Osc1 Mod Quant / Osc2 Mod Quant

### 4.1 Mod Quantize 모드 (10종)

Osc 1과 Osc 2 **별도 설정**. Pitch modulation에만 적용 (smooth → quantized step).

| 인덱스 | 모드 | 설명 | 반음 간격 |
|:------:|------|------|-----------|
| 0 | **Chromatic** | 12반음 전체 | 1 |
| 1 | **Octaves** | 옥타브 단위 | 12 |
| 2 | **Fifths** | 완전5도 단위 | 7 |
| 3 | **Minor** | 마이너 펜타토닉 | 1, 3, 5, 7, 8, 10 |
| 4 | **Major** | 메이저 펜타토닉 | 0, 2, 4, 7, 9 |
| 5 | **Phrygian Dominant** | 프리지안 도미넌트 | 0, 1, 4, 5, 7, 8, 10 |
| 6 | **Minor 9th** | 마이너 9th 스케일 | — |
| 7 | **Major 9th** | 메이저 9th 스케일 | — |
| 8 | **minor pentatonic** | 마이너 펜타토닉 | 0, 3, 5, 7, 10 |
| 9 | **Major pentatonic** | 메이저 펜타토닉 | 0, 2, 4, 7, 9 |

> **펌웨어 근거**: `Osc1 Mod Quant`, `Osc2 Mod Quant` @ eEditParams enum (0x081af904~)

---

## 5. LFO 트리거 모드 (LFO Trigger)

### 5.1 트리거 모드 (8종)

매뉴얼 §9.2 명시. LFO 1, LFO 2 각각 독립 설정.

| 인덱스 | 모드 | 설명 | 비고 |
|:------:|------|------|------|
| 0 | **Free** | 프리러닝, 키와 무관 | 가장 기본 |
| 1 | **Poly Kbd** | 각 음 press마다 리트리거 | 폴리포닉 |
| 2 | **Mono Kbd** | 첫 음 press에만 리트리거 | 모노포닉 |
| 3 | **Legato Kb** | 레가토 음에서 리트리거 | Mono/Uni 모드 |
| 4 | **One** | 단일 사이클 후 정지 | Saw/Sqr이 유니폴라로 변환 |
| 5 | **LFO** | 다른 LFO가 트리거 | LFO1→LFO2 또는 역방향 |
| 6 | **CycEnv** | Cycling Envelope가 트리거 | RHF/RHF 사이클 동기 |
| 7 | **Seq Start** | 시퀀서 시작에 트리거 | Arp/Seq Play 시 |

### 5.2 LFO 파라미터 구조

| 파라미터 | 설명 | 비고 |
|----------|------|------|
| LFO Wave | 파형 선택 (9종) | Sin/Tri/Saw/Sqr/SnH/SlewSNH/ExpSaw/ExpRamp/Shaper |
| LFO Rate | 주파수 (Hz 또는 tempo sync) | Sync En/Sync Filter 개별 설정 |
| LFO Sync En | 템포 싱크 ON/OFF | |
| LFO Sync Filter | 싱크 서브디비전 필터 | straight/triplet/dotted 선택 가능 |
| LFO Retrig | 트리거 모드 (상기 8종) | |
| LFO AM | 진폭 모듈레이션 깊이 | Mod Matrix Custom Assign 대상 |

### 5.3 LFO 파형 (9종)

`mf_enums.py` LFO_WAVES:

| 인덱스 | 파형 | 극성 | 설명 |
|:------:|------|:----:|------|
| 0 | **Sin** | Bi | 사인파 |
| 1 | **Tri** | Bi | 삼각파 |
| 2 | **Saw** | Bi | 톱니파 (falling) |
| 3 | **Sqr** | Bi | 구형파 |
| 4 | **SnH** | Bi | 샘플 앤 홀드 |
| 5 | **SlewSNH** | Bi | 슬루 제한 S&H |
| 6 | **ExpSaw** | Uni | 지수 톱니파 |
| 7 | **ExpRamp** | Uni | 지수 램프 |
| 8 | **Shaper** | 특수 | 사용자 그리기 (16 step) |

### 5.4 Vibrato (제3 LFO)

| 항목 | 설명 |
|------|------|
| 파형 | Free-running 삼각파 (고정) |
| Rate | Sound Edit > Pitch > Vib Rate |
| Depth | Sound Edit > Pitch > Vibrato Depth |
| 제어 | Touch Strip 직접 제어 (Shift-touch) |
| 펌웨어 파라미터 | `Vib Rate`, `Vib AM` @ Mod Matrix Custom Assign |

---

## 6. 사이클링 엔벨로프 (CycEnv)

### 6.1 CycEnv 모드 (3종 + 1 예약)

`mf_enums.py` CYCENV_MODES — 매뉴얼은 3종(Env/Run/Loop) 명시, 펌웨어는 4종 enum 확인.

| 인덱스 | 모드 | 설명 | 트리거 |
|:------:|------|------|--------|
| 0 | **Env** | Rise=Attack, Fall=Decay+Release, Hold=Sustain (ADSD 등가) | 모든 음 |
| 1 | **Run** | 모노포닉 원샷, MIDI Start만 리트리거 | MIDI Start |
| 2 | **Loop** | 폴리포닉 루프, 리트리거 소스 선택 가능 | 선택 가능 |
| 3 | **Loop2** | 대체 루프 모드 (예약/비활성?) | — |

### 6.2 Stage Order

| 옵션 | 설명 |
|------|------|
| **RHF** | Rise → Hold → Fall (기본) |
| **RFH** | Rise → Fall → Hold |
| **HRF** | Hold → Rise → Fall |

### 6.3 Retrig Source (Run/Loop 모드)

| 소스 | 설명 |
|------|------|
| Poly Kbd | 각 음 press마다 |
| Mono Kbd | 첫 음 press만 |
| Legato Kb | 레가토 음에서 |
| LFO 1 | LFO1 사이클에 동기 |
| LFO 2 | LFO2 사이클에 동기 |

### 6.4 CycEnv 파라미터 (MIDI CC)

| CC# | 파라미터 | 범위 |
|:---:|----------|------|
| 68 | Rise Shape | -50 ~ +50 |
| 76 | Rise | 0 ~ 127 |
| 77 | Fall | 0 ~ 127 |
| 78 | Hold | 0 ~ 127 |
| 69 | Fall Shape | -50 ~ +50 |

### 6.5 Tempo Sync

- 옵션 ON/OFF
- Sync 시 Rise/Fall/Hold가 템포에 스냅

---

## 7. 모듈레이션 매트릭스 (Mod Matrix)

### 7.1 매트릭스 구조 (7×13)

매뉴얼 §8.5 명시. 펌웨어 교차 검증 완료.

```
                    Col 1   Col 2   Col 3   Col 4  |  Col 5~7  Col 8~10  Col 11~13
Row 1: CycEnv       [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 2: LFO 1        [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 3: LFO 2        [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 4: Velo/AT      [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 5: Wheel        [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 6: Keyboard     [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 7: Mod Seq      [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
                     ──────── 하드와이어드 ────────  |  ─────── Assignable (3 page × 3) ───────
```

**최대 91개 라우팅 동시 가능** (7 row × 13 column)

### 7.2 Mod Matrix 소스 (7 Row + 하위 소스 = 12개)

#### 펌웨어 enum (9개, @ `0x081b1bcc`)

| # | 펌웨어 소스 | 매뉴얼 Row | 비고 |
|:-:|------------|:----------:|------|
| 0 | **Keyboard** | Row 6 | Note / Glide |
| 1 | **LFO** | Row 2~3 | LFO1 + LFO2 |
| 2 | **Cycling Env** | Row 1 | RHF envelope |
| 3 | **Env / Voice** | Row 4 (부분) | ADSR + voice params |
| 4 | **Voice** | — | Voice-specific |
| 5 | **Envelope** | — | ADSR |
| 6 | **FX** | — | Effects params |
| 7 | **Sample Select** | — | V3 추가 |
| 8 | **Wavetable Select** | — | V3 추가 |

#### 매뉴얼 Row 소스 (7개) + 하위 모드 (5개) = 12개

| Row | 매뉴얼 소스 | 하위 옵션 | Matrix Src 설정 |
|:---:|------------|-----------|-----------------|
| 1 | **Cycling Envelope** | — | 항상 활성 |
| 2 | **LFO 1** | — | Wave/Rate/Retrig 개별 |
| 3 | **LFO 2** | — | Wave/Rate/Retrig 개별 |
| 4 | **Velocity / Aftertouch** | Velocity / AT / Both | Sound Edit > Keyboard > Matrix Src VeloAT |
| 5 | **Wheel** | Mod Wheel / Touch Strip | 터치스트립 모드에 따라 |
| 6 | **Keyboard** | Linear / S Curve / Random / Voices | Sound Edit > Keyboard > Kbd Src |
| 7 | **Mod Seq** | 4 lane | 시퀀서 modulation lane |

#### 펌웨어 Kbd Src 모드 (4종, @ `0x081b0e10`)

| 인덱스 | 모드 | 설명 |
|:------:|------|------|
| 0 | **m9** | Minor 9th 베이스 |
| 1 | **m11** | Minor 11th 베이스 |
| 2 | **69** | Six-nine 베이스 |
| 3 | **M9** | Major 9th 베이스 |
| 4 | **M7** | Major 7th 베이스 |
| 5 | **S Curve** | S-커브 보간 |
| 6 | **Random** | 무작위 |
| 7 | **Voices** | 보이스 수 기반 |
| 8 | **Poly Kbd** | 폴리포닉 키보드 |

### 7.3 하드와이어드 Destination (4 Column)

| Column | Destination | 설명 |
|:------:|------------|------|
| Col 1 | **Osc 1+2 Pitch** | CycEnv 기본 연결 |
| Col 2 | **Osc 1+2 Shape** | — |
| Col 3 | **VCF Cutoff** | — |
| Col 4 | **VCA** | — |

### 7.4 Assignable Destination (9 Column = 3 Page × 3)

| Page | Column | 이름 |
|:----:|:------:|------|
| 1 | 5, 6, 7 | Assign 1, 2, 3 |
| 2 | 8, 9, 10 | Assign 4, 5, 6 |
| 3 | 11, 12, 13 | Assign 7, 8, 9 |

#### Assignable Destination 풀 (매뉴얼 §8.5.5)

```
Glide / Pitch 1 / Pitch 2
Osc 1 Type / Wave / Timbre / Shape / Volume
Osc 2 Type / Wave / Timbre / Shape / Volume
Filter Cutoff / Resonance / Env Amt
VCA
FX 1 Time / Intensity / Amount
FX 2 Time / Intensity / Amount
FX 3 Time / Intensity / Amount
Envelope A / D / S / R
CycEnv Rise / Fall / Sustain
LFO Rate / Wave / Amp
Macro 1 / 2
Matrix Mod Amount
```

### 7.5 Custom Assign Destination (물리 컨트롤 없음)

펌웨어 enum @ `0x081aea94`, 매뉴얼 §8.5.4 명시.

| Destination | 설명 | 비고 |
|------------|------|------|
| **Vib Rate** | Vibrato Rate | 제3 LFO |
| **Vib AM** | Vibrato AM Depth | 제3 LFO |
| **VCA** | VCA Level | 사이드체인 가능 |
| **LFO1 AM** | LFO1 진폭 모듈레이션 | 사이드체인 |
| **LFO2 AM** | LFO2 진폭 모듈레이션 | 사이드체인 |
| **CycEnv AM** | CycEnv 진폭 모듈레이션 | 사이드체인 |
| **Uni Spread** | 유니즌 스프레드 | — |
| **-Empty-** | 미할당 | — |

### 7.6 매트릭스 데이터 구조 (추정)

```
Mx_Dots[91]    — Boolean enable per routing (1 bit each)
Mx_Assign[91]  — Assignable 슬롯의 destination ID
Mx_Col[91]     — Amount/depth (-100 ~ +100, bipolar)
```

### 7.7 Macro 시스템

| 항목 | 설명 |
|------|------|
| Macro 1 | CC#117, dest/amount 개별 설정 |
| Macro 2 | CC#118, dest/amount 개별 설정 |
| `Macro1 dest` / `Macro2 dest` | 각 매크로의 대상 파라미터 |
| `Macro1 amount` / `Macro2 amount` | 각 매크로의 모듈레이션 양 |

### 7.8 메타-모듈레이션 (Modulating Modulation)

- Assign 슬롯에 `LFO1 AM` / `CycEnv AM` 등 "AM" destination 할당 가능
- → **다른 라우팅의 amount를 모듈레이션** (사이드체인)
- Macro Assign에서 `Matrix Mod Amount` 가능

---

## 8. 보이스 스틸 (Voice Steal)

### 8.1 Voice Steal 모드 (3종)

`mf_enums.py` POLY_STEAL_MODES, 펌웨어 `Poly Steal Mode` @ `0x081af974`

| 인덱스 | 모드 | 설명 | 비고 |
|:------:|------|------|------|
| 0 | **None** | 도난 없음 | 6음 초과 시 무시 |
| 1 | **Oldest** | 가장 오래된 보이스 도난 | 시간 기반 |
| 2 | **Lowest Vel** | 가장 낮은 벨로시티 보이스 도난 | 벨로시티 기반 |

> **참고**: 펌웨어 문자열 @ `0x081af974`에는 `None → Cycle → Reassign → Velocity → Aftertouch → Velo + AT` 6개 모드도 존재.
> 매뉴얼은 `None / Once / Cycle / Reassign` 4종을 명시 — 펌웨어 버전 간 차이 가능성.
> `mf_enums.py`의 3종(Cycle/Reassign/Reset)은 **Poly Allocation** 모드와 혼동 가능성 있음.

### 8.2 Voice Architecture 요약

| 항목 | 값 | 근거 |
|------|-----|------|
| Voice Struct 크기 | 0x118 (280바이트) | Phase 10 CM4 분석 |
| 슬롯 수 | **6** (Poly/Mono/Uni), **12** (Para) | VoiceAllocator lookup |
| Para 모드 | 6 voice × 2 osc = 12-note poly | Voice pair 구조 |

---

## 9. 폴리 할당 (Poly Allocation)

### 9.1 Poly Allocation 모드 (3종)

`mf_enums.py` POLY_ALLOC_MODES

| 인덱스 | 모드 | 설명 | 비고 |
|:------:|------|------|------|
| 0 | **Cycle** | 라운드 로빈 | 순차적 보이스 할당 |
| 1 | **Reassign** | 유지 | 기존 보이스 유지 |
| 2 | **Reset** | 리셋 | 새 음마다 리셋 |

### 9.2 Voice Mode (5종)

`mf_enums.py` VOICE_MODES

| 인덱스 | 모드 | 설명 |
|:------:|------|------|
| 0 | **Poly** | 폴리포닉 (노트당 1 voice) |
| 2 | **Mono** | 모노포닉 (glide + legato) |
| 3 | **Unison** | 유니즌 (2~6 voice) |
| 4 | **Para** | 파라포닉 (12 voice, 6 pair) |
| 5 | **Dual** | 듀얼 모드 |

### 9.3 관련 보이스 파라미터

| 파라미터 | 옵션 | 설명 |
|----------|------|------|
| Unison Mode | Mono / Poly / Para | 유니즌 음성 모드 |
| Unison Count | 2 ~ 6 | 동시 트리거 보이스 수 |
| Unison Spread | 1/1000 st ~ 1 octave | 디튠 범위 |
| Legato Mono | Off / On | Mono/Uni에서 리트리거 여부 |
| Retrig Mode | Env Reset / Env Continue | 새 음에서 엔벨로프 재시작 여부 |

---

## 10. 글로벌 설정 파라미터 (Settings)

**위치**: Utility 메뉴 (Shift + Category 버튼)
**펌웨어**: `Settings::set(eSettingsParams, value)` @ `0x081ad485`

### 10.1 Preset Operation (프리셋 동작)

| # | 파라미터 | 옵션 | 설명 |
|:-:|----------|------|------|
| 1 | **Panel Mode** | Favorite Panel / Original Panel | 패널 모드 선택 |
| 2 | **Preset Protect** | On / Off | 프리셋 보호 |
| 3 | **Auto Save** | On / Off | 자동 저장 |

### 10.2 Sync (동기화)

| # | 파라미터 | 옵션 | 설명 |
|:-:|----------|------|------|
| 4 | **Clock In PPQ** | 2 / 4 / 24 / 48 | 클럭 입력 해상도 |
| 5 | **Clock Out PPQ** | 2 / 4 / 24 / 48 / 1PPQ / 1PP2Q / 1PP4Q | 클럭 출력 해상도 |
| 6 | **Tempo** | 20 ~ 300 BPM | 내부 템포 |

### 10.3 MIDI

| # | 파라미터 | 옵션 | 설명 |
|:-:|----------|------|------|
| 7 | **MIDI Channel** | 1 ~ 16 | 수신 채널 |
| 8 | **Local Control** | On / Off | 로컬 키보드 활성화 |
| 9 | **MIDI Routing** | 4 configuration | Local × MIDI > Synth/ArpSeq 조합 |
| 10 | **MIDI Clock** | On / Off | MIDI 클럭 송수신 |
| 11 | **Program Change Rx** | On / Off | 프로그램 체인지 수신 |
| 12 | **SysEx Rx** | On / Off | SysEx 수신 |

### 10.4 Audio

| # | 파라미터 | 옵션 | 설명 |
|:-:|----------|------|------|
| 13 | **Audio In Mode** | Line / Microphone | 입력 모드 (Mic = Dynamic 전용) |
| 14 | **Audio In Gain** | -9 dB ~ +24 dB | 입력 게인 |

### 10.5 Keyboard

| # | 파라미터 | 옵션 | 설명 |
|:-:|----------|------|------|
| 15 | **Bend Range** | ±1 ~ ±12 반음 | 피치 벤드 범위 |
| 16 | **Knob Catch Mode** | Jump / Hook / Scale | 노브 캐치 모드 |
| 17 | **Velocity Curve** | Linear / Log / Expo | 벨로시티 커브 |
| 18 | **AT Curve** | Linear / Log / Expo | 애프터터치 커브 |
| 19 | **AT Sensitivity Start** | Low / Mid / High | AT 시작 감도 |
| 20 | **AT Sensitivity End** | Low / Mid / High | AT 종료 감도 |
| 21 | **Velo > VCA** | 0 ~ 127 | 벨로시티 → VCA 깊이 |
| 22 | **Velo > VCF** | 0 ~ 127 | 벨로시티 → VCF 깊이 |
| 23 | **Velo > Env** | 0 ~ 127 | 벨로시티 → Env 깊이 |
| 24 | **Velo > Time** | 0 ~ 127 | 벨로시티 → Env 타임 깊이 |

### 10.6 Display

| # | 파라미터 | 옵션 | 설명 |
|:-:|----------|------|------|
| 25 | **Brightness** | 0 ~ 100% | OLED 밝기 |
| 26 | **Contrast** | 0 ~ 100% | OLED 대비 |

### 10.7 Calibration

| # | 파라미터 | 옵션 | 설명 |
|:-:|----------|------|------|
| 27 | **VCF Calib** | — | 필터 캘리브레이션 |
| 28 | **VCA Calib** | — | VCA 캘리브레이션 |
| 29 | **Pitch Calib** | — | 피치 캘리브레이션 |

### 10.8 System

| # | 파라미터 | 옵션 | 설명 |
|:-:|----------|------|------|
| 30 | **Firmware Version** | 읽기 전용 | 현재 펌웨어 버전 |

> **총 30개** 글로벌 설정 파라미터 (Utility 메뉴).

---

## 11. 유틸리티 Enum

### 11.1 Knob Catch Mode (3종)

**위치**: Utility > Keyboard > Knob Catch Mode
**적용 대상**: 아날로그 노브 (Glide, Cutoff, Resonance, Env, Rise/Fall, Hold/Sustain, Attack, Decay, Sustain, Release)
**디지털 인코더**: 자동 처리 (캐치 모드 불필요)

| 모드 | 설명 | 동작 |
|------|------|------|
| **Jump** | 즉시 점프 | 노브 만지는 순간 노브 물리 위치 값으로 점프 |
| **Hook** | 통과 후 캐치 | 노브가 저장값을 통과해야 값 따라감 |
| **Scale** | 비례 보정 | 저장값 → 물리 위치까지 부드러운 비례 보정 |

> **Panel 버튼** (Save 옆): 모든 파라미터 값을 현재 물리 위치로 강제 점프 (영구 적용).

### 11.2 MIDI Routing (4 Configuration)

**위치**: Utility > MIDI > MIDI Routing

| 구성 | Local | MIDI → Synth | MIDI → Arp/Seq |
|:----:|:-----:|:------------:|:--------------:|
| 1 | On | On | On |
| 2 | On | On | Off |
| 3 | Off | On | On |
| 4 | Off | On | Off |

> **Local Control**과 **MIDI Routing**은 별개 파라미터. Local Off + MIDI Routing On = 키보드 무음이나 외부 MIDI로는 소리 남.

### 11.3 Clock PPQ (7종)

**위치**: Utility > Sync

#### Clock In PPQ (4종)

| 옵션 | 설명 |
|------|------|
| **2 PPQ** | 1拍당 2 펄스 |
| **4 PPQ** | 1拍당 4 펄스 (기본) |
| **24 PPQ** | 1拍당 24 펄스 (DIN Sync 호환) |
| **48 PPQ** | 1拍당 48 펄스 (고해상도) |

#### Clock Out PPQ (7종)

| 옵션 | 설명 |
|------|------|
| **2 PPQ** | 1拍당 2 펄스 |
| **4 PPQ** | 1拍당 4 펄스 |
| **24 PPQ** | 1拍당 24 펄스 |
| **48 PPQ** | 1拍당 48 펄스 |
| **1PPQ** | 1 펄스 per quarter note |
| **1PP2Q** | 1 펄스 per half note |
| **1PP4Q** | 1 펄스 per whole note |

### 11.4 Curves (3종 × 2 카테고리)

#### Velocity Curve

| 커브 | 특성 |
|------|------|
| **Linear** | 1:1 선형 매핑 |
| **Log** | 저벨로시티에서 더 큰 변화 (민감) |
| **Expo** | 고벨로시티에서 더 큰 변화 (둔감) |

#### Aftertouch Curve

| 커브 | 특성 |
|------|------|
| **Linear** | 1:1 선형 매핑 |
| **Log** | 저압에서 더 큰 변화 (민감) |
| **Expo** | 고압에서 더 큰 변화 (둔감) |

#### Aftertouch Sensitivity

| 파라미터 | 옵션 | 설명 |
|----------|------|------|
| **Start** | Low / Mid / High | AT 시작 임계값 |
| **End** | Low / Mid / High | AT 종료 감도 |

---

## 부록 A: 펌웨어 RTTI 서명

```
Preset::set(eSynthParams, value)    @ 0x081ac735
Preset::set(eCtrlParams, value)     @ 0x081ac7e9   ← Mod Matrix 관련
Preset::set(eFXParams, value)       @ 0x081ac791
Preset::set(eSeqParams, value)      @ 0x081ac845   ← Seq/Arp 관련
Preset::set(eSeqStepParams, value)  @ 0x081ac8d1
Preset::set(eSeqAutomParams, value) @ 0x081ac975   ← Mod Seq 관련
Preset::set(eShaperParams, value)   @ 0x081ac9d9   ← LFO Shaper 관련
MNF_Edit::set(eEditParams, value)   @ 0x081aa101   ← Voice/LFO/Mod Quant 관련
Settings::set(eSettingsParams, value) @ 0x081ad485  ← 글로벌 설정
```

## 부록 B: eEditParams enum (관련 항목 추출)

@ `0x081af904` ~ `0x081afa7c`:

```
LFO1 Wave → LFO1 Sync En → LFO1 Sync Filter → LFO1 Retrig →
LFO2 Wave → LFO2 Sync En → LFO2 Sync Filter → LFO2 Retrig →
Macro1 dest → Macro2 dest → Macro1 amount → Macro2 amount →
Retrig Mode → Legato Mono → Unison Count → Poly Allocation →
Poly Steal Mode → Vibrato Depth → Osc1 Mod Quant → Osc2 Mod Quant →
Release Curve → Osc Mix Non-Lin → Glide Sync →
Pitch 1 → Pitch 2 → Velo > VCF → Kbd Src →
Unison Mode → Osc Free Run → Mx Cursor → Mx Page → Mx Mode →
Osc Sel → Fx Sel → Lfo Sel
```

## 부록 C: 펌웨어 주소 레퍼런스

| 항목 | 주소 | 비고 |
|------|------|------|
| seq_arp_handler | `0x08189904` | Arp/Seq 공통 |
| Mod Source enum | `0x081b1bcc` | 9개 소스 |
| Mod Dest enum | `0x081aea94` | Custom Assign 대상 |
| eEditParams | `0x081af904` ~ `0x081afa7c` | 에디트 파라미터 |
| Smooth Mod 1~4 | `0x081b1b8c` | Mod Seq 스무딩 |
| midi_cc_handler | `0x08166810` | 161 CC 처리 |
| CycEnv Mode enum | mf_enums.py | 4 모드 |
| Voice Mode enum | `0x081af4f4` ~ `0x081af528` | 5 모드 (Phase 11 보정: 7→5) |
| Poly Steal Mode | `0x081af974` | 펌웨어 문자열 |

---

*문서 버전: Phase 8 최종 | 작성일: 2026-04-25*
*펌웨어 버전: fw4_0_1_2229 (2025-06-18)*
*매뉴얼 버전: v4.0.1 (2025-07-04)*
