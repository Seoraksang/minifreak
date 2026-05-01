import struct

with open('/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin', 'rb') as f:
    data = f.read()

CM7_BASE = 0x08020000

# 1. Check CMP #15 locations
print('=== CMP #15 locations with context ===')
for addr in [0x0807a9b7, 0x08083b82, 0x080918a5, 0x08095315, 0x0809539f]:
    offset = addr - CM7_BASE
    ctx_start = max(0, offset - 20)
    ctx_end = min(len(data), offset + 20)
    print(f'\n0x{addr:08x}:')
    for i in range(ctx_start, ctx_end, 2):
        hw = struct.unpack('<H', data[i:i+2])[0]
        marker = ' <<< CMP #15' if i == offset else ''
        # Decode simple Thumb instructions
        desc = ''
        if (hw & 0xff00) == 0x2800:
            desc = f' CMP R{(hw>>8)&7}, #{hw&0xff}'
        elif hw == 0xd100:
            desc = ' BNE (skip 1)'
        elif hw == 0xd002:
            desc = ' BEQ (skip 2)'
        elif hw == 0xd003:
            desc = ' BEQ (skip 3)'
        elif hw == 0xe002:
            desc = ' B +2'
        elif hw == 0xe003:
            desc = ' B +3'
        elif (hw & 0xf800) == 0x4800:
            desc = f' LDR R{(hw>>8)&7}, [PC, #{(hw&0xff)*4}]'
        print(f'  0x{CM7_BASE+i:08x}: {hw:04x}{desc}{marker}')

# 2. Search for the function at 0x08081386 that contains the pointer table literal pool
print('\n\n=== Function at 0x08081386 (contains pointer table) ===')
func_start = 0x08081386 - CM7_BASE
func_code = data[func_start:func_start+80]
hex_str = ' '.join(f'{b:02x}' for b in func_code)
print(f'First 80 bytes:')
for i in range(0, 80, 2):
    hw = struct.unpack('<H', func_code[i:i+2])[0]
    addr = 0x08081386 + i
    desc = ''
    if hw == 0xb570:
        desc = ' PUSH {r4-r6, lr}'
    elif hw == 0xbdf0:
        desc = ' POP {r4-r7, pc}'
    elif hw == 0xbd70:
        desc = ' POP {r4-r6, pc}'
    elif hw == 0x4770:
        desc = ' BX LR'
    elif (hw & 0xf800) == 0x4800:
        desc = f' LDR R{(hw>>8)&7}, [PC, #{(hw&0xff)*4}]'
    elif (hw & 0xff00) == 0x2800:
        desc = f' CMP R{(hw>>8)&7}, #{hw&0xff}'
    elif (hw & 0xf800) == 0x6800:
        desc = f' LDR R{(hw>>11)&7}, [R{(hw>>3)&7}, #{(hw&7)*4}]'
    elif (hw & 0xf000) == 0xd000:
        off_val = hw & 0xff
        if off_val > 127:
            off_val -= 256
        desc = f' B{["EQ","NE","CS","CC","MI","PL","VS","VC","HI","LS","GE","LT","GT","LE",""][hw&0xf]} +{off_val}'
    elif (hw & 0xff00) == 0x1c00:
        desc = f' ADD R{(hw>>8)&7}, R{(hw>>3)&7}, #{hw&7}'
    elif (hw & 0xf800) == 0x1c00:
        desc = f' ADD Rx, Ry, #imm'
    elif (hw & 0xf000) == 0x4000:
        desc = f' ALU: 0x{hw:04x}'
    print(f'  0x{addr:08x}: {hw:04x}{desc}')

# 3. Look at FUN_0803c2bc (VCF/Osc2 Processor) for filter dispatch
print('\n\n=== FUN_0803c2bc first 120 bytes ===')
func_start = 0x0803c2bc - CM7_BASE
func_code = data[func_start:func_start+120]
for i in range(0, 120, 2):
    hw = struct.unpack('<H', func_code[i:i+2])[0]
    addr = 0x0803c2bc + i
    if i % 32 == 0:
        print(f'\n  0x{addr:08x}:', end='')
    print(f' {hw:04x}', end='')
print()

# 4. Search for TBB/TBH (table branch) instructions
# TBB = 0xe8df (32-bit: 0xe8d0f000 + Rn)
# TBH = 0xe8df (32-bit: 0xe8d0f000 + Rn, LSL #1)
print('\n\n=== Searching for TBB/TBH instructions ===')
# TBB [Rn, Rm] = 0x4700 shifted = look for 0xf000 + register encoding
# In Thumb-2: TBB = 0xE8D0 Fn Tm where n=table base, m=index
# Encoding: 1110 1000 1101 0000 1111 0000 Rm4 Rm3..0 = E8D0F0xx
for offset in range(0, len(data) - 4, 2):
    w = struct.unpack('<I', data[offset:offset+4])[0]
    # TBB: E8D0 F0xy
    if (w & 0xfff0fff0) == 0xe8d0f000:
        addr = CM7_BASE + offset
        rm = w & 0xf
        print(f'  TBB [Rn, R{rm}] at 0x{addr:08x}')
    # TBH: E8D0 F1xy  
    if (w & 0xfff0fff0) == 0xe8d0f010:
        addr = CM7_BASE + offset
        rm = w & 0xf
        print(f'  TBH [Rn, R{rm}] at 0x{addr:08x}')
