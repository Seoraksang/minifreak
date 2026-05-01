# MiniFreak 매뉴얼 vs 펌웨어 일치도 분석 (Phase 16 업데이트)

**매뉴얼**: MiniFreak User Manual v4.0.1 + MiniFreak V Manual
**펌웨어**: fw4_0_1_2229 (CM4 + CM7 + FX)
**분석 날짜**: 2026-05-01
**종합 일치도**: **95.6%**

---

## 1. 종합 일치도

| 카테고리 | 가중치 | Phase 12 | Phase 13 | Phase 16 | 기여값 | 변화 사유 |
|----------|--------|----------|----------|----------|--------|-----------|
| 오실레이터 엔진 (OSC) | 20% | 95% | 95% | **95%** | 19.00 | — |
| 필터 시스템 (Filter) | 15% | 96% | 96% | **96%** | 14.40 | Phase 16-4 Multi Filter DSP 매핑으로 유지 |
| 디지털 이펙트 (FX) | 10% | 95% | 96% | **96%** | 9.60 | Phase 16-5 FX 11 DSP 함수 정리로 유지 |
| LFO | 8% | 98% | 98% | **97%** | 7.76 | Phase 14-2 RateSync 17→27 (CM4=17, VST=27), 매뉴얼=11→차이 확대 |
| 엔벨로프 (Env) | 8% | 97% | 97% | **97%** | 7.76 | — |
| 모듈레이션 매트릭스 (Mod Matrix) | 10% | 99% | 99% | **98%** | 9.80 | CORR-11 assignable 91슬롯 (매뉴얼 "7×~4"), CORR-02 소스 9개 (매뉴얼 7개) |
| 보이스 모드 (Voice) | 7% | 95% | 95% | **95%** | 6.65 | — |
| 아르페지에이터 (Arp) | 5% | 95% | 93% | **93%** | 4.65 | Walk LUT 포맷 불확실 유지 (Phase 13 하향) |
| 스텝 시퀀서 (Seq) | 5% | 97% | 97% | **97%** | 4.85 | — |
| 오디오 스펙/튜닝 (Audio) | 5% | 100% | 100% | **100%** | 5.00 | — |
| Spice/Dice | 3% | 88% | 85% | **83%** | 2.49 | Phase 13 LUT 포맷 재검토 하향 + 매뉴얼 확률 기술 vs 펌웨어 불일치 가능성 |
| CC 라우팅 | 2% | 96% | 96% | **95%** | 1.90 | CORR-13 DLL 1,557 hidden params (매뉴얼 전무) |
| 프리셋 시스템 (Preset) | 2% | 90% | 90% | **89%** | 1.78 | Phase 15-1 deprecated/obsolete 2종 추가 확인 + eEditParams 79항목 중 활성 27 |
| | **100%** | | | | **95.64%** | |
| **종합** | **100%** | **96.0%** | **95.7%** | **95.6%** | **95.64%** | Phase 14-2/15-1/16 신규 결함 누적 |

### 변화 추이

```
Phase 10:  86.4% ── 초기 갭 분석
Phase 11:  91.8% ── CM4 바이너리 직접 스캔
Phase 12:  96.0% ── 정적 분석 완료 (FX/CC/Mod/Seq 대폭 상승)
Phase 13:  95.7% ── V 매뉴얼 통합 재검증 (Walk LUT + Spice LUT 정직 하향)
Phase 16:  95.6% ── Collage/DLL/Deprecation/CORR-11~13 신규 결함 반영
```

---

## 2. 카테고리별 상세 분석

### 2.1 오실레이터 엔진 — 95%

**매뉴얼 기술 내용** (manual_mf.txt §5, p.24-48):
- Osc 1: 16 타입 (BasicWaves, SuperWave, Harmo, KarplusStr, VAnalog, Waveshaper, Two Op. FM, Formant, Speech, Modal, Noise, Bass, SawX, Harm, Audio In, Wavetable)
- Osc 2: 14 공통 + 7 고유 (Chords, FM/RM, Multi Filter, Surgeon Filt, Comb Filter, Phaser Filter, Destroy) = 21 타입
- 매뉴얼 §5.2: "Osc 1 and Osc 2 have fourteen Types in common; Osc 1 has two of its own (Audio In & Wavetables) and Osc 2 has six unique Types plus an additional chord Engine"
- Wave/Timbre/Shape 3노브 + Volume + Mod Quantize

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| CM4 Osc 타입 문자열 30개 | ★★★★★ | `0x081AF388`~`0x081AF4C8` — Osc1 16종 + Osc2 21종 (Wavetable/Sample/Grains 계열 포함) |
| CM7 vtable 99개 | ★★★★☆ | 다형성 OSC 아키텍처, 1:1 매핑은 런타임 필요 |
| CM7 16-case switch | ★★★★★ | `FUN_0803e6f8` — OSC 타입 디스패치 |
| VST XML Osc1 24종 | ★★★★★ | `Osc1_Type_V2.9.0` (Sample, Cloud Grains, Hit Grains, Frozen, Skan, Particle, Lick, Raster 추가) |
| VST XML Osc2 30종 | ★★★★★ | 21 real + 9 reserved (index 21~29, CORR-12) |
| Osc2 9 dummy 항목 | ★★★★★ | 매뉴얼에 reserved 언급 없음 (CORR-12) |

**일치 항목**: 16 Osc1 + 21 Osc2 타입 = 37개 중 37개 매뉴얼/펌웨어 일치
**불일치 항목**: Osc2 reserved 9개 (매뉴얼 누락, CORR-12), VST 전용 Sample/Grains 계열 8종 (HW 매뉴얼에 별도 설명 없음)
**누락 항목**: Mod Quantize 11스케일 (CM4 확인, 매뉴얼 명시 있음)

---

### 2.2 필터 시스템 — 96%

**매뉴얼 기술 내용** (manual_mf.txt §6, p.49-52):
- 아날로그 필터: SEM 기반 LP/HP/BP, 12dB/oct 고정 slope
- 디지털 Multi Filter (Osc2): LP/HP/BP 다양한 slope (§5.3.1)
- 디지털 Surgeon Filter (Osc2): 파라메트릭 EQ (§5.3.2)
- 디지털 Comb Filter (Osc2): 지연 기반 (§5.3.3)
- 디지털 Phaser Filter (Osc2): 2~12 pole (§5.3.4)
- 디지털 Destroy (Osc2): 웨이브폴더 + 디시메이터 + 비트크러셔 (§5.3.5)

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| CM4 VCF 모드 문자열 | ★★★★★ | `0x081AF4D0`: LP, BP, HP, Notch, LP1, HP1, Notch2 |
| Multi Filter 14모드 | ★★★★★ | `0x081B0D90`~`0x081B0DE8`: LP6/12/24/36, HP6/12/24/36, BP12/24/36, N12/24/36 (Phase 16-4 확인) |
| CM7 CMP #11/#12 | ★★★★☆ | 14모드(0-13) 범위 검사 패턴 |
| CM7 Biquad 계수 | ★★★★★ | 0.707(1/√2) ×8 |
| CM7 IIR smoothing 20개 | ★★★★★ | 필터 파라미터 스무딩 |
| 아날로그 SEM 회로 | ★★☆☆☆ | 하드웨어 회로, 보드 분해 필요 |

**일치 항목**: 아날로그 LP/HP/BP (3), Multi Filter 14모드, Surgeon/Comb/Phaser/Destroy (5종) — 전부 일치
**불일치 항목**: 매뉴얼은 Multi Filter slope를 "wide variety"로만 기술, 펌웨어는 14모드 구체적

---

### 2.3 디지털 이펙트 (FX) — 96%

**매뉴얼 기술 내용** (manual_mf.txt §7, p.53-62):
- FX 타입 10종 (§7.2: "There are ten Types in total") + Vocoder Ext In + Vocoder Self (v4.0 추가) = 총 12종 (HW)
- 3슬롯 체인, Insert/Send 라우팅
- Subtype 시스템 (FX 타입별 다수 프리셋)
- Singleton 제약: Reverb, Delay, Multi Comp (1개씩만)

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| CM4 FX 타입 12종 | ★★★★★ | `0x081AF308`: Chorus, Phaser, Flanger, Reverb, Distortion, Bit Crusher, 3 Bands EQ, Peak EQ, Multi Comp, SuperUnison, Vocoder Self, Vocoder Ext |
| VST FX 타입 13종 | ★★★★★ | + Stereo Delay (VST 전용) |
| FX 코어 7 SP | ★★★★★ | SP0~SP6, 3슬롯 × 7SP 체인 |
| DSP 11함수 1:1 매핑 | ★★★★☆ | Phase 16-5: Chorus→SP6, Reverb→SP3, Delay→SP1+SP2, Vocoder Self→SP5, Vocoder Ext→SP4 등 |
| Subtype 63종 | ★★★★★ | Phase 8 VST XML 확인 |

**일치 항목**: 12/12 CM4 FX 타입, 3슬롯 체인, Insert/Send, Singleton 제약, Subtype 시스템
**불일치 항목**: Stereo Delay (VST 전용, CM4 없음) — 매뉴얼에 HW/VST 차이 미명시 (CORR-10)
**누락 항목**: FX 코어 DSP 함수 290개, SP0~SP6 구조체 크기 — 매뉴얼에 기술 없음

---

### 2.4 LFO — 97% ⬇️

**매뉴얼 기술 내용** (manual_mf.txt §9, p.68-75):
- LFO 1/2: 9파형 (Sin, Tri, Saw, Sqr, SnH, SlewSNH, ExpSaw, ExpRamp, Shaper)
- 8 Retrig 모드
- Vibrato (LFO3): 독립 모듈, triangle wave
- Shaper: 16스텝 사용자 커브 + 프리셋
- Tempo Sync (Sync Filter)

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| CM4 LFO 파형 7/9 | ★★★★★ | `0x081B0FB0`: Sin, Tri, Sqr, SlewSNH, ExpSaw, ExpRamp, Shaper (Saw, SnH는 VST 교차검증) |
| CM4 LFO Retrig 8/8 | ★★★★★ | `0x081B0E7C` |
| Vibrato 6문자열 | ★★★★★ | `0x081AE128`: Vibrato On/Off, Vibrato, Vibrato Depth, Vib Rate, Vib AM |
| Shaper 25종 | ★★★★★ | `0x081AF128`: 1 기본 + 16 빌트인 + 8 사용자 |
| CM4 RateSync 17종 | ★★★★★ | `0x081AF0B4` (11종) + `0x081AF564` (6종) |
| **VST RateSync 27종** | ★★★★★ | Phase 14-2: LFO_RateSync item_list — CM4보다 10종 많음 |

**Phase 13→16 변경**: RateSync 불일치 확대
- 매뉴얼: Time Division 14종 (§14.1.3: 1/2D, 1/2, 1/4D, 1/4, 1/8D, 1/4T, 1/8, 1/16D, 1/8T, 1/16, 1/32D, 1/16T, 1/32, 1/32T)
- CM4 펌웨어: 17종 (매뉴얼 14 + 1/32t, 1/16t, 1/8t, 1/4t, 1/2t, 1/1 — 소문자 triplet 변형)
- VST: 27종 (CM4 17 + 8d, 4d, 2d, 1d 등 dotted 계열 추가)
- **CORR-06**: 매뉴얼 14종 vs VST 27종 = 13종 누락 (Phase 14-2에서 기존 CORR-06 업데이트)

---

### 2.5 엔벨로프 — 97%

**매뉴얼 기술 내용** (manual_mf.txt §10, p.76-83):
- ADSR Envelope: Attack, Decay, Sustain, Release + Velo > VCA/VCF/Env
- Retrig Mode: Env Reset, Free Run, Legato
- Cycling Envelope: Rise/Fall/Hold, Mode (Env/Run/Loop), Retrig (Poly Kbd/Mono Kbd/Legato Kb/LFO 1/LFO 2), Stage Order (RHF/RFH/HRF)
- Tempo Sync

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| ADSR 4단계 | ★★★★★ | CM4 eEditParams Attack/Decay/Release @ `0x081AF7E8`~`0x081AF7F8` |
| CycEnv Mode/Retrig | ★★★★★ | `0x081AF840`~`0x081AF880` |
| Stage Order 3종 | ★★★★★ | RHF, RFH, HRF @ `0x081AF880` |
| Para Env 분리없음 | ★★★★★ | Para 모드 = Voice Env + CycEnv 동시 사용 |
| CycEnv Loop2 | ★★★☆☆ | VST만 확인 (CM4에서 문자열 없음, ENH-04) |
| CM7 VABS.F32 ×68 | ★★★★☆ | 64-entry time scale LUT |

---

### 2.6 모듈레이션 매트릭스 — 98% ⬇️

**매뉴얼 기술 내용** (manual_mf.txt §8, p.63-67 + §12.2.1, p.86):
- 7 Row 소스: CycEnv, LFO1, LFO2, Velo/AT, Wheel, Keyboard, Mod Seq
- ~30개 Assignable Destination
- 7×4 dot (28 hardwired) + Assignable routing

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| CM4 Mod Source 9종 | ★★★★★ | `0x081B1BCC`: Keyboard, LFO, Cycling Env, Env/Voice, Voice, Envelope, FX, Sample Select, Wavetable Select |
| ~247 destination | ★★★★★ | 51 user + ~196 internal (Phase 12-4) |
| **91 assignable slots** | ★★★★★ | Mx_Dot 28 + Mx_AssignDot 63 (Phase 14-2, CORR-11) |
| Meta-modulation | ★★★★★ | 2-level depth |
| Custom Assign 8목적지 | ★★★★★ | `0x081AEA94`: Vib Rate, Vib AM, VCA, LFO1/2 AM, CycEnv AM, Uni Spread, -Empty- |

**불일치 항목**:
- **CORR-02**: 매뉴얼 7소스 vs 펌웨어 9소스 (Sample Select, Wavetable Select 누락)
- **CORR-11**: 매뉴얼 "7 rows × ~4 destinations" vs 펌웨어 91 assignable slots (28 hardwired + 63 assignable)

---

### 2.7 보이스 모드 — 95%

**매뉴얼 기술 내용** (manual_mf.txt §10.3, p.78-79):
- 4종: Mono, Poly, Para, Uni
- Unison 하위모드: Mono, Poly, Para
- Poly Steal Mode: None, Once, Cycle, Reassign (4종)
- Paraphonic: 12 voice pairs, Osc2 비활성화

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| Voice Mode enum | ★★★★★ | `0x081AF500`: Unison, Uni (Poly), Uni (Para), Mono, Para |
| **Poly Steal Mode 6종** | ★★★★★ | `0x081B0F70`: None, Cycle, Reassign, **Velocity, Aftertouch, Velo + AT** (CORR-01) |
| Poly Steal: "Once" 미존재 | ★★★★★ | 매뉴얼 "Once" = 펌웨어에 없음 |
| Poly2Mono toggle | ★★★★☆ | `0x081AE128` |
| Poly/Dual 독립 문자열 | ★★★★☆ | 다른 enum과 포인터 공유 |
| Poly Allocation 3모드 | ★★★☆☆ | Cycle/Reassign/Reset (mf_enums만) |

---

### 2.8 아르페지에이터 — 93% ⬇️

**매뉴얼 기술 내용** (manual_mf.txt §14.2, p.97-99):
- 8모드: Up, Down, UpDown, Random, Order, Walk, Poly, Pattern
- 수식어 4종: Repeat, Ratchets, Rand Oct, Mutate
- Walk 확률: "25% chance to play the previous or current one, 50% chance to play the next one"
- Rand Oct: 75% 정상, 15% +1oct, 7% -1oct, 3% +2oct
- Mutate: 75% 유지, 5% +5th, 5% -4th, 5% +oct, 5% -oct, 3% swap, 2% swap2

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| Arp Mode 8/8 | ★★★★★ | `0x081AEC3C`: Arp Up, Down, UpDown, Rand, Walk, Pattern, Order, Poly |
| 수식어 4종 | ★★★★★ | Repeat, Ratchet, Rand Oct, Mutate |
| Walk 확률 분포 | ★★☆☆☆ | CM7 Walk LUT @ `0x080546C4` (64 bytes) — uint8 해석 결과가 매뉴얼 기술과 불일치 (Phase 13) |
| Mutate 확률 분포 | ★★☆☆☆ | 동일 LUT 포맷 불확실 |
| Arp 모드 인덱스 순서 | ★★★★★ | 펌웨어 Up/Down/UpDown/Rand/Walk/Pattern/Order/Poly vs 매뉴얼 순서 상이 (CORR-03) |

**Phase 13 하향 사유**: Walk LUT `0x080546C4`의 64 bytes를 uint8로 해석한 결과가 매뉴얼의 "25/25/50%" 패턴과 일치하지 않음. LUT가 pair-wise 또는 structured 포맷일 가능성. 매뉴얼 확률값의 펌웨어 검증 불가 → 신뢰도 하향.

---

### 2.9 스텝 시퀀서 — 97%

**매뉴얼 기술 내용** (manual_mf.txt §14.3, p.99-111):
- 64스텝 최대, 4페이지 (16스텝/페이지)
- 4 modulation lane
- 3녹음 모드 (Step Rec, Real-time, Overdub)
- Time Division 14종 (Arp와 공유)
- Smooth Mod 1/2/3/4
- Copy Arp to Seq

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| 64-step buffer | ★★★★★ | CM7 정수 64 × 17회, boost::serialization |
| 24 field/step | ★★★★★ | StepState + Gate + 6×(Pitch, Length, Velo) + 4×Mod + ModState |
| Smooth Mod 4종 | ★★★★★ | `0x081B1B8C`: 4, 3, 2, 1 (역순) |
| 3녹음 모드 | ★★★★☆ | CM4 RecState/RecMode + CM7 6-case state machine |

---

### 2.10 오디오 스펙/튜닝 — 100%

| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| 48kHz 샘플레이트 | ★★★★★ | CM7 48000.0 float |
| A4 = 440Hz | ★★★★★ | CM7 440.0 ×12 |
| 3코어 아키텍처 | ★★★★★ | CM4+CM7+FX, HSEM 동기화 (Phase 15 Audio Routing) |
| USB MIDI | ★★★★★ | VID 0x152E, EP IN 0x81/OUT 0x02 |

---

### 2.11 Spice/Dice — 83% ⬇️

**매뉴얼 기술 내용** (manual_mf.txt §14.1.8, p.96):
- Spice: 확률적 변이 글로벌 양
- Dice: 새로운 랜덤 시퀀스 생성 (비파괴적)
- 대상 파라미터: Velocity, Octave(±1), Gate length, Step On/Off, Env Decay/Release

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| spice_exp_lut @ CM7 | ★★☆☆☆ | `0x08067FDC` (64 bytes) — 단순 지수 분포가 아님, pair-wise 패턴 (237, 242, 245, 248 반복) |
| env_time_scale @ CM7 | ★☆☆☆☆ | `0x0806D330` (256 bytes) — float32 해석 시 대부분 비정상값 |
| Walk 확률 LUT | ★★☆☆☆ | `0x080546C4` — uint8 해석 불일치 |
| Spice/Dice 대상 파라미터 | ★★★★☆ | 매뉴얼 5개 파라미터 (Velocity, Octave, Gate, Step, Env) — 논리적 합리 |

**Phase 13→16 하향 사유**:
1. Phase 13: spice_exp_lut이 단순 지수 분포가 아님 → "다른 LUT"일 가능성 (예: 오실레이터 파라미터 스케일링)
2. Phase 13: env_time_scale float32 해석 부적절 → 다른 포맷일 가능성
3. 매뉴얼에 확률 분포 수치 없음 (Walk 제외) → 펌웨어 LUT와의 교차검증 불가
4. Dice의 실제 난수 생성 알고리즘 미확인

---

### 2.12 CC 라우팅 — 95% ⬇️

**매뉴얼 기술 내용** (manual_mf.txt §16.2.5, p.115-116):
- MIDI Implementation Chart: ~38개 CC 매핑
- CC#1 (Mod Wheel), CC#5 (Glide), CC#14-21 (Osc1/2 파라미터), CC#22-31 (FX), CC#64 (Sustain), CC#68-78 (Env/CycEnv), CC#80-83 (ADSR), CC#85-87 (LFO), CC#94 (Velo Env Mod), CC#115-118 (Gate/Spice/M1/M2)

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| CM7 CC handler 161개 | ★★★★★ | `FUN_08066810` |
| VST 148 realtimemidi | ★★★★★ | minifreak_vst_params.xml |
| NRPN 33 case | ★★★★★ | Mod Matrix NRPN 22 sub-param |
| SysEx CRC + Q15 | ★★★★☆ | 고정소수점 스케일링 |
| Learn mode filtering | ★★★★★ | CC 204 excluded |
| 16-channel param router | ★★★★★ | NRPN 0x9E~0xAD |
| **DLL 1,705 params** | ★★★★☆ | VST 148 + hidden 1,557 (CORR-13) |

**Phase 14-2 하향 사유**: DLL에서 1,705개 파라미터 이름 추출, VST XML 148개와만 일치 → **1,557개 hidden VST↔HW sync parameters** 존재 (CORR-13). 매뉴얼에 이들에 대한 언급 전무.

---

### 2.13 프리셋 시스템 — 89% ⬇️

**매뉴얼 기술 내용** (manual_mf.txt §4, p.18-23):
- 512 프리셋 (4 bank × 128)
- 프리셋 타입: INIT, SFX 등
- Copy/Paste/Erase
- User Shaper Wave 저장

**펌웨어 증거**:
| 항목 | 증거 수준 | 상세 |
|------|----------|------|
| boost::serialization | ★★★★★ | 텍스트 포맷 (binary buffer 아님) |
| 2,368 total params | ★★★★★ | 2,175 seq + 193 synth |
| deprecated 4종 | ★★★★★ | UnisonOn DEPRECATED, old FX3 Routing, obsolete Rec Count-In, internal use only |
| eEditParams 79항목 | ★★★★★ | Phase 15-1: 활성 27, DEPRECATED 1, Obsolete 1, UI 상태 16, UI 라벨 35 |
| **Collage 프로토콜 62 메시지** | ★★★★☆ | Phase 14-1: protobuf 기반 USB bulk (MIDI 아님) — 매뉴얼에 USB 통신은 "MIDI와 동일"으로만 기술 |
| **이스터에그 4건** | ★★★★★ | Phase 15-1: 개발자 메시지 4건 (매뉴얼 외 영역) |
| 프리셋 로드 vtable swap | ★★☆☆☆ | 런타임 동적, JTAG 필요 |

**Phase 15-1 하향 사유**: eEditParams 79항목 중 활성 파라미터 27개뿐, 나머지 52개는 UI 상태/라벨/레거시. deprecated+obsolete 2종이 명시적으로 마크됨. 매뉴얼에 프리셋 포맷 구조나 파라미터 수에 대한 설명 없음.

---

## 3. 매뉴얼 결함 (정정 권고 CORR 요약)

### 정정 항목 13건

| ID | 카테고리 | 매뉴얼 | 펌웨어 실제 | 신뢰도 | Phase |
|----|----------|--------|-------------|--------|-------|
| CORR-01 | Voice | Poly Steal 4종 | **6종** (Velocity, Aftertouch, Velo+AT 추가) | ★★★★★ | 12 |
| CORR-02 | Mod Matrix | 소스 7개 | **9개** (Sample Select, Wavetable Select 추가) | ★★★★★ | 12 |
| CORR-03 | Arp | UpDown 재사용 추정 | **"Arp UpDown" 독립 문자열** | ★★★★★ | 12 |
| CORR-04 | Voice | Unison 하위모드 불명확 | **3개 독립 Voice Mode** (Unison, Uni(Poly), Uni(Para)) | ★★★★★ | 12 |
| CORR-05 | LFO | 전체 파형명 (Sine, Triangle 등) | **약어명** (Sin, Tri, Saw 등) | ★★★★★ | 12 |
| CORR-06 | Tempo | Subdivision 11→14종 | **27종** (VST XML LFO_RateSync) | ★★★★★ | 14-2 |
| CORR-07 | LFO | 9파형 (일부 섹션 누락) | **9파형 확정** (내부 모순) | ★★★★★ | 12 |
| CORR-08 | LFO Shaper | 첫 항목 "Shaper" | **"Preset Shaper"** (25종) | ★★★★★ | 12 |
| CORR-09 | Mod Matrix | 간략한 설명 | **Custom Assign 8목적지** 상세 주소 | ★★★★★ | 12 |
| CORR-10 | FX | HW/VST 구분 없음 | **Stereo Delay = VST 전용** (CM4 12, VST 13) | ★★★★★ | 12 |
| CORR-11 | Mod Matrix | "7 rows × ~4 dest" | **91 assignable slots** (28+63) | ★★★★★ | 14-2 |
| CORR-12 | OSC | Osc2 타입 개수 불명확 | **21 real + 9 reserved** (30 enum) | ★★★★★ | 14-2 |
| CORR-13 | Parameter | 언급 없음 | **1,557개 hidden VST↔HW sync params** | ★★★★☆ | 14-2 |

### 보완 항목 12건

| ID | 카테고리 | 매뉴얼 | 펌웨어 누락 기능 | 신뢰도 |
|----|----------|--------|-----------------|--------|
| ENH-01 | Mod Matrix | ~30 dest | **~196개 내부 목적지** | ★★★★☆ |
| ENH-02 | LFO | User Shaper만 | **25종 Shaper 프리셋** | ★★★★★ |
| ENH-03 | Preset | 언급 없음 | **4종 deprecated 파라미터** | ★★★★★ |
| ENH-04 | CycEnv | 3모드 | **Loop2 (4번째 모드)** | ★★★☆☆ |
| ENH-05 | Voice | 불충분 | **Poly Allocation 3모드** | ★★★☆☆ |
| ENH-06 | MIDI | 38 CC | **161개 내부 CC** | ★★★★☆ |
| ENH-07 | FX | 불충분 | **Vocoder 2타입 별도 DSP** | ★★★★☆ |
| ENH-08 | Seq | 4 lane만 | **Smooth Mod 1~4 파라미터** | ★★★★★ |
| ENH-09 | Arp | 모호한 설명 | **확률 분포 (추정, LUT 불확실)** | ★★★★☆ |
| ENH-10 | Mod Matrix | 간략 | **Custom Assign 8목적지** | ★★★★★ |
| ENH-11 | FX | 불명확 | **Singleton 제약 3종** | ★★★★☆ |
| ENH-12 | Seq | 64-step만 | **3녹음모드 + state machine** | ★★★★☆ |

---

## 4. 펌웨어 전용 영역 (매뉴얼에 없음)

### 4.1 Collage 프로토콜 (Phase 14-1)
- **62개 protobuf 메시지** + 14개 enum
- USB bulk transfer (MIDI 아님)
- VID 0x152E, EP IN 0x81 / OUT 0x02
- 12개 .proto 파일 (Top, Control, Data, Security 등)
- ResourceLocation 11개 (PRESET, WAVETABLE 등)
- **매뉴얼 §16.3**: "USB 포트는 MIDI 케이블 한 쌍과 동일하게 작동" — Collage 존재 미명시

### 4.2 Hidden VST↔HW 파라미터 (Phase 14-2, CORR-13)
- DLL strings 1,705개 중 VST 148개 제외 → **1,557개 hidden**
- Mod_S0~63, Pitch_S0~63, Velo_S0~63, Gate_S0~63, StepState_S0~63
- Reserved1~4, AutomReserved1
- 프리셋 직렬화/역직렬화, UI 상태 복원, 내부 DSP 제어

### 4.3 Deprecated/Obsolete/이스터에그 (Phase 15-1)
| 항목 | 주소 | 내용 |
|------|------|------|
| DEPRECATED | `0x081AF994` | `UnisonOn TO BE DEPRECATED` |
| Obsolete | `0x081AFB00` | `obsolete Rec Count-In` |
| 이스터에그 | `0x081B34A4` | "If you ask Olivier D, he'll tell you that it's a feature" |
| 이스터에그 | `0x081B3298` | "...Ask Thomas A" |
| 이스터에그 | `0x081B33E8` | "...ask Mathieu B" |
| 이스터에그 | `0x081B2F42` | "Hey Frederic, are you ready to hear sounds you never heard before?" |

### 4.4 FX 코어 DSP 상세 (Phase 16-5)
- FX 코어 290개 함수 (named 3, unnamed 287)
- 7서브프로세서 (SP0~SP6) 구조체 크기/함수 매핑
- SP6 하위 5개 DSP 엔진 (BiQuad, Allpass, Waveshaper, Modulation, Multi-detune)
- 32768.0 스케일링, FreeRTOS 기반

### 4.5 Multi Filter DSP 상세 (Phase 16-4)
- CM7 CMP #11/#12 패턴 → 14모드 범위 검사
- FUN_0803C2BC (9,250B) = VCF 필터 계수 + 오실레이터
- FUN_08034338 (5,046B) = 필터 계산 본체
- 정수 인덱스 기반 디스패치 (포인터 테이블 없음)

### 4.6 오디오 라우팅 (Phase 15 Audio Routing)
- CM4 HSEM 35회 참조 (코어간 동기화)
- CM7 TIM2 39회 (오디오 샘플레이트)
- CM4↔FX UART3 통신
- SAI2 I2S 오디오 출력

---

## 5. 진척 그래프

```
96.0% ┤████████████████████████████████████████████████████████████ Phase 12
      │
95.7% ┤███████████████████████████████████████████████████████████▌       Phase 13
      │                                                     (-0.3%)
95.4% ┤██████████████████████████████████████████████████████████        Phase 16
      │                                                     (-0.3%)
      │
94.0% ┤████████████████████████████████████████████████████████
      │
92.0% ┤████████████████████████████████████████████████████
      │
91.8% ┤███████████████████████████████████████████████████▌ Phase 11
      │
90.0% ┤█████████████████████████████████████████████████
      │
86.4% ┤███████████████████████████████████████████▌       Phase 10
      │
80.0% ┤███████████████████████████████████
      │
      └────────────────────────────────────────────────────────
       P10    P11    P12    P13    P16

카테고리별 Phase 16 일치도:
OSC    ██████████████████████████████████████████████████░  95%
Filter ███████████████████████████████████████████████████  96%
FX     ███████████████████████████████████████████████████  96%
LFO    ██████████████████████████████████████████████████░  97%
Env    ███████████████████████████████████████████████████  97%
ModMat ███████████████████████████████████████████████████  98%
Voice  ██████████████████████████████████████████████████░  95%
Arp    ████████████████████████████████████████████████░░░  93%
Seq    ███████████████████████████████████████████████████  97%
Audio  ████████████████████████████████████████████████████ 100%
S/Dice █████████████████████████████████████████████████░░░  83%
CC     ██████████████████████████████████████████████████░░  95%
Preset ████████████████████████████████████████████████░░░  89%
```

---

## 6. 잔여 갭 분석

### 6.1 정적 분석 한계 (~4.6%)

| 갭 | 카테고리 | 크기 | 해결 방법 |
|----|----------|------|-----------|
| OSC 99 vtable 1:1 매핑 | OSC | ~2% | JTAG/SWD 런타임 트레이스 |
| Walk/Mutate 확률 LUT | Arp | ~2% | USB 캡처 동적 검증 |
| Spice/Dice 확률 LUT | S/Dice | ~4% | USB 캡처 + LUT 포맷 확정 |
| Poly/Dual 독립 문자열 | Voice | ~1% | CM7 디스어셈블리 심화 |
| 프리셋 로드 vtable swap | Preset | ~2% | JTAG 런타임 트레이스 |
| 아날로그 필터 회로 | Filter | ~1% | 보드 분해 |
| CycEnv Loop2 | Env | ~1% | 향후 펌웨어 업데이트 관찰 |
| env_time_scale 포맷 | S/Dice | ~3% | CM7 디스어셈블리 (float32 아닐 가능성) |

### 6.2 매뉴얼 개선 우선순위

| 우선순위 | 항목 | 영향 | 작업량 |
|----------|------|------|--------|
| **높음** | CORR-01: Poly Steal Mode 4→6종 | Voice 기능 오류 | 낮음 |
| **높음** | CORR-06: Tempo Subdivision 14→27종 | LFO/Seq 동기화 누락 | 중간 |
| **높음** | CORR-11: Mod Matrix 91슬롯 명시 | 사용자 혼란 | 중간 |
| **높음** | CORR-12: Osc2 reserved 9개 명시 | 향후 확장 예고 | 낮음 |
| **중간** | CORR-02: Mod Source 9개 | V3 기능 누락 | 낮음 |
| **중간** | CORR-05: LFO 파형 약어 병기 | 디스플레이 불일치 | 낮음 |
| **중간** | ENH-06: CC 161개 전체 맵 | MIDI 구현 누락 | 높음 |
| **낮음** | ENH-02: Shaper 25종 목록 | 사용자 편의성 | 낮음 |

### 6.3 향후 분석 방향

1. **Phase 16-2 (동적 검증)**: USB 캡처로 Walk/Mutate/Spice 확률 LUT 확정 → Arp 93%→?, S/Dice 83%→? 상향 가능
2. **Phase 17 (CM7 디스어셈블리)**: env_time_scale 포맷 확정, OSC vtable 1:1 매핑 시도
3. **VST 추가 XML 탐색**: FX 타입, LFO 파형, Arp 모드 등의 별도 리소스 파일

---

## 참고 문헌

| 문서 | Phase | 내용 |
|------|-------|------|
| `PHASE10_MANUAL_GAP_ANALYSIS.md` | 10 | 초기 매뉴얼 갭 분석 |
| `PHASE11_GAP_FILL_ANALYSIS.md` | 11 | CM4 바이너리 직접 스캔 |
| `PHASE12_GAP_ANALYSIS.md` | 12 | 정적 분석 완료 |
| `PHASE12_FX_CORE_DSP.md` | 12 | FX 12/13타입 × 7SP + DSP 11함수 |
| `PHASE12_CC_FULL_MAPPING.md` | 12 | 161 CC 전체 매핑 |
| `PHASE12_MOD_DEST_FULL.md` | 12 | ~247 destination enum |
| `PHASE12_SEQ_BUFFER_LAYOUT.md` | 12 | 64-step 24 field/step |
| `PHASE13_V_INTEGRATED_VERIFICATION.md` | 13 | 3원 교차검증 (CM4+VST+mf_enums) |
| `PHASE14_COLLAGE_PROTOCOL_ANALYSIS.md` | 14-1 | Collage 프로토콜 62 메시지 |
| `PHASE14_VST_HW_PARAM_MAPPING.md` | 14-2 | VST 148 params + DLL 1,705 |
| `PHASE15_EDITPARAMS_DEPRECATION.md` | 15-1 | eEditParams 79항목 분류 |
| `PHASE15_AUDIO_ROUTING.md` | 15 | CM7→FX 오디오 라우팅 |
| `PHASE15_FIRMWARE_PATCH_EXPERIMENT.md` | 15-2 | 7개 안전한 펌웨어 패치 |
| `PHASE16_MULTI_FILTER_DSP.md` | 16-4 | Multi Filter 14모드 DSP 매핑 |
| `PHASE16_FX_TYPE_TO_DSP.md` | 16-5 | FX 11 DSP × 12/13 타입 매핑 |
| `MANUAL_CORRECTION_RECOMMENDATIONS.md` | V5 | CORR 13건 + ENH 12건 |

---

*Phase 10 초기 분석: 2026-04-26*
*Phase 11 갭 보완: 2026-04-26*
*Phase 12 정적 분석 완료: 2026-04-26*
*Phase 13 V 통합 재검증: 2026-04-29*
*Phase 14 Collage/VST 매핑: 2026-04-29~05-01*
*Phase 15 Deprecation/Audio: 2026-05-01*
*Phase 16 Filter/FX DSP: 2026-05-01*
*종합 일치도: 95.6% (Phase 16)*
