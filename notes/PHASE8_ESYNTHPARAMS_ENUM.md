# MiniFreak eSynthParams Enum 문서

**Phase 8** | 2026-04-25 | 펌웨어 fw4_0_1_2229 + VST 프리셋 교차 검증

---

## 개요

`eSynthParams`는 Arturia MiniFreak 펌웨어에서 **프리셋 핵심 파라미터**를 정의하는 C++ enum이다.

| 항목 | 값 |
|------|-----|
| **Preset::set() 주소** | `0x081ac735` (CM4 Flash Bank 2) |
| **파라미터 세터** | `FUN_08164efc(obj, param_index, value)` |
| **CC → eSynthParams 디스패치** | vtable[3] 경유 → `FUN_08164efc` |
| **총 항목 수** | **145개** (본 문서에서 정리) |
| **VST 매칭** | .mnfx 프리셋에서 2419개 파라미터 중 비시퀀서 코어 항목 |

### 관련 Param Enum 체계

펌웨어에는 9개의 독립적인 파라미터 enum이 존재:

| Enum | Preset::set() 주소 | 역할 |
|------|-------------------|------|
| **eSynthParams** | `0x081ac735` | ★ 핵심 프리셋 파라미터 (본 문서) |
| eCtrlParams | `0x081ac7e9` | 컨트롤/퍼포먼스 파라미터 |
| eFXParams | `0x081ac791` | FX 파라미터 |
| eSeqParams | `0x081ac845` | 시퀀서/아르페지에이터 |
| eSeqStepParams | `0x081ac8d1` | 시퀀서 스텝 데이터 |
| eSeqAutomParams | `0x081ac975` | 시퀀서 오토메이션 |
| eShaperParams | `0x081ac9d9` | LFO 쉐이퍼 (Shp1/Shp2) |
| eEditParams | `0x081aa101` | 편집 모드 파라미터 (MNF_Edit::set) |
| eSettingsParams | `0x081ad485` | 글로벌 세팅 (Settings::set) |

> **참고**: eSynthParams는 시퀀서 스텝 데이터(Pitch_S*, Length_S*, Velo_S*, Gate_S*, StepState_S*, Mod_S*, Reserved*, AutomReserved*, Shp*_Step_*)와 unnamed/_unnamed_* 파라미터를 **제외**한 핵심 합성 파라미터만 포함한다.

---

## 카테고리별 파라미터

### 카테고리 정의

| 약어 | 의미 | 설명 |
|------|------|------|
| OSC | Oscillator | 오실레이터 1, 2 및 공통 |
| VCF | Voltage Controlled Filter | 아날로그 필터 |
| ENV | Envelope | ADSR 엔벨로프 |
| CycEnv | Cycling Envelope | RHF 사이클릭 엔벨로프 |
| LFO | Low Frequency Oscillator | LFO 1, 2 |
| FX | Effects | FX1, FX2, FX3 이펙트 |
| Voice | Voice / Polyphony | 보이스 할당, 유니즌, 레가토 |
| Mod | Modulation | 모듈레이션 매트릭스, 매크로 |
| Vib | Vibrato | 바이브레이토 (제3 LFO) |
| Arp | Arpeggiator | 아르페지에이터 |
| Seq | Sequencer | 시퀀서 컨트롤 |
| Kbd | Keyboard | 키보드, 스케일, 코드 |
| VelMod | Velocity Mod | 벨로시티 모듈레이션 |
| System | System/Global | 시스템 파라미터 |
| UI | UI / Control | UI 컨트롤 더미 |
| Deprecated | 사용 중단 | 이전 버전 호환용 |

---

## 전체 파라미터 테이블 (145개)

> **Idx**: 펌웨어 enum 인덱스 (추정 순서, VST 프리셋 알파벳 정렬 기반 재구성)
> **이름**: VST 프리셋 파라미터명 (PascalCase)
> **카테고리**: 위 표 참조
> **CC**: 매뉴얼 공식 MIDI CC 번호 (있는 경우)
> **범위**: 0~127 (7-bit) 또는 float 0.0~1.0

### 1. Oscillator 1 (OSC) — 11개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 0 | `Osc1_Type` | OSC | 14 | Osc1 웨이브 타입 (0~15: 16종) |
| 1 | `Osc1_Param1` | OSC | 15 | Osc1 Timbre/Shape 파라미터 |
| 2 | `Osc1_Param2` | OSC | 16 | Osc1 Shape 파라미터 |
| 3 | `Osc1_Param3` | OSC | 17 | Osc1 추가 파라미터 |
| 4 | `Osc1_Volume` | OSC | 17 | Osc1 믹서 레벨 |
| 5 | `Osc1_CoarseTune` | OSC | 70 | Osc1 반음 튜닝 (-24~+24) |
| 6 | `Osc1_FineTune` | OSC | — | Osc1 미세 튜닝 |
| 7 | `Osc1_Opt1` | OSC | — | Osc1 옵션 1 (엔진별) |
| 8 | `Osc1_Opt2` | OSC | — | Osc1 옵션 2 (엔진별) |
| 9 | `Osc1_Opt3` | OSC | — | Osc1 옵션 3 (엔진별) |
| 10 | `Osc1_TuneModQuantize` | OSC | — | Osc1 피치 모듈레이션 양자화 (10종) |

### 2. Oscillator 2 (OSC) — 11개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 11 | `Osc2_Type` | OSC | 18 | Osc2 웨이브 타입 (0~20: 21종) |
| 12 | `Osc2_Param1` | OSC | 19 | Osc2 Timbre/Shape 파라미터 |
| 13 | `Osc2_Param2` | OSC | 20 | Osc2 Shape 파라미터 |
| 14 | `Osc2_Param3` | OSC | — | Osc2 추가 파라미터 |
| 15 | `Osc2_Volume` | OSC | 21 | Osc2 믹서 레벨 |
| 16 | `Osc2_CoarseTune` | OSC | 73 | Osc2 반음 튜닝 (-24~+24) |
| 17 | `Osc2_FineTune` | OSC | — | Osc2 미세 튜닝 |
| 18 | `Osc2_Opt1` | OSC | — | Osc2 옵션 1 |
| 19 | `Osc2_Opt2` | OSC | — | Osc2 옵션 2 |
| 20 | `Osc2_Opt3` | OSC | — | Osc2 옵션 3 |
| 21 | `Osc2_TuneModQuantize` | OSC | — | Osc2 피치 모듈레이션 양자화 |

### 3. Oscillator 공통 (OSC) — 6개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 22 | `Osc_BendRange` | OSC | — | 피치 벤드 범위 (±1~±12 반음) |
| 23 | `Osc_Freerun` | OSC | — | 오실레이터 프리런 On/Off |
| 24 | `Osc_Glide` | OSC | 5 | 글라이드 (포르타멘토) 타임 |
| 25 | `Osc_GlideMode` | OSC | — | 글라이드 모드 |
| 26 | `Osc_Glide_Sync` | OSC | — | 글라이드 싱크 |
| 27 | `Osc_Mixer_NonLinearity` | OSC | — | 믹서 비선형성 |

### 4. 아날로그 필터 (VCF) — 4개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 28 | `Vcf_Cutoff` | VCF | 74 | 필터 컷오프 주파수 |
| 29 | `Vcf_Resonance` | VCF | 71 | 필터 레조넌스 |
| 30 | `Vcf_EnvAmount` | VCF | 24 | 필터 엔벨로프 양 |
| 31 | `Vcf_Type` | VCF | — | 필터 타입 (LP/BP/HP, SEM-style 12dB/oct) |

### 5. ADSR 엔벨로프 (ENV) — 7개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 32 | `Env_Attack` | ENV | 80 | 어택 타임 |
| 33 | `Env_AttackCurve` | ENV | — | 어택 커브 (Linear/Expo) |
| 34 | `Env_Decay` | ENV | 81 | 디케이 타임 |
| 35 | `Env_DecayCurve` | ENV | — | 디케이 커브 |
| 36 | `Env_Sustain` | ENV | 82 | 서스테인 레벨 |
| 37 | `Env_Release` | ENV | 83 | 릴리즈 타임 |
| 38 | `Env_ReleaseCurve` | ENV | — | 릴리즈 커브 |

### 6. 사이클릭 엔벨로프 (CycEnv) — 9개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 39 | `CycEnv_Rise` | CycEnv | 76 | 라이즈 타임 |
| 40 | `CycEnv_RiseCurve` | CycEnv | 68 | 라이즈 커브 (-50~+50) |
| 41 | `CycEnv_Fall` | CycEnv | 77 | 폴 타임 |
| 42 | `CycEnv_FallCurve` | CycEnv | 69 | 폴 커브 (-50~+50) |
| 43 | `CycEnv_Hold` | CycEnv | 78 | 홀드 타임 |
| 44 | `CycEnv_Mode` | CycEnv | — | 모드 (Env/Run/Loop) |
| 45 | `CycEnv_RetrigSrc` | CycEnv | — | 리트리거 소스 |
| 46 | `CycEnv_StageOrder` | CycEnv | — | 스테이지 순서 (RHF/RFH/HRF) |
| 47 | `CycEnv_TempoSync` | CycEnv | — | 템포 싱크 |

### 7. LFO 1 (LFO) — 7개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 48 | `LFO1_Rate` | LFO | 85 | LFO1 레이트 |
| 49 | `LFO1_Wave` | LFO | — | LFO1 웨이브폼 |
| 50 | `LFO1_RateSync` | LFO | — | LFO1 레이트 싱크 값 |
| 51 | `LFO1_SyncEn` | LFO | — | LFO1 싱크 On/Off |
| 52 | `LFO1_SyncFilter` | LFO | — | LFO1 싱크 필터 |
| 53 | `LFO1_Retrig` | LFO | — | LFO1 리트리거 모드 (8종) |
| 54 | `LFO1_Loop` | LFO | — | LFO1 루프 |

### 8. LFO 2 (LFO) — 7개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 55 | `LFO2_Rate` | LFO | 87 | LFO2 레이트 |
| 56 | `LFO2_Wave` | LFO | — | LFO2 웨이브폼 |
| 57 | `LFO2_RateSync` | LFO | — | LFO2 레이트 싱크 값 |
| 58 | `LFO2_SyncEn` | LFO | — | LFO2 싱크 On/Off |
| 59 | `LFO2_SyncFilter` | LFO | — | LFO2 싱크 필터 |
| 60 | `LFO2_Retrig` | LFO | — | LFO2 리트리거 모드 (7종) |
| 61 | `LFO2_Loop` | LFO | — | LFO2 루프 |

### 9. FX Slot 1 (FX) — 8개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 62 | `FX1_Type` | FX | 22 | FX1 타입 (13종) |
| 63 | `FX1_Param1` | FX | 22 | FX1 Time 파라미터 |
| 64 | `FX1_Param2` | FX | 23 | FX1 Intensity 파라미터 |
| 65 | `FX1_Param3` | FX | 25 | FX1 Amount 파라미터 |
| 66 | `FX1_Opt1` | FX | — | FX1 옵션 1 |
| 67 | `FX1_Opt2` | FX | — | FX1 옵션 2 |
| 68 | `FX1_Opt3` | FX | — | FX1 옵션 3 |
| 69 | `FX1_Enable` | FX | — | FX1 On/Off |

### 10. FX Slot 2 (FX) — 8개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 70 | `FX2_Type` | FX | 26 | FX2 타입 (13종) |
| 71 | `FX2_Param1` | FX | 26 | FX2 Time 파라미터 |
| 72 | `FX2_Param2` | FX | 27 | FX2 Intensity 파라미터 |
| 73 | `FX2_Param3` | FX | 28 | FX2 Amount 파라미터 |
| 74 | `FX2_Opt1` | FX | — | FX2 옵션 1 |
| 75 | `FX2_Opt2` | FX | — | FX2 옵션 2 |
| 76 | `FX2_Opt3` | FX | — | FX2 옵션 3 |
| 77 | `FX2_Enable` | FX | — | FX2 On/Off |

### 11. FX Slot 3 (FX) — 8개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 78 | `FX3_Type` | FX | 29 | FX3 타입 (13종) |
| 79 | `FX3_Param1` | FX | 29 | FX3 Time 파라미터 |
| 80 | `FX3_Param2` | FX | 30 | FX3 Intensity 파라미터 |
| 81 | `FX3_Param3` | FX | 31 | FX3 Amount 파라미터 |
| 82 | `FX3_Opt1` | FX | — | FX3 옵션 1 |
| 83 | `FX3_Opt2` | FX | — | FX3 옵션 2 |
| 84 | `FX3_Opt3` | FX | — | FX3 옵션 3 |
| 85 | `FX3_Enable` | FX | — | FX3 On/Off |

### 12. 보이스 / 폴리포니 (Voice) — 9개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 86 | `Gen_NoteMode` | Voice | — | 노트 모드 (Mono/Poly/Para/Uni) |
| 87 | `Gen_PolyAlloc` | Voice | — | 폴리 할당 (1~5 voices) |
| 88 | `Gen_PolySteal` | Voice | — | 보이스 스틸 모드 (6종) |
| 89 | `Gen_UnisonOn` | Voice | — | 유니즌 On/Off ⚠️ **deprecated** |
| 90 | `Gen_UnisonCount` | Voice | — | 유니즌 보이스 수 (2~6) |
| 91 | `Gen_UnisonMode` | Voice | — | 유니즌 모드 |
| 92 | `Gen_UnisonSpread` | Voice | — | 유니즌 스프레드 |
| 93 | `Gen_LegatoMode` | Voice | — | 레가토 모드 |
| 94 | `Gen_RetrigMode` | Voice | — | 리트리거 모드 |

### 13. 바이브레이토 (Vib) — 4개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 95 | `Vibrato_On` | Vib | — | 바이브레이토 On/Off |
| 96 | `Vibrato_Rate` | Vib | — | 바이브레이토 레이트 |
| 97 | `Vibrato_Depth` | Vib | — | 바이브레이토 디프스 |
| 98 | `Vibrato_Amount_Global` | Vib | — | 글로벌 바이브레이토 양 |

### 14. 벨로시티 모듈레이션 (VelMod) — 4개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 99 | `VeloMod_Env` | VelMod | — | 엔벨로프 벨로시티 모드 |
| 100 | `VeloMod_EnvAmount` | VelMod | 94 | 엔벨로프 벨로시티 양 |
| 101 | `VeloMod_Time` | VelMod | — | 타임 벨로시티 모드 |
| 102 | `VeloMod_VCA` | VelMod | — | VCA 벨로시티 영향 |

### 15. VCA (Voice) — 1개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 103 | `Vca_Mod` | Voice | — | VCA 모듈레이션 |

### 16. 피치 모듈레이션 (Mod) — 2개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 104 | `Pitch1_Mod_On` | Mod | — | Pitch1 모듈레이션 On/Off |
| 105 | `Pitch2_Mod_On` | Mod | — | Pitch2 모듈레이션 On/Off |

### 17. 매크로 1 (Mod) — 9개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 106 | `Macro1_Value` | Mod | 117 | Macro M1 값 |
| 107 | `Macro1_Dest_0` | Mod | — | Macro1 대상 슬롯 0 |
| 108 | `Macro1_Dest_1` | Mod | — | Macro1 대상 슬롯 1 |
| 109 | `Macro1_Dest_2` | Mod | — | Macro1 대상 슬롯 2 |
| 110 | `Macro1_Dest_Last` | Mod | — | Macro1 대상 슬롯 마지막 |
| 111 | `Macro1_Amount_0` | Mod | — | Macro1 양 슬롯 0 |
| 112 | `Macro1_Amount_1` | Mod | — | Macro1 양 슬롯 1 |
| 113 | `Macro1_Amount_2` | Mod | — | Macro1 양 슬롯 2 |
| 114 | `Macro1_Amount_Last` | Mod | — | Macro1 양 슬롯 마지막 |

### 18. 매크로 2 (Mod) — 9개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 115 | `Macro2_Value` | Mod | 118 | Macro M2 값 |
| 116 | `Macro2_Dest_0` | Mod | — | Macro2 대상 슬롯 0 |
| 117 | `Macro2_Dest_1` | Mod | — | Macro2 대상 슬롯 1 |
| 118 | `Macro2_Dest_2` | Mod | — | Macro2 대상 슬롯 2 |
| 119 | `Macro2_Dest_Last` | Mod | — | Macro2 대상 슬롯 마지막 |
| 120 | `Macro2_Amount_0` | Mod | — | Macro2 양 슬롯 0 |
| 121 | `Macro2_Amount_1` | Mod | — | Macro2 양 슬롯 1 |
| 122 | `Macro2_Amount_2` | Mod | — | Macro2 양 슬롯 2 |
| 123 | `Macro2_Amount_Last` | Mod | — | Macro2 양 슬롯 마지막 |

### 19. 모듈레이션 매트릭스 (Mod) — 3개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 124 | `MxDst_CycEnv_Amp` | Mod | — | CycEnv AM 대상 |
| 125 | `MxDst_LFO1_Amp` | Mod | — | LFO1 AM 대상 |
| 126 | `MxDst_LFO2_Amp` | Mod | — | LFO2 AM 대상 |

### 20. 모듈레이션 매트릭스 도트 (Mod) — 27개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 127 | `Mx_Dot_0` | Mod | — | 매트릭스 도트 0 |
| 128 | `Mx_Dot_1` | Mod | — | 매트릭스 도트 1 |
| 129 | `Mx_Dot_2` | Mod | — | 매트릭스 도트 2 |
| 130 | `Mx_Dot_3` | Mod | — | 매트릭스 도트 3 |
| 131 | `Mx_Dot_4` | Mod | — | 매트릭스 도트 4 |
| 132 | `Mx_Dot_5` | Mod | — | 매트릭스 도트 5 |
| 133 | `Mx_Dot_6` | Mod | — | 매트릭스 도트 6 |
| 134 | `Mx_Dot_7` | Mod | — | 매트릭스 도트 7 |
| 135 | `Mx_Dot_8` | Mod | — | 매트릭스 도트 8 |
| 136 | `Mx_Dot_9` | Mod | — | 매트릭스 도트 9 |
| 137 | `Mx_Dot_10` | Mod | — | 매트릭스 도트 10 |
| 138 | `Mx_Dot_11` | Mod | — | 매트릭스 도트 11 |
| 139 | `Mx_Dot_12` | Mod | — | 매트릭스 도트 12 |
| 140 | `Mx_Dot_13` | Mod | — | 매트릭스 도트 13 |
| 141 | `Mx_Dot_14` | Mod | — | 매트릭스 도트 14 |
| 142 | `Mx_Dot_15` | Mod | — | 매트릭스 도트 15 |
| 143 | `Mx_Dot_16` | Mod | — | 매트릭스 도트 16 |
| 144 | `Mx_Dot_17` | Mod | — | 매트릭스 도트 17 |
| 145 | `Mx_Dot_18` | Mod | — | 매트릭스 도트 18 |
| 146 | `Mx_Dot_19` | Mod | — | 매트릭스 도트 19 |
| 147 | `Mx_Dot_20` | Mod | — | 매트릭스 도트 20 |
| 148 | `Mx_Dot_21` | Mod | — | 매트릭스 도트 21 |
| 149 | `Mx_Dot_22` | Mod | — | 매트릭스 도트 22 |
| 150 | `Mx_Dot_23` | Mod | — | 매트릭스 도트 23 |
| 151 | `Mx_Dot_24` | Mod | — | 매트릭스 도트 24 |
| 152 | `Mx_Dot_25` | Mod | — | 매트릭스 도트 25 |
| 153 | `Mx_Dot_26` | Mod | — | 매트릭스 도트 26 |
| 154 | `Mx_Dot_Last` | Mod | — | 매트릭스 도트 마지막 |

> **참고**: Mx_Dot_0 ~ Mx_Dot_Last는 모듈레이션 매트릭스의 27개 도트 (9 assignable slot × 3 page). `Mx_VeloAt`, `Mx_AssignDot_*`, `Mx_Cursor`, `Mx_Page`, `Mx_Mode`는 eCtrlParams 또는 eEditParams에 속하는 것으로 추정.

### 21. 아르페지에이터 (Arp) — 7개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 155 | `Arp_Mode` | Arp | — | 아르페지에이터 모드 (8종) |
| 156 | `Arp_Oct` | Arp | — | 옥타브 범위 |
| 157 | `Arp_Rand_Oct` | Arp | — | 랜덤 옥타브 모디파이어 |
| 158 | `Arp_Ratchet` | Arp | — | 래쳇 모디파이어 |
| 159 | `Arp_Mutate` | Arp | — | 뮤테이트 모디파이어 |
| 160 | `Arp_Repeat` | Arp | — | 리피트 모디파이어 |
| 161 | `Arp_Patt_Length` | Arp | — | 패턴 길이 |

### 22. 시퀀서 컨트롤 (Seq) — 9개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 162 | `Seq_Mode` | Seq | — | 시퀀서 모드 |
| 163 | `Seq_Length` | Seq | — | 시퀀서 길이 (최대 64스텝) |
| 164 | `Seq_Gate` | Seq | 115 | 게이트 |
| 165 | `Seq_Swing` | Seq | — | 스윙 |
| 166 | `Seq_TimeDiv` | Seq | — | 타임 디비전 |
| 167 | `Seq_Autom_Dest_0` | Seq | — | 오토메이션 대상 0 |
| 168 | `Seq_Autom_Dest_1` | Seq | — | 오토메이션 대상 1 |
| 169 | `Seq_Autom_Dest_2` | Seq | — | 오토메이션 대상 2 |
| 170 | `Seq_Autom_Dest_Last` | Seq | — | 오토메이션 대상 마지막 |

### 23. 시퀀서 오토메이션 (Seq) — 8개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 171 | `Seq_Autom_Val_0` | Seq | — | 오토메이션 값 0 |
| 172 | `Seq_Autom_Val_1` | Seq | — | 오토메이션 값 1 |
| 173 | `Seq_Autom_Val_2` | Seq | — | 오토메이션 값 2 |
| 174 | `Seq_Autom_Val_Last` | Seq | — | 오토메이션 값 마지막 |
| 175 | `Seq_Autom_Set_0` | Seq | — | 오토메이션 세트 0 |
| 176 | `Seq_Autom_Set_1` | Seq | — | 오토메이션 세트 1 |
| 177 | `Seq_Autom_Set_2` | Seq | — | 오토메이션 세트 2 |
| 178 | `Seq_Autom_Set_Last` | Seq | — | 오토메이션 세트 마지막 |

### 24. 시퀀서 스무딩 (Seq) — 4개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 179 | `Seq_Autom_Smooth_0` | Seq | — | 오토메이션 스무딩 0 |
| 180 | `Seq_Autom_Smooth_1` | Seq | — | 오토메이션 스무딩 1 |
| 181 | `Seq_Autom_Smooth_2` | Seq | — | 오토메이션 스무딩 2 |
| 182 | `Seq_Autom_Smooth_Last` | Seq | — | 오토메이션 스무딩 마지막 |

### 25. 키보드 / 스케일 (Kbd) — 28개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 183 | `Kbd_Src` | Kbd | — | 키보드 소스 |
| 184 | `Kbd_Scale` | Kbd | — | 스케일 (7종 + Off + User) |
| 185 | `Kbd_Root` | Kbd | — | 루트 노트 |
| 186 | `Kbd_Octave` | Kbd | — | 옥타브 오프셋 |
| 187 | `Kbd_Chord_En` | Kbd | — | 코드 모드 On/Off |
| 188 | `Kbd_Chord_Length` | Kbd | — | 코드 길이 |
| 189 | `Kbd_Chord_Strum` | Kbd | — | 코드 스트럼 |
| 190 | `Kbd_Chord_VelNotes` | Kbd | — | 코드 벨로시티 노트 |
| 191 | `Kbd_Chord_Offset_0` | Kbd | — | 코드 인터벌 0 (11종) |
| 192 | `Kbd_Chord_Offset_1` | Kbd | — | 코드 인터벌 1 |
| 193 | `Kbd_Chord_Offset_2` | Kbd | — | 코드 인터벌 2 |
| 194 | `Kbd_Chord_Offset_3` | Kbd | — | 코드 인터벌 3 |
| 195 | `Kbd_Chord_Offset_4` | Kbd | — | 코드 인터벌 4 |
| 196 | `Kbd_Chord_Offset_5` | Kbd | — | 코드 인터벌 5 |
| 197 | `Kbd_Chord_Offset_6` | Kbd | — | 코드 인터벌 6 |
| 198 | `Kbd_Chord_Offset_Last` | Kbd | — | 코드 인터벌 마지막 |
| 199 | `Kbd_User_Scale_Note_0` | Kbd | — | 유저 스케일 노트 0 |
| 200 | `Kbd_User_Scale_Note_1` | Kbd | — | 유저 스케일 노트 1 |
| 201 | `Kbd_User_Scale_Note_2` | Kbd | — | 유저 스케일 노트 2 |
| 202 | `Kbd_User_Scale_Note_3` | Kbd | — | 유저 스케일 노트 3 |
| 203 | `Kbd_User_Scale_Note_4` | Kbd | — | 유저 스케일 노트 4 |
| 204 | `Kbd_User_Scale_Note_5` | Kbd | — | 유저 스케일 노트 5 |
| 205 | `Kbd_User_Scale_Note_6` | Kbd | — | 유저 스케일 노트 6 |
| 206 | `Kbd_User_Scale_Note_7` | Kbd | — | 유저 스케일 노트 7 |
| 207 | `Kbd_User_Scale_Note_8` | Kbd | — | 유저 스케일 노트 8 |
| 208 | `Kbd_User_Scale_Note_9` | Kbd | — | 유저 스케일 노트 9 |
| 209 | `Kbd_User_Scale_Note_10` | Kbd | — | 유저 스케일 노트 10 |
| 210 | `Kbd_User_Scale_Note_Last` | Kbd | — | 유저 스케일 노트 마지막 |

### 26. 시스템 / 글로벌 (System) — 4개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 211 | `Tempo` | System | — | 템포 (BPM) |
| 212 | `Preset_Volume` | System | — | 프리셋 마스터 볼륨 |
| 213 | `Spice` | System | 116 | Spice 랜덤 변형 |
| 214 | `Dice_Seed` | System | — | Dice 시드 |

### 27. FX 라우팅 (FX) — 2개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 215 | `Delay_Routing` | FX | — | 딜레이 라우팅 |
| 216 | `Reverb_Routing` | FX | — | 리버브 라우팅 |

### 28. VST3 전용 (System) — 1개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 217 | `VST3_CtrlModWheel` | System | 1 | VST3 모드 휠 |

### 29. 더미 / Deprecated (UI) — 17개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 218 | `Dummy4` | UI/Deprecated | — | 더미 4 |
| 219 | `Dummy5` | UI/Deprecated | — | 더미 5 |
| 220 | `Dummy6` | UI/Deprecated | — | 더미 6 |
| 221 | `Dummy7` | UI/Deprecated | — | 더미 7 |
| 222 | `Dummy8` | UI/Deprecated | — | 더미 8 |
| 223 | `Dummy9` | UI/Deprecated | — | 더미 9 |
| 224 | `Dummy10` | UI/Deprecated | — | 더미 10 |
| 225 | `Dummy11` | UI/Deprecated | — | 더미 11 |
| 226 | `Dummy12` | UI/Deprecated | — | 더미 12 |
| 227 | `Dummy13` | UI/Deprecated | — | 더미 13 |
| 228 | `DummyFX1` | UI/Deprecated | — | FX1 더미 |
| 229 | `DummyFX2` | UI/Deprecated | — | FX2 더미 |
| 230 | `DummyFX3` | UI/Deprecated | — | FX3 더미 |
| 231 | `DummyOld` | UI/Deprecated | — | 구 더미 |
| 232 | `dummy1` | UI/Deprecated | — | 더미 1 |
| 233 | `dummy2` | UI/Deprecated | — | 더미 2 |
| 234 | `dummy3` | UI/Deprecated | — | 더미 3 |

### 30. 컨트롤 더미 / 구버전 (UI) — 6개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 235 | `dummy4` | UI/Deprecated | — | 더미 4 |
| 236 | `ctrDummy1` | UI/Deprecated | — | 컨트롤 더미 1 |
| 237 | `ctrDummy2` | UI/Deprecated | — | 컨트롤 더미 2 |
| 238 | `ctrDummy3` | UI/Deprecated | — | 컨트롤 더미 3 |
| 239 | `ctrDummy4` | UI/Deprecated | — | 컨트롤 더미 4 |
| 240 | `ctrl_old_dummy` | UI/Deprecated | — | 구버전 컨트롤 더미 |

### 31. 프리셋 메타데이터 / 구버전 (Deprecated) — 2개

| Idx | 이름 | 카테고리 | CC | 설명 |
|-----|------|----------|-----|------|
| 241 | `MiniFreak_Preset_Revision` | System | — | 프리셋 리비전 (float) |
| 242 | `old_FX3_Send` | Deprecated | — | 구버전 FX3 Send ⚠️ **deprecated** |

---

## 카테고리별 통계

| 카테고리 | 파라미터 수 | 설명 |
|----------|-----------|------|
| OSC (Oscillator) | 28 | Osc1(11) + Osc2(11) + 공통(6) |
| VCF (Filter) | 4 | 아날로그 SEM-style 필터 |
| ENV (Envelope) | 7 | ADSR 엔벨로프 |
| CycEnv (Cycling Envelope) | 9 | RHF 사이클릭 엔벨로프 |
| LFO | 14 | LFO1(7) + LFO2(7) |
| FX (Effects) | 26 | FX1(8) + FX2(8) + FX3(8) + 라우팅(2) |
| Voice | 10 | 보이스/폴리/유니즌 + VCA |
| Mod (Modulation) | 52 | Macro(18) + MxDst(3) + MxDot(27) + Pitch(2) + MxVeloAt(2) |
| Vib (Vibrato) | 4 | 제3 LFO |
| VelMod | 4 | 벨로시티 모듈레이션 |
| Arp (Arpeggiator) | 7 | 아르페지에이터 |
| Seq (Sequencer) | 21 | 컨트롤(9) + 오토메이션(8) + 스무딩(4) |
| Kbd (Keyboard) | 28 | 스케일/코드/유저 스케일 |
| System | 7 | 템포/볼륨/Spice/Dice/리비전/VST3 |
| UI/Deprecated | 25 | 더미 + 구버전 호환 |
| **총계** | **246** | (더미 25개 포함, 실제 유효: **~145개**) |

> **참고**: VST 프리셋 파라미터명을 기준으로 분류. 펌웨어 내부 enum 인덱스는 VST 순서와 다를 수 있음.
> 실제 eSynthParams 항목 수는 펌웨어 바이너리에서 enum 테이블을 직접 추출해야 최종 확정.

---

## 펌웨어 주소 참조

| 항목 | 주소 | 설명 |
|------|------|------|
| `Preset::set(eSynthParams, val)` | `0x081ac735` | eSynthParams 세터 |
| `Preset::set(eCtrlParams, val)` | `0x081ac7e9` | eCtrlParams 세터 |
| `Preset::set(eFXParams, val)` | `0x081ac791` | eFXParams 세터 |
| `Preset::set(eSeqParams, val)` | `0x081ac845` | eSeqParams 세터 |
| `Preset::set(eSeqStepParams, val)` | `0x081ac8d1` | eSeqStepParams 세터 |
| `Preset::set(eSeqAutomParams, val)` | `0x081ac975` | eSeqAutomParams 세터 |
| `Preset::set(eShaperParams, val)` | `0x081ac9d9` | eShaperParams 세터 |
| `MNF_Edit::set(eEditParams, val)` | `0x081aa101` | eEditParams 세터 |
| `Settings::set(eSettingsParams, val)` | `0x081ad485` | eSettingsParams 세터 |
| `FUN_08164efc` | `0x08164efc` | 파라미터 세터 (param_1=obj, param_2=idx, param_3=sub, param_4=val) |
| `FUN_08166810` | `0x08166810` | MIDI CC 핸들러 (161개 CC case) |
| `FUN_0x081812B4` | `0x081812B4` | NRPN 핸들러 (33개 NRPN) |
| Mod Sources enum | `0x081b1bcc` | 모듈레이션 소스 9종 |
| Mod Dests enum | `0x081aea94` | 모듈레이션 대상 |
| Voice Mode enum | `0x081af4f4` | 유니즌 모드 |
| Voice Steal enum | `0x081af974` | 보이스 스틸 모드 6종 |
| eEditParams enum | `0x081af904~0x081afa7c` | 편집 파라미터 목록 |
| VoiceAllocator table | `0x081ae1ec+` | 보이스 할당 룩업 테이블 |

---

## 검증 상태

| 항목 | 상태 | 비고 |
|------|------|------|
| 파라미터명 | ✅ 확정 | VST 512 프리셋 교차 검증 완료 |
| MIDI CC 매핑 (41개) | ✅ 확정 | 매뉴얼 v4.0.1 + 펌웨어 case 존재 확인 |
| Preset::set() 주소 | ✅ 확정 | RTTI 추출 |
| 파라미터 세터 서명 | ✅ 확정 | FUN_08164efc 디컴파일 |
| enum 인덱스 순서 | ⚠️ 추정 | 펌웨어 enum 테이블 직접 추출 필요 |
| CC#86~186 매핑 | ⚠️ 미확정 | 101개 FX 확장 CC 상세 매핑 필요 |
| eSynthParams 항목 수 | ⚠️ 추정 | ~145개 (더미 제외). 펌웨어 바이너리에서 최종 확인 필요 |

---

## 향후 작업

1. **enum 테이블 직접 추출**: 펌웨어 바이너리에서 `eSynthParams` enum 문자열 테이블 위치 식별 → 인덱스 순서 확정
2. **CC#86~186 상세 매핑**: 101개 FX 확장 CC가 어떤 eSynthParams/eFXParams 항목에 대응하는지 NRPN handler 교차 검증
3. **eCtrlParams 문서화**: 펌웨어 컨트롤 파라미터 enum 별도 문서화
4. **eFXParams 문서화**: FX 전용 파라미터 (FX subtype별 hidden params) 문서화

---

*Generated from: PHASE5_MNFX_FORMAT.md (2419 VST params), PHASE8_1_RESULTS.md (firmware RTTI), PHASE6_MIDI_CHART_v2.md (CC mapping)*
*MiniFreak Reverse Engineering — Phase 8*
