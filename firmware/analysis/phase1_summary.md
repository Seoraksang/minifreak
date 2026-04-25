# Phase 1 트리아지 결과 — MiniFreak 펌웨어 분석

> 분석일: 2026-04-21
> 펌웨어: v4.0.1.2229
> 도구: Ghidra 12.0.4 + PyGhidra (Hydra)

## 1. 바이너리 구조

```
.mnf (ZIP 컨테이너, 암호화 없음)
├── [0] main_CM4  (608KB) — Cortex-M4, 사운드 엔진 + UI + MIDI  ⭐ 핵심
├── [1] main_CM7  (512KB) — Cortex-M7, DSP 보조
├── [2] fx        (120KB) — 독립 FX DSP
├── [3] ui_screen (172KB) — OLED 디스플레이 MCU
├── [4] ui_matrix ( 68KB) — 버튼 매트릭스 MCU
├── [5] ui_ribbon ( 68KB) — 터치스트립 MCU
└── [6] ui_kbd    ( 44KB) — 키베드 MCU
```

### DFU 헤더 구조
- 모든 바이너리의 처음 64바이트(0x00~0x3F)는 DFU 메타데이터
- 오프셋 0x40부터 ARM Cortex-M 벡터 테이블
- 이미지 베이스: 0x08000000 (STM32 플래시)

## 2. 함수 분포

| 바이너리 | 함수 수 | 명명됨 | 문자열 | 흥미로운 문자열 |
|----------|---------|--------|--------|----------------|
| CM4 | 1,101 | 3 | 875 | **174** ⭐ |
| CM7 | 284 | 11 | 108 | 11 |
| FX | 290 | 3 | 6 | 2 |
| UI Screen | 275 | 0 | 25 | 7 |
| UI Matrix | 188 | 0 | 21 | 6 |
| UI Ribbon | 186 | 0 | 22 | 6 |
| UI KBD | 129 | 0 | 17 | 6 |
| **합계** | **2,453** | **17** | **1,074** | **212** |

## 3. 핵심 발견: CM4 RTTI 심볼

### 3.1 클래스 구조 (C++ RTTI로 복구)

#### Preset 클래스
```cpp
class Preset {
    bool set(eSynthParams, Preset::value_t);
    value_t get(eSynthParams);
    bool set(eFXParams, Preset::value_t);
    value_t get(eFXParams);
    bool set(eCtrlParams, Preset::value_t);
    value_t get(eCtrlParams);
    bool set(eSeqParams, Preset::value_t);
    value_t get(eSeqParams);
    bool set(eSeqStepParams, Preset::seqdatavalue_t);
    seqdatavalue_t get(eSeqStepParams);
    bool set(eSeqAutomParams, Preset::value_t);
    value_t get(eSeqAutomParams);
    bool set(eShaperParams, Preset::value_t);
    value_t get(eShaperParams);
};
```

→ **프리셋 파라미터 6개 그룹**: SynthParams, FXParams, CtrlParams, SeqParams, SeqStepParams, SeqAutomParams, ShaperParams

#### CvCalib 클래스 (CV 캘리브레이션)
```cpp
class CvCalib {
    void setCalibVcaClickValue(eVcfType, uint8_t, bool, uint16_t);
    void setCalibrated(eCvKind, uint8_t, bool, bool);
    void setCalibCutValue(int8_t, int16_t, uint16_t);
    void setCalibMaxValue(eCvKind, uint8_t, uint16_t);
    void setCalibMinValue(eCvKind, uint8_t, uint16_t);
    uint16_t getCalibMinValue(eCvKind, uint8_t);
    uint16_t getCalibMaxValue(eCvKind, uint8_t);
    uint16_t getCalibVcaClickValue(eVcfType, uint8_t, bool);
    uint16_t getCalibCutValue(int8_t, int16_t);
    bool getCalibrated(eCvKind, uint8_t);
    uint16_t getCvCalibrated(eCvKind, uint8_t, uint16_t);
};
```

→ **enum 추측**: `eVcfType` = 필터 타입 (LP/BP/HP), `eCvKind` = CV 채널

#### 기타 클래스
- `MedianFilter` — 노브 안정화 필터
- `SMAFilter<3>`, `SMAFilter<4>` — 단순 이동 평균
- `PotChainCalib` — 노브 체인 캘리브레이션
- `SensorChainCalib` — 센서 체인 캘리브레이션
- `VoiceAllocator` — 폴리포니 보이스 할당
- `HysteresisFilter<4095, 32, 1000>` — UI ADC 디바운스

### 3.2 오실레이터 타입 (UI 문자열에서 확인)

| Osc 1 (16종) | Osc 2 추가 (21종 중) |
|-------------|---------------------|
| Basic Waves | Multi Filter |
| SuperWave | Surgeon Filter |
| KarplusStr | Comb Filter |
| Waveshaper | Phaser Filter |
| Two Op. FM | Destroy (추정) |
| Noise | Chord (추정) |
| Audio In | FM/RM (추정) |
| Wavetable | |
| Sample | |
| Granular | |

### 3.3 FX 타입
Chorus, Phaser, Flanger, Reverb, Distortion, Delay

### 3.4 USB 인터페이스
- `MiniFreak` — 기본 USB 디바이스
- `MiniFreak MIDI` — MIDI 포트 1
- `MiniFreak MIDI 3 In/Out` — MIDI 포트 3
- `MiniFreak MIDI 4 In/Out` — MIDI 포트 4
- `MiniFreak VST` — VST 플러그인 통신
- `AUDIO Config` / `AUDIO Interface` — 오디오 설정
- `Firmware Updater` — 펌웨어 업데이트 모드

### 3.5 이스터에그 🎉
```
SUPERCALIFRAGILISTICMINIFREAKOUS
"I am MiniFreak, fluent in over 6,000,000 forms of madness."
"I can't mine crypto for you. But I CAN make a whole lot of noise."
"sometimes your MiniFreak is just having a really good day."
"The MiniFreak is as reliable as it is powerful, but it suffers from high recoil."
"If a machine, a MiniFreak, can learn the value of human life, maybe we can, too."
```

## 4. 아키텍처 가설 (업데이트)

```
┌─────────────────────────────────────────────────────┐
│                 STM32H745 (듀얼코어)                  │
│  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │   Cortex-M4      │  │    Cortex-M7             │  │
│  │   (608KB FW)     │  │    (512KB FW)            │  │
│  │                  │  │                          │  │
│  │ • 사운드 엔진    │──│→ • DSP 보조 연산         │  │
│  │ • UI 제어        │  │ • 오디오 버퍼 처리       │  │
│  │ • MIDI 처리      │  │                          │  │
│  │ • 프리셋 관리    │  │                          │  │
│  │ • USB 통신       │  │                          │  │
│  │ • VoiceAllocator │  │                          │  │
│  └──────────────────┘  └──────────────────────────┘  │
│                        ↕ IPC (공유 메모리)            │
└─────────────────────────────────────────────────────┘
           │ SPI/UART            │ I2S/SAI
           ↓                     ↓
┌────────────────┐    ┌──────────────────────┐
│ UI MCU x4      │    │ FX DSP (독립 MCU)    │
│ (Cortex-M0+?)  │    │ (120KB FW, 290 func) │
│ • screen (OLED)│    │ • Chorus/Phaser/     │
│ • matrix (LED) │    │   Flanger/Reverb/    │
│ • ribbon       │    │   Distortion/Delay   │
│ • kbd (keys)   │    └──────────────────────┘
└────────────────┘              │
                                ↓
                         아날로그 VCF/VCA
```

## 5. Phase 2 전략

### 우선순위
1. **CM4 → RTTI 문자열 기반 함수 리네임**
   - `CvCalib::*` 메서드 → 해당 함수 주소 매핑
   - `Preset::set/get` → 프리셋 파라미터 테이블 역설계
   - `MNF_MidiOut` → MIDI 처리 파이프라인 추적

2. **Plaits 코드 패턴 매칭**
   - Mutable Instruments Plaits 오픈소스 대조
   - 오실레이터 디스패치 테이블 식별

3. **프리셋 포맷 역설계**
   - `eSynthParams`, `eFXParams` enum 값 → 파라미터 ID 맵
   - 프리셋 바이너리 덤프 → 구조체 매핑
