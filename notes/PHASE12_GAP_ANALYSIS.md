# Phase 12: HW 매뉴얼 단독 정밀 검증 — 매뉴얼 정정 권고 + 분석 잔여 갭

> **2026-04-26** | fw4_0_1_2229 (CM4 + CM7 + FX) vs **HW 공식 매뉴얼 v4.0.1**
> **이전 산출물**: `PHASE11_GAP_FILL_ANALYSIS.md`(425줄), `MANUAL_VS_FIRMWARE_MATCH.md`(91.8% 갱신)
> **본 문서 목적**: HW 매뉴얼 단독 기준으로 (a) Phase 11 진척 정량 평가, (b) **매뉴얼 정정 권고** 항목 정리, (c) 잔여 8.2% 갭의 구체적 원인 진단, (d) Phase 12 실행 계획

---

## 0. Executive Summary

Phase 11 (커밋 `cadd861`)으로 일치도 **86.4% → 91.8%** (+5.4%p) 상승. Phase 12에서 추가 정적 분석으로 **91.8% → ~96%** 상향 목표.

### Phase 12 산출물

| 문서 | 크기 | 내용 |
|------|------|------|
| `MANUAL_CORRECTION_RECOMMENDATIONS.md` | 26.8KB | 매뉴얼 정정 7항 + 보강 12항 |
|| `PHASE12_FX_CORE_DSP.md` | 24.8KB | FX 12타입(CM4)/13타입(VST) DSP 매핑 완성 |
| `PHASE12_CC_FULL_MAPPING.md` | 19.3KB | 161 CC × 145 param 정밀 매핑 |
| `PHASE12_MOD_DEST_FULL.md` | 24.9KB | ~247 destination enum (51 user-reachable) |
| `PHASE12_SEQ_BUFFER_LAYOUT.md` | 15.7KB | 64-step + 4-lane + 6-track buffer layout |
| `PHASE12_RELIABILITY_UPGRADE.md` | 13.6KB | 4항목 ★★★★★ 격상 완료 |

### Phase 12 신규 발견 요약

| 항목 | Phase 11 | Phase 12 | 변화 |
|------|----------|----------|------|
| Poly Steal Mode | 6종 (★★★★★) | 6종 (★★★★★) | — |
| Vibrato (3rd LFO) | ★★★☆☆ | **★★★★★** | ↑2 |
| Para Env 분리 | ★★★☆☆ | **★★★★★** (분리없음 확인) | ↑2 |
| Multi Filter 모드 | ★★★☆☆ | **★★★★★** (14모드 전부) | ↑2 |
|| FX 코어 DSP | 타입만 | **12타입(CM4)/13타입(VST) × 7SP 매핑** | 완성 |
| CC 매핑 | 41 user CC | **161 CC 전체 매핑** | 완성 |
| Mod Dest | 13 user | **~247 (51 user-reachable)** | 완성 |
| Seq buffer | 미확정 | **24 field/step 구조** | 완성 |

---

## 1.1 Phase 12 감사 (Audit) — 오류 수정 이력

Phase 12 완료 후 전체 산출물에 대해 정합성 감사를 수행 (2026-04-26).

### 펌웨어 주소 검증 결과
- **~120개 주소/문자열 검증** — 92% 정확 일치
- **5건 불일치 발견 및 수정**:

| # | 문제 | 수정 내용 |
|---|------|----------|
| 1 | Arp index 2 "Arp Up 재사용" | → **"Arp UpDown" 독립 문자열** 확인 (0x081AEC4C) |
| 2 | Shaper 프리셋 20개 | → **25개** (Preset Shaper + 16 builtin + 8 user) |
| 3 | Multi Filter ptr 0x081B1850 | → scale names 혼합, 순수 14-포인터 테이블 아님 |
| 4 | Percussive 주소 오프셋 | +8바이트 |
| 5 | Custom Assign 시작 주소 | 0x081AEA94 → 0x081AEAA4 |

### 문서 내 불일치 수정
| 문제 | 수정 |
|------|------|
| FX DSP 섹션 "10개" | → "11개" |
| Mod Dest "35 options" | → "39 options" |
| FX Internal "~15" | → "~16" |

> **상세 검증 리포트**: `PHASE11_12_ADDRESS_VERIFICATION.md`

---

## 1.2 실행 계획 (원본)

> 원본 Phase 12 계획은 사용자가 제공한 PHASE12_GAP_ANALYSIS.md에 포함되어 있음.
> 아래는 실제 실행 결과와 대조.

### 1.1 Phase 12-1: 매뉴얼 정정 권고서 ✅ 완료
- 7개 정정 항목 (CORR-01 ~ CORR-07) — 전부 ★★★★★
- 12개 보강 항목 (ENH-01 ~ ENH-12)
- 펌웨어 주소 + hex dump 포함

### 1.2 Phase 12-2: FX 코어 DSP ✅ 완료
- CM4 12 FX 타입 → FX 코어 7 서브프로세서 매핑
- Chorus/Flanger/Phaser = SP6 공유, Vocoder = SP4/SP5 이중
- DSP 핵심 함수 11개 식별

### 1.3 Phase 12-3: CC 매핑 ✅ 완료
- 161 CC handler 전체 매핑 (41 user + 120 internal)
- NRPN 33 case + Mod Matrix NRPN 22 sub-param
- SysEx CRC 알고리즘 + Q15 fixed-point

### 1.4 Phase 12-4: Mod Matrix Dest ✅ 완료
- ~247 unique destination (51 user-reachable)
- 7×13 matrix 아키텍처 (91 max simultaneous)
- Meta-modulation 2-level depth

### 1.5 Phase 12-5: Seq Buffer ✅ 완료
- boost::serialization text format (binary buffer 아님)
- 24 field/step: StepState + Gate + 6×(Pitch,Length,Velo) + 4×Mod + ModState
- 64 step × 6 track + 4 mod lane + 3 CC lane + 2 LFO shaper

### 1.6 Phase 12-6: 신뢰도 격상 ✅ 완료
- Vibrato: ★★★★★ (6개 CM4 문자열 확보)
- Para Env: ★★★★★ (Voice Env + CycEnv, 별도 Para Env 없음)
- Multi Filter: ★★★★★ (14모드 전부: LP6/12/24/36, HP6/12/24/36, BP12/24/36, N12/24/36)
- Poly/Dual: ★★★★☆ (Poly2Mono toggle 확보, Poly/Dual 독립 문자열 없음)

---

## 2. 잔여 ~4% 갭 원인

| 항목 | 남은 갭 | 원인 | 해결 방법 |
|------|--------|------|----------|
| OSC 24→99 vtable | ★★☆☆☆ | 런타임 vtable swap | JTAG/SWD |
| Poly/Dual 문자열 | ★★★★☆ | 다른 enum과 포인터 공유 | CM4 추가 xref |
| Spice/Dice LUT 정량값 | ★★★★☆ | LUT는 식별, 값은 미추출 | 메모리 dump |
| 프리셋 로드 vtable | ★★☆☆☆ | 런타임 동적 | USB 캡처 |
| 아날로그 필터 회로 | — | 보드 분해 필요 | HW 분해 |

---

## 3. 후속 Phase 13+ 권고

- **Phase 13**: V 매뉴얼 통합 재검증 (Phase 11/12 발견사항 반영)
- **Phase 14**: HW 실기 + USB 캡처 동적 검증
- **Phase 15**: 안전한 펌웨어 패치 실험 (deprecated 슬롯 활용)

---

## V2 독립 검증 (2026-04-26)

Phase 12 감사와 완전히 다른 4가지 방법으로 재검증:

### V2-1: JSON vs MD 크로스체크
- phase8_midi_cc_extract.json: 161 CC 값 ✅ (문서와 일치)
- phase8_enum_tables.json: fx_types=11, voice_modes=4 (Phase 8 한계, Phase 11에서 보완됨)
- mf_enums.py: 13 FX 타입 ✅ (VST 기준, CM4=12종 차이는 정상)
- 가중치 합산: 96.21% → 96.2% (문서의 96.0%은 반올림 오류 → 수정)

### V2-2: 도구 실제 실행
- verify_phase11_12_addresses.py: 정상 실행 ✅
- mf_enums.py import: 정상 동작 ✅
- parse_mnfx.py: 정상 동작 ✅

### V2-3: CM4 전체 enum 재스캔
- FX 타입: **12종** 확인 (Chorus~Vocoder Ext). "Stereo Delay" CM4 없음, VST 전용.
- "Ensemble" 문자열: CM4 바이너리에 존재하지 않음.
- FX 테이블: inline null-terminated strings, 8-byte pointer 아님 (Phase 12 초기 오류).

### V2-4: 참조 무결성
- 빈 파일: plaits_source/__init__.py 등 61개 (정상 — Python 패키지 마커)
- 누락 참조: phase11_gap_fill_scan.py (repo에 없었음 → 복사 추가)
- Phase 10 계획 파일 8개: 아직 미생성 (정상 — Phase 10은 계획 문서)

### V2 수정사항
1. FX 타입 13→12 (CM4 기준), VST 13타입은 별도 표기
2. FX 주소 테이블: 8-byte pointer → inline strings로 정정
3. "Ensemble" 참조 제거 (바이너리 미존재)
4. 일치도 96.0% → 96.2% (반올림 수정)
5. phase11_gap_fill_scan.py repo에 추가

---

*Phase 12 정적 분석 완료. 예상 일치도 ~96.2%.*
