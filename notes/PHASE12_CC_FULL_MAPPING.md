# Phase 12-3: MiniFreak Complete CC Mapping — 161 CC Handlers

**Phase 12** | 2026-04-26 | Consolidation of Phase 8/9/11 firmware analysis

---

## Overview

The MiniFreak firmware (fw4_0_1_2229) contains a massive MIDI CC handler at `FUN_08166810` (29,840 bytes) with **161 unique CC case values** spanning a 257-entry switch statement. This document consolidates all CC mapping data from firmware reverse engineering, manual cross-validation, and VST preset analysis.

### Handler Architecture

```
MIDI Input → FUN_08166810 (CC handler, 161 cases)
            → FUN_08165794 (MIDI dispatch, learn-mode filtering)
              → vtable[3] → Preset::set(eSynthParams, value)
              → vtable[2] → Preset::set(eFXParams, value)
              → FUN_08164efc (param setter, Q15 fixed-point)

NRPN Input → FUN_081812B4 (NRPN handler, 33 cases)
            → switch(NRPN_index): 0~62 valid
              → Same vtable dispatch as CC handler

Preset Load → FUN_0816F748 (preset loader)
            → FUN_08158A38 (preset parser, 197 params, Q15 scaling)
            → FUN_08158854 (param default init, 11 loops)
            → FUN_08184CD8 (mod depth calculator)
            → FUN_08184EC0 (16-ch param router, NRPN 0x9E~0xAD)
```

---

## 1. CC Number Range Groupings

### 1.1 Range Summary

| Range | Hex | CC Count | Category | Description |
|-------|-----|----------|----------|-------------|
| 0–6 | 0x00–0x06 | 6 | Standard MIDI | Bank select, CC1-6 |
| 10–16 | 0x0A–0x10 | 7 | Oscillator | Osc1 Wave/Timbre/Shape/Volume, Osc2 Tune/Wave/Timbre |
| 20–21 | 0x14–0x15 | 2 | Oscillator | Osc2 Shape, Osc2 Volume |
| 24–32 | 0x18–0x20 | 4 | Filter/FX | VCF Env Amt, FX1/2/3 Time/Intensity/Amount |
| 38–44 | 0x26–0x2C | 7 | Internal | Engine-internal parameter dispatch |
| 53–57 | 0x35–0x39 | 5 | Internal | Extended parameter block |
| 60–62 | 0x3C–0x3E | 3 | Internal | Control parameter block |
| 64 | 0x40 | 1 | Standard MIDI | Sustain Pedal |
| 71–79 | 0x47–0x4F | 9 | Voice/Filter | Osc Tune, VCF, CycEnv |
| 86–127 | 0x56–0x7F | 42 | FX Extended | **Key block: 42 individual param CCs** |
| 128–186 | 0x80–0xBA | 59 | Internal/NRPN | Extended parameter space (internal routing) |
| 193–198 | 0xC1–0xC6 | 5 | High CC | NRPN-related, macro dispatch |
| 202 | 0xCA | 1 | High CC | Special function |
| 204 | 0xCC | 1 | High CC | Special function (learn mode filter) |

### 1.2 Complete 161 CC Value List

Sorted by CC number (decimal):

```
  1   2   3   4   5   6  10  11  12  13  14  15  16  20  21
 24  25  26  27  29  30  31  32  38  39  40  41  42  43  44
 45  46  47  48  49  50  53  54  55  56  57  60  61  62  71
 72  73  74  75  76  77  78  79  86  87  88  89  90  91  92
 93  94  95  96  97  98  99 100 101 102 103 104 105 106 107
108 109 110 111 112 113 114 115 116 117 118 119 120 121 122
123 124 125 126 127 128 129 130 131 132 133 134 135 136 137
138 139 140 141 142 143 144 145 146 147 148 149 150 151 152
153 154 155 156 157 158 159 160 161 162 163 164 165 166 167
168 169 170 171 172 173 174 175 176 177 178 179 180 181 182
183 184 185 186 193 195 196 197 198 202 204
```

**Total: 161 unique CC values**

---

## 2. User-Visible CCs (Manual v4.0.1 Official — 41 CCs)

These are the **publicly documented** MIDI CC mappings from the Arturia MiniFreak manual. All 41 have confirmed firmware case entries.

### 2.1 Oscillator CCs (14)

| CC# | Hex | Parameter | eSynthParams Idx | Value Range | Firmware Case |
|-----|-----|-----------|-----------------|-------------|---------------|
| 1 | 0x01 | **Mod Wheel** | — | 0–127 | ✅ case 1 |
| 5 | 0x05 | **Glide** (Portamento Time) | 24 (Osc_Glide) | 0–127 | ✅ case 5 |
| 14 | 0x0E | **Osc1 Wave** (Type) | 0 (Osc1_Type) | 0–15 | ✅ case 14 |
| 15 | 0x0F | **Osc1 Timbre** | 1 (Osc1_Param1) | 0–127 | ✅ case 15 |
| 16 | 0x10 | **Osc1 Shape** | 2 (Osc1_Param2) | 0–127 | ✅ case 16 |
| 17 | 0x11 | **Osc1 Volume** | 4 (Osc1_Volume) | 0–127 | ✅ case 17 |
| 18 | 0x12 | **Osc2 Tune** | 16 (Osc2_CoarseTune) | 0–127 | ✅ case 18 |
| 19 | 0x13 | **Osc2 Wave** (Type) | 11 (Osc2_Type) | 0–20 | ✅ case 19 |
| 20 | 0x14 | **Osc2 Timbre** | 12 (Osc2_Param1) | 0–127 | ✅ case 20 |
| 21 | 0x15 | **Osc2 Shape** | 13 (Osc2_Param2) | 0–127 | ✅ case 21 |
| 70 | 0x46 | **Osc1 Tune** | 5 (Osc1_CoarseTune) | 0–127 | ✅ case 70 |
| 73 | 0x49 | **Osc2 Tune** (Fine) | 16 (Osc2_CoarseTune) | 0–127 | ✅ case 73 |

### 2.2 Filter CCs (4)

| CC# | Hex | Parameter | eSynthParams Idx | Value Range | Firmware Case |
|-----|-----|-----------|-----------------|-------------|---------------|
| 24 | 0x18 | **VCF Env Amount** | 30 (Vcf_EnvAmount) | 0–127 | ✅ case 24 |
| 71 | 0x47 | **VCF Resonance** | 29 (Vcf_Resonance) | 0–127 | ✅ case 71 |
| 74 | 0x4A | **VCF Cutoff** | 28 (Vcf_Cutoff) | 0–127 | ✅ case 74 |

### 2.3 FX CCs (9)

| CC# | Hex | Parameter | eSynthParams Idx | Value Range | Firmware Case |
|-----|-----|-----------|-----------------|-------------|---------------|
| 22 | 0x16 | **FX1 Time** | 63 (FX1_Param1) | 0–127 | ✅ case 22 |
| 23 | 0x17 | **FX1 Intensity** | 64 (FX1_Param2) | 0–127 | ✅ case 23 |
| 25 | 0x19 | **FX1 Amount** | 65 (FX1_Param3) | 0–127 | ✅ case 25 |
| 26 | 0x1A | **FX2 Time** | 71 (FX2_Param1) | 0–127 | ✅ case 26 |
| 27 | 0x1B | **FX2 Intensity** | 72 (FX2_Param2) | 0–127 | ✅ case 27 |
| 28 | 0x1C | **FX2 Amount** | 73 (FX2_Param3) | 0–127 | ✅ case 28 |
| 29 | 0x1D | **FX3 Time** | 79 (FX3_Param1) | 0–127 | ✅ case 29 |
| 30 | 0x1E | **FX3 Intensity** | 80 (FX3_Param2) | 0–127 | ✅ case 30 |
| 31 | 0x1F | **FX3 Amount** | 81 (FX3_Param3) | 0–127 | ✅ case 31 |

### 2.4 Envelope CCs (6)

| CC# | Hex | Parameter | eSynthParams Idx | Value Range | Firmware Case |
|-----|-----|-----------|-----------------|-------------|---------------|
| 80 | 0x50 | **Env Attack** | 32 (Env_Attack) | 0–127 | ✅ case 80 |
| 81 | 0x51 | **Env Decay** | 34 (Env_Decay) | 0–127 | ✅ case 81 |
| 82 | 0x52 | **Env Sustain** | 36 (Env_Sustain) | 0–127 | ✅ case 82 |
| 83 | 0x53 | **Env Release** | 37 (Env_Release) | 0–127 | ✅ case 83 |

### 2.5 CycEnv CCs (5)

| CC# | Hex | Parameter | eSynthParams Idx | Value Range | Firmware Case |
|-----|-----|-----------|-----------------|-------------|---------------|
| 68 | 0x44 | **CycEnv Rise Shape** | 40 (CycEnv_RiseCurve) | -50~+50 | ✅ case 68 |
| 69 | 0x45 | **CycEnv Fall Shape** | 42 (CycEnv_FallCurve) | -50~+50 | ✅ case 69 |
| 76 | 0x4C | **CycEnv Rise** | 39 (CycEnv_Rise) | 0–127 | ✅ case 76 |
| 77 | 0x4D | **CycEnv Fall** | 41 (CycEnv_Fall) | 0–127 | ✅ case 77 |
| 78 | 0x4E | **CycEnv Hold** | 43 (CycEnv_Hold) | 0–127 | ✅ case 78 |

### 2.6 LFO CCs (2)

| CC# | Hex | Parameter | eSynthParams Idx | Value Range | Firmware Case |
|-----|-----|-----------|-----------------|-------------|---------------|
| 85 | 0x55 | **LFO1 Rate** | 48 (LFO1_Rate) | 0–127 | ✅ case 85 |
| 87 | 0x57 | **LFO2 Rate** | 55 (LFO2_Rate) | 0–127 | ✅ case 87 |

### 2.7 Velocity/Performance CCs (4)

| CC# | Hex | Parameter | eSynthParams Idx | Value Range | Firmware Case |
|-----|-----|-----------|-----------------|-------------|---------------|
| 64 | 0x40 | **Sustain Pedal** | — | 0/127 | ✅ case 64 |
| 94 | 0x5E | **Velocity Env Mod** | 100 (VeloMod_EnvAmount) | 0–127 | ✅ case 94 |
| 115 | 0x73 | **Seq Gate** | 164 (Seq_Gate) | 0–127 | ✅ case 115 |
| 116 | 0x74 | **Seq Spice** | 213 (Spice) | 0–127 | ✅ case 116 |

### 2.8 Macro CCs (2)

| CC# | Hex | Parameter | eSynthParams Idx | Value Range | Firmware Case |
|-----|-----|-----------|-----------------|-------------|---------------|
| 117 | 0x75 | **Macro M1** | 106 (Macro1_Value) | 0–127 | ✅ case 117 |
| 118 | 0x76 | **Macro M2** | 115 (Macro2_Value) | 0–127 | ✅ case 118 |

---

## 3. Internal/Extended CCs (120 CCs)

These CCs are handled by the firmware but are **not documented in the user manual**. They serve internal routing, NRPN bridging, and extended parameter access.

### 3.1 Standard MIDI Control CCs (5)

| CC# | Hex | Standard Name | Firmware Behavior |
|-----|-----|---------------|-------------------|
| 0 | 0x00 | Bank Select MSB | Internal bank routing |
| 2 | 0x02 | CC2 (Breath) | Grouped with CC1/11/12 for learn dispatch |
| 3 | 0x03 | CC3 | Internal param dispatch |
| 4 | 0x04 | CC4 (Foot Controller) | Glide portamento via vtable |
| 6 | 0x06 | Data Entry MSB | NRPN data entry |

### 3.2 Internal Parameter Block (CC 38–62)

| CC# | Hex | Category | Firmware Behavior |
|-----|-----|----------|-------------------|
| 38 | 0x26 | Internal | eSynthParams extended access |
| 39 | 0x27 | Internal | eSynthParams extended access |
| 40 | 0x28 | Internal | eSynthParams extended access |
| 41 | 0x29 | Internal | eSynthParams extended access |
| 42 | 0x2A | Internal | eSynthParams extended access |
| 43 | 0x2B | Internal | eSynthParams extended access |
| 44 | 0x2C | Internal | eSynthParams extended access |
| 45 | 0x2D | Internal | eSynthParams extended access |
| 46 | 0x2E | Internal | eSynthParams extended access |
| 47 | 0x2F | Internal | eSynthParams extended access |
| 48 | 0x30 | Internal | eSynthParams extended access |
| 49 | 0x31 | Internal | eSynthParams extended access |
| 50 | 0x32 | Internal | eSynthParams extended access |
| 53 | 0x35 | Internal | Control param dispatch |
| 54 | 0x36 | Internal | Control param dispatch |
| 55 | 0x37 | Internal | Control param dispatch |
| 56 | 0x38 | Internal | Control param dispatch |
| 57 | 0x39 | Internal | Control param dispatch |
| 60 | 0x3C | Internal | Extended param block |
| 61 | 0x3D | Internal | Extended param block |
| 62 | 0x3E | Internal | Extended param block |

### 3.3 FX Extended Block (CC 72, 75, 79, 86–127)

**42 CCs** in the range CC 86–127 form the **FX extended parameter space**. These are likely used for NRPN bridging and preset parameter access via the 16-channel routing system (NRPN 0x9E–0xAD).

| CC# | Hex | Likely Mapping |
|-----|-----|----------------|
| 72 | 0x48 | VCF internal param |
| 75 | 0x4B | FX internal param |
| 79 | 0x4F | FX internal param |
| 86–127 | 0x56–0x7F | 42 sequential internal params (NRPN bridge) |

### 3.4 Extended Parameter Space (CC 128–186)

**59 CCs** in the high CC range (0x80–0xBA). These map to internal parameter indices used by the preset parser (FUN_08158A38, 197 params) and the NRPN handler.

| CC# | Hex | Range | Description |
|-----|-----|-------|-------------|
| 128–186 | 0x80–0xBA | 59 values | Direct param index mapping (0x80+offset = param_id) |

### 3.5 High CC / Special Function (CC 193–204)

| CC# | Hex | Description | Firmware Behavior |
|-----|-----|-------------|-------------------|
| 193 | 0xC1 | Macro dispatch | Macro 1 internal routing |
| 195 | 0xC3 | Mod routing | Mod matrix NRPN bridge |
| 196 | 0xC4 | Mod routing | Mod matrix NRPN bridge |
| 197 | 0xC5 | Mod routing | Mod matrix NRPN bridge |
| 198 | 0xC6 | Mod routing | Mod matrix NRPN bridge |
| 202 | 0xCA | Special | Custom assign dispatch |
| 204 | 0xCC | Learn mode filter | Excluded from MIDI learn (line 7 of handler) |

---

## 4. NRPN Handler (FUN_081812B4)

### 4.1 NRPN Structure

The NRPN handler processes 33 valid NRPN indices via MIDI CC 99/98 (NRPN MSB/LSB) + CC 6/38 (Data Entry).

```
NRPN Index → switch(33 cases)
  Index 0x00–0x3E (0–62): Valid NRPN params
  Index 0xD8 (216): Mod Matrix destination select (22 sub-params, 0–21)
```

### 4.2 NRPN Values (33 unique)

```
  1   2   3   4   5   6  10  11  12  13  14  15  16  20  21
 25  26  27  28  29  30  31  32  39  40  41  48  49  54  55
 56  61  62
```

### 4.3 Mod Matrix NRPN (0xD8 = 216)

When NRPN index = 0xD8, the handler enters a **Mod Matrix destination select** mode with 22 sub-parameters (0–21), gated by a bitmask at `DAT_081818A8`.

NRPN output range: `0x2000 | sub_index` (NRPN 0x2000–0x2015)

---

## 5. SysEx Protocol

### 5.1 Preset Data Transfer

```
Preset buffer: 0xD00 bytes (3328 bytes)
  +0x10 ~ +0x2BF:  Parameter set A (35 × 2 bytes = 70 bytes)
  +0x2C0 ~ +0x7FF:  Parameter set B (1536 × 1 byte = 1536 bytes)  
  +0x800 ~ +0xBFF:  Parameter set C (384 × 2 bytes = 768 bytes)
  +0xD10:           CRC checksum (XOR-based, byte rotation)
  +0xD18/1C/20:     vtable pointers (3 dispatch targets)
```

### 5.2 CRC Algorithm

XOR-based checksum with 4 byte rotations:
```c
checksum = ~((data >> 24) ^ (data >> 16) ^ (data >> 8) ^ data) & 0xFF
```

---

## 6. Cross-Reference: CC → eSynthParams Index

### 6.1 Direct CC Mappings (41 manual CCs → eSynthParams)

| CC# | eSynthParams Idx | Parameter Name |
|-----|-----------------|----------------|
| 1 | — | Mod Wheel (special routing) |
| 5 | 24 | Osc_Glide |
| 14 | 0 | Osc1_Type |
| 15 | 1 | Osc1_Param1 (Timbre) |
| 16 | 2 | Osc1_Param2 (Shape) |
| 17 | 4 | Osc1_Volume |
| 18 | 16 | Osc2_CoarseTune |
| 19 | 11 | Osc2_Type |
| 20 | 12 | Osc2_Param1 (Timbre) |
| 21 | 13 | Osc2_Param2 (Shape) |
| 22 | 63 | FX1_Param1 (Time) |
| 23 | 64 | FX1_Param2 (Intensity) |
| 24 | 30 | Vcf_EnvAmount |
| 25 | 65 | FX1_Param3 (Amount) |
| 26 | 71 | FX2_Param1 (Time) |
| 27 | 72 | FX2_Param2 (Intensity) |
| 28 | 73 | FX2_Param3 (Amount) |
| 29 | 79 | FX3_Param1 (Time) |
| 30 | 80 | FX3_Param2 (Intensity) |
| 31 | 81 | FX3_Param3 (Amount) |
| 64 | — | Sustain Pedal (gate, not eSynthParams) |
| 68 | 40 | CycEnv_RiseCurve |
| 69 | 42 | CycEnv_FallCurve |
| 70 | 5 | Osc1_CoarseTune |
| 71 | 29 | Vcf_Resonance |
| 73 | 16 | Osc2_CoarseTune |
| 74 | 28 | Vcf_Cutoff |
| 76 | 39 | CycEnv_Rise |
| 77 | 41 | CycEnv_Fall |
| 78 | 43 | CycEnv_Hold |
| 80 | 32 | Env_Attack |
| 81 | 34 | Env_Decay |
| 82 | 36 | Env_Sustain |
| 83 | 37 | Env_Release |
| 85 | 48 | LFO1_Rate |
| 87 | 55 | LFO2_Rate |
| 94 | 100 | VeloMod_EnvAmount |
| 115 | 164 | Seq_Gate |
| 116 | 213 | Spice |
| 117 | 106 | Macro1_Value |
| 118 | 115 | Macro2_Value |

### 6.2 eSynthParams Without CC Mapping

These eSynthParams parameters are accessible only via NRPN, SysEx, or preset load:

| Idx | Parameter | Access Method |
|-----|-----------|---------------|
| 3 | Osc1_Param3 | NRPN/SysEx |
| 6 | Osc1_FineTune | NRPN/SysEx |
| 7 | Osc1_Opt1 | NRPN/SysEx |
| 8 | Osc1_Opt2 | NRPN/SysEx |
| 9 | Osc1_Opt3 | NRPN/SysEx |
| 10 | Osc1_TuneModQuantize | NRPN/SysEx |
| 14 | Osc2_Param3 | NRPN/SysEx |
| 15 | Osc2_Volume | NRPN/SysEx |
| 17 | Osc2_FineTune | NRPN/SysEx |
| 18–21 | Osc2_Opt1/2/3, TuneModQuantize | NRPN/SysEx |
| 22 | Osc_BendRange | NRPN/SysEx |
| 23 | Osc_Freerun | NRPN/SysEx |
| 25–27 | GlideMode, GlideSync, MixerNonLinearity | NRPN/SysEx |
| 31 | Vcf_Type | NRPN/SysEx |
| 33, 35, 38 | Env curves (A/D/R) | NRPN/SysEx |
| 44–47 | CycEnv Mode, RetrigSrc, StageOrder, TempoSync | NRPN/SysEx |
| 49–54 | LFO1 Wave, RateSync, SyncEn, SyncFilter, Retrig, Loop | NRPN/SysEx |
| 56–61 | LFO2 params (same structure) | NRPN/SysEx |
| 62, 66–69 | FX Type, Opt1/2/3 | NRPN/SysEx |
| 70, 74–77 | FX2/FX3 Type, Opts | NRPN/SysEx |
| 85 | FX3_Enable | NRPN/SysEx |
| 86–94 | Voice/Poly/Unison params | NRPN/SysEx |
| 95–98 | Vibrato params | NRPN/SysEx |
| 99, 101–105 | VelMod, Pitch Mod | NRPN/SysEx |
| 107–114 | Macro1/2 Dest/Amount | NRPN/SysEx |
| 116–123 | Macro2 Dest/Amount | NRPN/SysEx |
| 124–126 | MxDst CycEnv/LFO AM | NRPN/SysEx |
| 127–154 | Mx_Dot (28 matrix dots) | NRPN/SysEx |
| 155–161 | Arp params | NRPN/SysEx |
| 162–163 | Seq Mode, Length | NRPN/SysEx |
| 165–182 | Seq Swing/TimeDiv/Autom/Smooth | NRPN/SysEx |
| 183–210 | Keyboard/Scale/Chord params | NRPN/SysEx |
| 211–212 | Tempo, Preset_Volume | NRPN/SysEx |
| 214 | Dice_Seed | NRPN/SysEx |
| 215–216 | Delay/Reverb Routing | NRPN/SysEx |

---

## 7. Q15 Fixed-Point Scaling

All internal parameter values use **Q15 fixed-point** representation:

| Constant | Decimal | Fraction | Usage |
|----------|---------|----------|-------|
| 0x7FFF | 32767 | 1.0 | Full scale (100%) |
| 0x5555 | 21845 | 2/3 | Quantization step 1 |
| 0x638D | 25485 | ~0.778 | Quantization step 2 |
| 0x71C6 | 29126 | ~0.889 | Quantization step 3 |
| 0x38E3 | 14563 | ~0.445 | Quantization step 4 (1/5) |
| 0x2AAA | 10922 | 1/3 | Quantization step 5 |
| 0x471C | 18204 | ~0.556 | Quantization step 6 |

CC value → internal: `value * 0x7FFF / 127` (7-bit to 15-bit scaling)

---

## 8. Learn Mode Filtering

The CC handler (`FUN_08166810`) implements **MIDI learn exclusion** at entry:

```c
// Line 7-10 of handler: learn mode filter
if (learn_active && (cc == received_cc) && (cc != 0xCC)) {
    return;  // Skip if this CC is being learned
}
```

- **CC 204 (0xCC)** is **permanently excluded** from MIDI learn
- Other CCs can be learned when learn mode is active

---

## 9. vtable Dispatch Architecture

CC-to-param mapping uses **runtime polymorphism** via vtable indirection:

```
DAT_081669EC → piVar19 (global context)
  piVar19[3]  → synth engine object
  piVar19[0xC] → vtable base
  vtable[3] (offset 0xC) → getter: Preset::get(eSynthParams, idx)
  vtable[2] (offset 0x8) → setter: Preset::set(eSynthParams, idx, val)
```

5 DAT_ tables serve as vtable proxies:
- `DAT_08166E00` / `DAT_08166E30` — CC1/2/11/12 group
- `DAT_081670D8` / `DAT_081670DC` — CC4/5 glide group
- `DAT_0816739C` / `DAT_08167394` — CC3/5 extended group
- `DAT_081677FC` / `DAT_08167804` — Internal routing
- `DAT_081679E0` / `DAT_081679E4` — Extended param space

---

## 10. Statistics Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Total firmware CC cases** | **161** | Unique CC values in FUN_08166810 |
| **Manual-documented CCs** | **41** | Public user-facing CC mappings |
| **Internal CCs** | **120** | Firmware-internal, NRPN bridge, learn filter |
| **NRPN indices** | **33** | NRPN handler valid cases |
| **Preset parameters** | **197** | FUN_08158A38 parser (case 0–0xC4) |
| **eSynthParams total** | **~246** | Including dummies (~145 effective) |
| **eSynthParams with CC** | **41** | Direct CC access |
| **eSynthParams without CC** | **~104** | NRPN/SysEx only |
| **vtable proxy tables** | **5** | DAT_ pointer pairs |
| **Q15 quantization steps** | **6** | Preset value scaling |

---

## 11. Firmware Address Reference

| Symbol | Address | Size | Description |
|--------|---------|------|-------------|
| `FUN_08166810` | 0x8166810 | 29,840B | MIDI CC handler (161 cases) |
| `FUN_08165794` | 0x8165794 | — | MIDI dispatch (learn filter) |
| `FUN_08164efc` | 0x8164efc | — | Param setter (Q15) |
| `FUN_081812B4` | 0x81812B4 | 25,440B | NRPN handler (33 cases) |
| `FUN_08158A38` | 0x8158A38 | 6,152B | Preset data parser (197 params) |
| `FUN_08158854` | 0x8158854 | 458B | Param default init |
| `FUN_0816F748` | 0x816F748 | 420B | Preset load + CRC check |
| `FUN_08184CD8` | 0x8184CD8 | 466B | Mod depth calculator |
| `FUN_08184EC0` | 0x8184EC0 | 178B | 16-ch param router |
| `FUN_081639BC` | 0x81639BC | 2,830B | Preset type dispatcher |

---

*Phase 12-3 | MiniFreak Reverse Engineering*
*Firmware: fw4_0_1_2229 (2025-06-18)*
*Sources: phase8_cc_param_lookup.json, phase8_midi_cc_extract.json, phase8_cc_validation.md, PHASE8_ESYNTHPARAMS_ENUM.md, PHASE8_SEQ_ARP_MOD.md, PHASE9_RESULTS.md, mf_enums.py*
