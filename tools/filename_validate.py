#!/usr/bin/env python3
"""
Cross-validate enum names against preset filenames.
Preset names often contain engine type hints.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.mnfx_editor import MnfxParser
from tools.mf_enums import enum_lookup, OSC1_ENGINES, OSC2_ENGINES, FX_TYPES, LFO_WAVES
from pathlib import Path
import re

base = Path('reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory')
files = sorted(base.glob('*.mnfx'))

# Build keyword → expected enum mapping
KEYWORD_MAP = {
    # Osc1 engine keywords
    'wavetable': ('Osc1_Type', 'Wavetable'),
    'sample': ('Osc1_Type', 'Sample'),
    'granular': ('Osc1_Type', None),  # could be any granular
    'cloud': ('Osc1_Type', 'Cloud Grains'),
    'grain': ('Osc1_Type', None),  # generic
    'frozen': ('Osc1_Type', 'Frozen'),
    'skan': ('Osc1_Type', 'Skan'),
    'lick': ('Osc1_Type', 'Lick'),
    'raster': ('Osc1_Type', 'Raster'),
    'particle': ('Osc1_Type', 'Particle'),
    'karplus': ('Osc1_Type', 'KarplusStr'),
    'pluck': ('Osc1_Type', 'KarplusStr'),
    'fm': ('Osc1_Type', 'Two Op. FM'),
    'formant': ('Osc1_Type', 'Formant'),
    'speech': ('Osc1_Type', 'Speech'),
    'chord': ('Osc1_Type', 'Chords'),
    'noise': ('Osc1_Type', 'Noise'),
    'bass': ('Osc1_Type', None),  # could be engine or category
    'saw': ('Osc1_Type', None),  # could be many
    'va ': ('Osc1_Type', 'VAnalog'),
    'virtual': ('Osc1_Type', 'VAnalog'),
    'analog': ('Osc1_Type', 'VAnalog'),
    'wavefolder': ('Osc1_Type', 'Waveshaper'),
    'waveshape': ('Osc1_Type', 'Waveshaper'),
    'harmo': ('Osc1_Type', 'Harmo'),
    'harm': ('Osc1_Type', None),
    'super': ('Osc1_Type', 'SuperWave'),
    'modal': ('Osc1_Type', 'Modal'),
    'strings': ('Osc1_Type', 'Strings'),
    'audio': ('Osc1_Type', 'Audio In'),
}

# Also check FX keywords
FX_KEYWORDS = {
    'chorus': 'Chorus',
    'phaser': 'Phaser',
    'flanger': 'Flanger',
    'reverb': 'Reverb',
    'delay': 'Stereo Delay',
    'disto': 'Disto',
    'crush': 'BitCrusher',
    'eq': 'EQ3',
    'comp': 'MultiComp',
    'unison': 'SuperUnison',
    'vocoder': None,
}

errors = 0
verified = 0

for f in files:
    p = MnfxParser(f.read_bytes())
    if not p.params:
        continue
    
    name = f.stem.lower()
    
    for keyword, (param, expected) in KEYWORD_MAP.items():
        if keyword in name and param in p.params:
            v = float(p.params[param])
            actual = enum_lookup(OSC1_ENGINES, v)
            if expected and expected not in actual:
                errors += 1
                print(f"  ❌ {f.stem}: keyword='{keyword}', expected={expected}, got={actual}")
            elif expected:
                verified += 1

print(f"\nVerified: {verified}, Errors: {errors}")
if errors == 0 and verified > 0:
    print("✅ All filename hints match enum mapping!")
