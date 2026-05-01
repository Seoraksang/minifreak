import struct

with open('/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin', 'rb') as f:
    data = f.read()

CM7_BASE = 0x08020000
CM7_END = 0x080a0000

# Search for function pointer tables of various sizes
for size in [14, 15, 16, 10, 11, 12, 13, 20, 21]:
    found = []
    for offset in range(0, len(data) - size * 4, 4):
        vals = []
        valid = True
        for j in range(size):
            pos = offset + j * 4
            if pos + 4 > len(data):
                valid = False
                break
            val = struct.unpack('<I', data[pos:pos+4])[0]
            if not (CM7_BASE + 1 <= val <= CM7_END + 1) or not (val & 1):
                valid = False
                break
            vals.append(val)
        if valid:
            found.append((offset, vals))
    
    if found:
        print(f'\n=== {size}-entry function pointer tables ({len(found)} found) ===')
        for off, vals in found[:10]:
            addr = CM7_BASE + off
            print(f'  Table at 0x{addr:08x}:')
            for j, v in enumerate(vals):
                print(f'    [{j:2d}] 0x{v:08x}')
            print()

print('\nDone with pointer tables.')
