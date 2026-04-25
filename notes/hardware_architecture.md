# MiniFreak Hardware Architecture (Firmware-Inferred)

> 펌웨어 바이너리 분석으로 역설계한 하드웨어 아키텍처.  
> 분석 대상: fw4.0.1 (CM4 620KB, CM7 524KB, FX 122KB, UI×4)

## 1. 메인 MCU

| 항목 | 값 | 근거 |
|------|-----|------|
| 칩 | **STM32H745** (또는 H747) | 벡터테이블, HAL 함수 패턴, Cortex-M7/M4 분리 |
| 코어 | CM7 + CM4 듀얼코어 | 바이너리 2개 분리, HSEM 동기화 |
| CM7 역할 | 오디오 DSP 전용 | 페리페럴 접근 없음 (GPIO/TIM/HSEM만), 순수 연산 |
| CM4 역할 | 페리페럴 관리자 | DAC1, ADC1/2, SAI2, I2C1, TIM1, DMA1, GPIO×8 |
| 통신 | HSEM + AXI SRAM 공유 | HSEM 35refs, AXI_SRAM 6refs |

## 2. 페리페럴 사용 맵 (CM4 기준)

### 오디오 인터페이스
| 페리페럴 | 주소 | 참조 | 용도 |
|----------|------|------|------|
| **DAC1** | 0x40007400 | 2 | 아날로그 출력 (VCF cutoff/resonance, VCA, envelope) |
| **ADC1** | 0x40022000 | 5 | 아날로그 입력 (포텐시오미터 스캔) |
| **ADC2** | 0x40022100 | 5 | 아날로그 입력 (센서 체인) |
| **SAI2** | 0x40015800 | 1 | 오디오 시리얼 I2S (→ 외부 audio codec) |
| **I2C1** | 0x40005400 | 2 | I2C 버스 (디스플레이 제어 or codec config) |
| **DMA1** | 0x40020000 | 6 | SAI2 오디오 DMA 전송 |

### 타이머/클럭
| 페리페럴 | 참조 | 용도 |
|----------|------|------|
| **TIM1** | 28 | PWM/클럭 생성 (가장 많이 사용) |
| TIM2 | 5 | 보조 타이머 |
| TIM3 | 5 | 보조 타이머 |
| TIM4 | 3 | 보조 타이머 |

### 시리얼 통신
| 페리페럴 | 참조 | 용도 |
|----------|------|------|
| USART1 | 3 | MIDI IN/OUT? |
| USART2 | 3 | CM4↔FX 통신 |
| USART3 | 3 | CM4↔FX 통신 |

### 미사용 (CM4에서)
DAC2, SAI1, SPI1, SPI2, SPI3, I2C2, I2C3, ADC3, DMA2, UART4, UART5, TIM6, TIM7

## 3. 코어별 페리페럴 분담

```
CM4 (Periph Manager)          CM7 (Audio DSP)          FX Core
┌─────────────────────┐      ┌──────────────────┐      ┌────────────────┐
│ DAC1 (아날로그 출력) │      │ DTCM (local)      │      │ DAC1 (2 refs)  │
│ ADC1/2 (아날로그 입력)│      │ AXI SRAM (공유)    │      │ SAI2 (1 ref)   │
│ SAI2 (I2S → codec)  │◄────►│ TIM1 (35 refs)     │      │ ADC1/2 (각 1)  │
│ I2C1 (디스플레이)    │      │ GPIO (10 refs)     │      │ GPIO (다수)     │
│ TIM1 (28 refs)       │      │ HSEM (1 ref)       │      │                │
│ DMA1 (SAI2 전송)     │      │                    │      │                │
│ USART1/2/3           │      │ (페리페럴 접근 없음) │      │                │
│ GPIO × 8개 포트       │      │                    │      │                │
│ HSEM (35 refs)       │      └──────────────────┘      └────────────────┘
└─────────────────────┘
```

## 4. 아날로그 제어 아키텍처

### 발견된 클래스
- **`CvCalib`** — 아날로그 CV 캘리브레이션 관리자
  - `eCvKind` enum — CV 타입 (어떤 아날로그 파라미터인지)
  - `eVcfType` enum — VCF 타입별 다른 캘리브레이션
  - `getCalibCutValue()` — 컷오프 캘리브레이션값
  - `getCalibVcaClickValue()` — VCA 클릭 노이즈 캘리브레이션
  - `getCvCalibrated()` — 캘리브레이션 적용된 CV 값 반환 (15개 함수에서 29회 호출)

### 아날로그 제어 체인
```
프리셋 파라미터 → CvCalib::getCvCalibrated(eCvKind, voice, value)
                  → 보정값 계산
                  → 0x118 바이트 Voice Struct에 기록
                  → AXI SRAM을 통해 CM7 전달
                  → CM7이 오디오 스트림에 적용
                  → DAC1 → 아날로그 출력
```

### Voice Struct (0x118 = 280 bytes per voice)
```
offset 0x118: param_4=0 → primary CV value (uint16)
offset 0x11A: param_4=1 → secondary CV value (uint16)
offset 0x11C: param_2=1, param_4=0 → voice 1 primary
offset 0x11E: param_2=1, param_4=1 → voice 1 secondary
```

## 5. 오디오 입출력 체인

### 출력 체인 (확정)
```
CM7 DSP ──(AXI SRAM)──► CM4 ──(SAI2/I2S)──► [Audio Codec] ──► 아날로그 출력
                                   48kHz
                                   DMA1 전송
```

### 입력 체인 (확정)
```
[포텐시오미터 30개] ──(ADC1/2)──► CM4 ──(AdcScan<N>)──► 파라미터 값
[커패시티브 터치]  ──(ADC1/2)──► CM4 ──(SensorChainCalib)──► 터치 이벤트
[리본 센서 ×2]    ──(ADC1/2)──► CM4 ──(AdcScan<11>)──► 리본 값
[키베이드 애프터터치] ──(ADC?)──► CM4 ──(AdcScan<6>)──► 애프터터치
```

### Audio Codec
- **펌웨어에 칩명 문자열 없음** — HAL 레벨에서만 접근
- SAI2 사용 → I2S 프로토콜
- 후보: CS43L22 (STM32F4 eval board 표준), AK4376 (I2C addr 0x10 근처 hit)
- **확정 불가** — 물리 보드 확인 필요

### FX 코어
- 자체 DAC1 + SAI2 + ADC1/2 사용 → **FX 전용 아날로그 입출력**
- SPI1/2/3 사용 → FX DSP 칩 통신 가능성 (하지만 CM4에서는 SPI 미사용)
- CM4와 UART3 + SPI로 통신

## 6. UI 서브시스템

| 모듈 | 크기 | MCU | 페리페럴 | 기능 |
|------|------|-----|---------|------|
| ui_screen | 173KB | 전용 MCU | ADC1/2, SPI1 | OLED 디스플레이 |
| ui_ribbon | 69KB | 전용 MCU | ADC1/2, SPI1, SAI2, I2C1 | 터치 리본 |
| ui_matrix | 69KB | 전용 MCU | ADC1/2, SPI1, SAI2, I2C2 | 버튼 매트릭스 |
| ui_kbd | 42KB | 전용 MCU | ADC1/2, SAI2 | 키베이드 |

- 각 UI MCU가 **독립 ADC + SPI** 보유 → 자체 센서 스캐닝
- `AdcScan<N>` 템플릿으로 센서 읽기 (N = 채널 수)
- `HysteresisFilter<4095, 32, 1000>` — 12-bit ADC 노이즈 필터
- `SMAFilter<3>`, `MedianFilter` — 추가 필터링
- `PWM<7, 5, 7>` — LED PWM 제어

## 7. 확정 아키텍처 다이어그램

```
┌──────────────────────────────────────────────────────────────────┐
│                    Arturia MiniFreak Hardware                     │
│                    (firmware-inferred v1.0)                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐        │
│  │              STM32H745 (Main MCU)                     │        │
│  │                                                       │        │
│  │  ┌────────────────────┐    ┌─────────────────────┐   │        │
│  │  │  CM7 (Cortex-M7)   │    │  CM4 (Cortex-M4)    │   │        │
│  │  │  512KB, DSP 전용    │    │  608KB, 페리 관리    │   │        │
│  │  │                    │    │                      │   │        │
│  │  │  • Plaits 오실레이터│    │  • DAC1 (아날로그)   │   │        │
│  │  │  • VCF/VCA DSP      │    │  • ADC1/2 (센서)    │   │        │
│  │  │  • Envelope/LFO     │    │  • SAI2 (I2S out)   │   │        │
│  │  │  • Voice alloc      │    │  • I2C1 (디스플레이) │   │        │
│  │  │  • NEON SIMD        │    │  • TIM1 (PWM/클럭)  │   │        │
│  │  │  • Float32 DSP       │    │  • DMA1 (SAI2)     │   │        │
│  │  │                    │    │  • USART1/2/3       │   │        │
│  │  │  페리페럴: 없음     │    │  • CvCalib 클래스   │   │        │
│  │  │  메모리: DTCM+AXI   │    │  • GPIO A~H        │   │        │
│  │  └────────┬────────────┘    └────────┬─────────────┘   │        │
│  │           │  HSEM + AXI SRAM       │                  │        │
│  │           └────────────────────────┘                  │        │
│  └──────────────────────────────────────────────────────┘        │
│                            │                                      │
│              ┌─────────────┼─────────────┐                        │
│              │ SAI2/I2S    │ USART2/3    │ I2C1                   │
│              ▼             │ UART        │                        │
│    ┌──────────────┐        ▼             ▼                        │
│    │ Audio Codec  │  ┌──────────┐  ┌──────────┐                  │
│    │ (미확정)     │  │ FX Core  │  │ UI MCU×4 │                  │
│    │ SAI2, 48kHz  │  │ DAC1     │  │ Screen   │                  │
│    │ 16/24-bit    │  │ SAI2     │  │ Ribbon   │                  │
│    │              │  │ ADC1/2   │  │ Matrix   │                  │
│    └──────┬───────┘  │ SPI×3    │  │ Keyboard │                  │
│           │          └──────────┘  └──────────┘                  │
│           ▼                                                        │
│    ┌──────────────┐         ┌──────────────┐                      │
│    │ 아날로그 출력 │         │ 아날로그 입력 │                      │
│    │ L/R OUT      │         │ 30 Knobs     │                      │
│    │ HP OUT       │         │ 2 Ribbons    │                      │
│    │              │         │ 37 Keys+AT   │                      │
│    └──────────────┘         │ 30 Touch Btn │                      │
│                             └──────────────┘                      │
│                                                                  │
│  전원: DC 12V / 1A                                                │
└──────────────────────────────────────────────────────────────────┘
```

## 8. 미확인 사항 (물리 분석 필요)

| 항목 | 현재 상태 | 확인 방법 |
|------|----------|----------|
| Audio Codec 칩 | 미확정 | 보드 사진에서 SAI2 I2S 트레이스 추적 |
| 아날로그 VCF 회로 | SEM 스타일 (메뉴얼) | OP-AMP/커패시터 실제 회로 확인 |
| VCA 회로 | 미확정 | THAT 칩 or discrete |
| 전원 회로 | 12V→5V→3.3V | LDO/DC-DC 컨버터 확인 |
| FX 코어 MCU | 별도 칩 (확정) | 파트넘버 확인 필요 |
| UI MCU ×4 | 각각 전용 MCU | 파트넘버 확인 필요 |
| 헤드폰 amp | 미확정 | 출력단 회로 확인 |
