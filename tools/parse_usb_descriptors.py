#!/usr/bin/env python3
"""Parse USB descriptors from MiniFreak CM4 firmware binary."""
import struct, sys

BIN = "/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__fw4_0_1_2229__2025_06_18.bin"
BASE = 0x08120000

data = open(BIN, "rb").read()

# ── USB Config Descriptor (already found at offset 0x9759C) ──
print("=" * 60)
print("USB Configuration Descriptor @ 0x%08X" % (0x9759C + BASE))
print("=" * 60)

offset = 0x9759C
config_data = data[offset:offset + 256]
pos = 0

while pos < len(config_data):
    bLen = config_data[pos]
    bType = config_data[pos + 1] if pos + 1 < len(config_data) else 0
    if bLen < 2 or pos + bLen > len(config_data):
        break

    addr = offset + pos + BASE
    chunk = config_data[pos:pos + bLen]

    if bType == 0x02:  # Config
        wTL = struct.unpack_from('<H', chunk, 2)[0]
        print("  Configuration Descriptor")
        print("    wTotalLength=%d, bNumInterfaces=%d" % (wTL, chunk[4]))
        print("    bConfigurationValue=%d, bmAttributes=0x%02X, MaxPower=%dmA" % (chunk[5], chunk[7], chunk[8] * 2))
    elif bType == 0x04:  # Interface
        print("  Interface #%d (alt=%d)" % (chunk[2], chunk[3]))
        print("    bNumEndpoints=%d, bInterfaceClass=0x%02X, SubClass=0x%02X, Proto=0x%02X" % (
            chunk[4], chunk[5], chunk[6], chunk[7]))
    elif bType == 0x05:  # Endpoint
        ep = chunk[2]
        d = 'IN' if ep & 0x80 else 'OUT'
        n = ep & 0x0F
        attr = chunk[3]
        sz = struct.unpack_from('<H', chunk, 4)[0]
        tt = {0: 'Control', 1: 'Isochronous', 2: 'Bulk', 3: 'Interrupt'}.get(attr & 3, '?')
        print("  Endpoint 0x%02X (%s%d) %s maxpkt=%d interval=%d" % (ep, d, n, tt, sz, chunk[6]))
    elif bType == 0x24:  # CS_INTERFACE
        sub = chunk[2]
        names = {1: 'MIDI_HEADER', 2: 'MIDI_IN_JACK', 3: 'MIDI_OUT_JACK', 4: 'MIDI_ELEMENT'}
        nm = names.get(sub, "CS_0x%02X" % sub)
        if sub == 1:
            rev = struct.unpack_from('<H', chunk, 4)[0]
            print("  CS_INTERFACE %s bcdMSC=0x%04X" % (nm, rev))
        elif sub in (2, 3):
            jtype = {1: 'EMBEDDED', 2: 'EXTERNAL'}.get(chunk[3], str(chunk[3]))
            print("  CS_INTERFACE %s type=%s id=%d" % (nm, jtype, chunk[4]))
        else:
            print("  CS_INTERFACE %s raw=%s" % (nm, chunk.hex()))
    elif bType == 0x25:  # CS_ENDPOINT
        print("  CS_ENDPOINT len=%d raw=%s" % (bLen, chunk.hex()))
    elif bType == 0x0A:  # IAD
        print("  IAD: firstIF=%d count=%d class=0x%02X sub=0x%02X proto=0x%02X" % (
            chunk[2], chunk[3], chunk[4], chunk[5], chunk[6]))
    else:
        print("  Unknown type=0x%02X len=%d raw=%s" % (bType, bLen, chunk.hex()))

    pos += bLen
    if pos < len(config_data) and config_data[pos] == 0:
        break

# ── Search for Device Descriptor ──
print()
print("=" * 60)
print("USB Device Descriptor Search")
print("=" * 60)

search_start = max(0, offset - 8192)
found = False
for i in range(search_start, offset):
    if data[i] == 0x12 and data[i + 1] == 0x01:
        bcdUSB = struct.unpack_from('<H', data, i + 2)[0]
        vid = struct.unpack_from('<H', data, i + 8)[0]
        pid = struct.unpack_from('<H', data, i + 10)[0]
        if vid == 0x1C75 or 0x0100 <= bcdUSB <= 0x0300:
            desc = data[i:i + 18]
            print("  Found @ offset 0x%X (0x%08X)" % (i, i + BASE))
            print("    bcdUSB=0x%04X" % struct.unpack_from('<H', desc, 2)[0])
            print("    bDeviceClass=0x%02X, bDeviceSubClass=0x%02X, bDeviceProtocol=0x%02X" % (desc[4], desc[5], desc[6]))
            print("    bMaxPacketSize0=%d" % desc[7])
            print("    idVendor=0x%04X, idProduct=0x%04X" % (vid, pid))
            print("    bcdDevice=0x%04X" % struct.unpack_from('<H', desc, 12)[0])
            print("    iManufacturer=%d, iProduct=%d, iSerial=%d" % (desc[14], desc[15], desc[16]))
            print("    bNumConfigurations=%d" % desc[17])
            print("    Raw: %s" % desc.hex())
            found = True
            break

if not found:
    # Broader search
    print("  Not found near config. Searching entire binary for VID=0x1C75...")
    target_vid = struct.pack('<H', 0x1C75)
    p = 0
    count = 0
    while count < 10:
        p = data.find(target_vid, p)
        if p == -1:
            break
        # Check if it could be a device descriptor
        check = max(0, p - 8)
        if data[check] == 0x12 and data[check + 1] == 0x01:
            desc = data[check:check + 18]
            print("  Found @ offset 0x%X" % check)
            print("    Raw: %s" % desc.hex())
        p += 1
        count += 1
