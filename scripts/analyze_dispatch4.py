import struct

with open('/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin', 'rb') as f:
    data = f.read()

CM7_BASE = 0x08020000

# The function at 0x08080a40 contains the pointer table at 0x080819f4
# Let's examine it to understand how the pointer table is used
func_start = 0x08080a40 - CM7_BASE

# Find function end
func_end = None
for i in range(0x08081a4c - CM7_BASE + 2, min(0x08081a4c - CM7_BASE + 2000, len(data)), 2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    if hw == 0xbd70:  # POP {r4-r6, pc}
        func_end = i + 2
        break
    if hw == 0xbdf0:  # POP {r4-r7, pc}
        func_end = i + 2
        break
    if hw == 0x4770:  # BX LR
        func_end = i + 2
        break

if func_end:
    print(f'Function 0x08080a40: {func_end - func_start} bytes (ends at 0x{CM7_BASE+func_end:08x})')
else:
    func_end = 0x08081a4c - CM7_BASE + 2000
    print(f'Function 0x08080a40: could not find end, scanning {func_end - func_start} bytes')

# Find all LDR Rx, [PC, #imm] in this function that point to the pointer table
print('\n=== PC-relative loads in function targeting pointer table area ===')
for i in range(func_start, func_end - 1, 2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    if (hw & 0xf800) == 0x4800:  # LDR Rx, [PC, #imm*4]
        reg = (hw >> 8) & 7
        imm = (hw & 0xff) * 4
        pc_addr = (CM7_BASE + i) & ~3
        target = pc_addr + 4 + imm
        if 0x080819f0 <= target <= 0x08081a50:
            print(f'  0x{CM7_BASE+i:08x}: LDR R{reg}, [PC, #{imm}] -> 0x{target:08x}')

# Now look at the code just before the literal pool to understand the dispatch
print('\n=== Code before literal pool (0x080819b0 - 0x080819f0) ===')
for i in range(0x080819b0 - CM7_BASE, 0x080819f0 - CM7_BASE, 2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    addr = CM7_BASE + i
    desc = ''
    if (hw & 0xf800) == 0x4800:
        reg = (hw >> 8) & 7
        imm = (hw & 0xff) * 4
        pc_addr = (addr & ~3)
        target = pc_addr + 4 + imm
        desc = f' LDR R{reg}, [PC, #{imm}] -> 0x{target:08x}'
    elif (hw & 0xff00) == 0x2800:
        desc = f' CMP R{(hw>>8)&7}, #{hw&0xff}'
    elif (hw & 0xf800) == 0x1c00:
        rd = (hw >> 8) & 7
        rs = (hw >> 3) & 7
        imm3 = (hw >> 6) & 7
        imm2 = hw & 3
        imm = imm3 * 4 + imm2  # actually it's (imm3:imm2) = (bits 8:6):(bits 1:0)
        # Actually the encoding is: ADD Rd, Rn, #imm3_2 where imm = imm3*4+imm2 is wrong
        # Thumb ADD Rd, Rm, #imm3: 000 11 10 0 Rm(3) imm3(3) Rd(3)
        # Wait, let me just show the hex
        desc = f' ADD/offset'
    elif hw == 0x4770:
        desc = ' BX LR'
    elif hw == 0xbd70:
        desc = ' POP {r4-r6, pc}'
    elif hw == 0xbdf0:
        desc = ' POP {r4-r7, pc}'
    elif (hw & 0xf000) == 0xd000:
        cond = hw & 0xf
        cond_names = ['EQ','NE','CS','CC','MI','PL','VS','VC','HI','LS','GE','LT','GT','LE','','']
        soff = (hw >> 4) & 0xff
        if soff > 127: soff -= 256
        soff *= 2
        if cond < 15:
            desc = f' B{cond_names[cond]} {soff:+d}'
    elif (hw & 0xf800) == 0x4600:
        rd = (hw >> 8) & 7
        # 0100 0110 D Rm3 Rd3 Rm2
        # High bit = D (1), low 3 bits = Rm, bits 2:0 of rd
        rm = ((hw & 0x7) << 3) | ((hw >> 3) & 7)
        # Actually: MOV Rd, Rm where D:Rd3 = destination, Rm3:Rm = source
        # 0100 0110 D Rm3(3) Rd3(3) Rm2(2)
        # dest = (D << 3) | Rd3
        # src = (Rm3 << 2) | Rm2
        # Hmm, this is getting complex. Let me just show it.
        desc = f' MOV (0x{hw:04x})'
    print(f'  0x{addr:08x}: {hw:04x}{desc}')

# 6. Also examine FUN_08034338 (Filter Coefficients / Waveshaper)
print('\n\n=== FUN_08034338 (Filter Coefficients / Waveshaper) ===')
func_start2 = 0x08034338 - CM7_BASE
func_size2 = 5046

# Look for CMP with mode numbers
print('CMP instructions:')
for i in range(func_start2, func_start2 + func_size2 - 1, 2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    if (hw & 0xff00) == 0x2800:
        val = hw & 0xff
        if val <= 20:
            print(f'  0x{CM7_BASE+i:08x}: CMP R{(hw>>8)&7}, #{val}')

# 7. Search for the area 0x08080a40 - let's see what kind of function this is
# Look at the first instructions
print('\n=== FUN_08080a40 first instructions ===')
for i in range(func_start, func_start + 60, 2):
    hw = struct.unpack('<H', data[i:i+2])[0]
    addr = CM7_BASE + i
    desc = ''
    if hw == 0xb570: desc = ' PUSH {r4-r6, lr}'
    elif hw == 0xb5f0: desc = ' PUSH {r4-r7, lr}'
    elif (hw & 0xf800) == 0x4800:
        reg = (hw >> 8) & 7
        imm = (hw & 0xff) * 4
        pc_addr = (addr & ~3)
        target = pc_addr + 4 + imm
        desc = f' LDR R{reg}, [PC, #{imm}] -> 0x{target:08x}'
    elif (hw & 0xf800) == 0x6800:
        desc = f' LDR R{(hw>>11)&7}, [R{(hw>>3)&7}, #{(hw&7)*4}]'
    elif (hw & 0xf800) == 0x6000:
        desc = f' STR R{(hw>>11)&7}, [R{(hw>>3)&7}, #{(hw&7)*4}]'
    elif (hw & 0xff00) == 0x2800:
        desc = f' CMP R{(hw>>8)&7}, #{hw&0xff}'
    print(f'  0x{addr:08x}: {hw:04x}{desc}')
