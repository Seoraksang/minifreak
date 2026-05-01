#!/usr/bin/env python3
"""
Phase 14-2: minifreak_vst_params.xml 파싱 → VST 파라미터 매핑 테이블 생성
"""

import xml.etree.ElementTree as ET
import json, re

XML_PATH = "reference/minifreak_v_extracted/commonappdata/Arturia/MiniFreak V/resources/minifreak_vst_params.xml"

tree = ET.parse(XML_PATH)
root = tree.getroot()

params = []
item_lists = {}

# item_list 수집 (독립 정의)
for il in root.findall('item_list'):
    name = il.get('name')
    items = []
    for item in il.findall('item'):
        entry = {'text': item.get('text')}
        if item.get('processorvalue') is not None:
            entry['processorvalue'] = int(item.get('processorvalue'))
        if item.get('from') is not None:
            entry['range'] = (int(item.get('from')), int(item.get('to')))
        items.append(entry)
    item_lists[name] = items

# param 노드 파싱
for param in root.findall('param'):
    name = param.get('name')
    if not name:
        continue
    
    info = {
        'name': name,
        'display_name': param.get('display_name', ''),
        'text_desc': param.get('text_desc', ''),
        'resetable': param.get('resetable') == '1',
        'realtimemidi': param.get('realtimemidi') == '1',
        'defaultvalnorm': param.get('defaultvalnorm'),
        'mapping_min': param.get('mapping-min'),
        'mapping_max': param.get('mapping-max'),
        'savedinpreset': param.get('savedinpreset', '1') == '1',
    }
    
    # mapping 범위
    if info['mapping_min']:
        info['mapping_min'] = float(info['mapping_min'])
    if info['mapping_max']:
        info['mapping_max'] = float(info['mapping_max'])
    
    # 기본값
    if info['defaultvalnorm']:
        info['defaultvalnorm'] = float(info['defaultvalnorm'])
    
    # 인라인 item_list
    inline_items = param.findall('item')
    if inline_items:
        items = []
        for item in inline_items:
            entry = {'text': item.get('text')}
            if item.get('processorvalue') is not None:
                entry['processorvalue'] = int(item.get('processorvalue'))
            if item.get('from') is not None:
                entry['range'] = (int(item.get('from')), int(item.get('to')))
            items.append(entry)
        info['items'] = items
    
    # 참조 item_list
    ref_lists = param.findall('item_list')
    if ref_lists:
        refs = []
        for rl in ref_lists:
            rl_name = rl.get('name')
            version = rl.get('version')
            if rl_name in item_lists:
                refs.append({
                    'name': rl_name,
                    'version': version,
                    'items': item_lists[rl_name]
                })
        info['item_list_refs'] = refs
    
    params.append(info)

# 카테고리 분류
def categorize(name):
    if name.startswith('Osc') and not name.startswith('OscType'):
        return 'oscillator'
    if name.startswith('LFO') or name.startswith('Lfo'):
        return 'lfo'
    if name.startswith('Vcf_') or name.startswith('Cutoff') or name.startswith('Resonance'):
        return 'filter'
    if name.startswith('Env_') or name.startswith('CycEnv_'):
        return 'envelope'
    if name.startswith('FX') or name in ('Chorus', 'Delay', 'Reverb', 'Phaser', 'Flanger', 'Distortion', 'Bitcrusher', 'Octaver'):
        return 'fx'
    if name.startswith('Mx_') or name.startswith('Mod_S'):
        return 'matrix'
    if name.startswith('Seq_') or name.startswith('Arp') or name.startswith('ArpSeq'):
        return 'sequencer'
    if name.startswith('AMOUNT_'):
        return 'fm_routing'
    if name.startswith('Macro'):
        return 'macro'
    if name.startswith('Vibrato') or name.startswith('MxDst'):
        return 'modulation'
    if name.startswith('Pitch') or name.startswith('After') or name.startswith('Velo'):
        return 'performance'
    if name.startswith('Gen_'):
        return 'voice'
    if name.startswith('Slot') or name.startswith('Autom'):
        return 'system'
    return 'other'

# 출력
categories = {}
for p in params:
    cat = categorize(p['name'])
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(p)

print("=" * 80)
print(f"MiniFreak VST 파라미터 정의 (minifreak_vst_params.xml)")
print(f"총 {len(params)}개 파라미터, {len(item_lists)}개 아이템 리스트")
print("=" * 80)

for cat, plist in sorted(categories.items()):
    print(f"\n### {cat} ({len(plist)}개)")
    for p in plist:
        extras = []
        if p.get('mapping_min') is not None:
            extras.append(f"range=[{p['mapping_min']},{p['mapping_max']}]")
        if p.get('defaultvalnorm') is not None:
            extras.append(f"default={p['defaultvalnorm']}")
        if p.get('items'):
            extras.append(f"items={len(p['items'])}")
        if p.get('item_list_refs'):
            extras.append(f"list_refs={len(p['item_list_refs'])}")
        if p.get('text_desc'):
            extras.append(f"desc=\"{p['text_desc'][:50]}\"")
        extra_str = ' '.join(extras)
        print(f"  [{len(plist):3d}] {p['name']:<30} → {p['display_name']:<20} {extra_str}")

# JSON 출력
output = {
    'total_params': len(params),
    'total_item_lists': len(item_lists),
    'params': params,
    'item_lists': {k: v for k, v in item_lists.items()},
}

out_path = 'reference/minifreak_vst_params_parsed.json'
with open(out_path, 'w') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"\nJSON 출력: {out_path}")

# 핵심 enum 값 추출
print("\n" + "=" * 80)
print("핵심 Enum/아이템 리스트 요약")
print("=" * 80)

key_lists = ['Osc1_Type_V2.9.0', 'Osc2_Type_V2.9.0', 'LFO1_Wave', 'LFO1_RateSync', 'Arp_Mode']
for kl in key_lists:
    if kl in item_lists:
        print(f"\n{kl}:")
        for item in item_lists[kl]:
            pv = item.get('processorvalue', '')
            print(f"  {pv:>3}: {item['text']}")
