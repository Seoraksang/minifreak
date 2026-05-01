# Phase 10-5: V 전용 파일 포맷 분석 (.mnfxmidi, Sound Bank, Backup)

**분석 일시**: 2026-05-01  
**분석 대상**: MiniFreak V.dll (30,341,016 bytes, x86_64 PE), V 추출 파일, mnfx_editor.py  
**목표**: V 전용 파일 포맷(.mnfxmidi, Sound Bank, Backup)의 실제 포맷/구조/핸들러 식별

---

## 요약

| 포맷 | 실제 포맷 | 확장자 | 핸들러 클래스 |
|------|----------|--------|--------------|
| **MIDI Configuration** | XML | `.prefmidi.xml` | `MidiConfigManager` (JuceArturiaLib) |
| **Sound Bank** | 디렉토리(JSON 메타데이터 + .mnfx 파일들) | 폴더 구조 | `JsonData::HardwareBank` |
| **Backup** | ZIP 아카이브(JSON + .mnfx) | `MiniFreak V_Backup_%Y%m%d_%Hh%M` | `MiniFreakPresetBrowserController` |
| **Preset (.mnfx)** | boost::serialization text archive | `.mnfx` | `MiniFreakPresetHwVstConverter` |

---

## 1. .mnfxmidi — MIDI Configuration Export/Import

### 1.1 ".mnfxmidi" 확장자 존재 여부

**DLL 내에서 ".mnfxmidi" 문자열 전혀 발견되지 않음.**  
대소문자 변형(`mnfxmidi`, `Mnfxmidi`, `MNFXMIDI`, `.mnfxmidi`, `mnfx_midi`) 모두 검색했으나 0 hit.

### 1.2 실제 MIDI Config 포맷: XML

MIDI Configuration은 **Arturia 공유 라이브러리(JuceArturiaLib)의 `MidiConfigManager`** 가 처리하며, **XML 포맷**을 사용한다.

#### 핸들러 클래스

```
Arturia::JuceArturiaLib::MidiConfigManager
├── SaveMIDIConfigs()           → XML 파일 저장
├── LoadMIDIConfigs()           → XML 파일 로드
├── LoadFallbackMIDIConfigs()   → 폴백 설정 로드
├── ImportMIDIConfigFromFile()  → XML 파일에서 임포트
├── ExportCurrentMIDIConfigOnFile() → 현재 설정을 XML로 익스포트
├── SetCurrentMidiConfigName()  → 현재 MIDI 컨피그 이름 설정
├── SetMIDICCAssigned()         → CC 할당
└── GetMidiConfigsFromXmlDocument() → XML 문서에서 파싱
```

소스 경로: `C:/jenkins/root/workspace/VC/release/minifreakv/jucearturialib/src/Midi/IMidiAssignmentManager.cpp`

#### 파일 포맷

내부 변수명 `filename_plug_prefmidi` 가 사용되며, 에러 메시지에서 확정:

```
[XML] Error on parse midi config file
[XML] Error on write midi config file
Error on opening XML file : filename_plug_prefmidi = ...
```

**MIDI Config 파일 종류:**

| 파일 | 역할 |
|------|------|
| `controllers.prefmidi.xml` | 컨트롤러 정의 (MIDI 컨트롤러 이름, MIDI 이름 등) |
| `controllers-common.prefmidi.xml` | 공통 컨트롤러 설정 |
| `plugin.prefmidi.xml` | 플러그인별 MIDI 파라미터 매핑 |
| `mapping.pref.xml` | MIDI 매핑 환경설정 |

#### controllers.prefmidi.xml 실제 구조 (V 추출본)

```xml
<?xml version="1.0" encoding="utf-8"?>
<rootnode>
    <include controllers="controllers-common.prefmidi.xml"/>
    <defaultcontroller name="Generic MIDI Controller"/>
    <controller name="MiniFreak" midiname="MiniFreak MIDI" 
                openoutput="1" synth="1" substr="1" midiforward="1"/>
    <defaultmidiconfig name="MiniFreak"/>
    <midiconfig readonly="1" name="MiniFreak"/>
</rootnode>
```

#### UI 흐름

DLL에서 발견된 UI 문자열:
- `"MIDI Controller Configs"` — MIDI 컨피그 목록 탭
- `"Import MIDI Configuration File"` — 파일에서 임포트 (XML)
- `"Export MIDI Configuration"` — 현재 설정 익스포트 (XML)
- `"Export Current Config"` / `"Set User Config As Default"` / `"Reset Factory Default Config"`
- `"MidiSavePopup"` / `"MidiDeletePopup"` — 저장/삭제 팝업

### 1.3 결론

> **".mnfxmidi"는 VST DLL에 존재하지 않는 확장자.**  
> MIDI Configuration은 **XML 포맷**(`.prefmidi.xml`)으로 저장/로드되며,  
> `MidiConfigManager` (JuceArturiaLib 공유 컴포넌트)가 처리한다.  
> "Export MIDI Configuration" 버튼은 XML 파일을 생성한다.

---

## 2. Sound Bank — 사운드 뱅크 포맷

### 2.1 "SoundBank" 문자열 검색 결과

- `"SoundBank"` (한 단어): **0 hit** — 이 이름의 클래스/변수 없음
- `"Sound Bank"` (두 단어): **17 hits** — 모두 **UI 라벨** (브라우저 메뉴 등)
- `"soundbank"` / `"AudioBank"` / `"audio_bank"`: **모두 0 hit**

### 2.2 Sound Store 시스템

Sound Bank은 Arturia의 사운드 스토어 시스템을 통해 배포되며, DLL에서 `[SoundStore]` 접두사의 로그 메시지로 확인:

```
[SoundStore] InitCurrentPresetPackInfo
[SoundStore] PurchasablePackSelected
[SoundStore] Download full for pack ...
[SoundStore] Download component ...
```

UI 카테고리:
- `Sound Banks List` — 설치된 뱅크 목록
- `Free Banks List` — 무료 뱅크
- `My Library List` — 구매한 라이브러리
- `Store Preview Banks List` — 스토어 미리보기
- `Sound Banks Promos List` — 프로모션

### 2.3 실제 뱅크 포맷: 디렉토리 기반

V 추출본에서 확인된 뱅크 구조:

```
MiniFreak Banks/
└── Factory/
    ├── 100_RoboBallad.mnfx
    ├── 101_5th 5AM.mnfx
    ├── 102_Abductshum.mnfx
    └── ... (512개 프리셋)
```

뱅크 메타데이터는 **JSON** (`JsonData::HardwareBank`):

```
Arturia::JuceArturiaLib::JsonFile<struct Arturia::MiniFreak::JsonData::HardwareBank>
├── ParseJsonFile()       → JSON 파싱
└── SerializeJsonFile()   → JSON 직렬화
```

JSON 내부 구조 (DLL에서 발견된 템플릿):
```json
{
    "bytes": [...],
    "subtype": "..."
}
```

뱅크 메타데이터 파일명: `MiniFreak Banks.backup.json` (slot 단위 관리)

### 2.4 결론

> Sound Bank은 독자적인 바이너리 포맷이 아닌, **디렉토리 기반 구조**  
> (`.mnfx` 프리셋 파일들의 모음 + `backup.json` 메타데이터).  
> Arturia Sound Store에서 다운로드되며, `JsonData::HardwareBank`가 메타데이터를 관리한다.

---

## 3. Backup — 512 프리셋 백업

### 3.1 백업 아카이브 포맷: ZIP

DLL에서 명확하게 ZIP 아카이브 구조를 사용함이 확인됨:

```
PlaylistBackup.zip
ProjectsBackup.zip
```

백업 ZIP 내부 구조:
- `backup.json` — 뱅크 메타데이터 (JSON)
- `*.mnfx` — 개별 프리셋 파일 (boost::serialization text archive)

### 3.2 핸들러 클래스

```
Arturia::MiniFreak::MiniFreakPresetBrowserController
├── ImportBackup()              → ZIP에서 backup.json + .mnfx 추출
├── ExportBackup()              → backup.json + .mnfx를 ZIP으로 패키징
├── UpdateBankJson()            → 뱅크 JSON 업데이트
├── LoadHWPresetsFromBank()     → HW에서 프리셋 로드
├── DuplicateBankDirectory()    → 뱅크 디렉토리 복제
└── UpdatePreset()              → 프리셋 업데이트

Arturia::MiniFreak::MiniFreakHardwareBackupsList
├── Create()                    → 백업 목록 생성
└── ExportBackup()              → 백업 익스포트 (ZIP)
```

소스 경로:  
- `minifreakv/src/controller/browser/MiniFreakPresetBrowserController.cpp`  
- `minifreakv/src/controller/browser/MiniFreakHardwareBackupsList.cpp`

### 3.3 백업 파일명 포맷

DLL에서 발견된 시간 포맷 문자열:

| 컨텍스트 | 포맷 | 예시 |
|----------|------|------|
| HW 백업 디렉토리명 | `MiniFreak V_Backup_%Y%m%d_%Hh%M` | `MiniFreak V_Backup_20260501_14h30` |
| 뱅크 백업명 | `Backup %Y%m%d-%H%M%S` | `Backup 20260501-143000` |
| 내부 백업 슬롯 | `MiniFreak Banks.backup.json.slot` | (슬롯 인덱스) |

### 3.4 백업 JSON 구조

DLL의 에러 메시지에서 추정되는 JSON 구조:

```
backup.json 내부:
{
    "version": "...",
    "display_name": "...",
    "idx": ...,
    "uuid": "...",
    "show_in_menu": ...,
    "date_added": "...",
    "instrument": "...",
    "presets": [...],
    "songs": [...],
    "is_preview": ...
}
```

에러 메시지 단서:
- `"Could not find backup.json in the backup file"`
- `"[INVALID JSON] The json file is not valid"`
- `"Could not add json file for Backup"`
- `"Could not add preset file"`
- `"Could not write preset file"`

### 3.5 파일 필터

DLL에서 백업 임포트 시 사용하는 파일 필터:
```
*.mnfx,*.mnfdump
```

`.mnfdump`는 프리셋 덤프 포맷으로, `.mnfx`와 함께 백업에 포함될 수 있다.

### 3.6 UI 흐름

```
"Initialize new MiniFreak Backup"
"Failed to initialize a MiniFreak backup"
"Reading presets from the MiniFreak, please wait"
"Writing presets to the MiniFreak, please wait"
"The backup name cannot be empty"
"This backup already exists"
"There were not enough free slots to copy"
"Delete Backup"
"Export Backup"
"Export selected backup"
"Exporting, please wait"
"An error occured while importing"
"Presets backup imported successfully"
```

### 3.7 결론

> Backup은 **ZIP 아카이브** 포맷.  
> 내부에 `backup.json`(뱅크 메타데이터) + `.mnfx` 프리셋 파일들을 포함.  
> 파일명: `MiniFreak V_Backup_%Y%m%d_%Hh%M`.  
> 핸들러: `MiniFreakPresetBrowserController::ImportBackup/ExportBackup`.

---

## 4. .mnfx 프리셋 포맷 상세

### 4.1 포맷: boost::serialization text archive

**Phase 5에서 이미 분석 완료.** VST DLL에서도 동일 포맷 확인.

DLL 내부에서 `22 serialization::archive` 시그니처 3곳 발견:

| 오프셋 | 클래스 버전 | 컨텍스트 |
|--------|-----------|----------|
| `0x15c2028` | (버전 없음) | Arturia 공유 포맷 (Spatial, Instrument, Analyzer, Project 등) |
| `0x15f39b0` | `10 0 5` | MiniFreak/Pigments 프리셋 내장 데이터 |
| `.mnfx 파일` | `10 0 7 0 7` | 실제 프리셋 파일 헤더 |

### 4.2 .mnfx 헤더 구조 (V 프리셋)

```
22 serialization::archive 10 0 7 0 7 <name_len> <name> <bank_len> <bank> 
66 <author_len> <author> <cat_len> <category> ... Subtype <len> <subtype> 
Type <len> <type> ... <params...>
```

실제 예:
```
22 serialization::archive 10 0 7 0 7 10 RoboBallad 4 User 66 12 Jeremy Blake 7 Unknown 0 0 ...
```

| 필드 | 의미 | 예시 값 |
|------|------|--------|
| `22` | boost::serialization 시그니처 | 고정 |
| `serialization::archive` | 매직 스트링 | 고정 |
| `10` | 아카이브 헤더 버전 | 10 |
| `0 7 0 7` | 클래스 버전 (7.7) | 7.7 |
| `name` | 프리셋 이름 | "RoboBallad" |
| `bank` | 뱅크 이름 | "User" |
| `author` | 작성자 | "Jeremy Blake" |
| `category` | 카테고리 | "Unknown" |
| `Subtype` | 서브타입 키워드 | "Sequence" |
| `Type` | 타입 키워드 | "Sequence" |

### 4.3 파라미터 통계 (Factory 프리셋 기준)

| 항목 | 값 |
|------|-----|
| 총 파라미터 수 | ~2,376 개 |
| 파일 크기 | ~49 KB |
| `MiniFreak_Preset_Revision` | 0.043137256 |

### 4.4 Macro 관련 파라미터 (.mnfx 내)

Macro 1/2만 존재 (Macro 3/4 없음 — Phase 18 Macro 분석에서 확인):

```
Macro1_Value, Macro1_Dest_0/1/2/Last, Macro1_Amount_0/1/2/Last
Macro2_Value, Macro2_Dest_0/1/2/Last, Macro2_Amount_0/1/2/Last
```

총 18개 Macro 파라미터.

### 4.5 PresetData 버전 관리

DLL 내부에서 PresetData 버전 체크:
```
"PresetData version ... is too high. Can't read preset"
"PresetDataId version ...item_version"
```

`MiniFreakPresetHwVstConverter`가 SDK↔Data 변환:
- `ConvertPresetFromSDKToData` — SDK 포맷에서 .mnfx 데이터로
- `ConvertPresetFromDataToSDK` — .mnfx 데이터에서 SDK 포맷으로
- `Data size too small for a Preset::Data (expected ...)`

### 4.6 V 내장 프리셋 데이터

DLL `0x15f39b0` 부근에 Arturia 공유 시리얼라이제이션 데이터 내장:
- `MiniFreak 2.0`, `Pigments 5.0`, `Pigments 4.0` — 호환성 정보
- 프리셋 이름/카테고리 사전 데이터
- 에러 메시지 템플릿 (`"No characteristic on file"`, `"Expected empty characs for file"`)

---

## 5. boost::serialization 사용 현황

### 5.1 DLL 내 검색 결과

| 검색어 | 히트 수 | 비고 |
|--------|---------|------|
| `boost::serialization` | 0 | 링커에 의해 스트립됨 |
| `boost::archive` | 0 | 링커에 의해 스트립됨 |
| `serialization::archive` | 3 | 매직 스트링으로만 존재 |
| `binary_archive` | 0 | binary 아카이브 미사용 |
| `text_archive` | 0 | 텍스트 아카이브 (스트링만 매직) |
| `xml_archive` | 0 | XML 아카이브 미사용 |

### 5.2 분석

- VST DLL은 링커 최적화로 인해 `boost::` 네임스페이스 문자열이 스트립됨
- 하지만 `22 serialization::archive` 매직 바이트가 3곳에서 발견되어 **실제로 boost::serialization text_archive를 사용**함이 확정
- Arturia 공유 라이브러리(`JuceArturiaLib`)에 serialization 코드가 포함되어 있으며, MiniFreak V뿐만 아니라 Pigments 등 다른 Arturia 제품과 공유

---

## 6. V 추출 디렉토리 파일 현황

### 6.1 .mnfxmidi 파일

**0개** — V 추출 디렉토리에 `.mnfxmidi` 파일 없음.

### 6.2 Bank 관련 파일

```
commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/
└── MiniFreak Banks/
    └── Factory/
        ├── 100_RoboBallad.mnfx
        ├── ... (512개 프리셋)
        └── 511_Wavestation.mnfx
```

### 6.3 MIDI Config 파일

```
commonappdata/Arturia/MiniFreak V/resources/controllers/
├── controllers.prefmidi.xml          ← MIDI 컨트롤러 정의
├── controllers-common.prefmidi.xml   ← 공통 컨트롤러 설정
└── browser/
    └── KeyLab mk3-generated.xml      ← 키보드 컨트롤러 매핑
```

### 6.4 기타 관련 파일

```
commonappdata/Arturia/MiniFreak V/resources/
├── minifreak_vst_params.xml          ← VST 파라미터 정의
├── templates/mf-hw-storage-view.xml  ← HW 스토리지 뷰 템플릿
├── gui_xml/gui-preset-browser-hardware-menu.xml  ← 하드웨어 메뉴
└── gui_xml/gui-sound-store-popups-generated.xml  ← 사운드 스토어 팝업
```

---

## 7. 포맷별 파일 I/O 핸들러 맵

```
┌─────────────────────────┬──────────────────────────────────┬──────────────────┐
│ 포맷                    │ I/O 핸들러                       │ 직렬화 방식      │
├─────────────────────────┼──────────────────────────────────┼──────────────────┤
│ .mnfx (Preset)          │ MiniFreakPresetHwVstConverter    │ boost::ser text   │
│ MIDI Configuration      │ MidiConfigManager (JuceArturiaLib)│ XML              │
│ Sound Bank              │ JsonData::HardwareBank           │ JSON (nlohmann)   │
│ Backup (ZIP)            │ MiniFreakPresetBrowserController │ ZIP + JSON + .mnfx│
│ Hardware Preset Bank    │ MiniFreakHardwareBackupsList     │ ZIP + JSON + .mnfx│
│ VST State               │ BaseController::setStateFromPresetData │ boost::ser   │
│ MIDI Mapping            │ mapping.pref.xml                 │ XML              │
└─────────────────────────┴──────────────────────────────────┴──────────────────┘
```

---

## 8. 핵심 발견 요약

1. **".mnfxmidi" 확장자는 존재하지 않음** — MIDI Configuration은 XML 포맷(`.prefmidi.xml`)으로 저장됨
2. **Sound Bank은 독자 포맷이 아님** — `.mnfx` 파일들의 디렉토리 + JSON 메타데이터 구조
3. **Backup은 ZIP 아카이브** — `backup.json` + `.mnfx` 프리셋 파일들 포함, 시간 포맷 기반 파일명
4. **boost::serialization은 .mnfx 프리셋에만 사용** — MIDI Config은 XML, Bank 메타데이터는 JSON
5. **Arturia 공유 라이브러리(JuceArturiaLib)가 파일 I/O의 핵심** — `MidiConfigManager`, `JsonFile<T>`, `BaseController` 등
6. **PresetData 버전 관리 존재** — `"PresetData version ... is too high. Can't read preset"` 에러로 버전 호환성 검증
