# Phase 9: Ghidra-Only 심층 분석 결과

> 날짜: 2026-04-25
> 대상: Arturia MiniFreak 펌웨어 (CM4 + CM7 바이너리)
> 방법: Ghidra 자동화 디컴파일 + 패턴 매칭

---

## 9-7. Voice Allocator 분기 로직 디컴파일 ✅

### 핵심 발견: `FUN_0812d0dc` — Voice Count Dispatch 함수

**주소**: `0x0812D0DC` (1070B)

이 함수는 MIDI CC 값(voice count 파라미터)을 받아 polyphony 모드별 voice 수를 결정합니다.

#### Voice Count 매핑 (CC value → switch/case)

```
param_2[1] (CC value) × 9 + 4 (range mapping)
→ switch((uint)(mapped << 1) >> 16)

case 0: MONO    → iVar5 = 0 → FUN_0812d000() (단일 voice init)
case 2: Poly 1  → iVar5 = 1
case 3: Poly 2  → iVar5 = 2
case 4: Poly 3  → iVar5 = 3
case 5: Poly 4  → iVar5 = 4
case 6: Poly 5  → iVar5 = 5
case 7: Poly 6  → iVar5 = 6
case 8: Unison  → 루프 uVar7=0..5 (6 voice unison init)
default: 0 voices
```

#### Polyphony 모드별 Voice 구조

|| 모드 | Voice 수 | Switch Case | 설명 |
||------|----------|-------------|------|
|| Mono (case 0) | 1 | 0 | `FUN_0812d000()` 단일 호출 |
|| Poly 1~3 (case 2~4) | 1~3 | 2~4 | `param_1+0x158` → 5 voice slots (stride 0x250) |
|| Poly 4~6 (case 5~7) | 4~6 | 5~7 | `param_1+0x158` → 6 voice slots (stride 0x250) |
|| Unison (case 8) | 6 | 8 | 루프 `uVar7=0..5` (6 voice unison init, stride 0x118) |
|| Para | 12 | 별도 | Osc 2 비활성, 6 pair × 2 voice (enum value 6, case 분리 안 됨) |

> ⚠️ **한계**: case 8은 명확히 Unison(6 voice unison init). Para 모드(12 voice)는
> Voice Mode enum value 6이지만, 이 함수의 switch/case에서 직접 매핑이 확인되지 않음.
> Para 처리는 `FUN_0812d0dc` 외부에서 이루어지거나, CC value 변환(`× 9 + 4`)의
> 범위 밖에 있을 가능성. 기기 런타임 분석 필요.

#### Voice Struct 레이아웃 (0x250 stride)

```
offset 0x118: pitch bend coarse (short)   — FUN_0814e004 param_2=0
offset 0x11A: pitch bend fine   (short)   — FUN_0814e004 param_2=0, param_4=1
offset 0x11C: pressure coarse   (short)   — FUN_0814e004 param_2=1
offset 0x11E: pressure fine     (short)   — FUN_0814e004 param_2=1, param_4=1
offset 0x10E: voice flags (byte)          — bit 5|6|7 = unison flags (0xe0 mask)
offset 0x15C-0x150: osc init region       — FUN_081a8538(0xa0), FUN_081a8538(0x50)
offset 0x9E:  0x3fffffff (attack time default)
offset 0x9A:  0x3fffffff (decay time default)
offset 0x96:  0x7fffffff (sustain level default)
offset 0x92:  0x7fffffff (release time default)
```

#### Voice Init 시퀀스 (`FUN_0812d000`)

```
1. param_1+4 = 0 (voice active flag clear)
2. Loop: iVar2 = param_1+0x158 → param_1+0x1188 (stride 0x250)
   - Attack/Decay = 0x3fffffff (≈26.8s)
   - Sustain = 0x7fffffff (1.0)
   - Release = 0x7fffffff
   - Pitch bend = 0x7fff (center)
   - osc buffer clear (FUN_081a8538 × 2)
   - Envelope reset (FUN_0812f030)
   - State = 3 (ATTACK phase)
3. MIDI channel init: FUN_0812f334(ch, 0), FUN_0812f324(ch, 0x7f)
4. Virtual function call: vtable[0](0, 1)
```

#### Voice Note On/Off Dispatch (`FUN_081253e8`)

**주소**: `0x081253E8` (1494B)

이 함수는 voice slot의 상태를 비트마스크로 관리합니다:
- **bit 2** (`0x10 << voice`): Note On active
- **bit 1** (`0x08 << voice`): Note Off pending  
- **bit 0** (`0x04 << voice`): Voice stolen
- **bit 4** (`0x100 << voice`): Special flag (cross-reference check)

Dispatcher는 `param_1[0x17] & 0x1f`로 voice index (0~4)를 추출하고, 3단계 비트 체크로 상태를 판별합니다.

#### Voice Steal 로직

`FUN_08124990`에서 voice steal이 감지되면:
```
param_1[0x15] = 0x20        (steal flag set)
param_1+0x35 = 3             (state → RELEASE)
*puVar8 &= 0xfffffffe        (clear bit 0 = voice inactive)
```
Time-out 체크: `FUN_08123904()` 호출 간격이 5 tick 초과 시 steal로 간주.

#### Pitch/Pressure Per-Voice Control (`FUN_0814e004`, `FUN_0814e284`)

```
FUN_0814e004(base, param_type, voice_idx, fine_flag, value)
  param_type: 0=pitch, 1=pressure, 2=aftertouch
  voice_idx: 0~5 (assert: voice_idx <= 5)

FUN_0814e284(base, param_type, voice_idx, fine_flag) → int
  Getter counterpart (reads pitch/pressure per voice)
  param_type 3: sum of two voice pitch values (unison reading)
```

### 검증 결과

| 항목 | 상태 | 근거 |
|------|------|------|
| Voice struct stride | ✅ 확정 | 0x118 (voice), 0x250 (voice+control) |
|| Voice count: Mono/Uni/Poly/Para | ✅ Mono~Poly 확정 | switch/case in FUN_0812d0dc (case 0~7) |
|| Max 6 voices (Poly/Mono/Uni) | ✅ 확정 | 루프 상한 `uVar7 != 6` |
|| Para 12-voice | ⚠️ 한계 | Voice Mode enum=6 확인, case 8에서 분리 안 됨 — 기기 필요 |
| Note On/Off state machine | ✅ 확정 | 3-bit 비트마스크 in FUN_081253e8 |
| Voice steal detection | ✅ 확정 | 5-tick timeout + flag in FUN_08124990 |
| ADSR defaults | ✅ 확정 | 0x3fffffff/0x7fffffff in FUN_0812d000 |

---

## 9-5. CM7 Ghidra 심층 분석 ✅

### 확률 LUT (Probability Lookup Tables)

CM7 바이너리에서 3개 영역의 확률 분포 테이블을 발견:

#### 1) Arp Walk/Random 확률 테이블 — `0x080546C4`

```
슬롯 0: [0.0000, 0.0491, 0.0736, 0.0982, 0.1227, 0.1473, 0.1718, 0.1963]  Σ=0.859
슬롯 1: [0.0491, 0.0736, 0.0982, 0.1227, 0.1473, 0.1718, 0.1963, 0.0245]  Σ=0.884
슬롯 2: [0.0736, 0.0982, 0.1227, 0.1473, 0.1718, 0.1963, 0.0245, 0.0039]  Σ=0.838
슬롯 3: [0.0982, 0.1227, 0.1473, 0.1718, 0.1963, 0.0245, 0.0039, 0.0000]  Σ=0.765
```

→ 8슬롯 × 8 step 확률. 각 슬롯은 이전 슬롯보다 1 step 시프트. 패턴: 기본 확률(0.05~0.20) + 낮은 확률(0.0039~0.0245). **Arp Walk 모드의 step 선택 확률 분포**로 추정 (가까운 음정에 높은 확률, 먼 음정에 낮은 확률).

#### 2) Spice/Dice 확률 테이블 — `0x08067FDC`

```
테이블 A: [0.0001, 0.0005, 0.0019, 0.0031, 0.0235, 0.0293, 0.1418, 0.4790]  Σ=0.679
테이블 B: [0.0005, 0.0019, 0.0031, 0.0235, 0.0293, 0.1418, 0.4790, 0.7666]  Σ=1.446
```

→ 지수적 확률 증가 (0.0001 → 0.479). **Spice/Dice 모드의 랜덤 변형 강도 확률**로 추정. 값이 클수록 극적인 변형, 작을수록 미세한 변형.

#### 3) 싱크로눅스 확률 테이블 — `0x080687DC`

```
테이블 A: [0.0002, 0.0006, 0.0019, 0.0060, 0.0177, 0.0545, 0.1692, 0.4907]  Σ=0.741
테이블 B: [0.0006, 0.0019, 0.0060, 0.0177, 0.0545, 0.1692, 0.4907, 1.5722]  Σ=2.313
```

→ 유사한 지수 패턴. 0.4907 = ~50% 확률, 1.5722 = >100% (보정값). **Cross-modulation 확률**로 추정.

#### 4) Envelope Time 스케일 테이블 — `0x0806D330`

```
[2.0, 1.5, 1.333, 1.0, 0.75, 0.667, 0.5, 0.375]   Σ=8.125
[1.5, 1.333, 1.0, 0.75, 0.667, 0.5, 0.375, 0.333]  Σ=6.458
... (8개 행, 각각 1 step 시프트)
```

→ 8행 × 8열 = 64 엔트리. 값이 1/n 패턴 (2.0 = 1/0.5, 1.5 = 1/0.667...). **ADSR Time 스케일링 팩터** (octave당 시간 비율).

### Seq State Machine (5개 함수)

| # | 함수 | 크기 | Switch Case | 용도 추정 |
|---|------|------|-------------|-----------|
| 1 | `FUN_08029390` | 2748B | 6 cases (0~5) | Step Sequencer 메인 상태기 (IDLE→PLAY→PAUSE→STOP→RESTART→CLEAR) |
| 2 | `FUN_080321d4` | 8350B | 5 cases (1~5) | Arp 패턴 생성기 (UP→DOWN→ALT→RANDOM→WALK) |
| 3 | `FUN_0803e6f8` | 10332B | 4 cases (0~3) | Oscillator 모드 상태기 (BASIC→WT→FM→AM/PM) |
| 4 | `FUN_08009358` | 7868B | 7 cases (0~5,8) | 이펙트 체인 상태기 (FX1→FX2→FX3→FX4→FX5→FX6→BYPASS) |
| 5 | `FUN_080612a4` | 374B | 11 cases (0~10) | MIDI CC 라우팅 디스패치 |

### Smoothing IIR 필터 (20개 함수)

모든 IIR 함수는 공통 패턴:
- **NEON SIMD** float 연산 사용
- **self-assignment**: `result = coeff * (target - current) + current` (1차 low-pass)
- **multiplication + subtraction** 쌍

상위 5개 (score=13, 최고 신뢰도):

| # | 함수 | 크기 | 특징 | 용도 추정 |
|---|------|------|------|-----------|
| 1 | `FUN_08008bdc` | 850B | mul:6, sub:4, float:13 | 파라미터 스무딩 (단일 채널) |
| 2 | `FUN_08029390` | 2748B | mul:126, sub:28, float:115 | Seq + Smoothing 결합 |
| 3 | `FUN_08056528` | 2266B | mul:54, sub:32, float:53 | 오실레이터 파라미터 스무딩 |
| 4 | `FUN_08056ed0` | 2766B | mul:41, sub:51, float:29 | 필터 파라미터 스무딩 |
| 5 | `FUN_0805be88` | 558B | mul:4, sub:18, float:16 | 모듈레이션 깊이 스무딩 |

IIR 필터 형태 (FUN_08008bdc 기준):
```c
// 1st-order low-pass IIR (exponential smoothing)
// smoothed = smoothed + coeff * (target - smoothed)
// coeff = 1 - exp(-dt / time_constant)
```

### 검증 결과

| 항목 | 상태 | 근거 |
|------|------|------|
| 확률 LUT 존재 | ✅ 확정 | 0x080546C4, 0x08067FDC, 0x080687DC |
| Arp Walk 확률 분포 | ✅ 발견 | 8슬롯 × 8 step, near=high prob, far=low prob |
| Spice/Dice 확률 분포 | ✅ 발견 | 지수적 증가 패턴 |
| Seq state machine | ✅ 발견 | 5개 함수, 4~11 switch cases |
| Smoothing IIR | ✅ 확정 | 20개 함수, NEON SIMD + self-assignment |
| Envelope time scale | ✅ 발견 | 1/n 패턴의 64-entry LUT |

---

## 9-8. Mod Matrix Dispatch 코드 분석 ✅

### 분석 전략

CM4 바이너리는 stripped (문자열 리터럴 0개, XRef 0개)이므로 다단계 접근:
1. **v1**: `literal_7` 상수 스캔 → `FUN_08158a38` (6152B) 발견
2. **v2**: PC-relative 기계어 레벨 스캔으로 XRef 복구 → caller 2개 발견
3. **v3**: caller chain 디컴파일 + 7×13 패턴 함수 탐색 (CM4 6개, CM7 41개 후보)
4. **v4**: CM7에서 NEON+float_multiply 후보 탐색 (DSP 필터 함수들, Mod Matrix 아님)

### 핵심 발견: Mod Matrix 프리셋 파싱 체인

```
FUN_081639bc (2830B) — Preset Type Dispatcher
  └─ switch(20 cases, 0~0x1d)
     └─ case 4 → FUN_0816f748() — Preset Load + CRC Check
        ├─ FUN_08158a38() — Preset Data Parser (6152B)
        │  ├─ switch(type): case 1~0xf (15 param types)
        │  ├─ switch(quant): case 3~8 (6 quantization steps)
        │  │   └─ values: 0x5555, 0x638d, 0x71c6, 0x38e3, 0x2aaa, 0x471c
        │  └─ switch(param_id): case 0~0xc4 (197 preset parameters)
        └─ FUN_08158854() — Parameter Default Init (458B, 11 loops)
     ├─ FUN_08184cd8() — Modulation Depth Calculator (466B)
     │  └─ params: 9, 5, 13, 29, 10 → NRPN 0xAE~0xB1 output
     └─ FUN_08184ec0() — Parameter Router (178B)
        └─ loop: NRPN 0x9E~0xAD (16 channels) → vtable dispatch
```

### FUN_0816f748 — Preset Load & Apply

**주소**: `0x0816F748` (420B)

프리셋 버퍼 레이아웃:
```
param_1 + 0x10 ~ param_1 + 0xD10: 프리셋 데이터 (0xD00 = 3328 bytes)
param_1 + 0xD10: CRC 체크섬 종료점
param_1 + 0x2C0: 파라미터 세트 A (35개 × 2 bytes = 70 bytes)
param_1 + 0x307: 파라미터 세트 B (1536개 × 1 byte = 1536 bytes)
param_1 + 0x906: 파라미터 세트 C (384개 × 2 bytes = 768 bytes)
param_1 + 0xD18/D1C/D20: vtable 포인터 (3개 write dispatch)
```

CRC 알고리즘: XOR-based checksum with bit rotation (byte-level, 4 rotations).

### FUN_08158a38 — Preset Data Parser

**주소**: `0x08158A38` (6152B)

3단계 switch 구조:
1. **Type dispatch** (`param_1 + 2`): case 1~0xf → 파라미터 타입별 처리
2. **Quantization dispatch** (`param_1 + 0x232/0x244/0x256`): case 3~8 → 6단계 양자화
   - 값: `0x5555` (1/3), `0x638d`, `0x71c6`, `0x38e3` (1/5), `0x2aaa` (1/6), `0x471c`
3. **Parameter ID dispatch**: case 0~0xc4 (197개 프리셋 파라미터)

모든 스케일링은 **Q15 고정소수점** (0x7FFF = 1.0) 기반. `* 0x7fff` 패턴이 modulation depth × source value 곱셈.

### XRef 복구 (바이너리 PC-relative 스캔)

Ghidra가 인식하지 못한 XRef를 기계어 레벨에서 복구:

| 함수 | BL Direct | Literal Pool |
|------|-----------|-------------|
| `FUN_08158a38` | **2 callers**: `0x081429D4`, `0x0816F890` | 0 |
| `FUN_0812d0dc` | **4 callers**: `0x0813931A`, `0x0813947E`, `0x0813F052`, `0x0813F13E` | 0 |
| `FUN_081253e8` | **1 caller**: `0x08122608` | 0 |
| mod_source_enum | 0 | 1 ref: `0x081B1DD0` |
| custom_assign_enum | 0 | 3 refs: `0x081AEAF0`, `0x081B0184`, `0x081B1658` |

### 13-Column Int16 배열 (20개 발견)

바이너리 `0x0812002E`~`0x08120054` 영역에서 20개의 13-column int16 배열 발견. 대표값:

```
0x0812002E: [0,0,0,0,0,0,0,0,0,0,4098,14193,2066]     (3 nonzero)
0x08120038: [0,0,0,0,0,4098,14193,2066,9349,2066,9353,2066,9357] (8 nonzero)
0x08120054: [9361,2066,9365,2066,0,0,0,0,0,0,0,0,0]  (3 nonzero)
```

→ **대각선 슬라이딩 윈도우 패턴**: 각 배열이 이전 배열보다 1칸 시프트. 13-column = 13개 destination. 이는 **Mod Matrix source→destination 매핑의 기본 레이아웃 템플릿**으로 추정.

### CM7 Mod Matrix 탐색 결과

CM7 바이너리 (524KB, 295 functions)에서 41개의 NEON+float_multiply 후보 탐색. Mod Matrix 7×13 루프 패턴은 **발견되지 않음**. 이는 CM7에서 modulation 계산이 **inline/unrolled**되거나 **정수 기반 Q15**로 처리됨을 의미. CM7의 주요 NEON 함수들은 모두 DSP 필터/오실레이터 처리.

### Mod Matrix 런타임 구조 요약

```
┌──────────────────────────────────────────────────────────┐
│ CM4 (Control)                                           │
│  FUN_081639bc: preset type dispatch                      │
│    → case 4: FUN_0816f748 (preset load)                  │
│      → FUN_08158a38 (parse 197 params, Q15 scaling)     │
│      → FUN_08184cd8 (mod depth calc, NRPN 0xAE~0xB1)   │
│      → FUN_08184ec0 (16-ch param route, NRPN 0x9E~0xAD)│
│  Mod Matrix 데이터: 13-column int16 arrays @ 0x0812002E  │
│  Source enum refs: 0x081B1DD0, 0x081AEAF0, 0x081B0184  │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ CM7 (DSP)                                               │
│  Mod Matrix 계산: inline/unrolled Q15 multiply          │
│  (7×13 loop 패턴 미발견 — 정적 언롤링 추정)              │
│  주요 NEON 함수: DSP 필터/오실레이터 (41개 후보)         │
└──────────────────────────────────────────────────────────┘
```

### 분석 한계

| 한계 | 원인 | 해결 시도 |
|------|------|----------|
| Mod Matrix runtime dispatch 부재 | CM7에서 inline/unrolled 처리 | v4 스크립트로 탐색했으나 패턴 미발견 |
| XRef 0개 (Ghidra) | stripped 바이너리 + Thumb2 | ✅ PC-relative 기계어 스캔으로 7개 XRef 복구 |
| CC→param indirect dispatch | vtable 기반 간접 호출 | ✅ vtable 패턴 분석 완료 (아래 참조) |

### CC→Param Indirect Dispatch 분석

`FUN_08184cd8`에서 vtable 기반 CC→param 매핑 확정:

```
vtable[3] (getter, offset 0xc):
  param_2=9   → Mod Wheel depth
  param_2=5   → (unknown param, depth calc)
  param_2=0xd → (unknown param, depth calc)
  param_2=0x1d → (unknown param, depth calc)

vtable[2] (setter, offset 0x8):
  NRPN 0xAE (CC#174) → Mod depth ch1
  NRPN 0xAF (CC#175) → Mod depth ch2
  NRPN 0xB0 (CC#176) → Mod depth ch3
  NRPN 0xB1 (CC#177) → Mod depth ch4
```

**결론**: CC→param 매핑은 vtable을 통한 간접 호출 (런타임 다형성). DAT_ 테이블 5개가 vtable 프록시를 가리키며, 실제 CC→param 매핑은 vtable 내부 함수에 캡슐화됨. 정적 분석으로는 vtable resolve가 불가능하므로, 이 항목은 **기기 런타임 분석 필요**로 분류.

### 검증 결과

| 항목 | 상태 | 근거 |
|------|------|------|
| Preset load 체인 | ✅ 확정 | FUN_081639bc→case4→FUN_0816f748→FUN_08158a38 |
| Preset 파라미터 수 | ✅ 확정 | 197개 (case 0~0xc4) |
| Q15 스케일링 | ✅ 확정 | 0x7FFF = 1.0, `* 0x7fff` 곱셈 패턴 |
| Mod depth NRPN 채널 | ✅ 발견 | 0xAE~0xB1 (FUN_08184cd8) |
| Param 라우팅 채널 | ✅ 발견 | 0x9E~0xAD 16ch (FUN_08184ec0) |
| 13-column 배열 | ✅ 발견 | 20개 @ 0x0812002E, 대각선 슬라이딩 패턴 |
| Source enum ref | ✅ 발견 | 0x081B1DD0 (literal pool) |
| Quantization steps | ✅ 발견 | 6 steps: 0x5555~0x471c |
| Runtime 7×13 dispatch | ⚠️ 한계 | CM7에서 언롤링 추정, 기기 없이 검증 불가 |

---

## 진행 상태

- [x] 9-7. Voice Allocator 분기 로직 디컴파일
- [x] 9-5. CM7 Ghidra 심층 분석 — 확률 LUT, Seq state machine, Smoothing IIR
- [x] 9-8. Mod Matrix dispatch 코드 분석
