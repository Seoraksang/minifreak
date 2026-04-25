#!/usr/bin/env python3
"""Parse USB descriptors from MiniFreak CM4 firmware."""
import glob, os, struct

CM4 = glob.glob(os.path.expanduser(
    "~/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
))[0]
data = open(CM4, "rb").read()
BASE = 0x08120000

# ═══ USB Config Descriptor ═══
print("=" * 60)
print("USB Configuration Descriptor @ 0x%08X" % (0x9759C + BASE))
print("=" * 60)

offset = 0x9759C
cfg = data[offset:offset + 256]
pos = 0
wTotalLength = struct.unpack_from('<H', cfg, 2)[0]
end = min(wTotalLength, len(cfg))

while pos < end:
    bL = cfg[pos]
    bT = cfg[pos + 1] if pos + 1 < len(cfg) else 0
    if bL < 2 or pos + bL > end:
        break
    c = cfg[pos:pos + bL]

    if bT == 0x02:
        print("  Configuration: wTotalLength=%d bNumInterfaces=%d bConfigValue=%d bmAttributes=0x%02X MaxPower=%dmA" % (
            wTotalLength, c[4], c[5], c[7], c[8] * 2))
    elif bT == 0x04:
        cls_map = {0xFF: "Vendor", 0xFE: "Misc", 0x01: "Audio", 0x0E: "Video", 0x02: "CDC", 0x08: "MassStorage"}
        cls_name = cls_map.get(c[5], "0x%02X" % c[5])
        print("  Interface #%d (alt=%d): %d EPs, class=%s sub=0x%02X proto=0x%02X" % (
            c[2], c[3], c[4], cls_name, c[6], c[7]))
    elif bT == 0x05:
        ep = c[2]
        d = "IN" if ep & 0x80 else "OUT"
        n = ep & 0x0F
        attr = c[3]
        sz = struct.unpack_from('<H', c, 4)[0]
        tt_map = {0: "Control", 1: "Isochronous", 2: "Bulk", 3: "Interrupt"}
        tt = tt_map.get(attr & 3, "?")
        print("    EP 0x%02X (%s%d): %s maxpkt=%d interval=%d" % (ep, d, n, tt, sz, c[6]))
    elif bT == 0x24:
        sub_map = {1: "MIDI_HEADER", 2: "MIDI_IN_JACK", 3: "MIDI_OUT_JACK", 4: "ELEMENT"}
        sub = c[2]
        nm = sub_map.get(sub, "CS_0x%02X" % sub)
        if sub == 1:
            rev = struct.unpack_from('<H', c, 4)[0]
            print("    CS %s bcdMSC=0x%04X" % (nm, rev))
        elif sub in (2, 3):
            jt = {1: "EMBEDDED", 2: "EXTERNAL"}.get(c[3], str(c[3]))
            print("    CS %s type=%s id=%d" % (nm, jt, c[4]))
        else:
            print("    CS %s raw=%s" % (nm, c.hex()))
    elif bT == 0x25:
        print("    CS_ENDPOINT: assocEP=%d" % c[2])
    elif bT == 0x0A:
        print("  IAD: firstIF=%d count=%d class=0x%02X sub=0x%02X proto=0x%02X" % (
            c[2], c[3], c[4], c[5], c[6]))
    else:
        print("  Unknown type=0x%02X len=%d raw=%s" % (bT, bL, c.hex()))

    pos += bL

# ═══ Device Descriptor Search ═══
print()
print("=" * 60)
print("USB Device Descriptor Search (VID=0x1C75)")
print("=" * 60)

vid_bytes = struct.pack('<H', 0x1C75)
p = 0
found = False
while True:
    p = data.find(vid_bytes, p)
    if p == -1:
        break
    for co in range(max(0, p - 16), p):
        if data[co] == 0x12 and data[co + 1] == 0x01:
            d = data[co:co + 18]
            bcd = struct.unpack_from('<H', d, 2)[0]
            if 0x0100 <= bcd <= 0x0300:
                v = struct.unpack_from('<H', d, 8)[0]
                pi = struct.unpack_from('<H', d, 10)[0]
                print("  @0x%08X:" % (co + BASE))
                print("    bcdUSB=0x%04X class=0x%02X pkt0=%d" % (bcd, d[4], d[7]))
                print("    VID=0x%04X PID=0x%04X" % (v, pi))
                print("    bcdDevice=0x%04X" % struct.unpack_from('<H', d, 12)[0])
                print("    iManuf=%d iProd=%d iSerial=%d bNumCfg=%d" % (d[14], d[15], d[16], d[17]))
                print("    Raw: %s" % d.hex())
                found = True
    p += 1

if not found:
    print("  Not found. Trying raw search for 0x12 0x01 0x00 0x02 (USB 2.0)...")
    target = bytes([0x12, 0x01, 0x00, 0x02])
    p = 0
    while True:
        p = data.find(target, p)
        if p == -1:
            break
        d = data[p:p + 18]
        v = struct.unpack_from('<H', d, 8)[0]
        pi = struct.unpack_from('<H', d, 10)[0]
        print("  @0x%08X: VID=0x%04X PID=0x%04X raw=%s" % (p + BASE, v, pi, d.hex()))
        p += 1

# ═══ Check CM7 too ═══
print()
cm7 = glob.glob(os.path.expanduser("~/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7*.bin"))
if cm7:
    cm7d = open(cm7[0], "rb").read()
    print("Checking CM7 binary (%s, %d bytes)..." % (cm7[0].split("/")[-1], len(cm7d)))
    # Config descriptor search
    for i in range(len(cm7d) - 9):
        if cm7d[i] == 0x09 and cm7d[i + 1] == 0x02:
            wTL = struct.unpack_from('<H', cm7d, i + 2)[0]
            if 20 < wTL < 512 and 1 <= cm7d[i + 4] <= 8:
                print("  CM7 Config @ offset 0x%X: wTotalLength=%d bNumIF=%d" % (i, wTL, cm7d[i + 4]))
    # Device descriptor with VID
    p = 0
    while True:
        p = cm7d.find(vid_bytes, p)
        if p == -1:
            break
        for co in range(max(0, p - 16), p):
            if cm7d[co] == 0x12 and cm7d[co + 1] == 0x01:
                d = cm7d[co:co + 18]
                bcd = struct.unpack_from('<H', d, 2)[0]
                if 0x0100 <= bcd <= 0x0300:
                    print("  CM7 DeviceDesc @ 0x%X: VID=0x%04X PID=0x%04X raw=%s" % (
                        co, struct.unpack_from('<H', d, 8)[0], struct.unpack_from('<H', d, 10)[0], d.hex()))
        p += 1
