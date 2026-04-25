# Phase 8-1a: 매뉴얼 CC ↔ 펌웨어 CC 교차 검증

> **매뉴얼 기준 CC 41개** vs **펌웨어 FUN_08166810의 161 CC case**

## 매뉴얼 공식 MIDI CC 매핑 (v4.0.1)

| CC# | Parameter | 펌웨어 case 존재 | 비고 |
|-----|-----------|-----------------|------|
| 1 | Mod Wheel | ✅ case 1 | 펌웨어에 존재 |
| 5 | Glide (Portamento Time) | ✅ case 5 | |
| 14 | Osc1 Wave | ✅ case 0xe | |
| 15 | Osc1 Timbre | ✅ case 0xf | |
| 16 | Osc1 Shape | ✅ case 0x10 | |
| 17 | Osc1 Volume | ✅ case 0x11 | |
| 18 | Osc2 Tune | ✅ case 0x12 | |
| 19 | Osc2 Wave | ✅ case 0x13 | |
| 20 | Osc2 Timbre | ✅ case 0x14 | |
| 21 | Osc2 Shape | ✅ case 0x15 | |
| 22 | FX1 Time | ✅ case 0x16 | |
| 23 | FX1 Intensity | ✅ case 0x17 | |
| 24 | VCF Env Amt | ✅ case 0x18 | |
| 25 | FX1 Amount | ✅ case 0x19 | |
| 26 | FX2 Time | ✅ case 0x1a | |
| 27 | FX2 Intensity | ✅ case 0x1b | |
| 28 | FX2 Amount | ✅ case 0x1c | |
| 29 | FX3 Time | ✅ case 0x1d | |
| 30 | FX3 Intensity | ✅ case 0x1e | |
| 31 | FX3 Amount | ✅ case 0x1f | |
| 64 | Sustain Pedal | ✅ case 0x40 | |
| 68 | CycEnv Rise Shape | ✅ case 0x44 | |
| 69 | CycEnv Fall Shape | ✅ case 0x45 | |
| 70 | Osc1 Tune | ✅ case 0x46 | |
| 71 | VCF Resonance | ✅ case 0x47 | |
| 73 | Osc2 Tune | ✅ case 0x49 | |
| 74 | VCF Cutoff | ✅ case 0x4a | |
| 76 | CycEnv Rise | ✅ case 0x4c | |
| 77 | CycEnv Fall | ✅ case 0x4d | |
| 78 | CycEnv Hold | ✅ case 0x4e | |
| 80 | Env Attack | ✅ case 0x50 | |
| 81 | Env Decay | ✅ case 0x51 | |
| 82 | Env Sustain | ✅ case 0x52 | |
| 83 | Env Release | ✅ case 0x53 | |
| 85 | LFO1 Rate | ✅ case 0x55 | |
| 87 | LFO2 Rate | ✅ case 0x57 | |
| 94 | Velocity Env Mod | ✅ case 0x5e | |
| 115 | Seq Gate | ✅ case 0x73 | |
| 116 | Seq Spice | ✅ case 0x74 | |
| 117 | Macro M1 | ✅ case 0x75 | |
| 118 | Macro M2 | ✅ case 0x76 | |

## 분석 문서 오류 정정 필요

### PHASE6_MIDI_CHART.md의 CC 매핑 오류

| CC# | 기존 표기 (오류) | 매뉴얼 정정 | 차이 |
|-----|-----------------|-------------|------|
| 1 | Osc1 Type/Waveform | **Mod Wheel** | 완전 다름 |
| 5 | Osc1 Octave | **Glide** | 완전 다름 |
| 14 | Osc2 Octave | **Osc1 Wave** | Osc2 → Osc1 |
| 15 | Osc2 Semitone | **Osc1 Timbre** | 완전 다름 |
| 16 | Osc2 Amount/Mix | **Osc1 Shape** | 완전 다름 |
| 17 | — | **Osc1 Volume** | 누락 |
| 18 | — | **Osc2 Tune** | 누락 |
| 19 | — | **Osc2 Wave** | 누락 |
| 20 | Osc1 Level | **Osc2 Timbre** | Osc1 → Osc2 |
| 21 | Osc2 Level | **Osc2 Shape** | 완전 다름 |
| 24 | Filter Cutoff | **VCF Env Amt** | Cutoff → Env Amt |
| 25 | Filter Resonance | **FX1 Amount** | 완전 다름 |
| 26 | Filter Env Amount | **FX2 Time** | 완전 다름 |
| 71 | FX A Type | **VCF Resonance** | 완전 다름 |
| 72 | FX A Param 1 | — | 매뉴얼 없음 |
| 73 | FX A Param 2 | **Osc2 Tune** | 완전 다름 |
| 74 | FX A Param 3 | **VCF Cutoff** | Cutoff이지만 CC#이 24→74 |
| 75-79 | FX A Param 4-8 | — | 매뉴얼 없음 |
| 85 | FX B Type | **LFO1 Rate** | 완전 다름 |
| 86-186 | FX Extended (101개) | 개별 파라미터 | 101개 블록이 아님 |
| 193 | Macro 1 | — | 매뉴얼 CC117 |
| 195-204 | Macro 2-7 | — | 매뉴얼에 Macro는 M1/M2만 |

### 결론

**PHASE6_MIDI_CHART.md의 CC 매핑은 전면 잘못됨.** 원인:
1. Phase 6에서 CC 핸들러의 case 값은 올바르게 추출했으나
2. 각 case가 **어떤 파라미터**에 매핑되는지 추론할 때
3. 펌웨어 내부 순서(CC#1=첫 번째, CC#2=두 번째...)를 매뉴얼 파라미터 순서로 잘못 대응

**정확한 매핑은 XML 리소스와 매뉴얼을 교차 검증해야 함.**
