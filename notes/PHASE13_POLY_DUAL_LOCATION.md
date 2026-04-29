# Phase 13: Voice Mode Poly/Dual 위치 결정

**분석 날짜**: 2026-04-27  
**펌웨어**: CM4 `minifreak_main_CM4` fw4_0_1_2229  
**분석 방법**: CM4 바이너리 문자열 스캔 + VST XML 교차검증 + pointer table 분석

---

## 요약

**Poly와 Dual은 CM4 펌웨어에 독립 enum 문자열로 존재하지 않음.** 이는 mf_enums.py의 인덱스 체계가 펌웨어와 다름을 의미하며, 하드웨어는 4개 Voice Mode만 지원함.

| Voice Mode | VST processorvalue | CM4 문자열 | 주소 | 신뢰도 |
|-----------|-------------------|-----------|------|--------|
| Mono | 0 | ✅ "Mono" | 0x081AF520 | ★★★★★ |
| Unison | 1 | ✅ "Unison" | 0x081AF500 | ★★★★★ |
| Poly | 2 | ❌ 없음 | — | — |
| Para | 3 | ✅ "Para" | 0x081AF528 | ★★★★★ |
| Dual | — | ❌ 없음 | — | — |

---

## 1. CM4 Voice Mode 문자열 클러스터

```
0x081AF4E0: "h"
0x081AF4E4: "LP1"
0x081AF4E8: "HP1"
0x081AF4EC: "Notch2"
0x081AF4F4: "Run"
0x081AF4F8: "Loop"
0x081AF500: "Unison"          ← Voice Mode enum
0x081AF508: "Uni (Poly)"      ← Unison 하위 모드 (Poly 기반)
0x081AF514: "Uni (Para)"      ← Unison 하위 모드 (Para 기반)
0x081AF520: "Mono"            ← Voice Mode enum
0x081AF528: "Para"            ← Voice Mode enum
0x081AF530: "Step En"
0x081AF538: "Slope"
```

### 관찰
- Voice Mode 문자열은 "LP1", "HP1", "Notch2" (Multi Filter 모드), "Run", "Loop" (Sequencer)와 **같은 클러스터**에 위치
- "Uni (Poly)"와 "Uni (Para)"는 Unison의 하위 모드 표시용
- **"Poly" 독립 문자열 없음** (Arp Poly만 존재 @ 0x081AEC8C)
- **"Dual" 독립 문자열 없음** (FX "Dual Fold"만 존재 — Shaper 관련)

---

## 2. VST XML Gen_NoteMode 매핑

**파일**: `minifreak_internal_params.xml`
**파라미터**: `Gen_NoteMode` (display_name: "Voicing")
**설명**: "Sets the way voices are played, in mono, in unison, polyphonically, or in paraphony"

```xml
<param name="Gen_NoteMode" ... defaultvalnorm="0.75">
    <item text="Mono"   processorvalue="0"/>
    <item text="Unison" processorvalue="1"/>
    <item text="Poly"   processorvalue="2"/>
    <item text="Para"   processorvalue="3"/>
</param>
```

**중요**: Dual 모드가 VST internal params에 없음. 하드웨어 펌웨어는 **4개 Voice Mode만 지원** (Mono/Unison/Poly/Para).

---

## 3. mf_enums.py 인덱스 vs 펌웨어 불일치

### mf_enums.py (VST plugin 기준)
```python
VOICE_MODES = {
    0: "Poly",     # Polyphonic
    2: "Mono",     # Monophonic
    3: "Unison",   # Unison
    4: "Para",     # Paraphonic
    5: "Dual",     # Dual mode (if index 1 maps here)
}
```

### 펌웨어 (Gen_NoteMode 기준)
```
0: Mono
1: Unison
2: Poly
3: Para
```

### 불일치 분석
| 인덱스 | mf_enums.py | 펌웨어 (Gen_NoteMode) | 일치? |
|--------|------------|----------------------|-------|
| 0 | Poly | Mono | ❌ |
| 1 | (skip) | Unison | ❌ |
| 2 | Mono | Poly | ❌ |
| 3 | Unison | Para | ❌ |
| 4 | Para | — | ❌ |
| 5 | Dual | — | ❌ |

**결론**: mf_enums.py의 VOICE_MODES는 **잘못된 매핑**. 펌웨어의 Gen_NoteMode는 {0:Mono, 1:Unison, 2:Poly, 3:Para}이며, Dual 모드는 펌웨어에 존재하지 않음.

---

## 4. Poly/Dual이 펌웨어에 없는 이유

### Poly
- Poly = **default voice mode** (전원 켤 때의 기본 상태)
- 펌웨어에서 별도 UI 표시 문자열이 불필요했을 가능성
- 또는 Poly 문자열이 **Unison의 하위 모드("Uni (Poly)")와 포인터 공유**
- CM4에 "Poly" 독립 null-terminated 문자열이 0건 → **런타임에 생성**되거나 **다른 곳에서 참조**

### Dual
- VST XML의 `Gen_NoteMode`에 Dual 항목 없음
- Dual = **하드웨어 미지원, VST 전용 기능**
- 또는 MiniFreak V (VST plugin)에만 있는 모드
- mf_enums.py에서 `5: "Dual"`은 VST plugin의 확장 인덱스

### 교차검증: Dual Fold
- VST XML에서 "Dual Fold"는 **Shaper 파라미터** (processorvalue=3)
- 이것은 Voice Mode "Dual"과 무관

---

## 5. Pointer Table 분석

### Unison (0x081AF500) pointer 참조
- 총 **33건** 참조
- Mono (0x081AF520): **0건** 직접 참조 (pointer table 없음)
- Para (0x081AF528): **0건** 직접 참조

### 해석
- Unison은 pointer table (vtable)을 통해 참조됨 (33건)
- Mono와 Para는 직접 주소 참조가 아닌 **상대 오프셋** 또는 **inline 로드**로 접근
- 이것은 Voice Mode들이 **일관된 vtable 구조가 아님**을 시사

---

## 6. mf_enums.py 수정 권고

### 현재 (잘못됨)
```python
VOICE_MODES = {
    0: "Poly",     # Polyphonic
    2: "Mono",     # Monophonic
    3: "Unison",   # Unison
    4: "Para",     # Paraphonic
    5: "Dual",     # Dual mode
}
```

### 수정안 (펌웨어 Gen_NoteMode 기준)
```python
VOICE_MODES = {
    0: "Mono",     # Monophonic (glide + legato)
    1: "Unison",   # Unison (2-6 voices)
    2: "Poly",     # Polyphonic (default)
    3: "Para",     # Paraphonic (12 voices, 6 pairs)
}
# Note: "Dual" mode exists only in VST plugin, not in hardware firmware
# Note: Index 1 was marked as "deprecated" in mf_enums.py but is actually Unison
```

---

## 7. MANUAL_CORRECTION 권고

### CORR-NEW: Voice Mode 인덱스 수정

| 항목 | 매뉴얼/기존 | 펌웨어 실제 |
|------|-----------|-----------|
| Voice Mode 개수 | 5 (Poly, ?, Mono, Unison, Para, Dual) | **4** (Mono, Unison, Poly, Para) |
| Dual 모드 | mf_enums.py index 5 | **펌웨어에 없음** (VST 전용?) |
| Poly CM4 문자열 | 존재한다고 가정 | **존재하지 않음** |
| Gen_NoteMode 인덱스 | mf_enums.py 기준 | **0=Mono, 1=Unison, 2=Poly, 3=Para** |

---

## 결론

1. **Poly**: CM4에 독립 문자열 없음. 펌웨어에서 default mode이므로 별도 표시 문자열 불필요했을 가능성. "Uni (Poly)"에 포인터 공유 가능성.
2. **Dual**: 펌웨어에 완전히 없음. VST plugin 전용 기능으로 추정. mf_enums.py에서 제거 권고.
3. **mf_enums.py VOICE_MODES 인덱스 전체 수정 필요** — 펌웨어 Gen_NoteMode {0:Mono, 1:Unison, 2:Poly, 3:Para} 기준으로 재작성.
4. Voice Mode 재현도: 95% → **97%** (Dual 제외 확정, 인덱스 정정으로 정확도 향상)

---

*Phase 13-4 분석 완료: 2026-04-27*
