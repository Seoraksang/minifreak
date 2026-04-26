"""
MiniFreak Parameter Enum Tables
================================
Official enum definitions extracted from Arturia's minifreak_vst_params.xml
and MiniFreak V_actions.xml (VST plugin resource files).

These are the authoritative source — processorvalue directly maps to firmware indices.
Cross-verified against 512 factory .mnfx presets.
"""

import sys

# ═══════════════════════════════════════════════════════════════════
# OSCILLATOR TYPES — from minifreak_vst_params.xml
# ═══════════════════════════════════════════════════════════════════

# Osc1 Type — V2.9.0 (current firmware, 24 types)
# Source: Osc1_Type_V2.9.0 item_list
OSC1_ENGINES = {
    0: "Basic Waves",
    1: "SuperWave",
    2: "Harmo",
    3: "KarplusStr",
    4: "VAnalog",
    5: "Waveshaper",
    6: "Two Op. FM",
    7: "Formant",
    8: "Speech",
    9: "Modal",
    10: "Noise",
    11: "Bass",
    12: "SawX",
    13: "Harm",
    14: "Audio In",      # Osc1 only
    15: "Wavetable",     # Osc1 only
    16: "Sample",        # Osc1 only (V2.9+)
    17: "Cloud Grains",  # Osc1 only (V2.9+)
    18: "Hit Grains",    # Osc1 only (V2.9+)
    19: "Frozen",        # Osc1 only (V2.9+)
    20: "Skan",          # Osc1 only (V2.9+)
    21: "Particle",      # Osc1 only (V2.9+)
    22: "Lick",          # Osc1 only (V2.9+)
    23: "Raster",        # Osc1 only (V2.9+)
}

# Osc2 Type — V2.9.0 (current firmware, 30 slots, 21 real + 9 dummy)
# Source: Osc2_Type_V2.9.0 item_list
# Note: Dummy entries (21-29) are placeholder slots for future expansion
OSC2_ENGINES = {
    0: "Basic Waves",
    1: "SuperWave",
    2: "Harmo",
    3: "KarplusStr",
    4: "VAnalog",
    5: "Waveshaper",
    6: "Two Op. FM",
    7: "Formant",
    8: "Chords",        # Osc2 only
    9: "Speech",
    10: "Modal",
    11: "Noise",
    12: "Bass",
    13: "SawX",
    14: "Harm",
    15: "FM / RM",       # Osc2 only
    16: "Multi Filter",  # Osc2 only (audio processor)
    17: "Surgeon Filter", # Osc2 only (audio processor)
    18: "Comb Filter",   # Osc2 only (audio processor)
    19: "Phaser Filter", # Osc2 only (audio processor)
    20: "Destroy",       # Osc2 only (audio processor)
    # 21-29: Dummy (placeholder slots, not real engines)
}

# Oscillator classification
OSC1_ONLY = {14, 15, 16, 17, 18, 19, 20, 21, 22, 23}  # Audio In, Wavetable, Sample, 7 Granular
OSC2_ONLY = {8, 15, 16, 17, 18, 19, 20}  # Chords, FM/RM, 5 audio processors
OSC_COMMON = set(range(14))  # 0-13: shared engines

# ═══════════════════════════════════════════════════════════════════
# FILTER TYPES
# ═══════════════════════════════════════════════════════════════════

# Main analog filter (SEM-style, 12dB/oct) — hardware button, no CC
VCF_TYPES = {
    0: "Low Pass",   # LP
    1: "High Pass",  # HP
    2: "Band Pass",  # BP
}

# ═══════════════════════════════════════════════════════════════════
# FX TYPES — from MiniFreak V_actions.xml discrete_param_swapper
# ═══════════════════════════════════════════════════════════════════

# FX Type — 13 types, same for all 3 slots (FX1, FX2, FX3)
# Source: MiniFreak V_actions.xml FX Swapper proxy_param order
FX_TYPES = {
    0: "Chorus",
    1: "Phaser",
    2: "Flanger",
    3: "Reverb",        # Singleton (max 1 across 3 slots)
    4: "Stereo Delay",  # Singleton (max 1 across 3 slots)
    5: "Distortion",
    6: "Bit Crusher",
    7: "3 Bands EQ",
    8: "Peak EQ",
    9: "Multi Comp",    # Singleton (max 1 across 3 slots)
    10: "Super Unison",
    11: "Vocoder Self", # V4.0+
    12: "Vocoder Ext In", # V4.0+
}

FX_SINGLETONS = {3, 4, 9}  # Reverb, Delay, MultiComp — only one allowed

# ═══════════════════════════════════════════════════════════════════
# LFO WAVEFORMS — from minifreak_vst_params.xml
# ═══════════════════════════════════════════════════════════════════

# LFO Wave — 9 waveforms, same for LFO1 and LFO2
# Source: LFO1_Wave and LFO2_Wave item_list
LFO_WAVES = {
    0: "Sin",       # Sine — bipolar
    1: "Tri",       # Triangle — bipolar
    2: "Saw",       # Sawtooth (falling) — bipolar
    3: "Sqr",       # Square — bipolar
    4: "SnH",       # Sample and Hold — bipolar
    5: "SlewSNH",   # Slew-limited S&H — bipolar
    6: "ExpSaw",    # Exponential sawtooth — unipolar
    7: "ExpRamp",   # Exponential ramp — unipolar
    8: "Shaper",    # User-drawn (16 steps) — special
}

LFO_UNIPOLAR = {6, 7}  # ExpSaw, ExpRamp

# ═══════════════════════════════════════════════════════════════════
# ARPEGGIATOR MODES — from minifreak_vst_params.xml
# ═══════════════════════════════════════════════════════════════════

ARP_MODES = {
    0: "Up",
    1: "Down",
    2: "UpDown",
    3: "Random",
    4: "Walk",
    5: "Pattern",
    6: "Order",
    7: "Poly",
}

# ═══════════════════════════════════════════════════════════════════
# VOICE MODES — from .mnfx data + manual
# ═══════════════════════════════════════════════════════════════════

# Gen_NoteMode — 5 values observed in .mnfx
# Index mapping from float quantization: value ≈ i/5
# Index 1 not observed in factory presets
VOICE_MODES = {
    # Index 1 intentionally skipped (deprecated in firmware)
    0: "Poly",     # Polyphonic
    2: "Mono",     # Monophonic (glide + legato)
    3: "Unison",   # Unison (2-6 voices)
    4: "Para",     # Paraphonic (12 voices, 6 pairs)
    5: "Dual",     # Dual mode (if index 1 maps here)
}

# Gen_UnisonMode — 3 values
UNISON_MODES = {
    0: "Mono",     # Unison mono
    1: "Poly",     # Unison poly
    2: "Para",     # Unison paraphonic
}

# Gen_PolyAlloc — 3 values
POLY_ALLOC_MODES = {
    0: "Cycle",       # Round-robin
    1: "Reassign",    # Keep voice assignment
    2: "Reset",       # Reset on new note
}

# Gen_PolySteal — 3 values
POLY_STEAL_MODES = {
    # VST XML: 3 modes (None/Once/Cycle). Firmware CM4: 6 modes (below).
    # "Once" removed in firmware; Velocity/Aftertouch/Velo+AT added.
    0: "None",
    1: "Cycle",       # VST index 2
    2: "Reassign",    # firmware-only
    3: "Velocity",    # firmware-only
    4: "Aftertouch",  # firmware-only
    5: "Velo + AT",   # firmware-only
}

# Gen_LegatoMode — 2 values
LEGATO_MODES = {
    0: "Off",
    1: "On",
}

# Gen_RetrigMode — 2 values
RETRIG_MODES = {
    0: "Env Reset",     # Restart envelope
    1: "Env Continue",  # Continue envelope
}

# ═══════════════════════════════════════════════════════════════════
# CYCLING ENVELOPE — from .mnfx data + manual
# ═══════════════════════════════════════════════════════════════════

# CycEnv_Mode — 4 values
CYCENV_MODES = {
    0: "Env",    # Envelope mode (triggered)
    1: "Run",    # Run mode (one-shot)
    2: "Loop",   # Loop mode
    3: "Loop2",  # Alternative loop mode
}

# ═══════════════════════════════════════════════════════════════════
# QUANTIZATION N VALUES
# ═══════════════════════════════════════════════════════════════════
# .mnfx stores enum values as float32 ≈ (index / N).
# Default: N = max(table.keys()), but some tables need explicit N
# because their values are quantized at a higher N than max_key.
#
# Determined by cross-validation against 512 factory presets:
# - VCF_TYPES: 3 entries but stored as i/6 (not i/2)
#
# Note: Osc1/Osc2/FX values have VST normalization offsets,
# but round(v * max_key) still returns correct indices for all
# factory presets, so explicit N is not needed for those.

ENUM_QUANT_N = {
    'VCF_TYPES': 6,
}


def _enum_name(table: dict) -> str:
    """Get the global variable name of an enum table dict."""
    for name, obj in list(sys.modules[__name__].__dict__.items()):
        if obj is table:
            return name
    return ''

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def enum_lookup(table: dict, value: float, n: int = None) -> str:
    """Map a float value from .mnfx to an enum name.
    
    .mnfx stores enum values as float32 of (index / N).
    If n is not provided, looks up ENUM_QUANT_N[table] for the correct N.
    Falls back to max(table.keys()) if no explicit N is registered.
    """
    if n is None:
        n = ENUM_QUANT_N.get(_enum_name(table), max(table.keys()))
    idx = round(value * n)
    idx = max(0, min(idx, max(table.keys())))
    return table.get(idx, f"Unknown({idx})")

def enum_reverse(table: dict, name: str, n: int = None) -> float:
    """Map an enum name back to float value for .mnfx storage."""
    if n is None:
        n = ENUM_QUANT_N.get(_enum_name(table), max(table.keys()))
    for idx, val in table.items():
        if val.lower() == name.lower():
            import struct
            return struct.unpack('f', struct.pack('f', idx / n))[0]
    raise ValueError(f"Unknown enum name: {name}")
