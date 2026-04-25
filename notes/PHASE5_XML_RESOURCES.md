# Phase 5: XML Resource Files Analysis - MiniFreak V Plugin

**Date:** 2026-04-24  
**Source:** MiniFreak V installer extracted resources  
**Instrument Version:** 4.0.2.6369  
**Copyright:** Arturia (c) 2025

---

## Executive Summary

Analyzed 10 XML/config files from the MiniFreak V plugin that define the **complete parameter space, modulation architecture, MIDI controller mappings, and hardware communication protocols**. These files form the bridge between the DAW plugin interface and the MiniFreak hardware synthesizer.

### Key Numbers
| Metric | Count |
|--------|-------|
| Internal parameters | **2,363** |
| VST-exposed parameters | **148** |
| Feedback parameters | **138** |
| Modulation destinations | **140** |
| Automation destinations | **42** |
| Oscillator 1 types (latest) | **24** |
| Oscillator 2 types (latest) | **30** |
| Effect types (latest) | **13** |
| Preset slots on hardware | **512** |
| Sequencer steps | **64** |
| LFO shaper steps | **16** |
| Voice polyphony | **12** |

---

## File Inventory

### 1. `minifreak_internal_params.xml` (362KB, 7171 lines, 2363 params)
The **master parameter registry**. Auto-generated, defines every parameter the engine knows about. Includes:
- Synthesis parameters (oscillators, filter, envelope, LFOs, effects)
- Sequencer step data (64 steps × 6 params each = 384 params)
- Modulation matrix (91 dot values + 63 assign dots)
- LFO Shaper data (2 LFOs × 16 steps × 4 params = 128 params)
- 63 favorite slots (range 0-511)
- Hardware communication commands (calibration, preset management, SIBP, NRPN)
- Calibration interface (9 commands)
- Memory/storage management
- 12 dummy/placeholder parameters

### 2. `minifreak_vst_params.xml` (34KB, 554 lines, 148 params)
Subset of internal params **exposed to DAW hosts**. All marked with `realtimemidi="1"`. Includes:
- Oscillator controls (coarse, type, wave/timbre/shape, volume)
- Filter (cutoff, resonance, env amount)
- Envelope ADSR
- Cycling envelope (rise/fall/hold)
- LFOs (wave, rate, rate synced)
- Modulation matrix dots and assign dots
- FX parameters (time, intensity, amount for 3 slots)
- Arpeggiator controls
- Macro controls

### 3. `minifreak_feedback_params.xml` (12.6KB, 160 lines, 138 params)
Mirror of VST params with `_Feedback` suffix. Used to **send current state back to hardware**. All have `notsetmodified="1"` and `transmittedtoprocessor="0"` — they're one-way UI→hardware mirrors.

### 4. `minifreak_fx_presets_params.xml` (13.7KB, 277 lines, 33 params)
Defines **FX preset sub-options** (Opt1/Opt2/Opt3) for each effect type:
- Chorus: Default, Lush, Dark, Shaded, Single
- Phaser: Default, Default Sync, Space, Space Sync, SnH, SnH Sync
- Stereo Delay: 12 variants (Digital, Stereo, Ping-Pong, Mono, Filtered × Sync variants)
- Reverb: Default, Long, Hall, Echoes, Room, Dark Room
- Multi Comp: OPP, Bass Ctrl, High Ctrl, All Up, Tighter
- EQ3: Default, Wide, Mid 1K
- Distortion: Classic, Soft Clip, Germanium, Dual Fold, Climb, Tape
- Flanger: Default, Default Sync, Silly, Silly Sync
- SuperUnison: Classic, Ravey, Soli, Slow, Slow Trig, Wide Trig, Mono Trig, Wavy
- Vocoder (Self/Ext): Clean, Vintage, Narrow, Gated

### 5. `minifreak_mod_dests.xml` (4.47KB, 163 lines, 140 items)
Complete list of **modulation matrix destinations**:
- 32 core synthesis destinations
- 91 mod slot routing points (Mod 1:1 through Mod 7:13)
- 15 FX modulation targets (Vib AM, Pitch, LFO AM, CycEnv AM, FX Time/Intensity/Amount × 3)

### 6. `minifreak_autom_dests.xml` (1.78KB, 66 lines, 42 items)
Subset of mod destinations available for **step sequencer automation**. Notably includes Mod Wheel and Pitch Wheel which aren't in mod dests.

### 7. `Reference_ParamNames.xml` (1MB, 13323 lines)
Human-readable display name mapping. Maps every internal param ID to its UI display string. Essential for building any user-facing interface.

### 8. `MiniFreak V.xml` (34KB, 751 lines)
**Main application configuration** that assembles all components:
- Processor: `minifreakvProcessor` (DSP engine library)
- References all sub-XML files via `<xmlfile_parameters>` includes
- Defines VST parameter ordering (critical — order cannot change after release)
- Internal parameters for UI state, oscilloscope, voice tracking
- Parametric EQ blocks (3 bands with shelf/peak parameters)
- Multiband compressor (3 bands with threshold/ratio controls)
- Sample management (wavetable and sample paths)
- 12 voice tracking blocks

### 9. `MiniFreak V_actions.xml` (6KB, 118 lines)
**Parameter routing and proxy definitions**:
- Wheel bindings (mod wheel → `VST3_CtrlModWheel`, pitch wheel → `VST3_PitchBend`)
- Discrete param swappers for FX type-dependent options
- Oscillator coarse/fine proxy params linking internal to GUI
- FX rate proxy params (combining free rate, synced rate, synced delay rate)
- Sample manager for wavetable/sample loading

### 10. `log.conf` (2.82KB, 81 lines)
Logging configuration with 50+ categories at 5 severity levels. **Critical categories for RE:**
- `usb`, `bulk`, `usb.update`, `usb.update.cmd`, `usb.update.upload` — firmware update
- `hwvst.comm.sync`, `hwvst.comm.param.in/out` — hardware parameter sync
- `collage.comm.usb`, `collage.comm.usb.ll` — USB low-level protocol
- `collage.protocol.resource/system/data/security` — high-level protocol

---

## Hardware Communication Protocol

### Serial Interface Bulk Protocol (SIBP)
Two parameters control bulk data transfer:
- **SIBP_In** — Enable/disable serial bulk data input
- **SIBP_Out** — Enable/disable serial bulk data output

This is the protocol used for transferring presets, samples, wavetables, and likely firmware updates between the plugin and hardware.

### NRPN Communication
- **NRPN_Out** — Toggle NRPN output to hardware
- The NRPN mapping (NRPN numbers → parameter IDs) is **NOT in XML files** — it's in compiled code

### Preset Management
- 512 preset slots (0-511)
- Operations: Load, Save, Erase, Copy, Paste, Browse, Init
- Granular copy/paste: individual sections (Osc1, Osc2, FX1-3, Seq, LFO curves)
- Swap operations: SwapOsc, Swap FX1/FX2, Swap FX2/FX3, Swap FX1/FX3

### Calibration Interface
9 calibration commands exposed:
1. Calib Analog
2. Resonance min
3. Resonance max
4. Calib Cutoff
5. VCA min
6. VCA max
7. VCA offset
8. VCA_Offset_Reset

### Storage
- Format filesystem command
- Memory usage queries (full partition, wavetable factory)
- Wavetable factory count (max 31)

---

## MIDI Controller Support

### Dedicated Hardware
- **MiniFreak** — `MiniFreak MIDI` device name, bidirectional MIDI, synth mode, substring matching

### Arturia Controllers
KeyLab, MiniLab mkII/3, MicroLab, KeyLab Essential/mk3, KeyLab mkII/mk3

### MIDI CC Assignments (KeyLab example)
| CC | Item ID |
|----|---------|
| 7  | 48 (Master) |
| 74 | 1 (Osc1 Wave?) |
| 71 | 2 (Osc1 Timbre?) |
| 76 | 3 (Osc1 Shape?) |
| 77 | 4 (Osc2 Volume?) |
| 93 | 9 |
| 18 | 5 |
| 19 | 6 |
| 16 | 7 |
| 17 | 8 |
| 91 | 10 |

---

## Parameter Normalization

All continuous parameters use **0.0–1.0 normalized values** internally:
- `defaultvalnorm` — default as normalized float
- `mapping-min` / `mapping-max` — mapped range for display
- `mapping` — mapping function (e.g., `Exp(6)`, `BipolarVariableCenterInvPow(2,0.5)`)
- `unit` — display unit (dB, Hz, cts, st)

Conversion formula: `display_value = mapping_function(normalized_value, mapping-min, mapping-max)`

---

## Firmware Version Feature Gates

| Version | New Features |
|---------|-------------|
| V0.0.0 | Base release: 15 Osc1 types, 21 Osc2 types, 10 FX types |
| V1.9.0 | Wavetable for Osc1, SuperUnison FX |
| V2.9.0 | 9 new Osc1 types (Sample, grains, Skan, Particle, etc.), Osc2 placeholder slots |
| V3.9.0 | Vocoder (Self + Ext) FX, extended Preset Volume to +16dB |

---

## Key Findings for Reverse Engineering

1. **No SysEx templates in XML** — SysEx message construction is in compiled code (`.vst3`/`.component` binaries)
2. **NRPN mappings in compiled code** — XML only has the on/off toggle
3. **SIBP protocol** — Bulk data protocol name confirmed, implementation in compiled code
4. **Parameter IDs are the key** — Every parameter has a unique string ID that serves as the cross-reference between XML definitions, MIDI messages, and the DSP engine
5. **512 preset slots** — Hardware preset memory layout: 512 slots × (preset data size)
6. **Calibration exposes analog circuit tuning** — 8 calibration commands map to specific analog components
7. **USB update categories in logging** — `usb.update.cmd`, `usb.update.upload` confirm firmware update capability
8. **Collage protocol** — Arturia's internal communication protocol has categories for resource, system, data, and security layers
9. **Feedback params are the sync mechanism** — 138 _Feedback params form the hardware→plugin state sync channel
10. **Sample format**: `.raw`, `.RAW`, `.raw12b`, `.RAW12B` — 12-bit raw samples supported

---

## Parameter ID Naming Convention

```
Category[_Subcategory]_Property[_Index]
```

Examples:
- `Osc1_Param1` → Oscillator 1, first parameter (Wave)
- `LFO1_RateSync` → LFO 1, rate when synced
- `Mx_Dot_0` → Modulation matrix, dot value 0
- `Mx_AssignDot_10` → Modulation matrix, assignable destination 10
- `Shp1_Step_En_5` → LFO Shaper 1, step 5, enable
- `Seq_Gate` → Sequencer, gate length
- `FX1_Param2` → FX slot 1, parameter 2 (Intensity)
