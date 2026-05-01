import struct

with open('/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin', 'rb') as f:
    data = f.read()

CM7_BASE = 0x08020000

# 1. Look at the complete function at 0x08081386
print('=== Function 0x08081386 (IIR smoothing function) ===')
func_start = 0x08081386 - CM7_BASE
# Find function end
for i in range(func_start + 2, min(func_start + 4000, len(data) - 1), 2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    # POP {r4-r6, pc} = 0xbd70, POP {r4-r7, pc} = 0xbdf0
    if hw == 0xbd70:
        func_end = i + 2
        break
else:
    func_end = func_start + 4000

print(f'Size: {func_end - func_start} bytes')
print(f'End: 0x{CM7_BASE + func_end:08x}')

# Look for LDR PC-relative instructions that reference the pointer table at 0x080819f4
print('\nSearching for references to pointer table 0x080819f4:')
for i in range(func_start, func_end - 3, 2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    if (hw & 0xf800) == 0x4800:
        # LDR Rn, [PC, #imm*4]
        imm = (hw & 0xff) * 4
        # PC = (addr & ~3) + 4
        pc_addr = (CM7_BASE + i) & ~3
        target_addr = pc_addr + 4 + imm
        if target_addr == 0x080819f4:
            reg = (hw >> 8) & 7
            print(f'  0x{CM7_BASE+i:08x}: LDR R{reg}, [PC, #{imm}] -> 0x{target_addr:08x}')

# 2. Now search the entire binary for references to 0x080819f4 (pointer table)
print('\n=== All references to pointer table 0x080819f4 ===')
for i in range(0, len(data) - 3, 2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    if (hw & 0xf800) == 0x4800:
        imm = (hw & 0xff) * 4
        pc_addr = (CM7_BASE + i) & ~3
        target_addr = pc_addr + 4 + imm
        if target_addr == 0x080819f4:
            reg = (hw >> 8) & 7
            print(f'  0x{CM7_BASE+i:08x}: LDR R{reg}, [PC, #{imm}] -> table')

# 3. Examine FUN_0803c2bc more carefully for filter mode dispatch
print('\n=== FUN_0803c2bc scan for switch/dispatch patterns ===')
func_start = 0x0803c2bc - CM7_BASE
func_end = func_start + 9250

# Look for CMP instructions with small values (0-15)
cmp_locations = []
for i in range(func_start, func_end - 1, 2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    if (hw & 0xff00) == 0x2800:
        val = hw & 0xff
        if val <= 20:
            cmp_locations.append((CM7_BASE + i, val))

if cmp_locations:
    print(f'  CMP instructions with small immediates:')
    for addr, val in cmp_locations:
        offset = addr - CM7_BASE
        ctx = data[max(0,offset-2):offset+4]
        hex_ctx = ' '.join(f'{b:02x}' for b in ctx)
        print(f'    0x{addr:08x}: CMP R0, #{val}  (ctx: {hex_ctx})')

# 4. Look at the CMP #15 at 0x0807a9b7 more carefully - it's within a function
# Check what function it's in
print('\n=== Context around CMP #15 at 0x0807a9b7 ===')
# Look at what precedes it - search for PUSH instruction
for i in range(0x0807a9b7 - CM7_BASE, max(0, 0x0807a9b7 - CM7_BASE - 2000), -2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    if hw == 0xb5f0 or hw == 0xb570 or hw == 0xb580 or hw == 0xe92d:
        print(f'  Possible function start: 0x{CM7_BASE+i:08x} (0x{hw:04x})')
        break

# 5. Check 0x080918a5 and 0x08095315 areas
print('\n=== Context around CMP #15 at 0x080918a5 ===')
for i in range(0x080918a5 - CM7_BASE, max(0, 0x080918a5 - CM7_BASE - 2000), -2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    if hw == 0xb5f0 or hw == 0xb570 or hw == 0xb580:
        print(f'  Possible function start: 0x{CM7_BASE+i:08x} (0x{hw:04x})')
        break

print('\n=== Context around CMP #15 at 0x08095315 ===')
for i in range(0x08095315 - CM7_BASE, max(0, 0x08095315 - CM7_BASE - 2000), -2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    if hw == 0xb5f0 or hw == 0xb570 or hw == 0xb580:
        print(f'  Possible function start: 0x{CM7_BASE+i:08x} (0x{hw:04x})')
        break
