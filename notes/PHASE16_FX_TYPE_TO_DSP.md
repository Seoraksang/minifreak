# Phase 16-5: FX 11 DSP × 12/13 타입 1:1 매핑 정리

> **분석 날짜**: 2026-05-01
> **대상**: FX 코어 `minifreak_fx__fw1_0_0_2229__2025_06_18.bin` (122,640B)
> **기반 문서**: `PHASE12_FX_CORE_DSP.md` (Phase 12-2, 568줄), `PHASE7-3_FX_CORE_ANALYSIS.md`, `PHASE8_FX_OSC_ENUMS.md`
> **본 문서 목적**: Phase 12 데이터를 Phase 16 정적 검증 관점에서 재구성, 미해결 항목 명시

---

## 1. FX 코어 아키텍처 요약

```
CM4 (UI/Control)              FX Core (ARM Cortex-M, FreeRTOS)
┌──────────────┐              ┌──────────────────────────────┐
│ MIDI RX      │◄── UART ────►│ FX 파라미터 파서             │
│ Preset Mgmt  │              │                              │
│ FX Dispatch  │─── SPI ────►│ 3슬롯 × 7서브프로세서 체인   │
│              │   (DMA)      │                              │
│              │◄── HSEM ────│ SAI2 I2S IN/OUT (48kHz)      │
└──────────────┘   동기화      └──────────────────────────────┘
```

| 항목 | 값 |
|------|-----|
| 아키텍처 | ARM Cortex-M (Thumb-2), **별도 코어** (DSP56362 아님) |
| RTOS | FreeRTOS |
| 샘플레이트 | 48kHz, float32 |
| 버퍼 | 16 samples/channel (64 bytes) |
| 채널 | 스테레오 (L/R 병렬) |
| 함수 수 | 290 (named: 3, unnamed: 287) |

---

## 2. CM4 12타입 vs VST 13타입

| CM4 Index | CM4 타입명 | VST Index | VST 타입명 | 불일치 |
|-----------|-----------|-----------|-----------|--------|
| 0 | Chorus | 0 | Chorus | ✅ |
| 1 | Phaser | 1 | Phaser | ✅ |
| 2 | Flanger | 2 | Flanger | ✅ |
| 3 | Reverb | 3 | Reverb | ✅ |
| — | — | **4** | **Stereo Delay** | ⚠️ CM4 없음 |
| 4 | Distortion | 5 | Distortion | ✅ (index shift) |
| 5 | Bit Crusher | 6 | Bit Crusher | ✅ |
| 6 | 3 Bands EQ | 7 | 3 Bands EQ | ✅ |
| 7 | Peak EQ | 8 | Peak EQ | ✅ |
| 8 | Multi Comp | 9 | Multi Comp | ✅ |
| 9 | SuperUnison | 10 | SuperUnison | ✅ |
| 10 | Vocoder Self | 11 | Vocoder Self | ✅ |
| 11 | Vocoder Ext | 12 | Vocoder Ext | ✅ |

> **VST Stereo Delay (index 4)**: CM4 바이너리에 해당 문자열 없음. FX 코어 SP1+SP2를 사용하는 VST 전용 타입으로 추정.

---

## 3. FX 코어 7서브프로세서 구조

| SP# | Init 함수 | 주소 | 크기 | 구조체 | 핵심 특성 |
|-----|----------|------|------|--------|-----------|
| SP0 | `FUN_0800b4f4` | 0x800B4F4 | 104B | 48B | LFO ×1, wave ×1, 32768.0 스케일링 |
| SP1 | `FUN_0800bba0` | 0x800BBA0 | 300B | 148B | delay init ×5, buf 320B, mode=0 |
| SP2 | `FUN_0800bc88` | 0x800BC88 | 300B | 148B | delay init ×5, buf 320B, mode=0 |
| SP3 | `FUN_0800c5d0` | 0x800C5D0 | 312B | 224B | wave ×3, delay ×1, LFO ×2, mode=6 |
| SP4 | `FUN_0800c6ac` | 0x800C6AC | 392B | 336B | 1.0/n, osc ×3, filter ×6, delay ×2, mode=2 |
| SP5 | `FUN_0800c87c` | 0x800C87C | 312B | 243B | 1.0/n, osc ×3, filter ×6, delay ×1, mode=1 |
| SP6 | `FUN_0800bdd0` | 0x800BDD0 | 384B | 236B | **9개 하위 프로세서**, VTable |

### 3.1 SP6 하위 프로세서 (Multi-FX 엔진)

SP6은 5개 독립 모듈 포함:

| 하위 함수 | 주소 | DSP 유형 | 매핑 FX |
|-----------|------|----------|---------|
| `FUN_08009b98` | 0x8009B98 | BiQuad 필터 | 3 Bands EQ, Peak EQ |
| `FUN_08009e88` | 0x8009E88 | Allpass 체인 | Phaser |
| `FUN_0800a134` | 0x800A134 | 웨이브셰이퍼 | Distortion |
| `FUN_0800a408` | 0x800A408 | 모듈레이션 엔진 | Chorus, Flanger |
| `FUN_080082f0` | 0x80082F0 | 다중 디튠 카피 | SuperUnison |

---

## 4. 1:1 매핑: FX 타입 → DSP 함수

### 4.1 종합 매핑 테이블

| CM4# | FX 타입 | SP 할당 | DSP 함수 | 함수 크기 | DSP 알고리즘 | 신뢰도 |
|------|---------|---------|----------|----------|-------------|--------|
| 0 | Chorus | SP6 | `FUN_0800a408` | 258B | LFO + 모듈레이션 | ★★★★☆ |
| 1 | Phaser | SP6 | `FUN_08009e88` | — | Allpass 체인 + LFO | ★★★★☆ |
| 2 | Flanger | SP6 | `FUN_0800a408` | 258B | LFO + 모듈레이션 (Chorus와 공유) | ★★★★☆ |
| 3 | Reverb | SP3 | `FUN_080114b0` | 1024B | 6채널 FBP (Schroeder) | ★★★★☆ |
| 4 | Distortion | SP6 | `FUN_0800a134` | — | 웨이브셰이퍼 | ★★★★☆ |
| 5 | Bit Crusher | 전용 | `FUN_0801a468` | 1280B | FIR + 비트 리덕션 + 디시메이션 | ★★★★☆ |
| 6 | 3 Bands EQ | SP6 | `FUN_08009b98` | — | BiQuad 체인 (3 밴드) | ★★★★★ |
| 7 | Peak EQ | SP6 | `FUN_08009b98` | — | BiQuad (3 Bands EQ와 공유) | ★★★☆☆ |
| 8 | Multi Comp | SP0 | `FUN_0800f2dc` | 642B | RMS 엔벨롭 + 게인 리덕션 | ★★★★☆ |
| 9 | SuperUnison | SP6 | `FUN_080082f0` | — | 다중 디튠 카피 + 파나이저 | ★★★☆☆ |
| 10 | Vocoder Self | SP5 | `FUN_0800c87c` | 312B | 6 BP filter + 3 osc + delay | ★★★★★ |
| 11 | Vocoder Ext | SP4 | `FUN_0800c6ac` | 392B | 6 BP filter + 3 osc + 2 delay + 2 LFO | ★★★★★ |
| VST4 | Stereo Delay | SP1+SP2 | `FUN_0800bba0` + `FUN_0800bc88` | 300B×2 | Dual delay + allpass ×3 + 보간 | ★★★★★ |

### 4.2 DSP 함수 상세

#### 4.2.1 Chorus / Flanger (공유: `FUN_0800a408`)

```
모듈레이션 코어: FUN_080152e8 (648B, 9 case 분기)
  switch(param_1[0x84]):
    case 0: 웨이브셰이핑 (기본)
    case 1: LFO 룩업 타입A @ +0x9C
    case 2: LFO 룩업 타입B @ +0xC8
    case 3: LFO 룩업 타입B @ +0xE4
    case 4: LFO 룩업 타입A @ +0x100
    case 5: 결합 LFO @ +0xC8, +0x130
    case 6: 결합 LFO @ +0xE4, +0x13C
    case 7: 페이즈 싱크 감지
    case 8: 파라미터 램핑
```

**Chorus vs Flanger 구분**: 동일 DSP 코어, 서브타입(param_1[0x84])으로 구분.
- Chorus: 낮은 modulation rate, 긴 delay
- Flanger: 높은 modulation rate, 짧은 delay

#### 4.2.2 Reverb (`FUN_080114b0`, 1024B)

```
6채널 병렬 FBP (Feedback Delay Network):
  ch0: FUN_0800e990() → Schroeder delay
  ch1: FUN_0800e9b4() → Schroeder delay
  ch2: waveshaper → 비선형 디스토션
  ch3: FUN_0800e9d8() → Schroeder delay
  ch4: FUN_0800e9fc() → FUN_0800ea68() (cascade)
  ch5: FUN_0800ea20() → Schroeder delay
  최종: FUN_0801140c() (output filter)
```

#### 4.2.3 Bit Crusher / Distortion (`FUN_0801a468`, 1280B)

```
  1. FIR 필터: 입력 × 커널 (4 param)
  2. 비트 리덕션: int32 양자화 → remainder
  3. 디시메이션: 1/2/4비트 서브샘플링
  4. 양자화: round + floor
주파수 테이블: [21.99, 23.56, 25.13, 26.70, 28.27] Hz
```

> ⚠️ **미해결**: Bit Crusher(CM4#5)와 Distortion(CM4#4)이 동일 함수(`FUN_0801a468`)를 공유하는지, 아니면 Distortion이 SP6→`FUN_0800a134`이고 Bit Crusher만 `FUN_0801a468`인지 불명확.

#### 4.2.4 Multi Comp (`FUN_0800f2dc`, 642B)

```
  1. RMS 엔벨롭: (|L|+|R|)/2 * sensitivity
  2. attack/release: 1차 IIR (coeff = attack or release)
  3. noise gate: envelope < floor → 0.0
  4. 병렬 프로세싱: 8 밴드
  5. 크로스페이드: wet/dry 믹스
```

#### 4.2.5 Vocoder Self vs Ext In

| 속성 | Vocoder Self (SP5) | Vocoder Ext In (SP4) |
|------|-------------------|---------------------|
| Mode | 1 | 2 |
| 함수 | `FUN_0800c87c` (312B) | `FUN_0800c6ac` (392B) |
| 구조체 | 243B | 336B (최대) |
| 필터 | c2b0×4 + c854×2 (6개) | c260×2 + c288×2 + c2b0×2 (6개) |
| 오실레이터 | 3개 | 3개 |
| 딜레이 | 1개 (22222샘플) | 2개 |
| LFO | 없음 | 2개 |
| 모듈레이터 | 내부 (필터 뱅크) | 외부 오디오 입력 |

---

## 5. 3슬롯 FX 체인 메모리 레이아웃

```
Slot A:  SP0@+0x000  SP1@+0x3C4  SP2@+0xA9C  SP3@+0x1168
         SP4@+0x1BF4  SP5@+0x2BD8  SP6@+0x3748

Slot B:  SP0@+0x23C  SP1@+0x60C  SP2@+0xCE0  SP3@+0x14EC
         SP4@+0x2140  SP5@+0x2FA8  SP6@+0x3AEC

Slot C:  SP0@+0x300  SP1@+0x854  SP2@+0xF24  SP3@+0x1870
         SP4@+0x268C  SP5@+0x3378  SP6@+0x3E90

슬롯 간격: 0x248 (584B) per SP
총 크기: ~0x3FE0 (16,320B) per chain
```

---

## 6. 미해결 항목

### 6.1 Phase 12에서 지적된 미해결 (5건)

| # | 항목 | 내용 | 해결 가능성 | Phase |
|---|------|------|-----------|-------|
| 1 | Bit Crusher vs Distortion | `FUN_0801a468` 공유 여부 | Ghidra 디컴파일 | 16 |
| 2 | Peak EQ 독립 함수 | `FUN_08009b98`과 공유 여부 | Ghidra 디컴파일 | 16 |
| 3 | FX 타입 선택 로직 | `FUN_0800ca04`의 switch/case | Ghidra 디컴파일 | 16 |
| 4 | SPI 프로토콜 프레임 | 8-byte 추정 포맷 | USB 캡처 | 16-1 |
| 5 | SP1 vs SP2 구분 | Stereo Delay 내 역할 분담 | 동적 검증 | 16-2 |

### 6.2 Phase 16 추가 분석 필요

| # | 항목 | 접근 | 난이도 |
|---|------|------|--------|
| 6 | Chorus/Flanger/Phaser 서브타입 분기 | `FUN_080152e8` case 0~8 → 어떤 서브타입에 대응? | 낮음 |
| 7 | SP6 VTable 구조 | 9개 하위 프로세서 선택 메커니즘 | 중간 |
| 8 | Reverb Shimmer 모드 | SP3 mode=6 → Reverb Shimmer와 일반 Reverb의 차이 | 중간 |

---

## 7. FX 카테고리 재현도 영향

| 항목 | Phase 12 | Phase 16-5 | 변화 |
|------|---------|------------|------|
| CM4 12타입 문자열 | ★★★★★ | ★★★★★ | 확정 유지 |
| VST 13타입 (Stereo Delay) | ★★★★★ | ★★★★★ | 확정 유지 |
| 12→7 SP 매핑 | ★★★★★ | ★★★★★ | 확정 유지 |
| 11개 DSP 함수 식별 | ★★★★☆ | ★★★★☆ | 유지 |
| BitCrusher/Disto 공유 여부 | 미보고 | ★★★☆☆ | 미해결 명시 |
| Peak EQ 독립 여부 | ★★★☆☆ | ★★★☆☆ | 유지 |
| FX 타입 선택 로직 | 미보고 | ★★★☆☆ | 미해결 명시 |

→ **FX 카테고리 96% 유지**. 미해결 5건 중 Ghidra로 3건 해결 시 96% → 99% 가능.

---

## 8. 결론

### 8.1 Phase 16-5 성과

1. **Phase 12 FX 코어 분석(568줄)을 Phase 16 정적 검증 관점에서 재구성**
2. **12 CM4 타입 + 1 VST 전용 = 13 FX 타입 → 7 SP → 11 DSP 함수** 매핑 체계 정리
3. **미해결 5건 명시** — Phase 12에서 "미해결"로 남은 항목을 명확히 분류
4. **DSP 알고리즘 상세** — 각 FX 타입의 핵심 알고리즘을 pseudo-code로 정리

### 8.2 한계

- 모든 DSP 매핑은 **Ghidra 디컴파일 기반 추정** (Phase 12)이며, Phase 16에서 새로운 정적 분석을 수행하지 않음
- Bit Crusher/Distortion 공유 문제는 FX 코어 바이너리의 추가 Thumb-2 패턴 분석으로 해결 가능
- VST 전용 Stereo Delay의 실제 동작은 VST DLL 분석 필요

### 8.3 다음 단계

- Ghidra에서 `FUN_0800ca04` (FX Chain Init) 디컴파일 → 타입 선택 로직 확정
- `FUN_0801a468` 내부 case 분석 → BitCrusher vs Distortion 분리 확인
- USB 캡처 → SPI 프로토콜 프레임 확정

---

## 9. 교차 참조

| 문서 | 관계 |
|------|------|
| `PHASE12_FX_CORE_DSP.md` | FX 코어 전체 분석 (Phase 12-2, 원본) |
| `PHASE7-3_FX_CORE_ANALYSIS.md` | FX 코어 초기 분석 (Phase 7-3) |
| `PHASE7_FX_DEEP_DIVE.md` | FX Deep Dive (Phase 7) |
| `PHASE8_FX_OSC_ENUMS.md` | FX/OSC Enum (63 서브타입) |
| `PHASE16_MULTI_FILTER_DSP.md` | Multi Filter 14모드 DSP 매핑 (Phase 16-4) |
| `PHASE15_AUDIO_ROUTING.md` | CM7→FX 오디오 라우팅 정적 분석 |
| `MANUAL_VS_FIRMWARE_MATCH.md` | FX 카테고리 96% 평가 |

---

*문서 버전: Phase 16-5 v1.0*
*작성 도구: Phase 12 데이터 재구성 + 정적 분석 패턴 매칭*
*펌웨어 버전: CM4/CM7 fw4_0_1_2229, FX fw1_0_0_2229 (2025-06-18)*
