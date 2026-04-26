# 🐉 Hydra — MiniFreak 리버싱 마스터 플랜

> **대상**: Arturia MiniFreak 펌웨어 v4.0.1 (fw4_0_1_2229)
> **MCU**: STM32H745/747 (듀얼코어 Cortex-M7 + Cortex-M4)
> **시작일**: 2026-04-21

---

## 이미 파악된 정보

```
MCU: STM32H745/747 (듀얼코어 Cortex-M7 + Cortex-M4)
펌웨어: .mnf = ZIP 컨테이너 (암호화 없음, DFU 방식)
내부: 7개 ARM 바이너리 (main CM4, main CM7, FX DSP, UI x4)
USB: Class-compliant MIDI (VID:0x1C75, PID:0x0602)
MIDI CC: 30개+ 매핑됨 (Cutoff=74, Resonance=71 등)
엔진: 디지털 오실레이터 x2 → 아날로그 VCF → 아날로그 VCA → 디지털 FX
      Mutable Instruments Plaits 코드 일부 포함 (MIT)
```

## 바이너리 맵

| # | 파일명 | 크기 | 역할 (추정) |
|---|--------|------|-------------|
| 0 | `main_CM4` | 608K | Cortex-M4 코어 — 페리페럴 관리자 (SAI/DMA/GPIO), MIDI, UI 통신, 프리셋 관리 |
| 1 | `main_CM7` | 512K | Cortex-M7 코어 — 오디오 DSP 처리 (float/NEON, 오실레이터, 필터, VCA) |
| 2 | `fx` | 120K | 디지털 FX DSP (Chorus, Delay, Reverb 등) |
| 3 | `ui_screen` | 172K | OLED 디스플레이 컨트롤러 |
| 4 | `ui_matrix` | 68K | 버튼 매트릭스 + LED 컨트롤러 |
| 5 | `ui_ribbon` | 68K | 터치스트립 컨트롤러 |
| 6 | `ui_kbd` | 44K | 키베드 스캔 + 벨로시티/애프터터치 |

---

## Phase 0: 기반 작업 ✅ (완료)
- [x] 매뉴얼 분석 (minifreak_technical_summary.md)
- [x] 펌웨어 구조 파악 (.mnf = ZIP → 7개 바이너리)
- [x] 프로젝트 디렉토리 구성
- [x] 기술 사양 문서화

## Phase 1: 바이너리 초기 트리아지 ✅ (완료)
- [x] CM7 메인 — 메모리맵, 함수 목록, 문자열 추출
- [x] CM4 메인 — 메모리맵, 함수 목록, 문자열 추출
- [x] FX DSP — 메모리맵, 함수 목록, 문자열 추출
- [x] UI 4개 (screen/matrix/ribbon/kbd) 일괄 분석
- [x] 결과 비교/교차 분석 → 함수 네이밍 매핑

### Phase 1 산출물
- `firmware/analysis/{target}_triage.json` — 자동 분석 결과 (7개 전부 존재)
- `firmware/analysis/cm4_all_strings.json` — 추출 문자열 (JSON 포맷, txt 대체)
- `firmware/analysis/phase1_summary.md` — 함수 목록 요약 (CSV 대체)

## Phase 2: 사운드 엔진 심층 분석 ✅
- [x] 오실레이터 타입별 처리 함수 식별 → **21종 발견** (vtable 기반, Phase 8 정정: 초기 13종 → Osc1=24, Osc2=21+9 dummy)
- [x] Plaits 코드 패턴 매칭 → **Engine 기본 클래스 4 vmethod 확인** (Init, Reset, LoadUserData, Render)
- [x] RTTI 문자열로 함수 시그니처 복구 → **7개 파라미터 enum** 확인
- [x] 프리셋 포맷 역설계 → **0xD00 바이트 커스텀 바이너리** (nanopb 아님!)
- [x] MIDI CC 매핑 → **161개 내부 CC 핸들러** 분석 (매뉴얼 공식 41 CC는 별도, Phase 8 정정: PHASE6_MIDI_CHART_v2.md)
- [x] 아날로그 VCF/VCA 제어 코드 (SPI/I2C → DAC) — Phase 9 이관 (CvCalib 클래스 발견, Phase 7)
- [x] 폴리포니 보이스 할당 로직 — Phase 9 이관 (VoiceAllocator lookup 확정, Phase 8)
- [x] 모듈레이션 매트릭스 처리 코드 — Phase 9 이관 (7×13 구조 확정, Phase 8)

### 우선 순위
1. **Plaits 패턴 매칭** → 오픈소스 코드로 함수명 복구 가능 (최고 가치)
2. **오실레이터 디스패치 테이블** → 엔진 진입점 파악
3. **VCF/VCA DAC 제어** → 아날로그 경로 이해

## Phase 3: MIDI/USB 프로토콜 분석 ✅
- [x] USB MIDI 디스크립터 파싱 → **VID=0x1C75 PID=0x0602, 4 Interfaces (Vendor/MIDI/Audio/WINUSB)**
- [x] CC 처리 함수 매핑 (CC# → 파라미터) → **161 CC 핸들러 식별** (Phase 8 정정: 매뉴얼 41 CC 정답, v2 차트 참조)
- [x] SysEx 프로토콜 리버스 → **Arturia ID 0x00 0x20 0x6B, 43-state 파서, msg_type 2-37 디스패치**
- [x] 프리셋 바이너리 포맷 구조체 역설계 → **0xD00 바이트 커스텀 바이너리 (Phase 2-5)**
- [x] MiniFreak V ↔ 하드웨어 통신 프로토콜 → **Interface #0 (Vendor-specific Bulk EP)**
- [x] SysEx 빌더 함수 3종 → **6-param(0x4003), alt(0x1003), minimal(0x03)**

### 방법론
- 바이너리 내 "Arturia", "MiniFreak", SysEx ID 문자열 검색
- MIDI CC 핸들러 테이블 탐색 (CC# = 인덱스)
- USB 패킷 캡처 (MiniFreak V 실행 시) 대조

## Phase 4: 하드웨어 인터페이스 매핑 ✅ (완료)
- [x] STM32H745 페리페럴 사용 현황 — GPIO/RCC/TIM/I2C/SAI/DMA 매핑 완료
- [x] SAI 오디오 체인 — SAI2 ChA/B → DMA2 Stream 0/4/7, 48kHz, GPIOE/GPIOD 매핑
- [x] CM4 = 페리페럴 관리자 (30개 init), CM7 = 오디오 DSP (float/NEON)
- [x] DataMemoryBarrier 멀티코어 동기화 확인
- [x] FX 코어 페리페럴 — SPI1/2/3, USART3, HSEM, DMA1/2, SAI2 매핑 완료
- [x] CM4↔FX 통신 — UART3(커맨드) + SPI(파라미터 스트림) + HSEM(동기화)
- [x] DAC/ADC 사용 패턴 분석 — CM4: DAC1(아날로그 출력), ADC1/2(센서), SAI2(I2S→codec), I2C1(디스플레이)
- [x] CvCalib 클래스 발견 — eCvKind/eVcfType enum, getCalibCutValue/getCalibVcaClickValue, 29회 호출
- [x] Voice Struct 구조 확정 — 0x118(280B)/voice, CM4→CM7 공유 메모리 버퍼
- [x] UI MCU×4 분석 — 각각 전용 ADC+SPI, AdcScan<N>, HysteresisFilter, PWM<7,5,7>
- [x] Audio Codec 칩 — 펌웨어에 칩명 없음 (HAL 래퍼만), 물리 보드 필요
- [x] 하드웨어 아키텍처 문서 완성 → notes/hardware_architecture.md
- [ ] UI MCU 통신 프로토콜 — 간접 포인터 참조로 추적 불가
- [ ] SPI 페리페럴 (CM7) — HAL 래퍼 통해 간접 접근, 물리 분석 필요

## Phase 5: 데스크톱 소프트웨어 분석 ✅ (완료)
- [x] Inno Setup 설치본 추출 (innoextract 1.9, 7,865파일, 715MB)
- [x] DLL 바이너리 분석 — PE32+ x86-64, JUCE 7.7.5, Intel IPP DSP
- [x] SysEx 프로토콜 완전 해독 — `F0 00 20 6B <DevID:02> <Type> <Group> <Data> F7`
- [x] Collage 프로토콜 발견 — Protobuf over USB Bulk, 4서비스 도메인
- [x] .mnfx 프리셋 포맷 역설계 — boost::serialization, 2,362 파라미터
- [x] XML 리소스 분석 — 2,363 내부 파라미터, SIBP, NRPN, 512 프리셋 슬롯
- [x] 펌웨어 업데이트 3경로 — DFU / Rockchip / Collage
- [x] USB 통신 구조 — libusb 직접 사용, Bulk + Control transfer
- [x] 소스 코드 구조 추정 — minifreakv/ 모듈 트리

## Phase 6: 종합 문서화 및 도구 개발 ✅ (문서 완료, 도구 미구현)
- [x] 전체 아키텍처 다이어그램 (PHASE6_ARCHITECTURE.md)
- [x] 사운드 엔진 블록 다이어그램 (PHASE6_SOUND_ENGINE.md)
- [x] MIDI Implementation Chart 완성 (PHASE6_MIDI_CHART.md — ⚠️ v1 폐기, PHASE6_MIDI_CHART_v2.md 사용)
- [x] 통신 프로토콜 문서화 (PHASE6_COMMUNICATION_PROTOCOLS.md)
- [x] 펌웨어 패치 가능성 평가 (PHASE6_FIRMWARE_PATCH_ASSESSMENT.md)
- [x] 프리셋 편집 도구 프로토타입 → Phase 8 완료 (mnfx_editor.py)
- [x] 커스텀 펌웨어 패치 가능성 평가 → Phase 8 완료 (mf_patch.py + CRC 무결성 확인)

## Phase 7: 분석 보완 ✅ (완료)
- [x] 7-1. 마스터플랜 오류 수정 (CM4/CM7 역할 정정)
- [x] 7-2. Plaits ↔ 펌웨어 Diff 분석 (phase7_plaits_diff.md)
- [x] 7-3. FX 코어 심층 분석 — 3슬롯×7서브프로세서, 11 FX 타입 매핑, SPI/UART 프로토콜
- [x] 7-4. 펌웨어 CRC/무결성 — **바이너리 내부 CRC 없음!** ZIP 컨테이너 CRC만 있음. 자유롭게 수정 가능.

## Phase 8: 도구 개발 ✅ (완료)
- [x] 8-1. 프리셋 편집 도구 — `tools/mnfx_editor.py` (CLI, byte-perfect round-trip, 512프리셋 검증)
- [x] 8-2. MIDI SysEx 커맨드라인 도구 — `tools/minifreak_sysex.py` (빌더/파서/CC맵/MIDI I/O, 10테스트 통과)
- [x] 8-3. 펌웨어 패처 — `tools/mf_patch.py` (ZIP 추출/패키징, 바이트 패턴 검색/치환, JSON 패치 정의, 백업+검증, 10테스트 통과)
- [x] 8-4. 펌웨어 대조 검증 — 펌웨어 vs 매뉴얼 v4.0.1 전면 교차 검증
  - [x] 8-4a. MIDI CC 매핑 정정 (41 CC 전면 재작성, PHASE6_MIDI_CHART_v2.md)
  - [x] 8-4b. Voice 구조 확정 (6슬롯, Para 12voice, VoiceAllocator lookup)
  - [x] 8-4c. Mod Matrix 구조 정정 (7 row × 13 column, 9 hardwired dest)
  - [x] 8-4d. 누락 기능 8영역 전부 펌웨어 존재 확인 (Granular 7종, Sample, Wavetable, Vibrato, Snapshots, Favorites, ModSeq 4lane, Arp 8+4)
  - [x] 8-4e. 명칭 정정 3项 (Envelope/CycEnv, VCF 위치, Mod Matrix destination 수)
  - [x] 8-4f. Oscillator Type enum 21종 완전 추출 (Osc1: 24, Osc2: 21+9 dummy)
  - [x] 8-4g. CM4 바이너리 58/58 항목 문자열 검증 (Arp 12, Scale 9, Chord 12, ModQuant 10, LFO 17, CycEnv 4+5, Seq 4, Spice/Dice 10, FX 13, VCF 7, Voice 7, ModMatrix 16+9)
  - [x] 8-4h. UI 바이너리 스캔 — DualTouchSlider 확인, stripped로 한계
  - [x] 8-4i. 종합 문서 — PHASE8_COMPLETE_REPORT.md, PHASE8_SEQ_ARP_MOD.md (672줄), PHASE8_MANUAL_GAP_ANALYSIS-2.md (848줄)
  - [x] 8-4j. mf_enums.py 업데이트 — VST XML + 512프리셋 교차검증, enum 역매핑 함수
- [x] 8-5. Phase 8-9 이관 항목 정리
  - CM7 DSP 심층 분석 (확률 LUT, Seq state machine, Smoothing IIR) → Phase 9
  - 아날로그 VCF/VCA 제어 코드 (SPI/I2C → DAC) → Phase 9
  - 폴리포니 보이스 할당 로직 → Phase 9
  - 모듈레이션 매트릭스 처리 코드 → Phase 9

## Phase 9: 실제 패치 시도 + 심층 분석 (하드웨어 필요)
- [ ] 9-1. DFU 덤프 (백업)
- [ ] 9-2. MIDI CC 리매핑 패치
- [ ] 9-3. 오실레이터 파라미터 패치
- [ ] 9-4. 복구 테스트
- [x] 9-5. CM7 Ghidra 심층 분석 — 확률 LUT, Seq state machine, Smoothing IIR
- [ ] 9-6. 아날로그 VCF/VCA SPI 제어 코드 추출
- [x] 9-7. Voice Allocator 분기 로직 디컴파일
- [x] 9-8. Mod Matrix dispatch 코드 분석

## Phase 10: 하드웨어 + V 매뉴얼 통합 대조 검증 ✅ (완료)
- [x] 10-1. Collage Protocol 완성 — V↔HW USB Bulk opcode 매핑
- [ ] 10-2. V Macro 3/4 (Brightness/Timbre) → HW 동작 분석
- [x] 10-3. CC#86~186 정확한 매핑 (161 CC × 145 param 매트릭스) → Phase 12-3 완료
- [x] 10-4. 미완료 High 항목 보완 → Phase 12에서 대부분 해소
- [ ] 10-5. V 전용 영역 분석 — .mnfxmidi 포맷, Sound Bank, Backup 포맷
- [ ] 10-6. 잔여 Low — Reset Out, Clock PPQ, Knob Catch, AT Curve, Touch Strip, FX Insert/Send, Spice/Dice
> **상세 계획**: `PHASE10_MANUAL_GAP_ANALYSIS.md`

## Phase 11: CM4 바이너리 직접 스캔 갭 보완 ✅ (완료)
- [x] Arp 8모드 enum 완전 식별 (CM4 0x081AEC3C)
- [x] LFO 7/9 파형 + Retrig 8모드 식별
- [x] Voice Mode 5종 + Unison 하위모드 3종 + Poly Steal 6모드
- [x] FX 13타입 enum 완전 식별
- [x] CycEnv Stage Order 3종
- [x] Mod Source 9종
- [x] 일치도 86.4% → 91.8% 상향
> **상세 리포트**: `PHASE11_GAP_FILL_ANALYSIS.md`

## Phase 12: 정적 분석 완료 + 매뉴얼 정정 권고 ✅ (완료)
- [x] 12-1. 매뉴얼 정정 권고서 — 7 정정 + 12 보강 (`MANUAL_CORRECTION_RECOMMENDATIONS.md`)
- [x] 12-2. FX 코어 13타입 × 7SP 매핑 + DSP 11함수 (`PHASE12_FX_CORE_DSP.md`)
- [x] 12-3. 161 CC × 145 param 정밀 매핑 (`PHASE12_CC_FULL_MAPPING.md`)
- [x] 12-4. Mod Matrix ~247 destination enum (`PHASE12_MOD_DEST_FULL.md`)
- [x] 12-5. Step Sequencer 64-step buffer layout (`PHASE12_SEQ_BUFFER_LAYOUT.md`)
- [x] 12-6. ★★★★★ 격상 — Vibrato/Para Env/Multi Filter/PPoly2Mono (`PHASE12_RELIABILITY_UPGRADE.md`)
- [x] 일치도 91.8% → ~96% 상향
> **실행 계획**: `PHASE12_GAP_ANALYSIS.md`

## Phase 13+: 후속 단계 (예정)
- [ ] 13. V 매뉴얼 통합 재검증 (Phase 11/12 발견사항 반영)
- [ ] 14. HW 실기 + USB 캡처 동적 검증 (Collage, 161 CC, Para voice)
- [ ] 15. 안전한 펌웨어 패치 실험 (deprecated 슬롯 활용)

---

## 키 인사이트 추적

| 발견 | 상세 | Phase |
|------|------|-------|
| Plaits 코드 포함 | Mutable Instruments Eurorack 모듈 코드 (MIT) | 2 |
| 듀얼코어 분산 | CM7=오디오 DSP(오실레이터/필터/VCA, float/NEON), CM4=페리페럴 관리자+제어(MIDI/UI/프리셋/SAI/DMA) | 4 |
| FX 전용 MCU | FX DSP 바이너리가 별도 칩에서 실행 가능성 | 1 |
| UI MCU x4 | 각 UI 모듈이 독립 MCU에서 구동 | 4 |

## 도구 체인

| 도구 | 용도 |
|------|------|
| Ghidra 12.0.4 + PyGhidra 3.0.2 | 메인 디컴파일러 |
| Hydra 스크립트 | 자동화 분석 |
| STM32CubeIDE/HAL 소스 | 페리페럴 함수 패턴 매칭 |
| Mutable Instruments Plaits 소스 | 오실레이터 코드 대조 |
| Wireshark/USBPcap | USB 프로토콜 캡처 |

---

*이 문서는 분석 진행에 따라 지속 업데이트됨*
