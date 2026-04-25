# Phase 7: Plaits Source Code Analysis — Engine & Oscillator Mapping

## Overview

This document provides a comprehensive mapping of Mutable Instruments Plaits source code structures to enable identification of these components in the MiniFreak CM7 firmware binary. Plaits source is from the reference tree at `~/hoon/minifreak/reference/plaits_source/plaits/`.

---

## 1. Base Engine Class (Virtual Interface)

**File:** `dsp/engine/engine.h`

### Virtual Method Table (vtable) Layout

The `Engine` base class defines the vtable that all engine subclasses inherit:

| Slot | Method | Signature |
|------|--------|-----------|
| 0 | Destructor | `~Engine()` (virtual, no explicit override needed) |
| 1 | Init | `virtual void Init(stmlib::BufferAllocator* allocator) = 0` |
| 2 | Reset | `virtual void Reset() = 0` |
| 3 | LoadUserData | `virtual void LoadUserData(const uint8_t* user_data) = 0` |
| 4 | Render | `virtual void Render(const EngineParameters& parameters, float* out, float* aux, size_t size, bool* already_enveloped) = 0` |

**Note:** The vtable also includes a virtual destructor at slot 0. Slots 1-4 are the pure virtual methods above. There is **no** data vtable pointer — `post_processing_settings` is a plain member at offset 4 (after vptr).

### EngineParameters Struct

```c
struct EngineParameters {
  int trigger;      // TriggerState enum: 0=LOW, 1=RISING, 2=UNPATCHED, 4=HIGH
  float note;       // MIDI note (constrained -119 to 120)
  float timbre;     // 0.0 to 1.0
  float morph;      // 0.0 to 1.0
  float harmonics;  // 0.0 to 1.0
  float accent;     // compressed level 0.0 to ~1.0
};
```
**Struct size:** 24 bytes (6 fields × 4 bytes)

### PostProcessingSettings Struct

```c
struct PostProcessingSettings {
  float out_gain;          // Negative = use limiter
  float aux_gain;          // Negative = use limiter
  bool already_enveloped;  // Engine has its own envelope
};
```
**Struct size:** 12 bytes (2 floats + 1 bool + padding)

### Global DSP Constants

| Constant | Value | Notes |
|----------|-------|-------|
| `kSampleRate` | 48000.0f | Nominal sample rate |
| `kCorrectedSampleRate` | 47872.34f | Actual STM32 I2S clock-derived rate |
| `a0` | 55.0f / kCorrectedSampleRate ≈ 0.001148f | Tuning reference |
| `kMaxBlockSize` | 24 | Maximum render block size |
| `kBlockSize` | 12 | Normal render block size |
| `kMaxEngines` | 24 | EngineRegistry max capacity |
| `kMaxFrequency` | 0.25f | Max normalized frequency |
| `kMinFrequency` | 0.000001f | Min normalized frequency |

---

## 2. Engine Registration Order (Voice::Init)

**File:** `dsp/voice.cc`

The engines are registered in this exact order in `Voice::Init()`:

| Index | Engine Class | Category | out_gain | aux_gain | already_enveloped |
|-------|-------------|----------|----------|----------|-------------------|
| 0 | VirtualAnalogVCFEngine | engine2 | 1.0 | 1.0 | false |
| 1 | PhaseDistortionEngine | engine2 | 0.7 | 0.7 | false |
| 2 | SixOpEngine | engine2 | 1.0 | 1.0 | **true** |
| 3 | SixOpEngine | engine2 | 1.0 | 1.0 | **true** |
| 4 | SixOpEngine | engine2 | 1.0 | 1.0 | **true** |
| 5 | WaveTerrainEngine | engine2 | 0.7 | 0.7 | false |
| 6 | StringMachineEngine | engine2 | 0.8 | 0.8 | false |
| 7 | ChiptuneEngine | engine2 | 0.5 | 0.5 | false |
| 8 | VirtualAnalogEngine | engine | 0.8 | 0.8 | false |
| 9 | WaveshapingEngine | engine | 0.7 | 0.6 | false |
| 10 | FMEngine | engine | 0.6 | 0.6 | false |
| 11 | GrainEngine | engine | 0.7 | 0.6 | false |
| 12 | AdditiveEngine | engine | 0.8 | 0.8 | false |
| 13 | WavetableEngine | engine | 0.6 | 0.6 | false |
| 14 | ChordEngine | engine | 0.8 | 0.8 | false |
| 15 | SpeechEngine | engine | -0.7 | 0.8 | false |
| 16 | SwarmEngine | engine | -3.0 | 1.0 | false |
| 17 | NoiseEngine | engine | -1.0 | -1.0 | false |
| 18 | ParticleEngine | engine | -2.0 | 1.0 | false |
| 19 | StringEngine | engine | -1.0 | 0.8 | **true** |
| 20 | ModalEngine | engine | -1.0 | 0.8 | **true** |
| 21 | BassDrumEngine | engine | 0.8 | 0.8 | **true** |
| 22 | SnareDrumEngine | engine | 0.8 | 0.8 | **true** |
| 23 | HiHatEngine | engine | 0.8 | 0.8 | **true** |

**Key insight:** Negative out_gain values indicate a limiter should be used on that channel. The `already_enveloped` flag means the engine generates its own amplitude envelope (drums, strings, modal, 6-op FM).

---

## 3. Detailed Engine Class Structures

### 3.1 dsp/engine/ — Original Plaits Engines

#### 3.1.1 VirtualAnalogEngine
- **Parent:** `Engine`
- **Sub-objects:** `VariableShapeOscillator primary_`, `VariableShapeOscillator auxiliary_`, `VariableShapeOscillator sync_`, `VariableSawOscillator variable_saw_`
- **Allocated:** `float* temp_buffer_`
- **Unique members:** `auxiliary_amount_`, `xmod_amount_`
- **Defines:** `#define VA_VARIANT 2`
- **Signature constants:** Uses `kMaxFrequency = 0.25f` clamping, polyBLEP

#### 3.1.2 WaveshapingEngine
- **Parent:** `Engine`
- **Sub-objects:** `Oscillator slope_`, `Oscillator triangle_`
- **Unique members:** `previous_shape_`, `previous_wavefolder_gain_`, `previous_overtone_gain_`
- **No allocated buffers** — stateless oscillators
- **Signature constants:** Uses `lut_fold` (516 entries), `lut_fold_2` (516 entries), waveshaping lookup tables

#### 3.1.3 FMEngine
- **Parent:** `Engine`
- **Unique members:** `uint32_t carrier_phase_`, `uint32_t modulator_phase_`, `uint32_t sub_phase_`, `float previous_carrier_frequency_`, `float previous_modulator_frequency_`, `float previous_amount_`, `float previous_feedback_`, `float previous_sample_`, `float sub_fir_`, `float carrier_fir_`
- **No allocated buffers** — all phase accumulators are uint32_t
- **Signature:** Classic 2-operator FM with feedback, sub-oscillator. Uses `lut_fm_frequency_quantizer` (130 entries)

#### 3.1.4 GrainEngine
- **Parent:** `Engine`
- **Sub-objects:** `GrainletOscillator grainlet_[2]`, `ZOscillator z_oscillator_`, `stmlib::OnePole dc_blocker_[2]`
- **Unique members:** `float grain_balance_`
- **Signature:** Crossfades between two GrainletOscillators and one ZOscillator

#### 3.1.5 AdditiveEngine
- **Parent:** `Engine`
- **Constants:** `kHarmonicBatchSize = 12`, `kNumHarmonics = 36`, `kNumHarmonicOscillators = 3`
- **Sub-objects:** `HarmonicOscillator<12> harmonic_oscillator_[3]`
- **Allocated:** `float* amplitudes_` (36 floats)
- **Signature:** Chebyshev polynomial-based harmonic synthesis, 36 harmonics in 3 batches of 12

#### 3.1.6 WavetableEngine
- **Parent:** `Engine`
- **Sub-objects:** Uses `WavetableOscillator<128, 15>` (128 samples, 15 waveforms)
- **Unique members:** `float phase_`, 6 LP-filtered coordinates (`x/y/z_pre_lp_`, `x/y/z_lp_`), `previous_x/y/z_`, `previous_f0_`, `const int16_t** wave_map_`, `Differentiator diff_out_`
- **Has `LoadUserData`:** YES — loads custom wavetable map from user data
- **Signature:** 8×8×3 wave terrain (wav_integrated_waves = 25344 int16_t entries)

#### 3.1.7 ChordEngine
- **Parent:** `Engine`
- **Constants:** `kChordNumHarmonics = 3`
- **Sub-objects:** `StringSynthOscillator divide_down_voice_[kChordNumVoices]` (5 voices), `WavetableOscillator<128, 15> wavetable_voice_[kChordNumVoices]`, `ChordBank chords_`
- **Unique members:** `float morph_lp_`, `float timbre_lp_`
- **Signature:** Divide-down organ (StringSynthOscillator) crossfading with wavetable chords

#### 3.1.8 SpeechEngine
- **Parent:** `Engine`
- **Sub-objects:** `stmlib::HysteresisQuantizer2 word_bank_quantizer_`, `NaiveSpeechSynth`, `SAMSpeechSynth`, `LPCSpeechSynthController`, `LPCSpeechSynthWordBank`
- **Allocated:** `float* temp_buffer_[2]`
- **Unique members:** `float prosody_amount_`, `float speed_`
- **Signature constants:** `kSAMNumPhonemes = 17` (9 vowels + 8 consonants), `kLPCSpeechSynthFPS = 40.0f`, `kLPCSpeechSynthNumPhonemes = 15` (5 vowels + 10 consonants)

#### 3.1.9 SwarmEngine
- **Parent:** `Engine`
- **Constants:** `kNumSwarmVoices = 8`
- **Allocated:** `SwarmVoice* swarm_voice_` (dynamically allocated array of 8)
- **Sub-objects per voice:** `GrainEnvelope`, `AdditiveSawOscillator`, `FastSineOscillator`
- **Signature:** 8 saw+sine voice swarm with grain envelope, `SemitonesToRatio(48.0f * expo_amount * spread * rank_)` detuning

#### 3.1.10 NoiseEngine
- **Parent:** `Engine`
- **Sub-objects:** `ClockedNoise clocked_noise_[2]`, `stmlib::Svf lp_hp_filter_`, `stmlib::Svf bp_filter_[2]`
- **Allocated:** `float* temp_buffer_`
- **Unique members:** `previous_f0_`, `previous_f1_`, `previous_q_`, `previous_mode_`
- **Signature:** Two clocked noise sources → multimode filter (LP/HP/BP)

#### 3.1.11 ParticleEngine
- **Parent:** `Engine`
- **Constants:** `kNumParticles = 6`
- **Sub-objects:** `Particle particle_[6]`, `Diffuser diffuser_`, `stmlib::Svf post_filter_`
- **Signature:** 6 random impulse particles → bandpass filter → diffuser (7 allpass delay lines: 126, 180, 269, 444, 1653, 2010, 3411 samples)

#### 3.1.12 StringEngine
- **Parent:** `Engine`
- **Constants:** `kNumStrings = 3`
- **Sub-objects:** `StringVoice voice_[3]`, `DelayLine<float, 16> f0_delay_`
- **Allocated:** `float* temp_buffer_`
- **Unique members:** `float f0_[3]`, `int active_string_`
- **already_enveloped:** true — Karplus-Strong string synthesis

#### 3.1.13 ModalEngine
- **Parent:** `Engine`
- **Sub-objects:** `ModalVoice voice_`
- **Allocated:** `float* temp_buffer_`
- **Unique members:** `float harmonics_lp_`
- **Constants in ModalVoice:** `Resonator` with `kMaxNumModes = 24`, `kModeBatchSize = 4`
- **already_enveloped:** true — mallet/modal synthesis with click→LPF→resonator

#### 3.1.14 BassDrumEngine
- **Parent:** `Engine`
- **Sub-objects:** `AnalogBassDrum`, `SyntheticBassDrum`, `Overdrive`
- **already_enveloped:** true

#### 3.1.15 SnareDrumEngine
- **Parent:** `Engine`
- **Sub-objects:** `AnalogSnareDrum`, `SyntheticSnareDrum`
- **already_enveloped:** true

#### 3.1.16 HiHatEngine
- **Parent:** `Engine`
- **Sub-objects:** `HiHat<SquareNoise, SwingVCA, true, false> hi_hat_1_`, `HiHat<RingModNoise, LinearVCA, false, true> hi_hat_2_`
- **Allocated:** `float* temp_buffer_`
- **already_enveloped:** true — two 808-style noise hi-hats

### 3.2 dsp/engine2/ — Newer Engines (Plaits 1.x)

#### 3.2.1 VirtualAnalogVCFEngine
- **Parent:** `Engine`
- **Sub-objects:** `stmlib::Svf svf_[2]`, `VariableShapeOscillator oscillator_`, `VariableShapeOscillator sub_oscillator_`
- **Unique members:** `previous_cutoff_`, `previous_stage2_gain_`, `previous_q_`, `previous_gain_`, `previous_sub_gain_`
- **Signature:** VA oscillator → cascaded SVF (2× state-variable filter) + sub-osc

#### 3.2.2 PhaseDistortionEngine
- **Parent:** `Engine`
- **Sub-objects:** `VariableShapeOscillator shaper_`, `VariableShapeOscillator modulator_`
- **Allocated:** `float* temp_buffer_`
- **Signature:** Asymmetric triangle modulator → phase distortion on carrier

#### 3.2.3 SixOpEngine
- **Parent:** `Engine`
- **Constants:** `kNumSixOpVoices = 2`
- **Sub-objects:** `fm::Algorithms<6>`, `FMVoice voice_[2]` (each with `fm::Voice<6>`, `fm::Lfo`)
- **Allocated:** `float* temp_buffer_`, `float* acc_buffer_`, `fm::Patch* patches_`
- **Unique members:** `stmlib::HysteresisQuantizer2 patch_index_quantizer_`, `int active_voice_`, `int rendered_voice_`
- **Has `LoadUserData`:** YES — loads FM patch bank
- **Signature:** 6-operator FM synthesis, 2 voices, patch loading from SYX banks

#### 3.2.4 WaveTerrainEngine
- **Parent:** `Engine`
- **Sub-objects:** `FastSineOscillator path_`
- **Allocated:** `float* temp_buffer_`
- **Unique members:** `float offset_`, `float terrain_`, `const int8_t* user_terrain_`
- **Has `LoadUserData`:** YES — loads custom terrain data
- **Signature:** 2D terrain function evaluated along elliptical path

#### 3.2.5 StringMachineEngine
- **Parent:** `Engine`
- **Sub-objects:** `ChordBank chords_`, `Ensemble ensemble_`, `StringSynthOscillator divide_down_voice_[kChordNumNotes]` (4 voices), `stmlib::NaiveSvf svf_[2]`
- **Unique members:** `float morph_lp_`, `float timbre_lp_`
- **Signature:** String synth + chorus (ensemble) + filter — "string machine" emulation

#### 3.2.6 ChiptuneEngine
- **Parent:** `Engine`
- **Sub-objects:** `SuperSquareOscillator voice_[kChordNumVoices]` (5 voices), `NESTriangleOscillator<> bass_`, `ChordBank chords_`, `Arpeggiator arpeggiator_`, `stmlib::HysteresisQuantizer2 arpeggiator_pattern_selector_`
- **Unique members:** `float envelope_shape_`, `float envelope_state_`, `float aux_envelope_amount_`
- **Enum:** `NO_ENVELOPE = 2`
- **Signature:** NES/SNES-style chiptune with arpeggiator, hard-synced squares + NES triangle bass

#### 3.2.7 Arpeggiator (helper class, not an Engine)
- **Enum:** `ARPEGGIATOR_MODE_UP`, `_DOWN`, `_UP_DOWN`, `_RANDOM`, `_LAST` (5 modes)
- **Members:** `mode_`, `range_`, `note_`, `octave_`, `direction_`

---

## 4. Oscillator Subsystem Constants

### 4.1 Sine Oscillator
| Constant | Value |
|----------|-------|
| `kSineLUTSize` | 512.0f |
| `kSineLUTQuadrature` | 128 |
| `kSineLUTBits` | 9 |
| `LUT_SINE_SIZE` | 641 (in resources.h) |

### 4.2 Waveshaping Tables
| Table | Size | Type |
|-------|------|------|
| `lut_fold` | 516 | float |
| `lut_fold_2` | 516 | float |
| `lut_ws_inverse_tan` | 257 | int16_t |
| `lut_ws_inverse_sin` | 257 | int16_t |
| `lut_ws_linear` | 257 | int16_t |
| `lut_ws_bump` | 257 | int16_t |
| `lut_ws_double_bump` | 257 | int16_t |

### 4.3 FM Tables
| Table | Size | Type |
|-------|------|------|
| `lut_fm_frequency_quantizer` | 130 | float |
| FM patch banks (SYX) | 3 × 4096 | uint8_t |

### 4.4 Physical Modelling
| Constant | Value |
|----------|-------|
| `kMaxNumModes` | 24 |
| `kModeBatchSize` | 4 |
| `lut_stiffness` | 65 entries |
| `lut_svf_shift` | 257 entries |
| `lut_4x_downsampler_fir` | 4 entries |

### 4.5 Speech Synthesis
| Constant | Value |
|----------|-------|
| `kSAMNumFormants` | 3 |
| `kSAMNumVowels` | 9 |
| `kSAMNumConsonants` | 8 |
| `kSAMNumPhonemes` | 17 |
| `kLPCSpeechSynthMaxWords` | 32 |
| `kLPCSpeechSynthMaxFrames` | 1024 |
| `kLPCSpeechSynthNumVowels` | 5 |
| `kLPCSpeechSynthNumConsonants` | 10 |
| `kLPCSpeechSynthFPS` | 40.0f |
| `lut_lpc_excitation_pulse` | 640 entries |

### 4.6 Chord System
| Constant | Value |
|----------|-------|
| `kChordNumNotes` | 4 |
| `kChordNumVoices` | 5 |
| `kChordNumChords` | 17 (full build) / 11 (mini build) |
| `kChordNumHarmonics` | 3 |

### 4.7 Diffuser Delay Lines (ParticleEngine)
| Line | Size (samples) |
|------|---------------|
| ap1 | 126 |
| ap2 | 180 |
| ap3 | 269 |
| ap4 | 444 |
| dapa | 1653 |
| dapb | 2010 |
| del | 3411 |
| **Total** | **8083** (within 8192 FxEngine buffer) |

Constants: `kap = 0.625f`, `klp = 0.75f`

### 4.8 VariableSawOscillator
| Constant | Value |
|----------|-------|
| `kVariableSawNotchDepth` | 0.2f |

### 4.9 NESTriangleOscillator
| Constant | Value |
|----------|-------|
| Default `num_bits` template param | 5 |
| Number of steps | 32 (1 << 5) |

### 4.10 FastSineOscillator (Magic Circle)
| Constant | Value |
|----------|-------|
| Max frequency | 0.25f |
| Norm correction range | 0.5 to 2.0 |
| Fast2Sin polynomial | `f_pi * (2.0f - (2.0f * 0.96f / 6.0f) * f_pi * f_pi)` |
| Coefficient `0.96` | Magic constant for Taylor approximation |

### 4.11 SuperSquareOscillator
| Constant | Value |
|----------|-------|
| Sync threshold | `0.5f + 0.98f * shape` (shape < 0.5) |
| Octave spread | `1.0f + 16.0f * (shape - 0.5f)^2` (shape ≥ 0.5) |

---

## 5. Comprehensive Engine→MiniFreak Mapping Table

The MiniFreak CM7 binary was found to contain 13 oscillator types via vtable analysis. The MiniFreak uses a **subset** of the Plaits engines, likely selecting the most musically useful ones. Based on the 13 oscillator types identified from firmware analysis and the source code structure:

| Plaits Engine Index | Plaits Source Class | Directory | Likely MiniFreak Oscillator Type | Key Binary Signatures |
|---------------------|---------------------|-----------|----------------------------------|----------------------|
| 0 | VirtualAnalogVCFEngine | engine2 | **Virtual Analog (VCF)** | 2× SVF state vars, sub_oscillator_, `previous_cutoff_` |
| 1 | PhaseDistortionEngine | engine2 | **Phase Distortion** | `temp_buffer_`, two `VariableShapeOscillator` (shaper_ + modulator_) |
| 2/3/4 | SixOpEngine | engine2 | **FM (6-op)** — 3 slots | `fm::Algorithms<6>`, `FMVoice[2]`, `fm::Patch*`, patch banks |
| 5 | WaveTerrainEngine | engine2 | **Wave Terrain** | `FastSineOscillator path_`, `user_terrain_`, `offset_`, `terrain_` |
| 6 | StringMachineEngine | engine2 | **Strings** | `Ensemble`, `StringSynthOscillator[4]`, `NaiveSvf svf_[2]` |
| 7 | ChiptuneEngine | engine2 | **Chiptune/8-bit** | `SuperSquareOscillator[5]`, `NESTriangleOscillator`, `Arpeggiator` |
| 8 | VirtualAnalogEngine | engine | **Virtual Analog (sync)** | 2× VariableShapeOscillator + sync_, VariableSawOscillator, `VA_VARIANT=2` |
| 9 | WaveshapingEngine | engine | **Waveshaping** | 2× `Oscillator` (slope_, triangle_), fold LUT references |
| 10 | FMEngine | engine | **FM (2-op)** | 3× uint32_t phase accumulators, feedback, `sub_fir_` |
| 11 | GrainEngine | engine | **Grains** | `GrainletOscillator[2]`, `ZOscillator`, `OnePole dc_blocker_[2]` |
| 12 | AdditiveEngine | engine | **Additive/Harmonics** | `HarmonicOscillator<12>[3]`, 36 harmonics, `amplitudes_` alloc |
| 13 | WavetableEngine | engine | **Wavetable** | 8×8×3 terrain, `wave_map_`, `Differentiator diff_out_` |
| 14 | ChordEngine | engine | **Chords** | `StringSynthOscillator[5]`, `WavetableOscillator<128,15>[5]`, `ChordBank` |
| 15 | SpeechEngine | engine | **Speech/VOX** | `SAMSpeechSynth`, `LPCSpeechSynthController`, `word_bank_quantizer_` |
| 16 | SwarmEngine | engine | **Swarm/Super** | 8 dynamically allocated `SwarmVoice` (grain envelope + saw + sine) |
| 17 | NoiseEngine | engine | **Noise** | `ClockedNoise[2]`, `Svf lp_hp_filter_`, `Svf bp_filter_[2]` |
| 18 | ParticleEngine | engine | **Particles/Clouds** | `Particle[6]`, `Diffuser` (7 delay lines), `Svf post_filter_` |
| 19 | StringEngine | engine | **Karplus-Strong** | `StringVoice[3]`, `DelayLine<float,16>`, `active_string_` |
| 20 | ModalEngine | engine | **Modal/Pluck** | `ModalVoice` (Resonator with 24 modes, 6 SVF batches) |
| 21 | BassDrumEngine | engine | **Kick Drum** | `AnalogBassDrum` + `SyntheticBassDrum` + `Overdrive` |
| 22 | SnareDrumEngine | engine | **Snare Drum** | `AnalogSnareDrum` + `SyntheticSnareDrum` |
| 23 | HiHatEngine | engine | **Hi-Hat** | `HiHat<SquareNoise,SwingVCA,true,false>` + `HiHat<RingModNoise,LinearVCA,false,true>` |

### MiniFreak 13 Oscillator Types — Source Mapping

Based on the firmware vtable analysis finding 13 oscillator types, and typical Arturia product decisions (removing percussion engines, consolidating FM):

| # | MiniFreak Oscillator | Most Likely Plaits Source |
|---|---------------------|---------------------------|
| 1 | Virtual Analog | `VirtualAnalogVCFEngine` (engine2, index 0) or `VirtualAnalogEngine` (engine, index 8) |
| 2 | Waveshaping | `WaveshapingEngine` (index 9) |
| 3 | FM | `FMEngine` (index 10) or `SixOpEngine` (index 2/3/4) |
| 4 | Phase Distortion | `PhaseDistortionEngine` (index 1) |
| 5 | Additive | `AdditiveEngine` (index 12) |
| 6 | Wavetable | `WavetableEngine` (index 13) |
| 7 | Chords | `ChordEngine` (index 14) or `StringMachineEngine` (index 6) |
| 8 | Speech/VOX | `SpeechEngine` (index 15) |
| 9 | Noise | `NoiseEngine` (index 17) |
| 10 | Particle/Granular | `ParticleEngine` (index 18) or `GrainEngine` (index 11) |
| 11 | Swarm/Super | `SwarmEngine` (index 16) |
| 12 | String/KS | `StringEngine` (index 19) or `StringMachineEngine` (index 6) |
| 13 | Chiptune/8-bit | `ChiptuneEngine` (index 7) |

**Note:** The MiniFreak likely consolidated the 3 SixOpEngine slots into one selectable FM type, and removed the 3 percussion engines (BassDrum, SnareDrum, HiHat). The "13 oscillator types" may also include some combination of WaveTerrain and Modal.

---

## 6. Binary Search Patterns — Unique Constants for Firmware Identification

### 6.1 Float Constants (searchable as 32-bit IEEE 754)

| Constant | Float Value | Hex (little-endian bytes) | Engine(s) |
|----------|-------------|---------------------------|-----------|
| `kCorrectedSampleRate` | 47872.34f | `0x1F7B5B2A` → bytes `2A 5B 7B 1F` | Global |
| `kMaxFrequency` | 0.25f | `0x3E800000` → bytes `00 00 80 3E` | All oscillators |
| `kVariableSawNotchDepth` | 0.2f | `0x3E4CCCCD` → bytes `CD CC 4C 3E` | VariableSawOscillator |
| `kap` (diffuser) | 0.625f | `0x3F200000` → bytes `00 00 20 3F` | ParticleEngine/Diffuser |
| `klp` (diffuser) | 0.75f | `0x3F400000` → bytes `00 00 40 3F` | ParticleEngine/Diffuser |
| Fast2Sin `0.96f` | 0.96f | `0x3F75C28F` → bytes `8F C2 75 3F` | FastSineOscillator |
| `kLPCSpeechSynthFPS` | 40.0f | `0x42200000` → bytes `00 00 20 42` | SpeechEngine |

### 6.2 Integer Constants

| Constant | Value | Engine(s) |
|----------|-------|-----------|
| `kMaxBlockSize` | 24 | Voice (buffer sizing) |
| `kBlockSize` | 12 | Voice (render block) |
| `kMaxEngines` | 24 | EngineRegistry |
| `kNumHarmonics` | 36 | AdditiveEngine |
| `kHarmonicBatchSize` | 12 | AdditiveEngine |
| `kNumSwarmVoices` | 8 | SwarmEngine |
| `kNumStrings` | 3 | StringEngine |
| `kMaxNumModes` | 24 | ModalEngine/Resonator |
| `kModeBatchSize` | 4 | ModalEngine/Resonator |
| `kNumParticles` | 6 | ParticleEngine |
| `kNumSixOpVoices` | 2 | SixOpEngine |
| `kChordNumNotes` | 4 | ChordBank |
| `kChordNumVoices` | 5 | ChordBank |
| `kChordNumChords` | 17 (or 11) | ChordBank |
| `kSAMNumPhonemes` | 17 | SAMSpeechSynth |
| `kLPCSpeechSynthNumPhonemes` | 15 | LPCSpeechSynth |
| `kSineLUTBits` | 9 | SineOscillator |
| `LUT_SINE_SIZE` | 641 | resources.h |
| `LUT_FOLD_SIZE` | 516 | WaveshapingEngine |
| `LUT_FM_FREQUENCY_QUANTIZER_SIZE` | 130 | FMEngine |
| `LUT_STIFFNESS_SIZE` | 65 | StringVoice |
| `LUT_SVF_SHIFT_SIZE` | 257 | Resonator |
| `LUT_LPC_EXCITATION_PULSE_SIZE` | 640 | SpeechEngine |
| `WAV_INTEGRATED_WAVES_SIZE` | 25344 | WavetableEngine |
| `VA_VARIANT` | 2 | VirtualAnalogEngine |
| `SYX_BANK_SIZE` | 4096 | SixOpEngine (×3 banks) |

### 6.3 Post-Processing Gain Values (unique per engine)

These floats are written into `post_processing_settings` during `Voice::Init()` and are highly distinctive:

| Gain Value | Engine(s) |
|------------|-----------|
| -3.0f (out) / 1.0f (aux) | SwarmEngine |
| -2.0f (out) / 1.0f (aux) | ParticleEngine |
| -1.0f (out) / -1.0f (aux) | NoiseEngine |
| -1.0f (out) / 0.8f (aux) | StringEngine, ModalEngine |
| -0.7f (out) / 0.8f (aux) | SpeechEngine |
| 0.5f (out) / 0.5f (aux) | ChiptuneEngine |
| 0.6f (out) / 0.6f (aux) | FMEngine, WavetableEngine |
| 0.7f (out) / 0.6f (aux) | WaveshapingEngine |
| 0.7f (out) / 0.7f (aux) | PhaseDistortionEngine, WaveTerrainEngine |
| 0.8f (out) / 0.8f (aux) | VirtualAnalogEngine, AdditiveEngine, ChordEngine, StringMachineEngine, BassDrum, SnareDrum, HiHat |
| 1.0f (out) / 1.0f (aux) | VirtualAnalogVCFEngine, SixOpEngine (×3) |

### 6.4 Diffuser Delay Line Sizes (ParticleEngine unique fingerprint)

The sequence `{126, 180, 269, 444, 1653, 2010, 3411}` appearing together is a unique fingerprint for the ParticleEngine's Diffuser.

---

## 7. Render() Function Signature — All Engines Identical

Every engine implements the exact same virtual method:

```c++
virtual void Render(
    const EngineParameters& parameters,  // 24 bytes: trigger, note, timbre, morph, harmonics, accent
    float* out,                          // Main output buffer (kBlockSize or kMaxBlockSize samples)
    float* aux,                          // Aux output buffer (same size)
    size_t size,                         // Number of samples (typically 12)
    bool* already_enveloped              // [in/out] engine reports if it handles its own envelope
) = 0;
```

The `already_enveloped` parameter is both input (from `post_processing_settings.already_enveloped`) and output (engine can change it per-call — notably SpeechEngine toggles this between vowel and word modes).

---

## 8. Voice Class Memory Layout

From `dsp/voice.h`, the Voice class contains engine instances **by value** in this order:

```
Offset   Member
------   ------
0x0000   vptr (Voice vtable)
0x0004   VirtualAnalogVCFEngine virtual_analog_vcf_engine_
0x????   PhaseDistortionEngine phase_distortion_engine_
0x????   SixOpEngine six_op_engine_ (3 instances share same engine slot)
0x????   WaveTerrainEngine wave_terrain_engine_
0x????   StringMachineEngine string_machine_engine_
0x????   ChiptuneEngine chiptune_engine_
0x????   VirtualAnalogEngine virtual_analog_engine_
0x????   WaveshapingEngine waveshaping_engine_
0x????   FMEngine fm_engine_
0x????   GrainEngine grain_engine_
0x????   AdditiveEngine additive_engine_
0x????   WavetableEngine wavetable_engine_
0x????   ChordEngine chord_engine_
0x????   SpeechEngine speech_engine_
0x????   SwarmEngine swarm_engine_
0x????   NoiseEngine noise_engine_
0x????   ParticleEngine particle_engine_
0x????   StringEngine string_engine_
0x????   ModalEngine modal_engine_
0x????   BassDrumEngine bass_drum_engine_
0x????   SnareDrumEngine snare_drum_engine_
0x????   HiHatEngine hi_hat_engine_
```

**Note:** The MiniFreak likely removes some engines (drums) and may reorder/reduce the list. The `EngineRegistry<kMaxEngines>` (max 24) stores pointers to the engine instances in registration order.

---

## 9. Key Findings for Binary Matching

### Most Distinctive Engine Fingerprints

1. **SixOpEngine** — Only engine with `fm::Algorithms<6>`, `fm::Voice<6>`, `fm::Lfo`, `fm::Patch*`. The 6-operator FM architecture is unique. Registered 3 times (indices 2-4).

2. **ChiptuneEngine** — Only engine using `SuperSquareOscillator` and `NESTriangleOscillator`. Contains `Arpeggiator` with 5-mode enum.

3. **SpeechEngine** — Only engine with both `SAMSpeechSynth` and `LPCSpeechSynthController`. The `word_bank_quantizer_` is unique.

4. **WaveTerrainEngine** — Only engine with `user_terrain_` pointer (int8_t*). Unique `LoadUserData` casts to `(const int8_t*)`.

5. **ParticleEngine** — Only engine with `Diffuser` (7 delay lines with specific sizes). Combined with `kNumParticles = 6`.

6. **SwarmEngine** — Only engine with 8 dynamically allocated `SwarmVoice` (grain envelope + additive saw + fast sine). `kNumSwarmVoices = 8`.

7. **StringMachineEngine** — Only engine with `Ensemble` (chorus) effect. Uses `NaiveSvf` (different from regular `Svf`).

### Shared Subsystem Signatures

| Subsystem | Used By | Unique Constant |
|-----------|---------|-----------------|
| `VariableShapeOscillator` | VA, VCF, PD, Chiptune | master/slave phase, polyBLEP |
| `VariableSawOscillator` | VA | `kVariableSawNotchDepth = 0.2f` |
| `GrainletOscillator` | Grain | carrier/formant dual phase |
| `ZOscillator` | Grain | discontinuity_phase, 3-mode Z function |
| `HarmonicOscillator<12>` | Additive | Chebyshev, `two_x = 2.0 * SineNoWrap(phase)` |
| `StringSynthOscillator` | Chord, StringMachine | 4-bandlimited sawtooths, 7 registration gains |
| `WavetableOscillator<128,15>` | Chord, Wavetable | `Differentiator`, integrated wave interpolation |
| `FormantOscillator` | (speech subsystems) | carrier→formant phase sync with BLEP |
| `ClockedNoise` | Noise | sample-and-hold noise with BLEP transitions |
| `Resonator` (24 modes) | Modal | `kMaxNumModes=24`, `kModeBatchSize=4` |
| `String` (Karplus-Strong) | String | delay line + stiffness LUT |
| `Diffuser` | Particle | 7 delay lines: 126+180+269+444+1653+2010+3411 |

---

## 10. Notes on MiniFreak Adaptation

The MiniFreak firmware likely differs from stock Plaits in these ways:

1. **Sample rate may differ** — MiniFreak's internal DSP rate needs verification. If not 48kHz (or 47872.34 Hz corrected), the `a0` tuning constant and all frequency calculations would change.

2. **Engine subset** — 13 oscillator types suggests removal of some engines. Most likely removed: BassDrum, SnareDrum, HiHat (3 percussion engines), and possibly consolidation of the 3 SixOpEngine slots into 1.

3. **Additional parameters** — MiniFreak has more synthesis parameters (spread, sub mix, etc.) than stock Plaits. The `EngineParameters` struct may have been extended with `harmonics` and `accent` fields used differently.

4. **Post-processing** — The MiniFreak's signal chain (filter, effects, pan) wraps around the Plaits engine output differently than the original module.

5. **Memory layout** — The Voice class member order and engine registry contents may be rearranged for the MiniFreak's dual-timbral architecture.
