# Phase 12-5: Step Sequencer 64-Step Buffer Layout

**Date**: 2026-04-26
**Sources**: `firmware/analysis/phase5_mnfx_format.json`, `firmware/analysis/parse_mnfx.py`, `tools/mnfx_editor.py`, `notes/PHASE8_SEQ_ARP_MOD.md`, `notes/PHASE11_GAP_FILL_ANALYSIS.md`
**Firmware**: fw4_0_1_2229 (CM4 + CM7)

---

## 1. Overview

The MiniFreak step sequencer is a **64-step × multi-track** pattern sequencer stored as individual named float parameters in the boost::serialization text archive (.mnfx) format. There is no binary "step buffer" — the sequencer state is serialized as ~2,175 named parameter triplets out of the total 2,368 parameters per preset.

### Key Dimensions

| Dimension | Value | Evidence |
|-----------|-------|----------|
| Steps | **64** (0–63) | CM7: integer 64 appears 17×; all param names use S0–S63 |
| Note tracks | **6** (I0–I5) | Pitch_S, Length_S, Velo_S all have I0–I5 |
| Mod lanes | **4** (I0–I3) | Mod_S has I0–I3; Smooth Mod 1–4 confirmed in CM4 |
| CC Automations | **3** (+1 Last) | Seq_Autom_Dest/Set/Smooth/Val _0..2 + _Last |
| Total step params | **2,175** | Out of 2,368 total (92%) |

---

## 2. Parameter Block Layout (in .mnfx serialization order)

Parameters appear in **alphabetical order within boost::serialization** (not logical group order). The actual parameter index positions in a preset file (from `100_RoboBallad.mnfx`):

```
Offset  Param Group          Count  Description
──────  ───────────────────  ─────  ─────────────────────────────────────────
[0]     Header + metadata    —      Preset name, bank, author, category, etc.
[7]     AutomReserved1_S0-63  64    Automation reserved (all zero, unused)
[81]    Dice_Seed             1     Random seed for Dice mode
[127]   Gate_S0-63            64    Per-step gate (tie/slide) value
[242]   Length_S0-63_I0-5    384    Per-step per-track note length (64×6)
[645]   ModState_S0-63        64    Per-step mod state (smooth interpolation)
[709]   Mod_S0-63_I0-3       256    Per-step per-lane modulation value (64×4)
[969]   Mx_AssignDot_0-61     62    Mod matrix assignable routing enable
[1032]  Mx_ColId_0-7           8    Mod matrix assignable destination IDs
[1041]  Mx_Dot_0-26           27    Mod matrix hardwired routing enable (7×4-1)
[1100]  Pitch_S0-63_I0-5     384    Per-step per-track pitch (64×6)
[1486]  Reserved1-4_S0-63    256    Reserved banks 1–4 (all zero, future use)
[1743]  Seq_Autom_*           16    CC automation config (3 lanes + Last)
[1759]  Seq_Gate               1    Sequencer gate type
[1760]  Seq_Length             1    Sequence length (1–64)
[1761]  Seq_Mode               1    Sequencer mode (3 modes)
[1762]  Seq_Swing              1    Swing amount
[1763]  Seq_TimeDiv            1    Tempo subdivision
[1764]  Shp1_*                65    LFO Shaper 1 (Length + 16 steps × 4 params + Last)
[1829]  Shp2_*                65    LFO Shaper 2 (same structure)
[1895]  StepState_S0-63        64    Per-step active/inactive toggle
[1970]  Velo_S0-63_I0-5      384    Per-step per-track velocity (64×6)
```

---

## 3. Step Data Structure — Per Step

Each step in the sequencer has the following data across multiple parameter arrays:

### 3.1 Note Track Data (6 tracks × 64 steps = 384 entries each)

#### Pitch_S{step}_I{track} — Note Pitch
- **Type**: Float, normalized
- **Range**: [0.0, 1.0] (default 1.0 = "no note")
- **Encoding**: `pitch_normalized = midi_note / 127.0` (approximately)
- **Default**: 1.0 (tied/rest — no trigger)
- **Observation**: Values like 0.375, 0.46875, 0.5234375 map to specific MIDI notes
  - 0.375 × 128 ≈ 48 (C3) — these are quantized to 1/128 steps
  - 0.46875 × 128 = 60 (C4)
  - Likely: `value = midi_note / 128` (7-bit pitch, 0–127, normalized to 0.0–0.9921875)

#### Length_S{step}_I{track} — Note Length
- **Type**: Float, normalized
- **Range**: [0.0, ~0.74]
- **Default**: 0.0 (shortest — trigger only)
- **Observation**: Max observed ~0.74 (≈ 94/127), values like 0.49606299 ≈ 63/127
- **Likely encoding**: `value = length_ticks / 127.0` where length is in some internal tick unit
- **Per-track**: Each of the 6 tracks (I0–I5) can have independent note lengths
- **Usage**: I0 has most non-default values (65/256 presets); I1–I5 are sparse

#### Velo_S{step}_I{track} — Velocity
- **Type**: Float, normalized
- **Range**: [0.008, 1.0]
- **Default**: 0.78740156 ≈ 100/127
- **Encoding**: `value = midi_velocity / 127.0`
- **Observation**: 0.78740156 × 127 = 100 (default velocity = 100)
- **Per-track**: All 6 tracks always have velocity data (even tied notes)

### 3.2 Gate/Tie Data (64 steps, shared across tracks)

#### Gate_S{step} — Gate Value
- **Type**: Float
- **Range**: [0.5, 0.5] (observed — all presets show constant 0.5)
- **Encoding**: Likely encodes gate state as part of a combined bitfield
- **Note**: Despite being per-step, Gate_S is always 0.5 across all 256 presets
  - May be a legacy/unused parameter, or gate is encoded differently internally
  - The actual gate/trigger behavior may be controlled by StepState + Length

#### StepState_S{step} — Step Active Toggle
- **Type**: Float (effectively boolean)
- **Range**: [0.0, 1.0]
- **Default**: 0.0 (inactive)
- **Encoding**: 1.0 = step active, 0.0 = step inactive
- **Usage**: Determines whether a step triggers notes. In RoboBallad: S0–S31 = 1.0, S32–S63 = 0.0 (32-step pattern)

### 3.3 Modulation Lane Data (4 lanes × 64 steps = 256 entries)

#### Mod_S{step}_I{lane} — Mod Lane Value
- **Type**: Float, normalized
- **Range**: [0.36, 0.83]
- **Default**: 0.5 (center = no modulation)
- **Encoding**: Bipolar modulation, centered at 0.5
  - 0.0 = full negative, 0.5 = center, 1.0 = full positive
- **Lanes**: I0–I3 correspond to Smooth Mod 1–4 (confirmed in CM4 firmware)

#### ModState_S{step} — Mod Lane State/Smoothing
- **Type**: Float
- **Range**: [0.0, 0.797]
- **Default**: 0.0029297769 ≈ 3/1024 (nearly zero)
- **Encoding**: Controls interpolation/smoothing state per step
  - Near-zero = no modulation at this step
  - Non-zero = modulation value active at this step

---

## 4. Sequencer Global Parameters

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `Seq_Gate` | float | [0.0, 1.0] | 0.5 | Gate type/mode |
| `Seq_Length` | float | [0.0, 1.0] | 0.249 | Sequence length (1–64 steps) |
| `Seq_Mode` | float | [0.0, 0.667] | 0.667 | Seq mode: 3 choices (0=off, 0.333=forward, 0.667=?) |
| `Seq_Swing` | float | [0.0, 0.64] | 0.0 | Swing amount |
| `Seq_TimeDiv` | float | [0.0, 0.929] | 0.5 | Tempo subdivision (11 choices) |

### Seq_Mode Encoding
- `0.0` = Off (0/2)
- `0.33332315` ≈ 1/3 = Mode 1 (Forward?)
- `0.66667682` ≈ 2/3 = Mode 2 (most common in presets)

### Seq_TimeDiv Encoding (11 subdivisions)
Values follow `index / (N-1)` pattern with N likely = 14 (13 choices → 0/13 to 12/13).

---

## 5. CC Automation (3 Lanes)

The sequencer supports 3 CC automation lanes, each with 4 sub-parameters:

| Parameter | Count | Description |
|-----------|-------|-------------|
| `Seq_Autom_Dest_0..2` + `_Last` | 4 | Automation destination parameter ID |
| `Seq_Autom_Set_0..2` + `_Last` | 4 | Automation enable/set flag |
| `Seq_Autom_Smooth_0..2` + `_Last` | 4 | Smoothing on/off (default 1.0 = on) |
| `Seq_Autom_Val_0..2` + `_Last` | 4 | Automation value (bipolar, centered 0.5) |

**Total**: 16 automation parameters (3 usable lanes + 1 `_Last` sentinel each)

---

## 6. LFO Shaper Steps (2 Shapers × 16 Steps)

Each LFO Shaper has 16 steps with 4 sub-parameters + 1 global length:

| Parameter | Count | Description |
|-----------|-------|-------------|
| `Shp{N}_Length` | 1 | Shaper cycle length |
| `Shp{N}_Step_Amp_0..15` + `_Last` | 17 | Amplitude per step |
| `Shp{N}_Step_Curve_0..15` + `_Last` | 17 | Curve shape per step |
| `Shp{N}_Step_En_0..15` + `_Last` | 17 | Enable per step |
| `Shp{N}_Step_Slope_0..15` + `_Last` | 17 | Slope/interpolation per step |

**Total per shaper**: 65 parameters (1 length + 16×4 + 1 Last per sub-array)

---

## 7. Reserved/Unused Space

| Block | Count | Status |
|-------|-------|--------|
| `AutomReserved1_S0-63` | 64 | All zero across all presets — future automation expansion |
| `Reserved1_S0-63` | 64 | All zero — bank 1 |
| `Reserved2_S0-63` | 64 | All zero — bank 2 |
| `Reserved3_S0-63` | 64 | All zero — bank 3 |
| `Reserved4_S0-63` | 64 | All zero — bank 4 |

**Total reserved**: 320 parameters (13.5% of total)

The 4 Reserved banks × 64 steps suggest planned expansion from 6 to more note tracks, or additional per-step data types.

---

## 8. Mod Matrix (Sequencer-Related)

| Parameter | Count | Description |
|-----------|-------|-------------|
| `Mx_Dot_0-26` + `_Last` | 28 | Hardwired routing enable (7 sources × 4 destinations - 1) |
| `Mx_AssignDot_0-61` + `_Last` | 63 | Assignable routing enable (9 slots × 7 columns - 1) |
| `Mx_ColId_0-7` + `_Last` | 9 | Assignable destination parameter IDs |

**Row 7 of the mod matrix is "Mod Seq"** — the 4 Smooth Mod lanes feed into the modulation matrix as a source.

---

## 9. Firmware RTTI Confirmation

From Phase 11 gap-fill analysis, the following firmware functions handle sequencer parameters:

| Function | Address (CM4) | Enum |
|----------|---------------|------|
| `Preset::set(eSeqParams, ...)` | `0x081AC84D` | Sequencer global parameters |
| `Preset::set(eSeqStepParams, ...)` | `0x081AC8D9` | Step data (Pitch, Length, Velo, Gate, StepState) |
| `Preset::set(eSeqAutomParams, ...)` | `0x081AC97D` | CC automation parameters |
| `Preset::set(eShaperParams, ...)` | `0x081AC9D4` | LFO Shaper step data |

### CM4 Sequencer UI Parameters (eEditParams)

| Address | Parameter |
|---------|-----------|
| `0x081AFA90` | `Tempo Div` |
| `0x081AFA9C` | `Seq Page` |
| `0x081AFAA8` | `PlayState` |
| `0x081AFAB4` | `RecState` |
| `0x081AFAC0` | `RecMode` |
| `0x081AFAC8` | `Cursor` |
| `0x081AFAD0` | `MetronomeBeat` |
| `0x081AFAE0` | `Playing Tempo` |
| `0x081AFAF0` | `Seq Transpose` |

---

## 10. Conceptual Step Structure (Logical View)

While the .mnfx format stores each field as a separate named parameter, the logical per-step structure is:

```
Step N (0–63):
┌─────────────────────────────────────────────────────┐
│ StepState_S{N}         1 bit   Active/Inactive      │
│ Gate_S{N}              1 float Gate value (legacy?) │
├─────────────────────────────────────────────────────┤
│ Track 0 (I0):                                        │
│   Pitch_S{N}_I0        float  MIDI note / 128      │
│   Length_S{N}_I0       float  Note length           │
│   Velo_S{N}_I0         float  Velocity / 127        │
│ Track 1 (I1):                                        │
│   Pitch_S{N}_I1        float  MIDI note / 128      │
│   Length_S{N}_I1       float  Note length           │
│   Velo_S{N}_I1         float  Velocity / 127        │
│ Track 2 (I2): ...                                    │
│ Track 3 (I3): ...                                    │
│ Track 4 (I4): ...                                    │
│ Track 5 (I5):                                        │
│   Pitch_S{N}_I5        float  MIDI note / 128      │
│   Length_S{N}_I5       float  Note length           │
│   Velo_S{N}_I5         float  Velocity / 127        │
├─────────────────────────────────────────────────────┤
│ Mod Lane 0 (I0):                                    │
│   Mod_S{N}_I0          float  Mod value (bipolar)  │
│   ModState_S{N}        float  Interpolation state   │
│ Mod Lane 1 (I1):                                    │
│   Mod_S{N}_I1          float  Mod value (bipolar)  │
│ Mod Lane 2 (I2): ...                                 │
│ Mod Lane 3 (I3):                                    │
│   Mod_S{N}_I3          float  Mod value (bipolar)  │
└─────────────────────────────────────────────────────┘

Per step: 1 (state) + 6×3 (note tracks) + 4 (mod) + 1 (mod state) = 24 fields
Total: 64 steps × 24 fields = 1,536 core step parameters
Plus: 64 gate + 64 AutomReserved + 256 Reserved + 16 Seq_Autom + 130 Shaper + 101 Mx = 631 auxiliary
Grand total sequencer-related: 2,175 parameters
```

---

## 11. Value Encoding Summary

| Data Type | Normalization | Formula | Example |
|-----------|--------------|---------|---------|
| Pitch | 0.0–1.0 | `midi_note / 128` | C3 (48) = 0.375 |
| Velocity | 0.0–1.0 | `velocity / 127` | vel 100 = 0.7874 |
| Length | 0.0–1.0 | `ticks / 127` (approx) | — |
| Mod Value | 0.0–1.0 bipolar | Center = 0.5 | 0.5 = no modulation |
| Step State | Boolean | 0.0 or 1.0 | 1.0 = active |
| Gate | Constant | Always 0.5 | Legacy/unused |
| Mod State | 0.0–1.0 | ~0 = off, >0 = on | 0.003 = nearly off |
| Seq Mode | Enum | `index / (N-1)` | 0.667 = mode 2/3 |
| Seq Length | Enum | `index / (N-1)` | 0.249 ≈ step count |

---

## 12. Parameter Count Verification

| Category | Count | Running Total |
|----------|-------|---------------|
| AutomReserved1 | 64 | 64 |
| Dice_Seed | 1 | 65 |
| Gate | 64 | 129 |
| Length (64×6) | 384 | 513 |
| ModState | 64 | 577 |
| Mod (64×4) | 256 | 833 |
| Mx_AssignDot | 63 | 896 |
| Mx_ColId | 9 | 905 |
| Mx_Dot | 28 | 933 |
| Pitch (64×6) | 384 | 1,317 |
| Reserved (4×64) | 256 | 1,573 |
| Seq_Autom | 16 | 1,589 |
| Seq global | 5 | 1,594 |
| Shp1 | 65 | 1,659 |
| Shp2 | 65 | 1,724 |
| StepState | 64 | 1,788 |
| Velo (64×6) | 384 | 2,172 |
| **Subtotal (seq-related)** | **2,172** | |
| MxDst | 3 | 2,175 |
| **Total sequencer-related** | **2,175** | — |
| Non-sequencer params | 193 | — |
| **Grand total** | **2,368** | ✅ matches |

---

## 13. Key Findings

1. **No binary step buffer** — the sequencer is entirely represented as named float parameters in boost::serialization format. Each step field is a separate `<name_length> <name> <value>` triplet.

2. **6 independent note tracks** (I0–I5) with per-step pitch, length, and velocity. I0 is the primary track; I1–I5 are sparsely used in factory presets.

3. **4 modulation lanes** (Smooth Mod 1–4), bipolar, centered at 0.5, with per-step interpolation state.

4. **3 CC automation lanes** with destination, enable, smoothing, and value sub-parameters.

5. **320 reserved parameters** (4 banks × 64 + 64 AutomReserved) suggest future expansion — possibly additional note tracks or per-step CC automation data.

6. **Step sorting is alphabetical** within boost::serialization, not logical. The actual memory layout in firmware RAM likely differs from the serialized order.

7. **Gate_S is constant 0.5** across all presets — may be a vestigial parameter or gate encoding is handled differently (possibly through Length=0 meaning "no gate" and StepState=0 meaning "inactive").

8. **Pitch encoding uses /128 denominator** (not /127 like velocity), giving a 7-bit range 0–127 mapped to [0.0, 0.9921875]. Default value 1.0 represents "no note/tied".

---

*Document version: Phase 12-5 Final*
*Data source: 512 factory presets (256 full + 256 init), firmware fw4_0_1_2229*
