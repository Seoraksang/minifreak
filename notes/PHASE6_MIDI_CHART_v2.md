# Arturia MiniFreak — MIDI Implementation Chart (정정版)

**Phase 8-1a** | 2026-04-25 | 매뉴얼 v4.0.1 기준 + 펌웨어 교차 검증

---

## 1. MIDI Device Identity

| 항목 | 값 | 출처 |
|------|-----|------|
| **Manufacturer** | Arturia (`0x00 0x20 0x6B`) | 펌웨어 추출 |
| **Device ID** | `0x02` (MiniFreak) | SysEx 헤더 |
| **USB VID** | `0x1C75` | 펌웨어 추출 |
| **USB PID** | `0x0602` | 펌웨어 추출 |
| **Firmware** | 4.0.1 (`fw4_0_1_2229`) | 펌웨어 파일명 |

---

## 2. Channel Messages

### 2.1 Note Messages

| Status | Data 1 | Data 2 | 기능 | 비고 |
|--------|--------|--------|------|------|
| `0x9n` | Key (0-127) | Velocity (1-127) | **Note On** | 6-voice poly (Para 시 12) |
| `0x8n` | Key (0-127) | Velocity (0) | **Note Off** | Release envelope |
| `0xDn` | — | Pressure (0-127) | **Channel Aftertouch** | 키베드 = Mono AT; 외부 MIDI = Poly AT 수용 가능 |
| `0xAn` | Key (0-127) | Pressure (0-127) | **Poly Aftertouch** | **수신 전용** (외부 MIDI에서만) |

### 2.2 Control Change (매뉴얼 공식 41 CC)

#### Oscillator 1

| CC# | Hex | Parameter | 범위 | 비고 |
|-----|-----|-----------|------|------|
| **70** | 0x46 | Osc 1 Tune | -24~+24 semitone | |
| **14** | 0x0E | Osc 1 Wave | 0~127 | |
| **15** | 0x0F | Osc 1 Timbre | 0~127 | |
| **16** | 0x10 | Osc 1 Shape | 0~127 | |
| **17** | 0x11 | Osc 1 Volume | 0~127 | |

#### Oscillator 2

| CC# | Hex | Parameter | 범위 | 비고 |
|-----|-----|-----------|------|------|
| **73** | 0x49 | Osc 2 Tune | -24~+24 semitone | |
| **18** | 0x12 | Osc 2 Wave | 0~127 | |
| **19** | 0x13 | Osc 2 Timbre | 0~127 | |
| **20** | 0x14 | Osc 2 Shape | 0~127 | |
| **21** | 0x15 | Osc 2 Volume | 0~127 | |

#### Analog Filter

| CC# | Hex | Parameter | 범위 | 비고 |
|-----|-----|-----------|------|------|
| **74** | 0x4A | Filter Cutoff | 0~127 | |
| **71** | 0x47 | Filter Resonance | 0~127 | |
| **24** | 0x18 | VCF Env Amount | 0~127 | |
| **94** | 0x5E | Velocity Env Mod | 0~127 | |

#### Cycling Envelope

| CC# | Hex | Parameter | 범위 | 비고 |
|-----|-----|-----------|------|------|
| **68** | 0x44 | Rise Shape | -50~+50 | |
| **76** | 0x4C | Rise | 0~127 | |
| **77** | 0x4D | Fall | 0~127 | |
| **78** | 0x4E | Hold | 0~127 | |
| **69** | 0x45 | Fall Shape | -50~+50 | |

#### Envelope (ADSR)

| CC# | Hex | Parameter | 범위 | 비고 |
|-----|-----|-----------|------|------|
| **80** | 0x50 | Attack | 0~127 | |
| **81** | 0x51 | Decay | 0~127 | |
| **82** | 0x52 | Sustain | 0~127 | |
| **83** | 0x53 | Release | 0~127 | |

#### LFO

| CC# | Hex | Parameter | 범위 | 비고 |
|-----|-----|-----------|------|------|
| **85** | 0x55 | LFO 1 Rate | 0~127 | |
| **87** | 0x57 | LFO 2 Rate | 0~127 | |

#### Effects (3 Slot)

| CC# | Hex | Parameter | Slot | 비고 |
|-----|-----|-----------|------|------|
| **22** | 0x16 | FX Time | FX1 | |
| **23** | 0x17 | FX Intensity | FX1 | |
| **25** | 0x19 | FX Amount | FX1 | |
| **26** | 0x1A | FX Time | FX2 | |
| **27** | 0x1B | FX Intensity | FX2 | |
| **28** | 0x1C | FX Amount | FX2 | |
| **29** | 0x1D | FX Time | FX3 | |
| **30** | 0x1E | FX Intensity | FX3 | |
| **31** | 0x1F | FX Amount | FX3 | |

#### Modulation & Performance

| CC# | Hex | Parameter | 범위 | 비고 |
|-----|-----|-----------|------|------|
| **1** | 0x01 | Mod Wheel | 0~127 | Standard MIDI CC |
| **5** | 0x05 | Glide | 0~127 | Portamento Time |
| **117** | 0x75 | Macro M1 | 0~127 | |
| **118** | 0x76 | Macro M2 | 0~127 | |

#### Pedals

| CC# | Hex | Parameter | 범위 | 비고 |
|-----|-----|-----------|------|------|
| **64** | 0x40 | Sustain Pedal | <64=Off, ≥64=On | |

#### Sequencer

| CC# | Hex | Parameter | 범위 | 비고 |
|-----|-----|-----------|------|------|
| **115** | 0x73 | Gate | 0~127 | |
| **116** | 0x74 | Spice | 0~127 | |

#### Standard MIDI (Mode/Channel)

| CC# | Hex | Parameter | 비고 |
|-----|-----|-----------|------|
| **120** | 0x78 | All Sound Off | |
| **121** | 0x79 | Reset All Controllers | |
| **123** | 0x7B | All Notes Off | |

**총 매뉴얼 공식 CC: 41개**

### 2.3 펌웨어 내부 CC (161개) — 매뉴얼 미노출

펌웨어 `FUN_08166810`은 **161개 CC**를 처리. 매뉴얼 41개 외에 **120개의 내부 CC**가 존재:

| CC# 범위 | 개수 | 추정 용도 | 비고 |
|----------|------|-----------|------|
| 0x56~0xBA (86~186) | 101개 | FX extended 파라미터 | FX subtype별 hidden 파라미터 |
| 0xC3, 0xC5~C6, 0xCA, 0xCC | 7개 | Macro/Extended | 펌웨어 내부 macro 확장 |
| 기타 개별 | ~12개 | 내부 파라미터 | VCA Mod, Unison Spread 등 |

> **검증 필요**: CC#86~186 블록이 실제로 FX hidden parameter인지, 다른 용도인지는
> 펌웨어의 `eSynthParams` enum과 NRPN handler(0x081812b4) 교차 검증으로 확정.

### 2.4 Pitch Bend

| Status | Data | 범위 | 기능 |
|--------|------|------|------|
| `0xE0` | LSB, MSB | ±1~±12 반음 (가변) | Pitch Bend |

### 2.5 Program Change

| Status | Data | 기능 |
|--------|------|------|
| `0xCn` | 0-127 | 프리셋 선택 (512슬롯 중 128) |

### 2.6 NRPN

| MSB CC | LSB CC | Data Entry CC | 기능 |
|--------|--------|---------------|------|
| 0x63 | 0x62 | 0x06 | NRPN 파라미터 (14-bit) |
| — | — | 0x26 | Data Increment |
| — | — | 0x26 | Data Decrement |

NRPN handler: `FUN_0x081812B4` (CM4)
NRPN param values: 33개 (1~6, 10~16, 20~21, 25~32, 39~41, 48~49, 54~56, 61~62)

---

## 3. 펌웨어 CC vs 매뉴얼 CC 대조

### ✅ 일치 (매뉴얼 CC가 펌웨어에 case로 존재)

매뉴얼 41개 CC **모두** 펌웨어 switch/case에 존재 확인.

### ❌ 기존 PHASE6_MIDI_CHART.md 오류 정정

| CC# | 기존 (오류) | 정정 (매뉴얼) | 펌웨어 검증 |
|-----|------------|-------------|------------|
| 1 | Osc1 Type/Waveform | **Mod Wheel** | case 1 존재 ✅ |
| 5 | Osc1 Octave | **Glide** | case 5 존재 ✅ |
| 14 | Osc2 Octave | **Osc1 Wave** | case 14 존재 ✅ |
| 15 | Osc2 Semitone | **Osc1 Timbre** | case 15 존재 ✅ |
| 16 | Osc2 Amount/Mix | **Osc1 Shape** | case 16 존재 ✅ |
| 17 | — | **Osc1 Volume** | case 17 존재 ✅ |
| 18 | — | **Osc2 Tune** | case 18(=0x12) 존재 ✅ |
| 19 | — | **Osc2 Wave** | case 19(=0x13) 존재 ✅ |
| 20 | Osc1 Level | **Osc2 Timbre** | case 20(=0x14) 존재 ✅ |
| 21 | Osc2 Level | **Osc2 Shape** | case 21(=0x15) 존재 ✅ |
| 24 | Filter Cutoff | **VCF Env Amt** | case 24(=0x18) 존재 ✅ |
| 25 | Filter Resonance | **FX1 Amount** | case 25(=0x19) 존재 ✅ |
| 26 | Filter Env Amount | **FX2 Time** | case 26(=0x1a) 존재 ✅ |
| 27 | Filter Key Tracking | **FX2 Intensity** | case 27(=0x1b) 존재 ✅ |
| 29 | Filter Type | **FX3 Time** | case 29(=0x1d) 존재 ✅ |
| 30 | Filter Drive | **FX3 Intensity** | case 30(=0x1e) 존재 ✅ |
| 31 | Filter Env Velocity | **FX3 Amount** | case 31(=0x1f) 존재 ✅ |
| 32 | Filter Cutoff 2 | **펌웨어 내부 CC** (FX3 계열 same handler as CC29~31) | case 32(=0x20) 존재 ✅ |
| 38~50 | Env1/Env2 (13개) | **Env(4) + CycEnv(5) + 기타** | 재분류 필요 |
| 53 | LFO1 Rate | **—** (매뉴얼 CC85) | CC53 ≠ LFO1 Rate |
| 60 | LFO2 Rate | **—** (매뉴얼 CC87) | CC60 ≠ LFO2 Rate |
| 65 | Portamento | **—** (매뉴얼 CC5=.Glide) | CC65는 별개 파라미터 |
| 71~79 | FX A Param 1-8 | **Resonance/FX1~FX3** | 완전 재매핑 |
| 85 | FX B Type | **LFO1 Rate** | 완전 다름 |
| 86~186 | FX Extended 101개 | 개별 파라미터 | 블록 재매핑 필요 |
| 193~204 | Macro 1-7 | **Macro M1/M2만 (CC117/118)** | 7→2개 |

### 🔍 검증 대기

| 항목 | 상태 | 필요 작업 |
|------|------|-----------|
| CC#86~186 (101개) 실제 매핑 | 미확정 | NRPN handler + eSynthParams enum 교차 검증 |
| CC#53, 60, 65 펌웨어 내부 파라미터 | 미확정 | 각 case 디컴파일 분석 |
| Envelope CC (38~50) 재분류 | 미확정 | Env(ADSR) vs CycEnv 구분 |

---

## 4. SysEx Messages (변경 없음)

> Phase 6 분석 결과 유지 — 매뉴얼에 명시되지 않은 펌웨어 전용 프로토콜.
> 상세 내용은 기존 PHASE6_MIDI_CHART.md §3 참조.

---

## 5. MIDI Clock & Sync (변경 없음)

> 기존 분석 유지.

---

## 6. Aftertouch 정정

| 항목 | 기존 (오류) | 정정 | 근거 |
|------|------------|------|------|
| 키베드 AT | "Per-note pressure" | **Mono AT** | 매뉴얼 12.2 |
| 외부 MIDI 수신 | — | **Poly AT 호환** | 매뉴얼 12.2 |
| AT Curve | — | Linear/Log/Expo | 매뉴얼 |
| AT Sensitivity | — | Start + End (Low/Mid/High) | 매뉴얼 |

---

## 7. Bend Range 정정

| 항목 | 기존 (오류) | 정정 | 근거 |
|------|------------|------|------|
| Bend Range | "-2~+2 반음 (default)" | **±1~±12 반음 (가변)** | 매뉴얼 Sound Edit > Keyboard > Bend Range |
