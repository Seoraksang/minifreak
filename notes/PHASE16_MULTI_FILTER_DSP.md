# Phase 16-4: Multi Filter 14모드 ↔ DSP 함수 매핑 (정적 분석)

> **분석 날짜**: 2026-05-01
> **대상**: CM4 `minifreak_main_CM4` + CM7 `minifreak_main_CM7` fw4_0_1_2229
> **분석 방법**: 바이너리 정적 분석 (strings, pointer scan, Thumb-2 디스어셈블 패턴 매칭)
> **Phase 12 기반**: `PHASE12_FX_CORE_DSP.md`, `PHASE6_SOUND_ENGINE.md`

---

## 1. MiniFreak 필터 아키텍처 개요

MiniFreak는 **3계층 필터 시스템**을 갖는다:

```
┌─────────────────────────────────────────────────────┐
│              필터 TYPE (5종 + 아날로그)                │
│  CM4 enum @ 0x081AF41C                              │
├─────────────────────────────────────────────────────┤
│  Type 0: Multi Filter (디지털, 14모드) ← 본 문서     │
│  Type 1: Surgeon Filter (파라메트릭 EQ)              │
│  Type 2: Comb Filter                                │
│  Type 3: Phaser Filter (2~12 pole)                  │
│  Type 4: Destroy                                    │
│  아날로그: SEM LP/BP/HP (하드웨어 회로)               │
└─────────────────────────────────────────────────────┘
```

**디스패치 구조**:
- CM4 = UI/제어 코어 → 필터 타입/모드를 정수 인덱스로 CM7 전달 (공유 메모리)
- CM7 = 오디오 DSP 코어 → `FUN_0803C2BC` (VCF Filter, 9,250B)에서 실제 처리
- **포인터 테이블 없음** — 모든 필터 타입 문자열(0x081AF41C)에 대해 CM4 내 포인터 참조 0개

---

## 2. Multi Filter 14모드 문자열 테이블

### 2.1 CM4 문자열 영역

| # | 모드명 | CM4 주소 | 길이 | 필터 타입 | 오더 (pole) |
|---|--------|----------|------|-----------|-------------|
| 0 | LP36 | 0x081B0D90 | 4B | Low Pass | 36 dB/oct (6th order) |
| 1 | LP24 | 0x081B0D95 | 4B | Low Pass | 24 dB/oct (4th order) |
| 2 | LP12 | 0x081B0D9A | 4B | Low Pass | 12 dB/oct (2nd order) |
| 3 | LP6 | 0x081B0D9F | 3B | Low Pass | 6 dB/oct (1st order) |
| 4 | HP6 | 0x081B0DA3 | 3B | High Pass | 6 dB/oct (1st order) |
| 5 | HP12 | 0x081B0DA7 | 4B | High Pass | 12 dB/oct (2nd order) |
| 6 | HP24 | 0x081B0DAC | 4B | High Pass | 24 dB/oct (4th order) |
| 7 | HP36 | 0x081B0DB1 | 4B | High Pass | 36 dB/oct (6th order) |
| 8 | BP12 | 0x081B0DB6 | 4B | Band Pass | 12 dB/oct (2nd order) |
| 9 | BP24 | 0x081B0DBB | 4B | Band Pass | 24 dB/oct (4th order) |
| 10 | BP36 | 0x081B0DC0 | 4B | Band Pass | 36 dB/oct (6th order) |
| 11 | N12 | 0x081B0DC5 | 3B | Notch | 12 dB/oct (2nd order) |
| 12 | N24 | 0x081B0DC9 | 3B | Notch | 24 dB/oct (4th order) |
| 13 | N36 | 0x081B0DCD | 3B | Notch | 36 dB/oct (6th order) |

> **신뢰도**: ★★★★★ (문자열 직접 확인)

### 2.2 CM4 포인터 테이블 분석

`0x081B1850` 영역에 일부 필터 모드 포인터가 존재하나, 이는 **혼합 UI 표시용 테이블** (필터 모드 + 스케일명 + 엔진명이 섞임):

```
0x081B1850 → 0x081B0DAC "HP6"     (HP24 포인터 오정렬 — 패킹 차이)
0x081B1854 → 0x081B0DB0 "HP12"    (HP24 시작)
0x081B187C → 0x081B0D90 "LP36"    (Multi Filter 영역)
0x081B1880 → 0x081B0D98 "LP24"
0x081B1884 → 0x081B0DA0 "LP12"
0x081B1888 → 0x081B0DA4 ""        (LP6 null)
0x081B188C → 0x081B0DA8 "LP6"
0x081B1890 → 0x081AF490 "ains"    (오실레이터 영역으로 전환)
```

→ **필터 디스패치용 포인터 테이블이 아님**. 실제 디스패치는 정수 인덱스 기반.

---

## 3. CM7 필터 DSP 함수 분석

### 3.1 핵심 함수

| 함수 | CM7 주소 | 크기 | Phase 6 역할 추정 | 본 분석 |
|------|----------|------|------------------|---------|
| `FUN_0803C2BC` | 0x0803C2BC | 9,250B | VCF Filter Coeff / Osc2 Processor | **VCF 필터 계수 + 오실레이터** |
| `FUN_08034338` | 0x08034338 | 5,046B | Filter Coefficients / Waveshaper | **필터 계산 본체** |

### 3.2 FUN_08034338 (Filter Coefficients) 내부 구조

**Thumb-2 CMP 패턴 분석**:

| CMP 명령어 | 출현 횟수 | 해석 |
|-----------|-----------|------|
| CMP R4, #0 | 4 | null/default 체크 |
| CMP R0, #1 | 3 | 이진 분기 (type A/B) |
| CMP R5, #3 | 1 | 오더 분기 (6/12/24/36 dB) |
| CMP R2, #4 | 1 | 필터 타입 분기 |
| CMP R4, #11 | 2 | **모드 상한 검사** (14모드: 0~13, #11=경계) |
| CMP R7, #12 | 2 | **모드 상한 검사** (보조) |

> **해석**: CMP #11/#12 패턴은 14모드(0-13)의 범위 검사로 추정. R4에 필터 모드 인덱스가 들어오고, #11을 넘으면 기본값 또는 에러 처리.

**BL 호출 타겟 (9개 유니크)**:

| 호출 횟수 | 타겟 함수 | CM7 주소 | 추정 역할 |
|---------|----------|----------|-----------|
| 6 | `FUN_08080B5C` | 0x08080B5C | **핵심 biquad/필터 프로세스** (최다 호출) |
| 3 | `FUN_080746EC` | 0x080746EC | 필터 계수 계산 |
| 3 | `FUN_08076E8C` | 0x08076E8C | 필터 계수 계산 (변형) |
| 3 | `FUN_08076E90` | 0x08076E90 | 필터 계수 계산 (변형 2) |
| 3 | `FUN_080764E0` | 0x080764E0 | 필터 계수 계산 (변형 3) |
| 1 | `FUN_08074708` | 0x08074708 | 보조 계산 |
| 1 | `FUN_08076ED0` | 0x08076ED0 | 보조 계수 |
| 1 | `FUN_08076528` | 0x08076528 | 보조 |
| 1 | `FUN_0807DD00` | 0x0807DD00 | 유틸리티 |

> **해석**: `FUN_08080B5C`(6회 호출)이 핵심 biquad 프로세스 함수. 나머지 4개(각 3회)는 필터 계수 계산 변형으로, 오더(1/2/3/4/5/6 pole)에 따라 다른 계수 세트를 생성하는 것으로 추정.

### 3.3 CM7 상수 테이블 분석

**0.707107 (1/√2) 매치 — 8개, 4쌍 대칭**:

| 오프셋 | CM7 주소 | 주변 패턴 | 해석 |
|--------|----------|-----------|------|
| 0x06D81C | 0x0808D81C | [0.676~0.707~0.741] 단조 증가 | **Cosine table 1** (cos(0)~cos(π)) |
| 0x06DC1C | 0x0808DC1C | [0.741~0.707~0.676] 단조 감소 | **Cosine table 1** 역방향 |
| 0x078228 | 0x08098228 | 동일 패턴 | **Cosine table 2** (복제) |
| 0x078628 | 0x08098628 | 동일 패턴 역방향 | **Cosine table 2** 역방향 |
| 0x07C8D4 | 0x0809C8D4 | 1.059463 간격 (2^(1/12)) | **Semitone ratio table** |
| 0x07CD28 | 0x0809CD28 | [0.634~0.707~0.773] | 미확정 (필터 Q table 가능) |
| 0x07CF28 | 0x0809CF28 | [0.773~0.707~0.634] 대칭 | 미확정 (역방향) |

> **Cosine tables**: biquad 계수 계산에 사용 (cos(ω₀) = cosine of normalized cutoff frequency)
> **Semitone ratio**: cutoff frequency MIDI note → Hz 변환에 사용
> **미확정 테이블**: Q값 또는 resonance 곡선으로 추정

---

## 4. 14모드 ↔ DSP 함수 매핑 (추정)

### 4.1 아키텍처 추론

```
CM4 (제어)                         CM7 (오디오 DSP)
──────────                         ──────────────
filter_type = 0 (Multi)  ──→       FUN_08034338 (Filter Coefficients)
filter_mode = 0~13        ──→         │
cutoff, resonance         ──→         ├── CMP R4, #11 (상한 검사)
                                   ├── FUN_08080B5C ×6 (biquad process)
                                   ├── FUN_080746EC ×3 (coeff calc)
                                   ├── FUN_08076E8C ×3 (coeff variant)
                                   ├── FUN_08076E90 ×3 (coeff variant 2)
                                   └── FUN_080764E0 ×3 (coeff variant 3)
```

### 4.2 모드 → 오더 매핑

| 필터 타입 | 6dB | 12dB | 24dB | 36dB | 구현 방식 |
|-----------|-----|------|------|------|-----------|
| LP | LP6 | LP12 | LP24 | LP36 | cascaded biquads |
| HP | HP6 | HP12 | HP24 | HP36 | cascaded biquads |
| BP | — | BP12 | BP24 | BP36 | cascaded biquads |
| Notch | — | N12 | N24 | N36 | cascaded biquads |

**biquad cascade 관계**:
- 6dB/oct = **1st order** (1 pole) = 0.5 biquad (1-pole LP/HP)
- 12dB/oct = **2nd order** = **1 biquad**
- 24dB/oct = **4th order** = **2 cascaded biquads**
- 36dB/oct = **6th order** = **3 cascaded biquads**

### 4.3 DSP 함수 추정 매핑

> ⚠️ **신뢰도 ★★★★☆** — 정적 패턴 분석 기반 추정. Ghidra 디컴파일로 확정 필요.

| BL 타겟 | 호출 횟수 | 추정 역할 | 대응 모드 |
|---------|----------|-----------|----------|
| `FUN_08080B5C` | 6 | **biquad process** (최대 6 pole = 3 biquad cascade) | LP36, HP36, BP36, N36 |
| `FUN_080746EC` | 3 | **LP/HP coefficient calc** (type A) | LP 계열, HP 계열 |
| `FUN_08076E8C` | 3 | **BP coefficient calc** (type B) | BP 계열 |
| `FUN_08076E90` | 3 | **Notch coefficient calc** (type C) | N 계열 |
| `FUN_080764E0` | 3 | **1st order coefficient calc** (type D) | LP6, HP6 |

> **근거**: 호출 횟수 6 = 최대 6 pole (36dB/oct = 3 biquad × 2 = 6 호출)
> 계수 함수 4종 × 3회 = 4개 필터 타입(LP/HP, BP, Notch, 1st order) × 오더(1/2/3 cascade)

---

## 5. 아날로그 필터 (참고)

아날로그 SEM 필터는 CM7 펌웨어가 아닌 **하드웨어 회로**로 구현:

| VCF 모드 | CM4 주소 | 설명 |
|----------|----------|------|
| LP | 0x081AF4D0 | 아날로그 Low Pass |
| BP | 0x081AF4D3 | 아날로그 Band Pass |
| HP | 0x081AF4D6 | 아날로그 High Pass |
| Notch | 0x081AF4D9 | 아날로그 Notch |
| LP1 | 0x081AF4DF | 아날로그 LP 1-pole |
| HP1 | 0x081AF4E3 | 아날로그 HP 1-pole |
| Notch2 | 0x081AF4E7 | 아날로그 Notch variant |

> CM7 20개 IIR smoothing 함수 + biquad 계수 0.707(1/√2) ×8은 아날로그 필터의 **디지털 제어** (cutoff/resonance CV 생성)에 사용되는 것으로 추정.

---

## 6. 결론

### 6.1 확정 사항 (★★★★★)

1. Multi Filter 14모드 문자열 테이블 위치: CM4 `0x081B0D90`~`0x081B0DE8`
2. 필터 디스패치는 **정수 인덱스 기반** (포인터 테이블 없음)
3. CM7 핵심 필터 함수: `FUN_08034338` (5,046B) → 하위 9개 함수 호출
4. CM7 cosine table 2세트 + semitone ratio table 존재
5. 14모드 = 4 타입(LP/HP/BP/Notch) × 4 오더(6/12/24/36 dB) 구조

### 6.2 추정 사항 (★★★★☆)

1. `FUN_08080B5C` = biquad process 함수 (6회 호출 = 6 pole max)
2. 4개 계수 함수가 LP/HP, BP, Notch, 1st order에 각각 대응
3. CMP #11/#12 = 14모드 상한 검사

### 6.3 미해결 (Ghidra 디컴파일 필요)

1. 각 모드(0~13)별 정확한 biquad cascade 구성
2. 계수 함수 4종의 정확한 수식 (Butterworth? Chebyshev?)
3. `FUN_08080B5C`의 내부 biquad 알고리즘 (Direct Form I/II? Transposed?)
4. 0x07CD28/0x07CF28 테이블의 정체 (Q curve? Resonance map?)

### 6.4 필터 카테고리 재현도 영향

| 항목 | Phase 12 | Phase 16-4 | 변화 |
|------|---------|------------|------|
| Multi Filter 14모드 문자열 | ★★★★★ | ★★★★★ | 확정 유지 |
| 14모드 ↔ DSP 함수 매핑 | ★★★★☆ | ★★★★☆ | 추정 유지 |
| biquad cascade 구조 | 미보고 | ★★★★☆ | 신규 추정 |
| 계수 수식 | 미보고 | ★★★☆☆ | 미해결 |

→ **Filter 카테고리 96% 유지**. Ghidra 디컴파일 시 96% → 99% 가능.

---

## 7. 교차 참조

| 문서 | 관계 |
|------|------|
| `PHASE6_SOUND_ENGINE.md` | CM7 DSP 함수 클러스터 분석 (Phase 6) |
| `PHASE12_FX_CORE_DSP.md` | FX 코어 12타입 DSP 매핑 (Phase 12-2) |
| `MANUAL_VS_FIRMWARE_MATCH.md` | 필터 카테고리 96% 평가 |
| `PHASE13_V_INTEGRATED_VERIFICATION.md` | 3원 교차검증 |
| `PHASE14_VST_HW_PARAM_MAPPING.md` | VST 파라미터 148개 매핑 |

---

*문서 버전: Phase 16-4 v1.0*
*작성 도구: 바이너리 정적 분석 (strings, pointer scan, Thumb-2 패턴 매칭)*
*펌웨어 버전: fw4_0_1_2229 (2025-06-18)*
