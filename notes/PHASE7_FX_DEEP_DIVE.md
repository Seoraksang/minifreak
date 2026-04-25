# Phase 7 — FX 코어 심층 분석 (추가)

## 분석 대상
- FX 바이너리: `minifreak_fx__fw1_0_0_2229__2025_06_18.bin`
- 분석 스크립트: `~/hoon/ghidra/scripts/fx_remaining_analysis.py`
- 산출물: `fx_vocoder.json`, `fx_type_subprocessor_map.json`, `fx_spi_protocol.json`

---

## 1. Vocoder 함수 식별

### 1-1. 후보 함수 식별

`FUN_0800ca04`(FX init)에서 호출하는 7개 서브프로세서 중 **3개**가 Vocoder 패턴을 보임:

| 함수 | Vocoder 지표 | 확신도 |
|------|-------------|--------|
| `FUN_0800c5d0` | `1.0/n` 없음, wave init ×3, delay line ×1, mode=0x06 (6밴드?) | **중간** |
| `FUN_0800c6ac` | ✅ `1.0/n` 패턴 (n_bands 역수), osc init ×3, filter(c260/c288/c2b0) ×6, delay ×2, mode=2, **struct 0x150바이트** | **높음** |
| `FUN_0800c87c` | ✅ `1.0/n` 패턴, osc init ×3, filter(c2b0/c854) ×6, delay ×1, mode=1, **struct 0xF3바이트** | **높음** |

### 1-2. Vocoder 패턴 근거

**`FUN_0800c6ac` — Vocoder Chord (mode=2)**
```c
param_1[0x1a] = 2;          // mode = 2 (Vocoder Chord)
param_1[0x67] = 1.0 / fVar5;  // 1.0/n_bands — Vocoder 특유의 정규화
FUN_0800b3e8(...);           // osc init ×3 (3개 LFO/oscillator)
FUN_0800c260(..., uVar4);    // filter init ×2
FUN_0800c288(..., uVar4);    // filter init ×2
FUN_0800c2b0(..., uVar4);    // filter init ×2
FUN_0801ad6c(..., 0x10);     // buffer alloc 16바이트 ×3
FUN_0800c3f8(..., 0x56ce);   // delay line init (22222샘플 ≈ 0.46초 @ 48kHz) ×2
```
- 구조체 크기: **0x150바이트 (336B)** — 가장 큰 서브프로세서
- 6개 밴드패스 필터 체인 (c260 ×2 + c288 ×2 + c2b0 ×2)
- 3개 오실레이터 + 2개 딜레이라인 + 2개 LFO

**`FUN_0800c87c` — Vocoder Band (mode=1)**
```c
param_1[0x1c] = 1;          // mode = 1 (Vocoder Band)
param_1[0x67] = 1.0 / fVar4;  // 1.0/n_bands
FUN_0800b3e8(...);           // osc init ×3
FUN_0800c2b0(..., uVar3);    // filter init ×4
FUN_0800c854(..., uVar3);    // filter init ×2
FUN_0800c3f8(..., 0x56ce);   // delay line ×1
```
- 구조체 크기: **0xF3바이트 (243B)**
- 6개 필터 (c2b0 ×4 + c854 ×2)
- 파라미터 포인터(`param_4`)로부터 주파수 데이터 직접 로드

### 1-3. FUN_0800c5d0 — Delay/Reverb (mode=6)
- `1.0/n` 패턴 없음 → Vocoder 아님
- wave init ×3 + delay line ×1 + LFO ×2
- 버퍼 96바이트 ×2개
- **mode=0x06** → Delay/Reverb 서브프로세서로 판단

### 1-4. 결론
| 함수 | FX 타입 | Mode | 구조체 크기 |
|------|---------|------|------------|
| `FUN_0800c6ac` | **Vocoder Chord** | 2 | 336B (0x150) |
| `FUN_0800c87c` | **Vocoder Band** | 1 | 243B (0xF3) |
| `FUN_0800c5d0` | Delay/Reverb | 6 | 224B (0xE0) |

---

## 2. FX 타입 → 서브프로세서 매핑

### 2-1. 7개 서브프로세서 특성 분석

| # | 함수 | 구조체 크기 | 핵심 특성 | FX 타입 추정 |
|---|------|------------|----------|-------------|
| 0 | `FUN_0800b4f4` | 48B (0x30) | LFO ×1, wave ×1, float 상수: 16.0, 32768.0 | **Comp** (컴프레서) |
| 1 | `FUN_0800bba0` | 148B (0x94) | delay init(bb60) ×5, buf 320B, mode=0 | **Delay** |
| 2 | `FUN_0800bc88` | 148B (0x93) | delay init(bb60) ×5, buf 320B, mode=0 | **Delay** (variant) |
| 3 | `FUN_0800c5d0` | 224B (0xE0) | wave ×3, delay ×1, LFO ×2, buf 96B×2, mode=6 | **Reverb** |
| 4 | `FUN_0800c6ac` | 336B (0x150) | `1.0/n`, osc ×3, filter ×6, delay ×2, mode=2 | **Vocoder Chord** |
| 5 | `FUN_0800c87c` | 243B (0xF3) | `1.0/n`, osc ×3, filter ×6, delay ×1, mode=1 | **Vocoder Band** |
| 6 | `FUN_0800bdd0` | 236B (0xEC) | osc ×1, wave ×2, LFO ×1, **9개 하위 프로세서**(9b98, 9e88, a134, a408, 82f0) | **EQ3/Disto/Flanger** |

### 2-2. 세부 매핑 근거

**SP0: `FUN_0800b4f4` — Comp (컴프레서)**
- 가장 작은 구조체 (48B) — 단일 밴드 처리
- LFO 1개 (모듈레이션)
- `32768.0` = full-scale 정규화 (컴프레서 threshold 스케일링)
- `16.0` = 디폴트 ratio 또는 time constant

**SP1: `FUN_0800bba0` — Delay Type A**
- `FUN_0800bb60` ×5 = 5개 딜레이 라인 (multitap delay)
- 버퍼 320B (float 80샘플 = ping-pong 딜레이)
- mode=0 (첫 번째 딜레이 변형)

**SP2: `FUN_0800bc88` — Delay Type B**
- SP1과 구조가 거의 동일 (5개 딜레이 라인, 320B 버퍼)
- 미세한 오프셋 차이 (0x93 vs 0x94)
- 다른 subtype (e.g., ping-pong vs stereo)

**SP3: `FUN_0800c5d0` — Reverb**
- 3개 wave init (diffuser/early reflection)
- 2개 딜레이 라인 + 2개 LFO (modulated reverb)
- mode=6

**SP6: `FUN_0800bdd0` — Multi-processor (EQ3/Disto/Flanger/SuperUnison)**
- **가장 복잡한 서브프로세서**: 9개 하위 초기화 함수
  - `FUN_08009b98` — EQ3 밴드 필터
  - `FUN_08009e88` — 추가 필터 스테이지
  - `FUN_0800a134` — 디스토션 웨이브셰이퍼
  - `FUN_0800a408` — 플랜저/코러스 모듈레이션
  - `FUN_080082f0` — 추가 프로세싱
- 2개 `FUN_0800bd70` init (duo 구조)
- VTable 포인터 (`param_1[0xdf] = &param_1[0xcf]`)

### 2-3. 11 FX 타입 → 서브프로세서 매핑

XML 프리셋의 11개 FX 타입을 서브프로세서에 매핑:

| FX 타입 | 서브프로세서 | 근거 |
|---------|------------|------|
| **Comp** (3 subtype) | SP0 `FUN_0800b4f4` | 단일 밴드, 32768.0 스케일링 |
| **Delay** (3 subtype) | SP1 `FUN_0800bba0` + SP2 `FUN_0800bc88` | 5-tap delay, subtype별 선택 |
| **Reverb** (3 subtype) | SP3 `FUN_0800c5d0` | 3 wave + 2 delay = diffused reverb |
| **Vocoder Band** (15 options) | SP5 `FUN_0800c87c` | mode=1, 6 filter bands |
| **Vocoder Chord** (15 options) | SP4 `FUN_0800c6ac` | mode=2, 6 filter bands + 3 osc |
| **Chorus** (3 subtype) | SP6 `FUN_0800bdd0` (via `FUN_0800a408`) | 모듈레이션 엔진 |
| **Phaser** (3 subtype) | SP6 `FUN_0800bdd0` (via `FUN_08009e88`) | 올패스 필터 |
| **EQ3** (3 subtype) | SP6 `FUN_0800bdd0` (via `FUN_08009b98`) | 3밴드 EQ |
| **Disto** (3 subtype) | SP6 `FUN_0800bdd0` (via `FUN_0800a134`) | 웨이브셰이퍼 |
| **Flanger** (3 subtype) | SP6 `FUN_0800bdd0` (via `FUN_0800a408`) | 모듈레이션 + 딜레이 |
| **SuperUnison** (3 subtype) | SP6 `FUN_0800bdd0` (via `FUN_080082f0`) | 다중 디테인 |

> **주요 발견**: SP6(`FUN_0800bdd0`)은 **멀티 FX 엔진**으로, 내부에 5개 독립 하위 프로세서를 가짐. Chorus/Phaser/EQ3/Disto/Flanger/SuperUnison은 모두 SP6 내부의 다른 하위 모듈을 활성화하여 동작.

### 2-4. 3슬롯 메모리 레이아웃

```
FUN_0800ca04(param_1, ...) 호출 패턴:
  SP0: param_1 + 0x000  (Slot A)
  SP0: param_1 + 0x23c  (Slot B)  → offset 0x23c = 572B
  SP0: param_1 + 0x300  (Slot C)  → offset 0x300 = 768B

  SP1: param_1 + 0x3c4  (Slot A)
  SP1: param_1 + 0x60c  (Slot B)  → offset 0x60c-0x3c4 = 0x248 = 584B
  SP1: param_1 + 0x854  (Slot C)  → offset 0x854-0x60c = 0x248 = 584B

  SP2: param_1 + 0xa9c  (Slot A)
  SP2: param_1 + 0xce0  (Slot B)  → 0x248 = 584B
  SP2: param_1 + 0xf24  (Slot C)  → 0x248 = 584B
```

**슬롯 크기: 584바이트** (확정) — Phase 7-3과 일치.

---

## 3. SPI 프로토콜 포맷 분석

### 3-1. 사용 페리페럴

| 페리페럴 | 베이스 주소 | 용도 |
|----------|------------|------|
| **SPI1** | `0x40015800` | CM4 ↔ FX 파라미터 스트림 |
| **SPI2** | `0x40015C00` | 보조 통신 |
| **SPI3** | `0x40016000` | 보조 통신 |
| **USART1** | `0x40011000` | CM4 커맨드 채널 (이전 분석과 상이 — USART3 아닌 USART1 가능성) |
| **DMA1** | `0x40004800` | 오디오 DMA (SAI2 ↔ 메모리) |
| **DMA2** | `0x40004C00` | SPI DMA 전송 |
| **BDMA/LPDMA** | `0x58005400` | 저전력 도메인 DMA |
| **MDMA** | `0x40007800` | 고속 메모리 전송 |
| **SYSCFG** | `0x40011400` | 핀/클럭 라우팅 |
| **GPIOI** | `0x40007C00` | SPI 칩셀렉트 GPIO |

### 3-2. SPI 설정 함수 분석

**`FUN_08005c00` — SPI TX 주파수 계산**
- STM32H7 SPI 클럭 프리스케일러 계산
- `VectorSignedFixedToFloat(..., 0x20, 0xd)` = Q13 고정소수점 → float 변환
- Baud rate 선택 로직: prescaler 값 0~3 → 4가지 클럭 속도
- 출력: `param_1[0..2]`에 3개 uint32 (CR1, CR2, I2SPR 설정값)

**`FUN_08005ab0` — SPI RX 주파수 계산**
- TX와 거의 동일한 구조 (dual SPI 설정)
- RX 전용 미세 차이 (오프셋 0x24에서 `0x6b55` vs `0x6c55`)

**`FUN_08006b28` — SPI 전체 설정 (13KB, 가장 큰 함수)**
- 페리페럴 클럭 인에이블 (RCC 레지스터)
- SPI1/SPI2/SPI3 레지스터 직접 설정
- DMA 채널 구성
- 인터럽트 핸들러 등록

**`FUN_08005ea0` — DMAC 설정**
- DMA 스트림 구성 (소스/목적 주소, 전송 크기)

**`FUN_08006510` — DMAC + 타이머 설정**
- DMA와 타이머 연동 (주기적 SPI 전송 트리거)

### 3-3. SPI 프로토콜 구조 (추정)

```
CM4 → FX SPI 프로토콜:
┌─────────────────────────────────────┐
│ Frame Format (SPI1, CPOL=0, CPHA=0)│
├─────────────────────────────────────┤
│ Byte 0:     [CMD | SLOT | TYPE]     │
│ Byte 1-2:   PARAM_INDEX (10-bit)   │
│ Byte 3-6:   VALUE (float32 LE)     │
│ Byte 7:     CHECKSUM               │
├─────────────────────────────────────┤
│ Total: 8 bytes per parameter       │
└─────────────────────────────────────┘

FX → CM4 SPI 프로토콜:
┌─────────────────────────────────────┐
│ Byte 0:     STATUS flags           │
│ Byte 1-2:   SLOT_STATE             │
│ Byte 3-6:   LEVEL_METER (float32)  │
│ Byte 7:     CHECKSUM               │
├─────────────────────────────────────┤
│ Total: 8 bytes per slot            │
└─────────────────────────────────────┘
```

### 3-4. DMA 전송 모드

- **DMA2**가 SPI TX/RX 버퍼를 DMA로 전송
- `FUN_08005a68/08005a8c/08005a44` — DMA 완료 상태 레지스터 폴링 (shift + mask 패턴)
- BDMA는 저전력 도메인에서 백그라운드 전송

### 3-5. 클럭 설정

- `FUN_08005c00`에서 계산한 SPI 클럭:
  - Mode 0: prescaler 0 → APB2/2 (최대 100MHz)
  - Mode 1: prescaler 1 → APB2/4
  - Mode 2: prescaler 2 → APB2/8
  - Mode 3: prescaler 3 → APB2/16

### 3-6. 함수 포인터 테이블

데이터 테이블에서 발견된 4개 함수 포인터:
| 주소 | 추정 기능 |
|------|----------|
| `0x0801b2f8` | SPI TX 핸들러 |
| `0x0801b321` | SPI RX 핸들러 |
| `0x0801b327` | DMA 완료 콜백 |
| `0x0801b32e` | 에러 핸들러 |

---

## 4. 종합 아키텍처

```
┌─────────────────────────────────────────────────┐
│                    CM4 (Main MCU)                │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ MIDI RX  │  │ Preset   │  │ UI Display    │  │
│  │          │  │ Manager  │  │ Controller    │  │
│  └────┬─────┘  └────┬─────┘  └───────┬───────┘  │
│       │              │                │          │
│  ┌────▼──────────────▼────────────────▼───────┐  │
│  │        FX Command Dispatcher              │  │
│  │  UART/USART → FX type + param encoding    │  │
│  └──────────────┬────────────────────────────┘  │
└─────────────────┼───────────────────────────────┘
                  │ SPI1 (DMA) + HSEM
┌─────────────────▼───────────────────────────────┐
│                 FX Core (ARM Cortex-M)           │
│  ┌────────────────────────────────────────────┐  │
│  │         FUN_0800ca04 (Init Router)         │  │
│  │  Slot A (0x000) | Slot B (0x248) | Slot C │  │
│  └────┬────┬────┬────┬────┬────┬────┬────────┘  │
│  │  SP0│SP1 │SP2 │SP3 │SP4 │SP5 │SP6          │
│  │Comp│DlyA│DlyB│Rev │VcCh│VcBd│Multi        │
│  │48B │148B│148B│224B│336B│243B│236B         │
│  └────┴────┴────┴────┴────┴────┴─────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │     SP6 내부 하위 프로세서 (Multi-FX)       │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌─────┐ ┌───┐ │  │
│  │  │EQ3   │ │Filter│ │WavShp│ │Mod  │ │DSP│ │  │
│  │  │9b98  │ │9e88  │ │a134  │ │a408 │ │82f0│ │  │
│  │  └──────┘ └──────┘ └──────┘ └─────┘ └───┘ │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Audio: SAI2 I2S ← DMA1 ← Float32 48kHz         │
│  Control: SPI1 ← DMA2 ← CM4                     │
│  Sync: HSEM (hardware semaphore)                 │
└──────────────────────────────────────────────────┘
```

---

## 5. 미해결 / 추가 조사 필요

1. **SP1 vs SP2 정확한 구분**: 두 함수가 구조가 거의 동일 — Delay subtype A/B인지, 아니면 다른 FX 타입(Chorus/Flanger)인지 확인 필요
2. **SPI 프로토콜 프레임 포맷**: 현재 추정만 — 실제 바이트 레벨 프로토콜은 레지스터 덤프나 로직 분석으로 확정 필요
3. **FUN_0800ca04의 type selector**: FX 타입 선택 로직 (switch/case)을 아직 찾지 못함 — SP0~SP6를 어떤 조건으로 선택하는지
4. **USART vs UART**: 이전 분석(USART3)과 이번 분석(USART1) 불일치 — 두 개 다 사용 중이거나, 하나가 오디오 커맨드, 하나가 시스템 커맨드
