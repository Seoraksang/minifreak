# Phase 12-4: MiniFreak Mod Matrix Destination Full Map — 140+ Destinations

**Phase 12** | 2026-04-26 | Consolidation of Phase 8/9/11 firmware analysis

---

## Overview

The MiniFreak's modulation matrix is a **7×13 grid** (91 simultaneous routings) with **3 categories of destinations**: user-visible (13), Custom Assign (8), and internal (119+). This document catalogs all modulation destinations extracted from firmware analysis.

### Matrix Architecture

```
                  Col 1   Col 2   Col 3   Col 4  |  Col 5~7  Col 8~10  Col 11~13
Row 1: CycEnv       [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 2: LFO 1        [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 3: LFO 2        [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 4: Velo/AT      [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 5: Wheel        [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 6: Keyboard     [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
Row 7: Mod Seq      [ON]    [ON]    [ON]    [ON]   |  Assign    Assign     Assign
                   ────── Hardwired ────────  |  ── Assignable (3 page × 3) ──
```

**Total: 91 routing slots (7 sources × 13 destinations)**

---

## 1. Modulation Sources (7 Rows + Sub-Sources = 12 Effective)

### 1.1 Firmware Source Enum (9 entries @ `0x081B1BCC`)

| # | Source | Address | Description |
|---|--------|---------|-------------|
| 0 | **Keyboard** | 0x081B1BCC | Note value / Glide |
| 1 | **LFO** | 0x081B1BD8 | LFO1 + LFO2 combined |
| 2 | **Cycling Env** | 0x081B1BDC | RHF cycling envelope |
| 3 | **Env / Voice** | 0x081B1BE8 | ADSR + voice params |
| 4 | **Voice** | 0x081B1BF4 | Voice-specific modulation |
| 5 | **Envelope** | 0x081B1BFC | ADSR envelope output |
| 6 | **FX** | 0x081B1C08 | Effects modulation |
| 7 | **Sample Select** | 0x081B1C0C | V3+ sample selection |
| 8 | **Wavetable Select** | 0x081B1C1C | V3+ wavetable selection |

### 1.2 Manual Row Sources (7)

| Row | Source | Sub-Options | Configurable Via |
|-----|--------|-------------|-----------------|
| 1 | **Cycling Envelope** | — | Always active |
| 2 | **LFO 1** | Wave/Rate/Retrig per-row | Sound Edit > LFO 1 |
| 3 | **LFO 2** | Wave/Rate/Retrig per-row | Sound Edit > LFO 2 |
| 4 | **Velocity / Aftertouch** | Velocity / AT / Both | `Matrix Src VeloAT` @ 0x081AFA4C |
| 5 | **Wheel** | Mod Wheel / Touch Strip | Hardware config |
| 6 | **Keyboard** | 9 sub-modes (see below) | `Kbd Src` @ 0x081AFA5C |
| 7 | **Mod Seq** | 4 lane (Smooth Mod 1~4) | Sequencer page |

### 1.3 Keyboard Source Sub-Modes (9 @ `0x081B0E10`)

| Index | Mode | Description |
|-------|------|-------------|
| 0 | **m9** | Minor 9th chord voicing |
| 1 | **m11** | Minor 11th chord voicing |
| 2 | **69** | Six-nine chord voicing |
| 3 | **M9** | Major 9th chord voicing |
| 4 | **M7** | Major 7th chord voicing |
| 5 | **S Curve** | S-curve interpolation |
| 6 | **Random** | Random value per note |
| 7 | **Voices** | Number of active voices |
| 8 | **Poly Kbd** | Polyphonic keyboard tracking |

---

## 2. User-Visible Destinations (13 — Hardwired 4 + Assignable 9)

### 2.1 Hardwired Destinations (4 Columns)

These are **always connected** for every source row and cannot be changed:

| Column | Destination | eSynthParams | Description |
|:------:|-------------|-------------|-------------|
| 1 | **Osc 1+2 Pitch** | 5 (Osc1_CoarseTune), 16 (Osc2_CoarseTune) | Dual oscillator pitch |
| 2 | **Osc 1+2 Shape** | 2 (Osc1_Param2), 13 (Osc2_Param2) | Shape/wavetable position |
| 3 | **VCF Cutoff** | 28 (Vcf_Cutoff) | Filter cutoff frequency |
| 4 | **VCA** | ~37 (Env_Release) or internal VCA | Amplifier level |

### 2.2 Assignable Destinations (9 Columns = 3 Pages × 3)

| Page | Col | Name | eSynthParams/Custom Assign | Description |
|:----:|:---:|------|---------------------------|-------------|
| 1 | 5 | **Assign 1** | User-selectable | Page 1, Slot 1 |
| 1 | 6 | **Assign 2** | User-selectable | Page 1, Slot 2 |
| 1 | 7 | **Assign 3** | User-selectable | Page 1, Slot 3 |
| 2 | 8 | **Assign 4** | User-selectable | Page 2, Slot 1 |
| 2 | 9 | **Assign 5** | User-selectable | Page 2, Slot 2 |
| 2 | 10 | **Assign 6** | User-selectable | Page 2, Slot 3 |
| 3 | 11 | **Assign 7** | User-selectable | Page 3, Slot 1 |
| 3 | 12 | **Assign 8** | User-selectable | Page 3, Slot 2 |
| 3 | 13 | **Assign 9** | User-selectable | Page 3, Slot 3 |

### 2.3 Assignable Destination Pool (39 options)

The 9 assignable slots can be set to any of these 39 destinations (manual §8.5.5):

| # | Destination | Category | eSynthParams Idx |
|---|-------------|----------|-----------------|
| 1 | **Glide** | Osc | 24 |
| 2 | **Pitch 1** | Osc | 5 |
| 3 | **Pitch 2** | Osc | 16 |
| 4 | **Osc 1 Type** | Osc | 0 |
| 5 | **Osc 1 Wave** | Osc | — (sub-param) |
| 6 | **Osc 1 Timbre** | Osc | 1 |
| 7 | **Osc 1 Shape** | Osc | 2 |
| 8 | **Osc 1 Volume** | Osc | 4 |
| 9 | **Osc 2 Type** | Osc | 11 |
| 10 | **Osc 2 Wave** | Osc | — (sub-param) |
| 11 | **Osc 2 Timbre** | Osc | 12 |
| 12 | **Osc 2 Shape** | Osc | 13 |
| 13 | **Osc 2 Volume** | Osc | 15 |
| 14 | **Filter Cutoff** | VCF | 28 |
| 15 | **Filter Resonance** | VCF | 29 |
| 16 | **Filter Env Amt** | VCF | 30 |
| 17 | **VCA** | Env | — (internal) |
| 18 | **FX 1 Time** | FX | 63 |
| 19 | **FX 1 Intensity** | FX | 64 |
| 20 | **FX 1 Amount** | FX | 65 |
| 21 | **FX 2 Time** | FX | 71 |
| 22 | **FX 2 Intensity** | FX | 72 |
| 23 | **FX 2 Amount** | FX | 73 |
| 24 | **FX 3 Time** | FX | 79 |
| 25 | **FX 3 Intensity** | FX | 80 |
| 26 | **FX 3 Amount** | FX | 81 |
| 27 | **Env Attack** | Env | 32 |
| 28 | **Env Decay** | Env | 34 |
| 29 | **Env Sustain** | Env | 36 |
| 30 | **Env Release** | Env | 37 |
| 31 | **CycEnv Rise** | CycEnv | 39 |
| 32 | **CycEnv Fall** | CycEnv | 41 |
| 33 | **CycEnv Sustain** | CycEnv | 43 |
| 34 | **LFO Rate** | LFO | 48/55 |
| 35 | **LFO Wave** | LFO | — (sub-param) |
| 36 | **LFO Amp** | LFO | — (AM param) |
| 37 | **Macro 1** | Macro | 106 |
| 38 | **Macro 2** | Macro | 115 |
| 39 | **Matrix Mod Amount** | Meta | — (meta-mod) |

---

## 3. Custom Assign Destinations (8)

Firmware enum @ `0x081AEA94`. These are **modulation-only** destinations with no physical knob — they enable sidechaining and meta-modulation.

| # | Destination | Address | Description | Sidechain Capable |
|---|-------------|---------|-------------|:-----------------:|
| 0 | **Vib Rate** | 0x081AEA94 | Vibrato LFO rate | ✅ |
| 1 | **Vib AM** | — | Vibrato LFO amplitude | ✅ |
| 2 | **VCA** | — | VCA level (sidechain) | ✅ |
| 3 | **LFO1 AM** | — | LFO1 amplitude | ✅ |
| 4 | **LFO2 AM** | — | LFO2 amplitude | ✅ |
| 5 | **CycEnv AM** | — | Cycling Envelope amplitude | ✅ |
| 6 | **Uni Spread** | — | Unison detune spread | — |
| 7 | **-Empty-** | — | Unassigned slot | — |

### Custom Assign Literal Pool References

Three separate literal pool entries reference the custom assign enum:

| Address | Reference Context |
|---------|-------------------|
| `0x081AEAF0` | Mod Matrix destination select |
| `0x081B0184` | Preset serialization |
| `0x081B1658` | UI display/selection |

---

## 4. Internal Destinations (119+)

These are firmware-internal modulation destinations, not directly exposed to the user. They are used by the mod matrix engine internally.

### 4.1 Internal Mod Matrix Structures

**13-column int16 arrays** @ `0x0812002E` (20 arrays):

```
Array layout: 20 arrays × 13 columns (int16 each)
Pattern: diagonal sliding window of modulation amounts
Unique non-zero values: 8 distinct constants
  0x0000 = 0       (disabled)
  0x1002 = 4098    (quantization step)
  0x3781 = 14193   (primary mod amount)
  0x0812 = 2066    (secondary mod amount)
  0x2485 = 9349    (tertiary mod amount)
  0x2489 = 9353    (tertiary variant)
  0x248D = 9357    (tertiary variant)
  0x2491 = 9361    (tertiary variant)
  0x2495 = 9365    (tertiary variant)
  0x2499 = 9369    (tertiary variant)
```

### 4.2 Internal Destination Categories

#### 4.2.1 Oscillator Internal Destinations (~30)

| # | Destination | eSynthParams | Internal ID |
|---|-------------|-------------|-------------|
| 1 | Osc1 Param3 (sub-osc) | 3 | Osc1_Opt3 |
| 2 | Osc1 Fine Tune | 6 | Osc1_FineTune |
| 3 | Osc1 Opt1 | 7 | Osc1_Opt1 |
| 4 | Osc1 Opt2 | 8 | Osc1_Opt2 |
| 5 | Osc1 Opt3 | 9 | Osc1_Opt3 |
| 6 | Osc1 Mod Quantize | 10 | Osc1_TuneModQuantize |
| 7 | Osc2 Param3 | 14 | Osc2_Param3 |
| 8 | Osc2 Volume | 15 | Osc2_Volume |
| 9 | Osc2 Fine Tune | 17 | Osc2_FineTune |
| 10 | Osc2 Opt1 | 18 | Osc2_Opt1 |
| 11 | Osc2 Opt2 | 19 | Osc2_Opt2 |
| 12 | Osc2 Opt3 | 20 | Osc2_Opt3 |
| 13 | Osc2 Mod Quantize | 21 | Osc2_TuneModQuantize |
| 14 | Osc Bend Range | 22 | Osc_BendRange |
| 15 | Osc Free Run | 23 | Osc_Freerun |
| 16 | Glide Mode | 25 | GlideMode |
| 17 | Glide Sync | 26 | GlideSync |
| 18 | Mixer Non-Linearity | 27 | Osc_MixNonLinear |
| 19 | Osc1 Sub-voice spread | — | Internal voice mod |
| 20 | Osc2 Sub-voice spread | — | Internal voice mod |
| 21–30 | Osc1/2 engine-specific params | — | Per-engine sub-mods |

#### 4.2.2 Filter Internal Destinations (~6)

| # | Destination | eSynthParams |
|---|-------------|-------------|
| 1 | VCF Type | 31 |
| 2 | Env Attack Curve | 33 |
| 3 | Env Decay Curve | 35 |
| 4 | Env Release Curve | 38 |
| 5 | VCF internal resonance offset | — |
| 6 | VCF internal key tracking | — |

#### 4.2.3 FX Internal Destinations (~16)

| # | Destination | eSynthParams |
|---|-------------|-------------|
| 1 | FX1 Type | 62 |
| 2 | FX1 Opt1 | 66 |
| 3 | FX1 Opt2 | 67 |
| 4 | FX1 Opt3 | 68 |
| 5 | FX1 Enable | — |
| 6 | FX2 Type | 70 |
| 7 | FX2 Opt1 | 74 |
| 8 | FX2 Opt2 | 75 |
| 9 | FX2 Opt3 | 76 |
| 10 | FX3 Type | 77 |
| 11 | FX3 Opt1 | 78 |
| 12 | FX3 Opt2 | 79 (shared) |
| 13 | FX3 Opt3 | — |
| 14 | FX3 Enable | 85 |
| 15 | Delay Routing | 215 |
| 16 | Reverb Routing | 216 |

#### 4.2.4 Envelope/LFO Internal Destinations (~25)

| # | Destination | eSynthParams |
|---|-------------|-------------|
| 1 | Env Attack | 32 |
| 2 | Env Decay | 34 |
| 3 | Env Sustain | 36 |
| 4 | Env Release | 37 |
| 5 | CycEnv Mode | 44 |
| 6 | CycEnv Rise Curve | 40 |
| 7 | CycEnv Fall Curve | 42 |
| 8 | CycEnv Retrig Source | 45 |
| 9 | CycEnv Stage Order | 46 |
| 10 | CycEnv Tempo Sync | 47 |
| 11 | LFO1 Wave | 49 |
| 12 | LFO1 Rate Sync | 50 |
| 13 | LFO1 Sync Enable | 51 |
| 14 | LFO1 Sync Filter | 52 |
| 15 | LFO1 Retrig | 53 |
| 16 | LFO1 Loop | 54 |
| 17 | LFO2 Wave | 56 |
| 18 | LFO2 Rate Sync | 57 |
| 19 | LFO2 Sync Enable | 58 |
| 20 | LFO2 Sync Filter | 59 |
| 21 | LFO2 Retrig | 60 |
| 22 | LFO2 Loop | 61 |
| 23 | CycEnv AM | Custom Assign #5 |
| 24 | LFO1 AM | Custom Assign #3 |
| 25 | LFO2 AM | Custom Assign #4 |

#### 4.2.5 Voice/Vibrato Internal Destinations (~12)

| # | Destination | eSynthParams |
|---|-------------|-------------|
| 1 | Vibrato Rate | 86 |
| 2 | Vibrato Depth | 87 |
| 3 | Vibrato AM | 88 |
| 4 | Voice Mode | 89 |
| 5 | Unison Mode | 90 |
| 6 | Unison Count | 91 |
| 7 | Unison Spread | 92 |
| 8 | Legato Mode | 93 |
| 9 | Retrig Mode | 94 |
| 10 | Poly Allocation | 95 |
| 11 | Poly Steal Mode | 96 |
| 12 | Release Curve | — |

#### 4.2.6 Velocity Modulation Internal Destinations (~4)

| # | Destination | eSynthParams |
|---|-------------|-------------|
| 1 | Velo > Env Amount | 100 |
| 2 | Velo > VCA | 101 |
| 3 | Velo > VCF | 102 |
| 4 | Velo > Time | 103 |

#### 4.2.7 Pitch Modulation Internal Destinations (~4)

| # | Destination | eSynthParams |
|---|-------------|-------------|
| 1 | Pitch 1 (Osc1) | 104 |
| 2 | Pitch 2 (Osc2) | 105 |
| 3 | Osc1 Bend Range | — |
| 4 | Osc2 Bend Range | — |

#### 4.2.8 Macro Internal Destinations (~10)

| # | Destination | eSynthParams |
|---|-------------|-------------|
| 1 | Macro1 Value | 106 |
| 2 | Macro1 Dest | 107 |
| 3 | Macro1 Amount | 108 |
| 4 | Macro2 Value | 115 |
| 5 | Macro2 Dest | 116 |
| 6 | Macro2 Amount | 117 |
| 7 | Macro1 Dest Page | — |
| 8 | Macro2 Dest Page | — |
| 9 | Matrix Mod Amount | — (meta-mod) |
| 10 | Mod Depth (global) | — |

#### 4.2.9 Mod Matrix Dot Destinations (28)

The 28 matrix enable/disable dots are themselves internal modulation targets:

| # | Destination | eSynthParams Range |
|---|-------------|-------------------|
| 1–4 | MxDst CycEnv → Col1~4 | 124–127 |
| 5–8 | MxDst LFO1 → Col1~4 | 128–131 |
| 9–12 | MxDst LFO2 → Col1~4 | 132–135 |
| 13–16 | MxDst Velo/AT → Col1~4 | 136–139 |
| 17–20 | MxDst Wheel → Col1~4 | 140–143 |
| 21–24 | MxDst Kbd → Col1~4 | 144–147 |
| 25–28 | MxDst ModSeq → Col1~4 | 148–154 |

> **Note**: These enable/disable dots for the hardwired columns. The assignable columns (5–13) have their own separate dot storage.

#### 4.2.10 Arpeggiator Internal Destinations (~7)

| # | Destination | eSynthParams |
|---|-------------|-------------|
| 1 | Arp Mode | 155 |
| 2 | Arp Octave Range | 156 |
| 3 | Arp Tempo Div | 157 |
| 4 | Arp Repeat | 158 |
| 5 | Arp Ratchet | 159 |
| 6 | Arp Rand Oct | 160 |
| 7 | Arp Mutate | 161 |

#### 4.2.11 Sequencer Internal Destinations (~18)

| # | Destination | eSynthParams / eEditParams |
|---|-------------|---------------------------|
| 1 | Seq Mode | 162 |
| 2 | Seq Length | 163 |
| 3 | Seq Gate | 164 |
| 4 | Seq Swing | 165 |
| 5 | Seq Time Div | 166 |
| 6 | Seq Autom 1 | 167 |
| 7 | Seq Autom 2 | 168 |
| 8 | Seq Autom 3 | 169 |
| 9 | Seq Autom 4 | 170 |
| 10 | Smooth Mod 1 | 171 |
| 11 | Smooth Mod 2 | 172 |
| 12 | Smooth Mod 3 | 173 |
| 13 | Smooth Mod 4 | 174 |
| 14 | Seq Step | — |
| 15 | Seq Rec State | — |
| 16 | Seq Play State | — |
| 17 | Seq Transpose | — |
| 18 | Seq Page | — |

#### 4.2.12 Keyboard/Scale Internal Destinations (~28)

| # | Destination | eSynthParams |
|---|-------------|-------------|
| 1 | Scale Mode | 175 |
| 2 | Root Note | 176 |
| 3 | Scale Note 1 (C) | 177 |
| 4 | Scale Note 2 (C#) | 178 |
| 5 | Scale Note 3 (D) | 179 |
| 6 | Scale Note 4 (D#) | 180 |
| 7 | Scale Note 5 (E) | 181 |
| 8 | Scale Note 6 (F) | 182 |
| 9 | Scale Note 7 (F#) | 183 |
| 10 | Scale Note 8 (G) | 184 |
| 11 | Scale Note 9 (G#) | 185 |
| 12 | Scale Note 10 (A) | 186 |
| 13 | Scale Note 11 (A#) | 187 |
| 14 | Scale Note 12 (B) | 188 |
| 15 | Chord Mode | 189 |
| 16 | Chord Note 1 | 190 |
| 17 | Chord Note 2 | 191 |
| 18 | Chord Note 3 | 192 |
| 19 | Chord Note 4 | 193 |
| 20 | Chord Note 5 | 194 |
| 21 | Chord Note 6 | 195 |
| 22 | Chord Hold | 196 |
| 23 | Octave Shift | 197 |
| 24 | Transpose | 198 |
| 25 | Velo > VCF | 199 |
| 26 | Kbd Source | 200 |
| 27 | Matrix Src VeloAT | 201 |
| 28 | Dice Seed | 214 |

---

## 5. Destination Count Summary

| Category | Count | User Access | Description |
|----------|-------|:-----------:|-------------|
| **Hardwired** | **4** | Always ON | Col 1–4: Pitch, Shape, Cutoff, VCA |
| **Assignable** | **9** | Slot selection | Col 5–13: 3 pages × 3 slots |
| **Assignable Pool** | **39** | Via Assign slots | Destinations selectable for Assign slots |
| **Custom Assign** | **8** | Sidechain/Meta | Vib Rate/AM, VCA, LFO AMs, CycEnv AM, Uni Spread |
| **Internal Osc** | **~30** | NRPN/SysEx | Osc sub-params, engine-specific |
| **Internal VCF** | **~6** | NRPN/SysEx | Filter sub-params |
| **Internal FX** | **~16** | NRPN/SysEx | FX type, opts, routing |
| **Internal Env/LFO** | **~25** | NRPN/SysEx | Envelope curves, LFO sub-params |
| **Internal Voice** | **~12** | NRPN/SysEx | Voice mode, unison, legato |
| **Internal VeloMod** | **~4** | NRPN/SysEx | Velocity sensitivity |
| **Internal Pitch** | **~4** | NRPN/SysEx | Pitch bend per-osc |
| **Internal Macro** | **~10** | NRPN/SysEx | Macro dest/amount |
| **Matrix Dots** | **28** | Internal | Hardwired col enable/disable |
| **Internal Arp** | **~7** | NRPN/SysEx | Arpeggiator params |
| **Internal Seq** | **~18** | NRPN/SysEx | Sequencer params |
| **Internal Kbd/Scale** | **~28** | NRPN/SysEx | Scale, chord, keyboard |
| **TOTAL** | **~247** | — | All modulation destinations |

### User-Reachable Total

| Access Level | Count |
|-------------|-------|
| Direct (knobs + hardwired) | 4 (hardwired) + 39 (pool) = 43 |
| Custom Assign (sidechain) | 8 |
| **Total user-reachable** | **51** unique destinations |
| Firmware internal only | ~196 |

---

## 6. Source-to-Destination Routing Constraints

### 6.1 Hardwired Constraints

- **All 7 sources** are **always routed** to Columns 1–4
- Cannot be disabled per-source (dots only control enable/disable)
- Amount per dot: -100 to +100 (bipolar)

### 6.2 Assignable Constraints

- Each of 9 Assign slots can target **any** of the 39 assignable pool destinations
- **Singleton FX constraint**: Reverb, Delay, MultiComp — only 1 instance across 3 FX slots
- **Osc1-only engines** cannot be modulated on Osc2 row (Audio In, Wavetable, Sample, Granular)
- **Osc2-only engines** cannot be modulated on Osc1 row (Chords, FM/RM, Multi Filter, etc.)

### 6.3 Custom Assign Constraints

- Custom Assign destinations are **separate** from the Assign pool
- Enable **meta-modulation**: modulating a mod amount (sidechaining)
- LFO AM → modulates the output amplitude of that LFO
- CycEnv AM → modulates the output amplitude of the cycling envelope
- VCA Custom Assign → sidechain compression effect
- **Matrix Mod Amount** → modulates the amount of *another* routing (meta-mod)

### 6.4 Macro System Constraints

| Constraint | Value |
|-----------|-------|
| Macro count | 2 (M1, M2) |
| CC mapping | M1=CC117, M2=CC118 |
| Destinations | Any assignable pool destination |
| Amount | -100 to +100 |
| Cascading | Macro can target "Matrix Mod Amount" for 2nd-order mod |

### 6.5 NRPN Mod Depth Routing

The 16-channel param router (`FUN_08184EC0`) handles mod depth NRPN:

| NRPN Range | Function |
|-----------|----------|
| 0xAE–0xB1 | Mod depth ch1–ch4 (Q15 values) |
| 0x9E–0xAD | Param routing ch1–ch16 (16 MIDI channels) |

---

## 7. Mod Matrix Data Structures

### 7.1 Firmware Memory Layout

```
Mx_Dots[91]        — Boolean: 91 routing enable flags (1 bit each)
Mx_Assign[91]      — Destination ID for assignable slots
Mx_Amount[91]      — Mod amount per routing (-100 ~ +100, Q15)
Mx_DestPool[39]    — Assignable destination enum table
Mx_CustomAssign[8] — Custom Assign destination IDs
Mx_Source[7]       — Active source configuration
Mx_Page            — Current page (0–2)
Mx_Cursor          — Selected cell (row 0–6, col 0–12)
```

### 7.2 13-Column Array Pattern (20 arrays @ `0x0812002E`)

The 20 int16 arrays follow a **diagonal sliding window** pattern:

```
Array 0:  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x1002, 0x3781, 0x0812]
Array 1:  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0x1002, 0x3781, 0x0812, 0x2485]
Array 2:  [0, 0, 0, 0, 0, 0, 0, 0, 0x1002, 0x3781, 0x0812, 0x2485, 0x0812]
...
Array 11: [0x1002, 0x3781, 0x0812, 0x2485, 0x0812, 0x2489, 0x0812, 0x248D, 0x0812, 0x2491, 0x0812, 0x2495, 0x0812]
...
Array 19: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x0812, 0x0006, 0x0001]
```

Pattern: Each subsequent array shifts the non-zero window one position left, maintaining the diagonal structure. The primary mod values cycle through `0x3781, 0x0812, 0x2485, 0x2489, 0x248D, 0x2491, 0x2495`.

### 7.3 Mod Depth Calculator (`FUN_08184CD8`)

Key quantization constants (6 steps):

| Step | Value | Q15 Fraction | Meaning |
|------|-------|-------------|---------|
| 0 | 0x5555 | 2/3 | Default |
| 1 | 0x638D | ~0.778 | Step 1 |
| 2 | 0x71C6 | ~0.889 | Step 2 |
| 3 | 0x38E3 | ~0.445 | Step 3 |
| 4 | 0x2AAA | 1/3 | Step 4 |
| 5 | 0x471C | ~0.556 | Step 5 |

The function reads mod source values from vtable getter calls (index 9, 5, 13, 29) and applies piecewise-linear quantization.

---

## 8. CM7 Mod Matrix Dispatch (7×13 Unrolled)

### 8.1 CM7 Core Functions

| Function | Address | Size | Description |
|----------|---------|------|-------------|
| `FUN_0812853c` | 0x812853c | 2,588B | 7×13 per-voice mod dispatch |
| `FUN_08144ce0` | 0x8144ce0 | 568B | Per-voice mod routing |
| `FUN_08156d20` | 0x8156d20 | 1,272B | MIDI event parsing for mod |
| `FUN_08170fc4` | 0x8170fc4 | 1,290B | Mod amount calculation |
| `FUN_081719c4` | 0x81719c4 | 1,230B | Mod destination resolution |

### 8.2 Dispatch Pattern

The CM7 mod matrix uses **unrolled loops** with 7 iterations (one per source row) and 13 destination columns per row. The function `FUN_0812853c` contains:

- State machine with bit-flag checks (bit 27, bit 29, etc.)
- Voice flag validation (state bitmask)
- Per-voice mod amount accumulation
- Direct function calls to per-voice mod apply functions

### 8.3 7×13 Validation

Confirmed by 20 × 13-element int16 arrays at `0x0812002E` with diagonal sliding pattern — consistent with 7-row × 13-column unrolled dispatch.

---

## 9. Firmware Address Reference

| Symbol | Address | Size | Description |
|--------|---------|------|-------------|
| Mod Source enum | 0x081B1BCC | — | 9 source types |
| Mod Dest enum | 0x081AEA94 | — | Custom Assign destinations |
| Custom Assign ref 1 | 0x081AEAF0 | — | Literal pool ref |
| Custom Assign ref 2 | 0x081B0184 | — | Preset serialization ref |
| Custom Assign ref 3 | 0x081B1658 | — | UI display ref |
| Kbd Src enum | 0x081B0E10 | — | 9 keyboard sub-modes |
| 13-col arrays | 0x0812002E | 520B | 20 × 13 int16 arrays |
| Smooth Mod 1–4 | 0x081B1B8C | — | Mod Seq 4 lane |
| `FUN_08184CD8` | 0x8184CD8 | 466B | Mod depth calc (CM4) |
| `FUN_08184EC0` | 0x8184EC0 | 178B | 16-ch param router |
| `FUN_08184F8C` | 0x8184F8C | 246B | Mod depth apply |
| `FUN_0812853c` | 0x812853c | 2,588B | 7×13 dispatch (CM7) |
| `FUN_08144ce0` | 0x8144ce0 | 568B | Per-voice routing (CM7) |
| `FUN_08170fc4` | 0x8170fc4 | 1,290B | Amount calc (CM7) |
| `FUN_081719c4` | 0x81719c4 | 1,230B | Dest resolution (CM7) |
| `Preset::set(eCtrlParams)` | 0x081AC7E9 | — | Mod Matrix param setter |

---

## 10. Complete Destination Enum (eCtrlParams — Estimated)

Based on the eCtrlParams setter at `0x081AC7E9` and NRPN handler case values:

```
eCtrlParams (estimated ~140 entries):
  0–3:    Matrix Dot enable flags (per-source, 4 hardwired cols)
  4–12:   Matrix Assign destinations (9 slots, 3 pages)
  13–20:  Macro1 Dest, Macro1 Amount, Macro2 Dest, Macro2 Amount, etc.
  21–28:  MxDot CycEnv/LFO/Velo/Wheel/Kbd/Seq (28 total)
  29–36:  Arp Mode/Range/Div/Repeat/Ratchet/RandOct/Mutate
  37–54:  Seq Mode/Length/Gate/Swing/Div/Autom1-4/Smooth1-4
  55–82:  Scale Mode/Root/Notes(12)/Chord(8)/Hold
  83–90:  Voice Mode/Unison/Count/Spread/Legato/Retrig/PolyAlloc/Steal
  91–94:  Vibrato Rate/Depth/AM/Release Curve
  95–98:  VeloMod Env/VCA/VCF/Time
  99–104: Pitch/Bend/Mod Quantize per-osc
  105–110: CycEnv Mode/RiseCurve/FallCurve/Retrig/StageOrder/TempoSync
  111–124: LFO1/LFO2 Wave/RateSync/SyncEn/SyncFilter/Retrig/Loop
  125–140: FX Type/Opt1/Opt2/Opt3 per-slot, Delay/Reverb Routing
```

> **Note**: Exact enum ordering requires runtime extraction. The above is estimated from NRPN handler cases and eSynthParams indices.

---

## 11. Meta-Modulation (Modulating Modulation)

### 11.1 Architecture

```
Source (e.g., LFO1) → Custom Assign (e.g., LFO2 AM) → Reduces/amplifies LFO2 output
                                                          ↓
                                                   LFO2 (amplitude-modulated) → Destination
```

### 11.2 Valid Meta-Mod Paths

| Source | Via Custom Assign | Affects |
|--------|------------------|---------|
| Any source | LFO1 AM | LFO1 output amplitude |
| Any source | LFO2 AM | LFO2 output amplitude |
| Any source | CycEnv AM | CycEnv output amplitude |
| Any source | Vib AM | Vibrato output amplitude |
| Any source | VCA | Amplifier level (sidechain) |
| Any source | Matrix Mod Amount | Amount of another routing |
| Macro 1/2 | Matrix Mod Amount | 2nd-order modulation |

---

## 12. Statistics Summary

| Category | Count |
|----------|-------|
| **Mod sources (rows)** | 7 (manual) / 9 (firmware enum) |
| **Hardwired destinations** | 4 per source |
| **Assignable slots** | 9 (3 pages × 3) |
| **Assignable destination pool** | 39 |
| **Custom Assign destinations** | 8 (7 active + 1 empty) |
| **Max simultaneous routings** | 91 (7 × 13) |
| **Internal destinations (total)** | ~196 |
| **Total unique destinations** | ~247 |
| **User-reachable destinations** | 51 (43 assignable + 8 custom assign) |
| **Meta-modulation depth** | 2 levels (mod → mod → destination) |
| **Q15 quantization steps** | 6 |

---

*Phase 12-4 | MiniFreak Reverse Engineering*
*Firmware: fw4_0_1_2229 (2025-06-18)*
*Sources: PHASE8_SEQ_ARP_MOD.md, PHASE9_RESULTS.md, phase9_mod_matrix_v2.json, phase9_mod_matrix_v3.json, phase9_mod_matrix_cm7.json, phase9_mod_matrix_dispatch.json, PHASE11_GAP_FILL_ANALYSIS.md, mf_enums.py*
