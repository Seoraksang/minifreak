# MiniFreak CM4 — Phase 2-5: Preset & Parameter System Analysis

## Date: 2026-04-21
## Status: ✅ Complete

---

## 1. Preset Object Structure

**Total size: ~0xD40 bytes** (3392 bytes runtime object)

```c
struct Preset {
    /* === Header (16 bytes) === */
    uint16_t status;           // +0x00: modified/status flags
    uint16_t magic;            // +0x02: 0x410F (constant magic number)
    uint8_t  crc8;             // +0x04: checksum byte
    uint8_t  reserved_05[9];   // +0x05
    uint16_t flags_0E;         // +0x0E: 0x1A0000 (factory init flag)
    
    /* === Parameter Data (0xD00 = 3328 bytes) === */
    uint16_t params[0x680];    // +0x10: 1664 parameter values (uint16 each)
    
    /* === Runtime Pointers (after data) === */
    void*    storage_vtable;   // +0xD14: file read/write interface
    void*    seq_data_iface;   // +0xD18: sequencer data
    void*    wave_data_iface;  // +0xD1C: wavetable data  
    void*    patch_iface;      // +0xD20: patch data
    void*    storage2_iface;   // +0xD24: main storage (vtable ptr)
    void*    mod_iface;        // +0xD28: modulation interface
    uint16_t preset_slot;      // +0xD34: current slot number (1-256?)
};
```

## 2. CRC Checksum Algorithm

```python
def calc_preset_crc(data_bytes):
    """Calculate CRC8 for preset data (0xD00 bytes at offset +0x10)"""
    # Step 1: XOR all 32-bit words
    xor_val = 0
    for i in range(0, len(data_bytes), 4):
        word = struct.unpack_from('<I', data_bytes, i)[0]
        xor_val ^= word
    
    # Step 2: Fold to single byte
    crc = ~((xor_val >> 24) ^ (xor_val >> 16 & 0xFF) ^ 
            (xor_val >> 8 & 0xFF) ^ (xor_val & 0xFF)) & 0xFF
    return crc
```

## 3. Parameter Layout (within params[] array at +0x10)

| Index Range | Count | Description |
|-------------|-------|-------------|
| 0x00~0x03 | 4 | Header params (magic, flags) |
| 0x04 | 1 | CRC placeholder |
| 0x09~0x10 | 8 | Osc1 core parameters |
| 0x11~0x18 | 8 | Osc2 core parameters |
| 0x57~0x5F | 9 | Modulation routes (Spice/Dice) |
| 0x88~0x92 | 8 | Voice parameters (4 params × 2) |
| 0x10E | 1 | Osc1 type selector |
| 0x116 | 1 | Osc2 type selector |
| 0x13C~0x14E | 9 | Mod route destination assignments |

### Modulation Route Format (uint16)

```
Bits [15:12] = type tag (2 = active route)
Bits [11:0]  = destination parameter index (0x000~0x0FF)
  Values 2~7:   mapped to destination +0x0B
  Values 0xB~0x10: mapped to destination +0x02
```

## 4. MIDI CC → Parameter Mapping (161 CC numbers)

### Range Analysis

| CC Range | Count | Parameter Group |
|----------|-------|----------------|
| 1~6 | 6 | Oscillator 1 (type, color, shape, mod, target, unison) |
| 10~16 | 7 | Oscillator 2 (type, color, shape, mod, target, unison, ?) |
| 20~21 | 2 | Mixer (osc mix, noise level) |
| 24~27 | 4 | Filter part 1 (type, cutoff, resonance, env amount) |
| 29~32 | 4 | Filter part 2 (key track, drive, env dest, mod) |
| 38~50 | 13 | Envelopes (ADSR × 2 + VCA) |
| 53~57 | 5 | LFO 1 (rate, shape, amount, ?) |
| 60~62 | 3 | LFO 2 / Mod wheel |
| 71~79 | 9 | FX Group 1 |
| 86~186 | 101 | FX Group 2 / Extended params (continuous!) |
| 193~204 | 7 | Macros / Mod Matrix / Special |

### Total: 161 unique CC parameters

## 5. Preset Save/Load Operations

| Operation | Case | Function | Details |
|-----------|------|----------|---------|
| Load verify | 0 | Direct | CRC check + read from storage |
| Save | 1,2 | FUN_0816e7e0 | Save to slot (param_1+0xD34) |
| Direct access | 3 | — | No CRC check |
| Load slot | 4,5,6 | FUN_0816e9e8 | Load from named slot |
| Factory 3 | 7 | Inline | Init + fill 0xD00 + set magic |
| Factory 4 | 8 | Inline | Init + fill + remap params |
| Factory 5 | 9 | Inline | Init + fill + remap params |
| Write waves | 10 | FUN_081584ac×384 | Write 384 wavetable entries |
| Write seq | 10 | FUN_0815813c×31 | Write 31 sequencer steps |
| Write auto | 10 | FUN_081582f4×1536 | Write 1536 automation entries |
| Slot backup | 12,13 | FUN_0815862c | Save slot 7 or 8 |

## 6. Data Sub-Sections

### Wavetable Data
- **384 entries** (0x180) — wavetable sample points
- Read via FUN_081584ac (sequential access)

### Sequencer Steps  
- **31 entries** (0x1F) — step sequence data
- Read via FUN_0815813c (sequential access)

### Sequencer Automation
- **1536 entries** (0x600) — automation lane data
- Read via FUN_081582f4 (sequential access)

## 7. Parameter Enum Names (from RTTI strings)

```
eSynthParams    — Synthesis parameters (osc, filter, envelopes)
eFXParams       — Effects parameters  
eCtrlParams     — Control parameters (mod, macro)
eSeqParams      — Sequencer parameters (13 values: 0~12)
eSeqStepParams  — Sequencer step data (31 steps)
eSeqAutomParams — Sequencer automation (1536 entries)
eShaperParams   — Shaper/waveshaper parameters
```

## 8. Key Functions

| Address | Name | Description |
|---------|------|-------------|
| FUN_0816EBD8 | Preset::saveLoad | Preset save/load/verify dispatcher (14 cases) |
| FUN_08166810 | handleCC1 | Main MIDI CC handler (161 unique CCs) |
| FUN_08158A38 | handleCC2 | Secondary parameter handler (264 cases) |
| FUN_081812B4 | handleNRPN | SysEx/NRPN parameter handler (33 cases) |
| FUN_081639BC | handleParam | Parameter dispatch (20 cases) |
| FUN_08189904 | handleSeqArp | Sequencer/Arp handler (13 cases) |
| FUN_08181E0C | handleFX | FX parameter handler (98,970 chars!) |
| FUN_08157E44 | getPresetByte | Read byte from preset data |
| FUN_0816E7E0 | saveToSlot | Save preset to flash slot |
| FUN_0816E9E8 | loadFromSlot | Load preset from flash slot |

## 9. Related Findings

### Not nanopb!
Despite finding nanopb-related strings ("varint overflow", "invalid wire_type"), the preset data uses a **custom binary format** with:
- Fixed 0xD00 byte parameter block
- uint16 parameter values
- CRC8 checksum
- Magic number 0x410F

The nanopb strings likely come from a **different protocol** (possibly USB SysEx communication or firmware update).

### RTTI Rich Binary
The CM4 firmware has extensive RTTI information including full function signatures:
- `bool Preset::set(eSynthParams, Preset::value_t)`
- `Preset::value_t Preset::get(eSynthParams)`
- `void CvCalib::setCalibVcaClickValue(eVcfType, uint8_t, bool, uint16_t)`
- `MNF_Edit::value_t MNF_Edit::get(eEditParams)`
- `bool Settings::set(eSettingsParams, Settings::value_t)`
- etc.

This makes further reverse engineering significantly easier than typical stripped binaries.
