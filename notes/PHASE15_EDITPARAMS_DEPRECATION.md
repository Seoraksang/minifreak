# MiniFreak eEditParams Deprecated/사용슬롯 분석

**Phase 15-1** | 2026-05-01 | 펌웨어 fw4_0_1_2229 바이너리 직접 스캔

---

## 개요

eEditParams는 MiniFreak 펌웨어 CM4 코어에서 **편집 모드 파라미터**를 정의하는 C++ enum이다.
MNF_Edit 클래스의 `set()` 메서드에서 switch/case로 디스패치된다.

| 항목 | 값 |
|------|-----|
| **MNF_Edit::set() RTTI** | `0x081aa101` (CM4 Flash) |
| **문자열 클러스터** | `0x081AF904` ~ `0x081AFC34` |
| **총 항목 수** | **79개** (문자열 기준) |
| **활성 파라미터** | 27개 |
| ★ **DEPRECATED** | 1개 (`UnisonOn TO BE DEPRECATED`) |
| **Obsolete** | 1개 (`obsolete Rec Count-In`) |
| **UI 상태 플래그** | 16개 (프리셋 미저장) |
| **UI 라벨/상수** | 35개 (프리셋 미저장) |

> **교차참조**: [PHASE8_ESYNTHPARAMS_ENUM.md](PHASE8_ESYNTHPARAMS_ENUM.md) — eEditParams 포함 9개 enum 체계

---

## 전체 목록

### 활성 파라미터 (27개) — 프리셋 저장 대상

| idx | 주소 | 이름 |
|-----|------|------|
| 0 | `0x081AF904` | Macro1 dest |
| 1 | `0x081AF910` | Macro2 dest |
| 2 | `0x081AF91C` | Macro1 amount |
| 3 | `0x081AF92C` | Macro2 amount |
| 4 | `0x081AF93C` | Retrig Mode |
| 5 | `0x081AF948` | Legato Mono |
| 6 | `0x081AF954` | Unison Count |
| 7 | `0x081AF964` | Poly Allocation |
| 8 | `0x081AF974` | Poly Steal Mode |
| 9 | `0x081AF984` | Vibrato Depth |
| 10 | `0x081AF994` | **UnisonOn TO BE DEPRECATED** ★ |
| 11 | `0x081AF9B0` | Matrix Src VeloAT |
| 12 | `0x081AF9C4` | Osc1 Mod Quant |
| 13 | `0x081AF9D4` | Osc2 Mod Quant |
| 14 | `0x081AF9E4` | Release Curve |
| 15 | `0x081AF9F4` | Osc Mix Non-Lin |
| 16 | `0x081AFA04` | Glide Sync |
| 17 | `0x081AFA10` | Pitch 1 |
| 18 | `0x081AFA18` | Pitch 2 |
| 19 | `0x081AFA20` | Velo > VCF |
| 20 | `0x081AFA2C` | Kbd Src |
| 21 | `0x081AFA34` | Unison Mode |
| 22 | `0x081AFA40` | Osc Free Run |
| 29 | `0x081AFA84` | Octave Tune |
| 30 | `0x081AFA90` | Tempo Div |
| 38 | `0x081AFAF0` | Seq Transpose |
| 42 | `0x081AFB38` | Pre Master Volume |

### ★ DEPRECATED / Obsolete (2개)

| idx | 주소 | 이름 | 상태 | 비고 |
|-----|------|------|------|------|
| 10 | `0x081AF994` | **UnisonOn TO BE DEPRECATED** | ★ DEPRECATED | Arturia 개발자 명시적 마크. 유니즌 온/오프 → Unison Count/Mode로 대체됨 |
| 39 | `0x081AFB00` | **obsolete Rec Count-In** | Obsolete | 녹음 카운트인 기능 — 더 이상 사용되지 않음 |

### UI 상태 플래그 (16개) — 프리셋 미저장

| idx | 주소 | 이름 | 용도 |
|-----|------|------|------|
| 23 | `0x081AFA50` | Mx Cursor | 모듈레이션 매트릭스 커서 위치 |
| 24 | `0x081AFA5C` | Mx Page | 모듈레이션 매트릭스 페이지 |
| 25 | `0x081AFA64` | Mx Mode | 모듈레이션 매트릭스 모드 |
| 26 | `0x081AFA6C` | Osc Sel | 오실레이터 선택 상태 |
| 27 | `0x081AFA74` | Fx Sel | FX 선택 상태 |
| 28 | `0x081AFA7C` | Lfo Sel | LFO 선택 상태 |
| 31 | `0x081AFA9C` | Seq Page | 시퀀서 페이지 |
| 32 | `0x081AFAA8` | PlayState | 재생 상태 |
| 33 | `0x081AFAB4` | RecState | 녹음 상태 |
| 34 | `0x081AFAC0` | RecMode | 녹음 모드 |
| 35 | `0x081AFAC8` | Cursor | 일반 커서 위치 |
| 36 | `0x081AFAD0` | MetronomeBeat | 메트로놈 비트 |
| 37 | `0x081AFAE0` | Playing Tempo | 현재 재생 템포 |
| 40 | `0x081AFB18` | Preset filter | 프리셋 필터 문자열 |
| 41 | `0x081AFB28` | VST_IsConnected | VST3 플러그인 연결 상태 |
| 43 | `0x081AFB4C` | Favorites Page | 즐겨찾기 페이지 |

### UI 라벨/상수 (35개) — 프리셋 미저장

음이름(C, C#, D#, E, F, F#, G, G#, A#), 모듈레이션 소스 라벨(Pitch, Wave, Timb, CycEnv, LFO 1, LFO 2, Velo/AT, Keyb, Timbre), Assign1~9, L1, L2, V/A, W, K 등.

---

## 안전한 펌웨어 패치 슬롯 (우선순위순)

### 1순위: 명시적 DEPRECATED/OBSOLETE

| 슬롯 | 이름 | 안전성 이유 |
|------|------|------------|
| ★ `UnisonOn TO BE DEPRECATED` | 유니즌 온/오프 (구) | Arturia 개발자가 명시적으로 DEPRECATED 마크. Unison Count/Mode로 이미 대체됨. 기존 기능 유지 불필요 |
| ★ `obsolete Rec Count-In` | 녹음 카운트인 | "obsolete" 명시. 더 이상 호출되지 않음 |

### 2순위: UI 상태 플래그

| 슬롯 | 이름 | 안전성 이유 |
|------|------|------------|
| `VST_IsConnected` | VST 연결 상태 | 프리셋 미저장. 하드웨어 단독 동작 시 무효 |
| `Cursor` / `Mx Cursor` | UI 커서 | 프리셋 미저장. 디스플레이 전용 |
| `PlayState` / `RecState` / `RecMode` | 재생/녹음 상태 | 프리셋 미저장. 런타임 상태 |
| `Osc Sel` / `Fx Sel` / `Lfo Sel` | 선택 상태 | 프리셋 미저장. UI 전용 |
| `MetronomeBeat` | 메트로놈 | 프리셋 미저장 |
| `Playing Tempo` | 재생 템포 | 프리셋 미저장 |

---

## VST XML 교차 검증

VST `minifreak_vst_params.xml`에서 `savedinpreset="0"`인 파라미터:

| 파라미터 | 비고 |
|----------|------|
| `Pitch1_Mod_On` | eSynthParams (eEditParams 아님) |
| `Pitch2_Mod_On` | eSynthParams (eEditParams 아님) |

> eEditParams 자체는 VST XML에 노출되지 않음 — CM4 UI 전용 enum이므로 VST 연동 영향 없음.

---

## 펌웨어 이스터에그

바이너리 스캔 중 발견된 개발자 메시지:

| 주소 | 메시지 |
|------|--------|
| `0x081B34A4` | "If you ask Olivier D, he'll tell you that it's a feature" |
| `0x081B3298` | "...but the developpers never implement what I specify... Ask Thomas A" |
| `0x081B33E8` | "...has a solution. If it's not about math, ask Mathieu B" |
| `0x081B2F42` | "Hey Frederic, are you ready to hear sounds you never heard before?" |

---

## 향후 작업

1. **Ghidra에서 MNF_Edit::set() switch/case 분석** → 실제 eEditParams enum 인덱스 확정
   - 현재 idx는 문자열 클러스터 내 순서이며, enum 값과 다를 수 있음
2. **Phase 15-2**: 안전한 패치 정의 JSON 작성 + mf_patch.py 구현
3. **Phase 15-3**: 바이너리 패치 실제 테스트 (플래싱 없이 검증)

---

*MiniFreak Reverse Engineering — Phase 15-1*
*Related: [PHASE8_ESYNTHPARAMS_ENUM.md](PHASE8_ESYNTHPARAMS_ENUM.md), [PHASE6_FIRMWARE_PATCH_ASSESSMENT.md](PHASE6_FIRMWARE_PATCH_ASSESSMENT.md), [REVERSE_MASTER_PLAN.md](REVERSE_MASTER_PLAN.md)*
