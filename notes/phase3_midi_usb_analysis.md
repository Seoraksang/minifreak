# MiniFreak CM4 — Phase 3: MIDI/USB Protocol Analysis

## Date: 2026-04-21
## Status: ✅ Complete

---

## 1. Arturia SysEx Protocol

### Manufacturer ID
- **Long form**: `0x00 0x20 0x6B` (Arturia)
- **Short form**: `0x1C 0x75` (USB VID)

### Wire Format

```
F0 00 20 6B [device_id] [msg_type] [param_idx] [value_lo] [value_hi?] [payload...] F7
│  │  │  │   │          │           │            │           │            │
│  │  │  │   │          │           │            │           │            └─ 7-bit packed data
│  │  │  │   │          │           │            │           └─ present if type in {3,4,7,11,12,13}
│  │  │  │   │          │           │            └─ low 7 bits of value
│  │  │  │   │          │           └─ parameter index (0x00–0x7F)
│  │  │  │   │          └─ message type (2–37)
│  │  │  │   └─ device ID (0x00–0x7F, 0x7F = broadcast, 9 = extended mode)
│  │  │  └─ 0x6B (Arturia byte 3)
│  │  └─ 0x20 (Arturia byte 2)
│  └─ 0x00 (Arturia byte 1)
└─ 0xF0 (SysEx Start)
```

### State Machine Parser (0x08157278)

Byte-by-byte parser with **43 states** (TBH dispatch). State transitions:

| Byte Pos | Expected | State Transition |
|----------|----------|-----------------|
| [0] | F0 | → state 1 |
| [1] | 0x00 | 1→2 (also 0x7E→state31, 0x5A→state37) |
| [2] | 0x20 | 2→3 |
| [3] | 0x6B | 3→4 |
| [4] | device_id | 4→5 (dev_id=9→extended mode) |
| [5] | msg_type | 5→6 (0x42→special override to 0x26) |
| [6] | param_idx | 6→7 |
| [7] | value_lo | 7→8 |
| [8] | value_hi | 8→9 (optional, depends on msg_type) |

### State Struct Layout

```
[r0+0x00] state byte
[r0+0x01] sub-state (4 = needs 2-byte value)
[r0+0x02] expected device ID
[r0+0x04] buffer position / data length
[r0+0x06] sequence counter
[r0+0x08] message type (signed byte)
[r0+0x09] parameter index
[r0+0x0A] value byte
[r0+0x0C] 16-bit value
[r0+0x0E] bank/offset
[r0+0x0F] extra value byte
[r0+0x11–0x14] data bytes
[r0+0x15..] data buffer (~96 bytes)
[r0+0x7A] Arturia ID (0x096B2000)
[r0+0xAA] firmware data count
[r0+0xAB] firmware chunk counter
[r0+0xB4] callback pointer (MIDI send)
```

### Message Types (2–37)

| Type | Handler | Behavior |
|------|---------|----------|
| 2 | 0x08157672 | Counter-based — stores sequence byte |
| 3–9 | 0x08157434 | Standard → payload collection (state 0x21) |
| 10 | 0x08157672 | Counter-based (special) |
| 11 | 0x08157434 | Standard payload |
| 12 | 0x08157672 | Counter-based |
| 13–32 | 0x08157434 | Standard payload |
| 33 | 0x08157672 | Counter-based |
| 34 | 0x08157434 | Standard |
| 35 | 0x08157672 | Counter-based |
| 36–37 | mixed | Alternating |

**Two handler categories:**
1. **Standard** → transitions to state 0x21 (collect payload bytes)
2. **Counter-based** → stores counter, resets (acknowledgment messages?)

### Two-Byte Value Types (mask 0x0C13)

Message types requiring 2-byte values: **3, 4, 7, 11, 12, 13**

### SysEx Builder Functions

#### Builder 1 (0x0813D8C4) — 6-Parameter Format
```
Header: F0 00 20 6B [dev_id] [counter] [type=0x48] [sub=0x03]
Data:   [sign_bits] [p0&0x7F] [p1&0x7F] [p2&0x7F] [p3&0x7F] [p4&0x7F] [p5&0x7F]
```
Sign bits: bit6=p0, bit5=p1, bit4=p2, bit3=p3, bit2=p4, bit1=p5

#### Builder 2 (0x08135100) — Alternative Format
Same as Builder 1 but sub-type = `0x10` instead of `0x40`

#### Minimal Sender (0x08157BB8)
```
F0 03 06 00 06 02 [data1] [data2] F7
```

### 7-bit Unpacking Algorithm (msg_type 6)

Reconstructs 8-bit values from 7-bit MIDI bytes:
- Extracts high bits from sign-byte
- ORs into corresponding data bytes

---

## 2. Key Functions

| Address | Name | Description |
|---------|------|-------------|
| 0x08157278 | sysex_state_machine | Byte-by-byte SysEx parser (43 states) |
| 0x0815770C | sysex_dev9_handler | Extended mode for device_id=9 |
| 0x0815747A | sysex_dispatch | PC-relative msg_type dispatch (types 2–37) |
| 0x08157810 | midi_input_handler | High-level SysEx receiver (checks 0x49) |
| 0x0813D8C4 | sysex_builder_6param | Build 6-param SysEx (header 0x4003) |
| 0x08135100 | sysex_builder_alt | Build alt SysEx (header 0x1003) |
| 0x08157BB8 | sysex_send_minimal | Short SysEx send |
| 0x0813D4E0 | sysex_data_unpack | Unpack parameter data (TBB on byte>>4) |
| 0x08166810 | midi_cc_handler | CC → parameter mapping (161 CCs) |
| 0x08158A38 | midi_handler_2 | Secondary parameter handler |
| 0x081812B4 | nrpn_handler | NRPN parameter handler |
| 0x08189904 | seq_arp_handler | Sequencer/Arp handler |

---

## 3. Detailed MIDI CC → Parameter Mapping

### OSC1 (CC 1–6)
| CC | Hex | Parameter |
|----|-----|-----------|
| 1 | 0x01 | Osc1 Type/Waveform |
| 2 | 0x02 | Osc1 Shape/PWM |
| 3 | 0x03 | Osc1 Unison |
| 4 | 0x04 | Osc1 Unison Detune |
| 5 | 0x05 | Osc1 Octave |
| 6 | 0x06 | Osc1 Semitone |

### OSC2 (CC 10–16)
| CC | Hex | Parameter |
|----|-----|-----------|
| 10 | 0x0A | Osc2 Type/Waveform |
| 11 | 0x0B | Osc2 Shape/PWM |
| 12 | 0x0C | Osc2 Unison |
| 13 | 0x0D | Osc2 Unison Detune |
| 14 | 0x0E | Osc2 Octave |
| 15 | 0x0F | Osc2 Semitone |
| 16 | 0x10 | Osc2 Amount/Mix |

### Mixer (CC 20–21)
| CC | Hex | Parameter |
|----|-----|-----------|
| 20 | 0x14 | Osc1 Level |
| 21 | 0x15 | Osc2 Level |

### Filter (CC 24–32)
| CC | Hex | Parameter |
|----|-----|-----------|
| 24 | 0x18 | Filter Cutoff |
| 25 | 0x19 | Filter Resonance |
| 26 | 0x1A | Filter Env Amount |
| 27 | 0x1B | Filter Key Tracking |
| 29 | 0x1D | Filter Type |
| 30 | 0x1E | Filter Drive |
| 31 | 0x1F | Filter Env Velocity |
| 32 | 0x20 | Filter Cutoff 2 |

### Envelope 1 (CC 38–44)
| CC | Hex | Parameter |
|----|-----|-----------|
| 38 | 0x26 | Env1 Attack |
| 39 | 0x27 | Env1 Decay |
| 40 | 0x28 | Env1 Sustain |
| 41 | 0x29 | Env1 Release |
| 42 | 0x2A | Env1 Time |
| 43 | 0x2B | Env1 Loop |
| 44 | 0x2C | Env1 Velocity |

### Envelope 2 (CC 45–50)
| CC | Hex | Parameter |
|----|-----|-----------|
| 45 | 0x2D | Env2 Attack |
| 46 | 0x2E | Env2 Decay |
| 47 | 0x2F | Env2 Sustain |
| 48 | 0x30 | Env2 Release |
| 49 | 0x31 | Env2 Time |
| 50 | 0x32 | Env2 Velocity |

### LFO1 (CC 53–57)
| CC | Hex | Parameter |
|----|-----|-----------|
| 53 | 0x35 | LFO1 Rate |
| 54 | 0x36 | LFO1 Shape |
| 55 | 0x37 | LFO1 Amount |
| 56 | 0x38 | LFO1 Phase |
| 57 | 0x39 | LFO1 Sync |

### LFO2/Mod (CC 60–62)
| CC | Hex | Parameter |
|----|-----|-----------|
| 60 | 0x3C | LFO2/Mod Rate |
| 61 | 0x3D | LFO2/Mod Shape |
| 62 | 0x3E | LFO2/Mod Amount |

### FX A (CC 71–79)
| CC | Hex | Parameter |
|----|-----|-----------|
| 71 | 0x47 | FX A Type |
| 72 | 0x48 | FX A Param 1 |
| 73 | 0x49 | FX A Param 2 |
| 74 | 0x4A | FX A Param 3 |
| 75 | 0x4B | FX A Param 4 |
| 76 | 0x4C | FX A Param 5 |
| 77 | 0x4D | FX A Param 6 |
| 78 | 0x4E | FX A Param 7 |
| 79 | 0x4F | FX A Param 8 |

### FX Extended (CC 86–186)
101 consecutive FX parameters indexed as `FX_Param[CC-86]`.  
CC #95 (0x5F) calls `FUN_0817c670(state, CC - 0x57)` — FX dispatcher.

### Macros/Mod Matrix (CC 193–204)
| CC | Hex | Parameter |
|----|-----|-----------|
| 193 | 0xC1 | Macro 1 |
| 195 | 0xC3 | Macro 2 |
| 196 | 0xC4 | Macro 3 |
| 197 | 0xC5 | Macro 4 |
| 198 | 0xC6 | Macro 5 |
| 202 | 0xCA | Macro 6 |
| 204 | 0xCC | Macro 7 |

**Total: 161 unique CC parameters**

---

## 4. USB Device Configuration

### Device Descriptor (0x081B7528)
```
bcdUSB:           0x0201 (USB 2.01)
bDeviceClass:     0x00 (composite)
bMaxPacketSize0:  64 bytes
idVendor:         0x1C75 (Arturia)
idProduct:        0x0602 (MiniFreak)
bcdDevice:        0x4001 (firmware 4.0.1)
iManufacturer:    1
iProduct:         2
iSerial:          3
bNumConfigurations: 1
```

### Configuration Descriptor (0x081B759C)
```
wTotalLength:     142 bytes
bNumInterfaces:   4
bmAttributes:     0xC0 (bus-powered)
MaxPower:         0mA (self-powered)
```

### Interface #0 — Vendor-Specific (Proprietary Protocol)
```
Class:           0xFF (Vendor-specific)
SubClass:        0x00
Protocol:        0x00
Endpoints:       2
  EP 0x83 (IN3):  Bulk, 64 bytes, interval=0
  EP 0x04 (OUT4): Bulk, 64 bytes, interval=1
→ Arturia proprietary preset sync / firmware update / VST communication
```

### Interface #1 — WINUSB (Misc)
```
Class:           0xFE (Misc)
SubClass:        0x01
Protocol:        0x02
Endpoints:       0
WINUSB descriptor: 09 21 0B FF 00 40 00 10 01
→ WINUSB interface for driver update / DFU
```

### Interface #2 — Audio Control
```
Class:           0x01 (Audio)
SubClass:        0x01 (Audio Control)
Protocol:        0x00
Endpoints:       0
CS_INTERFACE:    MIDI_HEADER bcdMSC=0x0901
→ Audio Class Control header (no endpoints)
```

### Interface #3 — MIDI Streaming
```
Class:           0x01 (Audio)
SubClass:        0x03 (MIDI Streaming)
Protocol:        0x00
CS_INTERFACE:    MIDI_HEADER bcdMSC=0x4101
MIDI Jacks:
  IN:  EMBEDDED #1, EXTERNAL #2
  OUT: EMBEDDED #3, EXTERNAL #4
Endpoints:       2
  EP 0x02 (OUT2): Bulk, 64 bytes → MIDI Out to host
  EP 0x81 (IN1):  Bulk, 64 bytes → MIDI In from host
CS_ENDPOINT:     Associated with EP 0x02 and 0x81
→ Standard USB MIDI Class compliant
```

### USB String Descriptors Found
```
"MIDI>Syn"         — MIDI sync input
"MNF_MidiOut"      — MIDI output handler
"MIDI Seq/Synth"   — Sequencer/Synth MIDI routing
"MIDI To"           — MIDI output
"MIDI From"         — MIDI input
"SyncMidiIn"        — MIDI sync input
"SyncMidiOut"       — MIDI sync output
"MiniFreak"         — Device name
"MiniFreak MIDI"    — MIDI interface
"MiniFreak VST"     — VST plugin interface
"MiniFreak MIDI 3 In"  — Multi-port MIDI
"MiniFreak MIDI 3 Out" — Multi-port MIDI  
"MiniFreak MIDI 4 In"  — Multi-port MIDI
"MiniFreak MIDI 4 Out" — Multi-port MIDI
```

### MIDI Routing Modes
```
"USB Only"
"MIDI DIN Only"
"USB and MIDI DIN"
```

---

## 5. Special Protocol Features

- **Universal SysEx (0x7E)**: State 0x1F handler
- **Special byte 0x5A**: Firmware chunk counter (state 0x25)
- **Device ID 0x7F**: Broadcast (universal)
- **Device ID 9**: Extended data collection mode (47 bytes max)
- **Message type 0x42**: Override to extended type 0x26
- **Secondary Arturia check**: byte[7] == 0x49 in MIDI input handler

---

## 6. Easter Eggs 🥚
```
"SUPERCALIFRAGILISTICMINIFREAKOUS"
"I am MiniFreak, fluent in over 6,000,000 forms of madness."
"sometimes your MiniFreak is just having a really good day."
"The MiniFreak is as reliable as it is powerful, but it suffers from high recoil."
"If a machine, a MiniFreak, can learn the value of human life, maybe we can, too."
"I need your clothes, your boots, and your MiniFreak,"
```
