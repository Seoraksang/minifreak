#!/usr/bin/env python3
"""
Phase 14-2: MiniFreak VST 파라미터 이름 목록 추출 및 분류
DLL strings에서 MiniFreak 파라미터 관련 문자열을 추출하여
전체 파라미터 매핑 테이블을 구성
"""

import re, sys, subprocess

DLL_PATH = sys.argv[1]

# strings 추출 (UTF-8 default)
result = subprocess.run(['strings', DLL_PATH], capture_output=True, text=True)
all_strings = result.stdout.split('\n')

# MiniFreak 파라미터 이름 패턴
# 1. Oscillator: Osc1_*, Osc2_*, Osc_*
# 2. LFO: LFO1_*, LFO2_*, Lfo3_*
# 3. Filter: Cutoff*, Resonance*, Env_*
# 4. Envelope: Env_*, CycEnv_*
# 5. FX: Chorus, Delay, Reverb, Phaser, Flanger, Distortion, Bitcrusher
# 6. Matrix: Mod_S*, Pitch_S*, Velo_S*, Gate_S*, StepState_S*
# 7. Sequencer: Seq_*, ArpSeq_*, Arp_*
# 8. FM: AMOUNT_FM*, AMOUNT_AM*, AMOUNT_RES*
# 9. Automation: AutomReserved*_S*
# 10. Reserved: Reserved*_S*
# 11. General: RootNote, Scale, Transpose, etc.

param_patterns = {
    'oscillator': [
        r'^Osc[12]_', r'^Osc_', r'^Osc1', r'^Osc2', r'^OscType$',
        r'^Osc1Wavetable', r'^Osc2Wavetable', r'^Osc1Sample', r'^Osc2Sample',
    ],
    'lfo': [
        r'^LFO[123]_', r'^Lfo[123]_', r'^LFO1_', r'^LFO2_', r'^LFO3_',
    ],
    'filter': [
        r'^Cutoff', r'^Resonance', r'^Env_Attack', r'^Env_Decay', r'^Env_Release', r'^Env_Sustain',
        r'^Env_AttackCurve', r'^Env_DecayCurve', r'^Env_ReleaseCurve',
        r'^Cutoff_Cont', r'^Resonance_Cont',
    ],
    'envelope': [
        r'^CycEnv_', r'^ModEnvelope_',
    ],
    'fx': [
        r'^Chorus', r'^Delay', r'^Reverb', r'^Phaser', r'^Flanger',
        r'^Distortion', r'^Bitcrusher', r'^Octaver',
        r'^DEPTH_CHORUS', r'^Delay_Routing', r'^Reverb_Routing',
    ],
    'matrix_mod': [
        r'^Mod_S\d+_I\d+$', r'^MATRIX_',
    ],
    'matrix_pitch': [
        r'^Pitch_S\d+_I\d+$',
    ],
    'matrix_velocity': [
        r'^Velo_S\d+_I\d+$',
    ],
    'sequencer_step': [
        r'^StepState_S\d+$',
    ],
    'sequencer_gate': [
        r'^Gate_S\d+$',
    ],
    'sequencer': [
        r'^Seq_', r'^ArpSeq_', r'^Arp_', r'^Sequencer',
    ],
    'fm_routing': [
        r'^AMOUNT_FM', r'^AMOUNT_AM', r'^AMOUNT_RES',
    ],
    'automation': [
        r'^AutomReserved', r'^Autom_Full_Slot$',
    ],
    'reserved': [
        r'^Reserved[1234]_S\d+$', r'^ReservedRange$',
    ],
    'general': [
        r'^RootNote$', r'^Scale$', r'^Transpose$', r'^VOLUME$',
        r'^Aftertouch', r'^Pitch_Wheel$', r'^Mod_Wheel$',
        r'^Gen_', r'^Vca_', r'^VCA_', r'^Spread$',
        r'^Sustain_Polarity$', r'^SUSTAIN_TIME$',
        r'^Panel_Mode$', r'^Panic$',
        r'^Slot1_', r'^Slot2_', r'^SlotActive',
        r'^Chord_', r'^Chord_Length$', r'^Chord_Octave',
        r'^DistoType$', r'^FilterType$',
        r'^Pitch1_Mod_On$', r'^Pitch2_Mod_On$',
        r'^VeloMod_', r'^PitchReset$',
    ],
}

# 파라미터 후보 수집
params_by_category = {k: set() for k in param_patterns}
all_params = set()

for s in all_strings:
    s = s.strip()
    if not s or len(s) > 60:
        continue
    for cat, patterns in param_patterns.items():
        for pat in patterns:
            if re.match(pat, s):
                params_by_category[cat].add(s)
                all_params.add(s)
                break

# 출력
print("=" * 70)
print("MiniFreak VST 파라미터 이름 분류")
print("=" * 70)

total = 0
for cat, params in params_by_category.items():
    if not params:
        continue
    sorted_params = sorted(params)
    print(f"\n### {cat} ({len(sorted_params)}개)")
    for p in sorted_params:
        print(f"  {p}")
    total += len(sorted_params)

print(f"\n{'=' * 70}")
print(f"총 {total}개 파라미터 이름 (중복 제외: {len(all_params)}개)")
print(f"{'=' * 70}")

# 파라미터 ID 할당 추정
# MiniFreak의 파라미터 ID는 일반적으로 카테고리별로 연속 할당됨
# VST 파라미터 인덱스 = 순차적, HW 파라미터 ID = Collage DataParameterId.single

# 파라미터 구조 분석
print("\n## 파라미터 구조 분석")

# Matrix 슬롯 분석
mod_slots = sorted([p for p in all_params if p.startswith('Mod_S') and '_I' in p])
print(f"\nMod 매트릭스: {len(mod_slots)} 엔트리")
if mod_slots:
    # S0~S63 x I0~I3 = 64 x 4 = 256
    slots = set()
    inputs_per_slot = set()
    for p in mod_slots:
        m = re.match(r'Mod_S(\d+)_I(\d+)', p)
        if m:
            slots.add(int(m.group(1)))
            inputs_per_slot.add(int(m.group(2)))
    print(f"  Slots: {min(slots)}~{max(slots)} ({len(slots)}개)")
    print(f"  Inputs/slot: {min(inputs_per_slot)}~{max(inputs_per_slot)} ({len(inputs_per_slot)}개)")

# Pitch 슬롯 분석
pitch_slots = sorted([p for p in all_params if p.startswith('Pitch_S') and '_I' in p])
print(f"\nPitch 매트릭스: {len(pitch_slots)} 엔트리")
if pitch_slots:
    slots = set()
    inputs = set()
    for p in pitch_slots:
        m = re.match(r'Pitch_S(\d+)_I(\d+)', p)
        if m:
            slots.add(int(m.group(1)))
            inputs.add(int(m.group(2)))
    print(f"  Slots: {min(slots)}~{max(slots)} ({len(slots)}개)")
    print(f"  Inputs/slot: {min(inputs)}~{max(inputs)} ({len(inputs)}개)")

# Velocity 슬롯 분석
velo_slots = sorted([p for p in all_params if p.startswith('Velo_S') and '_I' in p])
print(f"\nVelocity 매트릭스: {len(velo_slots)} 엔트리")
if velo_slots:
    slots = set()
    inputs = set()
    for p in velo_slots:
        m = re.match(r'Velo_S(\d+)_I(\d+)', p)
        if m:
            slots.add(int(m.group(1)))
            inputs.add(int(m.group(2)))
    print(f"  Slots: {min(slots)}~{max(slots)} ({len(slots)}개)")
    print(f"  Inputs/slot: {min(inputs)}~{max(inputs)} ({len(inputs)}개)")

# Step State 분석
step_states = sorted([p for p in all_params if p.startswith('StepState_')])
print(f"\nStep State: {len(step_states)} 엔트리")

# Gate 분석
gates = sorted([p for p in all_params if p.startswith('Gate_S')])
print(f"Gate: {len(gates)} 엔트리")

# Reserved 분석
for prefix in ['AutomReserved1', 'Reserved1', 'Reserved2', 'Reserved3', 'Reserved4']:
    reserved = sorted([p for p in all_params if p.startswith(prefix)])
    if reserved:
        slots = set()
        for p in reserved:
            m = re.search(r'_S(\d+)$', p)
            if m:
                slots.add(int(m.group(1)))
        print(f"{prefix}: {len(reserved)} 엔트리 (S{min(slots)}~S{max(slots)})")

print("\n완료")
