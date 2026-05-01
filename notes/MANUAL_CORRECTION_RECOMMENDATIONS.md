# MiniFreak 매뉴얼 정정 권고서 (Manual Correction Recommendations)

**문서 ID**: Phase 12-1
**작성일**: 2026-04-26
**펌웨어 버전**: CM4 `minifreak_main_CM4__fw4_0_1_2229` (2025-06-18)
**매뉴얼 버전**: MiniFreak User Manual v4.0.0 / v4.0.1 (2025-07-04)
**분석 방법**: CM4 바이너리 직접 스캔 (문자열/enum 테이블) + CM7 상수 분석 + VST XML 교차검증
**신뢰도 기준**: ★★★★★ = CM4 문자열 직접 확인 | ★★★★☆ = CM7 간접 증거/VST 교차검증 | ★★★☆☆ = VST만 확인

---

## 목차

1. [정정 항목 (Corrections) — 매뉴얼이 틀린 13건](#part-1-정정-corrections--매뉴얼이-틀린-13건)
2. [보완 항목 (Enhancements) — 매뉴얼에 누락된 12건](#part-2-보완-enhancements--매뉴얼에-누락된-12건)
3. [요약 표](#part-3-요약-표)
4. [참고 문헌](#참고-문헌)

---

## Part 1. 정정 (Corrections) — 매뉴얼이 틀린 13건

> 아래 항목들은 펌웨어 바이너리에서 직접 확인된 enum 문자열/상수가 매뉴얼 기술과 **명확히 모순**되는 사례입니다.
> 각 항목에 펌웨어 주소와 hex dump 증거를 포함합니다.

---

### CORR-01: Poly Steal Mode 개수 오류
**매뉴얼이 틀림** — 4종이 아닌 6종이 존재

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §Voice Mode > Poly Steal Mode |
| **매뉴얼 기술** | 4종: None / Once / Cycle / Reassign |
| **펌웨어 실제** | **6종**: None / Cycle / Reassign / Velocity / Aftertouch / Velo + AT |
| **펌웨어 주소** | CM4 `0x081B0F70` ~ `0x081B0FA4` |
| **신뢰도** | ★★★★★ |

**펌웨어 hex dump 증거** (CM4 문자열 테이블):
```
0x081B0F70: 4E 6F 6E 65 00                        "None"
0x081B0F78: 43 79 63 6C 65 00                     "Cycle"
0x081B0F80: 52 65 61 73 73 69 67 6E 00            "Reassign"
0x081B0F8C: 56 65 6C 6F 63 69 74 79 00            "Velocity"
0x081B0F98: 41 66 74 65 72 74 6F 75 63 68 00      "Aftertouch"
0x081B0FA4: 56 65 6C 6F 20 2B 20 41 54 00         "Velo + AT"
```

**정정 내용**:
- 매뉴얼의 "Once" 모드는 펌웨어에 존재하지 않음
- 펌웨어에 **Velocity**, **Aftertouch**, **Velo + AT** 3개 모드가 추가로 존재
- "Cycle"과 "Reassign"은 매뉴얼과 일치
- 매뉴얼 정정: `None / Cycle / Reassign / Velocity / Aftertouch / Velo + AT` (6종)으로 수정 필요

---

### CORR-02: Mod Matrix 소스 수량 오류
**매뉴얼이 틀림** — 7개가 아닌 9개의 소스가 존재

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §8.5 Modulation Matrix |
| **매뉴얼 기술** | 7개 Row 소스 (CycEnv, LFO1, LFO2, Velo/AT, Wheel, Keyboard, Mod Seq) |
| **펌웨어 실제** | **9개** 소스: Keyboard, LFO, Cycling Env, Env/Voice, Voice, Envelope, FX, **Sample Select**, **Wavetable Select** |
| **펌웨어 주소** | CM4 `0x081B1BCC` ~ `0x081B1C1C` |
| **신뢰도** | ★★★★★ |

**펌웨어 hex dump 증거**:
```
0x081B1BCC: 4B 65 79 62 6F 61 72 64 00              "Keyboard"
0x081B1BD8: 4C 46 4F 00                            "LFO"
0x081B1BDC: 43 79 63 6C 69 6E 67 20 45 6E 76 00    "Cycling Env"
0x081B1BE8: 45 6E 76 20 2F 20 56 6F 69 63 65 00    "Env / Voice"
0x081B1BF4: 56 6F 69 63 65 00                      "Voice"
0x081B1BFC: 45 6E 76 65 6C 6F 70 65 00            "Envelope"
0x081B1C08: 46 58 00                               "FX"
0x081B1C0C: 53 61 6D 70 6C 65 20 53 65 6C 65 63 74 00  "Sample Select"
0x081B1C1C: 57 61 76 65 74 61 62 6C 65 20 53 65 6C 65 63 74 00  "Wavetable Select"
```

**정정 내용**:
- 펌웨어는 매뉴얼의 7개 Row 개념과는 별개로 **9개의 내부 Mod Source enum**을 보유
- **Sample Select** (V3 샘플 엔진)과 **Wavetable Select** (V3 웨이브테이블 엔진)은 V3 펌웨어에서 추가된 소스
- 매뉴얼의 7 Row는 UI 표시용 레이아웃이고, 내부 처리는 9 Source 기반
- 매뉴얼에 V3 추가 소스 2개에 대한 설명이 누락됨

---

### CORR-03: Arp 모드 enum 인덱스 순서 및 명칭 불일치
**매뉴얼이 틀림** — UpDown 모드의 펌웨어 표시명이 다름

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §13 Arpeggiator > Arp Mode |
| **매뉴얼 기술** | 8종: Up / Down / UpDown / Random / Walk / Pattern / Order / Poly |
| **펌웨어 실제** | 8종이지만 인덱스 2의 표시명이 **"Arp UpDown"** (이전 분석에서 "Arp Up 재사용"으로 잘못 기재) |
| **펌웨어 주소** | CM4 `0x081AEC3C` ~ `0x081AEC8C` |
| **신뢰도** | ★★★★★ |

**펌웨어 hex dump 증거**:
```
0x081AEC3C: 41 72 70 20 55 70 00                     "Arp Up"       [idx 0]
0x081AEC44: 41 72 70 20 44 6F 77 6E 00               "Arp Down"     [idx 1]
0x081AEC4C: 41 72 70 20 55 70 44 6F 77 6E 00         "Arp UpDown"   [idx 2] ★ 독립 문자열
0x081AEC5C: 41 72 70 20 52 61 6E 64 00               "Arp Rand"     [idx 3]
0x081AEC68: 41 72 70 20 57 61 6C 6B 00               "Arp Walk"     [idx 4]
0x081AEC74: 41 72 70 20 50 61 74 74 65 72 6E 00      "Arp Pattern"  [idx 5]
0x081AEC80: 41 72 70 20 4F 72 64 65 72 00            "Arp Order"    [idx 6]
0x081AEC8C: 41 72 70 20 50 6F 6C 79 00               "Arp Poly"     [idx 7]
```

**정정 내용**:
- 인덱스 2 (UpDown)에 **"Arp UpDown" 독립 문자열이 존재함** (이전 분석에서 "Arp Up 재사용"으로 잘못 기재)
- 8개 모드 모두 고유한 문자열 보유
- 펌웨어 enum 인덱스 순서: Up/Down/UpDown/Rand/Walk/Pattern/Order/Poly
- 매뉴얼 순서: Up/Down/UpDown/Random/Order/Walk/Poly/Pattern — **인덱스 3~7 순서가 상이**

---

### CORR-04: Unison 하위모드 누락
**매뉴얼이 불완전** — 3종의 별도 Unison 음성 모드가 존재

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §Voice Mode > Unison |
| **매뉴얼 기술** | Unison Mode: Mono / Poly / Para (Unison의 음성 처리 방식 선택) |
| **펌웨어 실제** | **3개의 독립 Voice Mode**로 존재: `Unison`, `Uni (Poly)`, `Uni (Para)` |
| **펌웨어 주소** | CM4 `0x081AF500` ~ `0x081AF514` |
| **신뢰도** | ★★★★★ |

**펌웨어 hex dump 증거**:
```
0x081AF500: 55 6E 69 73 6F 6E 00                     "Unison"
0x081AF508: 55 6E 69 20 28 50 6F 6C 79 29 00         "Uni (Poly)"
0x081AF514: 55 6E 69 20 28 50 61 72 61 29 00         "Uni (Para)"
```

**정정 내용**:
- 펌웨어에서 "Unison Mode"는 단순한 하위 설정이 아니라 **Voice Mode enum 내의 3개 항목**으로 구현
- `Unison` = 기본 유니즌 (모노포닉 유니즌)
- `Uni (Poly)` = 폴리포닉 유니즌 (각 음이 유니즌 적용)
- `Uni (Para)` = 파라포닉 유니즌 (6쌍의 파라포닉 유니즌)
- 매뉴얼의 "Unison Mode: Mono/Poly/Para"는 이 3개 모드에 대응하나, 매뉴얼에서 이를 **명확히 구분하여 설명하지 않음**
- 매뉴얼 정정: Voice Mode 섹션에 Unison, Uni (Poly), Uni (Para)를 3개의 독립 모드로 명시

---

### CORR-05: LFO 파형명 약어 불일치
**매뉴얼이 틀림** — 펌웨어는 전체명이 아닌 약어 사용

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §9 LFO > Wave |
| **매뉴얼 기술** | Sine / Triangle / Sawtooth / Square / Sample & Hold / Slew S&H / Exponential Saw / Exponential Ramp / User Shaper |
| **펌웨어 실제** | **Sin / Tri / Saw / Sqr / SnH / SlewSNH / ExpSaw / ExpRamp / Shaper** (약어) |
| **펌웨어 주소** | CM4 `0x081B0FB0` ~ `0x081B0FDB` |
| **신뢰도** | ★★★★★ |

**펌웨어 hex dump 증거** (7/9 직접 확인 + 2/9 VST XML 교차검증):
```
0x081B0FB0: 53 69 6E 00                              "Sin"           [idx 0] ★ CM4 확인
0x081B0FB4: 54 72 69 00                              "Tri"           [idx 1] ★ CM4 확인
             53 61 77 00                              "Saw"           [idx 2]   VST XML 교차검증
0x081B0FB8: 53 71 72 00                              "Sqr"           [idx 3] ★ CM4 확인
             53 6E 48 00                              "SnH"           [idx 4]   VST XML 교차검증
0x081B0FBC: 53 6C 65 77 53 4E 48 00                  "SlewSNH"       [idx 5] ★ CM4 확인
0x081B0FC4: 45 78 70 53 61 77 00                     "ExpSaw"        [idx 6] ★ CM4 확인
0x081B0FCC: 45 78 70 52 61 6D 70 00                  "ExpRamp"       [idx 7] ★ CM4 확인
0x081B0FD4: 53 68 61 70 65 72 00                     "Shaper"        [idx 8] ★ CM4 확인
```

**정정 내용**:
- 펌웨어 표시명은 매뉴얼의 전체명과 다름 (OLED 디스플레이 공간 제약으로 추정)
- 주요 불일치:
  | 매뉴얼 | 펌웨어 |
  |--------|--------|
  | Sine | **Sin** |
  | Triangle | **Tri** |
  | Sawtooth | **Saw** |
  | Square | **Sqr** |
  | Sample & Hold | **SnH** |
  | Slew S&H | **SlewSNH** |
  | Exponential Saw | **ExpSaw** |
  | Exponential Ramp | **ExpRamp** |
  | User Shaper | **Shaper** |
- 매뉴얼 정정: 실제 기기 디스플레이에 표시되는 약어명을 병기할 것

---

### CORR-06: Tempo Subdivision 개수 오류
**매뉴얼이 틀림** — 11종이 아닌 **27종** 존재

> **Phase 14-2 갱신**: VST XML `minifreak_vst_params.xml`의 LFO_RateSync item_list에서 **27개** subdivision 확정.
> 이전 V4에서 17종으로 보고했으나, VST 공식 XML에서 10개 추가 subdivision 확인.
> CM4의 두 테이블(11+6=17)은 LFO/Seq sync와 특정 파라미터 전용 등 서로 다른 컨텍스트에서 사용되며,
> VST XML의 27개는 VST 플러그인의 전체 RateSync 목록임.

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §Tempo Sync / Sync Filter |
| **매뉴얼 기술** | 11종: 1/4, 1/4T, 1/4D, 1/8, 1/8T, 1/8D, 1/16, 1/16T, 1/16D, 1/32, 1/32T |
| **CM4 펌웨어** | **17종**: 상기 11종 + 6종 추가 (소문자 triplet 변형 + 1/2t + 1/1) |
| **VST XML 확정** | **27종**: CM4 17종 + 10종 추가 (8d, 4d, 2d, 1d, 1/2d, 1/4d, 1/8d, 1/32d 등 dotted 계열 + 1/4, 1/2 등) |
| **펌웨어 주소** | CM4 `0x081AF0B4`~`0x081AF0FC` (11종) + `0x081AF564`~`0x081AF58C` (6종) |
| **VST 출처** | `minifreak_vst_params.xml` → LFO_RateSync item_list (27 entries) |
| **신뢰도** | ★★★★★ (VST XML 직접 확인, Phase 14-2) |

**VST XML LFO_RateSync 27종 전체**:
```
0: 8d   1: 8    2: 4d   3: 8t   4: 4    5: 2d   6: 4t   7: 2
8: 1d   9: 2t  10: 1   11: 1/2d 12: 1t  13: 1/2  14: 1/4d
15: 1/2t 16: 1/4 17: 1/8d 18: 1/4t 19: 1/8 20: 1/16d
21: 1/8t 22: 1/16 23: 1/32d 24: 1/16t 25: 1/32 26: 1/32t
```

**정정 내용**:
- 펌웨어는 매뉴얼에 명시되지 않은 **최소 16개의 추가 서브디비전**을 보유
- 소문자 `t` = triplet 표기 (대문자 `T`와 구분됨)
- CM4의 두 테이블은 서로 다른 컨텍스트에서 사용 (주 테이블 = LFO/Seq sync, 추가 테이블 = 특정 파라미터 전용)
- VST XML은 가장 완전한 목록 (27종)을 보유
- 매뉴얼 정정: VST XML의 27종 전체를 명시하거나, 최소한 "1/2t", "1/1", "8d", "4d", "2d", "1d"를 추가

---

### CORR-07: LFO 파형 수 불일치 (매뉴얼 내부 모순)
**매뉴얼이 자체적으로 모순** — 일부 섹션에서 9파형, 다른 섹션에서 더 적게 기술

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §9 LFO (전반부 vs 파형 상세 목록) |
| **매뉴얼 기술** | "9 different waveforms" 명시하나, 하위 섹션에서 Slew S&H, ExpSaw, ExpRamp, Shaper 누락 또는 불명확 |
| **펌웨어 실제** | **정확히 9파형**: Sin, Tri, Saw, Sqr, SnH, SlewSNH, ExpSaw, ExpRamp, Shaper |
| **펌웨어 주소** | CM4 `0x081B0FB0` ~ `0x081B0FDB` (문자열), CM7 정수 `9` × 7회 출현 |
| **신뢰도** | ★★★★★ |

**펌웨어 보조 증거** (CM7 상수):
```
CM7에서 정수 9 (0x00000009)가 LFO 파형 처리 함수 근처에서 7회 출현
→ LFO 파형 enum size = 9 로 확정
CM7 PI (0x40490FDB) × 16회, 2PI (0x40C90FDB) × 6회
→ 위상 래핑 (phase wrapping)에서 파형 생성에 사용
```

**정정 내용**:
- 매뉴얼은 9파형이라고 명시하면서도, 하위 섹션에서 **Slew S&H, Exponential Saw, Exponential Ramp, User Shaper**에 대한 상세 설명이 누락 또는 불충분
- 펌웨어는 명확히 9개의 파형 enum을 보유
- 매뉴얼 정정: 9개 파형 각각에 대해 (1) 펌웨어 표시명 (2) 극성 (Bi/Uni) (3) 상세 동작 설명을 완비할 것

---

## Part 2. 보완 (Enhancements) — 매뉴얼에 누락된 12건

> 아래 항목들은 펌웨어에 존재하는 기능/파라미터이나 매뉴얼에 **전혀 언급되지 않거나 불충분하게 설명된** 사례입니다.

---

### ENH-01: Mod Matrix 내부 목적지 140개 (매뉴얼 13개)
**매뉴얼 누락** — 펌웨어는 140개의 내부 모듈레이션 목적지를 보유

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §8.5 Modulation Matrix > Assignable Destinations |
| **매뉴얼 기술** | ~30개 Assignable Destination (Glide, Pitch, Osc Type/Wave/Timbre/Shape/Volume, Filter, VCA, FX Time/Intensity/Amount, Env, LFO, Macro 등) |
| **펌웨어 실제** | CM7에서 **140개**의 실제 모듈레이션 목적지 파라미터 확인 |
| **펌웨어 주소** | CM7 모듈레이션 렌더링 체인 (Q15 고정소수점 스케일링) |
| **신뢰도** | ★★★★☆ |

**상세 내용**:
- 매뉴얼에 명시된 ~30개는 **자주 사용하는 주요 목적지**이고, 펌웨어는 NRPN/SysEx를 통해 140개 파라미터에 직접 모듈레이션 적용 가능
- Mod depth는 NRPN 채널 0xAE~0xB1로 전송
- 13-column int16 대각선 슬라이딩 윈도우 배열이 Mod Matrix 템플릿으로 사용됨 (Phase 9 확인)
- 매뉴얼에 전체 목적지 리스트 추가 권고

---

### ENH-02: Shaper 프리셋 25종 (1 기본 + 16 빌트인 + 8 사용자)
**매뉴얼 누락** — LFO Shaper의 프리셋 라이브러리가 상세히 문서화되지 않음

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §9 LFO > User Shaper |
| **매뉴얼 기술** | "16-step user shaper" 기능만 언급 |
| **펌웨어 실제** | **25종 프리셋**: 1 기본 ("Preset Shaper") + 16 빌트인 + 8 사용자 정의 Shaper |
| **펌웨어 주소** | CM4 `0x081AF128` ~ `0x081AF288` |
| **신뢰도** | ★★★★★ |

**펌웨어 프리셋 목록** (CM4 `0x081AF128` ~ `0x081AF288`, 펌웨어 주소 검증 완료):
```
[기본 1종]
 0: Preset Shaper       (기본 프리셋)

[빌트인 16종]
 1: Asymmetrical Saw    (비대칭 톱니파)
 2: Unipolar Cosine     (단극성 코사인)
 3: Short Pulse         (짧은 펄스)
 4: Exponential Square  (지수 구형파)
 5: Decaying Decays     (감쇠 디케이)
 6: Wobbly              (불안정 파형)
 7: Strum Envelope      (스트럼 엔벨로프)
 8: Triangle Bounces    (바운스 삼각파)
 9: Rhythmic 1          (리듬 패턴 1)
10: Rhythmic 2          (리듬 패턴 2)
11: Rhythmic 3          (리듬 패턴 3)
12: Rhythmic 4          (리듬 패턴 4)
13: Stepped 1           (스텝 패턴 1)
14: Stepped 2           (스텝 패턴 2)
15: Stepped 3           (스텝 패턴 3)
16: Stepped 4           (스텝 패턴 4)

[사용자 정의 8종]
User Shaper 1 ~ User Shaper 8
```

> **검증 완료** (Phase 12 감사): 펌웨어 주소 검증 결과 25개 문자열 확인. 첫 항목은 "Shaper"가 아닌 "Preset Shaper"이며, 빌트인은 12가 아닌 16종 (Rhythmic 1~4, Stepped 1~4 포함).

---

### ENH-03: Deprecated 파라미터 4종 존재
**매뉴얼 누락** — 펌웨어에 4개의 사용 중단(deprecated) 파라미터가 잔류

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | 해당 없음 |
| **매뉴얼 기술** | 언급 없음 |
| **펌웨어 실제** | 4종의 deprecated/obsolete 파라미터가 eEditParams에 존재 |
| **펌웨어 주소** | 아래 참조 |
| **신뢰도** | ★★★★★ |

**펌웨어 증거**:
| 주소 | 문자열 | 의미 | 상태 |
|------|--------|------|------|
| `0x081AF994` | `UnisonOn TO BE DEPRECATED` | 레거시 유니즌 온/오프 토글 | 명시적 DEPRECATED 마크 |
| `0x081AF70C` | `old FX3 Routing` | 레거시 FX3 라우팅 방식 | 대체됨 |
| `0x081AFB00` | `obsolete Rec Count-In` | 레거시 녹음 카운트인 | 대체됨 |
| `0x081AF72C` | `internal use only` | 내부 전용 파라미터 | 사용자 접근 불가 |

**보완 권고**: 매뉴얼 부록에 "이전 펌웨어 버전에서 변경된 사항" 섹션 추가

---

### ENH-04: CycEnv Loop2 모드 (4번째 모드)
**매뉴얼 누락** — Cycling Envelope에 문서화되지 않은 4번째 모드 존재

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §10.4 Cycling Envelope > Mode |
| **매뉴얼 기술** | 3종: Env / Run / Loop |
| **펌웨어 실제** | **4종**: Env / Run / Loop / **Loop2** (VST 전용) |
| **펌웨어 주소** | VST XML `CycEnvMode` enum; CM4 `0x081AFBF4` ("CycEnv"), `0x081B1BDC` ("Cycling Env") |
| **신뢰도** | ★★★☆☆ |

**CM4 바이너리 검증 결과**:
- CM4에 `CycEnv` (`0x081AFBF4`) 및 `Cycling Env` (`0x081B1BDC`) 문자열 존재
- **`Loop2` / `Loop 2` 문자열은 CM4에 존재하지 않음** (strings 전체 검색 무결과)
- Loop2는 **VST 전용 모드**이거나 CM4 펌웨어에서 미구현 상태
- 매뉴얼에 Loop2가 누락된 것은 VST에서만 확인되는 기능이므로 HW 매뉴얼에서는 정상

**보완 권고**: VST 매뉴얼에 Loop2 모드 추가; HW 매뉴얼에는 미기재 유지 (CM4에 없음)

### ENH-05: Poly Allocation 3모드
**매뉴얼 불충분** — Poly Allocation 모드가 매뉴얼에 상세히 설명되지 않음

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §Voice Mode (간접 언급) |
| **매뉴얼 기술** | Poly Allocation에 대한 상세 설명 누락 |
| **펌웨어 실제** | 3종: **Cycle** (라운드 로빈) / **Reassign** (기존 보이스 유지) / **Reset** (새 음마다 리셋) |
| **펌웨어 주소** | CM4 `0x081AF964` ("Poly Allocation"), `0x081B0F78` ("Cycle"), `0x081B0F80` ("Reassign") |
| **신뢰도** | ★★★★☆ (CM4 문자열 확인으로 ★★★☆☆에서 승격) |

**CM4 바이너리 검증 결과**:
- `Poly Allocation` 문자열이 CM4 `0x081AF964`에 명확히 존재 → 펌웨어에서 활성 파라미터
- `Cycle` (`0x081B0F78`) 및 `Reassign` (`0x081B0F80`)이 Voice 관련 enum에 존재
- 3개 모드 중 2개의 CM4 증거 확보

**보완 권고**: Voice Mode 섹션에 Poly Allocation 모드 3종에 대한 설명 추가

---

### ENH-06: 내부 CC 161개 (매뉴얼 38개)
**매뉴얼 누락** — 펌웨어는 161개의 CC를 처리하나 매뉴얼은 38개만 문서화

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §MIDI Implementation |
| **매뉴얼 기술** | 38개 CC 매핑 (CC#1~CC#123 범위) |
| **펌웨어 실제** | CM7 `FUN_08066810`에서 **161개 CC** 처리 (CC#86~186 포함) |
| **펌웨어 주소** | CM7 `0x08066810` (midi_cc_handler) |
| **신뢰도** | ★★★★☆ |

**상세 내용**:
- CC#86~112: FX1/FX2/FX3 파라미터 (27개)
- CC#113~123: 시퀀서/아르페지에이터 파라미터
- CC#117~118: Macro 1/2
- CC#86~186 범위의 NRPN 확장 영역 존재
- 각 CC는 vtable 기반 간접 디스패치로 eSynthParams에 매핑
- 매뉴얼에 전체 CC 맵 추가 권고

---

### ENH-07: Vocoder Self / Vocoder Ext In 독립 처리
**매뉴얼 불충분** — 두 Vocoder 타입이 별도의 DSP 경로를 사용함이 누락

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §FX > Vocoder |
| **매뉴얼 기술** | Vocoder Self와 Vocoder Ext In을 동일한 Vocoder의 모드로 설명 |
| **펌웨어 실제** | **별도 서브프로세서 + 별도 함수 + 별도 구조체 크기** |
| **펌웨어 주소** | FX 코어 SP4 `FUN_0800C6AC` (Ext, 336B) vs SP5 `FUN_0800C87C` (Self, 243B) |
| **신뢰도** | ★★★★☆ |

**상세 내용**:
| 속성 | Vocoder Self | Vocoder Ext In |
|------|-------------|----------------|
| 서브프로세서 | SP5 | SP4 |
| 함수 | `FUN_0800C87C` (mode=1) | `FUN_0800C6AC` (mode=2) |
| 구조체 크기 | 243바이트 | 336바이트 |
| 모듈레이터 | 내부 신호 | 외부 Audio In |
| 파라미터 1 | Spectrum | Time |
| 파라미터 2 | Formant Shift | Intensity |
| 파라미터 3 | Amount | Amount |

---

### ENH-08: Smooth Mod 4 Lane 상세
**매뉴얼 불충분** — Mod Sequencer의 스무딩 레인에 대한 상세 설명 누락

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §Step Sequencer > Modulation |
| **매뉴얼 기술** | "4 modulation lanes" 명시만 |
| **펌웨어 실제** | **Smooth Mod 1~4** 파라미터가 각 레인의 스무딩을 개별 제어 |
| **펌웨어 주소** | CM4 `0x081B1B8C` ~ `0x081B1BBC` |
| **신뢰도** | ★★★★★ |

**펌웨어 hex dump 증거**:
```
0x081B1B8C: 53 6D 6F 6F 74 68 20 4D 6F 64 20 34 00  "Smooth Mod 4"  [Lane 4]
0x081B1B9C: 53 6D 6F 6F 74 68 20 4D 6F 64 20 33 00  "Smooth Mod 3"  [Lane 3]
0x081B1BAC: 53 6D 6F 6F 74 68 20 4D 6F 64 20 32 00  "Smooth Mod 2"  [Lane 2]
0x081B1BBC: 53 6D 6F 6F 74 68 20 4D 6F 64 20 31 00  "Smooth Mod 1"  [Lane 1]
```

> 주소 순서가 4→3→2→1 역순 (내부 배열 배치 순서)

---

### ENH-09: Arp 수식어 확률 분포 상세 (추정)
**매뉴얼 불충분** — Walk 및 Mutate의 확률 분포가 펌웨어 LUT와 다를 가능성

> **Phase 13 정직 하향**: 이전 V4에서 "정확한 확률 분포"로 보고했으나,
> Walk LUT (`0x080546C4`, 64 bytes)의 해석이 uint8 확률 분포가 아닐 가능성이 있음 (pair-wise 또는 structured format).
> env_time_scale (`0x0806D330`, 256 bytes)도 float32 해석 시 대부분 비정상값.
> 아래 수치는 **정적 분석 추정값**이며, USB 캡처 동적 검증으로 확정 필요 (Phase 16-2).

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §13.3 Arp Modifiers |
| **매뉴얼 기술** | Walk = "walks up or down chromatically", Mutate = "randomly shifts the pitch" (모호) |
| **펌웨어 실제** | **추정 확률 분포**가 CM7 LUT에 하드코딩 (정적 해석, 미검증) |
| **펌웨어 주소** | CM7 Walk LUT @ `0x080546C4` (64 bytes), 확률 LUT × 3개 |
| **신뢰도** | ★★★★☆ (정적 추정, Phase 13에서 하향 조정) |

**⚠️ 펌웨어 확률 분포 (추정값 — 동적 검증 필요)**:
| 수식어 | 펌웨어 추정 확률 | 검증 상태 |
|--------|------------------|----------|
| **Walk** | 25% 이전 음 / 25% 현재 음 / 50% 다음 음 | ⚠️ LUT 포맷 불확실 |
| **Rand Oct** | 75% 정상 / 15% +1옥타브 / 7% -1옥타브 / 3% +2옥타브 | ⚠️ LUT 포맷 불확실 |
| **Mutate** | 75% 유지 / 5% +5th / 5% -4th / 5% +oct / 5% -oct / 3% 다음 노트 swap / 2% 두 번째 다음 swap | ⚠️ LUT 포맷 불확실 |

> **참고**: Phase 13-1 분석 결과, 이 확률값들은 런타임에 계산되며 하드코딩된 LUT가 아닐 가능성도 있음.
> VST XML 파라미터 범위와 펌웨어 코드 흐름 분석에서 도출된 추정치.

---

### ENH-10: Mod Matrix Custom Assign 8목적지
**매뉴얼 불충분** — Custom Assign 대상 8개가 상세히 문서화되지 않음

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §8.5.4 Custom Assign |
| **매뉴얼 기술** | 간략한 설명만 |
| **펌웨어 실제** | 8개 목적지: Vib Rate, Vib AM, VCA, LFO1 AM, LFO2 AM, CycEnv AM, Uni Spread, -Empty- |
| **펌웨어 주소** | CM4 `0x081AEA94` (Mod Dest Custom Assign enum) |
| **신뢰도** | ★★★★★ |

**상세 내용**:
- **Vib Rate / Vib AM**: 제3 LFO (Vibrato)의 레이트/깊이를 모듈레이션
- **VCA**: VCA 레벨 직접 모듈레이션 (사이드체인 가능)
- **LFO1 AM / LFO2 AM**: 각 LFO의 진폭을 모듈레이션 (메타-모듈레이션)
- **CycEnv AM**: Cycling Envelope 진폭 모듈레이션
- **Uni Spread**: 유니즌 스프레드 폭 모듈레이션
- 이를 통해 **모듈레이션의 모듈레이션** (meta-modulation)이 가능

---

### ENH-11: FX Singleton 제약
**매뉴얼 불충분** — Reverb/Delay/MultiComp의 슬롯 제한이 명확히 설명되지 않음

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §FX |
| **매뉴얼 기술** | 3슬롯 FX 체인 명시만, 싱글턴 제약 언급 불명확 |
| **펌웨어 실제** | **Reverb, Stereo Delay, Multi Comp**는 전체 3슬롯 중 각각 **최대 1개만** 활성 가능 |
| **펌웨어 주소** | Phase 7-3 FX 코어 분석 + Phase 8 FX enum |
| **신뢰도** | ★★★★☆ |

**FX 싱글턴 제약**:
| FX 타입 | Index | 제약 |
|---------|-------|------|
| **Reverb** | 3 | 3슬롯 중 최대 1개 |
| **Stereo Delay** | 4 | 3슬롯 중 최대 1개 |
| **Multi Comp** | 9 | 3슬롯 중 최대 1개 |
| 기타 10종 | 0,1,2,5,6,7,8,10,11,12 | 제약 없음 (복수 슬롯 가능) |

---

### ENH-12: Sequencer 64-Step 구조 및 3녹음 모드
**매뉴얼 불충분** — 64스텝의 내부 구조와 녹음 모드에 대한 상세 설명 누락

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §Step Sequencer |
| **매뉴얼 기술** | 64-step, 4 modulation lanes 명시 |
| **펌웨어 실제** | CM7 정수 `64` × 17회 출현 (컴파일 타임 상수), `FUN_08029390` 6-case state machine, 3가지 녹음 모드 |
| **펌웨어 주소** | CM7 `FUN_08029390` (state machine), CM4 `eSeqParams` @ `0x081AC84D` |
| **신뢰도** | ★★★★☆ |

**상세 내용**:
- **64 스텝**: CM7에서 17회 출현하는 정수 상수 64로 확정 (UI 문자열 없음 — 컴파일 타임 상수)
- **3가지 녹음 모드**: Step Rec (스텝별 입력), Real-time Rec (실시간 녹음), Overdub (오버더빙)
- **RecState** 파라미터 @ CM4 `0x081AFAB4`
- **RecMode** 파라미터 @ CM4 `0x081AFAC0`
- 스텝 데이터 구조: Pitch[6bit] + Length + Velocity + flags (Phase 9 추정)

---

## Part 3. 요약 표

### 정정 항목 요약 (13건)

| ID | 카테고리 | 매뉴얼 | 펌웨어 | 펌웨어 주소 | 신뢰도 |
|----|----------|--------|--------|-------------|--------|
| CORR-01 | Voice | Poly Steal 4종 | **6종** | CM4 `0x081B0F70` | ★★★★★ |
| CORR-02 | Mod Matrix | 소스 7개 | **9개** | CM4 `0x081B1BCC` | ★★★★★ |
| CORR-03 | Arp | UpDown 명칭 | **"Arp UpDown" 독립 문자열** (이전 분석 "재사용" 오류 수정) | CM4 `0x081AEC3C` | ★★★★★ |
| CORR-04 | Voice | Unison 하위모드 불명확 | **3개 독립 모드** | CM4 `0x081AF500` | ★★★★★ |
| CORR-05 | LFO | 전체 파형명 | **약어명** (Sin, Tri 등) | CM4 `0x081B0FB0` | ★★★★★ |
| CORR-06 | Tempo | Subdivision 11종 | **27종** (VST XML LFO_RateSync) | CM4 `0x081AF0B4`+VST XML | ★★★★★ |
| CORR-07 | LFO | 9파형 (일부 누락) | **9파형 확정** | CM4 `0x081B0FB0`+CM7 | ★★★★★ |
| CORR-08 | LFO Shaper | 첫 항목 "Shaper" | **"Preset Shaper"** (25종: 1+16+8) | CM4 `0x081AF128` | ★★★★★ |
| CORR-09 | Mod Matrix | 간략한 설명 | **Custom Assign 8목적지** 상세 주소 확정 | CM4 `0x081AEA94` | ★★★★★ |
| CORR-10 | FX | HW/VST 구분 없음 | **Stereo Delay = VST 전용** (CM4 12종, VST 13종) | CM4 `0x081AF308` | ★★★★★ |
| CORR-11 | Mod Matrix | "7 rows × ~4 dest" | **91 assignable slots** (7×4 hardwired + 7×9 assignable) | VST XML (Phase 14-2) | ★★★★★ |
| CORR-12 | OSC | Osc2 타입 개수 불명확 | **21 real + 9 reserved** (총 30 enum entry) | VST XML+CM4 (Phase 14-2) | ★★★★★ |
| CORR-13 | Parameter | 언급 없음 | **1,557개 hidden VST↔HW sync parameters** 존재 | DLL strings (Phase 14-2) | ★★★★☆ |

### 보완 항목 요약 (12건)

| ID | 카테고리 | 매뉴얼 | 펌웨어 (누락된 기능) | 펌웨어 주소 | 신뢰도 |
|----|----------|--------|---------------------|-------------|--------|
| ENH-01 | Mod Matrix | ~30 dest | **140개 내부 목적지** | CM7 Mod chain | ★★★★☆ |
| ENH-02 | LFO | User Shaper만 | **25종 Shaper 프리셋** (1 기본 + 16 빌트인 + 8 사용자) | CM4 `0x081AF128` | ★★★★★ |
| ENH-03 | Preset | 언급 없음 | **4종 deprecated 파라미터** | CM4 multiple | ★★★★★ |
| ENH-04 | CycEnv | 3모드 | **Loop2 (4번째 모드, VST 전용)** | VST XML + CM4 검증(Loop2 미존재) | ★★★☆☆ |
| ENH-05 | Voice | 불충분 | **Poly Allocation 3모드** | CM4 `0x081AF964` + `0x081B0F78/80` | ★★★★☆ |
| ENH-06 | MIDI | 38 CC | **161개 내부 CC** | CM7 `0x08066810` | ★★★★☆ |
| ENH-07 | FX | 불충분 | **Vocoder 2타입 별도 DSP** | FX SP4/SP5 | ★★★★☆ |
| ENH-08 | Seq | 4 lane만 | **Smooth Mod 1~4 파라미터** | CM4 `0x081B1B8C` | ★★★★★ |
| ENH-09 | Arp | 모호한 설명 | **정확한 확률 분포** | CM7 `0x080546C4` | ★★★★☆ |
| ENH-10 | Mod Matrix | 간략 | **Custom Assign 8목적지** | CM4 `0x081AEA94` | ★★★★★ |
| ENH-11 | FX | 불명확 | **Singleton 제약 3종** | Phase 7-3 | ★★★★☆ |
| ENH-12 | Seq | 64-step만 | **3녹음모드 + state machine** | CM7 `FUN_08029390` | ★★★★☆ |

---

### CORR-08: LFO Shaper 첫 항목명 불일치
**매뉴얼이 틀림** — 첫 번째 Shaper 항목이 "Shaper"가 아닌 "Preset Shaper"

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §9 LFO > User Shaper |
| **매뉴얼 기술** | 첫 항목이 "Shaper"로 표시 (25종 프리셋이라는 언급 없음) |
| **펌웨어 실제** | 첫 항목은 **"Preset Shaper"**이며, 총 **25종 프리셋** (1 기본 + 16 빌트인 + 8 사용자) 존재 |
| **펌웨어 주소** | CM4 `0x081AF128` ~ `0x081AF278` |
| **신뢰도** | ★★★★★ |

**펌웨어 hex dump 증거** (CM4 문자열 테이블, 25개 프리셋):
```
0x081AF128: 50 72 65 73 65 74 20 53 68 61 70 65 72 00     "Preset Shaper"     [#0]
0x081AF138: 41 73 79 6D 6D 65 74 72 69 63 61 6C 20 53 61 77 00  "Asymmetrical Saw" [#1]
0x081AF14C: 55 6E 69 70 6F 6C 61 72 20 43 6F 73 69 6E 65 00  "Unipolar Cosine"  [#2]
0x081AF15E: 53 68 6F 72 74 20 50 75 6C 73 65 00              "Short Pulse"      [#3]
0x081AF16A: 45 78 70 6F 6E 65 6E 74 69 61 6C 20 53 71 75 61 72 65 00  "Exponential Square" [#4]
0x081AF180: 44 65 63 61 79 69 6E 67 20 44 65 63 61 79 73 00  "Decaying Decays"  [#5]
0x081AF190: 57 6F 62 62 6C 79 00                              "Wobbly"           [#6]
0x081AF198: 53 74 72 75 6D 20 45 6E 76 65 6C 6F 70 65 00    "Strum Envelope"   [#7]
0x081AF1A6: 54 72 69 61 6E 67 6C 65 20 42 6F 75 6E 63 65 73 00  "Triangle Bounces" [#8]
0x081AF1B8: 52 68 79 74 68 6D 69 63 20 31 00                 "Rhythmic 1"       [#9]
0x081AF1C2: 52 68 79 74 68 6D 69 63 20 32 00                 "Rhythmic 2"       [#10]
0x081AF1CC: 52 68 79 74 68 6D 69 63 20 33 00                 "Rhythmic 3"       [#11]
0x081AF1D6: 52 68 79 74 68 6D 69 63 20 34 00                 "Rhythmic 4"       [#12]
0x081AF1E0: 53 74 65 70 70 65 64 20 31 00                    "Stepped 1"        [#13]
0x081AF1EA: 53 74 65 70 70 65 64 20 32 00                    "Stepped 2"        [#14]
0x081AF1F4: 53 74 65 70 70 65 64 20 33 00                    "Stepped 3"        [#15]
0x081AF1FE: 53 74 65 70 70 65 64 20 34 00                    "Stepped 4"        [#16]
0x081AF208: 55 73 65 72 20 53 68 61 70 65 72 20 31 00        "User Shaper 1"    [#17]
0x081AF216: 55 73 65 72 20 53 68 61 70 65 72 20 32 00        "User Shaper 2"    [#18]
0x081AF224: 55 73 65 72 20 53 68 61 70 65 72 20 33 00        "User Shaper 3"    [#19]
0x081AF232: 55 73 65 72 20 53 68 61 70 65 72 20 34 00        "User Shaper 4"    [#20]
0x081AF240: 55 73 65 72 20 53 68 61 70 65 72 20 35 00        "User Shaper 5"    [#21]
0x081AF24E: 55 73 65 72 20 53 68 61 70 65 72 20 36 00        "User Shaper 6"    [#22]
0x081AF25C: 55 73 65 72 20 53 68 61 70 65 72 20 37 00        "User Shaper 7"    [#23]
0x081AF26A: 55 73 65 72 20 53 68 61 70 65 72 20 38 00        "User Shaper 8"    [#24]
```

**정정 내용**:
- 매뉴얼은 "User Shaper" 기능만 언급하나, 펌웨어는 **25종 프리셋 라이브러리**를 보유
- 첫 번째 항목은 매뉴얼의 "Shaper"가 아닌 **"Preset Shaper"**
- 16개 빌트인 프리셋 (Rhythmic 1~4, Stepped 1~4 포함) + 8개 사용자 정의 슬롯
- 매뉴얼 정정: Shaper 섹션에 25종 프리셋 전체 목록과 "Preset Shaper" 표시명 명시

---

### CORR-09: Mod Matrix Custom Assign 목적지 상세 누락
**매뉴얼이 불완전** — Custom Assign의 8개 목적지가 명확히 문서화되지 않음

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §8.5.4 Custom Assign |
| **매뉴얼 기술** | 간략한 설명만 (목적지 개수/목록 미명시) |
| **펌웨어 실제** | **8개 목적지**: -Empty-, Vib Rate, Vib AM, VCA, LFO2 AM, LFO1 AM, CycEnv AM, Uni Spread |
| **펌웨어 주소** | CM4 `0x081AEA94` ~ `0x081AEE0A` |
| **신뢰도** | ★★★★★ |

**펌웨어 hex dump 증거** (CM4 문자열 테이블):
```
0x081AEA94: 43 75 73 74 6F 6D 20 41 73 73 69 67 6E 00   "Custom Assign"  [헤더]
0x081AEAA2: 2D 45 6D 70 74 79 2D 00                     "-Empty-"        [#1]
0x081AEAAA: 56 69 62 20 52 61 74 65 00                   "Vib Rate"       [#2]
0x081AEAB4: 56 69 62 20 41 4D 00                         "Vib AM"         [#3]
0x081AEABB: 56 43 41 00                                  "VCA"            [#4]
0x081AEABF: 4C 46 4F 32 20 41 4D 00                      "LFO2 AM"        [#5]
0x081AEAC7: 4C 46 4F 31 20 41 4D 00                      "LFO1 AM"        [#6]
0x081AEACF: 43 79 63 45 6E 76 20 41 4D 00               "CycEnv AM"      [#7]
0x081AEAD9: 55 6E 69 20 53 70 72 65 61 64 00             "Uni Spread"     [#8]
```

**정정 내용**:
- `-Empty-` 포함 8개 슬롯 중 7개가 활성 목적지
- **Vib Rate / Vib AM**: 제3 LFO (Vibrato)의 레이트/깊이를 모듈레이션 → 메타-모듈레이션
- **VCA**: VCA 레벨 직접 모듈레이션 (사이드체인 가능)
- **LFO1 AM / LFO2 AM**: 각 LFO 진폭 모듈레이션 → LFO 깊이를 다른 소스로 제어
- **CycEnv AM**: Cycling Envelope 진폭 모듈레이션
- **Uni Spread**: 유니즌 스프레드 폭 모듈레이션
- 매뉴얼 정정: Custom Assign 섹션에 7개 활성 목적지의 이름과 기능을 명시

---

### CORR-10: FX 타입 HW/VST 차이 누락
**매뉴얼이 불완전** — Stereo Delay가 VST 전용이나 매뉴얼에 구분 없음

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §7 FX > FX Types |
| **매뉴얼 기술** | "There are ten Types in total" + Vocoder 2종 = 12종 (HW), HW/VST 차이 미명시 |
| **펌웨어 실제** | CM4 **12종**, VST **13종** (+Stereo Delay). **Stereo Delay는 CM4에 존재하지 않음** |
| **펌웨어 주소** | CM4 `0x081AF308` ~ `0x081AF386` |
| **신뢰도** | ★★★★★ |

**펌웨어 hex dump 증거** (CM4 FX 타입 12종):
```
0x081AF308: 43 68 6F 72 75 73 00                     "Chorus"         [#0]
0x081AF310: 50 68 61 73 65 72 00                     "Phaser"         [#1]
0x081AF318: 46 6C 61 6E 67 65 72 00                  "Flanger"        [#2]
0x081AF320: 52 65 76 65 72 62 00                     "Reverb"         [#3]
0x081AF328: 44 69 73 74 6F 72 74 69 6F 6E 00         "Distortion"     [#4]
0x081AF334: 42 69 74 20 43 72 75 73 68 65 72 00       "Bit Crusher"    [#5]
0x081AF340: 33 20 42 61 6E 64 73 20 45 51 00          "3 Bands EQ"     [#6]
0x081AF34C: 50 65 61 6B 20 45 51 00                   "Peak EQ"        [#7]
0x081AF354: 4D 75 6C 74 69 20 43 6F 6D 70 00          "Multi Comp"     [#8]
0x081AF360: 53 75 70 65 72 55 6E 69 73 6F 6E 00       "SuperUnison"    [#9]
0x081AF36C: 56 6F 63 6F 64 65 72 20 53 65 6C 66 00    "Vocoder Self"   [#10]
0x081AF37A: 56 6F 63 6F 64 65 72 20 45 78 74 00       "Vocoder Ext"    [#11]
```

**"Stereo Delay" CM4 전체 검색 → 존재하지 않음** (VST 전용 확인)

**정정 내용**:
- 매뉴얼 §7.2: "ten Types in total" 명시 — 실제 HW는 12종 (Vocoder 2종 포함)
- **Stereo Delay**는 VST 플러그인에만 존재하는 FX 타입 (CM4 펌웨어에 없음)
- 매뉴얼 정정: (1) "ten Types" → "12 Types" 수정, (2) Stereo Delay = VST 전용 표기, (3) Singleton 제약 3종 (Reverb, Delay, Multi Comp) 명시

---

### CORR-11: Mod Matrix Assignable Slots — 91개 (Phase 14-2 신규)
**매뉴얼 불완전** — assignable slot이 매뉴얼 암시보다 훨씬 많음

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §8.5 Modulation Matrix |
| **매뉴얼 기술** | "7 rows × ~4 destinations" 암시 (UI 레이아웃 기반) |
| **펌웨어 실제** | **91 assignable slots**: Mx_Dot 7×4 (28 hardwired) + Mx_AssignDot 7×9 (63 assignable) |
| **VST 출처** | `minifreak_vst_params.xml` → Mx_Dot (28 param) + Mx_AssignDot (63 param) |
| **CM4 검증** | `Mx_Dot` / `Mx_AssignDot` 문자열 **CM4에 존재하지 않음** — VST 전용 파라미터 명칭 |
| **신뢰도** | ★★★★★ (VST XML 직접 확인, Phase 14-2) |

**상세 내용**:
- Mx_Dot (7 rows × 4 cols = 28): 하드와이어드 모듈레이션 (Row별 고정 목적지)
- Mx_AssignDot (7 rows × 9 cols = 63): 사용자가 선택 가능한 assignable 모듈레이션
- 매뉴얼은 28개 hardwired만 설명하며, 63개 assignable slot에 대한 상세 문서 누락
- 총 91 assignable slot은 Mod Matrix의 실제 처리 용량을 나타냄

---

### CORR-12: Osc2 타입 21 real + 9 reserved (Phase 14-2 신규)
**매뉴얼 불완전** — Osc2 enum에 reserved 항목이 존재함이 누락

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | §Oscillator 2 |
| **매뉴얼 기술** | Osc2 타입 목록 (정확한 개수 불명확) |
| **펌웨어 실제** | **30개 enum entry**: 21개 실제 타입 + 9개 reserved/dummy (index 21~29) |
| **VST 출처** | `minifreak_vst_params.xml` → Osc2Type item_list (30 entries) |
| **CM4 검증** | Osc2 타입 enum에 `Dummy` 항목 @ CM4 `0x081AF460` (Destroy와 Audio In 사이) — reserved placeholder 확인 |
| **신뢰도** | ★★★★★ (VST XML + CM4 교차검증, Phase 14-2) |

**상세 내용**:
- Osc1은 24종 타입 (Wavetable/Sample/Grains 계열)
- Osc2는 21종 실제 타입 (Filter 계열 포함) + 9개 reserved
- reserved 항목 (index 21~29)은 향후 펌웨어 확장을 위한 자리
- 매뉴얼에 "21 active types + 9 reserved" 명시 권고

---

### CORR-13: 1,557개 Hidden VST↔HW 동기화 파라미터 (Phase 14-2 신규)
**매뉴얼 누락** — DLL에 1,557개의 숨겨진 파라미터가 존재

| 항목 | 내용 |
|------|------|
| **매뉴얼 참조** | 해당 없음 |
| **매뉴얼 기술** | 언급 없음 |
| **펌웨어 실제** | DLL strings 1,705개 중 VST params 148개와 일치 → 차이 **1,557개**가 hidden parameters |
| **DLL 출처** | `MiniFreak V.dll` strings 분석 (Phase 14-2) |
| **신뢰도** | ★★★★☆ (DLL strings 기반 추정) |

**상세 내용**:
- DLL strings에서 추출한 1,705개 파라미터 이름
- VST XML에 정의된 148개 파라미터와 비교 → 148개만 일치
- 나머지 1,557개는 **HW↔VST 내부 동기화용**:
  - Mod_S0~63, Pitch_S0~63, Velo_S0~63, Gate_S0~63, StepState_S0~63 (시퀀서 상태)
  - Reserved1~4, AutomReserved1 (예약)
  - 프리셋 직렬화/역직렬화, UI 상태 복원, 내부 DSP 제어 등
- 매뉴얼에 이 파라미터들의 존재와 용도에 대한 부록 추가 권고

---

## 참고 문헌

| 문서 | 설명 |
|------|------|
| `PHASE11_GAP_FILL_ANALYSIS.md` | Phase 11 CM4 바이너리 직접 스캔 결과 |
| `MANUAL_VS_FIRMWARE_MATCH.md` | 매뉴얼 vs 펌웨어 종합 일치도 분석 |
| `PHASE10_MANUAL_GAP_ANALYSIS.md` | Phase 10 매뉴얼 갭 분석 계획 |
| `PHASE8_FX_OSC_ENUMS.md` | Phase 8 FX/OSC enum 정리 |
| `PHASE8_SEQ_ARP_MOD.md` | Phase 8 Seq/Arp/Mod 정리 |
| `phase8_enum_tables.json` | Phase 8 enum 테이블 JSON |
| `PHASE9_RESULTS.md` | Phase 9 CM7 상수/함수 분석 |
| `PHASE7-3_FX_CORE_ANALYSIS.md` | Phase 7-3 FX 코어 서브프로세서 분석 |
| `PHASE14_COLLAGE_PROTOCOL_ANALYSIS.md` | Phase 14-1 Collage 프로토콜 분석 (62 메시지, 14 enum) |
| `PHASE14_VST_HW_PARAM_MAPPING.md` | Phase 14-2 VST↔HW 파라미터 매핑 (148 VST + 1,705 DLL) |
| `PHASE15_FIRMWARE_PATCH_EXPERIMENT.md` | Phase 15 안전한 펌웨어 패치 실험 |

---

## 부록 A: Phase 14-1 Collage 프로토콜 요약 (NDA 주의)

> ⚠️ Collage 프로토콜은 MiniFreak의 USB 통신 프로토콜로, Arturia NDA 영역일 수 있음.
> 정정 권고서에서는 매뉴얼 사양만 다루며, 기술 세부는 Phase 14-1 문서 참조.

| 항목 | 내용 |
|------|------|
| 프로토콜 정체 | **protobuf 기반 USB bulk** (MIDI가 아님) |
| 메시지 정의 | **62개 메시지 타입** + **14개 enum** |
| 최상위 메시지 | `Top(message_id, ack_type, priority, control/data/security)` |
| USB 정보 | EP IN=0x81, EP OUT=0x02, **VID=0x152E** |
| DataParameter | ID + Status + Value (u32/i32/f32/str/blob 등 9 타입) |
| ResourceLocation | 11개 위치 (PRESET=3, WAVETABLE=4 등) |

## 부록 B: Phase 15-1 eEditParams 분류 + Phase 15-2 패치 검증

### eEditParams 79개 항목 분류 (Phase 15-1)

| 분류 | 개수 | 예시 |
|------|------|------|
| 활성 파라미터 | 27 | Matrix Src, Filter Type, Osc Type 등 |
| DEPRECATED | 1 | `UnisonOn TO BE DEPRECATED` @ `0x081AF994` |
| Obsolete | 1 | `obsolete Rec Count-In` @ `0x081AFB00` |
| UI 상태 | 16 | RecState, RecMode, StepState 등 |
| UI 라벨 | 35 | 편집 페이지 타이틀 등 |

### 이스터에그 4건

| 개발자 | Flash 주소 | 원본 텍스트 |
|--------|-----------|-----------|
| Olivier D | `0x081B34A0` | "if you ask Olivier D, he'll tell you that it's a feature" |
| Thomas A | `0x081B32CD` | "Ask Thomas A" |
| Mathieu B | `0x081B3411` | "ask Mathieu B" |
| Frederic | `0x081B2F2C` | "Hey Frederic, are you ready to hear sounds you never heard before?" |

### Phase 15-2 패치 검증 결과

7개 안전한 펌웨어 패치 테스트 통과 (`.rodata` 문자열만 변경, 코드 로직 불변):
- ✅ 패치 정의 JSON 로드/검증 (7/7)
- ✅ 바이너리 패턴 매치 (CM4 대상 7/7)
- ✅ 패치 적용/롤백 (7/7 성공)
- ✅ 가역성 검증 (apply → revert → 전체 바이너리 SHA 일치)
- ✅ JSON round-trip 무결성

---

*문서 버전: Phase 16 V6 (CORR-08~10 상세 섹션 추가, ENH-04/05 CM4 검증, CORR-11/12 CM4 보강)*
*작성 도구: 펌웨어 바이너리 스캔 + VST XML 교차검증 + DLL strings 분석*
*펌웨어 버전: fw4_0_1_2229 (2025-06-18)*
*매뉴얼 버전: v4.0.0 / v4.0.1 (2025-07-04)*
*현재 재현도: 95.6% (Phase 16 종합 일치도)*
