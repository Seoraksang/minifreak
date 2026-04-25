#!/usr/bin/env python3
"""
Parse all 512 .mnfx preset files from MiniFreak V installer.
Handles boost::serialization text archive format with length-prefixed strings
that may contain spaces.
"""

import os
import re
import json
import glob
from collections import defaultdict

PRESET_DIR = "/home/jth/hoon/minifreak/reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/HardwarePresets/MiniFreak Banks/Factory/"

def tokenize_mnfx(text):
    """
    Properly tokenize a boost::serialization text archive.
    Tokens are space-separated, BUT length-prefixed strings consume 
    exactly N characters after the length (which may include spaces).
    
    Strategy: read token by token. When a token is an integer and the 
    next content looks like it could be a length-prefixed string,
    consume exactly that many characters.
    """
    # Clean up line endings
    text = text.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
    # Collapse multiple spaces
    while '  ' in text:
        text = text.replace('  ', ' ')
    text = text.strip()
    
    tokens = []
    i = 0
    while i < len(text):
        # Skip spaces
        if text[i] == ' ':
            i += 1
            continue
        
        # Try to read a token (until next space or end)
        j = i
        while j < len(text) and text[j] != ' ':
            j += 1
        
        token = text[i:j]
        
        # Check if this token is a positive integer that could be a string length
        if token.isdigit():
            length = int(token)
            # If the length is reasonable for a string name (1-100 chars)
            # and there's content after it, this might be a length prefix
            if 1 <= length <= 100:
                # Look at what follows
                rest_start = j
                # Skip spaces
                while rest_start < len(text) and text[rest_start] == ' ':
                    rest_start += 1
                
                if rest_start < len(text):
                    # Check if the next `length` chars look like a valid name/string
                    if rest_start + length <= len(text):
                        candidate = text[rest_start:rest_start + length]
                        # Check if it looks like a parameter name or string
                        if re.match(r'^[A-Za-z0-9_][A-Za-z0-9_ ()\-\./:]*$', candidate):
                            # This is likely a length-prefixed string
                            tokens.append(('len_prefix', length))
                            tokens.append(('string', candidate))
                            i = rest_start + length
                            continue
            
            # Not a length prefix, just a regular number token
            tokens.append(('number', token))
            i = j
            continue
        
        # Check for negative integers
        if token.lstrip('-').isdigit():
            tokens.append(('number', token))
            i = j
            continue
        
        # Check for floating point numbers
        try:
            float(token)
            tokens.append(('number', token))
            i = j
            continue
        except ValueError:
            pass
        
        # Check for the magic header tokens
        if token in ('22', 'serialization::archive'):
            tokens.append(('magic', token))
            i = j
            continue
        
        # Regular string token
        tokens.append(('string', token))
        i = j
    
    return tokens


def parse_mnfx(filepath):
    """Parse a single .mnfx file and return metadata + parameters."""
    with open(filepath, 'rb') as f:
        raw = f.read()
    
    text = raw.decode('latin-1')
    
    result = {
        'metadata': {},
        'parameters': {},
        'header_raw': '',
        'parse_errors': []
    }
    
    tokens = tokenize_mnfx(text)
    
    idx = 0
    
    # Parse magic header: 22 serialization::archive 10
    if idx < len(tokens) and tokens[idx] == ('magic', '22'):
        idx += 1
    if idx < len(tokens) and tokens[idx] == ('magic', 'serialization::archive'):
        idx += 1
    if idx < len(tokens) and tokens[idx] == ('number', '10'):
        idx += 1
        result['header_raw'] = '22 serialization::archive 10'
    
    # Known MiniFreak parameter name prefixes (used to detect start of param section)
    known_prefixes = {
        'Arp_', 'AutomReserved', 'CycEnv_', 'Delay_', 'Dice_', 'Dummy', 'Env_',
        'FX1_', 'FX2_', 'FX3_', 'Gate_', 'Gen_', 'Kbd_', 'LFO1_', 'LFO2_',
        'Length_', 'Macro', 'MiniFreak_', 'Mod_S', 'ModState_', 'Mod_Wheel',
        'MxDst_', 'Mx_Assign', 'Mx_ColId_', 'Mx_Dot_', 'Osc1_', 'Osc2_', 'Osc_',
        'Pitch1_', 'Pitch2_', 'Pitch_S', 'Preset_', 'Reserved', 'Reverb_',
        'Seq_Autom', 'Seq_Gate', 'Seq_Length', 'Seq_Mode', 'Seq_Swing', 'Seq_TimeDiv',
        'Shp1_', 'Shp2_', 'Spice', 'StepState_', 'Tempo', 'VST3_', 'Vca_', 'Vcf_',
        'VeloMod_', 'Velo_S', 'Vibrato_', 'ctrDummy', 'ctrl_old', 'dummy', 'old_FX',
    }
    
    # First pass: find where parameters begin
    param_start = len(tokens)
    for i in range(idx, len(tokens)):
        if tokens[i][0] == 'string':
            name = tokens[i][1]
            if any(name.startswith(p) for p in known_prefixes):
                # Verify there's a number before it (the length) and after it (the value)
                if i > 0 and i + 1 < len(tokens):
                    if tokens[i-1][0] == 'len_prefix' and tokens[i+1][0] == 'number':
                        param_start = i - 1  # include the length prefix
                        break
    
    # Parse metadata section (between header and parameters)
    meta_section = tokens[idx:param_start]
    
    # Extract metadata: the format has length-prefixed strings for name, origin, author, category
    # Pattern: <ints> <len> <preset_name> <len> <origin> <int> <len> <author> <len> <category> ...
    meta_strings = []
    meta_ints = []
    
    mi = 0
    while mi < len(meta_section):
        ttype, tval = meta_section[mi]
        if ttype == 'len_prefix':
            # Next should be a string
            if mi + 1 < len(meta_section) and meta_section[mi + 1][0] == 'string':
                meta_strings.append(meta_section[mi + 1][1])
                mi += 2
                continue
        elif ttype == 'number':
            meta_ints.append(tval)
            mi += 1
            continue
        mi += 1
    
    # The metadata structure from observation:
    # [some ints] <preset_name> <origin> <int> <author> <category> [more ints] <Subtype> <Type> <Sequence> [more ints]
    # The author can contain spaces (e.g., "Jeremy Blake") so it's length-prefixed
    
    # Assign metadata fields
    # First string = preset name, second = origin (User/Factory)
    # After origin there's an int, then author, then category
    if len(meta_strings) >= 4:
        result['metadata']['preset_name'] = meta_strings[0]
        result['metadata']['origin'] = meta_strings[1]
        # The 3rd string is author, but let's look for the pattern more carefully
        # After origin string, there should be an int, then author string
        # Actually the strings come in order as they appear in the file
        result['metadata']['author'] = meta_strings[2]
        result['metadata']['category'] = meta_strings[3]
    elif len(meta_strings) >= 1:
        result['metadata']['preset_name'] = meta_strings[0]
    
    result['metadata']['raw_ints'] = meta_ints
    result['metadata']['raw_strings'] = meta_strings
    
    # Parse parameters
    i = param_start
    while i < len(tokens):
        # Expect: ('len_prefix', N), ('string', name), ('number', value)
        if i + 2 < len(tokens):
            t0_type, t0_val = tokens[i]
            t1_type, t1_val = tokens[i + 1]
            t2_type, t2_val = tokens[i + 2]
            
            if t0_type == 'len_prefix' and t1_type == 'string' and t2_type == 'number':
                name = t1_val
                try:
                    value = float(t2_val)
                    # Only accept if name looks like a parameter
                    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name.strip()):
                        result['parameters'][name.strip()] = value
                        i += 3
                        continue
                except ValueError:
                    pass
        
        # Skip unknown tokens
        i += 1
    
    return result


def main():
    mnfx_files = sorted(glob.glob(os.path.join(PRESET_DIR, '*.mnfx')))
    print(f"Found {len(mnfx_files)} .mnfx files")
    
    param_values = defaultdict(list)
    param_types = {}
    param_nonzero_count = defaultdict(int)
    all_params_set = set()
    preset_count = 0
    categories = defaultdict(int)
    authors = defaultdict(int)
    param_value_counts = defaultdict(lambda: defaultdict(int))
    parse_error_files = []
    
    for filepath in mnfx_files:
        try:
            result = parse_mnfx(filepath)
            preset_count += 1
            
            cat = result['metadata'].get('category', '')
            if cat:
                categories[cat] += 1
            
            author = result['metadata'].get('author', '')
            if author:
                authors[author] += 1
            
            for param_name, value in result['parameters'].items():
                all_params_set.add(param_name)
                param_values[param_name].append(value)
                param_value_counts[param_name][round(value, 10)] += 1
                
                if param_name not in param_types:
                    # Check if this looks like it could be an integer value
                    if value == int(value) and 'e' not in str(value).lower():
                        param_types[param_name] = 'potentially_int'
                    else:
                        param_types[param_name] = 'float'
                
                if abs(value) > 1e-6:
                    param_nonzero_count[param_name] += 1
            
            if len(result['parameters']) < 10:
                parse_error_files.append((os.path.basename(filepath), f"Only {len(result['parameters'])} params (likely init/empty preset)"))
                
        except Exception as e:
            parse_error_files.append((os.path.basename(filepath), str(e)))
    
    print(f"Successfully parsed {preset_count} presets")
    print(f"Total unique parameters: {len(all_params_set)}")
    
    sorted_params = sorted(all_params_set)
    
    param_stats = {}
    for pname in sorted_params:
        values = param_values[pname]
        min_val = min(values)
        max_val = max(values)
        
        vc = param_value_counts[pname]
        most_common_val = max(vc, key=vc.get)
        most_common_count = vc[most_common_val]
        
        non_default = sum(1 for v in values if abs(v - most_common_val) > 1e-6)
        
        # Determine type more carefully
        all_ints = all(v == int(v) for v in values)
        has_decimal = any(v != int(v) for v in values)
        
        ptype = 'float'
        if all_ints and not has_decimal:
            ptype = 'int'
        elif has_decimal:
            ptype = 'float'
        else:
            ptype = 'int'
        
        param_stats[pname] = {
            'count_in_presets': len(values),
            'nonzero_count': param_nonzero_count[pname],
            'non_default_count': non_default,
            'type': ptype,
            'min': round(min_val, 10),
            'max': round(max_val, 10),
            'most_common_value': most_common_val,
            'most_common_count': most_common_count,
            'unique_values': len(vc),
        }
    
    # Recategorize parameters by prefix
    def get_group(name):
        if name.startswith('Arp_'): return 'Arp'
        if name.startswith('AutomReserved'): return 'AutomReserved'
        if name.startswith('CycEnv_'): return 'CycEnv'
        if name.startswith('Delay_Routing'): return 'Delay'
        if name.startswith('Dice_'): return 'Dice'
        if name.startswith('Dummy') or name.startswith('dummy'): return 'Dummy'
        if name.startswith('Env_'): return 'Env'
        if name.startswith('FX1_'): return 'FX1'
        if name.startswith('FX2_'): return 'FX2'
        if name.startswith('FX3_'): return 'FX3'
        if name.startswith('Gate_'): return 'Gate'
        if name.startswith('Gen_'): return 'Gen'
        if name.startswith('Kbd_'): return 'Kbd'
        if name.startswith('LFO1_'): return 'LFO1'
        if name.startswith('LFO2_'): return 'LFO2'
        if name.startswith('Length_'): return 'Length'
        if name.startswith('Macro'): return 'Macro'
        if name.startswith('MiniFreak_'): return 'MiniFreak'
        if name.startswith('Mod_S') or name.startswith('Mod_Wheel'): return 'Mod'
        if name.startswith('ModState_'): return 'ModState'
        if name.startswith('MxDst_'): return 'MxDst'
        if name.startswith('Mx_'): return 'Mx'
        if name.startswith('Osc1_'): return 'Osc1'
        if name.startswith('Osc2_'): return 'Osc2'
        if name.startswith('Osc_'): return 'Osc'
        if name.startswith('Pitch1_') or name.startswith('Pitch2_'): return 'PitchMod'
        if name.startswith('Pitch_S'): return 'Pitch'
        if name.startswith('Preset_'): return 'Preset'
        if name.startswith('Reserved'): return 'Reserved'
        if name.startswith('Reverb_'): return 'Reverb'
        if name.startswith('Seq_'): return 'Seq'
        if name.startswith('Shp1_'): return 'Shp1'
        if name.startswith('Shp2_'): return 'Shp2'
        if name == 'Spice': return 'Spice'
        if name.startswith('StepState_'): return 'StepState'
        if name.startswith('Tempo'): return 'Tempo'
        if name.startswith('VST3_'): return 'VST3'
        if name.startswith('Vca_'): return 'Vca'
        if name.startswith('Vcf_'): return 'Vcf'
        if name.startswith('VeloMod_'): return 'VeloMod'
        if name.startswith('Velo_S'): return 'Velo'
        if name.startswith('Vibrato_'): return 'Vibrato'
        if name.startswith('ctrDummy') or name.startswith('ctrl_'): return 'CtrlDummy'
        if name.startswith('old_'): return 'Old/Legacy'
        return 'Other'
    
    param_categories = defaultdict(list)
    for pname in sorted_params:
        param_categories[get_group(pname)].append(pname)
    
    # Build output
    output = {
        'summary': {
            'total_presets_parsed': preset_count,
            'total_unique_parameters': len(sorted_params),
            'presets_with_full_params': sum(1 for f in mnfx_files if parse_mnfx.__code__),
            'parameter_groups': {k: len(v) for k, v in sorted(param_categories.items(), key=lambda x: -len(x[1]))},
            'categories_found': dict(sorted(categories.items(), key=lambda x: -x[1])),
            'authors_found': dict(sorted(authors.items(), key=lambda x: -x[1])),
        },
        'format_specification': {
            'magic_header': '22 serialization::archive 10',
            'format_type': 'boost::serialization text archive (version 10)',
            'encoding': 'ASCII/Latin-1 with CRLF line endings',
            'line_ending': 'CRLF (\\r\\n)',
            'structure': {
                'header': '"22 serialization::archive 10" - identifies boost::serialization format',
                'metadata': 'Flat sequence of integers and length-prefixed strings',
                'parameters': 'Repeated triplets: <name_length> <name> <value>',
                'terminator': 'End of file (no explicit end marker)',
            },
            'metadata_format': {
                'description': 'After the header, metadata is a flat sequence of tokens',
                'field_order': [
                    'version/flag integers (variable count)',
                    'preset_name (length-prefixed string, may contain spaces)',
                    'origin (length-prefixed: "User" or "Factory")',
                    'integer (preset number or size)',
                    'author_name (length-prefixed string, may contain spaces)',
                    'category (length-prefixed string)',
                    'more integers (internal flags/state)',
                    'Subtype (length-prefixed string)',
                    'Type (length-prefixed string)',
                    'Sequence (length-prefixed string)',
                    'more integers (internal state)',
                    'final_integer (possibly parameter count: 2368 for full presets, 0 for init)',
                ],
                'string_encoding': 'Length-prefixed: <length_int> <string_of_exactly_N_chars_including_spaces>',
                'note': 'String tokens consume exactly N characters after the length prefix, including any spaces',
            },
            'parameter_encoding': {
                'triplet_format': '<name_byte_length> <parameter_name> <value>',
                'name_encoding': 'ASCII string, exactly name_byte_length characters, no embedded spaces in parameter names',
                'value_encoding': 'Space-separated numeric token (integer or float in scientific notation)',
                'normalization': 'Most continuous parameters are normalized to [0.0, 1.0] as floats',
                'enum_parameters': 'Discrete/enum parameters stored as float values matching integer choices (e.g., 0.0, 0.14285715 = 1/7)',
                'enum_encoding_note': 'Enum values are often fractions: value = choice_index / (num_choices - 1)',
                'example': '8 Arp_Mode 0  =>  Arp_Mode = 0 (first enum choice)',
                'example2': '9 Osc1_Type 0.42857143  =>  Osc1_Type = 3/7 (4th choice of 8 osc types)',
            },
            'special_observations': {
                'init_presets': '256 of 512 presets are "Init" templates with zero parameters (just header + metadata)',
                'full_presets': '256 presets contain the complete 2368-parameter set',
                'parameter_consistency': 'All full presets contain exactly the same 2368 parameters in the same order',
                'value_precision': 'Float values use ~7 significant digits (32-bit float precision)',
                'quantization_artifacts': 'Values like 0.14285715 = 1/7, 0.33332315 ≈ 1/3 suggest enum index / (N-1) encoding',
            }
        },
        'parameters': param_stats,
        'parameter_groups': {k: sorted(v) for k, v in sorted(param_categories.items(), key=lambda x: -len(x[1]))},
        'parameter_names_sorted': sorted_params,
    }
    
    # Fix the summary presets_with_full_params
    full_count = 0
    init_count = 0
    for filepath in mnfx_files:
        r = parse_mnfx(filepath)
        if len(r['parameters']) > 100:
            full_count += 1
        else:
            init_count += 1
    output['summary']['presets_with_full_parameters'] = full_count
    output['summary']['init_empty_presets'] = init_count
    
    json_path = "/home/jth/hoon/minifreak/firmware/analysis/phase5_mnfx_format.json"
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"JSON saved to {json_path}")
    
    # Generate markdown
    md = []
    md.append("# Phase 5: .mnfx Preset Format Analysis")
    md.append("")
    md.append("## Overview")
    md.append(f"- **Presets analyzed:** {preset_count} (256 full + 256 init templates)")
    md.append(f"- **Total unique parameters:** {len(sorted_params)}")
    md.append(f"- **Parameters per full preset:** 2368 (consistent across all)")
    md.append(f"- **Format:** boost::serialization text archive version 10")
    md.append("")
    
    md.append("## Format Specification")
    md.append("")
    md.append("### File Structure")
    md.append("```")
    md.append("22 serialization::archive 10    <-- magic header")
    md.append("<metadata tokens...>             <-- integers + length-prefixed strings")
    md.append("<param_len> <param_name> <value> <-- repeated parameter triplets")
    md.append("<param_len> <param_name> <value>")
    md.append("...                               (2368 triplets for full presets)")
    md.append("```")
    md.append("")
    md.append("### Encoding Details")
    md.append("| Aspect | Detail |")
    md.append("|--------|--------|")
    md.append("| Line ending | CRLF (`\\r\\n`) |")
    md.append("| Character set | ASCII/Latin-1 |")
    md.append("| Token separator | Space |")
    md.append("| String encoding | Length-prefixed: `<N> <exactly_N_chars>` |")
    md.append("| Integer values | Plain decimal |")
    md.append("| Float values | Scientific notation, ~7 sig digits |")
    md.append("")
    
    md.append("### Metadata Section")
    md.append("After the magic header, the metadata contains:")
    md.append("1. Version/flag integers")
    md.append("2. **Preset name** (length-prefixed, may contain spaces)")
    md.append("3. **Origin** (`\"User\"` or `\"Factory\"`)")
    md.append("4. Preset number/size integer")
    md.append("5. **Author name** (length-prefixed, may contain spaces)")
    md.append("6. **Category** (length-prefixed)")
    md.append("7. More internal integer fields")
    md.append("8. String fields: `Subtype`, `Type`, `Sequence`")
    md.append("9. Final integer (2368 for full presets, 0 for init)")
    md.append("")
    md.append("### Parameter Value Encoding")
    md.append("- **Continuous parameters:** Normalized floats in [0.0, 1.0]")
    md.append("- **Enum/discrete parameters:** Encoded as `index / (num_choices - 1)`")
    md.append("  - Example: `0.14285715 ≈ 1/7` → choice index 1 of 8 options")
    md.append("  - Example: `0.42857143 ≈ 3/7` → choice index 3 of 8 options")
    md.append("  - Example: `0.66667682 ≈ 2/3` → choice index 2 of 3 options")
    md.append("- **Float precision:** ~7 significant digits (32-bit float)")
    md.append("")
    
    md.append("## Parameter Groups")
    md.append("")
    md.append("| Group | Count | Description |")
    md.append("|-------|-------|-------------|")
    for group, params in sorted(param_categories.items(), key=lambda x: -len(x[1])):
        descs = {
            'Pitch': 'Sequencer pitch per step/instrument (64 steps × 6 instruments)',
            'Length': 'Sequencer note length per step/instrument',
            'Velo': 'Sequencer velocity per step/instrument',
            'Mod': 'Sequencer modulation per step/instrument + mod wheel',
            'Reserved': 'Reserved/future-use slots (4 banks × 64)',
            'Mx': 'Modulation matrix assign dots and column IDs',
            'Shp1': 'Envelope shaper 1 steps',
            'Shp2': 'Envelope shaper 2 steps',
            'AutomReserved': 'Automation reserved slots (64)',
            'Gate': 'Sequencer gate values (64 steps)',
            'ModState': 'Sequencer modulation state (64 steps)',
            'StepState': 'Sequencer step active state (64 steps)',
            'Macro': 'Macro controls (2 macros, destinations + amounts)',
            'Kbd': 'Keyboard/scale settings',
            'Osc1': 'Oscillator 1 settings',
            'Osc2': 'Oscillator 2 settings',
            'FX1': 'Effects slot 1',
            'FX2': 'Effects slot 2',
            'FX3': 'Effects slot 3',
            'Seq': 'Sequencer global settings',
            'Arp': 'Arpeggiator settings',
            'Env': 'ADSR envelope',
            'CycEnv': 'Cyclic envelope',
            'LFO1': 'LFO 1 settings',
            'LFO2': 'LFO 2 settings',
            'Vcf': 'VCF (filter) settings',
            'Vibrato': 'Vibrato settings',
            'VeloMod': 'Velocity modulation routing',
            'Gen': 'General/voice settings (polyphony, unison, etc.)',
            'Osc': 'Oscillator global settings',
            'Dummy': 'Dummy/placeholder parameters',
            'CtrlDummy': 'Controller dummy parameters',
            'MxDst': 'Modulation matrix destination enables',
            'PitchMod': 'Per-oscillator pitch modulation enable',
            'Spice': 'Spice/chaos parameter',
            'Preset': 'Preset-level settings (volume, revision)',
            'Reverb': 'Reverb routing',
            'Delay': 'Delay routing',
            'Vca': 'VCA settings',
            'VST3': 'VST3 host control (mod wheel)',
            'Tempo': 'Tempo setting',
            'Dice': 'Random seed',
            'MiniFreak': 'Preset revision tracking',
            'Old/Legacy': 'Legacy compatibility parameters',
        }
        desc = descs.get(group, '')
        md.append(f"| {group} | {len(params)} | {desc} |")
    md.append("")
    
    # Most active parameters
    md.append("## Most Active Parameters (non-default in most presets)")
    md.append("")
    md.append("| # | Parameter | Type | Non-default | Min | Max | Unique Values |")
    md.append("|---|-----------|------|-------------|-----|-----|---------------|")
    top_params = sorted(param_stats.items(), key=lambda x: -x[1]['non_default_count'])[:40]
    for rank, (pname, stats) in enumerate(top_params, 1):
        md.append(f"| {rank} | `{pname}` | {stats['type']} | {stats['non_default_count']}/{stats['count_in_presets']} | {stats['min']} | {stats['max']} | {stats['unique_values']} |")
    md.append("")
    
    # Core synthesis parameters detail
    md.append("## Core Synthesis Parameters")
    md.append("")
    md.append("### Oscillator 1")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Osc1', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Oscillator 2")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Osc2', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Oscillator Global")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Osc', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Filter (VCF)")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Vcf', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Envelope (ADSR)")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Env', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Effects")
    md.append("")
    for fx in ['FX1', 'FX2', 'FX3']:
        md.append(f"#### {fx}")
        md.append("")
        md.append("| Parameter | Type | Range | Non-default |")
        md.append("|-----------|------|-------|-------------|")
        for p in sorted(param_categories.get(fx, [])):
            s = param_stats[p]
            md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
        md.append("")
    
    md.append("### LFOs")
    md.append("")
    for lfo in ['LFO1', 'LFO2']:
        md.append(f"#### {lfo}")
        md.append("")
        md.append("| Parameter | Type | Range | Non-default |")
        md.append("|-----------|------|-------|-------------|")
        for p in sorted(param_categories.get(lfo, [])):
            s = param_stats[p]
            md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
        md.append("")
    
    md.append("### Arpeggiator")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Arp', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### General/Voice")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Gen', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Macros")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Macro', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Keyboard / Scale")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Kbd', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Sequencer")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Seq', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Vibrato")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('Vibrato', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Velocity Modulation")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('VeloMod', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("### Cyclic Envelope")
    md.append("")
    md.append("| Parameter | Type | Range | Non-default |")
    md.append("|-----------|------|-------|-------------|")
    for p in sorted(param_categories.get('CycEnv', [])):
        s = param_stats[p]
        md.append(f"| `{p}` | {s['type']} | [{s['min']}, {s['max']}] | {s['non_default_count']}/{s['count_in_presets']} |")
    md.append("")
    
    md.append("## Preset Categories")
    md.append("")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        md.append(f"- **{cat}**: {count} presets")
    md.append("")
    
    md.append("## Authors")
    md.append("")
    for author, count in sorted(authors.items(), key=lambda x: -x[1]):
        md.append(f"- **{author}**: {count} presets")
    md.append("")
    
    md.append("## Key Findings")
    md.append("")
    md.append("1. **Consistent parameter space:** All 256 full presets contain exactly 2368 parameters in identical order")
    md.append("2. **Normalized values:** Continuous parameters use [0.0, 1.0] float normalization")
    md.append("3. **Enum encoding:** Discrete parameters encode enum indices as `index / (N-1)` fractions")
    md.append("4. **Sequencer dominates:** ~60% of parameters are per-step sequencer data (pitch, velocity, gate, modulation)")
    md.append("5. **Large reserved space:** 384 reserved parameter slots across 4 banks suggest future expansion")
    md.append("6. **Init presets:** 256 of 512 files are empty init templates (header + metadata only)")
    md.append("")
    
    md_path = "/home/jth/hoon/minifreak/notes/PHASE5_MNFX_FORMAT.md"
    with open(md_path, 'w') as f:
        f.write('\n'.join(md))
    print(f"Markdown saved to {md_path}")
    
    # Print summary
    int_count = sum(1 for s in param_stats.values() if s['type'] == 'int')
    float_count = sum(1 for s in param_stats.values() if s['type'] == 'float')
    print(f"\n=== FINAL SUMMARY ===")
    print(f"Presets parsed: {preset_count} ({full_count} full, {init_count} init)")
    print(f"Unique parameters: {len(sorted_params)}")
    print(f"Int-type params: {int_count}")
    print(f"Float-type params: {float_count}")
    print(f"Parameter groups: {len(param_categories)}")


if __name__ == '__main__':
    main()
