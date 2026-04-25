# Phase 7-3: FX 코어 심층 분석

> **분석 대상**: `minifreak_fx__fw1_0_0_2229__2025_06_18.bin`
> **분석 날짜**: 2025-04-25
> **도구**: Ghidra 12.0.4 + PyGhidra 3.0.2 (ARM:LE:32:Cortex)

---

## 1. 바이너리 개요

### 1.1 기본 정보
| 항목 | 값 |
|------|-----|
| 파일명 | `minifreak_fx__fw1_0_0_2229__2025_06_18.bin` |
| 크기 | 122,640 바이트 (119.8 KB) |
| 아키텍처 | ARM Cortex-M (Thumb-2) |
| 벡터 테이블 | `0x080018C0` (SP = `0x08001840`) |
| 엔트리포인트 | `0x00000000` (Reset 벡터 = 0 → 부트로더 경유) |
| 빌드 날짜 | Jun 18 2025, 14:21:05 |
| 버전 | 0.0.1 |
| 식별자 | "FX app" (@ 0x1CB64) |

### 1.2 중요 발견: ARM 코어 (DSP56362 아님)
초기 추정과 달리 **별도 ARM Cortex-M 코어**에서 실행됨. DSP56362는 아닌 것으로 확정.
STM32H7xx 시리즈의 CM4 코어와 유사한 인스트럭션 셋 사용.

### 1.3 RTOS: FreeRTOS 확정
```
"Scheduler full" @ 0x1B396
"Segmentation fault" @ 0x1CC90
```
FreeRTOS의 표준 에러 메시지. 스케줄러 태스크 관리 사용.

### 1.4 오디오 사양
- **샘플레이트**: 48kHz (문자열 5회 참조)
- **비트심도**: float32 (1.0f 리터럴 161회)
- **버퍼 크기**: 16 샘플/채널 (64바이트 = 16 × float32)
- **채널**: 스테레오 (L/R 병렬 처리 확인)

---

## 2. 메모리 맵

| 영역 | 시작 | 끝 | 크기 | 용도 |
|------|------|-----|------|------|
| FLASH | 0x080018C0 | 0x0801F7CF | 122,640B | 코드 + 데이터 (XIP) |
| SP (스택) | 0x08001840 | — | — | 초기 스택 포인터 |

### 2.1 키 데이터 영역
| 주소 | 내용 |
|------|------|
| 0x1A3F8~0x1B118 | 사인/코사인 룩업 테이블 (sin values 0.04906~0.9238) |
| 0x1C984 | FX 파라미터 기본값 `[640.0, 3500.0, 4800.0, 2000.0, 0.1]` |
| 0x1D214 | 주파수 테이블 `[21.99, 23.56, 25.13, 26.70, 28.27]` Hz |

---

## 3. 페리페럴 사용 현황

### 3.1 오디오 I/O
| 페리페럴 | 주소 | 용도 | 증거 |
|----------|------|------|------|
| **SAI2** | 0x40015C00 | I2S 오디오 입출력 | 문자열 @ 0x4BEC, IRQ 매핑 |
| **DMA1** | 0x40026000 | 오디오 DMA 전송 | IRQ 11-17 (Stream0~6) |

### 3.2 통신
| 페리페럴 | 주소 | 용도 | 증거 |
|----------|------|------|------|
| **USART3** | 0x40004800 | CM4 ↔ FX 코어 통신 | IRQ 39 핸들러 |
| **UART1** | — | 예비 통신채널 | 문자열 참조 |
| **UART2** | — | 예비 통신채널 | 문자열 참조 |

### 3.3 동기화
| 페리페럴 | 용도 |
|----------|------|
| HSEM (0x4C000000) | 코어간 세마포어 — CM4/FX 동기화 |

---

## 4. FX 아키텍처

### 4.1 3슬롯 × 7서브프로세서 구조
FX 체인은 **3개 FX 슬롯** (A/B/C)으로 구성되며, 각 슬롯은 **7개 서브프로세서**로 초기화됨.

```
FX Chain Architecture
═════════════════════════════════════════════════════════

  FUN_0800ca04() — FX Chain Init (2054B)
  │
  ├── FX Slot A ────────────────────────────────────
  │   ├── FUN_0800b4f4() @ offset 0x00A0   [basic]
  │   ├── FUN_0800bba0() @ offset 0x03C4   [modulation]
  │   ├── FUN_0800bc88() @ offset 0x0A9C   [filter]
  │   ├── FUN_0800c5d0() @ offset 0x1168   [delay]
  │   ├── FUN_0800c6ac() @ offset 0x1BF4   [dynamics]
  │   ├── FUN_0800c87c() @ offset 0x2BD8   [special]
  │   └── FUN_0800bdd0() @ offset 0x3748   [output]
  │
  ├── FX Slot B ────────────────────────────────────
  │   ├── FUN_0800b4f4() @ offset 0x023C   [basic]
  │   ├── FUN_0800bba0() @ offset 0x060C   [modulation]
  │   ├── FUN_0800bc88() @ offset 0x0CE0   [filter]
  │   ├── FUN_0800c5d0() @ offset 0x14EC   [delay]
  │   ├── FUN_0800c6ac() @ offset 0x2140   [dynamics]
  │   ├── FUN_0800c87c() @ offset 0x2FA8   [special]
  │   └── FUN_0800bdd0() @ offset 0x3AEC   [output]
  │
  └── FX Slot C ────────────────────────────────────
      ├── FUN_0800b4f4() @ offset 0x0300   [basic]
      ├── FUN_0800bba0() @ offset 0x0854   [modulation]
      ├── FUN_0800bc88() @ offset 0x0F24   [filter]
      ├── FUN_0800c5d0() @ offset 0x1870   [delay]
      ├── FUN_0800c6ac() @ offset 0x268C   [dynamics]
      ├── FUN_0800c87c() @ offset 0x3378   [special]
      └── FUN_0800bdd0() @ offset 0x3E90   [output]
```

### 4.2 서브프로세서 간격 분석
| 슬롯 | 서브프로세서 간격 | 누적 |
|------|-------------------|------|
| A→B | 0x248 (584B) | 0x3C4 |
| B→C | 0x248 (584B) | 0x60C |
| **슬롯당 크기** | **0x248 (584B)** | — |

각 FX 슬롯은 정확히 **584바이트** 간격으로 배치됨. 7개 서브프로세서가 하나의 구조체를 공유.

---

## 5. FX 타입 매핑 (11종)

MiniFreak V 편집기에서 추출한 `minifreak_fx_presets_params.xml` 기준.

### 5.1 FX 타입 목록
| # | FX 타입 | Opt1 서브모드 수 | Opt2 서브모드 수 | Opt3 서브모드 수 |
|---|---------|-----------------|-----------------|-----------------|
| 1 | **Chorus** | 5 (Default/Lush/Dark/Shaded/Single) | 5 | 5 |
| 2 | **Phaser** | 6 (Default/Default Sync/Space/Space Sync/SnH/SnH Sync) | 6 | 6 |
| 3 | **StereoDelay** | 12 (Digital/Stereo/Ping-Pong/Mono/Filtered + Sync variants) | 12 | 12 |
| 4 | **Reverb** | 6 (Default/Long/Hall/Echoes/Room/Dark Room) | 6 | 6 |
| 5 | **MultiComp** | 5 (OPP/Bass Ctrl/High Ctrl/All Up/Tighter) | 5 | 5 |
| 6 | **EQ3** | 3 (Default/Wide/Mid 1K) | 3 | 3 |
| 7 | **Disto** | 6 (Classic/Soft Clip/Germanium/Dual Fold/Climb/Tape) | 6 | 6 |
| 8 | **Flanger** | 4 (Default/Default Sync/Silly/Silly Sync) | 4 | 4 |
| 9 | **SuperUnison** | 8 (Classic/Ravey/Soli/Slow/Slow Trig/Wide Trig/Mono Trig/Wavy) | 8 | 8 |
| 10 | **VocoderSelf** | 4 (Clean/Vintage/Narrow/Gated) | 4 | 4 |
| 11 | **VocoderExt** | 4 (Clean/Vintage/Narrow/Gated) | 4 | 4 |

### 5.2 공통 속성
- 모든 파라미터: `realtimemidi=1` (MIDI CC로 실시간 제어 가능)
- 모든 파라미터: `transmittedtoprocessor=0` (CM4에서 FX 코어로 직접 전송 안 함 → UART 브릿지 경유)
- 모든 파라미터: `resetable=1` (리셋 가능)

---

## 6. DSP 함수 분석

### 6.1 핵심 DSP 함수 (10개)

| 함수 | 주소 | 크기 | DSP Score | 추정 FX 타입 | 확신도 |
|------|------|------|-----------|-------------|--------|
| `FUN_0800ca04` | 0x800CA04 | 2054B | — | FX 체인 초기화 | ★★★★★ |
| `FUN_0800a83c` | 0x800A83C | 1954B | 21 | 파라미터 동기화 | ★★★★★ |
| `FUN_0801a468` | 0x801A468 | 1280B | 18 | **Disto** (비트크러셔) | ★★★★☆ |
| `FUN_080114b0` | 0x80114B0 | 1024B | 25 | **Reverb** (멀티패스) | ★★★☆☆ |
| `FUN_08006510` | 0x8006510 | 1102B | 27 | 하드웨어 설정 (SPI/DMAC) | ★★★★★ |
| `FUN_0800934c` | 0x800934C | 826B | 22 | **EQ3** (바이쿼드 체인) | ★★★★☆ |
| `FUN_08006b28` | 0x8006B28 | 720B | 44 | SPI 레지스터 설정 | ★★★★★ |
| `FUN_0801559c` | 0x801559C | 626B | 22 | **SuperUnison** (모듈레이션+게인) | ★★★☆☆ |
| `FUN_080152e8` | 0x80152E8 | 648B | 33 | **모듈레이션 코어** (Chorus/Flanger/Phaser 공유) | ★★★★☆ |
| `FUN_08012c3c` | 0x8012C3C | 652B | 22 | **StereoDelay** (딜레이라인+보간) | ★★★★☆ |
| `FUN_0800f2dc` | 0x800F2DC | 642B | 23 | **MultiComp** (엔벨롭+게인리덕션) | ★★★★☆ |
| `FUN_08005ea0` | 0x8005EA0 | 626B | 42 | DMAC/타이머 설정 | ★★★★★ |

### 6.2 DSP 유틸리티 함수 (12개)

| 함수 | 주소 | 크기 | 역할 | 알고리즘 |
|------|------|------|------|---------|
| `FUN_0800f25c` | 0x800F25C | 122B | **RMS 엔벨롭 팔로워** | (|L|+|R|)/2 → attack/release smoothing |
| `FUN_080080c0` | 0x80080C0 | 62B | **원포올 로우패스** | 1차 IIR 필터 (파라미터 스무딩) |
| `FUN_08012c12` | 0x8012C12 | 42B | **올패스 필터** | 1차 올패스 (리버브/페이저용) |
| `FUN_08003734` | 0x8003734 | 130B | **웨이브셰이퍼** | float 양자화 + 선형 보간 |
| `FUN_08015084` | 0x8015084 | 262B | **LFO 룩업 (타입A)** | 브레이크포인트 테이블 + 선형 보간 |
| `FUN_08015198` | 0x8015198 | 262B | **LFO 룩업 (타입B)** | 브레이크포인트 테이블 + 선형 보간 |
| `FUN_0800a478` | 0x800A478 | 258B | **LFO 룩업 (타입C)** | 3파라미터 브레이크포인트 |
| `FUN_080152ac` | 0x80152AC | 60B | **페이즈 싱크 체크** | LFO 위상 랩어라운드 감지 |
| `FUN_08007c6a` | 0x8007C6A | 76B | **파라미터 램프** | 선형 보간 + 레이트 리미팅 |
| `FUN_080073c8` | 0x80073C8 | 22B | **fmod** | float 나머지 연산 (페이즈 랩) |
| `FUN_08008720` | 0x8008720 | 62B | **파라미터 스무딩** | 원포올 필터 (FUN_080080c0과 유사) |
| `FUN_080083d0` | 0x80083D0 | 12B | **계수 계산** | 2차 필터 계수 (cos/sin 기반) |

### 6.3 제어/통신 함수

| 함수 | 주소 | 크기 | 역할 |
|------|------|------|------|
| `FUN_08005c00` | 0x8005C00 | 314B | SPI TX 레지스터 설정 (3채널 출력) |
| `FUN_08005ab0` | 0x8005AB0 | 314B | SPI RX 레지스터 설정 (3채널 입력) |
| `FUN_08006b28` | 0x8006B28 | 720B | SPI 전체 설정 (CS, 클럭, 폴링) |
| `FUN_08005ea0` | 0x8005EA0 | 626B | DMAC 스트림 설정 (오디오 DMA) |
| `FUN_08006510` | 0x8006510 | 1102B | DMAC/타이머 종합 설정 |

---

## 7. FX 타입별 DSP 알고리즘 상세

### 7.1 Chorus / Flanger / Phaser (공유 코어)
**메인 함수**: `FUN_080152e8` (9 case 분기)

```
입력: fVar10 (오디오 샘플), param_1 (FX 상태 구조체)
  │
  ├── case 0: FUN_08003734() → 웨이브셰이핑 (기본 모듈레이션)
  ├── case 1: FUN_08015084() → LFO 룩업 타입A @ offset+0x9C
  ├── case 2: FUN_08015198() → LFO 룩업 타입B @ offset+0xC8
  ├── case 3: FUN_08015198() → LFO 룩업 타입B @ offset+0xE4
  ├── case 4: FUN_08015084() → LFO 룩업 타입A @ offset+0x100
  ├── case 5: FUN_0800a478()  → 결합 LFO @ offset+0xC8, offset+0x130
  ├── case 6: FUN_0800a478()  → 결합 LFO @ offset+0xE4, offset+0x13C
  ├── case 7: FUN_080152ac()  → 페이즈 싱크 감지
  └── case 8: FUN_08007c6a()  → 파라미터 램핑
```

**모듈레이션 파라미터** (param_1 구조체 오프셋):
| 오프셋 | 용도 |
|--------|------|
| +0x30 | LFO rate |
| +0x34 | 현재 위상 (phase) |
| +0x38 | 위상 누적기 |
| +0x44 | 모듈레이션 깊이 (depth) |
| +0x50 | 위상 증분 |
| +0x71 | 업데이트 플래그 |
| +0x72 | 활성 플래그 |
| +0x84 | 서브타입 선택 (uint16) |
| +0x90 | 모듈레이션 입력 |

**SuperUnison** (`FUN_0801559c`)은 `FUN_080152e8`를 래핑하여:
- RMS 게인 계산 (FUN_080080c0 기반)
- 파나이저 계산: `pan = (ref - gain) / (ref + gain)`
- 다중 보이스 합성 (루프: pfVar8+0x10 != pfVar10)
- 보이스 간 주파수 디튜닝

### 7.2 StereoDelay
**메인 함수**: `FUN_08012c3c`

```
오디오 처리 루프 (16 samples, 64 bytes):
  1. 입력 합산: (L + R) * wet_gain
  2. 올패스 필터 체인 ×3: FUN_08012c12()
     - param_1+0x75c → param_1+0x76c → param_1+0x74c
  3. 딜레이 버퍼 읽기: param_1+0x784/0x788 (L/R 인덱스)
  4. 보간: 4포인트 nearest-neighbor
  5. 피드백 적용: fVar15 * fVar17
  6. 출력: dry * dry_gain + wet * wet_gain
```

**딜레이 파라미터** (param_1 구조체 오프셋):
| 오프셋 | 용도 |
|--------|------|
| +0x50 | 딜레이 버퍼 포인터 |
| +0x74c, +0x75c, +0x76c | 올패스 필터 상태 (×3) |
| +0x784, +0x788 | L/R 딜레이 버퍼 인덱스 |
| +0x78c | 딜레이 버퍼 길이 |
| +0x7a8 | 크로스피드 |
| +0x7ac | 스테레오 확장 |
| +0x7d4 | dry gain |
| +0x7e0 | 필터 상태 |
| +0x7f0~0x808 | 추가 파라미터 블록 |

### 7.3 MultiComp (멀티밴드 컴프레서)
**메인 함수**: `FUN_0800f2dc`

```
오디오 처리 루프 (16 samples):
  1. 입력 버퍼 복사: L/R → local_38/local_34
  2. RMS 엔벨롭 계산: FUN_0800f25c() — (|L|+|R|)/2
  3. 게인 리덕션: fVar13 → fVar16 (엔벨롭 기반)
  4. 그루밍: 입력 버퍼를 출력으로 직접 복사 (pass-through)
  5. 병렬 프로세싱: 8개 밴드 (iVar10 != param_1+0x10)
  6. 크로스페이드: FUN_080080c0() 기반 wet/dry 믹스
```

**엔벨롱 팔로워** (`FUN_0800f25c`):
```
fVar2 = ABS(sample_L)
fVar4 = (ABS(sample_R) + fVar2) * 0.5 * sensitivity  // dual-channel RMS
if (current <= fVar4) coeff = attack
else                   coeff = release
envelope = current + coeff * (fVar4 - current)  // 1st order
if (envelope < floor) envelope = 0.0             // noise gate
```

### 7.4 EQ3 (3밴드 이퀄라이저)
**메인 함수**: `FUN_0800934c`

```
오디오 처리 루프:
  1. 입력 4채널 복사: param_2[0..3] → local_48
  2. 병렬 바이쿼드 처리: 16 samples × N bands
     - FUN_080080c0(): 원포올 필터 (각 밴드)
     - FUN_080083e0/FUN_08007370: 계산 유틸
  3. 주파수 의존적 게인: extraout_s0 * extraout_s10
  4. 출력: param_1+0xE4까지 병렬 버퍼
```

**파라미터**: 65개 float 참조, 다중 주파수 대역 계수.

### 7.5 Disto (디스토션)
**메인 함수**: `FUN_0801a468`

```
핵심 알고리즘 — 비트크러셔/디시메이터:
  1. FIR 필터: 입력 × 커널 (param_4개) → local_88[]
  2. 비트 리덕션:
     fVar20 * fVar19 → int32 → (int32 - quantized * floor) → remainder
  3. 샘플레이트 리덕션:
     - 8비트 누산기 (local_178[])
     - 오버플로우 캐리 체인
     - 1/2/4비트 서브샘플링 (iVar12)
  4. 양자화: FUN_0801abd4 (round) + FUN_0801ab50 (floor)
```

**주파수 테이블** @ 0x1D214: `[21.99, 23.56, 25.13, 26.70, 28.27]` Hz
→ 2π × 3.5~4.5Hz 범위 = LFO 레이트 테이블

### 7.6 Reverb (추정)
**메인 함수**: `FUN_080114b0`

```
멀티패스 오디오 처리:
  1. 병렬 입력 읽기 (6채널):
     - param_1+0x16: FUN_0800e990() → offset+0x34
     - param_1+0x17: FUN_0800e9b4() → offset+0x1E8
     - param_1+0x18: VectorUnsignedToFloat → waveshaper → offset+0x4C
     - param_1+0x19: FUN_0800e9d8() → offset+0x194
     - param_1+0x1a: FUN_0800e9fc() → FUN_0800ea68()
     - param_1+0x1b: FUN_0800ea20() → offset+0x1B0
  2. SQRT 기반 계수 계산:
     fVar15 = FUN_080083d0(gain * DAT_08011964)
     fVar13 = SQRT(fVar15) + SQRT(fVar15)  // = 2*sqrt(Q)
     fVar14 = 1/(fVar20 + fVar11 * fVar13)  // reciprocal
  3. 필터 매트릭스 출력:
     - offset+300: (fVar18 + fVar18) * fVar14
     - offset+0x128: fVar15 * (fVar19 - fVar11*fVar13) * fVar14
     - offset+0x120: fVar15 * (fVar19 + fVar11*fVar13) * fVar14
     - offset+0x124: fVar15 * -2 * (...) * fVar14
     - offset+0x130: fVar14 * (fVar20 - fVar11*fVar13)
  4. FUN_0801140c(): 최종 필터 적용
```

6개 병렬 입력 경로 + SQRT 기반 계수 → **Schroeder 리버브** 또는 **FBP (Feedback Delay Network)** 패턴.

---

## 8. CM4 ↔ FX 코어 통신

### 8.1 통신 경로
```
CM4 (제어)                    FX 코어 (DSP)
┌──────────────┐    UART3     ┌──────────────┐
│ MIDI 처리     │◄───────────►│ FX 파라미터   │
│ 프리셋 관리   │             │ 오디오 처리   │
│ UI 브릿지     │    SPI      │ SAI2 I2S I/O │
│              │◄───────────►│              │
│ 파라미터 전송  │             │ 상태 리포트   │
└──────────────┘             └──────────────┘
      │                           │
      └──── HSEM (0x4C000000) ────┘
           (동기화 세마포어)
```

### 8.2 통신 프로토콜
- **UART3**: 메인 커맨드 채널 (FX 타입 변경, 파라미터 업데이트)
- **SPI**: 고속 파라미터 스트림 (실시간 MIDI CC → FX 파라미터)
- **HSEM**: 프레임 동기화 (오디오 버퍼 스왑 트리거)

### 8.3 파라미터 전송 흐름
```
MIDI CC → CM4 수신 → 파라미터 매핑 → UART/SPI → FX 코어
                                                   │
                                          FUN_0800a83c (385 data refs)
                                          584B × 3 슬롯 파라미터 직렬화
```

`FUN_0800a83c`는 385개 데이터 참조를 가진 거대한 파라미터 직렬화 함수로, FX 상태 구조체에서 UART/SPI 전송용 버퍼로 파라미터를 복사.

---

## 9. 오디오 신호 경로

```
SAI2 RX (I2S Input, 48kHz)
  │
  ▼
┌─────────────────────────────────────────────┐
│              FX Processing Chain             │
│                                             │
│  ┌─────┐   ┌─────┐   ┌─────┐              │
│  │Slot A│ → │Slot B│ → │Slot C│              │
│  │(584B)│   │(584B)│   │(584B)│              │
│  └──┬──┘   └──┬──┘   └──┬──┘              │
│     │         │         │                   │
│  [7 sub-]  [7 sub-]  [7 sub-]              │
│  [procs ]  [procs ]  [procs ]              │
└─────┬─────────┬─────────┬───────────────────┘
      │         │         │
      └─────────┴─────────┘
                │
                ▼
SAI2 TX (I2S Output, 48kHz)
```

---

## 10. 함수 통계

| 카테고리 | 개수 |
|----------|------|
| 전체 함수 | 290 |
| DSP 함수 (score≥20) | 10 |
| DSP 유틸리티 | 12 |
| 제어/통신 | 5 |
| 초기화 | 4 |
| Thunk | 3 |
| 기타 | 256 |

### 크기 분포
| 범위 | 개수 |
|------|------|
| <10B (tiny) | 27 |
| 10-50B (small) | 112 |
| 50-200B (medium) | 94 |
| 200-500B (large) | 36 |
| 500-1KB (XL) | 16 |
| 1KB+ (XXL) | 5 |

---

## 11. 미해결 사항

### 11.1 Vocoder 분석 미완료
VocoderSelf / VocoderExt에 해당하는 DSP 함수를 명확히 식별하지 못함.
`FUN_080114b0`의 6채널 병렬 처리가 Vocoder의 밴드필터 체인일 가능성도 있음.
→ 추가 분석 필요: 6채널 입력 경로의 주파수 응답 확인.

### 11.2 FX 타입 → 서브프로세서 매핑 미확정
어떤 FX 타입이 7개 서브프로세서 중 어떤 것을 활성화하는지 미확인.
→ FUN_0800ca04의 하위 init 함수들 디컴파일 필요.

### 11.3 SPI 프로토콜 상세 미분석
CM4→FX 파라미터 전송의 실제 프레임 포맷 미확인.
→ FUN_08005c00/FUN_08005ab0의 레지스터 값 분석 필요.

### 11.4 IRQ 핸들러 미식별
DMA IRQ 핸들러의 실제 주소가 Ghidra에서 감지되지 않음.
→ DMA 스트림 설정 레지스터에서 핸들러 주소 역추적 필요.

---

## 12. 산출물

| 파일 | 내용 |
|------|------|
| `fx_deep_analysis.json` | 전체 함수 분석 (메모리맵, 벡터테이블, 함수통계, 문자열, xref, 디컴파일 15개) |
| `fx_decompiled_medium.json` | 중간 크기 DSP 함수 디컴파일 (25개 함수) |
| `fx_subfunctions.json` | 서브함수 디컴파일 (30개 함수) |
| `fx_triage.json` | 초기 triage 결과 (Phase 4) |
