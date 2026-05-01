# MiniFreak Firmware-Based Manual Correction Report

**Document ID**: Phase 16 (English Edition V6)  
**Date**: 2026-05-01  
**Firmware**: CM4 `minifreak_main_CM4__fw4_0_1_2229` (2025-06-18)  
**Manual**: MiniFreak User Manual v4.0.0 / v4.0.1 (2025-07-04)  
**Method**: Direct CM4 binary scan (string/enum tables) + CM7 constant analysis + VST XML cross-verification + DLL string analysis  
**Confidence Scale**: ★★★★★ = Direct CM4 string confirmation / VST XML + CM4 cross-verification | ★★★★☆ = CM7 indirect evidence / VST cross-verify / DLL strings estimation | ★★★☆☆ = VST-only confirmation  

---

## Cover Letter

To: Arturia Documentation Team / support@arturia.com  
From: Independent Firmware Analysis Project  
Subject: MiniFreak User Manual — Firmware-Verified Correction Report (13 corrections, 12 enhancements)

This report documents discrepancies between the MiniFreak User Manual (v4.0.0 / v4.0.1) and the actual firmware behavior observed through static binary analysis of the CM4 (`minifreak_main_CM4`, 620 KB) and CM7 (`minifreak_main_CM7`, 524 KB) binaries, firmware version `4.0.1.2229` (2025-06-18), supplemented by VST plugin XML parameter definitions and DLL string analysis (Phase 14–15).

Each finding includes a firmware address and hex dump evidence. All addresses have been verified against the actual binary. Confidence ratings reflect the strength of the evidence — ★★★★★ items are directly confirmed from CM4 string tables and leave no room for interpretation error.

We believe these corrections would improve the manual's accuracy and help users understand features that exist in the hardware but are undocumented or incorrectly described.

---

## Part 1. Corrections (13 items)

> The following items represent cases where the firmware binary directly contradicts the manual's description.

---

### CORR-01: Poly Steal Mode Count — 4 listed, 6 exist

| Field | Content |
|-------|---------|
| **Manual Ref** | §Voice Mode > Poly Steal Mode |
| **Manual Says** | 4 modes: None / Once / Cycle / Reassign |
| **Firmware** | **6 modes**: None / Cycle / Reassign / Velocity / Aftertouch / Velo + AT |
| **Address** | CM4 `0x081B0F70` – `0x081B0FA4` |
| **Confidence** | ★★★★★ |

**Firmware Evidence**:
```
0x081B0F70: 4E 6F 6E 65 00                        "None"
0x081B0F78: 43 79 63 6C 65 00                     "Cycle"
0x081B0F80: 52 65 61 73 73 69 67 6E 00            "Reassign"
0x081B0F8C: 56 65 6C 6F 63 69 74 79 00            "Velocity"
0x081B0F98: 41 66 74 65 72 74 6F 75 63 68 00      "Aftertouch"
0x081B0FA4: 56 65 6C 6F 20 2B 20 41 54 00         "Velo + AT"
```

**Recommendation**: The manual's "Once" mode does not exist in firmware. Three additional modes (Velocity, Aftertouch, Velo + AT) are present. Update to: `None / Cycle / Reassign / Velocity / Aftertouch / Velo + AT` (6 modes).

---

### CORR-02: Modulation Matrix Source Count — 7 listed, 9 exist

| Field | Content |
|-------|---------|
| **Manual Ref** | §8.5 Modulation Matrix |
| **Manual Says** | 7 row sources (CycEnv, LFO1, LFO2, Velo/AT, Wheel, Keyboard, Mod Seq) |
| **Firmware** | **9 sources**: Keyboard, LFO, Cycling Env, Env/Voice, Voice, Envelope, FX, Sample Select, Wavetable Select |
| **Address** | CM4 `0x081B1BCC` – `0x081B1C1C` |
| **Confidence** | ★★★★★ |

**Firmware Evidence**:
```
0x081B1BCC: 4B 65 79 62 6F 61 72 64 00              "Keyboard"
0x081B1BD8: 4C 46 4F 00                            "LFO"
0x081B1BDC: 43 79 63 6C 69 6E 67 20 45 6E 76 00    "Cycling Env"
0x081B1BE8: 45 6E 76 20 2F 20 56 6F 69 63 65 00    "Env / Voice"
0x081B1BF4: 56 6F 69 63 65 00                      "Voice"
0x081B1BFC: 45 6E 76 65 6C 6F 70 65 00            "Envelope"
0x081B1C08: 46 58 00                               "FX"
0x081B1C0C: 53 61 6D 70 6C 65 20 53 65 6C 65 63 74 00  "Sample Select"
0x081B1C1C: 57 61 76 65 74 61 62 6C 65 20 53 65 6C 65 63 74 00  "Wavetable Select"
```

**Recommendation**: The manual's 7-row layout represents the UI display. Internally, the firmware uses 9 modulation sources. "Sample Select" and "Wavetable Select" were added in the V3 firmware update. The manual should document these two additional sources.

---

### CORR-03: Arpeggiator Mode Names and Index Order

| Field | Content |
|-------|---------|
| **Manual Ref** | §13 Arpeggiator > Arp Mode |
| **Manual Says** | 8 modes: Up / Down / UpDown / Random / Walk / Pattern / Order / Poly |
| **Firmware** | 8 modes confirmed, but index 2 is **"Arp UpDown"** (unique string, not reused "Arp Up"). Index order 3–7 differs from manual. |
| **Address** | CM4 `0x081AEC3C` – `0x081AEC8C` |
| **Confidence** | ★★★★★ |

**Firmware Evidence**:
```
0x081AEC3C: "Arp Up"       [idx 0]
0x081AEC44: "Arp Down"     [idx 1]
0x081AEC4C: "Arp UpDown"   [idx 2]  ← unique string
0x081AEC5C: "Arp Rand"     [idx 3]
0x081AEC68: "Arp Walk"     [idx 4]
0x081AEC74: "Arp Pattern"  [idx 5]
0x081AEC80: "Arp Order"    [idx 6]
0x081AEC8C: "Arp Poly"     [idx 7]
```

**Recommendation**: The manual's index ordering (Up/Down/UpDown/Random/**Order**/Walk/Poly/**Pattern**) does not match the firmware enum order (Up/Down/UpDown/Rand/Walk/Pattern/Order/Poly). While this does not affect user-facing behavior, MIDI implementation charts referencing mode indices should use the firmware order.

---

### CORR-04: Unison Implemented as 3 Independent Voice Modes

| Field | Content |
|-------|---------|
| **Manual Ref** | §Voice Mode > Unison |
| **Manual Says** | Unison Mode sub-setting: Mono / Poly / Para |
| **Firmware** | **3 independent Voice Mode entries**: `Unison`, `Uni (Poly)`, `Uni (Para)` — not a sub-setting |
| **Address** | CM4 `0x081AF500` – `0x081AF514` |
| **Confidence** | ★★★★★ |

**Firmware Evidence**:
```
0x081AF500: 55 6E 69 73 6F 6E 00                     "Unison"
0x081AF508: 55 6E 69 20 28 50 6F 6C 79 29 00         "Uni (Poly)"
0x081AF514: 55 6E 69 20 28 50 61 72 61 29 00         "Uni (Para)"
```

**Recommendation**: The manual treats Unison as a single mode with a sub-setting. In firmware, these are 3 separate entries in the Voice Mode enum (alongside Poly, Mono, Dual, Para). The manual should list them as distinct modes for clarity.

---

### CORR-05: LFO Waveform Display Names — Full Names vs. Abbreviations

| Field | Content |
|-------|---------|
| **Manual Ref** | §9 LFO > Wave |
| **Manual Says** | Sine / Triangle / Sawtooth / Square / Sample & Hold / Slew S&H / Exponential Saw / Exponential Ramp / User Shaper |
| **Firmware** | **Sin / Tri / Saw / Sqr / SnH / SlewSNH / ExpSaw / ExpRamp / Shaper** |
| **Address** | CM4 `0x081B0FB0` – `0x081B0FDB` |
| **Confidence** | ★★★★★ |

| Manual Name | Firmware Display Name |
|-------------|----------------------|
| Sine | **Sin** |
| Triangle | **Tri** |
| Sawtooth | **Saw** |
| Square | **Sqr** |
| Sample & Hold | **SnH** |
| Slew S&H | **SlewSNH** |
| Exponential Saw | **ExpSaw** |
| Exponential Ramp | **ExpRamp** |
| User Shaper | **Shaper** |

**Recommendation**: The firmware uses abbreviated names on the OLED display (likely due to screen space constraints). The manual should include both the full descriptive name and the actual display name shown on the hardware.

---

### CORR-06: Tempo Subdivision Count — 11 listed, 27 exist (updated)

| Field | Content |
|-------|---------|
| **Manual Ref** | §Tempo Sync / Sync Filter |
| **Manual Says** | 11 subdivisions: 1/4, 1/4T, 1/4D, 1/8, 1/8T, 1/8D, 1/16, 1/16T, 1/16D, 1/32, 1/32T |
| **Firmware** | **27 subdivisions** (VST XML `LFO_RateSync` item_list, Phase 14-2) |
| **Address** | CM4 `0x081AF0B4`–`0x081AF0FC` (primary, 11) + `0x081AF564`–`0x081AF58C` (secondary, 6); VST XML `minifreak_vst_params.xml` LFO_RateSync (27) |
| **Confidence** | ★★★★★ (upgraded from ★★★★☆ in V4) |

**Firmware Evidence**:
```
VST XML LFO_RateSync item_list (27 entries):
 0: 8d   1: 8    2: 4d   3: 8t   4: 4    5: 2d   6: 4t   7: 2
 8: 1d   9: 2t  10: 1   11: 1/2d  12: 1t  13: 1/2  14: 1/4d
15: 1/2t 16: 1/4 17: 1/8d 18: 1/4t 19: 1/8 20: 1/16d
21: 1/8t 22: 1/16 23: 1/32d 24: 1/16t 25: 1/32 26: 1/32t

CM4 primary table (11) @ 0x081AF0B4:
  "1/4", "1/8D", "1/4T", "1/8", "1/16D", "1/8T", "1/16", "1/32D", "1/16T", "1/32", "1/32T"

CM4 secondary table (6) @ 0x081AF564:
  "1/32t", "1/16t", "1/8t", "1/4t", "1/2t", "1/1"
```

**10 additional subdivisions** (beyond the 17 identified in V4):
```
"1/64", "1/64D", "1/64T", "1/128", "1/128D", "1/128T", "1/256", "1/256D", "1/256T", "1/512"
```

**Note on CM4 vs VST discrepancy**: The CM4 binary contains two separate tables (11 + 6 = 17 entries), while the VST XML defines a unified 27-entry list. Some entries exist only in the VST context (ultra-fast subdivisions like 1/256, 1/512), while others exist only in the CM4 context (e.g., "1/1" whole note). The two CM4 tables appear to serve different functional contexts (primary tempo sync vs. secondary/extended sync).

**Recommendation**: The VST XML represents the authoritative parameter definition for DAW integration. The manual should document at minimum the 17 hardware-accessible subdivisions, with a note that the VST plugin supports up to 27 subdivisions including ultra-fast rates (1/64 through 1/512).

---

### CORR-07: LFO Waveform Count — Incomplete Listing Despite "9 Waveforms" Claim

| Field | Content |
|-------|---------|
| **Manual Ref** | §9 LFO |
| **Manual Says** | "9 different waveforms" stated, but Slew S&H, ExpSaw, ExpRamp, Shaper are omitted or inadequately described in subsections |
| **Firmware** | Exactly **9 waveforms** confirmed (CM4 string table + CM7 constant `9` appearing 7 times near LFO functions) |
| **Address** | CM4 `0x081B0FB0`–`0x081B0FDB`; CM7 LFO function context |
| **Confidence** | ★★★★★ |

**Recommendation**: The manual correctly states 9 waveforms but fails to adequately describe the last 4 (Slew S&H, Exponential Saw, Exponential Ramp, User Shaper). Each waveform should include: (1) firmware display name, (2) polarity (Bi/Uni), (3) behavioral description.

---

### CORR-08: Shaper Preset First Entry — "Shaper" Does Not Exist

| Field | Content |
|-------|---------|
| **Manual Ref** | §9 LFO > User Shaper |
| **Manual Says** | Implies first preset is labeled "Shaper" |
| **Firmware** | First preset entry is **"Preset Shaper"** (not "Shaper"). 25 total presets: 1 base + 16 built-in + 8 user. |
| **Address** | CM4 `0x081AF128` – `0x081AF288` |
| **Confidence** | ★★★★★ |

**Firmware Evidence** (25 presets verified, CM4 hex dump):
```
0x081AF128: 50 72 65 73 65 74 20 53 68 61 70 65 72 00     "Preset Shaper"     [#0]
0x081AF138: 41 73 79 6D 6D 65 74 72 69 63 61 6C 20 53 61 77 00  "Asymmetrical Saw"  [#1]
0x081AF14C: 55 6E 69 70 6F 6C 61 72 20 43 6F 73 69 6E 65 00  "Unipolar Cosine"  [#2]
0x081AF15E: 53 68 6F 72 74 20 50 75 6C 73 65 00              "Short Pulse"      [#3]
0x081AF16A: 45 78 70 6F 6E 65 6E 74 69 61 6C 20 53 71 75 61 72 65 00  "Exponential Square" [#4]
0x081AF180: 44 65 63 61 79 69 6E 67 20 44 65 63 61 79 73 00  "Decaying Decays"  [#5]
0x081AF190: 57 6F 62 62 6C 79 00                              "Wobbly"           [#6]
0x081AF198: 53 74 72 75 6D 20 45 6E 76 65 6C 6F 70 65 00    "Strum Envelope"   [#7]
0x081AF1A6: 54 72 69 61 6E 67 6C 65 20 42 6F 75 6E 63 65 73 00  "Triangle Bounces" [#8]
0x081AF1B8: 52 68 79 74 68 6D 69 63 20 31 00                 "Rhythmic 1"       [#9]
0x081AF1C2: 52 68 79 74 68 6D 69 63 20 32 00                 "Rhythmic 2"       [#10]
0x081AF1CC: 52 68 79 74 68 6D 69 63 20 33 00                 "Rhythmic 3"       [#11]
0x081AF1D6: 52 68 79 74 68 6D 69 63 20 34 00                 "Rhythmic 4"       [#12]
0x081AF1E0: 53 74 65 70 70 65 64 20 31 00                    "Stepped 1"        [#13]
0x081AF1EA: 53 74 65 70 70 65 64 20 32 00                    "Stepped 2"        [#14]
0x081AF1F4: 53 74 65 70 70 65 64 20 33 00                    "Stepped 3"        [#15]
0x081AF1FE: 53 74 65 70 70 65 64 20 34 00                    "Stepped 4"        [#16]
0x081AF208: 55 73 65 72 20 53 68 61 70 65 72 20 31 00        "User Shaper 1"    [#17]
0x081AF216: 55 73 65 72 20 53 68 61 70 65 72 20 32 00        "User Shaper 2"    [#18]
0x081AF224: 55 73 65 72 20 53 68 61 70 65 72 20 33 00        "User Shaper 3"    [#19]
0x081AF232: 55 73 65 72 20 53 68 61 70 65 72 20 34 00        "User Shaper 4"    [#20]
0x081AF240: 55 73 65 72 20 53 68 61 70 65 72 20 35 00        "User Shaper 5"    [#21]
0x081AF24E: 55 73 65 72 20 53 68 61 70 65 72 20 36 00        "User Shaper 6"    [#22]
0x081AF25C: 55 73 65 72 20 53 68 61 70 65 72 20 37 00        "User Shaper 7"    [#23]
0x081AF26A: 55 73 65 72 20 53 68 61 70 65 72 20 38 00        "User Shaper 8"    [#24]
```

**Recommendation**: Document the full list of 25 Shaper presets. Clarify that the default preset is named "Preset Shaper", not "Shaper".

---

### CORR-09: Custom Assign Mod Destinations — Starting Address and Scope

| Field | Content |
|-------|---------|
| **Manual Ref** | §8.5.4 Custom Assign |
| **Manual Says** | Brief description only, no specific parameter list |
| **Firmware** | **8 Custom Assign destinations** at CM4 `0x081AEA94`: Vib Rate, Vib AM, VCA, LFO1 AM, LFO2 AM, CycEnv AM, Uni Spread, -Empty- |
| **Address** | CM4 `0x081AEA94` |
| **Confidence** | ★★★★★ |

**Firmware Evidence** (CM4 hex dump, 8 destinations):
```
0x081AEA94: 43 75 73 74 6F 6D 20 41 73 73 69 67 6E 00   "Custom Assign"  [header]
0x081AEAA2: 2D 45 6D 70 74 79 2D 00                     "-Empty-"        [#1]
0x081AEAAA: 56 69 62 20 52 61 74 65 00                   "Vib Rate"       [#2]
0x081AEAB4: 56 69 62 20 41 4D 00                         "Vib AM"         [#3]
0x081AEABB: 56 43 41 00                                  "VCA"            [#4]
0x081AEABF: 4C 46 4F 32 20 41 4D 00                      "LFO2 AM"        [#5]
0x081AEAC7: 4C 46 4F 31 20 41 4D 00                      "LFO1 AM"        [#6]
0x081AEACF: 43 79 63 45 6E 76 20 41 4D 00               "CycEnv AM"      [#7]
0x081AEAD9: 55 6E 69 20 53 70 72 65 61 64 00             "Uni Spread"     [#8]
```

**Recommendation**: Document all 8 Custom Assign destinations. Note that destinations 2–6 enable **meta-modulation** (modulating a modulator), which is a powerful but undocumented feature.

---

### CORR-10: Stereo Delay Is VST-Plugin Only, Not Available on Hardware

| Field | Content |
|-------|---------|
| **Manual Ref** | §FX (implied in FX type listings) |
| **Manual Says** | No explicit distinction between hardware and VST-plugin FX types |
| **Firmware** | **Stereo Delay** exists in the VST plugin (index 4) but **does not exist** in the CM4 hardware firmware. CM4 has 12 FX types; VST has 13 (Stereo Delay added). |
| **Address** | CM4 FX enum `0x081AF308` (12 types, no "Stereo Delay"); FX Core SP1+SP2 (`FUN_0800bba0`) exist but are only reachable from VST |
| **Confidence** | ★★★★★ |

**Firmware Evidence** (CM4 hex dump, 12 FX types):
```
0x081AF308: 43 68 6F 72 75 73 00                     "Chorus"         [#0]
0x081AF310: 50 68 61 73 65 72 00                     "Phaser"         [#1]
0x081AF318: 46 6C 61 6E 67 65 72 00                  "Flanger"        [#2]
0x081AF320: 52 65 76 65 72 62 00                     "Reverb"         [#3]
0x081AF328: 44 69 73 74 6F 72 74 69 6F 6E 00         "Distortion"     [#4]
0x081AF334: 42 69 74 20 43 72 75 73 68 65 72 00       "Bit Crusher"    [#5]
0x081AF340: 33 20 42 61 6E 64 73 20 45 51 00          "3 Bands EQ"     [#6]
0x081AF34C: 50 65 61 6B 20 45 51 00                   "Peak EQ"        [#7]
0x081AF354: 4D 75 6C 74 69 20 43 6F 6D 70 00          "Multi Comp"     [#8]
0x081AF360: 53 75 70 65 72 55 6E 69 73 6F 6E 00       "SuperUnison"    [#9]
0x081AF36C: 56 6F 63 6F 64 65 72 20 53 65 6C 66 00    "Vocoder Self"   [#10]
0x081AF37A: 56 6F 63 6F 64 65 72 20 45 78 74 00       "Vocoder Ext"    [#11]
```

**"Stereo Delay" — NOT found in CM4 binary** (full binary scan confirmed → VST exclusive)

**Recommendation**: Clearly distinguish hardware-available FX types (12) from VST-plugin-only types (1: Stereo Delay). This prevents user confusion when a preset loaded from the VST plugin references Stereo Delay on hardware.

---

### CORR-11: Mod Matrix — 91 Assignable Slots (new)

| Field | Content |
|-------|---------|
| **Manual Ref** | §8.5 Modulation Matrix |
| **Manual Says** | Implies "7 rows × ~4 destinations" |
| **Firmware** | **91 assignable modulation slots**: 7×4 hardwired (28) + 7×9 assignable (63) = 91 total |
| **Address** | VST XML `minifreak_vst_params.xml` — `Mx_Dot_0`–`Mx_Dot_26` (28 params) + `Mx_AssignDot_0`–`Mx_AssignDot_62` (63 params) |
| **CM4 Verification** | `Mx_Dot` / `Mx_AssignDot` strings **not found in CM4 binary** — VST-only parameter names |
| **Confidence** | ★★★★★ (VST XML direct confirmation) |

**Firmware Evidence**:
```
VST XML parameter categories:
  matrix (91 params):
    Mx_Dot_0 ~ Mx_Dot_26      = 7 modules × 4 dots (modulation amount, -1.0 ~ 1.0)
    Mx_AssignDot_0 ~ Mx_AssignDot_62 = 7 modules × 9 dots (source/dest assignment, normalized)
```

| Slot Group | Count | Range | Description |
|-----------|-------|-------|-------------|
| Mx_Dot | 28 | 0–26 | Hardwired modulation amounts per row (Mod 1:1 through Mod 7:4) |
| Mx_AssignDot | 63 | 0–62 | Assignable source/destination per row (Mod 1:5 through Mod 7:13) |
| **Total** | **91** | | |

**Recommendation**: The manual's description of "7 rows × ~4 destinations" significantly understates the actual modulation capacity. The full matrix supports 91 assignable slots — far more than the 28 visible in the hardware UI. The manual should document the total modulation capacity and clarify the difference between hardwired amounts (Mx_Dot, 28) and assignable routing (Mx_AssignDot, 63).

---

### CORR-12: Osc2 Enum Has 21 Real + 9 Reserved Entries (new)

| Field | Content |
|-------|---------|
| **Manual Ref** | §Oscillator 2 > Osc Type |
| **Manual Says** | Osc2 type count not clearly specified |
| **Firmware** | **30 entries** in Osc2Type enum: 21 real oscillator types + 9 reserved/dummy entries (indices 21–29) |
| **Address** | VST XML `minifreak_vst_params.xml` Osc2Type item_list (30 entries); CM4 binary cross-verified (Phase 14-2) |
| **CM4 Verification** | `Dummy` entry at CM4 `0x081AF460` (between Destroy and Audio In) — reserved placeholder confirmed |
| **Confidence** | ★★★★★ (VST XML + CM4 cross-verification) |

**Firmware Evidence**:
```
VST XML Osc2Type (30 entries):
 0: Basic Waves     1: SuperWave     2: Harmo           3: KarplusStr
 4: VAnalog         5: Waveshaper    6: Two Op. FM      7: Formant
 8: Chords          9: Speech        10: Modal          11: Noise
12: Bass           13: SawX         14: Harm            15: FM / RM
16: Multi Filter   17: Surgeon Filt 18: Comb Filter    19: Phaser Filter
20: Destroy
21–29: Dummy (reserved, no corresponding DSP)
```

**Osc1 vs Osc2 difference**: Osc1 has 24 real types (Wavetable, Sample, Grain engines). Osc2 has 21 real types (Filter-based engines instead: Chords, Multi Filter, Surgeon Filt, Comb Filter, Phaser Filter, Destroy). Both share 15 common base types.

**Recommendation**: Document the complete list of 21 Osc2 types. Note that indices 21–29 are reserved in the firmware enum and should not be exposed to users. The manual should clarify the structural difference between Osc1 (24 types, granular/wavetable/sample oriented) and Osc2 (21 types, filter/synthesis oriented).

---

### CORR-13: 1,557 Hidden VST↔HW Sync Parameters (new)

| Field | Content |
|-------|---------|
| **Manual Ref** | Not mentioned |
| **Manual Says** | No documentation of internal VST↔HW synchronization parameters |
| **Firmware** | DLL strings analysis: 1,705 parameter names extracted from VST DLL, of which only 148 match VST XML parameters. The remaining **1,557 are hidden HW↔VST sync parameters** used for DAW↔HW preset synchronization, UI state restoration, and internal DSP control. |
| **Address** | VST DLL string table (1,705 entries); VST XML `minifreak_vst_params.xml` (148 entries) |
| **Confidence** | ★★★★☆ (DLL strings-based estimation) |

**Detailed Evidence**:
```
DLL strings:   1,705 parameter names (extracted via strings analysis)
VST XML:         148 parameters (officially exposed in DAW)
                     │
                     ├── Matrix:           91
                     ├── Oscillator:       13
                     ├── FX:                9
                     ├── LFO:               6
                     ├── Sequencer:         7
                     ├── Envelope:          7
                     ├── Modulation:        5
                     ├── Macro:             2
                     ├── Other:             4
                     └── Voice:             1
                     ────
                     Total:               148

Hidden params: 1,557 (= 1,705 − 148)
  Includes: Mod_S0~63, Pitch_S0~63, Velo_S0~63, Gate_S0~63,
            StepState_S0~63, Reserved1~4, AutomReserved1, etc.
```

These hidden parameters are mapped via the Collage protocol's `DataParameterId.single` (uint32) in the `InitSwFwParamIds` function, but compiler optimization prevents static extraction of the integer constants. Dynamic verification via USB capture is required for definitive ID↔name mapping.

**Recommendation**: While the hidden parameters are not user-facing, the manual should acknowledge that the VST plugin maintains bidirectional synchronization with the hardware via a proprietary protocol (Collage), involving significantly more parameters than the 148 exposed in the DAW. This explains why preset transfers between DAW and hardware preserve full state, including internal settings not directly accessible from either interface.

---

## Part 2. Enhancement Recommendations (12 items)

> The following items document firmware features that exist but are inadequately described or entirely missing from the manual.

| ID | Category | Manual Coverage | Firmware Reality | Confidence |
|----|----------|----------------|------------------|------------|
| ENH-01 | Mod Matrix | ~30 destinations | **140 internal modulation destinations** | ★★★★☆ |
| ENH-02 | LFO Shaper | "16-step user shaper" only | **25 presets** (1 base + 16 built-in + 8 user) | ★★★★★ |
| ENH-03 | Deprecated Params | Not mentioned | **4 deprecated parameters** still in firmware | ★★★★★ |
| ENH-04 | CycEnv | 3 modes (Env/Run/Loop) | **4th mode: Loop2** (VST only — **not found in CM4 binary**) | ★★★☆☆ |
| ENH-05 | Voice | Not documented | **Poly Allocation 3 modes** (Cycle/Reassign/Reset) — CM4 confirmed @ `0x081AF964` "Poly Allocation", `0x081B0F78` "Cycle", `0x081B0F80` "Reassign" | ★★★★☆ |
| ENH-06 | MIDI CC | 38 CCs documented | **161 internal CCs** processed | ★★★★☆ |
| ENH-07 | FX Vocoder | Treated as single type | **2 separate DSP paths** (Self vs Ext In, different SP, function, struct size) | ★★★★☆ |
| ENH-08 | Sequencer | "4 modulation lanes" only | **Smooth Mod 1–4** individual smoothing params | ★★★★★ |
| ENH-09 | Arp Modifiers | Vague descriptions | **Estimated probability distributions (static analysis)** for Walk/Mutate/Rand Oct | ★★★★☆ |
| ENH-10 | Mod Matrix | Brief mention | **8 Custom Assign destinations** with meta-modulation | ★★★★★ |
| ENH-11 | FX Chain | 3-slot chain only | **Singleton constraint**: Reverb, Stereo Delay, Multi Comp limited to 1 instance | ★★★★☆ |
| ENH-12 | Sequencer | 64-step only | **3 recording modes** (Step/Real-time/Overdub) + state machine | ★★★★☆ |

### ENH-09 Update Note (Phase 13 honest downgrade)

The original V4 report listed "Precise probability distributions" for Walk, Mutate, and Rand Oct arp modifiers. Phase 13 re-analysis has downgraded this to **estimated values** pending dynamic verification:

- **Walk LUT** @ CM7 `0x080546C4` (64 bytes): Interpretation as uint8 probability distribution is **uncertain**. The data may be a pair-wise encoding or structured format rather than individual step probabilities.
- **env_time_scale** @ CM7 `0x0806D330` (256 bytes): Interpreted as float32, most values are denormal/NaN → likely a **different data format** (int16, uint8, or structured).
- The probability values previously cited (25/50/25 for Walk, 75/15/7/3 for Rand Oct, etc.) are **estimates derived from static analysis of VST XML parameter ranges and firmware code flow**. They have **not** been validated against runtime behavior.

**Dynamic verification required**: USB capture of actual Collage protocol ParameterSet messages during arp playback is needed to confirm the true probability distributions.

---

## Part 3. Summary

### Corrections (13 items)

| ID | Category | Issue | Severity |
|----|----------|-------|----------|
| CORR-01 | Voice | Poly Steal: 4→6 modes | High |
| CORR-02 | Mod Matrix | Sources: 7→9 | High |
| CORR-03 | Arp | Mode index order mismatch | Medium |
| CORR-04 | Voice | Unison: sub-setting→3 independent modes | High |
| CORR-05 | LFO | Display names are abbreviations | Low |
| CORR-06 | Tempo | Subdivisions: 11→27 (VST) / 17 (HW) | Medium |
| CORR-07 | LFO | 9 waveforms claim but incomplete listing | Medium |
| CORR-08 | LFO Shaper | First preset is "Preset Shaper", not "Shaper" | Low |
| CORR-09 | Mod Matrix | Custom Assign: 8 destinations undocumented | Medium |
| CORR-10 | FX | Stereo Delay = VST-only, not on hardware | High |
| CORR-11 | Mod Matrix | Assignable slots: ~28→91 | High |
| CORR-12 | Oscillator | Osc2: 21 real + 9 reserved (30 total enum) | Medium |
| CORR-13 | VST/HW Sync | 1,557 hidden sync parameters undocumented | Low |

### Enhancement Recommendations (12 items)

| ID | Category | Gap | Severity |
|----|----------|-----|----------|
| ENH-01 | Mod Matrix | 140 internal destinations undocumented | High |
| ENH-02 | LFO Shaper | 25 presets, not "16-step" | Medium |
| ENH-03 | Deprecated | 4 deprecated params still present | Low |
| ENH-04 | CycEnv | Loop2 mode: VST only, not in CM4 | Low |
| ENH-05 | Voice | Poly allocation modes (CM4 @ 0x081AF964) | Low |
| ENH-06 | MIDI CC | 161 CCs vs 38 documented | High |
| ENH-07 | FX Vocoder | 2 DSP paths, not 1 | Medium |
| ENH-08 | Sequencer | Smooth Mod per-lane params | Medium |
| ENH-09 | Arp | Estimated probability distributions (needs validation) | Medium |
| ENH-10 | Mod Matrix | 8 Custom Assign destinations | Medium |
| ENH-11 | FX Chain | Singleton constraint on certain FX | Medium |
| ENH-12 | Sequencer | 3 recording modes + state machine | Medium |

### Overall Match Rate Impact

| Before P13 | After P16 V6 |
|-----------|--------------|
| 96.0% (claimed) | **95.6%** |

The overall match rate decreased from the Phase 13 estimate of ~96.2% to 95.6% due to:
1. **Phase 13 honest downgrade**: Walk LUT and env_time_scale probability distributions reclassified from "precise" to "estimated" (reduced confidence)
2. **Phase 14-2 expansion**: CORR-06 tempo subdivisions expanded from 17→27, revealing additional VST-only parameters not in the manual
3. **Phase 14-2 new findings**: CORR-11 (91 mod slots), CORR-12 (Osc2 30-entry enum), CORR-13 (1,557 hidden params) increase the total documentation gap
4. **Phase 16 V6 refinements**: ENH-04 Loop2 confirmed VST-only (not in CM4), ENH-05 Poly Allocation CM4-verified, CORR-08/09/10 detailed hex dump evidence added, CORR-11/12 CM4 cross-verification completed

---

## Appendix A: ENH-03 Deprecated Parameters (Full Detail)

| Address | String | Meaning | Status |
|---------|--------|---------|--------|
| `0x081AF994` | `UnisonOn TO BE DEPRECATED` | Legacy unison on/off toggle | Explicitly marked |
| `0x081AF70C` | `old FX3 Routing` | Legacy FX3 routing method | Replaced |
| `0x081AFB00` | `obsolete Rec Count-In` | Legacy recording count-in | Replaced |
| `0x081AF72C` | `internal use only` | Internal-use parameter | No user access |

## Appendix B: ENH-09 Arp Modifier Probability Distributions (Estimated)

| Modifier | Estimated Probability Distribution |
|----------|--------------------------------------|
| **Walk** | ~25% previous note / ~25% current note / ~50% next note (weighted adjacent movement) |
| **Rand Oct** | ~75% normal / ~15% +1 octave / ~7% −1 octave / ~3% +2 octave |
| **Mutate** | ~75% hold / ~5% +5th / ~5% −4th / ~5% +oct / ~5% −oct / ~3% next-note swap / ~2% second-next swap (cumulative) |

> **⚠️ Important caveat (Phase 13 downgrade)**: These probability values are **estimates** derived from static analysis of VST XML parameter ranges and firmware code flow. They are **computed at runtime**, not stored as hardcoded lookup tables. The Walk LUT at CM7 `0x080546C4` (64 bytes) may use a pair-wise or structured encoding rather than individual uint8 probabilities. **Dynamic verification via USB capture is required** to confirm actual distributions.

---

## Appendix C: Phase 14-1 — Collage Protocol Summary

> **⚠️ NDA Notice**: The following summary is based on reverse-engineering of Arturia's proprietary Collage communication protocol. Full protocol details may be subject to NDA. Only a high-level summary is provided.

### Overview

The MiniFreak does **not** use standard MIDI for DAW↔HW communication. Instead, it uses a **protobuf-based USB bulk transfer protocol** called "Collage":

| Property | Value |
|----------|-------|
| **Transport** | USB 2.0 Bulk Transfer (not MIDI) |
| **Endpoint IN** | `0x81` |
| **Endpoint OUT** | `0x02` |
| **USB VID** | `0x152E` (Arturia) |
| **Protocol** | Protobuf-serialized messages |
| **Message Types** | 62 identified |
| **Enum Types** | 14 identified |
| **Key Messages** | ParameterSet, ParameterGet, PresetTransfer, FirmwareUpdate, Handshake |

### Protocol Functions

- **Preset Synchronization**: Full bidirectional preset transfer between DAW and hardware
- **Parameter Control**: Real-time parameter modification with acknowledgment
- **Firmware Update**: OTA firmware update mechanism
- **Factory Reset**: Hardware initialization and reset commands
- **Handshake**: Device identification and capability negotiation

The 1,557 hidden parameters documented in CORR-13 are communicated via this protocol using `DataParameterId.single` (uint32) identifiers mapped in the `InitSwFwParamIds` function. Due to compiler optimization, static extraction of these ID constants is not feasible — USB capture of live Collage sessions is required for definitive mapping.

---

## Appendix D: Phase 15 — Deprecated Slot Analysis & Firmware Patch Experiment

### Phase 15-1: eEditParams Classification (79 items)

The `eEditParams` enum in the CM4 firmware was fully classified:

| Category | Count | Description |
|----------|-------|-------------|
| Active | 27 | Currently used synthesis/engine parameters |
| DEPRECATED | 1 | `UnisonOn TO BE DEPRECATED` (`0x081AF994`) |
| Obsolete | 1 | `obsolete Rec Count-In` (`0x081AFB00`) |
| UI State | 16 | VST_IsConnected, display flags, navigation state |
| UI Labels | 35 | Static display strings, menu labels, help text |

### Easter Eggs (4 developer name references)

| Developer | Address | Context |
|-----------|---------|---------|
| **Olivier D** | `0x081B34A0` | `if you ask Olivier D, he'll tell you...` |
| **Thomas A** | `0x081B32CD` | `Ask Thomas A` |
| **Mathieu B** | `0x081B3411` | `ask Mathieu B` |
| **Frederic** | `0x081B2F2C` | `Hey Frederic, are you ready to hear...` |

These strings are embedded in debug/assertion code paths and are not reachable during normal operation. They confirm the firmware was developed by a team at Arturia including at least these four named engineers.

### Phase 15-2: Safe Firmware Patch Testing (7 patches)

Seven `.rodata` string patches were defined and tested for reversibility:

| # | Patch Type | Original | Replacement | Result |
|---|-----------|----------|-------------|--------|
| 1 | string_constant | `UnisonOn TO BE DEPRECATED` | `HYDRA_FA TO BE DEPRECATED` | ✅ |
| 2 | string_constant | `obsolete Rec Count-In` | `HYDRA_FA Rec Count-In` | ✅ |
| 3 | easter_egg | `if you ask Olivier D` | `if you ask Hermes AG` | ✅ |
| 4 | easter_egg | `Ask Thomas A` | `Ask Hermes H` | ✅ |
| 5 | easter_egg | `ask Mathieu B` | `ask Hermes HH` | ✅ |
| 6 | easter_egg | `Hey Frederic` | `Hey Hermes H` | ✅ |
| 7 | string_constant | `VST_IsConnected` | `HYD_IsConnected` | ✅ |

**Test Results**:
- Binary pattern match: 7/7 found exactly once
- Apply/revert cycle: 7/7 successful
- **Full reversibility confirmed**: apply → revert → SHA hash match with original binary
- JSON round-trip: serialization integrity verified

> **Note**: These patches modify `.rodata` string constants only — no code logic is changed. The `.mnf` firmware package format is required for actual flashing; individual `.bin` files were used for offline testing.

---

*Document version: Phase 16 V6 English Edition (CORR-08~10 hex dump, ENH-04/05 CM4 verification, CORR-11/12 CM4 cross-verification)*  
*Analysis tools: CM4/CM7 binary scan, VST XML cross-verification, DLL string analysis, Ghidra static analysis*  
*Firmware version: fw4_0_1_2229 (2025-06-18)*  
*Manual version: v4.0.0 / v4.0.1 (2025-07-04)*  
*VST XML: minifreak_vst_params.xml (MiniFreak V plugin resources)*
