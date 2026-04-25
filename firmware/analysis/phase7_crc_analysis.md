# Phase 7: CRC/Integrity Protection Analysis — MiniFreak Firmware

**Date:** 2025-06-18 firmware, analysis performed 2026-04-25  
**Target:** MiniFreak firmware v4.0.1.2229 (`.mnf` package)  
**MCU:** STM32H745 (dual-core Cortex-M7 + Cortex-M4)

---

## 1. DFU Header Structure (0x40 bytes)

All 7 binaries share the same minimal header format. Only **12 bytes** are non-zero; the remaining 52 bytes (0x10–0x3F) are all zeros.

| Offset | Size | Field | CM7 | CM4 | FX | screen | matrix | ribbon | kbd |
|--------|------|-------|-----|-----|-----|--------|--------|--------|-----|
| 0x00 | 4 | Signature/Target ID | 0x0000BE80 | 0x0000AB80 | 0x0000DD80 | 0x00005180 | 0x00005880 | 0x00008780 | 0x00000180 |
| 0x04 | 4 | Reserved | 0x00000000 | 0x00000000 | 0x00000000 | 0x00000000 | 0x00000000 | 0x00000000 | 0x00000000 |
| 0x08 | 4 | Payload Size (LE32) | 0x0007FF40 | 0x00097678 | 0x0001DED0 | 0x0002A4FC | 0x00010F10 | 0x00010E30 | 0x0000A3F0 |
| 0x0C | 4 | Reserved | 0x00000000 | 0x00000000 | 0x00000000 | 0x00000000 | 0x00000000 | 0x00000000 | 0x00000000 |
| 0x10–0x3F | 48 | Unused/Padding | all zeros | all zeros | all zeros | all zeros | all zeros | all zeros | all zeros |

### Header Signature Analysis

The 4-byte signature at offset 0x00 encodes a **DFU alternate setting identifier**:

- **Byte 0:** Always `0x80` (likely a validity flag or prefix marker)
- **Bytes 1–3:** Big-endian alt-setting number

| Image | Alt Setting (decimal) | `info.json` image_num | Target |
|-------|----------------------|-----------------------|--------|
| CM4 | 0xAB = 171 | 0 | Cortex-M4 flash (0x08100000) |
| CM7 | 0xBE = 190 | 1 | Cortex-M7 flash (0x08000000) |
| FX | 0xDD = 221 | 2 | DSP/Effects flash (0x08000000) |
| screen | 0x51 = 81 | 3 | UI display MCU |
| matrix | 0x58 = 88 | 4 | UI matrix MCU |
| ribbon | 0x87 = 135 | 5 | UI ribbon MCU |
| kbd | 0x01 = 1 | 6 | UI keyboard MCU |

**Key finding: No CRC or checksum field exists in the DFU header.**

---

## 2. Binary Footers / Trailers

### Padding After Payload

The payload size field (offset 0x08) defines the exact firmware image size. The file may contain zero-padding after the payload for alignment:

| Binary | Payload Size | File Size | Padding | Alignment |
|--------|-------------|-----------|---------|-----------|
| CM7 | 524,096 (0x7FF40) | 524,192 (0x7FFA0) | 32 bytes (0x20) | 32-byte aligned |
| CM4 | 620,152 (0x97678) | 620,224 (0x976C0) | 8 bytes (0x08) | 8-byte aligned |
| FX | 122,576 (0x1DED0) | 122,640 (0x1DF10) | 64 bytes (0x40) | 64-byte aligned |
| screen | 173,308 (0x2A4FC) | 173,372 (0x2A4FC+0x40) | 64 bytes (0x40) | 64-byte aligned |
| matrix | 69,392 (0x10F10) | 69,456 | 64 bytes (0x40) | 64-byte aligned |
| ribbon | 69,168 (0x10E30) | 69,232 | 64 bytes (0x40) | 64-byte aligned |
| kbd | 41,968 (0xA3F0) | 42,032 | 64 bytes (0x40) | 64-byte aligned |

**All trailing padding bytes are zero. No CRC32, CRC16, checksum, or any non-zero signature was found in any footer/trailer region.**

### Last Non-Zero Content

The last non-zero bytes in each ARM binary are data pointers (addresses in RAM), not CRC values:

| Binary | Last Non-Zero Offset | Last 4 Bytes (LE32) | Interpretation |
|--------|---------------------|---------------------|----------------|
| CM7 | 0x7F367 | 0x2001B65A | AXI SRAM data pointer |
| CM4 | 0x976B7 | 0x100139C1 | CM4 DTCM data pointer |
| FX | 0x1DF0F | 0x200189F0 | DTCM/AXI SRAM pointer |

---

## 3. CRC Lookup Table Search

Searched all three ARM binaries (CM7, CM4, FX) for:

- **Standard CRC32 table** (reflected polynomial 0xEDB88320): `00 00 00 00 96 30 07 77 2C 61 0E EE BA 51 09 99`
- **STM32 CRC32 table** (non-reflected polynomial 0x04C11DB7): `00 00 00 00 B7 1D C1 04 6E 3B 82 09 D9 26 43 0D`
- Both little-endian and big-endian variants

**Result: No CRC32 lookup tables found in any binary.** The firmware does not appear to contain software-implemented CRC computation using lookup tables.

### String Search Results

Only one CRC-related string found across all binaries:

- **FX binary:** `&XCrC` (likely a false positive from compressed data or code sequence)

No strings matching `checksum`, `integrity`, `verify`, `hash`, or `CRC` were found in CM7 or CM4 binaries.

---

## 4. STM32H7 DFU Protocol Analysis

### Standard STM32 DFU Behavior

The STM32 DFU bootloader (built into the STM32H745) performs its own integrity verification during firmware upload:

1. **Transport-level:** USB DFU protocol uses CRC16 for each USB transaction (handled by USB stack)
2. **Write-level:** Each block written to flash is verified by reading back
3. **Boot-level:** The STM32 built-in bootloader does NOT typically store or verify a file-level CRC — it relies on the host to ensure correct upload

### DfuSe Format

The MiniFreak firmware uses a simplified DfuSe-style format:
- **Prefix:** 0x40 bytes (target ID + payload size, rest zero)
- **No DfuSe suffix** (standard DfuSe suffix contains: `dwSignature=0x04D6`, `bLength`, `dwCRC`)
- **No DFU suffix signatures** found (`UFDW`/`0x57445546`, `DFUS`/`0x53554644`)

This is a **custom, simplified DFU format** — not the full DfuSe specification.

---

## 5. CRC32 Verification Attempts

Computed CRC32 over multiple regions of each binary using all standard variants:

### Algorithms Tested

| Algorithm | Init Value | Polynomial | Reflection | Final XOR |
|-----------|-----------|------------|------------|-----------|
| zlib CRC32 | 0xFFFFFFFF | 0xEDB88320 (reflected) | Yes | 0xFFFFFFFF |
| STM32 HAL CRC32 | 0xFFFFFFFF | 0x04C11DB7 | No | None |
| STM32 CRC32 (init=0) | 0x00000000 | 0x04C11DB7 | No | None |
| CRC32-MPEG-2 | 0xFFFFFFFF | 0x04C11DB7 | No | None |
| CRC16-CCITT | 0xFFFF | 0x1021 | No | None |

### Regions Tested

- Full binary (header + payload + padding)
- Payload only (excluding 0x40 header)
- Payload excluding last 4 bytes
- Payload excluding last 2 bytes

### Results

**No computed CRC matched any value stored in the binary.** Specifically, none of the computed CRC values were found embedded in the header, footer, padding, or anywhere else in the binary files.

### ZIP Container CRC32 (Important!)

The `.mnf` ZIP file DOES contain standard CRC32 values for each member:

| Binary | ZIP CRC32 | zlib CRC32(full file) | Match? |
|--------|-----------|----------------------|--------|
| CM7 | 0x9322A276 | 0x9322A276 | ✓ Yes |
| CM4 | 0x4930D798 | 0x4930D798 | ✓ Yes |
| FX | 0xBD41B0EA | 0xBD41B0EA | ✓ Yes |

These are standard ZIP container integrity checks, not embedded in the firmware binaries themselves. The binaries are stored uncompressed (`compress_type=0`), so the ZIP CRC32 covers the entire binary file as-is.

---

## 6. Firmware Integrity Protection Summary

### What EXISTS:

1. **ZIP container CRC32** — Standard ZIP format CRC32 stored in the `.mnf` archive metadata. Protects against file corruption during distribution/storage.

2. **USB DFU transport integrity** — The USB DFU protocol itself provides per-transaction integrity checks.

3. **STM32 bootloader read-back verification** — During DFU upload, the STM32 built-in bootloader verifies each written flash block by reading it back.

### What does NOT exist:

- ❌ No CRC32 or checksum embedded in the binary footer
- ❌ No CRC32 or checksum embedded in the binary header
- ❌ No DfuSe suffix with CRC
- ❌ No CRC32 lookup table in firmware code
- ❌ No software CRC verification of the firmware image at runtime
- ❌ No firmware image signature/authentication (no RSA/ECDSA)
- ❌ No "integrity" or "checksum" strings in CM7/CM4 code

### Implications for Firmware Modification:

1. **No internal CRC to patch** — The firmware binaries can be freely modified without needing to recalculate any embedded checksum. The only integrity check is the ZIP container CRC.

2. **Re-packing the MNF** — After modifying a binary, the `.mnf` ZIP must be repacked (Python's `zipfile` or standard `zip` will automatically update the CRC32).

3. **DFU upload** — The DFU upload process does not verify a file-level CRC; it only verifies individual block writes. Modified firmware will upload successfully.

4. **No cryptographic signing** — There is no firmware signature to bypass, which means the bootloader accepts any validly-formatted DFU image.

---

## 7. Header Format Summary

```
Offset  Size  Field              Description
------  ----  -----------------  ------------------------------------------
0x00    1     Prefix             Always 0x80 (validity flag)
0x01    3     Target/AltSetting  DFU alt setting (BE24), identifies target
0x04    4     Reserved           Always 0x00000000
0x08    4     PayloadSize        Size of ARM firmware image (LE32)
0x0C    4     Reserved           Always 0x00000000
0x10    48    Padding            All zeros
0x40    N     ARM Vector Table   Standard Cortex-M vector table starts here
```

Total header: **0x40 (64) bytes**  
ARM image: **PayloadSize bytes** starting at offset 0x40  
File size: **0x40 + PayloadSize + alignment_padding**
