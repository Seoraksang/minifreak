# MiniFreak C++ 재구현 마스터플랜

> **2026-05-01** | 정적 분석 완료율 98% → C++ 재구현 목표 100%
> **전제**: Ghidra + PyGhidra 기반 DSP 역설계, Plaits MIT 소스 활용

---

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                    MiniFreak Audio Engine                     │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  Control     │  Sequencer   │  Audio       │  FX            │
│  Layer       │  Layer       │  Core        │  Chain         │
│  (CM4)       │  (CM7)       │  (CM7)       │  (FX DSP)      │
├──────────────┼──────────────┼──────────────┼────────────────┤
│ Preset       │ Step Seq     │ Oscillator   │ Chorus         │
│ MIDI CC      │ Arpeggiator  │ VCF          │ Delay          │
│ SysEx/Collage│ LFO          │ VCA          │ Reverb         │
│ Mod Matrix   │ Env Gen      │ Voice Alloc  │ Vocoder        │
│ Calibration  │ Smoothing    │ Audio Route  │ Multi-FX       │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

---

## Phase 19: CM7 오디오 메인 루프 & 파이프라인 역설계 ⏳ IN PROGRESS

**목표**: CM7 DSP의 진입점 → 오디오 처리 체인 전체 추적

| Task | 내용 | 난이도 | 예상 시간 |
|------|------|--------|----------|
| 19-1 | TIM2/IRQ 디스패치 → 오디오 트리거 메커니즘 확정 | 중 | 2~4h |
| 19-2 | 메인 루프: voice render → VCF → VCA → mix → output 파이프라인 | 고 | 4~8h |
| 19-3 | CM7↔FX 인터코어 오디오 버퍼 구조 확정 | 중 | 2~3h |
| 19-4 | CM7↔CM4 파라미터 공유 메모리 레이아웃 | 중 | 2~3h |

**산출물**: `PHASE19_CM7_AUDIO_PIPELINE.md`, CM7 메인 루프 C 의사코드

---

## Phase 20: 오실레이터 엔진 역설계

**목표**: 24종 오실레이터 타입의 DSP 알고리즘 완전 추출

| Task | 내용 | 신뢰도 | 예상 시간 |
|------|------|--------|----------|
| 20-1 | Plaits 통합 분석 — MIT 소스 ↔ CM7 바이너리 매칭 | ★★★★★ | 3~5h |
| 20-2 | Audio Processor 타입 (Multi/Surgeon/Comb/Phaser/Destroy) | ★★★★☆ | 6~10h |
| 20-3 | V3 엔진 (Wavetable/Sample/Granular ×7) | ★★★☆☆ | 8~15h |
| 20-4 | Voice unison/detune 렌더링 로직 | ★★★★☆ | 3~5h |
| 20-5 | 오실레이터 vtable 구조 → C++ 가상 함수 클래스 | ★★★★☆ | 2~3h |

**참고**: Plaits(MIT) 소스가 이미 있으므로 20-1은 비교적 쉬움. 20-2~3이 핵심 난관.

---

## Phase 21: 아날로그 모델링 (VCF/VCA)

**목표**: VCF 3종 + VCA의 DSP 알고리즘 추출

| Task | 내용 | 난이도 | 예상 시간 |
|------|------|--------|----------|
| 21-1 | VCF 렌더링 함수 디컴파일 (LP/BP/HP) | 고 | 6~10h |
| 21-2 | VCF 계수(coefficient) 계산 — cutoff/resonance → biquad/moog ladder | 고 | 4~8h |
| 21-3 | VCA envelope follower + gain staging | 중 | 3~5h |
| 21-4 | CvCalib 보정 곡선 — DAC value → Hz/level 매핑 | 중 | 2~4h |
| 21-5 | DAC1 출력 제어 (12-bit → 아날로그) | 중 | 2~3h |

**참고**: DAC1(STM32 내장) 사용 확정. CvCalib 11메서드 시그니처 이미 확보.

---

## Phase 22: FX 엔진 (FX 코어 120K)

**목표**: 11종 FX 타입의 DSP 알고리즘 추출

| Task | 내용 | 난이도 | 예상 시간 |
|------|------|--------|----------|
| 22-1 | FX 아키텍처: 3슬롯 × 7서브프로세서 → 라우팅 | 중 | 3~5h |
| 22-2 | Chorus (Default/Lush + Vibrato/Warm) | 중 | 4~6h |
| 22-3 | Delay (Mono/Stereo + Multitap) | 중 | 4~6h |
| 22-4 | Reverb (plate/hall/shimmer) | 고 | 8~12h |
| 22-5 | Vocoder (Band/Chord + 6밴드필터 체인) | 고 | 6~10h |
| 22-6 | Multi-FX (EQ3/AP/WaveShaper/Mod/MultiDetune) | 고 | 8~12h |
| 22-7 | Comp (압축기 + MultiComp) | 중 | 4~6h |
| 22-8 | BitCrusher/PeakEQ/LoFi | 중 | 3~4h |

**참고**: FX 코어는 120K로 작아 Ghidra 전체 디컴파일이 가능. Phase 7-3에서 11개 DSP 함수 이미 식별.

---

## Phase 23: 서포팅 시스템

| Task | 내용 | 난이도 | 예상 시간 |
|------|------|--------|----------|
| 23-1 | Smoothing IIR (20함수) — NEON SIMD 포함 | 중 | 4~6h |
| 23-2 | Envelope Generator (ADSR ×2 + CycEnv) | 중 | 3~5h |
| 23-3 | LFO (Shaper 9종 + rate/depth/sync) | 중 | 3~5h |
| 23-4 | Mod Matrix evaluation (7×13 → 91 라우팅) | 중~고 | 4~6h |
| 23-5 | Arp 엔진 (Walk/RandOct/Mutate — LCG 이미 재현 완료) | ★★★★★ | 2~3h |
| 23-6 | Step Sequencer (64step × 24field 구조체) | 중 | 4~6h |
| 23-7 | Audio routing (CM7→FX insert/send→mix→output) | 중 | 3~5h |
| 23-8 | Spice/Dice (LCG + timestamp seed) | ★★★★★ | 1~2h |

---

## Phase 24: C++ 코드 생성

**목표**: 추출된 알고리즘으로 C++ 코드베이스 구축

| Task | 내용 | 예상 시간 |
|------|------|----------|
| 24-1 | Core 타입 정의 (eSynthParams, Voice Struct, Preset 등) | 3~5h |
| 24-2 | 컨트롤 레이어 (Preset, MIDI CC, SysEx, Collage) | 8~12h |
| 24-3 | 오디오 엔진 프레임워크 (render loop, voice alloc) | 6~10h |
| 24-4 | 오실레이터 구현 (24종) | 15~25h |
| 24-5 | VCF/VCA 구현 | 8~12h |
| 24-6 | FX 구현 (11종) | 15~25h |
| 24-7 | Arp/Seq/LFO/Mod 구현 | 10~15h |
| 24-8 | 빌드 시스템 (CMake) + 유닛 테스트 | 5~8h |
| 24-9 | 프리셋 호환성 검증 (.mnfx 로드/세이브) | 3~5h |

---

## Phase 25: 하드웨어 인터페이스 (실기 필요)

| Task | 내용 | 필요 장비 |
|------|------|----------|
| 25-1 | STM32H747 HAL 레이어 (DAC1, ADC, SAI, GPIO) | MiniFreak |
| 25-2 | USB MIDI 인터페이스 | MiniFreak + PC |
| 25-3 | Collage USB 프로토콜 | MiniFreak + Linux usbmon |
| 25-4 | UI MCU 통신 (USART2) | MiniFreak + ST-Link |
| 25-5 | 펌웨어 플래싱 테스트 | MiniFreak + ST-Link |

---

## 일정 추정

```
Phase 19 (CM7 메인 루프)      : 10~18h  ← 지금 진행 중
Phase 20 (오실레이터)         : 22~38h
Phase 21 (VCF/VCA)           : 17~30h
Phase 22 (FX)                : 40~61h
Phase 23 (서포팅)            : 24~38h
Phase 24 (C++ 코드)          : 73~107h
Phase 25 (HW 인터페이스)     : 실기 필요
─────────────────────────────────────
총합 (소프트웨어만)          : ~186~292h
```

---

## 우선순위 (가치/난이도 기준)

| 순위 | Task | 이유 |
|------|------|------|
| 🥇 1 | **19-1~2** CM7 메인 루프 | 모든 것의 기반 — 진입점을 알아야 파이프라인 추적 가능 |
| 🥈 2 | **22-1** FX 아키텍처 | FX 코어 작음(120K) — 빠른 성과, 3슬롯 구조 확정 |
| 🥉 3 | **20-1** Plaits 통합 | MIT 소스 있어 가장 쉬운 오실레이터 분석 |
| 4 | **21-1~2** VCF | 사운드 핵심 — 모델링 기법 확정이 다른 것에 영향 |
| 5 | **23-5,8** Arp+Spice | 이미 LCG 재현 완료 → 코드화만 하면 됨 |
| 6 | **23-4** Mod Matrix | 91 라우팅 evaluation order 확정 |
| 7 | **22-2~8** FX 개별 | DSP 난이도 높지만 FX 코어 작아서 시간 예측 가능 |
| 8 | **20-2~3** 나머지 OSC | 가장 복잡한 DSP |
| 9 | **24-1~9** C++ 코드 | Phase 19~23 완료 후 병렬 가능 |

---

## 기존 자산 활용

| 자산 | 내용 | 활용 |
|------|------|------|
| **mf_enums.py** | 15 enum 테이블, 512 프리셋 검증 | C++ enum 정의 그대로 사용 |
| **LCG 재현** | Arp RandOct/Mutate 99.5% 일치 | C++ 코드 바로 작성 가능 |
| **Phase 7-3 FX 분석** | 11 DSP 함수 식별, vtable 구조 | FX C++ 클래스 스켈레톤 |
| **Phase 8 CC 매핑** | 161 CC × 145 param 매트릭스 | MIDI 핸들러 구현 |
| **Phase 9 Voice Alloc** | 0x118 byte/voice, 6슬롯 | Voice struct 정의 |
| **Phase 15 AXI SRAM** | 인터코어 버퍼 오프셋 확정 | 공유 메모리 레이아웃 |
| **Phase 18 CvCalib** | 11메서드 시그니처 | 캘리브레이션 클래스 |
| **Plaits MIT 소스** | Emilie Gillet 오픈소스 | 오실레이터 기반 코드 |
| **boost::serialization** | .mnfx 포맷 완전 분석 | 프리셋 I/O |
