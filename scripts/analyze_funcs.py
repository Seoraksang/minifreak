import struct

with open('/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin', 'rb') as f:
    data = f.read()

CM7_BASE = 0x08020000

# 1. Look for the function containing the literal pool at 0x080819f4
# Search backwards from 0x080819c0 to find function prologue
print('=== Looking for function containing literal pool at 0x080819f4 ===')
# In Thumb code, function prologues often start with PUSH {r4-r7, lr} = 0xb5xx or 0xe92d
# Search backwards for a common prologue pattern
search_start = 0x080819c0 - CM7_BASE
# Look at 0x08061800 to 0x080819c0 range
for addr in range(0x08061800, 0x080819f4, 2):
    offset = addr - CM7_BASE
    hw = struct.unpack('<H', data[offset:offset+2])[0]
    # PUSH {r4-r7, lr} = 0xb5f0 or 0xb570
    # PUSH {r4-r11, lr} = 0xe92d 0x4ff0 (but this is 32-bit)
    # In Thumb-2: PUSH.W {r4-r11, lr} = 0xe92d4ff0
    if hw == 0xb5f0 or hw == 0xb570:
        print(f'  Possible function start at 0x{addr:08x} (PUSH {hw:04x})')

# 2. Analyze the small functions FN_A through FN_G in detail
print('\n=== Detailed function analysis ===')
funcs = {
    'NOP': 0x0806199d,
    'FN_A': 0x08061a0d,
    'FN_B': 0x08061a21,
    'FN_C': 0x08061b2d,
    'FN_D': 0x08061a51,
    'FN_E': 0x08061b0f,
    'FN_F': 0x08061b4f,
    'FN_G': 0x08061b17,
}

for name, addr in funcs.items():
    offset = addr - CM7_BASE
    # Find function end by looking for next function start or BX LR
    # Also calculate function size
    next_func = min(v for v in funcs.values() if v > addr) if any(v > addr for v in funcs.values()) else addr + 100
    func_size = next_func - addr
    
    code = data[offset:offset+func_size]
    print(f'\n{name} @ 0x{addr:08x}, size ~{func_size} bytes:')
    
    # Decode some Thumb instructions
    i = 0
    while i < len(code) - 1:
        hw = struct.unpack('<H', code[i:i+2])[0]
        
        # VFP/NEON instructions (32-bit)
        if (hw & 0xef00) == 0xef00 or (hw & 0xef00) == 0xee00:
            if i + 3 < len(code):
                w = struct.unpack('<I', code[i:i+4])[0]
                # Check if it's a 32-bit instruction
                if (w >> 16) & 0xff in [0xee, 0xef]:
                    # VFP instruction
                    i += 4
                    continue
        
        # BX LR = 0x4770
        if hw == 0x4770:
            print(f'    +{i:3d}: BX LR (return)')
            i += 2
            break
        
        # STR/LDR with immediate
        if (hw & 0xf800) == 0x6000:
            print(f'    +{i:3d}: STR Rx, [Ry, #imm] (0x{hw:04x})')
        elif (hw & 0xf800) == 0x6800:
            print(f'    +{i:3d}: LDR Rx, [Ry, #imm] (0x{hw:04x})')
        elif (hw & 0xff00) == 0x4600:
            print(f'    +{i:3d}: MOV Rx, Ry (0x{hw:04x})')
        elif (hw & 0xff00) == 0x4400:
            print(f'    +{i:3d}: ADD Rx, Ry (0x{hw:04x})')
        else:
            print(f'    +{i:3d}: 0x{hw:04x}')
        
        i += 2
        
        if i > 40:
            print(f'    ... (truncated)')
            break

# 3. Look for the number 14 (0x0e) used as comparison in switch-like patterns
# CMP Rx, #14 = 0x280e
print('\n=== Searching for CMP Rx, #14 (0x280e) pattern ===')
target_cmp = struct.pack('<H', 0x280e)
offset = 0
while True:
    pos = data.find(target_cmp, offset)
    if pos == -1:
        break
    addr = CM7_BASE + pos
    # Check context
    ctx_start = max(0, pos - 8)
    ctx_end = min(len(data), pos + 8)
    ctx = data[ctx_start:ctx_end]
    hex_ctx = ' '.join(f'{b:02x}' for b in ctx)
    print(f'  0x{addr:08x}: ...{hex_ctx}...')
    offset = pos + 1

# Also CMP Rx, #13 = 0x280d
print('\n=== Searching for CMP Rx, #13 (0x280d) ===')
target_cmp = struct.pack('<H', 0x280d)
offset = 0
while True:
    pos = data.find(target_cmp, offset)
    if pos == -1:
        break
    addr = CM7_BASE + pos
    print(f'  0x{addr:08x}')
    offset = pos + 1

# CMP Rx, #15 = 0x280f
print('\n=== Searching for CMP Rx, #15 (0x280f) ===')
target_cmp = struct.pack('<H', 0x280f)
offset = 0
while True:
    pos = data.find(target_cmp, offset)
    if pos == -1:
        break
    addr = CM7_BASE + pos
    print(f'  0x{addr:08x}')
    offset = pos + 1
