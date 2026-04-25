# Phase 2: CM4 Sound Engine Analysis — Results

## Date: 2026-04-21
## Binary: minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin
## Image Base: 0x08120000 (STM32H745 Flash Bank 2)

---

## 2-1. String XRef Analysis (76 mappings found)

### Key Functions
| Function | Description | Key Strings |
|----------|-------------|-------------|
| FUN_08179fb0 | Oscillator type name lookup | "-Empty-", "SuperWave", "VAnalog", "Noise" |
| FUN_0817a4f4 | Shaper/sub-type lookup | "SuperWave", "Sculpting", "Soft Clip", "RingMod", "Rectify" |
| FUN_081492b8 | CM4 app main | "CM4 app" |
| FUN_081a1558 | Build info | "build version : " |
| FUN_081a3e7c | USB MIDI | "MiniFreak MIDI 4 In" |

### Preset System Functions (17 unique)
- `FUN_0813da28`: "Unable to get preset" / "Too many dir entries"
- `FUN_0816589c`: "Preset corrupted" (2 refs)
- `FUN_08167a9c`: "Preset save error!" + "Preset corrupted"
- `FUN_08170fc4`: "Preset %d" (display formatting)
- `FUN_08174430`: "Press preset encoder"
- 12+ functions with "Preset save error!" — each corresponds to a different save context

### Preset Parameter Enums (from RTTI strings)
| Enum Type | Getter | Setter | Description |
|-----------|--------|--------|-------------|
| eSynthParams | Preset::get(eSynthParams) | Preset::set(eSynthParams) | Oscillator, filter, envelope params |
| eFXParams | Preset::get(eFXParams) | Preset::set(eFXParams) | FX processor params |
| eCtrlParams | Preset::get(eCtrlParams) | Preset::set(eCtrlParams) | Control surface params |
| eSeqParams | Preset::get(eSeqParams) | Preset::set(eSeqParams) | Sequencer params |
| eSeqAutomParams | Preset::get(eSeqAutomParams) | Preset::set(eSeqAutomParams) | Automation params |
| eSeqStepParams | Preset::get(eSeqStepParams) | Preset::set(eSeqStepParams) | Step sequencer data |
| eShaperParams | Preset::get(eShaperParams) | Preset::set(eShaperParams) | Custom shaper params |
| eAutomIdx | get(eAutomIdx) | — | Automation index (never accessed) |
| eStepIdx | get(eStepIdx) | — | Step index (never accessed) |

### Other Key Classes
- **CvCalib**: CV calibration (getCalibMinValue, getCalibMaxValue, getCvCalibrated, setCalibCutValue, setCalibVcaClickValue)
  - Uses eCvKind enum and eVcfType enum
- **MNF_Edit**: Edit parameter management (set(eEditParams))
- **Settings**: Global settings (set(eSettingsParams))
- **MNF_WheelsController**: Wheel/column matrix control (clearColumn, drawColumnPosition)

---

## 2-2. Oscillator Engine VTable Mapping

### Engine Base Class (from Plaits source + vtable analysis)
```cpp
class Engine {
    virtual ~Engine();           // vtable[0]
    virtual ~Engine();           // vtable[1] 
    virtual void Init(...);      // vtable[2] = 0x081AA098 (shared base)
    virtual void Reset();        // vtable[3] = 0x081AEFD4 (shared base)
    virtual void LoadUserData(); // vtable[4] = 0x081AA0A4 (shared base)
    virtual void Render(...);    // vtable[5] = 0x081AA0AC (shared base)
};
```

### 13 Oscillator VTables (binary offsets 0x37CB4~0x386D4)
| Idx | VTable (abs) | Init Func | Group | Engine | Plaits Equivalent |
|-----|-------------|-----------|-------|--------|-------------------|
| 0 | 0x081B7CB4 | ? (default) | — | **VAnalog** | VirtualAnalogEngine |
| 1 | 0x081B7D70 | FUN_0819c714 | A | **SuperWave** | SwarmEngine |
| 2 | 0x081B7E2C | FUN_0819c714 | A | **KarplusStr** | StringEngine |
| 3 | 0x081B7EEC | FUN_0819c714 | A | **Waveshaper** | WaveshapingEngine |
| 4 | 0x081B7FA8 | FUN_0819c714 | A | **Two Op. FM** | FMEngine |
| 5 | 0x081B8068 | FUN_0819c714 | A | **Noise** | NoiseEngine |
| 6 | 0x081B8124 | FUN_0819c7e4 | B | **Wavetable** | WavetableEngine |
| 7 | 0x081B81E4 | FUN_0819c7e4 | B | **Sample** | Custom (Arturia) |
| 8 | 0x081B82DC | FUN_0819c7e4 | B | **Audio In** | Custom (Arturia) |
| 9 | 0x081B839C | FUN_0819c7e4 | B | **Granular** | GrainEngine |
| 10 | 0x081B8494 | FUN_0819c7e4 | B | **Chord** | ChordEngine |
| 11 | 0x081B8558 | FUN_0819c93c | C | **Speech** | SpeechEngine |
| 12 | 0x081B8614 | FUN_0819c93c | C | **Strings** | StringEngine (ext) |

### Init Function Groups
- **Group A** (FUN_0819c714, 78 instr): Simple parameter fill — analog/math oscillators
- **Group B** (FUN_0819c7e4, 123 instr): Complex init with config flags — digital/sample oscillators
- **Group C** (FUN_0819c93c, 96 instr): Table-lookup init — speech synthesis with formant data

---

## 2-3. Oscillator String Enum Order (by binary address)

```
0x081AF388: "Basic Waves"     — Type 0
0x081AF394: "SuperWave"       — Type 1
0x081AF3A8: "KarplusStr"      — Type 2
0x081AF3B4: "VAnalog"         — Type 3
0x081AF3BC: "Waveshaper"      — Type 4
0x081AF3C8: "Two Op. FM"      — Type 5
              (gap ~12 bytes)
0x081AF3E4: "Speech"          — Type 6/7
0x081AF3EC: "Modal"           — Type 7/8
0x081AF3F4: "Noise"           — Type 8/9
              (gap ~116 bytes — Granular?)
0x081AF468: "Audio In"        — Type 9/10
0x081AF474: "Wavetable"       — Type 10/11
0x081AF480: "Sample"          — Type 11/12
```

Additional types at separate locations:
```
0x081AE058: "Chorder"
0x081B0A14: "Strings"
```

---

## 2-4. Shaper Types (from FUN_0817a4f4)
```
0: SuperWave (wave multiplication)
1: Sculpting
2: Soft Clip
3: RingMod
4: Rectify
```

---

## 2-5. FX Types (from string references)
```
- Chorus
- Phaser
- Flanger
- Reverb
- Distortion
- Stereo
- Delay Routing / Reverb Routing
```

### Filter Types
```
- Multi Filter
- Surgeon Filter
- Comb Filter
- Phaser Filter
```

---

### 2-6. Preset Format = 커스텀 바이너리 (nanopb 아님!)

nanopb 에러 문자열이 존재하지만, 프리셋 데이터는 **커스텀 바이너리 포맷** 사용:
- `\"varint overflow\"` — nanopb 문자열 발견 (but 프리셋과 무관)
- `\"invalid wire_type\"` — nanopb 문자열 발견 (but 프리셋과 무관)
- 실제 프리셋: **고정 0xD00 바이트 + uint16 파라미터 + CRC8 + 매직 0x410F** (Phase 2-5에서 확인)
- nanopb는 **다른 목적** (USB SysEx 통신 등)에 사용되는 것으로 추정

---

## 2-7. Key UI/Parameter Strings (Categorized)

### Oscillator Parameters
Osc Sel, Osc Types, Osc Free Run, Osc Mix Non-Lin, Osc1 Mod Quant, Osc2 Mod Quant,
Pitch 1, Pitch 2, Shape 1, Shape 2, Timbre 1, Timbre 2, Wave 1, Wave 2,
Detune, Morph, Wavefold, Waveform, Paraphony On, SwapOsc

### Filter Parameters  
Cutoff, Resonance, Poles, Envelope > Cutoff, Filtered, Multi Filter, Surgeon Filter,
Comb Filter, Phaser Filter

### Envelope Parameters
Attack, Decay, Sustain, Release, Attack Curve, Decay Curve, Release Curve,
Env Continue, Env Reset, Velo > Env, Velo > Env Amnt, CycEnv, Cycling Env,
Decaying Decays

### LFO Parameters
LFO1 Rate, LFO1 Retrig, LFO1 Sync, LFO1 Wave, LFO1 user curve,
LFO2 Rate, LFO2 Sync, LFO2 Wave, LFO2 user curve, Lfo Sel

### FX Parameters
FX Slots, FX1 Enable, FX1 Type, FX3 Type, Dry/Wet, Sound FX,
Delay Routing, Reverb Routing, Chorus, Phaser, Flanger, Reverb, Distortion

### Sequencer Parameters
Seq Page, Seq Start, Seq Transpose, Seq + Mods, Seq Mods,
Step En, Step %d / %d (On/Off), All Steps, One Step,
Stepped 1-4, L: %d.%d, V: %d-%d

### Macro/Matrix Parameters
Matrix, Matrix Amount, Matrix Routing, Matrix Src VeloAT,
Macro 1, Macro 2, Macro1 amount, Macro1 dest, Macro2 amount, Macro2 dest,
Click for more Dest, Move controls to assign to Macro

### Voice Parameters
Voice, Voices, Unison, Uni (Poly), Uni Spread, Unison Count, Unison Mode,
Poly Allocation, Poly Kbd, Poly Steal Mode, Poly2Mono,
Bend Range, Octave, Octave Tune, Master Tune, Glide, Glide Mode

---

## Files Generated
- `cm4_engine_analysis.json` — 1473 functions, 906 strings, 76 string→function XRefs
- `cm4_decompiled_osc.json` — Oscillator name lookup decompilation (10K + 13K chars)
- `cm4_osc_init_decompiled.json` — 13 oscillator Init() decompilations
