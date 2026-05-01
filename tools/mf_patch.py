#!/usr/bin/env python3
"""
MiniFreak Firmware Patcher
Phase 8-3 | Arturia MiniFreak Reverse Engineering

Binary patching tool for .mnf firmware packages.
- Extract/inspect firmware binaries from .mnf (ZIP container)
- Apply YAML-defined patches (pattern search + byte replacement)
- Create patched .mnf packages
- Verify patches with SHA256 checksums
- Revert patches from backup

Key facts from Phase 7-4:
  - .mnf = ZIP container (store mode, no compression)
  - No internal CRC or integrity checks on binaries
  - 7 ARM binaries: CM4, CM7, FX, UI (screen, matrix, ribbon, kbd)
  - DFU method: image_num maps to flash targets
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

IMAGE_NAMES = [
    "minifreak_main_CM4",
    "minifreak_main_CM7",
    "minifreak_fx",
    "minifreak_ui_screen",
    "minifreak_ui_matrix",
    "minifreak_ui_ribbon",
    "minifreak_ui_kbd",
]

# STM32H7 Flash layout (from Phase 6 assessment)
FLASH_MAP = {
    0: {"name": "CM4", "base": 0x08120000, "size": 620224, "desc": "Flash Bank 2 — I/O, MIDI, UI comms"},
    1: {"name": "CM7", "base": 0x08000000, "size": 524192, "desc": "Flash Bank 1 — Audio DSP"},
    2: {"name": "FX",  "base": None,        "size": 122640, "desc": "FX DSP core"},
    3: {"name": "UI_Screen", "base": None,  "size": 173372, "desc": "OLED display"},
    4: {"name": "UI_Matrix", "base": None,  "size": 69456,  "desc": "Button matrix + LED"},
    5: {"name": "UI_Ribbon", "base": None,  "size": 69232,  "desc": "Touch strip"},
    6: {"name": "UI_Kbd",   "base": None,   "size": 42032,  "desc": "Keybed scan"},
}

PATCHES_DIR = Path(__file__).parent / "patches"


# ═══════════════════════════════════════════════════════════════
# Firmware Package Manager
# ═══════════════════════════════════════════════════════════════

@dataclass
class FirmwareImage:
    """A single firmware binary within .mnf package."""
    image_num: int
    filename: str
    data: bytes
    original_hash: str = ""
    patched_hash: str = ""

    @property
    def name(self) -> str:
        return FLASH_MAP.get(self.image_num, {}).get("name", f"Image#{self.image_num}")

    @property
    def size(self) -> int:
        return len(self.data)

    @property
    def flash_base(self) -> Optional[int]:
        return FLASH_MAP.get(self.image_num, {}).get("base")

    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()

    def find_pattern(self, pattern: bytes, max_results: int = 10) -> list[int]:
        """Find all occurrences of byte pattern."""
        offsets = []
        start = 0
        while len(offsets) < max_results:
            idx = self.data.find(pattern, start)
            if idx == -1:
                break
            offsets.append(idx)
            start = idx + 1
        return offsets

    def read_bytes(self, offset: int, length: int) -> bytes:
        return self.data[offset:offset + length]

    def write_bytes(self, offset: int, new_data: bytes) -> None:
        """Patch bytes at offset (in-place)."""
        end = offset + len(new_data)
        if offset < 0 or end > len(self.data):
            raise ValueError(f"Out of bounds: offset={offset}, len={len(new_data)}, image_size={len(self.data)}")
        self.data = self.data[:offset] + new_data + self.data[end:]


@dataclass
class FirmwarePackage:
    """Represents a .mnf firmware package."""
    path: Path
    info: dict = field(default_factory=dict)
    images: list[FirmwareImage] = field(default_factory=list)
    backup_path: Optional[Path] = None

    @classmethod
    def open(cls, path: str | Path) -> 'FirmwarePackage':
        """Open an .mnf firmware package."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Firmware not found: {path}")

        pkg = cls(path=path)

        with zipfile.ZipFile(path, 'r') as z:
            # Read info.json
            try:
                pkg.info = json.loads(z.read('info.json'))
            except KeyError:
                pkg.info = {}

            # Read all binary images
            for entry in z.infolist():
                if entry.filename.endswith('.bin'):
                    data = z.read(entry.filename)
                    # Determine image_num from filename
                    num = cls._get_image_num(entry.filename, pkg.info)
                    img = FirmwareImage(
                        image_num=num,
                        filename=entry.filename,
                        data=data,
                        original_hash=hashlib.sha256(data).hexdigest(),
                    )
                    pkg.images.append(img)

        pkg.images.sort(key=lambda i: i.image_num)
        return pkg

    @staticmethod
    def _get_image_num(filename: str, info: dict) -> int:
        """Determine image number from filename."""
        for img in info.get("images", []):
            if img.get("file_name") == filename:
                return img.get("image_num", 0)
        # Fallback: parse from IMAGE_NAMES
        for i, prefix in enumerate(IMAGE_NAMES):
            if filename.startswith(prefix):
                return i
        return 0

    def get_image(self, name_or_num: str | int) -> Optional[FirmwareImage]:
        """Get firmware image by name or number."""
        if isinstance(name_or_num, str):
            name_or_num = name_or_num.upper()
            for img in self.images:
                if img.name.upper() == name_or_num:
                    return img
            # Try by prefix
            for img in self.images:
                if name_or_num in img.name.upper() or name_or_num in img.filename.upper():
                    return img
            return None
        else:
            for img in self.images:
                if img.image_num == name_or_num:
                    return img
            return None

    def create_backup(self, backup_dir: Optional[str] = None) -> Path:
        """Create a backup of the original .mnf."""
        if backup_dir:
            dest = Path(backup_dir) / self.path.name
        else:
            dest = self.path.with_suffix('.mnf.bak')
        shutil.copy2(self.path, dest)
        self.backup_path = dest
        return dest

    def save(self, output_path: Optional[str | Path] = None) -> Path:
        """Save patched firmware as new .mnf package."""
        if output_path:
            out = Path(output_path)
        else:
            # Auto-generate name: original_patched_<timestamp>.mnf
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = self.path.with_stem(f"{self.path.stem}_patched_{ts}")

        # Create ZIP in store mode (no compression, matching original)
        with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_STORED) as z:
            # Write info.json
            info_bytes = json.dumps(self.info, indent=2).encode()
            z.writestr('info.json', info_bytes)

            # Write all images
            for img in self.images:
                img.patched_hash = img.sha256()
                z.writestr(img.filename, img.data)

        return out

    def is_modified(self) -> bool:
        """Check if any image has been modified."""
        for img in self.images:
            if img.sha256() != img.original_hash:
                return True
        return False

    def diff_summary(self) -> list[dict]:
        """Show which images were modified."""
        results = []
        for img in self.images:
            current = img.sha256()
            modified = current != img.original_hash
            results.append({
                "image": img.name,
                "num": img.image_num,
                "filename": img.filename,
                "size": img.size,
                "modified": modified,
                "original_hash": img.original_hash[:16],
                "current_hash": current[:16],
            })
        return results


# ═══════════════════════════════════════════════════════════════
# Patch Definition & Application
# ═══════════════════════════════════════════════════════════════

@dataclass
class PatchRule:
    """A single patch rule: find byte pattern and replace."""
    name: str
    description: str = ""
    target: str = ""       # Image name (CM4, CM7, etc.)
    target_num: int = -1   # Or image number
    find: bytes = b""      # Byte pattern to find
    replace: bytes = b""   # Replacement bytes
    offset: int = -1       # Exact offset (-1 = search for pattern)
    find_mask: bytes = b"" # Optional mask (? = wildcard)

    def validate(self) -> list[str]:
        """Validate patch rule."""
        errors = []
        if not self.name:
            errors.append("Patch name required")
        if not self.target and self.target_num < 0:
            errors.append("Target image required (name or number)")
        if self.offset >= 0:
            if not self.replace:
                errors.append("Replace bytes required for offset patch")
        else:
            if not self.find:
                errors.append("Find pattern required for search patch")
            if self.find_mask and len(self.find_mask) != len(self.find):
                errors.append("Mask length must match find pattern")
        if self.find and self.replace and len(self.replace) != len(self.find):
            errors.append(f"Replace length ({len(self.replace)}) must match find length ({len(self.find)})")
        return errors

    def apply(self, image: FirmwareImage, dry_run: bool = False) -> dict:
        """Apply this patch to a firmware image."""
        result = {
            "name": self.name,
            "status": "skip",
            "offset": -1,
            "original": "",
            "patched": "",
            "message": "",
        }

        if self.offset >= 0:
            # Direct offset patch
            result["offset"] = self.offset
            result["original"] = image.read_bytes(self.offset, len(self.replace)).hex()
            if not dry_run:
                image.write_bytes(self.offset, self.replace)
            result["status"] = "patched"
            result["patched"] = self.replace.hex()
            result["message"] = f"Offset 0x{self.offset:X}"
        else:
            # Pattern search
            if self.find_mask:
                # Masked search
                offsets = self._masked_find(image)
            else:
                offsets = image.find_pattern(self.find, max_results=1)

            if not offsets:
                result["status"] = "not_found"
                result["message"] = f"Pattern not found ({len(self.find)} bytes)"
                return result

            offset = offsets[0]
            result["offset"] = offset
            result["original"] = image.read_bytes(offset, len(self.find)).hex()

            if not dry_run:
                image.write_bytes(offset, self.replace)
            result["status"] = "patched"
            result["patched"] = self.replace.hex()
            result["message"] = f"Found at offset 0x{offset:X}"

        return result

    def _masked_find(self, image: FirmwareImage) -> list[int]:
        """Search with wildcard mask (? = don't care)."""
        offsets = []
        data = image.data
        pat_len = len(self.find)
        for i in range(len(data) - pat_len + 1):
            match = True
            for j in range(pat_len):
                if self.find_mask[j] != ord('?') and data[i + j] != self.find[j]:
                    match = False
                    break
            if match:
                offsets.append(i)
                break  # first match only
        return offsets

    @classmethod
    def from_dict(cls, d: dict) -> 'PatchRule':
        """Create from YAML/JSON dict."""
        find = bytes.fromhex(d["find"]) if isinstance(d.get("find"), str) else d.get("find", b"")
        replace = bytes.fromhex(d["replace"]) if isinstance(d.get("replace"), str) else d.get("replace", b"")
        mask = d.get("mask", "").encode() if isinstance(d.get("mask"), str) else d.get("mask", b"")

        return cls(
            name=d.get("name", "unnamed"),
            description=d.get("description", ""),
            target=d.get("target", ""),
            target_num=d.get("target_num", -1),
            find=find,
            replace=replace,
            offset=d.get("offset", -1),
            find_mask=mask,
        )


def load_patches_from_yaml(path: str | Path) -> list[PatchRule]:
    """Load patch definitions from YAML file."""
    if yaml is None:
        raise ImportError("PyYAML required: pip install pyyaml")
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)

    patches = []
    for item in data.get("patches", []):
        rule = PatchRule.from_dict(item)
        errors = rule.validate()
        if errors:
            print(f"  WARNING: Patch '{rule.name}' errors: {errors}")
            continue
        patches.append(rule)
    return patches


def load_patches_from_json(path: str | Path) -> list[PatchRule]:
    """Load patch definitions from JSON file."""
    path = Path(path)
    with open(path) as f:
        data = json.load(f)

    patches = []
    for item in data.get("patches", []):
        rule = PatchRule.from_dict(item)
        patches.append(rule)
    return patches


def load_patches(path: str | Path) -> list[PatchRule]:
    """Auto-detect format and load patches."""
    path = Path(path)
    if path.suffix in ('.yaml', '.yml'):
        return load_patches_from_yaml(path)
    elif path.suffix == '.json':
        return load_patches_from_json(path)
    else:
        # Try YAML first, then JSON
        try:
            return load_patches_from_yaml(path)
        except Exception:
            return load_patches_from_json(path)


def save_patches_json(patches: list[PatchRule], path: str | Path) -> None:
    """Save patches as JSON (always available, no YAML dep)."""
    data = {"patches": []}
    for p in patches:
        entry = {"name": p.name, "description": p.description}
        if p.target:
            entry["target"] = p.target
        if p.target_num >= 0:
            entry["target_num"] = p.target_num
        if p.offset >= 0:
            entry["offset"] = p.offset
        if p.find:
            entry["find"] = p.find.hex()
        if p.replace:
            entry["replace"] = p.replace.hex()
        if p.find_mask:
            entry["mask"] = p.find_mask.decode()
        data["patches"].append(entry)

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


# ═══════════════════════════════════════════════════════════════
# Disassembly Helpers
# ═══════════════════════════════════════════════════════════════

def decode_arm_instruction(data: bytes, offset: int) -> str:
    """Simple ARM (thumb) instruction decoder for display."""
    if offset + 4 > len(data):
        return "?? (out of bounds)"
    word = struct.unpack_from('<I', data, offset)[0]
    return f"0x{word:08X}"


def hexdump(data: bytes, offset: int = 0, length: int = 64) -> str:
    """Generate hexdump of data at given offset."""
    end = min(offset + length, len(data))
    lines = []
    for i in range(offset, end, 16):
        chunk = data[i:min(i + 16, end)]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"  {i:08X}: {hex_part:<48s} |{ascii_part}|")
    return "\n".join(lines)


def find_string_refs(data: bytes, search_str: str, max_results: int = 5) -> list[dict]:
    """Find string references in binary data."""
    pattern = search_str.encode('utf-8', errors='replace')
    results = []
    start = 0
    while len(results) < max_results:
        idx = data.find(pattern, start)
        if idx == -1:
            break
        # Get context
        ctx_start = max(0, idx - 8)
        ctx_end = min(len(data), idx + len(pattern) + 8)
        results.append({
            "offset": idx,
            "string": search_str,
            "context": data[ctx_start:ctx_end].hex(),
        })
        start = idx + 1
    return results


def open_standalone_bin(path: str | Path, image_num: int = 0) -> 'FirmwarePackage':
    """Open a standalone .bin file as a single-image package (for testing without .mnf)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Binary not found: {path}")

    pkg = FirmwarePackage(path=path)
    data = path.read_bytes()
    name = FLASH_MAP.get(image_num, {}).get("name", f"Image#{image_num}")

    img = FirmwareImage(
        image_num=image_num,
        filename=path.name,
        data=data,
        original_hash=hashlib.sha256(data).hexdigest(),
    )
    pkg.images.append(img)
    return pkg


# ═══════════════════════════════════════════════════════════════
# CLI Commands
# ═══════════════════════════════════════════════════════════════

def cmd_info(args):
    """Show firmware package info."""
    pkg = FirmwarePackage.open(args.firmware)
    print(f"╔{'═'*58}╗")
    print(f"║  MiniFreak Firmware: {pkg.path.name:<35s}║")
    print(f"╚{'═'*58}╝")

    print(f"\nVersion: {pkg.info.get('version_number', '?')}")
    print(f"Date:    {pkg.info.get('date', '?')}")
    print(f"Method:  {pkg.info.get('method', '?')}")
    print(f"VID/PID: {pkg.info.get('vendorid', '?')}/{pkg.info.get('productid', '?')}")

    print(f"\n{'─'*60}")
    print(f"{'#':>2} {'Image':<14} {'Size':>10} {'Hash (SHA256 first 16)':<40}")
    print(f"{'─'*60}")
    for img in pkg.images:
        h = img.original_hash[:16]
        base = f" @ 0x{img.flash_base:08X}" if img.flash_base else ""
        print(f"{img.image_num:>2} {img.name:<14} {img.size:>10,} {h:<40}{base}")

    total = sum(i.size for i in pkg.images)
    print(f"{'─'*60}")
    print(f"{'':>2} {'TOTAL':<14} {total:>10,}")


def cmd_extract(args):
    """Extract binaries from firmware package."""
    pkg = FirmwarePackage.open(args.firmware)
    out_dir = Path(args.output) if args.output else Path(args.firmware).parent / "extracted"
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = [args.image] if args.image else None
    extracted = 0

    for img in pkg.images:
        if targets and img.name.upper() not in [t.upper() for t in targets] and str(img.image_num) not in targets:
            continue
        out_path = out_dir / img.filename
        out_path.write_bytes(img.data)
        print(f"  Extracted: {img.filename} ({img.size:,} bytes) → {out_path}")
        extracted += 1

    print(f"\nExtracted {extracted} image(s) to {out_dir}")


def cmd_search(args):
    """Search for byte patterns in firmware."""
    pkg = FirmwarePackage.open(args.firmware)
    pattern = bytes.fromhex(args.pattern.replace(" ", "").replace("0x", ""))

    targets = [args.image] if args.image else [i.name for i in pkg.images]

    for target in targets:
        img = pkg.get_image(target)
        if not img:
            print(f"  Image '{target}' not found")
            continue

        offsets = img.find_pattern(pattern, max_results=args.max)
        print(f"\n[{img.name}] Pattern '{args.pattern}' → {len(offsets)} match(es)")
        for off in offsets:
            print(f"  Offset 0x{off:08X}:")
            if img.flash_base:
                print(f"    Flash:  0x{img.flash_base + off:08X}")
            print(hexdump(img.data, off, min(32, len(pattern) + 16)))


def cmd_find_str(args):
    """Search for strings in firmware."""
    pkg = FirmwarePackage.open(args.firmware)
    targets = [args.image] if args.image else [i.name for i in pkg.images]

    for target in targets:
        img = pkg.get_image(target)
        if not img:
            continue
        refs = find_string_refs(img.data, args.string)
        print(f"\n[{img.name}] '{args.string}' → {len(refs)} reference(s)")
        for ref in refs:
            addr = f"0x{img.flash_base + ref['offset']:08X}" if img.flash_base else f"0x{ref['offset']:08X}"
            print(f"  {addr} (offset 0x{ref['offset']:08X})")


def cmd_hexdump(args):
    """Hexdump a region of firmware."""
    pkg = FirmwarePackage.open(args.firmware)
    img = pkg.get_image(args.image)
    if not img:
        print(f"Image '{args.image}' not found")
        return 1

    offset = int(args.offset, 0)
    length = args.length

    print(f"[{img.name}] Offset 0x{offset:X} + 0x{length:X} bytes")
    if img.flash_base:
        print(f"Flash address: 0x{img.flash_base + offset:08X}")
    print(hexdump(img.data, offset, length))


def cmd_patch(args):
    """Apply patches from file."""
    if not Path(args.patch_file).exists():
        print(f"Patch file not found: {args.patch_file}")
        return 1

    pkg = FirmwarePackage.open(args.firmware)

    # Create backup
    if not args.dry_run and not args.no_backup:
        bak = pkg.create_backup(args.backup_dir)
        print(f"Backup: {bak}")

    # Load patches
    patches = load_patches(args.patch_file)
    print(f"Loaded {len(patches)} patch(es) from {args.patch_file}\n")

    results = []
    for patch in patches:
        # Find target image
        img = None
        if patch.target:
            img = pkg.get_image(patch.target)
        if not img and patch.target_num >= 0:
            img = pkg.get_image(patch.target_num)
        if not img:
            results.append({"name": patch.name, "status": "no_target", "message": f"Image '{patch.target or patch.target_num}' not found"})
            continue

        result = patch.apply(img, dry_run=args.dry_run)
        results.append(result)

        status_icon = {"patched": "✅", "not_found": "❌", "skip": "⏭", "no_target": "❌"}.get(result["status"], "?")
        print(f"  {status_icon} {result['name']}: {result['message']}")
        if result["status"] == "patched":
            print(f"     Original: {result['original']}")
            print(f"     Patched:  {result['patched']}")

    # Summary
    patched = sum(1 for r in results if r["status"] == "patched")
    failed = sum(1 for r in results if r["status"] in ("not_found", "no_target"))

    print(f"\n{'─'*40}")
    print(f"Results: {patched} patched, {failed} failed, {len(results) - patched - failed} skipped")

    if patched > 0 and not args.dry_run:
        out = pkg.save(args.output)
        print(f"Saved: {out}")

        # Save patch results
        results_path = out.with_suffix('.patch_results.json')
        with open(results_path, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "source": str(pkg.path),
                "output": str(out),
                "results": results,
            }, f, indent=2)
        print(f"Results: {results_path}")

    return 0 if failed == 0 else 1


def cmd_verify(args):
    """Verify patches by comparing with original."""
    pkg = FirmwarePackage.open(args.firmware)

    # Check if there's a patch_results.json alongside
    results_path = Path(args.firmware).with_suffix('.patch_results.json')
    if results_path.exists():
        with open(results_path) as f:
            results_data = json.load(f)
        original_path = results_data.get("source", "")
        print(f"Firmware: {pkg.path.name}")
        print(f"Patched from: {original_path}")
        print(f"Patch time:   {results_data.get('timestamp', '?')}")

        # Compare with original
        if original_path and Path(original_path).exists():
            orig_pkg = FirmwarePackage.open(original_path)
            modified_count = 0
            for orig, patched in zip(orig_pkg.images, pkg.images):
                if orig.data != patched.data:
                    modified_count += 1
                    # Find first difference
                    for i in range(len(orig.data)):
                        if orig.data[i] != patched.data[i]:
                            print(f"\n  🔴 {patched.name} MODIFIED at offset 0x{i:X}")
                            print(f"     Original: {orig.data[i:i+16].hex()}")
                            print(f"     Patched:  {patched.data[i:i+16].hex()}")
                            break
            if modified_count == 0:
                print("\n  🟢 No differences from original")
            print(f"\n  Modified images: {modified_count}/{len(pkg.images)}")
        else:
            print(f"\n  Original not found at: {original_path}")
    else:
        # Standalone verification — just show hashes
        print(f"Firmware: {pkg.path.name}")
        print(f"(No patch_results.json found — showing current hashes)")
        print()
        for img in pkg.images:
            print(f"  {img.name:<14} {img.size:>10,}  {img.sha256()[:32]}")


def cmd_create_patch(args):
    """Create a new patch definition interactively."""
    if yaml is None:
        print("PyYAML required for YAML output: pip install pyyaml")
        print("Falling back to JSON format.")

    patches = []

    # Parse arguments
    name = args.name
    target = args.target
    offset = int(args.offset, 0) if args.offset else -1
    find_hex = args.find
    replace_hex = args.replace
    desc = args.description or ""

    if not name or not target:
        print("ERROR: --name and --target required")
        return 1

    if offset >= 0:
        if not replace_hex:
            print("ERROR: --replace required for offset patches")
            return 1
        rule = PatchRule(
            name=name, description=desc, target=target,
            offset=offset, replace=bytes.fromhex(replace_hex),
        )
    elif find_hex:
        if not replace_hex:
            print("ERROR: --replace required")
            return 1
        find = bytes.fromhex(find_hex)
        replace = bytes.fromhex(replace_hex)
        if len(find) != len(replace):
            print(f"ERROR: find ({len(find)}B) and replace ({len(replace)}B) must be same length")
            return 1
        rule = PatchRule(
            name=name, description=desc, target=target,
            find=find, replace=replace,
        )
    else:
        print("ERROR: --offset or --find required")
        return 1

    errors = rule.validate()
    if errors:
        print(f"ERROR: {errors}")
        return 1

    patches.append(rule)

    # Save
    out_path = Path(args.output) if args.output else PATCHES_DIR / f"{name}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    save_patches_json(patches, out_path)
    print(f"Created patch: {out_path}")
    print(f"  Name: {name}")
    print(f"  Target: {target}")
    if offset >= 0:
        print(f"  Offset: 0x{offset:X}")
        print(f"  Replace: {replace_hex}")
    else:
        print(f"  Find:    {find_hex}")
        print(f"  Replace: {replace_hex}")
    return 0


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog="mf_patch",
        description="MiniFreak Firmware Patcher — Phase 8-3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("firmware", nargs="?", help="Path to .mnf firmware file")

    sub = parser.add_subparsers(dest="command", help="Command")

    # info
    sub.add_parser("info", help="Show firmware package info")

    # extract
    e = sub.add_parser("extract", help="Extract binaries from .mnf")
    e.add_argument("--image", "-i", help="Specific image to extract")
    e.add_argument("--output", "-o", help="Output directory")

    # search
    s = sub.add_parser("search", help="Search byte pattern in firmware")
    s.add_argument("pattern", help="Hex pattern (e.g., '48 8B 45 F8')")
    s.add_argument("--image", "-i", help="Target image")
    s.add_argument("--max", type=int, default=10, help="Max results")

    # find_str
    fs = sub.add_parser("find-str", help="Search for string in firmware")
    fs.add_argument("string", help="String to search")
    fs.add_argument("--image", "-i", help="Target image")

    # hexdump
    h = sub.add_parser("hexdump", help="Hexdump a firmware region")
    h.add_argument("--image", "-i", required=True, help="Target image")
    h.add_argument("--offset", required=True, help="Offset (hex ok: 0x1000)")
    h.add_argument("--length", type=int, default=64, help="Bytes to dump")

    # patch
    p = sub.add_parser("patch", help="Apply patches from file")
    p.add_argument("patch_file", help="Patch definition file (.json or .yaml)")
    p.add_argument("--output", "-o", help="Output .mnf path")
    p.add_argument("--dry-run", action="store_true", help="Simulate without writing")
    p.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    p.add_argument("--backup-dir", help="Backup directory")

    # verify
    sub.add_parser("verify", help="Verify modification status")

    # create-patch
    cp = sub.add_parser("create-patch", help="Create a new patch definition")
    cp.add_argument("--name", "-n", required=True, help="Patch name")
    cp.add_argument("--target", "-t", required=True, help="Target image (CM4, CM7, etc.)")
    cp.add_argument("--offset", help="Exact offset (hex ok)")
    cp.add_argument("--find", help="Byte pattern to find (hex)")
    cp.add_argument("--replace", "-r", help="Replacement bytes (hex)")
    cp.add_argument("--description", "-d", help="Description")
    cp.add_argument("--output", "-o", help="Output file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if not args.firmware and args.command != "create-patch":
        print("ERROR: firmware path required")
        return 1

    cmds = {
        "info": cmd_info,
        "extract": cmd_extract,
        "search": cmd_search,
        "find-str": cmd_find_str,
        "hexdump": cmd_hexdump,
        "patch": cmd_patch,
        "verify": cmd_verify,
        "create-patch": cmd_create_patch,
    }

    return cmds[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
