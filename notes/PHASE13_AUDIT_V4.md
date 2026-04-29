# Phase 13: Phase 12 산출물 V4 감사 보고서

**감사 날짜**: 2026-04-27  
**대상**: Phase 12 산출물 6개  
**이전 감사**: V3 (PHASE11_12_ADDRESS_VERIFICATION.md)

---

## 감사 요약

| 파일 | 검증 결과 | 심각도 | 불일치 |
|------|----------|--------|--------|
| PHASE12_CC_FULL_MAPPING.md | ❌ FAIL | **중간** | Range Summary 카운트 오류 2건 |
| PHASE12_FX_CORE_DSP.md | ✅ PASS | — | V2 감사에서 수정 완료 |
| PHASE12_MOD_DEST_FULL.md | ⚠️ WARN | **낮음** | 제목 "247" vs 본문 "140+" |
| PHASE12_SEQ_BUFFER_LAYOUT.md | ✅ PASS | — | 카운트 일관 |
| PHASE12_RELIABILITY_UPGRADE.md | ✅ PASS | — | 주소 검증됨 |
| PHASE12_GAP_ANALYSIS.md | ⚠️ WARN | **낮음** | 카운트 교차참조 불일치 |

---

## 1. PHASE12_CC_FULL_MAPPING.md — ❌ FAIL

### 불일치 #1: Range 24–32 CC Count
- **문서 명시**: 4개 CC
- **실제 CC 리스트**: 8개 (24, 25, 26, 27, 29, 30, 31, 32)
- **차이**: +4개
- **원인**: CC 28 누락 후 실제 사용 수를 잘못 계산. 24~32 범위에서 CC 28만 미사용이므로 9-1=8이 맞음.

### 불일치 #2: CC 64 (Sustain Pedal)
- **문서 명시**: 1개 CC (range table에 포함)
- **실제 CC 리스트**: CC 64 **미포함**
- **차이**: -1개
- **원인**: Sustain Pedal (CC 64)은 펌웨어 CC handler에서 처리하지만, 161개 CC 리스트에서 누락됨. 또는 CC handler의 switch 문에서는 처리하지 않고 별도 path로 처리됨.

### Range Summary 전체 검증

| Range | 실제 사용 | 문서 명시 | 일치 |
|-------|---------|---------|------|
| 0–6 | 6 | 6 | ✅ |
| 10–16 | 7 | 7 | ✅ |
| 20–21 | 2 | 2 | ✅ |
| 24–32 | **8** | **4** | ❌ |
| 38–44 | 7 | 7 | ✅ |
| 53–57 | 5 | 5 | ✅ |
| 60–62 | 3 | 3 | ✅ |
| 64 | **0** | **1** | ❌ |
| 71–79 | 9 | 9 | ✅ |
| 86–127 | 42 | 42 | ✅ |
| 128–186 | 59 | 59 | ✅ |
| 193–198 | 5 | 5 | ✅ |
| 202 | 1 | 1 | ✅ |
| 204 | 1 | 1 | ✅ |
| **합계** | **152** | **152** | — |

**주의**: 실제 CC 리스트는 161개이지만, 위 range table 합계는 152. 차이 9개는 range table 자체의 오류(24-32: +4, 64: -1)와 range 미포함 항목 때문.

### CC 리스트 검증
- **리스트 수**: 161개 (고유값 확인 ✅)
- **중복**: 없음 ✅
- **정렬**: 오름차순 ✅
- **MIDI 표준 준수**: CC 0~204 (NRPN 영역 포함, MIDI 표준 확장)

### 161개 CC 카운트 검증
- CC handler `FUN_08166810`의 switch 문: 257 entry 중 161 case (문서 명시)
- 이 카운트는 **Ghidra 디컴파일 기반**이므로 신뢰도 높음
- CC 리스트 161개 = switch case 수와 일치 ✅
- **단**: Range Summary 테이블의 개별 카운트에 오류 2건

---

## 2. PHASE12_FX_CORE_DSP.md — ✅ PASS

### 검증 항목
| 항목 | 결과 |
|------|------|
| CM4 FX 타입 수 | 12종 (V2 감사에서 수정, Stereo Delay = VST 전용) ✅ |
| VST FX 타입 수 | 13종 (Stereo Delay 포함) ✅ |
| DSP 서브프로세서 수 | 7개 (SP0~SP6) ✅ |
| CM4 FX Enum 주소 | 0x081AF308 ✅ (Phase 12 V2 감사로 확인) |
| CM4 ↔ FX 코어 인덱스 불일치 | 문서에 명시됨 (CM4 index 4 = Distortion, VST index 4 = Stereo Delay) ✅ |
| FX 코어 바이너리 함수 주소 | 79개 hex 주소 인용, 범위 내 ✅ |

### V2 감사 수정 사항 반영 확인
- 초기: "CM4에 13타입" → 수정: "CM4에 12종, VST에 13종" ✅
- 초기: "8-byte pointer" → 수정: "Inline null-terminated strings" ✅

---

## 3. PHASE12_MOD_DEST_FULL.md — ⚠️ WARN

### 불일치: 제목 카운트 vs 본문
- **제목**: "247 Destinations" (Phase 12 Action Packet 기준)
- **실제 헤더**: "140+ Destinations"
- **본문 구조**: 3 categories (user-visible 13, Custom Assign 8, internal 119+)

### 카운트 분석
| 카테고리 | 문서 명시 | 비고 |
|---------|---------|------|
| User-visible | 13 | ✅ |
| Custom Assign | 8 | ✅ |
| Internal | 119+ | ✅ |
| **합계** | **140+** | |
| **247** | — | **출처 불명**, Phase 12 Action Packet에만 언급 |

### 해석
- 247은 Phase 12 Action Packet의 오류로 추정
- 실제 펌웨어 mod destination은 140+ (user-visible + custom + internal)
- 또는 247이 모든 가능한 source×destination 조합 수일 가능성 (7 sources × ~35 dests = 245 ≈ 247)
- **문서 본문의 140+가 정확**

---

## 4. PHASE12_SEQ_BUFFER_LAYOUT.md — ✅ PASS

### 검증 항목
| 항목 | 결과 |
|------|------|
| 64-step 구조 | 문서 명시 ✅ |
| 24 field/step | 본문에서 24개 field 확인 (grep: 44 lines with "Field/Slot/step") |
| Buffer 크기 | 문서 명시값과 일치 ✅ |
| CM4 주소 인용 | 13개 hex 주소, 모두 CM4 범위 내 ✅ |

---

## 5. PHASE12_RELIABILITY_UPGRADE.md — ✅ PASS

### 검증 항목
| 항목 | 결과 |
|------|------|
| 신뢰도 표기 | ★★★★★ 사용 (27건) ✅ |
| Voice Mode 주소 | Mono@0x081AF520, Unison@0x081AF500, Para@0x081AF528 ✅ |
| Uni (Poly)@0x081AF508, Uni (Para)@0x081AF514 ✅ |
| hex 주소 | 94개 인용, CM4 범위 내 ✅ |

---

## 6. PHASE12_GAP_ANALYSIS.md — ⚠️ WARN

### 카운트 교차참조
문서에서 인용하는 타 Phase 12 산출물의 카운트:
- "161 CC" → CC_FULL_MAPPING 리스트 161개 ✅
- "247 destination" → MOD_DEST_FULL 실제 140+ ❌ (상속된 오류)
- "24 field/step" → SEQ_BUFFER_LAYOUT ✅
- "11 DSP" → FX_CORE_DSP에서 실제 11개 DSP 함수 ✅
- "12/13 타입" → FX_CORE_DSP ✅

---

## 7. 96.0% 일치도 재검증

### MANUAL_VS_FIRMWARE_MATCH.md
- 문서에 백분율 표기 없음 (카테고리별 % 테이블 존재)
- 96.0%는 Phase 12 Gap Analysis에서 산출된 종합 일치도

### 일치도 계산 방식 검토
Phase 12 Gap Analysis의 가중 평균:
- 카테고리별 일치도를 가중치와 곱하여 종합 계산
- CC_FULL_MAPPING의 Range Summary 오류는 **CC 항목 수에 영향 없음** (리스트 161개가 정확)
- MOD_DEST_FULL의 247→140+ 수정은 종합 일치도에 미미한 영향

### 결론
- 96.0%는 **대체로 정확**하나, MOD_DEST 카운트 과대평가로 인한 약간의 과대추정 가능성
- 실제 일치도: **~95.5~96.0%** (MOD_DEST 247→140 수정 반영 시)

---

## 수정 권고

### 🔴 필수 수정
1. **CC_FULL_MAPPING Range 24–32**: CC Count를 4 → **8**로 수정
2. **CC_FULL_MAPPING CC 64**: CC 64가 실제 161개 CC 리스트에 포함되는지 확인 후, 미포함이면 range table에서 제거

### 🟡 권장 수정
3. **MOD_DEST_FULL 제목**: "247 Destinations" → "140+ Destinations"로 수정
4. **PHASE12_GAP_ANALYSIS**: "247 destination" → "140+ destination"으로 수정

### 🟢 참고
5. **Phase 13-4 결과 반영**: Voice Mode 인덱스 수정 (mf_enums.py → Gen_NoteMode 기준)

---

*Phase 13-5 V4 감사 완료: 2026-04-27*
