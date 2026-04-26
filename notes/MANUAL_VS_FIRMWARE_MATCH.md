# MiniFreak 매뉴얼 vs 펌웨어 일치도 분석 (Phase 11 업데이트)

**매뉴얼**: MiniFreak User Manual v4.0.0 (2025-07-04)
**펌웨어**: CM4 `minifreak_main_CM4` + CM7 `minifreak_main_CM7` fw4_0_1_2229 (2025-06-18)
**FX 코어**: `minifreak_fx` fw1_0_0_2229 (2025-06-18)
**분석 날짜**: 2026-04-26 (Phase 11 갭 보완 후 업데이트)
**분석 방법**: 매뉴얼 각 기능 항목 → CM4/CM7 바이너리 + VST XML 교차검증

---

## 종합 일치도: **~92%** (Phase 10: ~86% → Phase 11: ~92%)

| 카테고리 | 가중치 | Phase 10 | Phase 11 | 기여값 | 상승 요인 |
|----------|--------|----------|----------|--------|-----------|
| 오실레이터 엔진 | 20% | 95% | 95% | 19.00 | — |
| 필터 시스템 | 15% | 85% | 85% | 12.75 | — |
| 디지털 이펙트 (FX) | 10% | 80% | **92%** | 9.20 | CM4에서 13타입 문자열 전부 확인 |
| LFO | 8% | 75% | **92%** | 7.36 | CM4에서 7/9 파형 + VST XML으로 9/9 확인 |
| 엔벨로프 | 8% | 90% | **92%** | 7.36 | CycEnv Stage Order CM4에서 확인 |
| 모듈레이션 매트릭스 | 10% | 95% | 96% | 9.60 | Mod Source 9종 CM4에서 직접 확인 |
| 보이스 모드 | 7% | 85% | **92%** | 6.44 | 5모드 + Unison 하위모드 3종 확인 |
| 아르페지에이터 | 5% | 65% | **95%** | 4.75 | CM4에서 8모드 enum 전부 확인 |
| 스텝 시퀀서 | 5% | 80% | **90%** | 4.50 | Smooth Mod 1~4 (4 lane) + CM7 64-step 상수 |
| 오디오 스펙/튜닝 | 5% | 100% | 100% | 5.00 | — |
| Spice/Dice | 3% | 85% | 85% | 2.55 | — |
| CC 라우팅 | 2% | 80% | 82% | 1.64 | eSeqParams/eSeqStepParams RTTI 추가 |
| 프리셋 시스템 | 2% | 80% | 82% | 1.64 | deprecated 파라미터 4종 식별 |
| **종합** | **100%** | **86.4%** | **91.8%** | | |

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

### 2. 필터 시스템 — 85%
**매뉴얼**: 아날로그 SEM LP/HP/BP + 디지털(Multi/Surgeon/Comb/Phaser/Destroy)

**펌웨어 증거**:
- ✅ CM7 20개 IIR smoothing 함수
- ✅ CM7 Biquad 계수 0.707(1/√2) ×8
- ✅ CM4 VCF 모드 문자열: `LP`, `BP`, `HP`, `Notch`, `LP1`, `HP1`, `Notch2` @ `0x081AF4D0`
- ✅ CM4 Multi Filter 14모드: `LP6`~`N36` @ `0x081B0D90`
- ⚠️ 아날로그 필터는 하드웨어 회로 (CM4/DAC 제어)

### 3. 디지털 이펙트 (FX) — 80% → **92%** ⬆️
**매뉴얼**: 13 FX 타입, 3슬롯, Insert/Send

**펌웨어 증거 (Phase 11 신규)**:
- ✅ CM4 FX 타입 문자열 테이블 @ `0x081AF308`~`0x081AF37C`: **13/13 타입 전부 확인**
  - Chorus, Phaser, Flanger, Reverb, Distortion, Bit Crusher, 3 Bands EQ, Peak EQ, Multi Comp, SuperUnison, Vocoder Self, Vocoder Ext + Stereo Delay (별도 주소)
- ✅ FX 코어 바이너리 = 순수 DSP (UI 문자열 없음 확인)
- ✅ CM7 `FUN_08009358` 7-case FX 체인 상태기
- ✅ FX 서브타입 63종 (Phase 8 VST XML 확인)
- ✅ Phase 7-3: FX 코어 7개 서브프로세서 매핑 완료
- ⚠️ FX 코어 개별 타입 내부 DSP는 Ghidra 분석 필요

### 4. LFO — 75% → **92%** ⬆️
**매뉴얼**: 9파형 + LFO3 Vibrato, 8 Retrig 모드

**펌웨어 증거 (Phase 11 신규)**:
- ✅ CM4 LFO 파형 enum @ `0x081B0FB0`: Sin, Tri, Sqr, SlewSNH, ExpSaw, ExpRamp, Shaper (7/9 직접 확인)
- ✅ VST XML 교차검증으로 Saw, SnH 포함 9/9 확정
- ✅ CM4 LFO Retrig 모드 @ `0x081B0E7C`~`0x081B0E88`: Free, Poly Kbd, Mono Kbd, Legato Kbd, One, LFO, CycEnv, Seq Start (8/8 확인)
- ✅ CM4 파라미터: LFO1/2 Wave, Sync En, Sync Filter, Retrig @ `0x081AF88C`~`0x081AF8F8`
- ✅ CM7 PI ×16, 2PI ×6 (위상 래핑), 정수 9 ×7회 (파형 수)
- ✅ Shaper 프리셋 20종 @ `0x081AF128`~`0x081AF288`

### 5. 엔벨로프 — 90% → **92%** ⬆️
**매뉴얼**: ADSR + Cycling Envelope (Rise/Fall/Hold, 3 Stage Order)

**펌웨어 증거 (Phase 11 신규)**:
- ✅ CM4 CycEnv Stage Order: RHF, RFH, HRF 각 1회 확인
- ✅ CM4 CycEnv 파라미터: Mode, Hold, Rise/Fall Curve, Stage Order, Tempo Sync, Retrig Src @ `0x081AF840`~`0x081AF880`
- ✅ CM7 VABS.F32 ×68 (attack/release 램프)
- ✅ CM7 64-entry time scale LUT

### 6. 모듈레이션 매트릭스 — 95% → 96% ⬆️
**매뉴얼**: 7소스 × 13목적지

**펌웨어 증거 (Phase 11 신규)**:
- ✅ CM4 Mod Source enum @ `0x081B1BCC`: Keyboard, LFO, Cycling Env, Env/Voice, Voice, Envelope, FX, Sample Select, Wavetable Select (9종 직접 확인)
- ✅ CM4 Mod Dest Custom Assign: Vib Rate, Vib AM, VCA, LFO1/2 AM, CycEnv AM, Uni Spread @ `0x081AEA94`
- ✅ CM7 Q15 → inline 적용
- ✅ CM7 실제 목적지 140개 (매뉴얼보다 더 많음)

### 7. 보이스 모드 — 85% → **92%** ⬆️
**매뉴얼**: Mono/Unison/Poly/Para/Dual

**펌웨어 증거 (Phase 11 신규)**:
- ✅ CM4 Voice Mode: Mono @ `0x081AF520`, Unison @ `0x081AF500`, Para @ `0x081AF528` (3/5 직접)
- ✅ CM4 Unison 하위모드 3종: Unison, Uni (Poly), Uni (Para) @ `0x081AF500`~`0x081AF514`
- ✅ CM4 Poly Steal Mode 6종 @ `0x081B0F70`: None, Cycle, Reassign, Velocity, Aftertouch, Velo + AT
- ✅ CM4 파라미터: Poly Allocation, Retrig Mode, Legato Mono, Unison Count, Unison Mode
- ✅ CM7 정수 6 ×14회 (기본 보이스), 12 ×10회 (Para 보이스)
- ⚠️ Poly/Dual은 mf_enums.py에서만 확인 (CM4 문자열 미발견 — 공유 포인터 가능성)

### 8. 아르페지에이터 — 65% → **95%** ⬆️⬆️
**매뉴얼**: 8모드 (Up/Down/UpDown/Random/Walk/Pattern/Order/Poly)

**펌웨어 증거 (Phase 11 신규)**:
- ✅ CM4 Arp Mode enum @ `0x081AEC3C`~`0x081AEC8C`: **Arp Up, Arp Down, Arp UpDown, Arp Rand, Arp Walk, Arp Pattern, Arp Order, Arp Poly — 8/8 전부 확인**
- ✅ CM4 Arp 수식어 4종: Arp Repeat, Arp Ratchet, Arp Rand Oct, Arp Mutate
- ✅ CM7 `FUN_080321d4` 5-case switch = 하위 분기 (CM4에서 8모드 → CM7에 5그룹 전달)
- ✅ CM7 확률 LUT ×3 (Walk/Random/Mutate)

### 9. 스텝 시퀀서 — 80% → **90%** ⬆️
**매뉴얼**: 64스텝, 4모듈레이션 레인

**펌웨어 증거 (Phase 11 신규)**:
- ✅ CM4 Smooth Mod 1~4 @ `0x081B1B8C`~`0x081B1BBC`: **4 lane 전부 확인**
- ✅ CM4 RTTI: `eSeqParams` @ `0x081AC84D`, `eSeqStepParams` @ `0x081AC8D9`, `eSeqAutomParams` @ `0x081AC97D`
- ✅ CM4 Seq 파라미터: Tempo Div, Seq Page, PlayState, RecState, RecMode, Cursor, MetronomeBeat
- ✅ CM7 정수 64 ×17회 (스텝 수), 4 ×16회 (레인 수)
- ⚠️ "64 Step" UI 문자열 없음 (컴파일 타임 상수)

### 10. 오디오 스펙/튜닝 — 100%
**매뉴얼**: 48kHz, A4=440Hz, ±48반음

**펌웨어 증거**:
- ✅ CM7 48000.0 ×1, 440.0 ×12, 1/12=0.0833, LOG2E=1.4427
- ✅ CM7 스테레오 처리 (VLD1/VST1 pairs)

### 11. Spice/Dice — 85%
CM7 지수적 확률 LUT @ `0x08067FDC`, Sync LUT @ `0x080687DC

### 12. CC 라우팅 — 80% → 82% ⬆️
CM7 `FUN_080612a4` 11-case CC 디스패치, 내부 161 CCs. CM4 RTTI eSeqParams 계열 추가.

### 13. 프리셋 시스템 — 80% → 82% ⬆️
CM7 프리셋 로드 시 vtable 포인터 3개 write. CM4 deprecated 파라미터 4종 식별:
- `UnisonOn TO BE DEPRECATED` @ `0x081AF994`
- `old FX3 Routing` @ `0x081AF70C`
- `obsolete Rec Count-In` @ `0x081AFB00`
- `internal use only` @ `0x081AF72C`

---

## 📌 주요 발견

### 매뉴얼에 없는 펌웨어 기능 (숨겨진 기능)
| 항목 | 매뉴얼 | 실제 펌웨어 |
|------|--------|-------------|
| Mod Matrix 소스 | 7개 | 9개 (+Sample Select, Wavetable Select) |
| Mod Matrix 목적지 | 13개 | 140개 (내부 파라미터 직접 모듈레이션) |
| 내부 CC | 38개 | 161개 |
| Poly Steal Mode | 4종 (None/Once/Cycle/Reassign) | **6종** (+Velocity, Velo + AT) |
| Unison 하위모드 | 미명시 | **3종** (Unison / Uni Poly / Uni Para) |
| deprecated 파라미터 | 미명시 | 4종 (UnisonOn, old FX3 Routing, Rec Count-In, internal) |
| Shaper 프리셋 | 미상세 | 20종 (12 빌트인 + 8 사용자) |

### 매뉴얼 불일치 (확인 필요)
| 항목 | 매뉴얼 | 펌웨어 | 신뢰도 |
|------|--------|--------|--------|
| Poly Steal Mode 수 | 4종 | 6종 | ★★★★★ (CM4 문자열) |
| Arp 모드 CM7 switch | 8모드 기대 | 5-case (그룹 분기) | ★★★★☆ (정상 — CM4→CM7 그룹화) |

---

## 분석 한계

불일치의 대부분은 **매뉴얼이 틀렸다**가 아니라 **stripped 바이너리에서 개별 항목을 식별할 수 없다**에 기인합니다. Phase 11에서 CM4 바이너리 스캔을 추가함으로써 대부분의 갭이 해소되었습니다.

### 남은 미확인 항목 (~8%)
1. **FX 코어 내부 DSP**: FX 코어 바이너리에 UI 문자열이 없어 개별 FX 타입의 내부 알고리즘 식별 불가 (Phase 7-3에서 서브프로세서 레벨까지만 확인)
2. **아날로그 필터 회로**: VCF는 하드웨어 → 보드 분해 없이 DAC LUT, 캘리브레이션 곡선 확인 불가
3. **Poly/Dual Voice Mode**: CM4 문자열 미발견 (mf_enums.py로만 확인)
4. **Spice/Dice 확률 분포**: LUT는 확인했으나 매뉴얼 명시값과의 정량적 비교 미완료

---

*Phase 10 초기 분석: 2026-04-26*
*Phase 11 갭 보완: 2026-04-26*
*상세 내역: `PHASE11_GAP_FILL_ANALYSIS.md`*
