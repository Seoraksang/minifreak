# Phase 14-2: VST ↔ HW 파라미터 매핑 테이블

> **상태**: 완료
> **소스**: `reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/minifreak_vst_params.xml`
> **파서**: `tools/phase14_vst_params_parse.py`
> **산출**: `reference/minifreak_vst_params_parsed.json`

## 발견 요약

Arturia VST 플러그인의 파라미터 정의가 **별도 XML 파일**로 배포됨 (DLL 내부가 아님).
이 XML은 VST 플러그인 로드 시 `ParamMappingMgr::LoadConfig()`가 읽어들임.

### VST 파라미터 총 148개

| 카테고리 | 수량 | 설명 |
|----------|------|------|
| matrix | 91 | Mod 매트릭스 (Mx_Dot_0~26 + Mx_AssignDot_0~61) |
| oscillator | 13 | Osc1/2 타입, 파라미터, 볼륨, 글라이드 |
| fx | 9 | FX1/2/3 각각 Param1~3 (Time/Intensity/Amount) |
| lfo | 6 | LFO1/2 웨이브, 레이트, 레이트싱크 |
| sequencer | 7 | Seq_Gate, Arp_Mode/Repeat/Ratchet/Mutate/Rand_Oct/Oct |
| envelope | 7 | Env ADSR + CycEnv Rise/Fall/Hold |
| modulation | 5 | Vibrato, LFO/CycEnv AM |
| macro | 2 | Macro1/2_Value |
| other | 4 | VCA, Spice, Pitch1/2_Mod_On |
| voice | 1 | Gen_UnisonSpread |

### 핵심 Enum 정의

#### Osc1_Type (v2.9.0, 24개)
```
0: Basic Waves   1: SuperWave    2: Harmo         3: KarplusStr
4: VAnalog       5: Waveshaper   6: Two Op. FM     7: Formant
8: Speech        9: Modal        10: Noise         11: Bass
12: SawX         13: Harm        14: Audio In      15: Wavetable
16: Sample       17: Cloud Grains 18: Hit Grains  19: Frozen
20: Skan         21: Particle    22: Lick          23: Raster
```

#### Osc2_Type (v2.9.0, 30개)
```
0: Basic Waves     1: SuperWave     2: Harmo           3: KarplusStr
4: VAnalog         5: Waveshaper    6: Two Op. FM      7: Formant
8: Chords          9: Speech        10: Modal          11: Noise
12: Bass           13: SawX         14: Harm            15: FM / RM
16: Multi Filter   17: Surgeon Filt 18: Comb Filter    19: Phaser Filter
20: Destroy        21~29: Dummy (reserved)
```

**Osc1 vs Osc2 차이**: Osc1은 Wavetable/Sample/Grains 계열, Osc2는 Filter 계열 포함

#### LFO Wave (9개)
```
0: Sin  1: Tri  2: Saw  3: Sqr  4: SnH
5: SlewSNH  6: ExpSaw  7: ExpRamp  8: Shaper
```

#### LFO RateSync (27개)
```
0: 8d  1: 8  2: 4d  3: 8t  4: 4  5: 2d  6: 4t  7: 2
8: 1d  9: 2t  10: 1  11: 1/2d  12: 1t  13: 1/2  14: 1/4d
15: 1/2t  16: 1/4  17: 1/8d  18: 1/4t  19: 1/8  20: 1/16d
21: 1/8t  22: 1/16  23: 1/32d  24: 1/16t  25: 1/32  26: 1/32t
```

#### Arp_Mode (8개)
```
0: Up  1: Down  2: UpDown  3: Random
4: Walk  5: Pattern  6: Order  7: Poly
```

### VST 파라미터 vs DLL strings 파라미터 비교

DLL에서 추출한 **1,705개 파라미터 이름** (strings 분석) vs XML의 **148개 VST 파라미터**.

차이 원인:
- DLL strings에는 **HW 펌웨어 파라미터 이름**도 포함 (Mod_S0~63, Pitch_S0~63, Velo_S0~63, Gate_S0~63, StepState_S0~63, Reserved1~4, AutomReserved1 등)
- VST XML은 **VST UI에 노출되는 파라미터만** 정의
- 나머지 ~1,557개는 HW↔VST 내부 동기화용으로 DLL에 하드코딩

### VST 매트릭스 구조 (Mx_Dot / Mx_AssignDot)

```
Mx_Dot_0~26      = 7 모듈 × 4 닷 (amount) = Mod 1:1 ~ Mod 7:4
Mx_AssignDot_0~61 = 7 모듈 × 9 닷 (assign) = Mod 1:5 ~ Mod 7:13
```

- **Dot (0~26)**: 모듈레이션 amount (-1.0 ~ 1.0)
- **AssignDot (0~61)**: 모듈레이션 source/destination 할당 (-1.0 ~ 1.0, normalized)

### HW 파라미터 이름 (DLL strings, 비-VST)

이름들은 Collage 프로토콜의 `DataParameterId.single` (uint32)와 매핑됨.
정확한 ID ↔ 이름 매핑은 `InitSwFwParamIds` 함수에서 수행하며,
컴파일러 최적화로 인해 정적 분석으로는 정수 상수 추출이 어려움.
→ **USB 캡처로 실제 Collage ParameterSet 메시지를 관찰해야 최종 확정 가능**

## 참고

- `tools/phase14_param_extract.py` — DLL strings 파라미터 분류 스크립트
- `tools/phase14_param_id_extract2.py` — PE 섹션 파싱 + LEA 참조 검색
- `tools/phase14_param_id_extract3.py` — InitSwFwParamIds 영역 상수 추출
- `tools/phase14_vst_params_parse.py` — XML 파싱 스크립트
- `reference/minifreak_vst_params_parsed.json` — 파싱 결과 JSON
- → Phase 14-1: `notes/PHASE14_COLLAGE_PROTOCOL_ANALYSIS.md` (Collage 프로토콜 스키마)
