# Phase 8: FX / OSC Enum 정리 문서

> **대상 펌웨어**: `fw4_0_1_2229` (2025-06-18)
> **VST 기준**: MiniFreak V v2.9.0 / v4.0.1
> **작성일**: 2026-04-25
> **출처**: `mf_enums.py` (VST XML 크로스검증), `phase8_enum_tables.json`, `phase8_cc86_186_detail.json`, `PHASE8_COMPLETE_REPORT.md`, `PHASE7-3_FX_CORE_ANALYSIS.md`, `minifreak_v_manual_extraction.md`

---

## 목차

1. [FX 타입 (14종)](#1-fx-타입-14종)
2. [FX 서브타입 (63종)](#2-fx-서브타입)
3. [오실레이터 타입 (OSC1: 24종, OSC2: 21종)](#3-오실레이터-타입)
4. [OSC2 Audio Processor (4종)](#4-osc2-audio-processor-4종)
5. [Vocoder 서브타입 (4종)](#5-vocoder-서브타입-4종)
6. [그래뉼러 엔진 (7종) 및 파라미터 (8종)](#6-그래뉼러-엔진-7종-및-파라미터)

---

## 1. FX 타입 (14종)

FX 체인은 **3슬롯** (FX1, FX2, FX3)으로 구성. Reverb, Stereo Delay, Multi Comp는 **싱글턴** — 전체 슬롯에서 각각 최대 1개만 활성화 가능.

### 1-1. VST 확정 FX 타입 (13종, index 0–12)

| Index | FX 타입 | 펌웨어 주소¹ | 서브프로세서² | 싱글턴 | 비고 |
|-------|---------|-------------|-------------|--------|------|
| 0 | **Chorus** | `0x081AF308` | SP6 `FUN_0800bdd0` (via `FUN_0800a408`) | — | 모듈레이션 엔진 |
| 1 | **Phaser** | `0x081AF310` | SP6 `FUN_0800bdd0` (via `FUN_08009e88`) | — | 올패스 필터 |
| 2 | **Flanger** | `0x081AF318` | SP6 `FUN_0800bdd0` (via `FUN_0800a408`) | — | 모듈레이션 + 딜레이 |
| 3 | **Reverb** | `0x081AF320` | SP3 `FUN_0800c5d0` | ✅ | Schroeder/FBDN 리버브 |
| 4 | **Stereo Delay** | `0x081AF328` | SP1 `FUN_0800bba0` + SP2 `FUN_0800bc88` | ✅ | 5-tap multitap |
| 5 | **Distortion** | `0x081AF334` | SP6 `FUN_0800bdd0` (via `FUN_0800a134`) | — | 웨이브셰이퍼 |
| 6 | **Bit Crusher** | `0x081AF340` | — | — | 디시메이션 + 비트 리덕션 |
| 7 | **3 Bands EQ** | `0x081AF34C` | SP6 `FUN_0800bdd0` (via `FUN_08009b98`) | — | 3밴드 셸빙 EQ |
| 8 | **Peak EQ** | `0x081AF354` | — | — | 파라메트릭 피킹 EQ |
| 9 | **Multi Comp** | `0x081AF360` | SP0 `FUN_0800b4f4` | ✅ | 멀티밴드 컴프레서 |
| 10 | **Super Unison** | `0x081AF36C` | SP6 `FUN_0800bdd0` (via `FUN_080082f0`) | — | 다중 디튠 카피 |
| 11 | **Vocoder Self** | `0x081AF37C` | SP5 `FUN_0800c87c` (mode=1) | — | V4.0+ 내부 신호 기반 |
| 12 | **Vocoder Ext In** | — | SP4 `FUN_0800c6ac` (mode=2) | — | V4.0+ 외부 오디오 입력 기반 |

> **주소 ¹**: CM4 펌웨어 `minifreak_main_CM4`의 FX 타입 문자열 포인터 테이블. 포인터 간격은 8바이트 (ARM32 포인터).
> **서브프로세서 ²**: FX 코어 펌웨어 `minifreak_fx`의 7개 서브프로세서 매핑 (Phase 7-3 분석).

### 1-2. 펌웨어 추가 문자열 (2종)

| 문자열 | 펌웨어 주소 | 비고 |
|--------|------------|------|
| **Destroy** | `0x081AF458` | FX 타입 문자열 테이블에 존재하나, 실제로는 **Osc2 Audio Processor** (index 9). FX 슬롯에서는 사용되지 않음. |
| **Delay** | `0x081AE368` | "Stereo Delay"의 단축명. FX 파라미터 문자열 영역에 별도 존재. |

### 1-3. FX 슬롯 구조

```
FX Chain: FX1 → FX2 → FX3 (시리얼 체인)
├── 라우팅: Insert (시리얼) / Send (병렬, Delay/Reverb 전용)
├── 슬롯당 파라미터: Type, Param1–6, Mix, Routing (9개)
├── CC 매핑: FX1=CC86–94, FX2=CC95–103, FX3=CC104–112
└── 펌웨어 슬롯 크기: 584바이트 (0x248) × 3슬롯
```

### 1-4. FX 싱글턴 제약

| 싱글턴 타입 | Index | 제약 |
|------------|-------|------|
| **Reverb** | 3 | 3슬롯 중 최대 1개 |
| **Stereo Delay** | 4 | 3슬롯 중 최대 1개 |
| **Multi Comp** | 9 | 3슬롯 중 최대 1개 |

---

## 2. FX 서브타입

각 FX 타입 내 **Preset (서브타입)** 목록. VST XML `discrete_param_swapper`에서 추출.

### 2-1. Chorus (5종)

| # | 서브타입 | 설명 |
|---|---------|------|
| 0 | Default | 표준 코러스 |
| 1 | Lush | 풍부한 디테인 코러스 |
| 2 | Dark | 따뜻한 저역 강조 코러스 |
| 3 | Shaded | 섀도우 톤 코러스 |
| 4 | Single | 싱글 보이스 코러스 |

### 2-2. Phaser (6종)

| # | 서브타입 | 싱크 | 설명 |
|---|---------|------|------|
| 0 | Default | — | 표준 페이저 |
| 1 | Default Sync | ✅ | 템포 싱크 기본 페이저 |
| 2 | Space | — | 와이드 스페이스 페이저 |
| 3 | Space Sync | ✅ | 템포 싱크 스페이스 페이저 |
| 4 | SnH | — | S&H 랜덤 스텝 페이저 |
| 5 | SnH Sync | ✅ | 템포 싱크 S&H 페이저 |

### 2-3. Flanger (4종)

| # | 서브타입 | 싱크 | 설명 |
|---|---------|------|------|
| 0 | Default | — | 표준 플랜저 |
| 1 | Default Sync | ✅ | 템포 싱크 플랜저 |
| 2 | Silly | — | 엑스트림 피드백 플랜저 |
| 3 | Silly Sync | ✅ | 템포 싱크 엑스트림 플랜저 |

### 2-4. Reverb (6종)

| # | 서브타입 | 설명 |
|---|---------|------|
| 0 | Default | 표준 리버브 |
| 1 | Long | 롱 디케이 리버브 |
| 2 | Hall | 홀 리버브 |
| 3 | Echoes | 에코 리버브 |
| 4 | Room | 룸 리버브 |
| 5 | Dark Room | 다크 톤 룸 리버브 |

### 2-5. Stereo Delay (12종)

| # | 서브타입 | 싱크 | 설명 |
|---|---------|------|------|
| 0 | Digital | — | 디지털 딜레이 |
| 1 | Digital Sync | ✅ | 템포 싱크 디지털 |
| 2 | Stereo | — | 스테레오 딜레이 |
| 3 | Stereo Sync | ✅ | 템포 싱크 스테레오 |
| 4 | Ping-Pong | — | 핑퐁 딜레이 |
| 5 | Ping-Pong Sync | ✅ | 템포 싱크 핑퐁 |
| 6 | Mono | — | 모노 딜레이 |
| 7 | Mono Sync | ✅ | 템포 싱크 모노 |
| 8 | Filtered | — | 필터 딜레이 |
| 9 | Filtered Sync | ✅ | 템포 싱크 필터 |
| 10 | Filtered Ping-Pong | — | 필터 핑퐁 딜레이 |
| 11 | Filtered Ping-Pong Sync | ✅ | 템포 싱크 필터 핑퐁 |

### 2-6. Distortion (6종)

| # | 서브타입 | 설명 |
|---|---------|------|
| 0 | Classic | 클래식 오버드라이브 |
| 1 | Soft Clip | 소프트 클리핑 |
| 2 | Germanium | 저마늄 트랜지스터 왜곡 |
| 3 | Dual Fold | 듀얼 웨이브폴더 |
| 4 | Climb | 스테어스텝 왜곡 |
| 5 | Tape | 테이프 사츄레이션 |

### 2-7. Bit Crusher (0종)

서브타입 없음. 파라미터만 제어:
- **Decimate**: 디시메이션 양
- **BitDepth**: 비트 해상도 (높을수록 더 크러싱)
- **Dry/Wet**: 드라이/웻 믹스

### 2-8. 3 Bands EQ (3종)

| # | 서브타입 | 설명 |
|---|---------|------|
| 0 | Default | 기본 3밴드 EQ |
| 1 | Wide | 와이드 대역 EQ |
| 2 | Mid 1K | 1kHz 미드 강조 EQ |

### 2-9. Peak EQ (0종)

서브타입 없음. 파라미터만 제어:
- **Freq**: 중심 주파수
- **Gain**: 부스트/컷 양
- **Width**: Q (대역폭)

### 2-10. Multi Comp (5종)

| # | 서브타입 | 설명 |
|---|---------|------|
| 0 | OPP (OTT) | 상/하 멀티밴드 컴프레서 |
| 1 | Bass Ctrl | 베이스 대역 컨트롤 |
| 2 | High Ctrl | 하이 대역 컨트롤 |
| 3 | All Up | 전체 대역 부스트 |
| 4 | Tighter | 타이트 컴프레션 |

### 2-11. Super Unison (8종)

| # | 서브타입 | 설명 |
|---|---------|------|
| 0 | Classic | 클래식 유니즌 (최대 6카피) |
| 1 | Ravey | 레이브 스타일 와이드 유니즌 |
| 2 | Soli | 솔리 유니즌 |
| 3 | Slow | 슬로우 디튠 유니즌 |
| 4 | Slow Trig | 슬로우 트리거 유니즌 |
| 5 | Wide Trig | 와이드 트리거 유니즌 |
| 6 | Mono Trig | 모노 트리거 유니즌 |
| 7 | Wavy | 웨이비 모듈레이션 유니즌 |

### 2-12. Vocoder Self (4종)

Vocoder Self / Vocoder Ext In 공통 서브타입. 자세한 내용은 [§5 Vocoder 서브타입](#5-vocoder-서브타입-4종) 참조.

### 2-13. Vocoder Ext In (4종)

Vocoder Self와 동일한 4종 서브타입. 자세한 내용은 [§5 Vocoder 서브타입](#5-vocoder-서브타입-4종) 참조.

### 2-14. 서브타입 집계

| FX 타입 | 서브타입 수 | 비고 |
|---------|-----------|------|
| Chorus | 5 | |
| Phaser | 6 | 3 base + 3 sync |
| Flanger | 4 | 2 base + 2 sync |
| Reverb | 6 | |
| Stereo Delay | 12 | 6 base + 6 sync |
| Distortion | 6 | |
| Bit Crusher | 0 | 파라미터만 |
| 3 Bands EQ | 3 | |
| Peak EQ | 0 | 파라미터만 |
| Multi Comp | 5 | |
| Super Unison | 8 | |
| Vocoder Self | 4 | |
| Vocoder Ext In | 4 | |
| **합계** | **63** | |

---

## 3. 오실레이터 타입

### 3-1. OSC1 엔진 (24종, index 0–23)

> 소스: `minifreak_vst_params.xml` `Osc1_Type_V2.9.0` item_list. 512개 팩토리 `.mnfx` 프리셋 크로스검증 완료.

| Index | 엔진 명 | 출처 | 펌웨어 비고 |
|-------|--------|------|-----------|
| 0 | **Basic Waves** | 공통 | Morph: Square→Saw→Double Saw |
| 1 | **SuperWave** | 공통 | 다향 웨이브 슈퍼 |
| 2 | **Harmo** | 공통 | 하모닉 테이블 (최대 8차) |
| 3 | **KarplusStr** | 공통 | Karplus-Strong 물리 모델링 |
| 4 | **VAnalog** | 공통 | Mutable Instruments Plaits |
| 5 | **Waveshaper** | 공통 | Mutable Instruments Plaits |
| 6 | **Two Op. FM** | 공통 | 2-오퍼레이터 FM 합성 |
| 7 | **Formant** | 공통 | Mutable Instruments Plaits |
| 8 | **Speech** | 공통 | Mutable Instruments Plaits |
| 9 | **Modal** | 공통 | Mutable Instruments Plaits |
| 10 | **Noise** | 공통 | 파티클→화이트→메탈릭 노이즈 |
| 11 | **Bass** | 공통 | Noise Engineering Vert Iter Legio |
| 12 | **SawX** | 공통 | Noise Engineering Vert Iter Legio |
| 13 | **Harm** | 공통 | Noise Engineering Vert Iter Legio |
| 14 | **Audio In** | OSC1 전용 | 외부 오디오 입력 |
| 15 | **Wavetable** | OSC1 전용 | 웨이브테이블 스캐닝 |
| 16 | **Sample** | OSC1 전용 | V2.9+ 샘플 재생 |
| 17 | **Cloud Grains** | OSC1 전용 | V2.9+ 그래뉼러 (클라우드) |
| 18 | **Hit Grains** | OSC1 전용 | V2.9+ 그래뉼러 (히트) |
| 19 | **Frozen** | OSC1 전용 | V2.9+ 그래뉼러 (프로즌) |
| 20 | **Skan** | OSC1 전용 | V2.9+ 그래뉼러 (스캔) |
| 21 | **Particle** | OSC1 전용 | V2.9+ 그래뉼러 (파티클) |
| 22 | **Lick** | OSC1 전용 | V2.9+ 그래뉼러 (릭) |
| 23 | **Raster** | OSC1 전용 | V2.9+ 그래뉼러 (래스터) |

### 3-2. OSC2 엔진 (21종, index 0–20)

> 소스: `minifreak_vst_params.xml` `Osc2_Type_V2.9.0` item_list. index 21–29은 더미 슬롯 (향후 확장용).

| Index | 엔진 명 | 출처 | 펌웨어 비고 |
|-------|--------|------|-----------|
| 0 | **Basic Waves** | 공통 | |
| 1 | **SuperWave** | 공통 | |
| 2 | **Harmo** | 공통 | |
| 3 | **KarplusStr** | 공통 | |
| 4 | **VAnalog** | 공통 | |
| 5 | **Waveshaper** | 공통 | |
| 6 | **Two Op. FM** | 공통 | |
| 7 | **Formant** | 공통 | |
| 8 | **Chords** | OSC2 전용 | 코드 (Oct, 5th, m, m7, m9, M9 등) |
| 9 | **Speech** | 공통 | |
| 10 | **Modal** | 공통 | |
| 11 | **Noise** | 공통 | |
| 12 | **Bass** | 공통 | |
| 13 | **SawX** | 공통 | |
| 14 | **Harm** | 공통 | |
| 15 | **FM / RM** | OSC2 전용 | FM 링 모듈레이션 |
| 16 | **Multi Filter** | OSC2 전용 | Audio Processor |
| 17 | **Surgeon Filter** | OSC2 전용 | Audio Processor |
| 18 | **Comb Filter** | OSC2 전용 | Audio Processor |
| 19 | **Phaser Filter** | OSC2 전용 | Audio Processor |
| 20 | **Destroy** | OSC2 전용 | 웨이브폴더 + 디시메이트 |
| 21–29 | *(Dummy)* | — | 향후 확장용 플레이스홀더 |

### 3-3. 엔진 분류

```
OSC1 전용 (10종):  Audio In, Wavetable, Sample, Cloud Grains, Hit Grains,
                   Frozen, Skan, Particle, Lick, Raster
OSC2 전용 (7종):   Chords, FM/RM, Multi Filter, Surgeon Filter,
                   Comb Filter, Phaser Filter, Destroy
공통 (14종):        Basic Waves ~ Harm (index 0–13)
```

### 3-4. 펌웨어 Oscillator Type enum (0x081AF474)

CM4 펌웨어의 원시 enum 테이블. VST 순서와 다름:

| Index | 엔진 명 | 비고 |
|-------|--------|------|
| 0 | Noise | |
| 1 | Bass | |
| 2 | SawX | |
| 3 | Harm | |
| 4 | FM / RM | |
| 5 | Multi Filter | ← Osc2 Audio Processor |
| 6 | Surgeon Filter | ← Osc2 Audio Processor |
| 7 | Comb Filter | ← Osc2 Audio Processor |
| 8 | Phaser Filter | ← Osc2 Audio Processor |
| 9 | Destroy | |
| 10 | *(Dummy)* | |
| 11 | Audio In | |
| 12 | Wavetable | V3 |
| 13 | Sample | V3 |
| 14 | Cloud Grains | V3 그래뉼러 |
| 15 | Hit Grains | V3 그래뉼러 |
| 16 | Frozen | V3 그래뉼러 |
| 17 | Skan | V3 그래뉼러 |
| 18 | Particle | V3 그래뉼러 |
| 19 | Lick | V3 그래뉼러 |
| 20 | Raster | V3 그래뉼러 |

> 펌웨어 enum은 VST enum과 순서가 다름. VST enum은 사용자 표시 순서, 펌웨어 enum은 내부 처리 순서로 추정.

---

## 4. OSC2 Audio Processor (4종)

Osc2 전용 디지털 필터/프로세서. **VCF (아날로그 SEM 필터)**와 별개의 디지털 처리.

| Index | 프로세서 | 파라미터 (Wave) | 파라미터 (Timbre) | 파라미터 (Shape) | 설명 |
|-------|---------|----------------|-----------------|-----------------|------|
| 16 | **Multi Filter** | Cutoff | Resonance | Mode | LP6/HP6/LP12/HP12/BP12/N12/LP24/HP24/BP24/N24/LP36/HP36/BP36/N36 (14종) |
| 17 | **Surgeon Filter** | Cutoff | Spread | Mode | LP/BP/HP/Notch (Spread=LP/HP에서 비활성) |
| 18 | **Comb Filter** | Cutoff | Gain | Damping | 딜레이 기반 콤 필터 |
| 19 | **Phaser Filter** | Cutoff | Feedback | Poles | 2–12폴 올패스 체인 (1–6 노치) |

> **참고**: `Destroy` (index 20)은 Osc2 전용이지만 "Audio Processor" 카테고리에는 포함되지 않음. 웨이브폴더/디시메이터/비트크러셔 기반의 왜곡 프로세서.

### 4-1. Multi Filter Mode (14종)

| Mode | 타입 | 슬로프 |
|------|------|-------|
| LP6 | Low Pass | 6 dB/oct |
| HP6 | High Pass | 6 dB/oct |
| LP12 | Low Pass | 12 dB/oct |
| HP12 | High Pass | 12 dB/oct |
| BP12 | Band Pass | 12 dB/oct |
| N12 | Notch | 12 dB/oct |
| LP24 | Low Pass | 24 dB/oct |
| HP24 | High Pass | 24 dB/oct |
| BP24 | Band Pass | 24 dB/oct |
| N24 | Notch | 24 dB/oct |
| LP36 | Low Pass | 36 dB/oct |
| HP36 | High Pass | 36 dB/oct |
| BP36 | Band Pass | 36 dB/oct |
| N36 | Notch | 36 dB/oct |

### 4-2. Surgeon Filter Mode (4종)

| Mode | 설명 | Spread 동작 |
|------|------|-----------|
| Low Pass | 로우패스 | 비활성 |
| Band Pass | 밴드패스 | 피크/컷 폭 제어 |
| High Pass | 하이패스 | 비활성 |
| Notch | 노치 | 노치 폭 제어 |

### 4-3. 펌웨어 내부 구조

Osc2 Audio Processor는 펌웨어에서 Osc Type enum에 직접 포함 (index 16–19). VCF와 달리 **키보드 트래킹 불가** (Cutoff 파라미터에 Mod Matrix로만 제어).

```
VCF (아날로그):  LP, BP, HP (SEM-style 12dB/oct) — 하드웨어 버튼 선택
Audio Processor: Multi/Surgeon/Comb/Phaser Filter — 디지털 처리 (Osc2 전용)
```

---

## 5. Vocoder 서브타입 (4종)

Vocoder Self (index 11)과 Vocoder Ext In (index 12)이 **공유**하는 4종 서브타입.

| # | 서브타입 | 설명 | DSP 특성 |
|---|---------|------|---------|
| 0 | **Clean** | 모던 하이파이 보코더 | 높은 음성 명료도, 넓은 대역 |
| 1 | **Vintage** | 70/80년대 레트로 보코더 | 따뜻한 색감, 좁은 대역 |
| 2 | **Narrow** | 좁은 대역 보코더 | 매우 높은 레조넌스, 사운드 디자인용 |
| 3 | **Gated** | 게이티드 보코더 | 입력 신호 기반 플러키/드롭렛 사운드 |

### 5-1. Vocoder Self vs Vocoder Ext In

| 속성 | Vocoder Self | Vocoder Ext In |
|------|-------------|----------------|
| **캐리어** | MiniFreak 신디사이저 신호 | MiniFreak 신디사이저 신호 |
| **모듈레이터** | MiniFreak 자체 신호 (필터 뱅크) | 외부 오디오 입력 (사이드체인) |
| **펌웨어 함수** | `FUN_0800c87c` (mode=1, 243B) | `FUN_0800c6ac` (mode=2, 336B) |
| **서브프로세서** | SP5 | SP4 |
| **구조체 크기** | 0xF3 (243B) | 0x150 (336B) |

### 5-2. Vocoder 파라미터

| 파라미터 | Vocoder Self | Vocoder Ext In |
|---------|-------------|----------------|
| 파라미터 1 | **Spectrum** (주파수 분석 폭) | **Time** (디케이 타임) |
| 파라미터 2 | **Formant Shift** (포먼트 시프트) | **Intensity** (주파수 콘텐츠 시프트) |
| 파라미터 3 | **Amount** (드라이/프로세스 블렌드) | **Amount** (드라이/프로세스 블렌드) |

> Gated 서브타입에서는 Formant Shift / Intensity 파라미터가 **게이트 임계값**으로 동작.

### 5-3. 펌웨어 DSP 특성

```
Vocoder Self (SP5 FUN_0800c87c):
  - mode = 1
  - 6개 밴드패스 필터 (c2b0 ×4 + c854 ×2)
  - 3개 오실레이터 + 1개 딜레이라인
  - 1.0/n_bands 정규화 (보코더 특유)
  - 파라미터 포인터로 주파수 데이터 직접 로드

Vocoder Ext In (SP4 FUN_0800c6ac):
  - mode = 2
  - 6개 밴드패스 필터 (c260 ×2 + c288 ×2 + c2b0 ×2)
  - 3개 오실레이터 + 2개 딜레이라인 + 2개 LFO
  - 1.0/n_bands 정규화
  - 가장 큰 서브프로세서 구조체 (336B)
```

---

## 6. 그래뉼러 엔진 (7종) 및 파라미터

### 6-1. 그래뉼러 엔진 목록

V2.9 (V3)에서 추가된 7종 그래뉼러 오실레이터. **OSC1 전용**.

| OSC1 Index | 엔진 명 | 펌웨어 enum Index | 설명 |
|-----------|--------|------------------|------|
| 17 | **Cloud Grains** | 14 | 흩어진 그레인 클라우드 — 텍스처/패드용 |
| 18 | **Hit Grains** | 15 | 타격형 그레인 — 퍼커시브/리듬용 |
| 19 | **Frozen** | 16 | 프리즌 그레인 — 스태틱 텍스처 |
| 20 | **Skan** | 17 | 스캐닝 그레인 — 플레이헤드 속도 제어 |
| 21 | **Particle** | 18 | 파티클 그레인 — 밀도 기반 |
| 22 | **Lick** | 19 | 릭 그레인 — 템포 싱크 (1/16) |
| 23 | **Raster** | 20 | 래스터 그레인 — 템포 서브디비전 |

### 6-2. 그래뉼러 파라미터 (8종)

3개 노브 (Wave, Timbre, Shape)가 엔진별로 다른 파라미터에 매핑됨. **Volume**은 모든 엔진 공통.

#### 파라미터 정의

| # | 파라미터 | 노브 | 대응 엔진 | 설명 | 범위 |
|---|---------|------|---------|------|------|
| 1 | **Start** | Wave | 전체 (7종) | 샘플 시작점 | 0–100 |
| 2 | **Density** | Timbre | Cloud, Hit, Particle, Raster | 그레인 생성 속도 | 0–100 |
| 3 | **Chaos** | Shape | Cloud, Frozen, Skan, Particle, Lick, Raster | 그레인 무작위화 | 0–100 |
| 4 | **Size** | Timbre | Frozen, Lick | 그레인 길이 | 0–100 |
| 5 | **Shape** | Shape | Hit Grains | 그레인 길이, 어택, 홀드 | 0–100 |
| 6 | **Scan** | Timbre | Skan | 플레이헤드 속도 | 0–100 |
| 7 | **Volume** | (공통) | 전체 (7종) | 오실레이터 출력 레벨 | 0–100 |
| 8 | **Mod Quant** | (공통) | 전체 (7종) | 모듈레이션 양자화 스케일 | Continuous/Chromatic/Octaves 등 |

#### 엔진별 파라미터 매핑

| 엔진 | Wave | Timbre | Shape |
|------|------|--------|-------|
| **Cloud Grains** | Start | Density | Chaos |
| **Hit Grains** | Start | Density | Shape |
| **Frozen** | Start | Size | Chaos |
| **Skan** | Start | Scan | Chaos |
| **Particle** | Start | Density | Chaos |
| **Lick** | Start | Size | Chaos |
| **Raster** | Start | Density | Chaos |

### 6-3. 그래뉼러 엔진별 상세

#### Cloud Grains (흩어진 클라우드)
- 여러 그레인을 동시에 생성하여 텍스처/패드 사운드 생성
- **Density**가 높을수록 더 많은 그레인 동시 발생
- **Chaos**로 그레인 위치, 피치, 길이 무작위화

#### Hit Grains (타격형)
- 타격 소리 생성 (퍼커시브/리듬)
- **Shape**으로 그레인 길이, 어택 길이, 홀드 제어
- 짧은 Shape = 날카로운 타격, 긴 Shape = 부드러운 타격

#### Frozen (정지 텍스처)
- 샘플을 그레인으로 분해하여 정지된 텍스처 생성
- **Size**로 개별 그레인 길이 제어 (짧=그래뉼러, 김=스태틱)
- **Chaos**로 그레인 분산도 제어

#### Skan (스캐닝)
- 플레이헤드가 샘플을 스캔하며 그레인 생성
- **Scan**으로 플레이헤드 속도 제어
- **Chaos**로 스캔 위치 무작위화

#### Particle (파티클)
- 밀도 기반 파티클 생성
- **Density**로 파티클 생성 비율 제어
- **Chaos**로 파티클 특성 무작위화

#### Lick (템포 싱크)
- 그레인 생성이 템포에 동기화 (1/16 노트)
- **Size**로 그레인 크기 제어
- **Chaos**로 리듬 변형

#### Raster (래스터)
- 템포 서브디비전 기반 그레인 생성 (1/2 ~ 1/32)
- **Density**로 템포 서브디비전 선택
- **Chaos**로 타이밍 변형

### 6-4. 펌웨어 내부 구조

그래뉼러 엔진은 펌웨어 Oscillator Type enum에서 연속된 index (14–20)를 차지. Sample 엔진(index 13)과 동일한 샘플 메모리를 공유하며, 그레인 단위로 오디오를 분해하여 재합성.

```
Sample (index 13) ──┐
                     ├── 공유 샘플 메모리
Cloud Grains (14)  ──┤
Hit Grains   (15)  ──┤
Frozen       (16)  ──┤
Skan         (17)  ──┤
Particle     (18)  ──┤
Lick         (19)  ──┤
Raster       (20)  ──┘
```

---

## 부록: 펌웨어 주소 참조

### CM4 펌웨어 (`minifreak_main_CM4__fw4_0_1_2229`)

| 항목 | 주소 | 설명 |
|------|------|------|
| FX 타입 문자열 테이블 | `0x081AF308` | 11개 연속 포인터 (8B 간격) |
| FX 타입 추가 (Vocoder Ext) | `0x081AF37C` | |
| FX 타입 추가 (Destroy) | `0x081AF458` | Osc2 Audio Processor 문자열 |
| FX 타입 추가 (Delay) | `0x081AE368` | |
| OSC 타입 문자열 테이블 | `0x081AF388` | Basic Waves, SuperWave... |
| Oscillator Type enum | `0x081AF474` | 펌웨어 내부 enum (21슬롯) |
| VCF 타입 enum | `0x081AF4D0` | LP/BP/HP/Notch/LP1/HP1/Notch2 (7종) |
| Voice Mode enum | `0x081AF4F4` | Run/Loop/Unison/Uni(Poly)/Uni(Para)/Mono/Para |
| Voice Steal Mode | `0x081AF974` | None/Cycle/Reassign/Velocity/Aftertouch/Velo+AT |
| eEditParams enum | `0x081AF904` | 에디트 파라미터 문자열 테이블 |
| Mod Source enum | `0x081B1BCC` | 9개 소스 (Keyboard~Wavetable Select) |
| Mod Dest enum | `0x081AEA94` | 하드웨어드 목적지 |

### FX 코어 펌웨어 (`minifreak_fx__fw1_0_0_2229`)

| 항목 | 주소 | 설명 |
|------|------|------|
| FX 체인 초기화 | `FUN_0800CA04` | 3슬롯 × 7서브프로세서 |
| SP0 Comp | `FUN_0800B4F4` | 48B, 컴프레서 |
| SP1 Delay A | `FUN_0800BBA0` | 148B, 5-tap 딜레이 |
| SP2 Delay B | `FUN_0800BC88` | 148B, 5-tap 딜레이 변형 |
| SP3 Reverb | `FUN_0800C5D0` | 224B, 디퓨저 리버브 |
| SP4 Vocoder Chord | `FUN_0800C6AC` | 336B, Vocoder Ext (mode=2) |
| SP5 Vocoder Band | `FUN_0800C87C` | 243B, Vocoder Self (mode=1) |
| SP6 Multi-FX | `FUN_0800BDD0` | 236B, Chorus/Phaser/EQ/Disto/Flanger/SuperUnison |
| 파라미터 직렬화 | `FUN_0800A83C` | 385 data ref, CM4→FX 파라미터 전송 |
| 모듈레이션 코어 | `FUN_080152E8` | Chorus/Flanger/Phaser 공유 (9 case) |
| RMS 엔벨롭 | `FUN_0800F25C` | MultiComp 엔벨롭 팔로워 |
| StereoDelay | `FUN_08012C3C` | 딜레이라인 + 올패스 필터 |
| SuperUnison | `FUN_0801559C` | 다중 보이스 + 파나이저 |
| Disto | `FUN_0801A468` | 비트크러셔/웨이브셰이퍼 |
| EQ3 | `FUN_0800934C` | 바이쿼드 체인 |
| MultiComp | `FUN_0800F2DC` | 멀티밴드 컴프레서 |

---

> **문서 버전**: 1.0
> **검증 상태**: VST XML (mf_enums.py) 기준 확정, 펌웨어 주소는 CM4 Ghidra 분석 기준
