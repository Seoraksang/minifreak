import struct, math

with open('/home/jth/hoon/minifreak/reference/firmware_extracted/minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin', 'rb') as f:
    data = f.read()

CM7_BASE = 0x08020000

# 1. Search for the function that contains the literal pool at 0x080819f4
# The pool is at 0x080819f4. In ARM Thumb, PC-relative loads use (PC & ~3) + 4
# For a LDR Rx, [PC, #imm] at address A, the target is ((A & ~3) + 4 + imm)
# We need imm = target - ((A & ~3) + 4)
# For the function to reference 0x080819f4, it must be within ±4095 bytes

print('=== Finding function containing literal pool at 0x080819f4 ===')
# Look for the nearest PUSH instruction before the code that references the pool
# The pool ends around 0x08081a4c
# Look for function starts between 0x08081a4c and 0x080819f4-4096

# Actually, let's search for all LDR Rx, [PC, #imm] that target 0x080819f4
# with various PC values
for func_addr in range(0x080819f4 - 4096, 0x080819f4 + 4, 2):
    pc_val = func_addr & ~3
    target = pc_val + 4  # base
    imm = 0x080819f4 - target
    if 0 <= imm <= 1020 and (imm % 4 == 0):
        imm_encoded = imm // 4
        if imm_encoded < 256:
            # Could be a LDR Rx, [PC, #imm] instruction
            hw_base = 0x4800  # LDR R0, [PC, #imm]
            for reg in range(8):
                hw = hw_base | (reg << 8) | imm_encoded
                offset = func_addr - CM7_BASE
                if offset + 2 <= len(data):
                    actual = struct.unpack('<H', data[offset:offset+2])[0]
                    if actual == hw:
                        print(f'  Found: 0x{func_addr:08x}: LDR R{reg}, [PC, #{imm}] -> 0x{0x080819f4:08x}')

# 2. Let's look at the code around 0x08081a4c (after the pointer table)
# to find the function that owns this literal pool
print('\n=== Code after literal pool 0x08081a4c ===')
# Search backwards for PUSH from 0x080819f4
for addr in range(0x080819f4, 0x080819f4 - 8000, -2):
    offset = addr - CM7_BASE
    if offset < 0:
        break
    hw = struct.unpack('<H', data[offset:offset+2])[0]
    # Check for 32-bit PUSH.W {r4-r11, lr}
    if hw == 0xe92d:
        next_hw = struct.unpack('<H', data[offset+2:offset+4])[0]
        if next_hw == 0x47b0:  # PUSH.W {r4-r11, lr} (but actually this encoding varies)
            print(f'  32-bit PUSH at 0x{addr:08x}')
    # PUSH {r4-r7, lr} = 0xb5f0
    if hw == 0xb5f0:
        # Verify it's a function start by checking it's not mid-stream
        # Look for BX LR or POP before it
        prev_offset = offset - 2
        if prev_offset >= 0:
            prev_hw = struct.unpack('<H', data[prev_offset:prev_offset+2])[0]
            if prev_hw == 0x4770 or prev_hw == 0xbdf0 or prev_hw == 0xbd70:
                print(f'  Function start (after return): 0x{addr:08x} (PUSH {{r4-r7, lr}})')
                break
    # Also check for BX LR before this
    if hw == 0x4770 or hw == 0xbdf0:
        # The next instruction should be a function start
        next_offset = offset + 2
        if next_offset + 2 <= len(data):
            next_hw = struct.unpack('<H', data[next_offset:next_offset+2])[0]
            if next_hw == 0xb5f0 or next_hw == 0xb570 or next_hw == 0xb580:
                print(f'  Function start at 0x{CM7_BASE+next_offset:08x} (after BX LR/POP, PUSH 0x{next_hw:04x})')

# 3. Search for what references the function pointer entries
# Look for the address of the NOP function 0x0806199d as a literal
print('\n=== References to NOP function 0x0806199d ===')
target_bytes = struct.pack('<I', 0x0806199d)
offset = 0
refs = []
while True:
    pos = data.find(target_bytes, offset)
    if pos == -1:
        break
    refs.append(CM7_BASE + pos)
    offset = pos + 1
print(f'  {len(refs)} references:')
for r in refs[:20]:
    print(f'    0x{r:08x}')

# 4. Look at the data tables around the 0x0809c8xx area
# The 2^(n/12) table at 0x0809c880 is a frequency ratio table
# Let's check what else is near it
print('\n=== Data region around 0x0809c800-0x0809ca00 ===')
for i in range(0x0809c800 - CM7_BASE, 0x0809ca00 - CM7_BASE, 16):
    vals = []
    for j in range(4):
        pos = i + j * 4
        if pos + 4 <= len(data):
            val = struct.unpack('<f', data[pos:pos+4])[0]
            vals.append(f'{val:10.4f}')
        else:
            vals.append('         ?')
    addr = CM7_BASE + i
    print(f'  0x{addr:08x}: {" ".join(vals)}')

# 5. Search for specific Butterworth Q values
# For Butterworth filters:
# 1st order: no Q parameter (1 pole)
# 2nd order: Q = 0.7071 (1/sqrt(2))
# 3rd order: Q = 1.0 (for the 2nd-order section), first section has Q=0.5
# 4th order (cascaded): Q = 0.5412, Q = 1.3066
print('\n=== Searching for Butterworth cascade Q values ===')
# Q1 = 0.5411961001 for 4th order Butterworth
q1 = 0.5411961001
q1_bytes = struct.pack('<f', q1)
pos = 0
while True:
    p = data.find(q1_bytes, pos)
    if p == -1:
        break
    print(f'  Q1=0.5412 at 0x{CM7_BASE+p:08x}')
    pos = p + 1

# Q2 = 1.3065629648 for 4th order Butterworth
q2 = 1.3065629648
q2_bytes = struct.pack('<f', q2)
pos = 0
while True:
    p = data.find(q2_bytes, pos)
    if p == -1:
        break
    print(f'  Q2=1.3066 at 0x{CM7_BASE+p:08x}')
    pos = p + 1

# For 6th order (3 cascaded biquads):
# Q1 = 0.5176380902
# Q2 = 0.7071067812 = 1/sqrt(2) (already found)
# Q3 = 1.9318516526
q3 = 0.5176380902
q3_bytes = struct.pack('<f', q3)
pos = 0
while True:
    p = data.find(q3_bytes, pos)
    if p == -1:
        break
    print(f'  Q3=0.5176 at 0x{CM7_BASE+p:08x}')
    pos = p + 1

q6 = 1.9318516526
q6_bytes = struct.pack('<f', q6)
pos = 0
while True:
    p = data.find(q6_bytes, pos)
    if p == -1:
        break
    print(f'  Q6=1.9319 at 0x{CM7_BASE+p:08x}')
    pos = p + 1
