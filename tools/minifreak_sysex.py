#!/usr/bin/env python3
"""
MiniFreak MIDI SysEx Command-Line Tool
Phase 8-2 | Arturia MiniFreak Reverse Engineering

Capabilities:
  - Build/parse Arturia SysEx messages (F0 00 20 6B ...)
  - Send/receive via MIDI (USB/DIN)
  - CC mapping with human-readable names
  - Preset dump request/response
  - Real-time parameter control
  - Listen/sniff MIDI traffic

Protocol reference: notes/PHASE6_MIDI_CHART.md, notes/PHASE6_COMMUNICATION_PROTOCOLS.md
"""

import argparse
import sys
import os
import time
from pathlib import Path
from dataclasses import dataclass
from collections import Counter
from typing import Optional

try:
    import mido
except ImportError:
    print("ERROR: mido required. pip install mido python-rtmidi")
    sys.exit(1)

# Ensure sibling modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════
# Constants — Arturia MiniFreak MIDI Specification
# ═══════════════════════════════════════════════════════════════

ARTURIA_MFR = (0x00, 0x20, 0x6B)
MINIFREAK_DEV_ID = 0x02
BROADCAST_DEV_ID = 0x7F
SYSEX_START = 0xF0
SYSEX_END = 0xF7

# SysEx Message Types (Phase 6 analysis)
MSG_TYPES = {
    2:  ("Counter ACK", "ACK"),
    3:  ("Param 2-byte A", "Param"),
    4:  ("Param 2-byte B", "Param"),
    5:  ("Param Data", "Param"),
    6:  ("Param 7-bit Unpack", "Param"),
    7:  ("Param 2-byte C", "Param"),
    8:  ("Alt Channel", "Param"),
    9:  ("Param Standard", "Param"),
    10: ("Special Counter", "ACK"),
    11: ("Param 2-byte D", "Param"),
    12: ("Counter 2-byte", "ACK"),
    13: ("Param 2-byte E", "Param"),
    33: ("Counter ACK B", "ACK"),
    34: ("Payload", "Param"),
    35: ("Counter ACK C", "ACK"),
    0x42: ("Request/Query", "Request"),
    0x48: ("6-Param Pack", "Param"),
}

# 14-bit value types
FOURTEEN_BIT_TYPES = {3, 4, 7, 11, 12, 13}

# ── MIDI CC Mapping (161 CCs from Phase 6-3) ──
CC_MAP = {
    0:   ("Bank Select MSB", 0, 127),
    1:   ("Osc1 Type/Waveform", 0, 127),
    2:   ("Osc1 Shape/PWM", 0, 127),
    3:   ("Osc1 Unison", 0, 127),
    4:   ("Osc1 Unison Detune", 0, 127),
    5:   ("Osc1 Octave", 0, 127),
    6:   ("Osc1 Semitone", 0, 127),
    10:  ("Osc2 Type/Waveform", 0, 127),
    11:  ("Osc2 Shape/PWM", 0, 127),
    12:  ("Osc2 Unison", 0, 127),
    13:  ("Osc2 Unison Detune", 0, 127),
    14:  ("Osc2 Octave", 0, 127),
    15:  ("Osc2 Semitone", 0, 127),
    16:  ("Osc2 Amount/Mix", 0, 127),
    20:  ("Osc1 Level", 0, 127),
    21:  ("Osc2 Level", 0, 127),
    24:  ("Filter Cutoff", 0, 127),
    25:  ("Filter Resonance", 0, 127),
    26:  ("Filter Env Amount", 0, 127),
    27:  ("Filter Key Tracking", 0, 127),
    29:  ("Filter Type", 0, 127),
    30:  ("Filter Drive", 0, 127),
    31:  ("Filter Env Velocity", 0, 127),
    32:  ("Filter Cutoff 2", 0, 127),
    38:  ("Env1 Attack", 0, 127),
    39:  ("Env1 Decay", 0, 127),
    40:  ("Env1 Sustain", 0, 127),
    41:  ("Env1 Release", 0, 127),
    42:  ("Env1 Time", 0, 127),
    43:  ("Env1 Loop", 0, 127),
    44:  ("Env1 Velocity", 0, 127),
    45:  ("Env2 Attack", 0, 127),
    46:  ("Env2 Decay", 0, 127),
    47:  ("Env2 Sustain", 0, 127),
    48:  ("Env2 Release", 0, 127),
    49:  ("Env2 Time", 0, 127),
    50:  ("Env2 Velocity", 0, 127),
    53:  ("LFO1 Rate", 0, 127),
    54:  ("LFO1 Shape", 0, 127),
    55:  ("LFO1 Amount", 0, 127),
    56:  ("LFO1 Phase", 0, 127),
    57:  ("LFO1 Sync", 0, 127),
    60:  ("LFO2/Mod Rate", 0, 127),
    61:  ("LFO2/Mod Shape", 0, 127),
    62:  ("LFO2/Mod Amount", 0, 127),
    64:  ("Sustain Pedal", 0, 127),
    65:  ("Portamento", 0, 127),
    66:  ("Sostenuto", 0, 127),
    71:  ("FX A Type", 0, 127),
    72:  ("FX A Param 1", 0, 127),
    73:  ("FX A Param 2", 0, 127),
    74:  ("FX A Param 3", 0, 127),
    75:  ("FX A Param 4", 0, 127),
    76:  ("FX A Param 5", 0, 127),
    77:  ("FX A Param 6", 0, 127),
    78:  ("FX A Param 7", 0, 127),
    79:  ("FX A Param 8", 0, 127),
    85:  ("FX B Type", 0, 127),
    193: ("Macro 1", 0, 127),
    195: ("Macro 2", 0, 127),
    196: ("Macro 3", 0, 127),
    197: ("Macro 4", 0, 127),
    198: ("Macro 5", 0, 127),
    202: ("Macro 6", 0, 127),
    204: ("Macro 7", 0, 127),
    120: ("All Sound Off", 0, 0),
    121: ("Reset All Controllers", 0, 0),
    123: ("All Notes Off", 0, 0),
}

# ── Enum Mappings (official, from Arturia VST XML) ──
# Source: minifreak_vst_params.xml + MiniFreak V_actions.xml
from mf_enums import (
    OSC1_ENGINES, OSC2_ENGINES, FX_TYPES, LFO_WAVES,
    ARP_MODES, VOICE_MODES, CYCENV_MODES,
    VCF_TYPES, UNISON_MODES, POLY_ALLOC_MODES,
    POLY_STEAL_MODES, LEGATO_MODES, RETRIG_MODES,
    OSC1_ONLY, OSC2_ONLY, OSC_COMMON, FX_SINGLETONS,
    enum_lookup,
)


# ═══════════════════════════════════════════════════════════════
# SysEx Message Builder / Parser
# ═══════════════════════════════════════════════════════════════

@dataclass
class SysExMessage:
    """Parsed Arturia SysEx message."""
    device_id: int = MINIFREAK_DEV_ID
    msg_type: int = 0
    param_idx: int = 0
    value_lo: int = 0
    value_hi: Optional[int] = None
    payload: bytes = b""
    raw: bytes = b""

    @property
    def type_name(self) -> str:
        return MSG_TYPES.get(self.msg_type, (f"Unknown({self.msg_type})", "?"))[0]

    @property
    def type_cat(self) -> str:
        return MSG_TYPES.get(self.msg_type, ("?", "?"))[1]

    @property
    def is_14bit(self) -> bool:
        return self.msg_type in FOURTEEN_BIT_TYPES

    @property
    def value_14bit(self) -> int:
        if self.value_hi is not None:
            return (self.value_hi << 7) | self.value_lo
        return self.value_lo

    def hex_str(self) -> str:
        return " ".join(f"{b:02X}" for b in self.raw)

    def __repr__(self) -> str:
        s = f"SysEx [Dev=0x{self.device_id:02X}] Type={self.msg_type} ({self.type_name})"
        s += f" Param={self.param_idx}"
        if self.is_14bit and self.value_hi is not None:
            s += f" Value={self.value_14bit} (0x{self.value_14bit:04X}, lo={self.value_lo} hi={self.value_hi})"
        else:
            s += f" Value={self.value_lo}"
        if self.payload:
            s += f" Payload=[{len(self.payload)}B]"
        return s


def build_sysex(dev_id: int, msg_type: int, param_idx: int,
                value: int, is_14bit: bool = False) -> bytes:
    """
    Build Arturia SysEx parameter set message.
    Format: F0 00 20 6B [DevID] [MsgType] [ParamIdx] [ValueLo] [ValueHi?] F7
    """
    if is_14bit:
        if not 0 <= value <= 16383:
            raise ValueError(f"14-bit value out of range: {value}")
        return bytes([SYSEX_START, *ARTURIA_MFR, dev_id, msg_type,
                      param_idx & 0x7F, value & 0x7F, (value >> 7) & 0x7F, SYSEX_END])
    else:
        if not 0 <= value <= 127:
            raise ValueError(f"7-bit value out of range: {value}")
        return bytes([SYSEX_START, *ARTURIA_MFR, dev_id, msg_type,
                      param_idx & 0x7F, value & 0x7F, SYSEX_END])


def build_request(dev_id: int, param_idx: int) -> bytes:
    """Build parameter request: F0 00 20 6B [DevID] 42 [ParamIdx] F7"""
    return bytes([SYSEX_START, *ARTURIA_MFR, dev_id, 0x42, param_idx & 0x7F, SYSEX_END])


def build_identity_request() -> bytes:
    """Universal SysEx Identity Request: F0 7E 7F 06 01 F7"""
    return bytes([0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7])


def build_6param(dev_id: int, counter: int, params: list) -> bytes:
    """
    6-parameter SysEx (HW→Host format).
    Format: F0 00 20 6B [dev] [counter] 0x48 0x03 [sign_bits] [p0..p5] F7
    """
    if len(params) != 6:
        raise ValueError(f"Expected 6 params, got {len(params)}")
    sign_bits = 0
    packed = []
    for i, p in enumerate(params):
        p = max(-64, min(63, int(p)))
        sign_bits |= ((p < 0) << (6 - i))
        packed.append(p & 0x7F)
    return bytes([SYSEX_START, *ARTURIA_MFR, dev_id & 0x7F, counter & 0x7F,
                  0x48, 0x03, sign_bits, *packed, SYSEX_END])


def parse_sysex(data: bytes) -> Optional[SysExMessage]:
    """Parse an Arturia SysEx message into a SysExMessage."""
    if not data or data[0] != SYSEX_START or data[-1] != SYSEX_END:
        return None
    if len(data) < 6:
        return None

    # Universal SysEx
    if data[1] == 0x7E:
        msg = SysExMessage(device_id=0x7F, msg_type=0x7E, raw=data)
        msg.payload = data[1:-1]
        return msg

    # Arturia check
    if tuple(data[1:4]) != ARTURIA_MFR:
        return None

    dev_id = data[4]

    # 6-param format: F0 00 20 6B [dev] [counter] 0x48 0x03 [sign] [p0..p5] F7 = 16 bytes
    if len(data) == 16 and data[6] == 0x48 and data[7] == 0x03:
        msg = SysExMessage(device_id=dev_id, msg_type=0x48, param_idx=data[5], raw=data)
        sign_bits = data[8]
        vals = []
        for i in range(6):
            v = data[9 + i]  # already unsigned 0-127 from 7-bit packing
            if sign_bits & (1 << (6 - i)):
                v = v - 128  # convert to signed (-128..-1)
            vals.append(v)
        # Store as list of signed ints (not bytes) to preserve sign
        msg.payload = vals  # type: ignore
        return msg

    msg_type = data[5]
    # Short message: no value field (e.g., type 0x42 request)
    # F0 00 20 6B [dev] [type] [param] F7 = 8 bytes
    if len(data) == 8:
        return SysExMessage(device_id=dev_id, msg_type=msg_type,
                            param_idx=data[6], raw=data)

    # Standard format with value: F0 00 20 6B [dev] [type] [param] [val_lo] [val_hi?] F7
    if len(data) >= 9:
        param_idx = data[6]
        value_lo = data[7]
        # value_hi exists if there's exactly one byte between value_lo and F7
        # 14-bit: F0 00 20 6B [dev] [type] [param] [lo] [hi] F7 = 11 bytes
        # 7-bit:  F0 00 20 6B [dev] [type] [param] [lo] F7 = 10 bytes
        value_hi = data[8] if len(data) >= 10 else None
        msg = SysExMessage(device_id=dev_id, msg_type=msg_type,
                           param_idx=param_idx, value_lo=value_lo,
                           value_hi=value_hi, raw=data)
        end_idx = 9 if value_hi is not None else 8
        if len(data) > end_idx + 1:
            msg.payload = data[end_idx:-1]
        return msg

    msg = SysExMessage(device_id=dev_id, raw=data)
    msg.payload = data[5:-1]
    return msg


def parse_all_sysex(data: bytes) -> list[SysExMessage]:
    """Parse multiple SysEx messages from a byte stream."""
    results = []
    i = 0
    while i < len(data):
        if data[i] == SYSEX_START:
            end = data.find(SYSEX_END, i)
            if end == -1:
                break
            parsed = parse_sysex(data[i:end + 1])
            if parsed:
                results.append(parsed)
            i = end + 1
        else:
            i += 1
    return results


# ═══════════════════════════════════════════════════════════════
# MIDI Port Manager
# ═══════════════════════════════════════════════════════════════

class MidiManager:
    """MIDI I/O for MiniFreak."""

    def __init__(self, port_name: Optional[str] = None):
        self.port_name = port_name
        self.in_port = None
        self.out_port = None
        self._received: list = []
        self._got_msg = False

    def list_ports(self) -> None:
        """List all MIDI ports."""
        print("─── MIDI Input Ports ───")
        for i, name in enumerate(mido.get_input_names()):
            tag = " ◄" if (self.port_name and self.port_name.lower() in name.lower()) else ""
            print(f"  [{i:2d}] {name}{tag}")
        print("\n─── MIDI Output Ports ───")
        for i, name in enumerate(mido.get_output_names()):
            tag = " ◄" if (self.port_name and self.port_name.lower() in name.lower()) else ""
            print(f"  [{i:2d}] {name}{tag}")

    def _find_port(self, direction: str) -> Optional[str]:
        names = mido.get_input_names() if direction == "in" else mido.get_output_names()
        if self.port_name:
            for n in names:
                if self.port_name.lower() in n.lower():
                    return n
        for n in names:
            low = n.lower()
            if 'minifreak' in low or 'mini freak' in low or 'mini_freak' in low:
                return n
            if 'arturia' in low and 'mini' in low:
                return n
        return None

    def open(self) -> bool:
        """Open MIDI ports. Returns True if output opened successfully."""
        out_name = self._find_port("out")
        if not out_name:
            print("ERROR: MiniFreak MIDI output port not found.")
            print("Use --port to specify, or connect the device.")
            return False
        try:
            self.out_port = mido.open_output(out_name)
            print(f"OUT: {out_name}")
        except Exception as e:
            print(f"ERROR opening output: {e}")
            return False

        in_name = self._find_port("in")
        if in_name:
            try:
                self.in_port = mido.open_input(in_name, callback=self._cb)
                print(f"IN:  {in_name}")
            except Exception as e:
                print(f"WARNING: input disabled ({e})")
        else:
            print("WARNING: no input port, receive disabled")
        return True

    def _cb(self, msg):
        self._received.append(msg)
        self._got_msg = True

    def send(self, msg) -> None:
        if not self.out_port:
            print("ERROR: no output port")
            return
        self.out_port.send(msg)
        if hasattr(msg, 'bytes'):
            print(f"→ {msg.hex()}")
        else:
            print(f"→ {msg}")

    def send_sysex(self, data: bytes) -> None:
        self.send(mido.Message('sysex', data=data))

    def send_cc(self, cc: int, value: int, channel: int = 0) -> None:
        if cc not in CC_MAP:
            print(f"NOTE: CC#{cc} not in MiniFreak mapping")
        self.send(mido.Message('control_change', channel=channel, control=cc, value=value))

    def send_note(self, note: int, velocity: int = 100, channel: int = 0) -> None:
        self.send(mido.Message('note_on', channel=channel, note=note, velocity=velocity))

    def send_note_off(self, note: int, channel: int = 0) -> None:
        self.send(mido.Message('note_off', channel=channel, note=note, velocity=0))

    def wait_response(self, timeout: float = 2.0) -> Optional[mido.Message]:
        self._received.clear()
        self._got_msg = False
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._got_msg:
                self._got_msg = False
                return self._received.pop(0)
            time.sleep(0.005)
        return None

    def listen(self, duration: float = 10.0, parse: bool = True) -> list:
        """Listen and optionally parse SysEx messages."""
        self._received.clear()
        print(f"Listening {duration}s... (Ctrl+C to stop)")
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            print("\nStopped.")
        msgs = self._received[:]
        self._received.clear()

        if not parse:
            return msgs

        results = []
        for msg in msgs:
            if msg.type == 'sysex':
                parsed = parse_sysex(msg.data)
                if parsed:
                    results.append(parsed)
            else:
                results.append(msg)
        return results

    def close(self):
        if self.in_port:
            self.in_port.close()
        if self.out_port:
            self.out_port.close()


# ═══════════════════════════════════════════════════════════════
# CC Human-Readable Conversion
# ═══════════════════════════════════════════════════════════════

def cc_to_human(cc: int, value: int) -> str:
    """Convert CC value to human-readable text."""
    info = CC_MAP.get(cc)
    if not info:
        return str(value)
    name = info[0]
    if "Osc1 Type" in name:
        return f"{value} ({OSC1_ENGINES.get(value, '?')})"
    if "Osc2 Type" in name:
        return f"{value} ({OSC2_ENGINES.get(value, '?')})"
    if "Filter Type" in name:
        return f"{value} ({VCF_TYPES.get(value, '?')})"
    if "FX" in name and "Type" in name:
        return f"{value} ({FX_TYPES.get(value, '?')})"
    if "LFO" in name and "Shape" in name:
        return f"{value} ({LFO_WAVES.get(value, '?')})"
    if "Sustain Pedal" in name:
        return f"{value} ({'ON' if value >= 64 else 'OFF'})"
    if "All " in name:
        return "EXECUTED"
    return str(value)


def human_to_cc(cc: int, text: str) -> Optional[int]:
    """Convert human-readable text to CC value."""
    info = CC_MAP.get(cc)
    if not info:
        try:
            return max(0, min(127, int(text)))
        except ValueError:
            return None

    name, lo, hi = info
    try:
        return max(lo, min(hi, int(text)))
    except ValueError:
        pass

    t = text.lower().strip()
    t_nospace = t.replace(' ', '').replace('_', '')
    
    def _match(n: str) -> bool:
        nl = n.lower()
        ns = nl.replace(' ', '').replace('_', '')
        ts = t_nospace
        if t in nl or ts in ns or nl.startswith(t) or t.startswith(nl):
            return True
        # Fuzzy: all chars of input appear in name with at least same frequency
        # (handles 'EQ3' → '3 Bands EQ', 'BitCrusher' → 'Bit Crusher')
        if len(ts) < 3:
            return False
        tc = Counter(ts)
        nc = Counter(ns)
        return all(nc[c] >= tc[c] for c in tc)
    
    if "Osc1 Type" in name:
        for v, n in OSC1_ENGINES.items():
            if _match(n):
                return v
    if "Osc2 Type" in name:
        for v, n in OSC2_ENGINES.items():
            if _match(n):
                return v
    if "Filter Type" in name:
        for v, n in VCF_TYPES.items():
            if _match(n):
                return v
    if "FX" in name and "Type" in name:
        for v, n in FX_TYPES.items():
            if _match(n):
                return v
    if "Shape" in name:
        for v, n in LFO_WAVES.items():
            if _match(n):
                return v
    if t in ("on", "true", "1"):
        return 127
    if t in ("off", "false", "0"):
        return 0
    return None


# ═══════════════════════════════════════════════════════════════
# CLI Commands
# ═══════════════════════════════════════════════════════════════

def cmd_ports(args):
    """List MIDI ports."""
    mgr = MidiManager(args.port)
    mgr.list_ports()


def cmd_build(args):
    """Build a SysEx message and print it."""
    try:
        data = build_sysex(args.dev or MINIFREAK_DEV_ID, args.type,
                           args.param, args.value, args.bits14)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    parsed = parse_sysex(data)
    print(f"Built: {parsed}")
    print(f"Hex:   {parsed.hex_str()}")

    if args.send:
        mgr = MidiManager(args.port)
        if mgr.open():
            mgr.send_sysex(data)
            resp = mgr.wait_response(args.timeout)
            if resp:
                print(f"← {resp.hex()}")
            mgr.close()
    return 0


def cmd_request(args):
    """Send parameter request."""
    data = build_request(args.dev or MINIFREAK_DEV_ID, args.param)
    parsed = parse_sysex(data)
    print(f"Request: {parsed}")
    print(f"Hex:     {parsed.hex_str()}")

    mgr = MidiManager(args.port)
    if not mgr.open():
        return 1
    mgr.send_sysex(data)
    resp = mgr.wait_response(args.timeout)
    if resp:
        if resp.type == 'sysex':
            p = parse_sysex(resp.data)
            if p:
                print(f"← {p}")
                if p.type_cat == "Param":
                    print(f"  Value: {p.value_lo}" + (f" (14-bit: {p.value_14bit})" if p.is_14bit else ""))
            else:
                print(f"← {resp.hex()}")
        else:
            print(f"← {resp}")
    else:
        print("No response (timeout)")
    mgr.close()
    return 0


def cmd_cc(args):
    """Send MIDI CC."""
    value = args.value
    if args.human:
        parsed = human_to_cc(args.cc, args.value_str or str(value))
        if parsed is None:
            print(f"ERROR: cannot parse value '{args.value_str}' for CC#{args.cc}")
            return 1
        value = parsed

    info = CC_MAP.get(args.cc, ("Unknown", 0, 127))
    print(f"CC#{args.cc} ({info[0]}) = {value} ({cc_to_human(args.cc, value)})")

    mgr = MidiManager(args.port)
    if not mgr.open():
        return 1
    mgr.send_cc(args.cc, value, args.channel)
    mgr.close()
    return 0


def cmd_note(args):
    """Send Note On/Off."""
    mgr = MidiManager(args.port)
    if not mgr.open():
        return 1
    mgr.send_note(args.note, args.velocity, args.channel)
    if args.duration > 0:
        time.sleep(args.duration)
        mgr.send_note_off(args.note, args.channel)
    mgr.close()
    return 0


def cmd_listen(args):
    """Listen for MIDI messages."""
    mgr = MidiManager(args.port)
    if not mgr.open():
        return 1
    msgs = mgr.listen(args.duration, parse=True)
    print(f"\n=== {len(msgs)} messages received ===")
    for i, msg in enumerate(msgs):
        if isinstance(msg, SysExMessage):
            print(f"  [{i}] {msg}")
        elif hasattr(msg, 'type'):
            print(f"  [{i}] {msg}")
    mgr.close()
    return 0


def cmd_parse(args):
    """Parse hex SysEx string."""
    hex_str = args.hex.replace(" ", "").replace("0x", "").replace(",", "")
    try:
        data = bytes.fromhex(hex_str)
    except ValueError as e:
        print(f"ERROR: invalid hex: {e}")
        return 1

    msgs = parse_all_sysex(data)
    if not msgs:
        print("No valid Arturia SysEx found in input")
        # Show raw anyway
        print(f"Raw: {' '.join(f'{b:02X}' for b in data)}")
        return 1

    for msg in msgs:
        print(f"┌─ {msg}")
        print(f"│  Type: {msg.type_name} ({msg.type_cat})")
        print(f"│  Device: 0x{msg.device_id:02X}")
        print(f"│  Param: {msg.param_idx}")
        if msg.is_14bit and msg.value_hi is not None:
            print(f"│  Value: {msg.value_lo} + {msg.value_hi} = {msg.value_14bit} (14-bit)")
        else:
            print(f"│  Value: {msg.value_lo}")
        if msg.payload:
            print(f"│  Payload: {msg.payload.hex()}")
        print(f"└  Hex: {msg.hex_str()}")
    return 0


def cmd_dump(args):
    """Preset dump request/response."""
    mgr = MidiManager(args.port)
    if not mgr.open():
        return 1

    # Send identity request first to verify connection
    print("Sending Identity Request...")
    mgr.send_sysex(build_identity_request())
    resp = mgr.wait_response(2.0)
    if resp and resp.type == 'sysex':
        print(f"← Device responded: {resp.hex()}")
    else:
        print("WARNING: no identity response — device may not be connected")

    # Request parameter 0 (first parameter of current preset)
    print(f"\nRequesting param #{args.param}...")
    mgr.send_sysex(build_request(args.dev or MINIFREAK_DEV_ID, args.param))
    resp = mgr.wait_response(args.timeout)
    if resp and resp.type == 'sysex':
        p = parse_sysex(resp.data)
        if p:
            print(f"← {p}")
    else:
        print("No response")

    mgr.close()
    return 0


def cmd_info(args):
    """Show MiniFreak MIDI reference info."""
    print("╔══════════════════════════════════════════════════╗")
    print("║     Arturia MiniFreak — MIDI Reference         ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"\nManufacturer ID: {' '.join(f'{b:02X}' for b in ARTURIA_MFR)}")
    print(f"Device ID:       0x{MINIFREAK_DEV_ID:02X} (Broadcast: 0x{BROADCAST_DEV_ID:02X})")
    print(f"USB VID/PID:     0x1C75/0x0602")

    print(f"\n─── SysEx Message Types ({len(MSG_TYPES)}) ───")
    for t, (name, cat) in sorted(MSG_TYPES.items()):
        flag = " (14-bit)" if t in FOURTEEN_BIT_TYPES else ""
        print(f"  Type {t:3d} (0x{t:02X}): {name:20s} [{cat}]{flag}")

    print(f"\n─── CC Mapping ({len(CC_MAP)} CCs) ───")
    for cc in sorted(CC_MAP.keys()):
        name, lo, hi = CC_MAP[cc]
        print(f"  CC#{cc:3d} (0x{cc:02X}): {name:25s} [{lo}-{hi}]")

    print(f"\n─── Osc1 Engines ({len(OSC1_ENGINES)}) ───")
    for v, n in sorted(OSC1_ENGINES.items()):
        print(f"  {v:2d}: {n}")

    print(f"\n─── Osc2 Engines ({len(OSC2_ENGINES)}) ───")
    for v, n in sorted(OSC2_ENGINES.items()):
        print(f"  {v:2d}: {n}")

    print(f"\n─── Filter Types ({len(VCF_TYPES)}) ───")
    for v, n in sorted(VCF_TYPES.items()):
        print(f"  {v}: {n}")

    print(f"\n─── FX Types ({len(FX_TYPES)}) ───")
    for v, n in sorted(FX_TYPES.items()):
        print(f"  {v:2d}: {n}")

    print(f"\n─── LFO Waves ({len(LFO_WAVES)}) ───")
    for v, n in sorted(LFO_WAVES.items()):
        print(f"  {v}: {n}")

    return 0


# ═══════════════════════════════════════════════════════════════
# Main CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog="minifreak_sysex",
        description="MiniFreak MIDI SysEx Tool — Phase 8-2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--port", "-p", help="MIDI port name substring (auto-detects MiniFreak)")

    sub = parser.add_subparsers(dest="command", help="Command")

    # ports
    sub.add_parser("ports", help="List MIDI ports")

    # build
    b = sub.add_parser("build", help="Build SysEx message")
    b.add_argument("--type", "-t", type=lambda x: int(x, 0), required=True, help="Msg type (hex ok: 0x03)")
    b.add_argument("--param", type=int, required=True, help="Parameter index (0-127)")
    b.add_argument("--value", "-v", type=int, required=True, help="Value")
    b.add_argument("--bits14", action="store_true", help="14-bit value (lo+hi)")
    b.add_argument("--dev", type=lambda x: int(x, 0), help="Device ID (default: 0x02)")
    b.add_argument("--send", action="store_true", help="Send to device")
    b.add_argument("--timeout", type=float, default=2.0, help="Response timeout (seconds)")

    # request
    r = sub.add_parser("request", help="Request parameter value")
    r.add_argument("--param", type=int, required=True, help="Parameter index")
    r.add_argument("--dev", type=lambda x: int(x, 0), help="Device ID")
    r.add_argument("--timeout", type=float, default=2.0)

    # cc
    c = sub.add_parser("cc", help="Send MIDI CC")
    c.add_argument("cc", type=int, help="CC number")
    c.add_argument("value", type=int, help="CC value (0-127)")
    c.add_argument("--value-str", help="Human-readable value (e.g. 'Saw Up', 'Surgeon')")
    c.add_argument("--human", action="store_true", help="Enable human-readable value parsing")
    c.add_argument("--channel", type=int, default=0, help="MIDI channel (0-15)")

    # note
    n = sub.add_parser("note", help="Send Note On (+ optional duration)")
    n.add_argument("note", type=int, help="Note number (0-127)")
    n.add_argument("--velocity", type=int, default=100, help="Velocity (0-127)")
    n.add_argument("--duration", type=float, default=0.5, help="Duration in seconds (0=infinite)")
    n.add_argument("--channel", type=int, default=0)

    # listen
    l = sub.add_parser("listen", help="Listen for MIDI messages")
    l.add_argument("--duration", type=float, default=10.0, help="Listen duration (seconds)")

    # parse
    p = sub.add_parser("parse", help="Parse hex SysEx string")
    p.add_argument("hex", help="Hex string (spaces/commas ok, 0x prefix ok)")

    # dump
    d = sub.add_parser("dump", help="Preset dump request")
    d.add_argument("--param", type=int, default=0, help="Start parameter index")
    d.add_argument("--dev", type=lambda x: int(x, 0))
    d.add_argument("--timeout", type=float, default=2.0)

    # info
    sub.add_parser("info", help="Show MiniFreak MIDI reference")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    cmds = {
        "ports": cmd_ports,
        "build": cmd_build,
        "request": cmd_request,
        "cc": cmd_cc,
        "note": cmd_note,
        "listen": cmd_listen,
        "parse": cmd_parse,
        "dump": cmd_dump,
        "info": cmd_info,
    }

    return cmds[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
