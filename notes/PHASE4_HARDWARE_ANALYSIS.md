# MiniFreak 펌웨어 Phase 4: 하드웨어 페리페럴 분석 완료

**펌웨어 버전:** fw4.0.1.2229 (2025-06-18)
**분석 일자:** 2026-04-24
**분석 대상:** CM4, CM7, FX, UI_SCREEN, UI_MATRIX, UI_RIBBON, UI_KBD

---

## 1. 아키텍처 개요

### 1.1 코어 역할 분담 (확정)

| 코어 | 역할 | 페리페럴 접근 | 함수 수 |
|------|------|-------------|---------|
| **CM4** | 페리페럴 관리, DMA 라우팅, GPIO, 클럭, 코어간 동기화 | SAI, DMA, GPIO, RCC, HSEM, IPCC | ~수백개 |
| **CM7** | 오디오 DSP 처리 (float/NEON/FP 연산) | **간접 참조만** (직접 레지스터 접근 없음) | 295개 |
| **FX** | DSP56362 전용 오디오 FX 처리 | STM32 페리페럴 접근 없음 | 별도 바이너리 |
| **UI MCU x4** | 버튼/엔코더/리본/스크린 UI | GPIO, TIM, ADC1 (일부) | 소형 |

### 1.2 CM4 메인 초기화 시퀀스 (FUN_08121cfc, 234B)

```
FUN_08121cfc() {  // CM4 main init orchestrator
    FUN_08124600();     // DataMemoryBarrier - 코어간 동기화 시작
    FUN_08124644();     // ??? 
    FUN_08124620(4);    // ???
    FUN_081277e0();     // ???
    FUN_08123850();     // ???
    FUN_0812192c();     // ???
    FUN_081216b0();     // ???
    FUN_08121e00();     // ???
    FUN_08122010();     // ???
    FUN_08123214();     // ???
    FUN_081233a8();     // ???
    FUN_0812353c();     // ???
    FUN_081236c0();     // ???
    FUN_08122080();     // ???
    FUN_081210e0();     // ???
    FUN_08121240();     // ???
    FUN_08121b40();     // ???
    FUN_08121e24();     // ???
    FUN_081226f8();     // ???
    FUN_08122cc8();     // ???
    FUN_08122da4();     // ???
    FUN_08122e98();     // ???
    FUN_08122f8c();     // ???
    FUN_081230a4();     // ???
    FUN_08122840();     // ???
    FUN_08121590();     // ???
    FUN_081220f4();     // ★ SAI 오디오 init (48kHz)
    FUN_08123150();     // ???
    FUN_081228b8();     // ???
    FUN_08121c4c();     // ???
    FUN_081a1558();     // ???
    do { FUN_081a1650(); } while(true);  // ★ CM4 메인 루프
}
```

---

## 2. 오디오 하드웨어 경로

### 2.1 SAI (Serial Audio Interface)

| 인스턴스 | 베이스 주소 | ChA | ChB | 상태 |
|----------|-----------|-----|-----|------|
| **SAI2** | 0x40015800 | 0x40015804 | 0x40015824 | ✅ 확정 |
| **SAI3?** | 0x40015C00 | 0x40015C04 | 0x40015C24 | ⚠️ H745 예약 영역 |
| **SAI4?** | 0x40016000 | 0x40016004 | ??? | ⚠️ H745 예약 영역 |
| **SAI1 alias** | 0x58005400 | 0x58005404 | ??? | ⚠️ D3 도메인 alias |

> **참고:** 0x40015C00/0x40016000은 STM32H745에서 예약된 영역이나, H747에서는 SAI3로 존재. 펌웨어가 H747 호환으로 컴파일되었을 가능성.

### 2.2 DMA 채널 (오디오 데이터 전송)

| DMA 스트림 | 베이스 주소 | 용도 추정 | 설정값 |
|-----------|-----------|----------|--------|
| **DMA2 Stream0** | 0x40020410 | SAI2 ChA RX/TX | priority=0x57, dir=0x40 |
| **DMA2 Stream4** | 0x40020470 | SAI2 ChB 또는 추가 | priority=0x59, dir=0x40 |
| **DMA2 Stream7** | 0x400204B8 | 모니터링 또는 제어 | priority=0x5a, dir=0x00 |

### 2.3 GPIO 핀 맵핑

**SAI2 Block A — GPIOE (AF6):**
| 핀 | AF | 기능 | 레지스터 설정 |
|----|-----|------|------------|
| PE4 | AF6 | SAI2_MCLK_A | mode=2, speed=0, pull=0 |
| PE5 | AF6 | SAI2_SCK_A | mode=2, speed=0, pull=1 |
| PE6 | AF6 | SAI2_SD_A | mode=2, speed=0, pull=1 |

**SAI2 Block B / 추가 — GPIOD (AF10):**
| 핀 | AF | 기능 | 레지스터 설정 |
|----|-----|------|------------|
| PD1 | AF10 | SAI2_SD_A (alt?) | mode=2, speed=0, pull=0 |
| PD11 | AF10 | SAI2_SD_B | mode=2, speed=0, pull=0 |
| PD12 | AF10 | SAI2_FS_B | mode=2, speed=0, pull=0 |
| PD13 | AF10 | SAI2_SCK_B | mode=2, speed=0, pull=0 |

**추가 GPIO — GPIOD (AF6):**
| 핀 | AF | 기능 |
|----|-----|------|
| PD0 | AF6 | ??? |
| PD4 | AF6 | ??? |

### 2.4 샘플레이트

- **기본 샘플레이트: 48,000 Hz** (FUN_081220f4에서 `puVar1[8] = 48000` 설정)
- SAI 클럭 디바이더: FUN_08129144, FUN_08128fec에서 FP 연산으로 계산
- 클럭 소스: RCC D3 도메인 (DAT_081296e4 = 0x58024400)에서 상태 확인

---

## 3. 핵심 함수 매핑

### 3.1 CM4 오디오 관련

| 함수 | 크기 | 역할 |
|------|------|------|
| `FUN_08121cfc` | 234B | CM4 메인 init 오케스트레이터 (30개 init 호출 + 메인 루프) |
| `FUN_081220f4` | 94B | SAI config 설정 — 48kHz, 호출자로 SAI init 트리거 |
| `FUN_08129a98` | 922B | **SAI 페리페럴 초기화** (SAI1~SAI4 멀티 인스턴스) |
| `FUN_0812215c` | ~1200B | SAI 클럭 활성화 + GPIO 설정 + DMA 설정 (4개 인스턴스 분기) |
| `FUN_081293f4` | 704B | SAI 상태/인터럽트 핸들러 |
| `FUN_08129144` | ~300B | SAI 클럭 디바이더 계산 (FP 연산, DAT_08129284 구조체) |
| `FUN_08128fec` | ~300B | SAI 클럭 디바이더 계산 v2 (DAT_0812912c 구조체) |
| `FUN_081259e0` | ~500B | GPIO 핀 설정 (범용 — 모든 포트/핀) |
| `FUN_08124990` | ~1500B | DMA 스트림 설정 (범용 — DMA1/DMA2/BDMA) |
| `FUN_0812853c` | ~1000B | 페리페럴 클럭 활성화 (범용 — RCC 레지스터) |
| `FUN_081239ec` | 1070B | HSEM 획득 (코어간 동기화) |
| `FUN_0812421c` | 522B | HSEM 해제 (코어간 동기화) |
| `FUN_08124600` | ~50B | DataMemoryBarrier + 레지스터 초기화 (멀티코어 부트) |
| `FUN_0812f518` | 6B | SAI 래퍼 — 인스턴스 1 (DAT_0812f520) |
| `FUN_0812f584` | 6B | SAI 래퍼 — 인스턴스 2 (DAT_0812f58c) |

### 3.2 CM7 오디오 DSP

| 함수 | 크기 | 오디오 점수 | 특징 |
|------|------|-----------|------|
| `FUN_080359f4` | 18,232B | ? | CM7 최대 함수 — 메인 오디오 DSP |
| `FUN_0803e6f8` | 10,332B | 12 | float + short + VectorFloat |
| `FUN_0803c2bc` | 9,250B | 6 | float + short, 구조체 포인터 연산 |
| `FUN_080321d4` | 8,350B | 11 | float + short + VectorFloat |
| `FUN_0803a490` | 7,610B | 12 | float + short + VectorFloat, 9개 전역변수 |
| `FUN_08054708` | 7,480B | 12 | float + short + VectorFloat |
| `FUN_08034338` | 5,046B | 6 | float + short, 15개 전역변수 (필터 계수?) |
| `FUN_0805a040` | 3,840B | 10 | float + VectorFloat, 23개 전역변수 |
| `FUN_08056ed0` | 2,766B | 12 | float + short + VectorFloat |
| `FUN_08016968` | 2,334B | 13 | **0x3f800000 (1.0f) 사용** — 정규화 |
| `FUN_08056528` | 2,276B | 12 | float + short + VectorFloat |
| `FUN_0801b8b0` | 2,260B | 12 | float + short + VectorFloat |
| `FUN_0805c408` | 2,700B | 10 | 10개 파라미터 — 복잡한 DSP 체인 |
| `FUN_08029390` | 2,748B | 4 | float, 9개 전역변수 |

---

## 4. 미해결 질문

### 4.1 ❓ 오디오 코덱 미발견
- 어떤 바이너리에서도 AK/WM/CS/PCM/TLV/ES 코덱 칩 이름 없음
- I2C 레퍼런스 없음 — 코덱이 I2C로 제어되지 않거나 간접 참조
- **가능성:** 코덱이 SPI로 제어됨, 또는 하드웨어 기본설정 (jumper/하드웨어 pin), 또는 FX 코어가 제어

### 4.2 ❓ CM4-CM7 인터코어 통신
- Ghidra에서 HSEM/IPCC/AXI SRAM/DTCM 레퍼런스 전무
- `DataMemoryBarrier(0x1f)` 명령어 존재 → 실제 동기화는 일어남
- **가능성:** 포인터 간접 참조로 인해 Ghidra가 추적 못 함. 런타임에 주소 계산.

### 4.3 ❓ 0x40015C00, 0x40016000 미확인
- STM32H745에서는 예약 영역이나 H747에서는 SAI3
- 펌웨어가 H747 호환으로 빌드되었을 가능성 높음
- GPIO PD11/12/13 (AF10)은 실제로 SAI2 Block B 핀

### 4.4 ❓ DMA 버퍼 주소 미확인
- DMA 스트림 레지스터 (PAR, M0AR, M1AR)가 런타임에 설정됨
- 정적 분석으로는 버퍼 위치 추적 불가
- 동적 분석 (JTAG/SWD) 또는 런타임 트레이싱 필요

### 4.5 ❓ IRQ 벡터 테이블 확인 불가
- CM4 벡터 테이블에서 오디오 관련 IRQ 핸들러 미발견
- DMA 전송이 폴링 기반일 가능성, 또는 VTOR가 다른 주소를 가리킴

---

## 5. 다음 단계 (Phase 5+)

### Phase 5: DAC/ADC 칩 식별
- [ ] 물리적 보드 분석 (칩 사진, 데이터시트 확인)
- [ ] SPI 레지스터 접근 패턴 검색 (DMA1/DMA2 + SPI 클럭 활성화)
- [ ] FUN_08122010, FUN_08122080 등 미분석 init 함수들 확인

### Phase 6: SAI 오디오 인터페이스 심층
- [ ] SAI CR1/CR2 설정값 분석 (프로토콜: I2S/TDM/PDM)
- [ ] DMA 버퍼 사이즈 및 듀얼 버퍼 구조
- [ ] CM7 오디오 DSP 함수별 기능 식별

### Phase 7: UI MCU 통신 프로토콜
- [ ] UI MCU별 통신 인터페이스 (SPI/UART?)
- [ ] 프로토콜 구조 (명령어 포맷, 상태 보고)
- [ ] CM4의 30개 init 함수 중 UI 관련 함수 식별

---

## 6. 분석 스크립트

| 스크립트 | 경로 | 목적 |
|----------|------|------|
| phase4_comprehensive_scan.py | ~/hoon/ghidra/scripts/ | Raw 바이너리 검색 (결과 불량) |
| phase4_ref_scan.py | ~/hoon/ghidra/scripts/ | Reference 기반 스캔 (부분 성공) |
| phase4_i2c_deep.py | ~/hoon/ghidra/scripts/ | I2C/SAI 심층 분석 |
| phase4_sai_audio_chain.py | ~/hoon/ghidra/scripts/ | SAI 오디오 체인 추적 |
| phase4_cm7_dsp_intercore.py | ~/hoon/ghidra/scripts/ | CM7 DSP + 인터코어 통신 |
| phase4_dma_irq_summary.py | ~/hoon/ghidra/scripts/ | DMA + IRQ + 요약 |

## 7. 분석 결과 파일

| 파일 | 경로 |
|------|------|
| SAI reference scan | ~/hoon/minifreak/firmware/analysis/phase4_ref_scan.json |
| I2C deep analysis | ~/hoon/minifreak/firmware/analysis/phase4_i2c_deep_analysis.json |
| Audio analysis summary | ~/hoon/minifreak/firmware/analysis/phase4_audio_analysis_summary.json |
