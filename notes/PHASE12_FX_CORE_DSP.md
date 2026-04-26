# Phase 12-2: FX 코어 12타입 DSP 식별 (VST: 13타입) — 종합 매핑 문서

> **대상 펌웨어**: `minifreak_fx__fw1_0_0_2229__2025_06_18.bin`
> **분석 날짜**: 2026-04-26
> **소스**: Phase 7-3, Phase 7-3+ (Deep Dive), Phase 8 FX Enum 분석 종합
> **도구**: Ghidra 12.0.4 (ARM:LE:32:Cortex), strings, xxd

---

## 1. FX 코어 바이너리 개요

| 항목 | 값 |
|------|-----|
| **파일명** | `minifreak_fx__fw1_0_0_2229__2025_06_18.bin` |
| **크기** | 122,640 바이트 (119.8 KB) |
| **MD5** | `176eb2b7940ce7e1318c33ac21bdf450` |
| **아키텍처** | ARM Cortex-M (Thumb-2) — **별도 ARM 코어** (DSP56362 아님) |
| **RTOS** | FreeRTOS ("Scheduler full" @ 0x1B396) |
| **빌드 날짜** | Jun 18 2025, 14:21:05 |
| **버전** | 0.0.1 |
| **식별자** | "FX app" (@ 0x1CB64) |
| **벡터 테이블** | `0x080018C0` (SP = `0x08001840`, Reset = `0x00000000`) |
| **메모리 맵** | FLASH `0x080018C0` ~ `0x0801F7CF` (122,640B, RWX) |
| **전체 함수 수** | 290 (named: 3, unnamed: 287, thunks: 3) |

### 1.1 오디오 사양
- **샘플레이트**: 48kHz (문자열 5회 참조)
- **비트심도**: float32 (1.0f 리터럴 161회)
- **버퍼 크기**: 16 샘플/채널 (64바이트 = 16 × float32)
- **채널**: 스테레오 (L/R 병렬 처리)

### 1.2 페리페럴 맵

| 페리페럴 | 주소 | 용도 |
|----------|------|------|
| **SAI2** | 0x40015C00 | I2S 오디오 입출력 |
| **DMA1** | 0x40026000 | 오디오 DMA 전송 |
| **SPI1** | 0x40015800 | CM4 ↔ FX 파라미터 스트림 |
| **SPI2** | 0x40015C00 | 보조 통신 |
| **SPI3** | 0x40016000 | 보조 통신 |
| **USART1/3** | 0x40011000/0x40004800 | CM4 커맨드 채널 |
| **DMA2** | 0x40004C00 | SPI DMA 전송 |
| **MDMA** | 0x40007800 | 고속 메모리 전송 |
| **HSEM** | 0x4C000000 | 코어간 세마포어 동기화 |
| **SYSCFG** | 0x40011400 | 핀/클럭 라우팅 |
| **GPIOI** | 0x40007C00 | SPI 칩셀렉트 GPIO |

### 1.3 함수 크기 분포

| 범위 | 개수 |
|------|------|
| <10B (tiny) | 27 |
| 10-50B (small) | 112 |
| 50-200B (medium) | 94 |
| 200-500B (large) | 36 |
| 500-1KB (XL) | 16 |
| 1KB+ (XXL) | 5 |

### 1.4 내부 문자열

| 주소 | 문자열 | 용도 |
|------|--------|------|
| 0x1CC56 | "Scheduler full" | FreeRTOS 스케줄러 에러 |
| 0x1E550 | "Segmentation fault" | 메모리 접근 에러 |
| 0x1E563 | "build version : " | 빌드 정보 |
| 0x1E574 | "Unknown" | 알 수 없는 에러 |
| 0x1E5AB | "Warning- " | 경고 메시지 |
| 0x1E5B5 | "Error- " | 에러 메시지 |
| 0x1CB64 | "FX app" | 펌웨어 식별자 |

---

## 2. CM4 FX 타입 Enum → FX 코어 서브프로세서 매핑

### 2.1 CM4 FX 타입 Enum (12종, 주소 0x081AF308)

CM4 펌웨어 `minifreak_main_CM4`에 있는 FX 타입 문자열 테이블. **Inline null-terminated strings** (8-byte pointer 아님 — Phase 12 초기 분석의 오류, V2 감사에서 수정). CM4에는 12종, VST 플러그인에는 13종 ("Stereo Delay" 추가).

> ⚠️ **V2 감사 수정**: 초기 Phase 12는 CM4에 13타입 (VST 기반)이라고 주장했으나, 바이너리 직접 스캔 결과 CM4에는 12종만 존재. "Stereo Delay"는 VST 전용 타입으로 CM4 바이너리에 해당 문자열 없음.

| Index | FX 타입 | CM4 주소 | 바이트 오프셋 | VST 일치 |
|-------|---------|----------|--------------|----------|
| 0 | **Chorus** | 0x081AF308 | +0 | ✅ |
| 1 | **Phaser** | 0x081AF310 | +8 | ✅ |
| 2 | **Flanger** | 0x081AF318 | +16 | ✅ |
| 3 | **Reverb** | 0x081AF320 | +24 | ✅ |
| 4 | **Distortion** | 0x081AF328 | +32 | ✅ (VST index 5) |
| 5 | **Bit Crusher** | 0x081AF334 | +44 | ✅ (VST index 6) |
| 6 | **3 Bands EQ** | 0x081AF340 | +56 | ✅ (VST index 7) |
| 7 | **Peak EQ** | 0x081AF34C | +68 | ✅ (VST index 8) |
| 8 | **Multi Comp** | 0x081AF354 | +76 | ✅ (VST index 9) |
| 9 | **SuperUnison** | 0x081AF360 | +88 | ✅ (VST index 10) |
| 10 | **Vocoder Self** | 0x081AF36C | +96 | ✅ (VST index 11) |
| 11 | **Vocoder Ext** | 0x081AF37C | +116 | ✅ (VST index 12) |
| *(VST only)* | **Stereo Delay** | — | — | CM4 없음 |

**CM4 서브타입 합계: 53종** (VST: 63종, +Stereo Delay 12종)

> **인덱스 불일치 참고**: CM4 index 4 = Distortion, VST index 4 = Stereo Delay. CM4는 index 4부터 Distortion이 시작되므로 VST index 5~12와 CM4 index 4~11이 같은 FX 타입을 가리킴.

### 2.2 FX 코어 7서브프로세서 구조

FX 코어 `FUN_0800ca04` (FX Chain Init, 2054B)에서 초기화하는 7개 서브프로세서. 각 FX 슬롯당 7개를 순차적으로 초기화.

| SP# | 함수 | 주소 | 크기 | 구조체 크기 | 핵심 특성 |
|-----|------|------|------|-----------|----------|
| **SP0** | `FUN_0800b4f4` | 0x800B4F4 | 104B | 48B (0x30) | LFO ×1, wave ×1, `32768.0` 스케일링 |
| **SP1** | `FUN_0800bba0` | 0x800BBA0 | 300B | 148B (0x94) | `FUN_0800bb60` ×5 (delay init), buf 320B, mode=0 |
| **SP2** | `FUN_0800bc88` | 0x800BC88 | 300B | 148B (0x93) | `FUN_0800bb60` ×5 (delay init), buf 320B, mode=0 |
| **SP3** | `FUN_0800c5d0` | 0x800C5D0 | 312B | 224B (0xE0) | wave ×3, delay ×1, LFO ×2, buf 96B×2, **mode=6** |
| **SP4** | `FUN_0800c6ac` | 0x800C6AC | 392B | 336B (0x150) | **`1.0/n`**, osc ×3, filter ×6, delay ×2, **mode=2** |
| **SP5** | `FUN_0800c87c` | 0x800C87C | 312B | 243B (0xF3) | **`1.0/n`**, osc ×3, filter ×6, delay ×1, **mode=1** |
| **SP6** | `FUN_0800bdd0` | 0x800BDD0 | 384B | 236B (0xEC) | **9개 하위 프로세서**, VTable, duo 구조 |

### 2.3 SP6 내부 하위 프로세서 (Multi-FX 엔진)

SP6은 가장 복잡한 서브프로세서로, 5개 독립 하위 모듈을 포함:

| 하위 함수 | 주소 | 역할 | 매핑 FX 타입 |
|-----------|------|------|-------------|
| `FUN_08009b98` | 0x8009B98 | 3밴드 EQ 필터 | **3 Bands EQ** (index 7) |
| `FUN_08009e88` | 0x8009E88 | 추가 필터 스테이지 (올패스) | **Phaser** (index 1) |
| `FUN_0800a134` | 0x800A134 | 웨이브셰이퍼 | **Distortion** (index 5) |
| `FUN_0800a408` | 0x800A408 | 모듈레이션 엔진 | **Chorus** (index 0), **Flanger** (index 2) |
| `FUN_080082f0` | 0x80082F0 | 다중 디튠 카피 | **Super Unison** (index 10) |

### 2.4 종합 매핑: CM4 12타입 → FX 코어 DSP 함수

```
┌─────────────────────────────────────────────────────────────────────┐
│              CM4 FX Enum (12 types) → FX Core DSP Mapping          │
├───────┬────────────────┬──────────────────────┬──────────┬─────────┤
│ Index │ FX Type        │ FX Core SP / Function│ DSP Proc │ Conf.   │
├───────┼────────────────┼──────────────────────┼──────────┼─────────┤
│   0   │ Chorus         │ SP6 → FUN_0800a408  │ Mod.Core │ ★★★★☆  │
│   1   │ Phaser         │ SP6 → FUN_08009e88  │ AP Chain │ ★★★★☆  │
│   2   │ Flanger        │ SP6 → FUN_0800a408  │ Mod.Core │ ★★★★☆  │
│   3   │ Reverb         │ SP3 → FUN_0800c5d0  │ Diffuser │ ★★★★☆  │
│   4   │ Distortion     │ SP6 → FUN_0800a134  │ WaveShp  │ ★★★★☆  │
│   5   │ Bit Crusher    │ FUN_0801a468 (proc) │ BitCrush │ ★★★★☆  │
│   6   │ 3 Bands EQ     │ SP6 → FUN_08009b98  │ BiQuad   │ ★★★★★  │
│   7   │ Peak EQ        │ SP6 → FUN_08009b98  │ BiQuad   │ ★★★☆☆  │
│   8   │ Multi Comp     │ SP0 → FUN_0800b4f4  │ Envelope │ ★★★★☆  │
│   9   │ Super Unison   │ SP6 → FUN_080082f0  │ MultiDet │ ★★★☆☆  │
│  10   │ Vocoder Self   │ SP5 → FUN_0800c87c  │ Vocoder  │ ★★★★★  │
│  11   │ Vocoder Ext In │ SP4 → FUN_0800c6ac  │ Vocoder  │ ★★★★★  │
│ *(VST)*│ Stereo Delay  │ SP1+SP2 → 0800bba0/ │ Multitap │ ★★★★★  │
│       │                │          0800bc88    │          │         │
└───────┴────────────────┴──────────────────────┴──────────┴─────────┘
```

---

## 3. FX 체인 메모리 레이아웃

### 3.1 3슬롯 × 7서브프로세서 구조

```
FUN_0800ca04(param_1, ...) 호출 패턴 (offset from param_1 base):

Slot A:
  SP0 @ +0x000  FUN_0800b4f4  [Comp]
  SP1 @ +0x3C4  FUN_0800bba0  [Delay A]
  SP2 @ +0xA9C  FUN_0800bc88  [Delay B]
  SP3 @ +0x1168 FUN_0800c5d0  [Reverb]
  SP4 @ +0x1BF4 FUN_0800c6ac  [Vocoder Chord]
  SP5 @ +0x2BD8 FUN_0800c87c  [Vocoder Band]
  SP6 @ +0x3748 FUN_0800bdd0  [Multi-FX]

Slot B (offset +0x248 per SP from Slot A):
  SP0 @ +0x23C, SP1 @ +0x60C, SP2 @ +0xCE0, SP3 @ +0x14EC
  SP4 @ +0x2140, SP5 @ +0x2FA8, SP6 @ +0x3AEC

Slot C (offset +0x248 per SP from Slot B):
  SP0 @ +0x300, SP1 @ +0x854, SP2 @ +0xF24, SP3 @ +0x1870
  SP4 @ +0x268C, SP5 @ +0x3378, SP6 @ +0x3E90
```

**슬롯 간격: 0x248 (584바이트)** — 모든 서브프로세서 동일 간격.

### 3.2 총 메모리 사용

```
총 FX 체인 크기 = 0x3E90 + 최대 구조체 크기 (0x150) ≈ 0x3FE0 (16,320B)
+ FUN_0800bf70 ×8 (추가 초기화, per-slot)
+ 파라미터 블록 (584B × 3 슬롯 = 1,752B)
```

---

## 4. DSP 프로세싱 함수 상세

### 4.1 핵심 DSP 함수 (11개)

| 함수 | 주소 | 크기 | DSP Score | FX 타입 | 확신도 |
|------|------|------|-----------|---------|--------|
| `FUN_0800ca04` | 0x800CA04 | 2054B | — | **FX 체인 초기화** | ★★★★★ |
| `FUN_0800a83c` | 0x800A83C | 1954B | — | **파라미터 직렬화** (385 data refs) | ★★★★★ |
| `FUN_0801a468` | 0x801A468 | 1280B | 18 | **Bitcrusher/Disto** | ★★★★☆ |
| `FUN_080114b0` | 0x80114B0 | 1024B | 25 | **Reverb** (멀티패스) | ★★★☆☆ |
| `FUN_08006510` | 0x8006510 | 1102B | 27 | **하드웨어 설정** (SPI/DMAC) | ★★★★★ |
| `FUN_0800934c` | 0x800934C | 826B | 22 | **EQ3** (바이쿼드 체인) | ★★★★☆ |
| `FUN_08006b28` | 0x8006B28 | 720B | 44 | **SPI 전체 설정** | ★★★★★ |
| `FUN_0801559c` | 0x801559C | 626B | 22 | **SuperUnison** (모듈레이션+게인) | ★★★☆☆ |
| `FUN_080152e8` | 0x80152E8 | 648B | 33 | **모듈레이션 코어** (Chorus/Flanger/Phaser) | ★★★★☆ |
| `FUN_08012c3c` | 0x8012C3C | 652B | 22 | **StereoDelay** (딜레이라인+보간) | ★★★★☆ |
| `FUN_0800f2dc` | 0x800F2DC | 642B | 23 | **MultiComp** (엔벨롭+게인리덕션) | ★★★★☆ |

### 4.2 Chorus / Flanger / Phaser 공유 코어

**메인 함수**: `FUN_080152e8` (648B, 9 case 분기, DSP Score 33)

```
입력: fVar10 (오디오 샘플), param_1 (FX 상태 구조체)
switch(param_1[0x84]):  // subtype selector
  case 0: FUN_08003734() → 웨이브셰이핑 (기본 모듈레이션)
  case 1: FUN_08015084() → LFO 룩업 타입A @ offset+0x9C
  case 2: FUN_08015198() → LFO 룩업 타입B @ offset+0xC8
  case 3: FUN_08015198() → LFO 룩업 타입B @ offset+0xE4
  case 4: FUN_08015084() → LFO 룩업 타입A @ offset+0x100
  case 5: FUN_0800a478()  → 결합 LFO @ offset+0xC8, offset+0x130
  case 6: FUN_0800a478()  → 결합 LFO @ offset+0xE4, offset+0x13C
  case 7: FUN_080152ac()  → 페이즈 싱크 감지
  case 8: FUN_08007c6a()  → 파라미터 램핑
```

**모듈레이션 구조체 오프셋**:
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

### 4.3 SuperUnison

**메인 함수**: `FUN_0801559c` (626B) — `FUN_080152e8`를 래핑
- RMS 게인 계산 (`FUN_080080c0` 기반)
- 파나이저: `pan = (ref - gain) / (ref + gain)`
- 다중 보이스 합성 (루프: `pfVar8+0x10 != pfVar10`)
- 보이스 간 주파수 디튜닝

### 4.4 StereoDelay

**메인 함수**: `FUN_08012c3c` (652B)

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

**딜레이 파라미터 구조체**:
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

### 4.5 MultiComp (멀티밴드 컴프레서)

**메인 함수**: `FUN_0800f2dc` (642B)

```
오디오 처리 루프 (16 samples):
  1. 입력 버퍼 복사: L/R → local_38/local_34
  2. RMS 엔벨롭 계산: FUN_0800f25c() — (|L|+|R|)/2
  3. 게인 리덕션: fVar13 → fVar16 (엔벨롭 기반)
  4. pass-through (grooming)
  5. 병렬 프로세싱: 8개 밴드
  6. 크로스페이드: FUN_080080c0() 기반 wet/dry 믹스
```

**RMS 엔벨롭 팔로워** (`FUN_0800f25c`, 122B):
```
fVar4 = (|L| + |R|) * 0.5 * sensitivity
if (current <= fVar4) coeff = attack
else                   coeff = release
envelope = current + coeff * (fVar4 - current)  // 1st order
if (envelope < floor) envelope = 0.0             // noise gate
```

### 4.6 EQ3 (3밴드 이퀄라이저)

**메인 함수**: `FUN_0800934c` (826B)
- 입력 4채널 병렬 복사
- 바이쿼드 체인: 16 samples × N bands
- `FUN_080080c0()`: 원포올 필터 (각 밴드)
- `FUN_080083e0/FUN_08007370`: 주파수 계수 계산
- 65개 float 참조, 다중 주파수 대역 계수

### 4.7 Reverb

**메인 함수**: `FUN_080114b0` (1024B)

```
6채널 병렬 입력 처리:
  param_1+0x16 → FUN_0800e990() → offset+0x34
  param_1+0x17 → FUN_0800e9b4() → offset+0x1E8
  param_1+0x18 → waveshaper     → offset+0x4C
  param_1+0x19 → FUN_0800e9d8() → offset+0x194
  param_1+0x1a → FUN_0800e9fc() → FUN_0800ea68()
  param_1+0x1b → FUN_0800ea20() → offset+0x1B0

SQRT 기반 계수 계산 → Schroeder / FBP (Feedback Delay Network) 패턴
최종 필터: FUN_0801140c()
```

### 4.8 Distortion / Bitcrusher

**메인 함수**: `FUN_0801a468` (1280B)

```
핵심 알고리즘:
  1. FIR 필터: 입력 × 커널 (param_4개) → local_88[]
  2. 비트 리덕션: int32 양자화 → remainder 계산
  3. 샘플레이트 리덕션:
     - 8비트 누산기 (local_178[])
     - 1/2/4비트 서브샘플링 (iVar12)
  4. 양자화: FUN_0801abd4 (round) + FUN_0801ab50 (floor)
```

주파수 테이블 @ 0x1D214: `[21.99, 23.56, 25.13, 26.70, 28.27]` Hz

### 4.9 Vocoder Self (SP5)

**Init 함수**: `FUN_0800c87c` (312B, 구조체 243B)

```c
param_1[0x1c] = 1;          // mode = 1 (Vocoder Self)
param_1[0x67] = 1.0 / fVar4;  // 1.0/n_bands 정규화
FUN_0800b3e8();              // osc init ×3
FUN_0800c2b0(..., uVar3);   // filter init ×4
FUN_0800c854(..., uVar3);   // filter init ×2
FUN_0800c3f8(..., 0x56ce);  // delay line (22222샘플 ≈ 0.46초 @ 48kHz)
```

- 6개 밴드패스 필터 (c2b0 ×4 + c854 ×2)
- 3개 오실레이터 + 1개 딜레이라인
- 파라미터 포인터로 주파수 데이터 직접 로드

### 4.10 Vocoder Ext In (SP4)

**Init 함수**: `FUN_0800c6ac` (392B, 구조체 336B — 가장 큰 서브프로세서)

```c
param_1[0x1a] = 2;          // mode = 2 (Vocoder Chord)
param_1[0x67] = 1.0 / fVar5;  // 1.0/n_bands 정규화
FUN_0800b3e8();              // osc init ×3
FUN_0800c260(..., uVar4);   // filter init ×2
FUN_0800c288(..., uVar4);   // filter init ×2
FUN_0800c2b0(..., uVar4);   // filter init ×2
FUN_0800c3f8(..., 0x56ce);  // delay line ×2
```

- 6개 밴드패스 필터 (c260 ×2 + c288 ×2 + c2b0 ×2)
- 3개 오실레이터 + 2개 딜레이라인 + 2개 LFO

### 4.11 Vocoder Self vs Vocoder Ext In 비교

| 속성 | Vocoder Self (SP5) | Vocoder Ext In (SP4) |
|------|--------------------|----------------------|
| **Mode** | 1 | 2 |
| **함수** | `FUN_0800c87c` | `FUN_0800c6ac` |
| **구조체** | 243B (0xF3) | 336B (0x150) |
| **필터** | c2b0 ×4 + c854 ×2 (6개) | c260 ×2 + c288 ×2 + c2b0 ×2 (6개) |
| **오실레이터** | 3개 | 3개 |
| **딜레이** | 1개 | 2개 |
| **LFO** | — | 2개 |
| **모듈레이터** | 내부 신호 (필터 뱅크) | 외부 오디오 입력 |

---

## 5. DSP 유틸리티 함수

| 함수 | 주소 | 크기 | 알고리즘 |
|------|------|------|---------|
| `FUN_0800f25c` | 0x800F25C | 122B | RMS 엔벨롭 팔로워 (dual-channel) |
| `FUN_080080c0` | 0x80080C0 | 62B | 원포올 로우패스 (파라미터 스무딩) |
| `FUN_08012c12` | 0x8012C12 | 42B | 1차 올패스 필터 (리버브/페이저용) |
| `FUN_08003734` | 0x8003734 | 130B | 웨이브셰이퍼 (float 양자화 + 보간) |
| `FUN_08015084` | 0x8015084 | 262B | LFO 룩업 타입A (브레이크포인트 테이블) |
| `FUN_08015198` | 0x8015198 | 262B | LFO 룩업 타입B (브레이크포인트 테이블) |
| `FUN_0800a478` | 0x800A478 | 258B | LFO 룩업 타입C (3파라미터 결합) |
| `FUN_080152ac` | 0x80152AC | 60B | 페이즈 싱크 체크 (랩어라운드 감지) |
| `FUN_08007c6a` | 0x8007C6A | 76B | 파라미터 램프 (선형 보간 + 레이트 리미팅) |
| `FUN_080073c8` | 0x80073C8 | 22B | fmod (float 나머지, 페이즈 랩) |
| `FUN_08008720` | 0x8008720 | 62B | 파라미터 스무딩 (원포올 필터) |
| `FUN_080083d0` | 0x80083D0 | 12B | 2차 필터 계수 계산 (cos/sin 기반) |
| `FUN_08007370` | 0x8007370 | 70B | float → 파라미터 변환 (3차 다항식) |
| `FUN_080036b8` | 0x80036B8 | 110B | 정수 → float 변환 (룩업 테이블) |
| `FUN_08008278` | 0x8008278 | 38B | 역수 계산 + 정규화 |

---

## 6. 제어/통신 함수

| 함수 | 주소 | 크기 | 역할 |
|------|------|------|------|
| `FUN_08005c00` | 0x8005C00 | 314B | SPI TX 클럭 설정 (3채널) |
| `FUN_08005ab0` | 0x8005AB0 | 314B | SPI RX 클럭 설정 (3채널) |
| `FUN_08006b28` | 0x8006B28 | 720B | SPI 전체 설정 (CS, 클럭, 폴링, 13 case) |
| `FUN_08005ea0` | 0x8005EA0 | 626B | DMAC 스트림 설정 (6 case) |
| `FUN_08006510` | 0x8006510 | 1102B | DMAC + 타이머 종합 설정 (13 case) |
| `FUN_08004a84` | 0x8004A84 | 838B | 페리페럴 제어 (5 case, SPI/UART) |

### 6.1 SPI 프로토콜 (추정)

```
CM4 → FX SPI 프로토콜 (SPI1, CPOL=0, CPHA=0):
┌──────────────────────────────────────────┐
│ Byte 0:     [CMD | SLOT | TYPE]         │
│ Byte 1-2:   PARAM_INDEX (10-bit)        │
│ Byte 3-6:   VALUE (float32 LE)          │
│ Byte 7:     CHECKSUM                    │
│ Total: 8 bytes per parameter            │
└──────────────────────────────────────────┘

FX → CM4:
┌──────────────────────────────────────────┐
│ Byte 0:     STATUS flags                │
│ Byte 1-2:   SLOT_STATE                  │
│ Byte 3-6:   LEVEL_METER (float32)       │
│ Byte 7:     CHECKSUM                    │
│ Total: 8 bytes per slot                 │
└──────────────────────────────────────────┘
```

### 6.2 함수 포인터 테이블

| 주소 | 기능 |
|------|------|
| 0x0801B2F8 | SPI TX 핸들러 |
| 0x0801B321 | SPI RX 핸들러 |
| 0x0801B327 | DMA 완료 콜백 |
| 0x0801B32E | 에러 핸들러 |

### 6.3 SPI 클럭 모드

| Mode | Prescaler | 클럭 속도 |
|------|-----------|-----------|
| 0 | 0 | APB2/2 (최대 ~100MHz) |
| 1 | 1 | APB2/4 |
| 2 | 2 | APB2/8 |
| 3 | 3 | APB2/16 |

---

## 7. 오디오 신호 경로

```
SAI2 RX (I2S Input, 48kHz, float32, stereo)
  │
  ▼
┌──────────────────────────────────────────────────────┐
│              FX Processing Chain (FreeRTOS Task)      │
│                                                      │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐         │
│  │ Slot A   │ →  │ Slot B   │ →  │ Slot C   │         │
│  │ (584B)   │    │ (584B)   │    │ (584B)   │         │
│  └────┬────┘    └────┬────┘    └────┬────┘         │
│       │              │              │                │
│  [SP0~SP6]      [SP0~SP6]      [SP0~SP6]          │
│  7 subprocs     7 subprocs     7 subprocs           │
└───────┼──────────────┼──────────────┼────────────────┘
        │              │              │
        └──────────────┴──────────────┘
                       │
                       ▼
SAI2 TX (I2S Output, 48kHz, float32, stereo)
```

### 7.1 CM4 ↔ FX 코어 통신 경로

```
CM4 (Main MCU)                    FX Core (ARM Cortex-M)
┌──────────────┐    UART1/3       ┌──────────────┐
│ MIDI RX      │◄────────────────►│ FX 파라미터  │
│ Preset Mgmt  │                  │ 오디오 처리   │
│ UI Bridge    │    SPI1 (DMA)    │              │
│              │◄────────────────►│ SAI2 I2S I/O │
│ FX Command   │                  │              │
│ Dispatcher   │                  │              │
└──────────────┘    HSEM          └──────────────┘
                   (0x4C000000)
                   동기화 세마포어
```

---

## 8. Xref 핫스팟 (가장 많이 호출되는 함수)

| 함수 | 주소 | 크기 | 호출수 | 용도 |
|------|------|------|--------|------|
| `FUN_0801ad6c` | 0x801AD6C | 16B | 18 | 메모리 초기화 (memset) |
| `thunk_FUN_0801ad24` | 0x8019794 | 4B | 12 | thunk (에러 핸들러) |
| `FUN_0800b3e8` | 0x800B3E8 | 54B | 9 | 오실레이터/LFO 초기화 |
| `FUN_0800b4c4` | 0x800B4C4 | 40B | 7 | 웨이브/버퍼 초기화 |
| `FUN_0800b3de` | 0x800B3DE | 8B | 6 | 파라미터 로드 |
| `FUN_080034d8` | 0x80034D8 | 104B | 5 | 메모리 복사 |
| `FUN_08007370` | 0x8007370 | 70B | 5 | float 변환 유틸 |
| `FUN_080080c0` | 0x80080C0 | 62B | 5 | 원포올 로우패스 |

---

## 9. 키 데이터 테이블

| 주소 | 내용 | 용도 |
|------|------|------|
| 0x1A3F8~0x1B118 | 사인/코사인 룩업 테이블 | DSP 계수 (sin 0.04906~0.9238) |
| 0x1C984 | `[640.0, 3500.0, 4800.0, 2000.0, 0.1]` | FX 파라미터 기본값 |
| 0x1D214 | `[21.99, 23.56, 25.13, 26.70, 28.27]` Hz | 주파수/디튠 테이블 |

---

## 10. 미해결 사항 및 향후 조사

### 10.1 Bit Crusher DSP 식별
- CM4 enum index 6 ("Bit Crusher")에 해당하는 서브프로세서를 명확히 식별하지 못함
- `FUN_0801a468`의 비트 리덕션/디시메이션 코드가 Bitcrusher에 해당할 가능성 높음
- 그러나 이 함수가 Distortion(index 5)과 공유되는지 별도인지 미확인

### 10.2 Peak EQ 식별
- CM4 enum index 8 ("Peak EQ")에 해당하는 별도 DSP 함수 미발견
- EQ3(`FUN_0800934c`)과 공유될 가능성 있으나, 파라메트릭 EQ는 다른 계수 구조 필요

### 10.3 FX 타입 선택 로직
- `FUN_0800ca04`의 type selector (switch/case)를 아직 찾지 못함
- SP0~SP6를 어떤 조건으로 활성화/비활성화하는지 미확인

### 10.4 SPI 프로토콜 프레임 포맷
- 현재 추정만 — 실제 바이트 레벨 프로토콜은 레지스터 덤프나 로직 분석으로 확정 필요

### 10.5 SP1 vs SP2 정확한 구분
- 두 함수가 구조가 거의 동일 — Stereo Delay 내에서 어떤 역할 분담인지 미확인

---

## 11. 산출물 요약

| 파일 | 내용 |
|------|------|
| `PHASE12_FX_CORE_DSP.md` | **본 문서** — 종합 FX DSP 매핑 |
| `fx_deep_analysis.json` | 전체 함수 분석 (메모리맵, 벡터테이블, 함수통계, 문자열, xref, 디컴파일 15개) |
| `fx_decompiled_medium.json` | 중간 크기 DSP 함수 디컴파일 (25개 함수) |
| `fx_subfunctions.json` | 서브함수 디컴파일 (30개 함수) |
| `fx_triage.json` | 초기 triage 결과 (Phase 4) |
| `fx_type_subprocessor_map.json` | 서브프로세서 init 디컴파일 + 매핑 |
| `fx_vocoder.json` | Vocoder 분석 상세 |
| `fx_spi_protocol.json` | SPI 프로토콜 레지스터 분석 |
| `PHASE7-3_FX_CORE_ANALYSIS.md` | Phase 7-3 FX 코어 심층 분석 |
| `PHASE7_FX_DEEP_DIVE.md` | Phase 7 FX Deep Dive |
| `PHASE8_FX_OSC_ENUMS.md` | Phase 8 FX/OSC Enum 정리 (63 서브타입) |
