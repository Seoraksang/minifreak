#!/usr/bin/env python3
"""
MiniFreak .mnfx Preset Editor v1.2
===================================
Arturia MiniFreak 프리셋(.mnfx) 파일 파서/에디터.
boost::serialization text archive 포맷 기반.

특징:
- Byte-perfect round-trip (수정 안 한 부분은 원본 그대로 보존)
- 정확한 공백/포맷 보존
- 엔진/FX 타입 human-readable 표시

Usage:
    python mnfx_editor.py info <file.mnfx>              # 프리셋 요약 정보
    python mnfx_editor.py show <file.mnfx>              # 모든 파라미터 표시
    python mnfx_editor.py show <file.mnfx> --section osc  # 특정 섹션만
    python mnfx_editor.py get <file.mnfx> <param>       # 파라미터 값 조회
    python mnfx_editor.py set <file.mnfx> <param> <val> # 파라미터 수정
    python mnfx_editor.py rename <file.mnfx> "New Name" # 프리셋 이름 변경
    python mnfx_editor.py copy <src.mnfx> <dst.mnfx>    # 프리셋 복사
    python mnfx_editor.py diff <a.mnfx> <b.mnfx>        # 두 프리셋 비교
    python mnfx_editor.py batch_info <dir/>             # 디렉토리 전체 요약
    python mnfx_editor.py dump <file.mnfx>              # raw 파서 출력 (디버그)
"""

import sys
import os
import re
import json
import shutil
from pathlib import Path

# Ensure sibling modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PARAM_NAME_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_]+$')

# ─── Category Map ─────────────────────────────────────────────────────────
CATEGORY_MAP = {}
for prefix, cat in sorted([
    ('Osc1_', 'OSC 1'), ('Osc2_', 'OSC 2'), ('Osc_', 'OSC Common'),
    ('Env_', 'ENVELOPE (AMP)'), ('LFO1_', 'LFO 1'), ('LFO2_', 'LFO 2'),
    ('FX1_', 'FX 1'), ('FX2_', 'FX 2'), ('FX3_', 'FX 3'),
    ('Mod_', 'MODULATION'), ('ModState_', 'MOD STATE'),
    ('Gate_', 'SEQ Gate'), ('Length_', 'SEQ Length'),
    ('Arp_', 'ARPEGGIATOR'), ('CycEnv_', 'CYCLIC ENV'),
    ('Kbd_', 'KEYBOARD'), ('Gen_', 'GENERAL'),
    ('Delay_', 'DELAY'), ('Routing_', 'ROUTING'),
    ('Spk_', 'SPEAKER'), ('Multi_', 'MULTI'),
    ('Mixer_', 'MIXER'), ('Pan_', 'PAN'),
    ('Pitch_', 'PITCH'), ('Brace_', 'BRACE'),
    ('Dice_', 'DICE'), ('AutomReserved', 'AUTO (reserved)'), ('Dummy', 'DUMMY'),
], key=lambda x: -len(x[0])):
    CATEGORY_MAP[prefix] = cat

SECTION_ALIASES = {
    'osc': ['Osc1_', 'Osc2_', 'Osc_'],
    'env': ['Env_'],
    'lfo': ['LFO1_', 'LFO2_'],
    'fx':  ['FX1_', 'FX2_', 'FX3_'],
    'mod': ['Mod_', 'ModState_'],
    'gate': ['Gate_', 'Length_'],
    'arp': ['Arp_'],
    'cyc': ['CycEnv_'],
    'kbd': ['Kbd_'],
    'gen': ['Gen_'],
    'mix': ['Mixer_', 'Pan_', 'Routing_'],
    'all': None,
}

# ─── Value mappers (official, from Arturia VST XML) ───────────────
from mf_enums import (
    OSC1_ENGINES, OSC2_ENGINES, FX_TYPES, LFO_WAVES,
    ARP_MODES, VOICE_MODES, CYCENV_MODES,
    VCF_TYPES, UNISON_MODES, POLY_ALLOC_MODES,
    POLY_STEAL_MODES, LEGATO_MODES, RETRIG_MODES,
    enum_lookup,
)

def _nearest_enum(val, table: dict, n: int = None):
    """Map float value from .mnfx to nearest enum name."""
    try:
        v = float(val)
    except (ValueError, TypeError):
        return str(val)
    name = enum_lookup(table, v, n)
    return f'{name} ({v:.5f})'

def _format_osc_type(name, value):
    table = OSC1_ENGINES if name == 'Osc1_Type' else OSC2_ENGINES
    return _nearest_enum(value, table)

def map_lfo_wave(val):
    return _nearest_enum(val, LFO_WAVES)

def format_value(name, value):
    if name == 'Osc1_Type': return f'{value}  ← {_format_osc_type(name, value)}'
    if name == 'Osc2_Type': return f'{value}  ← {_format_osc_type(name, value)}'
    if name in ('FX1_Type', 'FX2_Type', 'FX3_Type'): return f'{value}  ← {_nearest_enum(value, FX_TYPES)}'
    if name in ('LFO1_Wave', 'LFO2_Wave'): return f'{value}  ← {map_lfo_wave(value)}'
    if name == 'Arp_Mode': return f'{value}  ← {_nearest_enum(value, ARP_MODES)}'
    if name == 'Gen_NoteMode': return f'{value}  ← {_nearest_enum(value, VOICE_MODES, 5)}'
    if name == 'CycEnv_Mode': return f'{value}  ← {_nearest_enum(value, CYCENV_MODES)}'
    if name == 'Vcf_Type': return f'{value}  ← {_nearest_enum(value, VCF_TYPES)}'
    return value

def categorize(name):
    for prefix, cat in CATEGORY_MAP.items():
        if name.startswith(prefix):
            return cat
    return 'OTHER'


# ═══════════════════════════════════════════════════════════════════════════
# .mnfx Parser — text-based, byte-perfect round-trip
# ═══════════════════════════════════════════════════════════════════════════

class MnfxParser:
    """
    boost::serialization text archive 파서.
    
    원본 텍스트를 기반으로 파라미터 위치를 기록하고,
    수정 시 해당 위치만 치환. 나머지는 원본 바이트 그대로 보존.
    """

    def __init__(self, data: bytes):
        self.raw = data
        self.text = data.rstrip(b'\r\n').decode('latin-1')
        self.tokens = self.text.split()
        self.pos = 0

        # Parsed fields
        self.header_version = 10
        self.class_version = (7, 7)
        self.name = ''
        self.bank = ''
        self.author = ''
        self.category = ''
        self.subtype = ''
        self.type_ = ''
        self.params = {}       # name → value (str)
        self.param_order = []  # insertion order
        self._modifications = {}  # name → new_value (only modified ones)
        self._new_name = None  # set by rename()

        self._parse()

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _next(self):
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def _read_len_prefixed_string(self):
        """Read <byte_length> <chars...> → str."""
        length = int(self._next())
        chars = []
        byte_count = 0
        while byte_count < length and self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            self.pos += 1
            if chars:
                byte_count += 1
                if byte_count >= length:
                    chars.append(token[:length - byte_count + len(token)])
                    break
            chars.append(token)
            byte_count += len(token)
        return ' '.join(chars)

    def _is_param_start(self):
        """Check if current position starts a parameter: <name_len> <param_name>."""
        if self.pos + 2 >= len(self.tokens):
            return False
        try:
            length = int(self.tokens[self.pos])
            if not (1 <= length <= 50):
                return False
        except ValueError:
            return False
        return bool(PARAM_NAME_RE.match(self.tokens[self.pos + 1]))

    def _parse(self):
        # ── Magic header ──
        self._next()  # '22'
        self._next()  # 'serialization::archive'
        self.header_version = int(self._next())
        self._next()  # 0
        self.class_version = (int(self._next()),)
        self._next()  # 0
        self.class_version = (self.class_version[0], int(self._next()))

        # ── Named header fields ──
        self.name = self._read_len_prefixed_string()
        self.bank = self._read_len_prefixed_string()
        self._next()  # 66
        self.author = self._read_len_prefixed_string()
        self.category = self._read_len_prefixed_string()

        # ── Subtype / Type (optional keyword fields) ──
        # Format: ... <ints> Subtype <len> <value> <int> Type <len> <value> <ints> params...
        # Subtype/Type are literal keywords (not length-prefixed).
        while self.pos < len(self.tokens):
            tok = self._peek()
            if tok == 'Subtype':
                self._next()  # consume 'Subtype'
                self.subtype = self._read_len_prefixed_string()
            elif tok == 'Type':
                self._next()
                self.type_ = self._read_len_prefixed_string()
                break  # Type is always the last header field before params
            else:
                self._next()

        # ── Skip pre-parameter integers ──
        while self.pos < len(self.tokens):
            if self._is_param_start():
                break
            self._next()

        # ── Parameters ──
        while self.pos < len(self.tokens):
            if not self._is_param_start():
                self.pos += 1
                continue

            # Read name
            name_start = self.pos
            name_len = int(self.tokens[self.pos])
            self.pos += 1
            name_parts = []
            byte_count = 0
            while byte_count < name_len and self.pos < len(self.tokens):
                token = self.tokens[self.pos]
                self.pos += 1
                if name_parts:
                    byte_count += 1
                    if byte_count >= name_len:
                        name_parts.append(token[:name_len - byte_count + len(token)])
                        break
                name_parts.append(token)
                byte_count += len(token)
            param_name = ' '.join(name_parts)

            # Value
            if self.pos < len(self.tokens):
                value = self.tokens[self.pos]
                self.pos += 1
            else:
                value = '0'

            self.params[param_name] = value
            self.param_order.append(param_name)

    def serialize(self) -> bytes:
        """Serialize — text-replace approach for byte-perfect output."""
        if not self._modifications and self._new_name is None:
            return self.raw  # No changes, return original bytes

        text = self.text

        # Apply name change if any
        if self._new_name is not None:
            old_name = self.name
            new_name = self._new_name
            old_enc = f'{len(old_name.encode("latin-1"))} {old_name}'
            new_enc = f'{len(new_name.encode("latin-1"))} {new_name}'
            text = text.replace(old_enc, new_enc, 1)
            self.name = new_name

        # Apply parameter value changes — use original values from raw text
        for param_name, new_value in self._modifications.items():
            # Get original value from raw text (not the modified self.params)
            name_tokens = param_name.split()
            name_pattern = r'\s+'.join(re.escape(t) for t in name_tokens)
            # Match: <number> <name_pattern> <any_value>
            pattern = rf'(\d+\s+{name_pattern}\s+)\S+'
            replacement = rf'\g<1>{new_value}'
            text = re.sub(pattern, replacement, text, count=1)

        return text.encode('latin-1') + b'\r\n'

    # ─── Editing ──────────────────────────────────────────────────────────

    def set_param(self, name, value):
        if name not in self.params:
            return False
        # Validate value is numeric
        try:
            float(value)
        except ValueError:
            raise ValueError(f"Invalid value '{value}' for {name}: must be numeric")
        self._modifications[name] = value
        self.params[name] = value
        return True

    def get_param(self, name):
        return self.params.get(name)

    def rename(self, new_name):
        self._new_name = new_name


# ═══════════════════════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════════════════════

def cmd_info(p):
    n = len(p.params)
    interesting = sum(1 for k in p.params
                      if not k.startswith('Dummy') and not k.startswith('AutomReserved')
                      and not k.startswith('Gate_') and not k.startswith('Length_')
                      and not k.startswith('ModState_'))
    print(f'╔══════════════════════════════════════════╗')
    print(f'║  🎹 {p.name:<37s}║')
    print(f'╠══════════════════════════════════════════╣')
    print(f'║  Bank:     {p.bank:<30s}║')
    print(f'║  Author:   {p.author:<30s}║')
    print(f'║  Category: {p.category:<30s}║')
    print(f'║  Type:     {p.type_ or "—":<30s}║')
    print(f'║  Params:   {n} total, {interesting} active{" " * max(0, 18 - len(str(interesting)))}║')
    print(f'╚══════════════════════════════════════════╝')

    for section, params in [
        ('OSC1', [('Osc1_Type', 'Type'), ('Osc1_Param1', 'Timbre'), ('Osc1_Param2', 'Morph'), ('Osc1_Volume', 'Vol')]),
        ('OSC2', [('Osc2_Type', 'Type'), ('Osc2_Param1', 'Timbre'), ('Osc2_Param2', 'Morph'), ('Osc2_Volume', 'Vol')]),
        ('ENV',  [('Env_Attack', 'A'), ('Env_Decay', 'D'), ('Env_Sustain', 'S'), ('Env_Release', 'R')]),
        ('FX',   [('FX1_Type', 'FX1'), ('FX2_Type', 'FX2'), ('FX3_Type', 'FX3')]),
        ('LFO',  [('LFO1_Wave', 'LFO1'), ('LFO1_Rate', 'Rate'), ('LFO2_Wave', 'LFO2'), ('LFO2_Rate', 'Rate')]),
    ]:
        vals = []
        for pname, label in params:
            if pname in p.params:
                v = format_value(pname, p.params[pname]).split('←')[0].strip()
                vals.append(f'{label}={v}')
        if vals:
            print(f'  [{section:>4s}] {"  ".join(vals)}')

def cmd_show(p, section='all'):
    prefixes = SECTION_ALIASES.get(section)
    current_cat = None
    shown = 0
    skipped = 0

    for name in p.param_order:
        if name not in p.params:
            continue
        if prefixes and not any(name.startswith(pr) for pr in prefixes):
            continue
        if name.startswith('Dummy') or name.startswith('AutomReserved'):
            skipped += 1
            continue

        cat = categorize(name)
        if cat != current_cat:
            if current_cat is not None:
                print()
            print(f'  ── {cat} ──')
            current_cat = cat

        print(f'  {name:<30s} = {format_value(name, p.params[name])}')
        shown += 1

    if skipped:
        print(f'\n  (skipped {skipped} dummy/reserved)')
    print(f'\n  Total: {shown} parameters')

def cmd_get(p, param_name):
    val = p.get_param(param_name)
    if val is None:
        matches = [k for k in p.params if param_name.lower() in k.lower()]
        if matches:
            print(f"'{param_name}' not found. Did you mean:")
            for m in matches[:10]:
                print(f'  {m} = {format_value(m, p.params[m])}')
            if len(matches) > 10:
                print(f'  ... +{len(matches)-10} more')
        else:
            print(f"'{param_name}' not found.")
        return 1
    print(f'{param_name} = {format_value(param_name, val)}')
    return 0

def cmd_set(p, param_name, value, filepath):
    if not p.set_param(param_name, value):
        print(f"'{param_name}' not found.")
        return 1
    print(f'{param_name} = {format_value(param_name, value)}')
    fp = Path(filepath)
    bak = fp.with_suffix('.mnfx.bak')
    if fp.exists():
        shutil.copy2(fp, bak)
        print(f'Backup: {bak}')
    fp.write_bytes(p.serialize())
    print(f'Saved: {fp}')
    return 0

def cmd_rename(p, new_name, filepath):
    old = p.name
    p.rename(new_name)
    print(f'"{old}" → "{new_name}"')
    fp = Path(filepath)
    bak = fp.with_suffix('.mnfx.bak')
    if fp.exists():
        shutil.copy2(fp, bak)
    fp.write_bytes(p.serialize())
    print(f'Saved: {fp}')
    return 0

def cmd_diff(a, b):
    print(f'"{a.name}" vs "{b.name}"')
    all_keys = list(dict.fromkeys(list(a.param_order) + list(b.param_order)))
    diffs = [(k, a.params.get(k), b.params.get(k)) for k in all_keys
             if a.params.get(k) != b.params.get(k)]
    if not diffs:
        print('  ✓ Identical')
        return

    current_cat = None
    count = 0
    for name, va, vb in diffs:
        if name.startswith('Dummy') or name.startswith('AutomReserved'):
            continue
        cat = categorize(name)
        if cat != current_cat:
            print(f'\n  ── {cat} ──')
            current_cat = cat
        va_s = format_value(name, va) if va is not None else '(absent)'
        vb_s = format_value(name, vb) if vb is not None else '(absent)'
        marker = '+' if va is None else ('-' if vb is None else '~')
        print(f'  {marker} {name:<30s}  {va_s} → {vb_s}')
        count += 1
    print(f'\n  {count} differences')

def cmd_batch_info(directory):
    files = sorted(Path(directory).rglob('*.mnfx'))
    if not files:
        print(f'No .mnfx files in {directory}')
        return
    print(f'{len(files)} presets in {directory}')
    print(f'{"Name":<35s} {"Bank":<6s} {"#":>4s}  {"Osc1":<18s} {"Osc2":<18s} {"FX Chain":<35s}')
    print('─' * 125)
    for fp in files:
        try:
            p = MnfxParser(fp.read_bytes())
            o1 = _nearest_enum(p.params.get('Osc1_Type', ''), OSC1_ENGINES).split('(')[0].strip()
            o2 = _nearest_enum(p.params.get('Osc2_Type', ''), OSC2_ENGINES).split('(')[0].strip()
            f1 = _nearest_enum(p.params.get('FX1_Type', ''), FX_TYPES).split('(')[0].strip()
            f2 = _nearest_enum(p.params.get('FX2_Type', ''), FX_TYPES).split('(')[0].strip()
            f3 = _nearest_enum(p.params.get('FX3_Type', ''), FX_TYPES).split('(')[0].strip()
            n = p.name[:34] if p.name else fp.stem[:34]
            print(f'{n:<35s} {p.bank:<6s} {len(p.params):>4d}  {o1:<18s} {o2:<18s} {f1} → {f2} → {f3}')
        except Exception as e:
            print(f'{fp.stem:<35s} ERROR: {e}')

def cmd_dump(p):
    d = {
        'header_version': p.header_version,
        'class_version': list(p.class_version),
        'name': p.name, 'bank': p.bank, 'author': p.author,
        'category': p.category, 'subtype': p.subtype, 'type': p.type_,
        'param_count': len(p.params),
        'total_tokens': len(p.tokens),
        'params': {k: p.params[k] for k in p.param_order if k in p.params},
    }
    print(json.dumps(d, indent=2, ensure_ascii=False))


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd in ('help', '--help', '-h'):
        print(__doc__)
        sys.exit(0)

    def need_file(min_args=3):
        if len(sys.argv) < min_args:
            print(f'Usage: mnfx_editor.py {cmd} <file.mnfx> [args...]')
            sys.exit(1)
        fp = sys.argv[2]
        if not os.path.exists(fp):
            print(f'Not found: {fp}')
            sys.exit(1)
        return fp

    if cmd == 'info':
        p = MnfxParser(Path(need_file()).read_bytes())
        cmd_info(p)

    elif cmd == 'show':
        fp = need_file()
        p = MnfxParser(Path(fp).read_bytes())
        section = 'all'
        if '--section' in sys.argv:
            idx = sys.argv.index('--section')
            section = sys.argv[idx+1] if idx+1 < len(sys.argv) else 'all'
        cmd_show(p, section)

    elif cmd == 'get':
        fp = need_file(4)
        p = MnfxParser(Path(fp).read_bytes())
        sys.exit(cmd_get(p, sys.argv[3]))

    elif cmd == 'set':
        fp = need_file(5)
        p = MnfxParser(Path(fp).read_bytes())
        sys.exit(cmd_set(p, sys.argv[3], sys.argv[4], fp))

    elif cmd == 'rename':
        fp = need_file(4)
        p = MnfxParser(Path(fp).read_bytes())
        sys.exit(cmd_rename(p, sys.argv[3], fp))

    elif cmd == 'diff':
        if len(sys.argv) < 4:
            print('Usage: mnfx_editor.py diff <a.mnfx> <b.mnfx>')
            sys.exit(1)
        a = MnfxParser(Path(sys.argv[2]).read_bytes())
        b = MnfxParser(Path(sys.argv[3]).read_bytes())
        cmd_diff(a, b)

    elif cmd == 'batch_info':
        if len(sys.argv) < 3:
            print('Usage: mnfx_editor.py batch_info <dir/>')
            sys.exit(1)
        cmd_batch_info(sys.argv[2])

    elif cmd == 'copy':
        if len(sys.argv) < 4:
            print('Usage: mnfx_editor.py copy <src.mnfx> <dst.mnfx>')
            sys.exit(1)
        shutil.copy2(sys.argv[2], sys.argv[3])
        print(f'Copied: {sys.argv[2]} → {sys.argv[3]}')
        cmd_info(MnfxParser(Path(sys.argv[3]).read_bytes()))

    elif cmd == 'dump':
        p = MnfxParser(Path(need_file()).read_bytes())
        cmd_dump(p)

    else:
        print(f'Unknown command: {cmd}')
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
