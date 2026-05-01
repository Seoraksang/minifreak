# MiniFreak Phase 9-6: 아날로그 VCF/VCA SPI 제어 코드 정적 분석

**분석 일자:** 2026-05-01
**분석 대상:** CM4 펌웨어 `minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin` (620,224 bytes)
**기준 주소:** 0x08120000 (CM4 펌웨어 베이스)

---

## 1. 핵심 발견 요약

| 항목 | 발견 내용 |
|------|----------|
| **DAC 칩** | STM32H747 내장 DAC1 (0x40007400) 사용 — 외부 DAC 칩 없음 |
| **SPI** | SPI 레지스터 주소 전무 — VCF/VCA 제어에 SPI 미사용 |
| **제어 방식** | DAC1 + ADC1 직접 레지스터 접근 (bare-metal, HAL 미사용) |
| **I2C** | I2C1 (0x40005400) 존재 — 코덱 제어용으로 추정 |
| **TIM2** | TIM2 (0x40000000) 28회 참조 — PWM 기반 CV 출력 가능성 |
| **ADC** | ADC1 (0x40022000) 5회 참조 — Pot/Sensor 스캐닝 (AdcScan\<7\>) |

---

## 2. CvCalib 클래스 완전 구조

### 2.1 클래스 메서드 (RTTI 기반, 11개)

| 메서드 | Ghidra 주소 | 시그니처 |
|--------|------------|----------|
| `setCalibVcaClickValue` | `0x081ac2e5` | `void CvCalib::setCalibVcaClickValue(eVcfType, uint8_t, bool, uint16_t)` |
| `setCalibrated` | `0x081ac341` | `void CvCalib::setCalibrated(eCvKind, uint8_t, bool, bool)` |
| `setCalibCutValue` | `0x081ac37d` | `void CvCalib::setCalibCutValue(int8_t, int16_t, uint16_t)` |
| `setCalibMaxValue` | `0x081ac3dd` | `void CvCalib::setCalibMaxValue(eCvKind, uint8_t, uint16_t)` |
| `setCalibMinValue` | `0x081ac419` | `void CvCalib::setCalibMinValue(eCvKind, uint8_t, uint16_t)` |
| `getCalibMinValue` | `0x081ac459` | `uint16_t CvCalib::getCalibMinValue(eCvKind, uint8_t)` |
| `getCalibMaxValue` | `0x081ac491` | `uint16_t CvCalib::getCalibMaxValue(eCvKind, uint8_t)` |
| `getCalibVcaClickValue` | `0x081ac4c9` | `uint16_t CvCalib::getCalibVcaClickValue(eVcfType, uint8_t, bool)` |
| `getCalibCutValue` | `0x081ac50d` | `uint16_t CvCalib::getCalibCutValue(int8_t, int16_t)` |
| `getCalibrated` | `0x081ac53d` | `bool CvCalib::getCalibrated(eCvKind, uint8_t)` |
| `getCvCalibrated` | `0x081ac571` | `uint16_t CvCalib::getCvCalibrated(eCvKind, uint8_t, uint16_t)` |

### 2.2 Enum 타입

**eCvKind** — CV 종류 (캘리브레이션 그룹):
- `setCalibMinValue(eCvKind, uint8_t, uint16_t)` — min/max 저장
- `getCalibMinValue(eCvKind, uint8_t)` — min/max 조회
- `getCalibrated(eCvKind, uint8_t)` — 캘리브레이션 완료 여부
- `getCvCalibrated(eCvKind, uint8_t, uint16_t)` — 보정된 CV 값 조회
- `setCalibrated(eCvKind, uint8_t, bool, bool)` — 캘리브레이션 상태 설정

**eVcfType** — VCF 타입 (필터 종류):
- `setCalibVcaClickValue(eVcfType, uint8_t, bool, uint16_t)` — VCA 클릭 캘리브레이션
- `getCalibVcaClickValue(eVcfType, uint8_t, bool)` — VCA 클릭값 조회

### 2.3 에러/검증 문자열 (바운드 체크)

| 문자열 | Ghidra 주소 | 의미 |
|--------|------------|------|
| `"Invalid CV group"` | `0x081ac328` | eCvKind 값 범위 초과 |
| `"Invalid CV idx"` | `0x081ac3b4` | uint8_t idx 파라미터 범위 초과 |
| `"Invalid CV point"` | `0x081ac3c4` | 캘리브레이션 포인트 (min/max) 범위 초과 |

### 2.4 CvCalib 데이터 구조 추론

```
CvCalib {
    // eCvKind별 데이터 (그룹 x 인덱스)
    uint16_t min_values[MAX_KIND][MAX_IDX];    // get/setCalibMinValue
    uint16_t max_values[MAX_KIND][MAX_IDX];    // get/setCalibMaxValue
    bool     calibrated[MAX_KIND][MAX_IDX];    // get/setCalibrated

    // Cutoff 캘리브레이션 (int8_t = voice_idx, int16_t = note/point)
    uint16_t cut_values[VOICE_COUNT][CAL_POINTS];  // get/setCalibCutValue

    // VCA 클릭 캘리브레이션 (eVcfType별)
    uint16_t vca_click_values[VCF_TYPE_COUNT][MAX_IDX][2];  // get/setCalibVcaClickValue

    // 메인 보정 함수
    uint16_t getCvCalibrated(eCvKind, idx, raw_value);  // min-max 선형 보간
}
```

---

## 3. 캘리브레이션 파라미터 메뉴

UI 메뉴에서 노출되는 캘리브레이션 항목들 (Ghidra 주소 `0x081af` 영역):

| 파라미터 | Ghidra 주소 | 설명 |
|----------|------------|------|
| `"Calib Analog"` | `0x081af298` | 아날로그 섹션 캘리브레이션 진입점 |
| `"Resonance min"` | `0x081af2a8` | VCF Resonance 최소값 |
| `"Resonance max"` | `0x081af2b8` | VCF Resonance 최대값 |
| `"Calib Cutoff"` | `0x081af2c8` | VCF Cutoff 캘리브레이션 |
| `"VCA min"` | `0x081af2d8` | VCA 게인 최소값 |
| `"VCA max"` | `0x081af2e0` | VCA 게인 최대값 |
| `"VCA offset"` | `0x081af2e8` | VCA DC 오프셋 |
| `"VCA_Offset_Reset"` | `0x081af2f4` | VCA 오프셋 리셋 명령 |

### 관련 UI 파라미터

| 파라미터 | Ghidra 주소 | 설명 |
|----------|------------|------|
| `"Cutoff"` | `0x081aec98` | 메인 VCF Cutoff 노브 |
| `"Resonance"` | `0x081af7d8` | 메인 Resonance 노브 (줄여서 "Reso") |
| `"Velo > VCA"` | `0x081af81c` | 벨로시티 → VCA 라우팅 |
| `"Velo > VCF"` | `0x081afa20` | 벨로시티 → VCF 라우팅 |
| `"Envelope > Cutoff"` | `0x081aeebc` | 엔벨로프 → Cutoff 라우팅 |
| `"Velo > Env Amnt"` | `0x081aeed4` | 벨로시티 → 엔벨로프 양 |

---

## 4. DAC/SPI 제어 방식

### 4.1 DAC1 레지스터 접근

**결정적 발견:** DAC1 베이스 주소 `0x40007400`가 CM4 펌웨어에서 2회 참조됨.

| 참조 위치 | 파일 오프셋 | Ghidra 주소 | 컨텍스트 |
|----------|-----------|------------|----------|
| 참조 1 | `0x15F4` | `0x081215F4` | DAC 데이터 쓰기 함수 (literal pool) |
| 참조 2 | `0x169C` | `0x0812169C` | DAC 초기화 함수 (literal pool) |

**참조 1 상세 (DAC 쓰기 함수):**
```
Literal pool at 0x081215F4:
  0x081215F0: 0x10012784    (RAM 데이터)
  0x081215F4: 0x40007400    ← DAC1_CR 레지스터
  0x081215F8: 코드 시작 (PUSH {r6, lr})
```
- 함수 시작 추정: `0x08121591` (PUSH 명령어)
- DAC1_CR 레지스터에 직접 접근하여 비트 설정/클리어

**참조 2 상세 (DAC 초기화 함수):**
```
Literal pool at 0x0812169C:
  0x0812169C: 0x40007400    ← DAC1_CR
  0x081216A0: 0x58024400    ← RCC 레지스터
  0x081216A4: 0x1001270C    (RAM 데이터)
  0x081216A8: 0x58020000    ← GPIOA 레지스터
```
- DAC 초기화 시 RCC 클럭 인에이블 + GPIOA 핀 설정 동시 수행
- 함수 시작 추정: `0x081215F9`

### 4.2 SPI 미사용 확인

**SPI 레지스터 주소 검색 결과:** SPI1~SPI6 모든 베이스 주소가 CM4 펌웨어에서 **0회** 참조됨.

| 주소 | 칩 | 참조 횟수 |
|------|-----|---------|
| `0x40013000` | SPI1 | 0 |
| `0x40003800` | SPI2 | 0 |
| `0x40003C00` | SPI3 | 0 |
| `0x40013400` | SPI4 | 0 |
| `0x40015000` | SPI5 | 0 |
| `0x58001400` | SPI6 | 0 |

> **결론:** MiniFreak의 VCF/VCA 아날로그 제어는 SPI 기반 외부 DAC 칩이 아닌, STM32H747 내장 DAC1을 직접 사용합니다. 이는 하드웨어 비용 절감 설계입니다.

### 4.3 HAL 라이브러리 미사용

`HAL_SPI_*`, `HAL_DAC_*` 등 STM32 HAL 문자열이 펌웨어에서 전혀 발견되지 않음. 모든 페리페럴 접근이 레지스터 직접 읽기/쓰기 (bare-metal)로 구현됨.

---

## 5. ADC/Pot 스캐닝 시스템

### 5.1 ADC1 레지스터 사용

ADC1 베이스 `0x40022000`이 5회 참조됨 (ISR 레지스터 = 베이스):

| 파일 오프셋 | Ghidra 주소 | 용도 추정 |
|-----------|------------|----------|
| `0x3D98` | `0x08123D98` | ADC 변환 완료 대기 |
| `0x3EF8` | `0x08123EF8` | ADC ISR 상태 체크 |
| `0x4008` | `0x08124008` | ADC 시작/폴링 |
| `0x4200` | `0x08124200` | ADC 결과 읽기 |
| `0x4430` | `0x08124430` | ADC 초기화 |

### 5.2 관련 클래스 (RTTI)

| 클래스 | Ghidra 주소 | 설명 |
|--------|------------|------|
| `AdcScan<7>` | `0x081a9e4c` | 7채널 ADC 스캐너 (템플릿) |
| `PotChainCalib` | `0x081a9de4` | 포텐시오미터 체인 캘리브레이션 |
| `SensorChainCalib` | `0x081a9e20` | 센서 체인 캘리브레이션 |
| `SensorComp` | `0x081a9df4` | 센서 보상 |
| `ContinuousSwitchChain` | `0x081a9e34` | 연속 스위치 체인 |
| `MedianFilter` | `0x081a9da0` | 중간값 필터 (노이즈 제거) |
| `SMAFilter<3>` | `0x081a9dd4` | 3샘플 이동평균 필터 |
| `SMAFilter<4>` | `0x081a9e10` | 4샘플 이동평균 필터 |
| `IIR_LP<14, 2>` | `0x081a9db4` | 14차 IIR 로우패스 필터 |
| `IIR_LP<7, 1>` | `0x081a9dc4` | 7차 IIR 로우패스 필터 |
| `IIR_LP<3, 1>` | `0x081a9e00` | 3차 IIR 로우패스 필터 |

### 5.3 UI 노브 시스템

| 문자열 | Ghidra 주소 |
|--------|------------|
| `"Knob Panel"` | `0x081b0758` |
| `"Knob Catch"` | `0x081b2248` |
| `"Knob Send CC"` | 이전 검색에서 확인 |

---

## 6. VCA Offset 코드 분석

### 6.1 VCA Offset 관련 문자열

| 문자열 | Ghidra 주소 | 설명 |
|--------|------------|------|
| `"VCA offset"` | `0x081af2e8` | VCA DC 오프셋 파라미터 이름 |
| `"VCA_Offset_Reset"` | `0x081af2f4` | VCA 오프셋 리셋 기능 |
| `"Chord Offset"` | `0x081af608` | 코드 오프셋 (VCA offset과 별개) |

### 6.2 VCA Offset 구현 추론

`CvCalib::getCalibVcaClickValue(eVcfType, uint8_t, bool)` 함수가 VCA 관련 캘리브레이션 값을 관리합니다. `bool` 파라미터는 오프셋/오프셋리셋 모드 전환으로 추정됩니다.

VCA Offset Reset은 아날로그 VCA 회로의 DC 바이어스를 영점 조정하는 기능으로, DAC1에 특정 값을 출력하여 VCA의 DC 오프셋을 보상합니다.

---

## 7. 페리페럴 참조 맵 (CM4 전체)

| 페리페럴 | 베이스 주소 | 참조 횟수 | 용도 |
|----------|-----------|---------|------|
| GPIOG | `0x58021800` | 36 | 가장 많이 사용되는 GPIO 포트 |
| RCC | `0x58024400` | 36 | 클럭 제어 |
| TIM2 | `0x40000000` | 28 | PWM CV 출력 또는 타이머 |
| GPIOD | `0x58020c00` | 14 | SAI2 GPIO |
| GPIOB | `0x58020400` | 13 | 다목적 GPIO |
| GPIOE | `0x58021000` | 9 | SAI2 GPIO |
| GPIOA | `0x58020000` | 6 | DAC 출력 핀 |
| GPIOC | `0x58020800` | 6 | 다목적 GPIO |
| DMA1 | `0x40020000` | 6 | 데이터 전송 |
| TIM3 | `0x40000400` | 5 | 타이머 |
| ADC1 | `0x40022000` | 5 | Pot/Sensor ADC |
| ADC2 | `0x40022100` | 5 | 추가 ADC 채널 |
| RCC_AHB3 | `0x58026000` | 5 | ADC 클럭 |
| DAC1 | `0x40007400` | 2 | **VCF/VCA 아날로그 출력** |
| I2C1 | `0x40005400` | 2 | 오디오 코덱 제어 |
| SAI2 | `0x40015800` | 1 | 오디오 인터페이스 |
| SAI3 | `0x40015c00` | 1 | 오디오 인터페이스 |
| SAI4 | `0x40016000` | 1 | 오디오 인터페이스 |
| SPI1~SPI6 | 다양 | **0** | 미사용 |

---

## 8. 아키텍처 결론

### 8.1 아날로그 제어 경로

```
CM4 펌웨어
  │
  ├── DAC1 (0x40007400) ──→ VCF Cutoff / VCA Gain / Resonance
  │     └── GPIOA 핀 설정 (DAC 출력 핀)
  │
  ├── ADC1 (0x40022000) ──→ Pot/Sensor 읽기 (7채널)
  │     └── AdcScan<7> + SMAFilter<3/4> + MedianFilter
  │
  ├── I2C1 (0x40005400) ──→ 오디오 코덱 제어 (추정)
  │
  └── TIM2 (0x40000000) ──→ 추가 PWM CV 출력 (가능성)
```

### 8.2 CM4-CM7 분업

- **CM4:** 모든 페리페럴 제어 (DAC, ADC, I2C, GPIO, TIM, SAI, DMA)
- **CM7:** 오디오 DSP 처리 (DAC/SPI 레지스터 직접 접근 없음, TIM2만 35회 참조)

### 8.3 핵심 설계 특징

1. **외부 DAC 없음:** STM32H747 내장 DAC1 사용 → BOM 비용 절감
2. **SPI 미사용:** VCF/VCA 제어에 SPI 통신 없이 직접 레지스터 쓰기
3. **Bare-metal:** HAL 라이브러리 없이 직접 레지스터 조작
4. **7채널 ADC 스캐닝:** Pot + 센서 체인을 AdcScan<7> 템플릿으로 관리
5. **다단 필터링:** MedianFilter → SMAFilter → IIR_LP 체인으로 ADC 노이즈 제거

---

## 9. 다음 단계 권장

1. **Ghidra에서 DAC1 함수 디컴파일** — `0x08121591` (쓰기), `0x081215F9` (초기화) 분석
2. **DAC1_DHR12R1 레지스터 추적** — 실제 Cutoff/VCA 값이 어떻게 DAC에 쓰이는지 확인
3. **ADC1 7채널 매핑** — 어떤 Pot/Sensor가 어느 채널에 연결되었는지 확인
4. **TIM2 PWM 출력 분석** — CCR4 레지스터 1회 참조 → 추가 CV 출력 채널 확인
5. **I2C1 트랜잭션 분석** — 코덱 칩 식별 및 제어 프로토콜 역공학
6. **동적 분석** — JTAG/SWD로 DAC1 출력 값 모니터링

---

*Phase 9-6 분석 완료. 다음 Phase에서는 Ghidra 디컴파일을 통한 DAC 함수 상세 분석을 진행할 것을 권장함.*
