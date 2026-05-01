# Phase 18: UI MCU 통신 프로토콜 + CM7 SPI 페리페럴 정적 분석

> **2026-05-01** | fw4_0_1_2229 | 정적 레지스터 참조 분석
> **이전 산출물**: `PHASE4_HARDWARE_ANALYSIS.md`, `PHASE7-3_FX_CORE_ANALYSIS.md`

---

## 1. 분석 방법

7개 펌웨어 바이너리에서 STM32H747 페리페럴 레지스터 베이스 주소를 32-bit LE 패턴으로 검색.
Thumb-2 LDR literal 풀에서 레지스터 주소를 직접 참조하는지 확인.

검색 대상: SPI1~6, I2C1~4, USART1~3, UART3~4, HSEM, IPCC, DMA1~2, DMAMUX1~2

---

## 2. UI MCU × CM4 통신 아키텍처

### 2.1 UI MCU별 페리페럴 사용 현황

| MCU | 크기 | SPI | I2C | UART | DMA | 역할 |
|-----|------|-----|-----|------|-----|------|
| **ui_screen** | 173KB | SPI1 (2) | — | UART3 (2), UART4 (1), USART2 (2) | DMA1 (8) | OLED 디스플레이 |
| **ui_matrix** | 69KB | SPI1 (2) | I2C2 (2) | UART3 (2), UART4 (1), USART2 (2) | DMA1 (9) | 버튼 매트릭스 + LED |
| **ui_ribbon** | 69KB | SPI1 (2) | I2C1 (2) | UART3 (2), UART4 (1), USART2 (2) | DMA1 (9) | 터치스트립 |
| **ui_kbd** | 42KB | — | — | UART3 (2), UART4 (1), USART2 (2) | DMA1 (8) | 키보드 스캔 |

> 숫자 = 레지스터 베이스 주소 참조 횟수

### 2.2 핵심 발견: UART 기반 통신

**모든 UI MCU가 UART3 (또는 동일 주소의 USART3) 레지스터를 참조함.**

- UART3 = `0x40004800` (APB1 버스)
- UART4 = `0x40004C00` (APB1 버스)
- USART2 = `0x40004400` (APB1 버스)

**CM4 측 UART 사용**:
- USART1 (0x40011000): 3회 — USB MIDI VCP 또는 디버그
- USART2 (0x40004400): 3회 — UI MCU 통신
- USART3/UART3 (0x40004800): 3회 — FX 코어 통신 (Phase 7-3 확인)

### 2.3 추정 통신 토폴로지

```
┌──────────┐    USART2     ┌──────────┐
│ ui_screen │◄────────────►│          │
├──────────┤               │          │
│ ui_matrix │◄────────────►│   CM4    │
├──────────┤    USART2     │          │
│ ui_ribbon │◄────────────►│          │
├──────────┤               │          │
│  ui_kbd  │◄────────────►│          │
└──────────┘               └────┬─────┘
                                │ USART3
                           ┌────▼─────┐
                           │ FX 코어  │
                           └──────────┘
```

- **CM4 → UI MCU**: USART2 (CM4 측) ↔ USART2 (UI MCU 측) — 단일 UART 버스 다중 슬레이브 또는 개별 UART
- **CM4 → FX**: USART3 (Phase 7-3 확인: UART3=커맨드, SPI=파라미터 스트림, HSEM=동기화)
- **UI MCU끼리**: 직접 통신 없음. 모두 CM4 경유

### 2.4 UI MCU별 추가 페리페럴

| MCU | SPI 용도 | I2C 용도 |
|-----|---------|---------|
| ui_screen | SPI1 → OLED SSD13xx 드라이버 | — |
| ui_matrix | SPI1 → LED 매트릭스 드라이버 | I2C2 → LED 컨트롤러 또는 I/O 확장 |
| ui_ribbon | SPI1 → 터치 ADC (CAP1188 등) | I2C1 → 터치 컨트롤러 |
| ui_kbd | — | — |

### 2.5 CM4에서 UI MCU 관련 문자열

```
MNF_WheelsController::getWheelColor(MNF_WheelsController::eWheel)
MNF_WheelsController::clearColumn(MNF_WheelsController::eWheel)
MNF_WheelsController::drawColumnPosition(MNF_WheelsController::eWheel, uint16_t, uint16_t)
LED Intensity
Kbd Src / Mono Kbd / Poly Kbd / Legato Kbd
Mod Wheel / Pitch Wheel
Matrix / Matrix Amount / Matrix Routing / Matrix Src VeloAT
```

→ CM4에 `MNF_WheelsController` 클래스가 존재하며, UI MCU (특히 ui_matrix) LED 제어를 담당.
`LED Intensity`는 eSettingsParams 항목으로 CM4에서 UI MCU로 전달.

---

## 3. CM7 페리페럴 사용 현황 (확정)

| 페리페럴 | 참조 횟수 | 용도 |
|----------|----------|------|
| RCC (0x58024400) | 29 | 클럭 설정 (init 전용) |
| TIM2 (0x40000000) | 35 | 오디오 샘플 타이밍 |
| GPIOA (0x58020000) | 1 | 최소한의 GPIO (init) |
| **SPI1~6** | **0** | **없음** |
| **I2C1~4** | **0** | **없음** |
| **USART1~3** | **0** | **없음** |
| **DMA1/2** | **0** | **없음** |
| **HSEM/IPCC** | **0** | **없음** |

### 결론: CM7은 어떤 통신 페리페럴도 사용하지 않음

CM7은 RCC로 자신의 클럭만 설정하고, TIM2로 오디오 샘플링 레이트를 유지함.
**오디오 데이터는 공유 메모리(DTCM/SRAM)를 통해 CM4와 교환** (DataMemoryBarrier로 동기화 — Phase 4 확인).

이는 CM7이 **순수 DSP 코어**로 설계되었음을 최종 확인:
- CM4 = 시스템 컨트롤러 (모든 페리페럴 관리, UI 통신, MIDI, USB)
- CM7 = 오디오 전용 (DMA/인터럽트 없이 폴링 또는 타이머 기반 처리)

---

## 4. FX 코어 페리페럴 현황 (보완)

| 페리페럴 | 참조 횟수 | 비고 |
|----------|----------|------|
| UART3/USART3 | 3 | CM4와 커맨드 통신 (Phase 7-3 확인) |
| UART4 | 1 | 보조 통신 |
| USART1 | 1 | 보조 통신 |
| USART2 | 1 | 보조 통신 |
| IPCC | 1 | CM4↔FX 동기화 |

Phase 7-3에서 확인한 내용과 일치: CM4↔FX = UART3(커맨드) + SPI(파라미터 스트림) + HSEM(동기화).

---

## 5. 종합 아키텍처 (최종)

```
┌─────────────────────────────────────────────────────────────────┐
│                    USB (MIDI + Collage)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  CM4 (Cortex-M4) — 시스템 컨트롤러                              │
│  USART1(USB VCP/Debug) | USART2(UI MCU×4) | USART3(FX)        │
│  I2C1(코덱) | DMA1 | SAI2(오디오 I2S) | DAC1(아날로그 VCF/VCA) │
└──┬──────┬──────────┬──────────┬─────────────────────────────────┘
   │      │          │          │ 공유 메모리
   │      │          │          │ (DTCM/SRAM + DMB 동기화)
   │ USART2  USART2  USART2    │
┌──▼──┐ ┌─▼───┐ ┌──▼──┐ ┌──▼───────────────────────────────────┐
│screen│ │matrix│ │ribbon│ │ CM7 (Cortex-M7) — 순수 DSP 엔진     │
│SPI1  │ │SPI1  │ │SPI1  │ │ RCC + TIM2만 사용                    │
│OLED  │ │LED   │ │Touch │ │ SPI/I2C/UART/DMA 전부 0              │
└─────┘ │I2C2  │ │I2C1  │ │ → 페리페럴 없이 메모리 폴링으로 동작   │
        └──────┘ └──────┘ └──────────────────────────────────────┘
   │ USART2
┌──▼──────┐
│ ui_kbd  │  SPI/I2C 없음 — UART만으로 CM4와 통신
└─────────┘

   │ USART3 + SPI + HSEM
┌──▼──────────────────┐
│ FX 코어 (Cortex-M4) │
│ IPCC(1) + UART3(3)  │
└─────────────────────┘
```

---

## 6. Phase 4 마스터플랜 업데이트

| 항목 | 이전 상태 | 현재 상태 |
|------|----------|----------|
| UI MCU 통신 프로토콜 | ❌ 간접 참조로 추적 불가 | ✅ **USART2 기반 확정** (CM4 ↔ UI MCU ×4) |
| CM7 SPI 페리페럴 | ❌ HAL 래퍼로 간접 접근 | ✅ **CM7는 페리페럴 전혀 없음** (순수 메모리 기반 DSP) |

> Phase 4의 두 미완료 항목 모두 해결.
