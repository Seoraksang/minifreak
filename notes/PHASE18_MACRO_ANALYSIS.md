# Phase 10-2: V Macro 3/4 (Brightness/Timbre) → HW 동작 분석

**분석 일시**: 2026-05-01  
**분석 대상**: MiniFreak V DLL, CM4 펌웨어, VST 파라미터 XML  
**목표**: Macro 3(Brightness)/Macro 4(Timbre)가 V 전용인지, HW 펌웨어에도 슬롯이 있는지, Collage protocol을 통해 HW로 전송되는지 판정

---

## 1. VST 파라미터 XML 분석

### 1.1 minifreak_vst_params.xml (VST UI 노출 파라미터, 148개)

Macro 관련 파라미터는 **2개만** 존재:
- `Macro1_Value` — display_name: "Macro 1", realtimemidi=1
- `Macro2_Value` — display_name: "Macro 2", realtimemidi=1

**Macro3_Value, Macro4_Value 없음.** VST 호스트에게 노출되는 MIDI 자동화 파라미터에는 Macro 3/4가 포함되지 않는다.

### 1.2 minifreak_internal_params.xml (내부 파라미터, 2363개)

Macro 관련 항목:
- `Macro1_Dest_0/1/2/Last`, `Macro1_Amount_0/1/2/Last`
- `Macro2_Dest_0/1/2/Last`, `Macro2_Amount_0/1/2/Last`

Mod Matrix 소스 선택 항목:
- `Macro 1` (processorvalue=6)
- `Macro 2` (processorvalue=7)

**__Macro3, __Macro4, Macro3_Dest, Macro4_Dest 등 모두 없음.**  
내부 파라미터 정의에 Macro 3/4는 존재하지 않는다.

### 1.3 minifreak_feedback_params.xml

- `Macro1_Value_Feedback` (transmittedtoprocessor=0)
- `Macro2_Value_Feedback` (transmittedtoprocessor=0)

**Macro3/4 피드백 파라미터 없음.**

### 1.4 minifreak_feedback_params_data_offsets.xml

- `Macro1_Value_Feedback_Offset` = 896
- `Macro2_Value_Feedback_Offset` = 928

**Macro3/4 피드백 오프셋 없음.**

### 1.5 hw_vst_tools_params.xml

Macro 관련 항목 없음. Instance State / Sync Mode 등 VST-HW 연동 도구 파라미터만 포함.

### 1.6 Reference_ParamNames.xml (이름 참조 테이블)

**Macro 3/4 관련 항목이 존재함** (주의: 이 XML은 파라미터 정의가 아닌 **이름 매핑 테이블**):

```
__Macro3        → "Macro 3"
__Macro4        → "Macro 4"
__Macro3_Name   → "__Macro3 Name"
__Macro4_Name   → "__Macro4 Name"
Macro3_Mapped1~36  (36개 매핑 대상)
Macro3_Amount1~36  (36개 액션)
Macro4_Mapped1~36  (36개 매핑 대상)
Macro4_Amount1~36  (36개 액션)
```

비교: Macro1, Macro2도 동일하게 Mapped1~36 + Amount1~36 구조.

### 1.7 gui-constants-generated.xml (GUI 상수)

```xml
MACRO3_PARAM_NAME = "__Macro3"
MACRO4_PARAM_NAME = "__Macro4"
MACRO3_NAME = "__Macro3_Name"
MACRO4_NAME = "__Macro4_Name"
MACRO3_DEFAULT_NAME = "Macro 3"
MACRO4_DEFAULT_NAME = "Macro 4"
```

---

## 2. VST DLL 바이너리 분석

### 2.1 Macro 3/4 관련 문자열

DLL 내에서 Macro 3/4 관련 문자열 발견:

| 오프셋 | 문자열 | 문맥 |
|--------|--------|------|
| 0x015F0688 | `__Macro4_Name` | PresetData 변환 함수 근처 |
| 0x015F0698 | `__Macro3_Name` | (동상) |
| 0x015F0800 | `Macro4` | Analog Lab 프리셋 카테고리 테이블 |
| 0x015F0808 | `Macro3` | (동상) |
| 0x015F4138 | `Macro 3 Name` | Analog Lab 검증 메시지 |
| 0x015F4398 | `Macro 4 Name` | Analog Lab 검증 메시지 |

### 2.2 핵심 DLL 컨텍스트

DLL에서 Macro 3/4가 등장하는 모든 문맥은 **Analog Lab 관련 코드**에 국한됨:

```
0x015F0688: __Macro4_Name
0x015F0698: __Macro3_Name
0x015F06A8: Tonewheel Organ ← Analog Lab instrument type
0x015F06B8: Clavinet
...
0x015F0800: Macro4
0x015F0808: Macro3
0x015F0810: Macro2
0x015F0818: Macro1
```

```
0x015F3C06: "[SEM] ...Macro 3 Name..."
0x015F4398: "Macro 4 Name..." (failed). Assign unused Env..."
```

Analog Lab 검증 경고 메시지:
> "Default Macro. Probably no real effect => please make sure the macros are well connected and update the name to what the macro do"

### 2.3 Brightness / Timbre 관련 문자열

DLL에서 "Brightness"는 6군데, "Timbre"는 여러 군데 등장하지만, **모두 MPE/CC 컨텍스트 또는 Osc 파라미터 컨텍스트**:

| 오프셋 | 문자열 | 의미 |
|--------|--------|------|
| 0x015B6B30 | `Movement` | MPE CC 74 (Timbre/Brightness 계열) |
| 0x015B6B3C | `Time` | MPE CC 76 |
| 0x015B6B44 | `Timbre` | MPE CC 77 |
| 0x015B6B50 | `Brightness` | MPE CC 78 |
| 0x015BBC50 | `MPE_Brightness_0` | MPE 채널 Brightness 파라미터 |
| 0x015BBE00 | `MPE_GlobalBrightness` | MPE 글로벌 Brightness |
| 0x017751A6 | `Sound Brightness` | MIDI CC 74 표준 이름 |
| 0x017752B8 | `Sound Timbre` | MIDI CC 77 표준 이름 |
| 0x015CC9C2 | `_Slot2_Brightness` | Mod Matrix 디버그 출력 (Brightness가 Slot 2의 매핑 대상) |

**"Brightness" / "Timbre"는 Macro 3/4의 별칭이 아님.** Osc1_Param2는 "Osc1 Timbre"로, Osc2_Param2는 "Osc2 Timbre"로 표시됨.

### 2.4 Mod Matrix의 `_Slot2_Brightness`

DLL 디버그 문자열에서:
```
show_macro __Macro1
  |-> _Slot1___Macro1
  |-> _Slot2___Macro1
        |-> _Slot1_Cutoff
        |-> _Slot2_Brightness
```

이것은 Macro 1이 Mod Matrix Slot 2에서 Brightness(Osc Timbre)를 조절하는 매핑 예시.  
**Macro의 대상(destination)으로서의 Brightness**이지, Macro 3의 별명이 아님.

---

## 3. CM4 펌웨어 분석

### 3.1 eEditParams 파라미터 이름 테이블

CM4 펌웨어(0x08120000 기준)의 파라미터 테이블(0x0008F000~0x0008FD00 영역):

```
0x0008F904: Macro1 dest
0x0008F910: Macro2 dest
0x0008F91C: Macro1 amount
0x0008F92C: Macro2 amount
0x0008F93C: Retrig Mode
...
0x0008F994: UnisonOn TO BE DEPRECATED
0x0008F9B0: Matrix Src VeloAT
...
0x0008FB28: VST_IsConnected
0x0008FB38: Pre Master Volume
0x0008FB4C: Favorites Page
```

**Macro3 dest, Macro4 dest, Macro3 amount, Macro4 amount 없음.**  
Macro 항목은 Macro1/2 dest/amount 4개로 끝남.

### 3.2 DEPRECATED 항목

CM4에서 DEPRECATED는 1개뿐:
```
0x0008F994: UnisonOn TO BE DEPRECATED
```

이것은 UnisonOn 파라미터의 예약 슬롯으로, Macro 3/4와 무관.  
**Macro 3/4를 위한 hidden/deprecated 슬롯은 존재하지 않음.**

### 3.3 "Brightness" / "Timbre" 문자열

CM4에서 "Timbre"는 Osc 파라미터로만 존재:
```
0x0008F764: Timbre 1  (Osc1_Param2)
0x0008F7A0: Timbre 2  (Osc2_Param2)
0x0008FB90: Timb     (UI 디스플레이 단축명)
0x0008FC1C: Timbre   (Matrix Assign 대상명)
```

"Brightness" 문자열 **전혀 없음** (CM4 펌웨어 어디에도).

### 3.4 CM4 "Macro" 문자열 전체

```
Macro Ed, Macro 1, Macro 2, Shift + Macros to assign to Macro,
Macro1 dest, Macro2 dest, Macro1 amount, Macro2 amount,
Macro Dest Full, Couldn't create macro edit display
```

**Macro 3/4 관련 문자열 일절 없음.**

---

## 4. .mnfx 프리셋 포맷 분석

### 4.1 Hardware Preset (.mnfx) 구조

mnfx_editor.py로 분석한 하드웨어 프리셋의 Macro 관련 필드:

```
Macro1_Amount_0/1/2/Last    ← Mod Matrix 3개 슬롯 + Last
Macro1_Dest_0/1/2/Last      ← 매핑 대상 3개 + Last
Macro1_Value                 ← Macro 1 현재값
Macro2_Amount_0/1/2/Last    ← 동일
Macro2_Dest_0/1/2/Last      ← 동일
Macro2_Value                 ← Macro 2 현재값
```

**Macro3/4 관련 필드 없음.**  
하드웨어 프리셋은 boost::serialization text archive 포맷으로, 파라미터 목록이 고정되어 있음.

### 4.2 Osc Timbre 파라미터

```
Osc1_Param1 → display: "Timbre" (실제로는 Wave)
Osc1_Param2 → display: "Morph"
```

mnfx_editor.py 카테고리 매핑:
```python
('OSC1', [('Osc1_Type', 'Type'), ('Osc1_Param1', 'Timbre'),
           ('Osc1_Param2', 'Morph'), ('Osc1_Volume', 'Vol')])
```

**Osc1_Param1이 "Timbre"로 표시됨** — 이것이 HW에서 "Timbre" 문자열이 등장하는 이유.

---

## 5. 종합 판정

### 판정 결과: **Macro 3/4는 V 전용 기능 (가설 A 확정)**

| 검증 항목 | 결과 |
|-----------|------|
| VST vst_params.xml에 Macro3/4 Value 파라미터 | ❌ 없음 |
| VST internal_params.xml에 __Macro3/__Macro4 | ❌ 없음 |
| VST feedback_params.xml에 Macro3/4 Feedback | ❌ 없음 |
| CM4 펌웨어 eEditParams에 Macro3/4 | ❌ 없음 |
| CM4 펌웨어에 "Brightness" 문자열 | ❌ 없음 |
| CM4 펌웨어에 Macro3/4 DEPRECATED 슬롯 | ❌ 없음 |
| .mnfx 프리셋에 Macro3/4 필드 | ❌ 없음 |
| Collage protocol로 HW 전송 가능? | ❌ (전송할 대상 파라미터가 없음) |
| Reference_ParamNames.xml에 Macro3/4 이름 정의 | ⚠️ 있음 (Analog Lab 호환용) |
| DLL에 Macro3/4 코드 존재 | ⚠️ 있음 (Analog Lab 프리셋 데이터 처리 전용) |

### 상세 분석

#### Macro 3/4의 실체
- DLL 내 Macro 3/4 코드는 **모두 Analog Lab 프리셋 파싱/검증 컨텍스트**에 존재
- `ConvertPresetChildXToChildY()`, `ConvertAnalogLabSlotToPluginSingle()` 등의 함수 근처
- Analog Lab은 VST 플러그인 내의 독립 프리셋 포맷을 사용하며, 여기에 Macro 1~4 슬롯이 정의됨
- **하지만 MiniFreak의 실제 오디오 엔진은 Macro 1/2만 처리**

#### Brightness/Timbre의 실체
- V 매뉴얼 §7.2.3에서 "Brightness" / "Timbre"라고 표기된 Side Panel의 M3/M4는:
  - **별도의 Brightness/Timbre 파라미터가 아님**
  - 단지 Analog Lab 호환 프리셋 데이터에서 Macro 3의 기본 라벨이 "Brightness", Macro 4의 기본 라벨이 "Timbre"인 것으로 추정
  - DLL의 `gui-constants-generated.xml`에서 기본명은 "Macro 3" / "Macro 4"임 (Brightness/Timbre는 아니지만, Analog Lab에서 커스텀 이름으로 지정 가능)
- Osc1_Param2는 "Osc1 Timbre"로, Osc2_Param2는 "Osc2 Timbre"로 표시됨 (HW와 동일)

#### V 매뉴얼의 모순 해명
- §4.7.1: "2개(M1, M2)만" — **정확함** (실제 오디오 엔진 관점)
- §7.2.3: "M1, M2 + Brightness, Timbre 4개" — **Analog Lab 호환 레이어 관점** (실제로는 작동하지 않거나 Analog Lab 모드에서만 의미 있음)
- VST 호스트 자동화 파라미터(vst_params.xml)에는 Macro 1/2만 노출 → 호스트에서 Macro 3/4를 자동화 불가

#### 데이터 흐름

```
[VST Side Panel]
  M1 ──→ Macro1_Value ──→ internal_params ──→ .mnfx ──→ HW (Collage) ✅
  M2 ──→ Macro2_Value ──→ internal_params ──→ .mnfx ──→ HW (Collage) ✅
  M3 ──→ (Analog Lab preset data only) ──→ HW 전송 없음 ❌
  M4 ──→ (Analog Lab preset data only) ──→ HW 전송 없음 ❌
```

---

## 6. 결론

**Macro 3(Brightness)/Macro 4(Timbre)는 MiniFreak V 플러그인의 Analog Lab 호환 레이어 전용 기능.**

1. **HW 펌웨어에는 Macro 3/4 슬롯이 없음** — eEditParams enum에 Macro1/2 dest/amount만 존재
2. **Collage protocol로 HW 전송 불가** — 전송할 파라미터 ID가 HW에 정의되어 있지 않음
3. **하드웨어 프리셋(.mnfx)에 저장 불가** — 프리셋 포맷에 Macro3/4 필드 없음
4. **VST 오디오 엔진에서도 실제로 작동하지 않음** — internal_params에 정의되지 않음
5. **DLL 코드에 존재하는 Macro3/4는 Analog Lab 프리셋 호환성 처리 전용** — PresetData 변환/검증 함수에만 등장

V 매뉴얼 §7.2.3에서 4개 Macro가 표시되는 것은 UI 레이어의 착시 현상으로, 실제 음향 제어에는 Macro 1/2만 유효함.

---

## 부록: 주요 오프셋 참조

### CM4 펌웨어 파라미터 테이블
| 주소 | 파라미터명 |
|------|-----------|
| 0x0008F764 | Timbre 1 (Osc1_Param2) |
| 0x0008F7A0 | Timbre 2 (Osc2_Param2) |
| 0x0008F904 | Macro1 dest |
| 0x0008F910 | Macro2 dest |
| 0x0008F91C | Macro1 amount |
| 0x0008F92C | Macro2 amount |
| 0x0008F994 | UnisonOn TO BE DEPRECATED |
| 0x0008FB28 | VST_IsConnected |

### VST DLL Macro3/4 관련
| 주소 | 문자열 |
|------|--------|
| 0x015F0688 | __Macro4_Name (Analog Lab preset data) |
| 0x015F0698 | __Macro3_Name (Analog Lab preset data) |
| 0x015F0800 | Macro4 (Analog Lab 카테고리 테이블) |
| 0x015F4138 | "Macro 3 Name" (AL 검증) |
| 0x015F4398 | "Macro 4 Name" (AL 검증) |
| 0x015CC9C2 | _Slot2_Brightness (Mod Matrix 디버그, Macro 대상) |
