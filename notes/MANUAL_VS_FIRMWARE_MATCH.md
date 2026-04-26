# MiniFreak 매뉴얼 vs 펌웨어 일치도 분석 (Phase 12 업데이트)

**매뉴얼**: MiniFreak User Manual v4.0.0 (2025-07-04)
**펌웨어**: CM4 `minifreak_main_CM4` + CM7 `minifreak_main_CM7` fw4_0_1_2229 (2025-06-18)
**FX 코어**: `minifreak_fx` fw1_0_0_2229 (2025-06-18)
**분석 날짜**: 2026-04-26 (Phase 12 완료 후 업데이트)
**분석 방법**: 매뉴얼 각 기능 항목 → CM4/CM7 바이너리 + VST XML 교차검증

---

## 종합 일치도: **~96.0%** (Phase 10: ~86% → Phase 11: ~92% → Phase 12: ~96.0%)

| 카테고리 | 가중치 | Phase 10 | Phase 11 | Phase 12 | 기여값 | 상승 요인 |
|----------|--------|----------|----------|----------|--------|-----------|
| 오실레이터 엔진 | 20% | 95% | 95% | 95% | 19.00 | — |
| 필터 시스템 | 15% | 85% | 85% | **96%** | 14.40 | Multi Filter 14모드 전부 ★★★★★ 확보 |
|| 디지털 이펙트 (FX) | 10% | 80% | 92% | **95%** | 9.50 | 12타입(CM4)/13타입(VST) × 7SP 매핑 + DSP 11함수 식별 |
| LFO | 8% | 75% | 92% | **98%** | 7.84 | Vibrato ★★★★★ (6개 CM4 문자열) |
| 엔벨로프 | 8% | 90% | 92% | **97%** | 7.76 | Para Env 분리없음 ★★★★★ 확보 |
| 모듈레이션 매트릭스 | 10% | 95% | 96% | **99%** | 9.90 | ~247 dest (51 user) 완전 매핑 |
| 보이스 모드 | 7% | 85% | 92% | **95%** | 6.65 | Poly2Mono toggle 확보 |
| 아르페지에이터 | 5% | 65% | 95% | **95%** | 4.75 | — |
| 스텝 시퀀서 | 5% | 80% | 90% | **97%** | 4.85 | 24 field/step buffer layout 완성 |
| 오디오 스펙/튜닝 | 5% | 100% | 100% | 100% | 5.00 | — |
| Spice/Dice | 3% | 85% | 85% | 88% | 2.64 | LUT 구조 확인, 정량값 미완 |
| CC 라우팅 | 2% | 80% | 82% | **96%** | 1.92 | 161 CC 전체 매핑 + NRPN |
| 프리셋 시스템 | 2% | 80% | 82% | **90%** | 1.80 | deprecated 4종 + boost::serialization |
|| **종합** | **100%** | **86.4%** | **91.8%** | **96.0%** | | |

---

## 카테고리별 상세 분석

### 1. 오실레이터 엔진 — 95%
**매뉴얼**: Osc 1 = 16타입, Osc 2 = 21타입, 총 ~31엔진

**펌웨어 증거**:
- ✅ CM4 enum @ `0x081AF388`~`0x081AF4C8`: 30개 엔진명 문자열 전부 확인
- ✅ CM7 99개 vtable (16/19/20 entries) — 다형성 OSC 아키텍처
- ✅ CM7 `FUN_0803e6f8` 16-case switch — OSC 타입 디스패치
- ✅ CM7 7개 이상 렌더 함수 (440Hz×12 참조)
- ✅ VST XML `Osc1_Type_V2.9.0` 24종, `Osc2_Type_V2.9.0` 21종 교차검증
- ✅ NEON SIMD 가속
- ⚠️ 99 vtable → 30 엔진 1:1 매핑은 런타임 vtable swap 필요 (JTAG/SWD)

### 2. 필터 시스템 — 85% → **96%** ⬆️
**매뉴얼**: 아날로그 SEM LP/HP/BP + 디지털(Multi/Surgeon/Comb/Phaser/Destroy)

**펌웨어 증거**:
- ✅ CM4 VCF 모드 문자열: `LP`, `BP`, `HP`, `Notch`, `LP1`, `HP1`, `Notch2` @ `0x081AF4D0`
- ✅ **CM4 Multi Filter 14모드 전부 ★★★★★ 확보** @ `0x081B0D90`~`0x081B0DE8`:
  LP6, LP12, LP24, LP36, HP6, HP12, HP24, HP36, BP12, BP24, BP36, N12, N24, N36
- ✅ 포인터 참조: `0x081B1850` 영역에 일부 필터 모드 포인터 존재 (scale names와 혼합)
- ✅ CM7 20개 IIR smoothing 함수
- ✅ CM7 Biquad 계수 0.707(1/√2) ×8
- ⚠️ 아날로그 필터는 하드웨어 회로 (CM4/DAC 제어)

### 3. 디지털 이펙트 (FX) — 92% → **97%** ⬆️
**매뉴얼**: 13 FX 타입, 3슬롯, Insert/Send

**펌웨어 증거 (Phase 12 신규)**:
- ✅ CM4 FX 타입 문자열 테이블 @ `0x081AF308`~`0x081AF37C`: **12/12 CM4 타입 전부 확인 (VST 13타입, Stereo Delay는 VST 전용)**
- ✅ **CM4 12타입(CM4)/13타입(VST) → FX 코어 7서브프로세서 매핑 완성**:
  - SP6 공유: Chorus, Chorus Stereo, Flanger, Flanger Stereo, Phaser, Phaser Stereo
  - SP4(mode=2): Vocoder Self / SP5(mode=1): Vocoder Ext
  - SP0: Reverb, Reverb Shimmer
  - SP1: Delay, Stereo Delay
  - SP2: Bitcrusher, Distortion, 3 Bands EQ, Peak EQ, Multi Comp
- ✅ **DSP 핵심 함수 11개 식별** (Phase 12-2)
- ✅ FX 서브타입 63종 (Phase 8 VST XML)
- ✅ FX 체인 3슬롯 × 7SP, 슬롯 간격 584B
- ⚠️ Vocoder Self vs Ext In은 구조적 차이 (필터/딜레이/LFO)

### 4. LFO — 92% → **98%** ⬆️
**매뉴얼**: 9파형 + LFO3 Vibrato, 8 Retrig 모드

**펌웨어 증거 (Phase 12 신규)**:
- ✅ CM4 LFO 파형 enum @ `0x081B0FB0`: 9/9 (7 직접 + VST XML 2)
- ✅ CM4 LFO Retrig 모드 @ `0x081B0E7C`: 8/8
- ✅ **Vibrato ★★★★★ 확보** — 6개 CM4 문자열: `Vibrato On`, `Vibrato Off`, `Vibrato` (panel), `Vibrato Depth`, `Vib Rate`, `Vib AM`
- ✅ Vibrato는 LFO1/LFO2와 완전히 독립된 최상위 모듈 (LFO3 명칭 없음)
- ✅ Shaper 프리셋 25종 @ `0x081AF128` (1 기본 + 16 빌트인 + 8 사용자)

### 5. 엔벨로프 — 92% → **97%** ⬆️
**매뉴얼**: ADSR + Cycling Envelope (Rise/Fall/Hold, 3 Stage Order)

**펌웨어 증거 (Phase 12 신규)**:
- ✅ **Para Master Env ★★★★★ 확보** — 별도 Para Env 존재하지 않음
  - Para 모드 = Voice Envelope (ADSR) + Cycling Envelope 동시 사용
  - Voice Env: CM4 eEditParams Attack/Decay/Release @ `0x081AF7E8`~`0x081AF7F8`
  - CycEnv: Mode/Hold/Rise/Fall/Stage Order @ `0x081AF840`~`0x081AF880`
- ✅ CycEnv Stage Order: RHF, RFH, HRF @ `0x081AF880`
- ✅ CM7 VABS.F32 ×68, 64-entry time scale LUT

### 6. 모듈레이션 매트릭스 — 96% → **99%** ⬆️
**매뉴얼**: 7소스 × 13목적지

**펌웨어 증거 (Phase 12 신규)**:
- ✅ CM4 Mod Source 9종 @ `0x081B1BCC`
- ✅ **~247 unique destination** (Phase 12-4):
  - 51 user-reachable (39 assignable pool + 8 Custom Assign + 4 always-on)
  - ~196 internal (Osc ~30, VCF ~6, FX ~15, Env/LFO ~25, Voice ~12, Seq ~18, Kbd/Scale ~28 등)
- ✅ 7×13 matrix (91 max simultaneous routings)
- ✅ Meta-modulation 2-level depth
- ✅ Mod Matrix NRPN 0xD8 (22 sub-param destinations)

### 7. 보이스 모드 — 92% → **95%** ⬆️
**매뉴얼**: Mono/Unison/Poly/Para/Dual

**펌웨어 증거 (Phase 12 신규)**:
- ✅ CM4 Voice Mode: Mono @ `0x081AF520`, Unison @ `0x081AF500`, Para @ `0x081AF528`
- ✅ **`Poly2Mono` UI toggle** @ `0x081AE128` 신규 발견
- ✅ Unison 하위모드 3종: Unison, Uni (Poly), Uni (Para)
- ✅ Poly Steal Mode 6종 @ `0x081B0F70`
- ⚠️ Poly/Dual 독립 enum 문자열 없음 (★★★★☆)

### 8. 아르페지에이터 — 95%
**매뉴얼**: 8모드 (Up/Down/UpDown/Random/Walk/Pattern/Order/Poly)

**펌웨어 증거**:
- ✅ CM4 Arp Mode enum @ `0x081AEC3C`: **8/8 전부 확인**
- ✅ Arp 수식어 4종: Repeat, Ratchet, Rand Oct, Mutate
- ✅ CM7 5-case switch = 그룹 분기 (정상)

### 9. 스텝 시퀀서 — 90% → **97%** ⬆️
**매뉴얼**: 64스텝, 4모듈레이션 레인

**펌웨어 증거 (Phase 12 신규)**:
- ✅ **64-step buffer layout 완전 해명** (Phase 12-5):
  - boost::serialization text format (binary buffer 아님)
  - 24 field/step: StepState + Gate + 6×(Pitch, Length, Velo) + 4×Mod + ModState
  - 6 note tracks (I0~I5) + 4 mod lanes (I0~I3) + 3 CC automation lanes + 2 LFO Shaper (16 step each)
  - Pitch /128, Velocity /127, Mod bipolar centered at 0.5
- ✅ CM4 Smooth Mod 1~4 @ `0x081B1B8C`
- ✅ CM7 64×17 + 4×16 상수 확인

### 10. 오디오 스펙/튜닝 — 100%
- ✅ CM7 48000.0, 440.0×12, 1/12=0.0833

### 11. Spice/Dice — 85% → 88%
- ✅ CM7 지수적 확률 LUT @ `0x08067FDC`
- ⚠️ Walk 25/50/25, Mutate 75/5/5/5/5/3/2 정량 LUT 값 미추출

### 12. CC 라우팅 — 82% → **96%** ⬆️⬆️
**펌웨어 증거 (Phase 12 신규)**:
- ✅ **161 CC handler 전체 매핑** (Phase 12-3):
  - 41 user-visible CCs + 120 internal CCs
  - NRPN 33 case + Mod Matrix NRPN 22 sub-param
  - SysEx CRC + Q15 fixed-point scaling
  - 5 DAT_ proxy vtable dispatch
  - Learn mode filtering (CC 204 excluded)
  - 16-channel param router (NRPN 0x9E~0xAD)

### 13. 프리셋 시스템 — 82% → **90%** ⬆️
- ✅ boost::serialization text format (Phase 12-5에서 구조 확인)
- ✅ 2,368 total params (2,175 seq + 193 synth)
- ✅ deprecated 파라미터 4종
- ⚠️ 프리셋 로드 시 vtable swap = 런타임 (JTAG 필요)

---

## 📌 Phase 12 주요 발견

### 매뉴얼 정정 권고 (7건) — 상세: `MANUAL_CORRECTION_RECOMMENDATIONS.md`
| ID | 내용 | 신뢰도 |
|----|------|--------|
| CORR-01 | Poly Steal Mode: 매뉴얼 4종 → 펌웨어 6종 | ★★★★★ |
| CORR-02 | Mod Matrix 소스: 매뉴얼 7 → 펌웨어 9 | ★★★★★ |
| CORR-03 | Arp UpDown 모드 — 독립 문자열 (이전 분석 "재사용" 오류 수정) | ★★★★★ |
| CORR-04 | Unison 하위모드 3종 | ★★★★★ |
| CORR-05 | LFO 파형명 약어 | ★★★★★ |
| CORR-06 | Tempo Subdivision 17종 (매뉴얼 11) | ★★★★☆ |
| CORR-07 | LFO 9파형 매뉴얼 내부 모순 | ★★★★★ |

### 매뉴얼 보강 권고 (12건) — 상세: `MANUAL_CORRECTION_RECOMMENDATIONS.md`
- ENH-01~12: Mod Dest 247개, Shaper 25종, deprecated 4종, Vibrato 독립 모듈, CC 161개, Multi Filter 14모드 등

### 신뢰도 격상 완료 (Phase 12-6)
| 항목 | Phase 11 | Phase 12 |
|------|----------|----------|
| Vibrato (3rd LFO) | ★★★☆☆ | **★★★★★** |
| Para Env 분리 | ★★★☆☆ | **★★★★★** (분리없음) |
| Multi Filter 모드 | ★★★☆☆ | **★★★★★** (14모드) |
| Poly/Dual | ★★★☆☆ | **★★★★☆** (Poly2Mono) |

---

## Phase 12 산출물

| 문서 | 크기 | 내용 |
|------|------|------|
| `PHASE12_GAP_ANALYSIS.md` | 4.4KB | Phase 12 실행 계획 + 결과 요약 |
| `MANUAL_CORRECTION_RECOMMENDATIONS.md` | 26.8KB | 매뉴얼 정정 7항 + 보강 12항 |
|| `PHASE12_FX_CORE_DSP.md` | 24.8KB | FX 12타입(CM4)/13타입(VST) × 7SP + DSP 11함수 |
| `PHASE12_CC_FULL_MAPPING.md` | 19.3KB | 161 CC 전체 매핑 |
| `PHASE12_MOD_DEST_FULL.md` | 24.9KB | ~247 destination enum |
| `PHASE12_SEQ_BUFFER_LAYOUT.md` | 15.7KB | 64-step 24 field/step layout |
| `PHASE12_RELIABILITY_UPGRADE.md` | 13.6KB | 4항목 ★★★★★ 격상 |

---

## 분석 한계 (잔여 ~4%)

1. **OSC 24→99 vtable 1:1 매핑** (★★☆☆☆) — 런타임 vtable swap, JTAG/SWD 필요
2. **Poly/Dual 독립 문자열** (★★★★☆) — 다른 enum과 포인터 공유
3. **Spice/Dice 확률 정량값** — LUT 구조 확인, Walk/Mutate 비율 미추출
4. **프리셋 로드 vtable swap** (★★☆☆☆) — 런타임 동적
5. **아날로그 필터 회로** — 보드 분해 필요

---

*Phase 10 초기 분석: 2026-04-26*
*Phase 11 갭 보완: 2026-04-26*
*Phase 12 정적 분석 완료: 2026-04-26*
*상세 내역: `PHASE11_GAP_FILL_ANALYSIS.md`, `PHASE12_GAP_ANALYSIS.md`*
