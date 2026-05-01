import struct

with open('/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin', 'rb') as f:
    data = f.read()

CM7_BASE = 0x08020000

# Dump the complete pointer table region from 0x080819e0 to 0x08081a30
start = 0x080819e0 - CM7_BASE
end = 0x08081a30 - CM7_BASE

print('=== Complete pointer table at 0x080819e0 ===')
for i in range(start, end, 4):
    val = struct.unpack('<I', data[i:i+4])[0]
    addr = CM7_BASE + i
    is_code = (CM7_BASE + 1 <= val <= 0x080a0001) and (val & 1)
    marker = ''
    if is_code:
        names = {
            0x0806199d: 'NOP/DEFAULT',
            0x08061a0d: 'FN_A',
            0x08061a21: 'FN_B', 
            0x08061b2d: 'FN_C',
            0x08061a51: 'FN_D',
            0x08061b0f: 'FN_E',
            0x08061b4f: 'FN_F',
            0x08061b17: 'FN_G',
        }
        marker = f'  <- {names.get(val, "UNKNOWN")}'
    print(f'  [{(i-start)//4:2d}] 0x{addr:08x}: 0x{val:08x}{marker}')

# Check what's before
print('\n=== Preceding area 0x080819c0-0x080819e0 ===')
for i in range(0x080819c0 - CM7_BASE, 0x080819e0 - CM7_BASE, 4):
    val = struct.unpack('<I', data[i:i+4])[0]
    addr = CM7_BASE + i
    is_code = (CM7_BASE + 1 <= val <= 0x080a0001) and (val & 1)
    marker = ' (code)' if is_code else ''
    print(f'  0x{addr:08x}: 0x{val:08x}{marker}')

# And after
print('\n=== Following area 0x08081a20-0x08081a60 ===')
for i in range(0x08081a20 - CM7_BASE, 0x08081a60 - CM7_BASE, 4):
    val = struct.unpack('<I', data[i:i+4])[0]
    addr = CM7_BASE + i
    is_code = (CM7_BASE + 1 <= val <= 0x080a0001) and (val & 1)
    marker = ' (code)' if is_code else ''
    print(f'  0x{addr:08x}: 0x{val:08x}{marker}')

# Now examine each unique function briefly
print('\n=== Unique functions in table ===')
unique_funcs = {
    0x0806199d: 'NOP/DEFAULT',
    0x08061a0d: 'FN_A',
    0x08061a21: 'FN_B', 
    0x08061b2d: 'FN_C',
    0x08061a51: 'FN_D',
    0x08061b0f: 'FN_E',
    0x08061b4f: 'FN_F',
    0x08061b17: 'FN_G',
}

for func_addr, name in unique_funcs.items():
    offset = func_addr - CM7_BASE
    # Show first 32 bytes of each function
    print(f'\n{name} @ 0x{func_addr:08x}:')
    # Calculate approximate function size by finding next function or pattern
    code = data[offset:offset+32]
    hex_str = ' '.join(f'{b:02x}' for b in code)
    print(f'  {hex_str}')
