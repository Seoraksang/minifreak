# Phase 15: 안전한 펌웨어 패치 실험

## 개요
Phase 14까지의 정적 분석 결과를 바탕으로, 실제 펌웨어 바이너리에 안전한 패치를 적용하고 검증하는 실험 단계.

**펌웨어**: fw4_0_1_2229 (CM4, CM7, FX)
**위험도**: LOW_RISK — .rodata 문자열만 변경, 코드 로직 불변
**가역성**: 완전 — apply → revert → 바이너리 SHA 일치 확인

## Phase 15-1: Deprecated 슬롯 식별 + 오디오 라우팅 분석

### eEditParams Deprecated 슬롯
`tools/phase15_audio_routing.py`로 CM4 펌웨어를 스캔한 결과:

| 항목 | Flash 주소 | 내용 |
|------|-----------|------|
| DEPRECATED | `0x081AF994` | `UnisonOn TO BE DEPRECATED` — 더 이상 사용 안 함 |
| Obsolete | `0x081AFB00` | `obsolete Rec Count-In` — 제거된 기능 |
| VST_IsConnected | `0x081AFB28` | 프리셋 미저장 플래그 문자열 |

### 이스터에그 문자열 (디버그 전용)
| 항목 | Flash 주소 | 원본 |
|------|-----------|------|
| Olivier D | `0x081B34A0` | `if you ask Olivier D, he'll tell you...` |
| Thomas A | `0x081B32CD` | `Ask Thomas A` |
| Mathieu B | `0x081B3411` | `ask Mathieu B` |
| Frederic | `0x081B2F2C` | `Hey Frederic, are you ready to hear...` |

### CM7→FX 오디오 라우팅
- CM4 HSEM (Hardware Semaphore): 35개 핸들
- CM7 AXI SRAM: 16개 참조
- FX DMA: SAI→I2S 라우팅 경로 확인
- **상세 분석**: `tools/phase15_audio_routing.py` 출력 참조

## Phase 15-2: 안전한 패치 정의 + 테스트

### 패치 정의 (`tools/patches/phase15_safe_patches.json`)

| # | 이름 | 원본 | 치환 | 길이 | 카테고리 |
|---|------|------|------|------|----------|
| 1 | deprecated-string | `UnisonOn TO BE DEPRECATED` | `HYDRA_FA TO BE DEPRECATED` | 25B | string_constant |
| 2 | obsolete-string | `obsolete Rec Count-In` | `HYDRA_FA Rec Count-In` | 21B | string_constant |
| 3 | easter-egg-olivier | `if you ask Olivier D` | `if you ask Hermes AG` | 20B | easter_egg |
| 4 | easter-egg-thomas | `Ask Thomas A` | `Ask Hermes H` | 12B | easter_egg |
| 5 | easter-egg-mathieu | `ask Mathieu B` | `ask Hermes HH` | 13B | easter_egg |
| 6 | easter-egg-frederic | `Hey Frederic` | `Hey Hermes H` | 12B | easter_egg |
| 7 | vst-connected | `VST_IsConnected` | `HYD_IsConnected` | 15B | string_constant |

### 테스트 결과 (`tools/phase15_patch_test.py`)

```
테스트 1: 패치 정의 JSON 로드         ✅ 7개 전부 validate 통과
테스트 2: 바이너리 패턴 매치          ✅ CM4 대상 전부 1 match
테스트 3: 패치 적용/롤백              ✅ 7/7 성공, 0 실패
테스트 4: 가역성 (apply→revert→compare) ✅ 전체 바이너리 원본 복원
테스트 5: JSON round-trip             ✅ 직렬화/역직렬화 무결성
```

### mf_patch.py 확장
- `open_standalone_bin()` 함수 추가: .mnf 패키지 없이 개별 .bin 파일을 `FirmwarePackage`로 열 수 있음
- 테스트 목적으로 사용, 실제 플래싱은 .mnf 패키지 경로 필요

## Phase 15-3: 실제 플래싱 테스트 (준비 완료)

### 전제 조건
1. [ ] MiniFreak 하드웨어 + USB 연결
2. [ ] DFU 모드 진입 가능
3. [ ] `.mnf` 펌웨어 패키지 준비 (현재 개별 .bin만 보유)
4. [ ] Arturia MIDI Control Center 또는 dfu-util

### 실행 계획
1. `.mnf` 패키지에 패치 적용 (`mf_patch.py open <file.mnf>`)
2. 패치된 `.mnf`로 플래싱
3. 하드웨어 부팅 확인
4. 이스터에그/문자열 변경 확인 (디버그 로그 또는 MIDI sysex)
5. 모든 기능 정상 동작 확인
6. 원본 `.mnf`로 롤백

## 파일 목록

| 파일 | 설명 |
|------|------|
| `tools/patches/phase15_safe_patches.json` | 패치 정의 (7개) |
| `tools/phase15_patch_test.py` | 패치 테스트 스크립트 |
| `tools/phase15_audio_routing.py` | CM7→FX 라우팅 분석 스크립트 |
| `tools/mf_patch.py` | 펌웨어 패치 프레임워크 (open_standalone_bin 추가) |

## 교차 참조
- Phase 6 펌웨어 패치 평가 → `PHASE6_FIRMWARE_PATCH_ASSESSMENT.md`
- Phase 8 eEditParams enum → `PHASE8_ESYNTHPARAMS_ENUM.md`
- Phase 14 파라미터 매핑 → `PHASE14_VST_HW_PARAM_MAPPING.md`
- mf_patch.py 설계 → `tools/mf_patch.py` (CLI: `open`, `patch`, `info`, `export`, `revert`)
