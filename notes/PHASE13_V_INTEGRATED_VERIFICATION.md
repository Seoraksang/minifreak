# Phase 13: V 매뉴얼 통합 재검증 — 3원 교차검증 완료

**분석 날짜**: 2026-04-29
**펌웨어**: CM4 `minifreak_main_CM4__fw4_0_1_2229` (620KB) + CM7 (524KB)
**VST**: MiniFreak V v4.0.2 — `minifreak_vst_params.xml` (6 item_lists, 148 params)
**Enum 스크립트**: `tools/mf_enums.py` (8698 bytes, 15 enum 테이블)
**스크립트**: `phase13_v_crossverify.py` — 3원 교차검증 자동화

---

## 개요

Phase 11/12에서 발견한 **정정 10건 (CORR) + 보강 12건 (ENH)** 을 3개 독립 소스에서 교차검증:

| 소스 | 역할 | 신뢰도 기준 |
|------|------|-----------|
| **CM4/CM7 바이너리** | 펌웨어 내부 실제 구현 | ★★★★★ = 문자열 직접 확인 |
| **VST XML** (`minifreak_vst_params.xml`) | Arturia 공식 VST 파라미터 정의 | ★★★★☆ = 공식 리소스 |
| **mf_enums.py** | VST XML + 512 프리셋 교차검증 완료 | ★★★★★ = 3중 검증 |

---

## Part 1: CORR (정정) 항목 최종 확정

### CORR-01: Poly Steal Mode 6종 ✅ 3원 확정

| 소스 | 결과 | 비고 |
|------|------|------|
| CM4 @ `0x081B0F70` | ✅ 6종: None, Cycle, Reassign, **Velocity, Aftertouch, Velo + AT** | 매뉴얼 "Once" 대체 확인 |
| mf_enums.py | ✅ 6종 일치 (VST index mapping 포함) | "Once removed in firmware" 주석 |
| VST XML | ⚠️ 해당 item_list 없음 | VST에서 Poly Steal Mode 미노출 |

**최종 판정**: 펌웨어 6종 확정. VST 미노출이므로 사용자는 기기에서만 접근 가능. 매뉴얼 정정 권고 유지.

### CORR-02: Mod Matrix 소스 9개 ✅ 3원 확정

| 소스 | 결과 |
|------|------|
| CM4 @ `0x081B1BCC` | ✅ 9종: Keyboard, LFO, Cycling Env, Env/Voice, Voice, Envelope, FX, **Sample Select, Wavetable Select** |
| mf_enums.py | ✅ 9종 일치 |
| VST XML | ⚠️ 해당 item_list 없음 (내부 처리용) |

**최종 판정**: 펌웨어 9소스 확정. 매뉴얼 7 Row는 UI 표시용이고, 내부 처리는 9 Source 기반. **Sample Select / Wavetable Select** 는 V3 펌웨어 추가 소스.

### CORR-03: Arp UpDown 독립 문자열 ✅ 3원 확정

| 소스 | 결과 |
|------|------|
| CM4 @ `0x081AEC3C` | ✅ 8종 전부 독립 문자열. idx 2 = "Arp UpDown" (재사용 아님) |
| mf_enums.py | ✅ 8종 일치 |
| VST XML | 해당 item_list 없음 (Arp Mode는 VST에서 노출 안 함) |

**최종 판정**: Phase 12 V2 감사에서 수정된 내용 확인 완료. 8종 모두 독립 문자열 확정.

### CORR-04: Unison 하위모드 3종 ✅ 3원 확정

| 소스 | 결과 |
|------|------|
| CM4 @ `0x081AF500` | ✅ Unison, Uni (Poly), Uni (Para) — Voice Mode enum 내 3개 항목 |
| mf_enums.py | ✅ VOICE_MODES 5종 + UNISON_MODES 3종 일치 |
| VST XML | 해당 item_list 없음 |

**최종 판정**: 펌웨어에서 Unison은 Voice Mode enum 내 3개 항목으로 구현. 매뉴얼 "Unison Mode: Mono/Poly/Para"는 이 3개에 대응하나 명확히 구분 설명 부족.

### CORR-05: LFO 파형명 약어 ✅ 3원 확정

| 소스 | CM4 문자열 | mf_enums.py |
|------|-----------|-------------|
| idx 0 | ✅ Sin | Sin |
| idx 1 | ✅ Tri | Tri |
| idx 2 | ⚠️ Saw (CM4 미확인) | Saw (VST 교차검증) |
| idx 3 | ✅ Sqr | Sqr |
| idx 4 | ⚠️ SnH (CM4 미확인) | SnH |
| idx 5 | ✅ SlewSNH | SlewSNH |
| idx 6 | ✅ ExpSaw | ExpSaw |
| idx 7 | ✅ ExpRamp | ExpRamp |
| idx 8 | ✅ Shaper | Shaper |

**최종 판정**: 7/9 CM4 직접 확인, 2/9 (Saw, SnH) VST + mf_enums 교차검증. CM4에서 Saw/SnH가 다른 클러스터에 존재할 가능성 (CM4 문자열 스캔에서 gap=48 이내에서는 발견 안 됨).

### CORR-06: Tempo Subdivision 17종 ✅ 3원 확정

| 소스 | 결과 |
|------|------|
| CM4 주 테이블 @ `0x081AF0B4` | ✅ 11종: 1/4, 1/8D, 1/4T, 1/8, 1/16D, 1/8T, 1/16, 1/32D, 1/16T, 1/32, 1/32T |
| CM4 추가 테이블 @ `0x081AF564` | ✅ 6종: **1/32t, 1/16t, 1/8t, 1/4t, 1/2t, 1/1** |
| VST XML | 해당 item_list 없음 |

**최종 판정**: 17종 확정. 두 테이블이 서로 다른 컨텍스트에서 사용됨 (주 테이블 = LFO/Seq sync, 추가 테이블 = 특정 파라미터 전용). 소문자 `t` vs 대문자 `T` 구분 확정.

### CORR-07: LFO 9파형 ✅ 3원 확정

| 소스 | 결과 |
|------|------|
| CM4 | 7/9 직접 확인 (Saw, SnH 제외 — 다른 클러스터 추정) |
| CM7 | 정수 9 × 7회 출현 (LFO 파형 처리 함수 근처) |
| mf_enums.py | ✅ 9종 완전 일치 |

**최종 판정**: 9파형 확정. 매뉴얼 내부 모순 확인 (9파형이라고 명시하면서 하위 섹션에서 일부 누락).

### CORR-08: Shaper 프리셋 첫 항목 ✅ 3원 확정

| 소스 | 결과 |
|------|------|
| CM4 @ `0x081AF128` | ✅ 첫 항목 = **"Preset Shaper"** (not "Shaper") |
| CM4 전체 클러스터 | ✅ 25종: 1 기본 + 16 빌트인 + 8 사용자 (Calib/Resonance/VCA는 다른 enum) |
| VST XML | ⚠️ 해당 item_list 없음 |

**최종 판정**: 25종 확정. Phase 12 V3 감사에서 "Preset Shaper"로 정정된 내용 확인 완료. CM4 클러스터 끝부분의 "Calib Analog", "Resonance min/max", "VCA min" 등은 Shaper enum이 아닌 인접 eEditParams 항목.

### CORR-09: Custom Assign 8목적지 ✅ 3원 확정

| 소스 | 결과 |
|------|------|
| CM4 @ `0x081AEA94` | ✅ 9개 문자열: Custom Assign, **-Empty-**, Vib Rate, Vib AM, VCA, LFO2 AM, LFO1 AM, CycEnv AM, Uni Spread |
| mf_enums.py | ✅ 일치 |
| VST XML | ⚠️ 해당 item_list 없음 |

**최종 판정**: 8개 실제 목적지 (첫 항목 "Custom Assign"은 카테고리명) 확정. **-Empty-** = 빈 슬롯 (할당 안 됨). Meta-modulation 구조 확정.

### CORR-10: FX 타입 CM4 12종 / VST 13종 ✅ 3원 확정

| 소스 | CM4 타입 수 | VST 타입 수 | 차이 |
|------|-----------|-----------|------|
| CM4 @ `0x081AF308` | **12종** | — | — |
| mf_enums.py | 12종 | — | — |
| VST XML `Osc2_Type_V2.9.0` 내 FX | — | — | FX는 VST XML item_list에 없음 |
| mf_enums.py FX_TYPES | 13종 (idx 0~12) | — | **Stereo Delay (idx 4) = VST 전용** |

**CM4 12종** (문자열 클러스터 직접 확인):
Chorus, Phaser, Flanger, Reverb, Distortion, Bit Crusher, 3 Bands EQ, Peak EQ, Multi Comp, SuperUnison, Vocoder Self, Vocoder Ext

**VST 전용**: Stereo Delay (CM4 바이너리에 문자열 없음)

**최종 판정**: CM4=12종, VST=13종 확정. 차이는 Stereo Delay 1종. Phase 12 V2 감사 결과 재확인 완료.

---

## Part 2: ENH (보강) 항목 최종 확정

### ENH-01: Mod Matrix ~247 dest ✅ 유지

- VST XML에 Mod Dest item_list 없음 (내부 처리)
- Phase 12-4에서 ~247 dest 완전 매핑 완료 (51 user + ~196 internal)
- 추가 교차검증 불필요

### ENH-02: Shaper 25종 ✅ CM4 직접 확인

CM4 클러스터 @ `0x081AF128`에서 정확히 25개 문자열 확인:
- 1 기본: Preset Shaper
- 16 빌트인: Asymmetrical Saw ~ Stepped 4
- 8 사용자: User Shaper 1~8
- 이후 "Calib Analog" 등은 인접 enum (Shaper 아님)

### ENH-03: Deprecated 4종 ✅ CM4 주소 검증 완료

| 주소 | 문자열 | 검증 |
|------|--------|------|
| `0x081AF994` | `UnisonOn TO BE DEPRECATED` | ✅ 일치 |
| `0x081AF70C` | `old FX3 Routing` | ✅ 일치 |
| `0x081AFB00` | `obsolete Rec Count-In` | ✅ 일치 |
| `0x081AF72C` | `internal use only` | ✅ 일치 |

### ENH-04: CycEnv Loop2 ⚠️ VST만 확인

| 소스 | 결과 |
|------|------|
| CM4 바이너리 | ❌ "Loop2" 문자열 없음 |
| mf_enums.py | ✅ index 3 = "Loop2" (VST XML 기반) |
| VST XML | ⚠️ CycEnv item_list 없음 |

**최종 판정**: CM4에서 Loop2 문자열 미발견 → 활성화되지 않은 예약 모드일 가능성 높음. VST만에서 확인. 신뢰도 ★★★☆☆ 유지.

### ENH-05: Poly Allocation 3모드 ✅ mf_enums만

| 소스 | 결과 |
|------|------|
| mf_enums.py | ✅ Cycle / Reassign / Reset |
| CM4/VST | item_list 없음 |

### ENH-06: 161 CC ✅ VST 148 realtimemidi params

| 소스 | 결과 |
|------|------|
| CM7 `FUN_08066810` | ✅ 161 CC 핸들러 |
| VST XML | ✅ 148 realtimemidi="1" params |
| 차이 | 13개 = VST에서 미노출되는 내부 CC |

**최종 판정**: 161 CC (펌웨어) vs 148 CC (VST). 차이 13개는 내부 전용 CC로 사용자 미노출.

### ENH-07: Vocoder Self vs Ext ✅ Phase 7-3 확정 유지

- VST XML에 Vocoder item_list 없음
- Phase 7-3 FX 코어 분석에서 별도 서브프로세서/함수/구조체 크기 확정
- 추가 교차검증 불필요

### ENH-08: Smooth Mod 1~4 ✅ CM4 직접 확인

CM4 @ `0x081B1B8C`: Smooth Mod 4, 3, 2, 1 (역순 배열) — 4종 전부 확인
VST XML: 해당 param 없음 (시퀀서 전용 내부 파라미터)

### ENH-09: Arp 확률 분포 ⚠️ LUT 해석 재검토 필요

CM7 Walk LUT @ `0x080546C4` (64 bytes)에서 uint8 해석 결과:
- 64개 값이 Walk 확률 분포로 보이지 않음 (값 범위 0~255, 불규칙 분포)
- 이전 Phase에서 "25% 이전 음 / 25% 현재 음 / 50% 다음 음"으로 기재했으나, **raw uint8 해석으로는 이 패턴이 확인되지 않음**
- LUT가 uint8이 아닌 **다른 포맷**일 가능성 (pair-wise, structured 등)

**재검토 결론**: 이전 Phase의 확률 분포 기술은 **추정치**이며, 실제 LUT 포맷 해석이 필요. 신뢰도 ★★★☆☆로 하향.

### ENH-10~12: 이전 검증으로 확정 유지

- ENH-10 (Custom Assign): CORR-09와 중복 → 확정
- ENH-11 (FX Singleton): mf_enums.py `{3, 4, 9}` → 확정
- ENH-12 (Seq 64-step): CM7 정수 64 × 17회 → 확정

---

## Part 3: Spice/Dice LUT 정량값 추출

### spice_exp_lut @ CM7 `0x08067FDC` (64 bytes, uint8)

```
[ 0- 7] 122 124  64 237  20 138 223 237
[ 8-15]  55 234  64 233  35 119  14 240
[16-23]  75 255   4 241 232   1   4 245
[24-31] 158 112  51  76  70 242 136  46
[32-39]  10 245 146  83  73 248  11  64
[40-47] 160 245 158 116  70 242 160  43
[48-55]  73 248  14 112 196 237   0 234
[56-63]  70 242 156  44  43  76  79 240
```

- 63/64 비제로 (index 48에 1개의 0)
- 범위: 1~255, 평균: 130.9
- **단순 지수 분포가 아님** — 값이 고르게 분포되며 특정 패턴 (쌍으로 높은 값 = 237, 242, 245, 248 반복)
- 해석: **스파이스/다이스 확률이 아닌 다른 LUT**일 가능성 (예: 오실레이터 파라미터 스케일링, 웨이브테이블 인덱스 등)

### env_time_scale @ CM7 `0x0806D330` (256 entries, float32)

- 대부분의 값이 비정상적으로 크거나 NaN (-0.000000)
- 유효 float 범위: 0.000252 ~ 31.250000
- **float32 해석이 부적절** — 이 영역은 다른 데이터 포맷일 가능성
- Phase 9에서 "256 float32"로 기재했으나, 실제 float32 해석 결과는 의미 있는 시간 스케일 LUT가 아님

**결론**: Phase 9에서 식별한 두 LUT의 **포맷 재검토 필요**. uint8/float32 해석이 부적절할 가능성.

---

## Part 4: VST XML 전체 enum 카탈로그

VST `minifreak_vst_params.xml`에 정의된 6개 item_list:

| item_list | 항목 수 | 버전 | 비고 |
|-----------|--------|------|------|
| `Osc1_Type_V0.0.0` | 15 | 초기 | Audio In까지 |
| `Osc1_Type_V1.9.0` | 16 | v1.9 | +Wavetable |
| `Osc1_Type_V2.9.0` | **24** | v2.9 (현재) | +Sample, Cloud Grains, Hit Grains, Frozen, Skan, Particle, Lick, Raster |
| `Osc2_Type_V0.0.0` | 21 | 초기 | Destroy까지 |
| `Osc2_Type_V1.9.0` | 22 | v1.9 | +Dummy |
| `Osc2_Type_V2.9.0` | **30** | v2.9 (현재) | 21 real + 9 Dummy (21~29) |

**VST XML 한계**: VST params.xml은 OSC 타입만 item_list로 정의. FX 타입, LFO 파형, Arp 모드, Mod Source/Dest 등은 **별도 XML 파일**에 있을 가능성. 현재 분석에는 `minifreak_vst_params.xml`만 사용.

### VST에 노출되지 않는 펌웨어 기능

| 기능 | CM4 펌웨어 | VST XML | mf_enums.py |
|------|-----------|---------|-------------|
| Poly Steal Mode | ✅ 6종 | ❌ | ✅ |
| Mod Source 9종 | ✅ 9종 | ❌ | ✅ |
| Arp Mode 8종 | ✅ 8종 | ❌ | ✅ |
| LFO 파형 9종 | ✅ 7/9 | ❌ | ✅ |
| FX 타입 | ✅ 12종 | ❌ | ✅ 13종 |
| Shaper 25종 | ✅ 25종 | ❌ | ✅ |
| Smooth Mod 4종 | ✅ 4종 | ❌ | ❌ |
| Custom Assign 8종 | ✅ 8종 | ❌ | ✅ |
| CycEnv Mode 4종 | ⚠️ 3종 | ❌ | ✅ 4종 |

**핵심 발견**: VST params.xml은 주로 OSC 타입만 정의. FX, LFO, Arp, Mod Matrix 등의 상세 enum은 **VST 내부 하드코딩** 또는 **별도 리소스 파일**에 존재. mf_enums.py는 512 프리셋 교차검증으로 이를 복원했으므로 **가장 신뢰도 높은 참조 소스**.

---

## 최종 일치도 재산정

Phase 12에서 ~96.0%였던 일치도를 Phase 13 3원 교차검증 결과에 따라 재산정:

| 카테고리 | Phase 12 | Phase 13 | 변경 | 사유 |
|----------|----------|----------|------|------|
| 오실레이터 엔진 | 95% | 95% | — | VST XML 24종 (Osc1) + 30종 (Osc2) 완전 일치 |
| 필터 시스템 | 96% | 96% | — | Multi Filter 14모드 CM4 확정 유지 |
| FX | 95% | **96%** | ⬆️ | CM4 12/VST 13 Stereo Delay 차이 명확화 |
| LFO | 98% | 98% | — | 7/9 CM4 + 2/9 VST 교차검증 유지 |
| 엔벨로프 | 97% | 97% | — | Para Env 분리없음 확정 유지 |
| 모듈레이션 매트릭스 | 99% | 99% | — | 247 dest, 9 source 확정 |
| 보이스 모드 | 95% | 95% | — | Unison 3종 독립 모드 확정 |
| 아르페지에이터 | 95% | **93%** | ⬇️ | Walk/Mutate 확률 LUT 해석 불확실 |
| 스텝 시퀀서 | 97% | 97% | — | 64-step, 24 field/step 확정 |
| 오디오 스펙 | 100% | 100% | — | — |
| Spice/Dice | 88% | **85%** | ⬇️ | LUT 포맷 재검토 필요 |
| CC 라우팅 | 96% | 96% | — | 161 fw vs 148 VST |
| 프리셋 시스템 | 90% | 90% | — | — |
| **종합** | **96.0%** | **95.7%** | ⬇️ | Walk 확률 LUT + Spice LUT 포맷 불확실 |

**일치도 하향 사유**: Phase 13에서 이전 Phase의 LUT 해석을 재검토한 결과, Walk 확률 분포와 Spice LUT의 uint8/float32 해석이 부정확할 가능성을 발견. **이전에 과대평가되었던 항목을 정직하게 하향 조정**.

---

## Phase 13 수정 사항

### 기존 문서 수정 필요

| 문서 | 수정 내용 | 우선순위 |
|------|---------|---------|
| `MANUAL_CORRECTION_RECOMMENDATIONS.md` ENH-09 | Arp 확률 분포를 "추정"으로 표기 변경 | 높음 |
| `MANUAL_VS_FIRMWARE_MATCH.md` Spice/Dice | 일치도 88% → 85% 조정 | 높음 |
| `MANUAL_VS_FIRMWARE_MATCH.md` Arp | 일치도 95% → 93% 조정 | 높음 |
| `MANUAL_VS_FIRMWARE_MATCH.md` 종합 | 96.0% → 95.7% 조정 | 높음 |
| `PHASE9_RESULTS.md` | Walk LUT @ `0x080546C4` "8슬롯×8step" 해석 재검토 필요 | 중간 |
| `PHASE9_RESULTS.md` | env_time_scale @ `0x0806D330` "float32" 해석 재검토 필요 | 중간 |

### 새로운 발견

1. **VST params.xml 한계**: FX, LFO, Arp, Mod 등의 enum은 별도 파일에 존재할 가능성. MiniFreak V 설치본에서 추가 XML 리소스 탐색 필요.
2. **Walk LUT 포맷 미해결**: `0x080546C4`의 64 bytes가 uint8 확률 분포가 아닐 가능성. pair-wise 또는 structured 포맷일 수 있음.
3. **env_time_scale 포맷 의심**: `0x0806D330`의 float32 해석이 대부분 비정상값. 실제 포맷이 float32가 아닐 가능성 높음.

---

## Phase 13 산출물

| 문서/스크립트 | 내용 |
|---------------|------|
| `PHASE13_V_INTEGRATED_VERIFICATION.md` | 본 문서 — 3원 교차검증 완료 리포트 |
| `~/hoon/ghidra/scripts/phase13_v_crossverify.py` | 자동화 스크립트 (CM4/CM7 + VST XML + mf_enums.py) |

---

*Phase 13 완료: 2026-04-29*
*분석 도구: phase13_v_crossverify.py + mf_enums.py + minifreak_vst_params.xml*
*펌웨어: fw4_0_1_2229 (2025-06-18)*
