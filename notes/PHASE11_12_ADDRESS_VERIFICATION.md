# 펌웨어 주소 검증 결과: Phase 11/12 vs CM4 바이너리

**검증 날짜**: 2026-04-26  
**펌웨어**: `minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin`  
**바이너리 크기**: 620,224 bytes (605.7 KB) ✅ (문서 표기 620KB와 일치)  
**포맷**: ARM Cortex-M4 Thumb-2 ✅ (Vector table: SP=0x0000AB80, Reset=0x00000000)  
**FX 바이너리**: 122,640 bytes (119.8 KB) ✅ (문서 표기 122KB와 일치)

**베이스 주소**: `0x08120000` (문서 주소 - 파일 오프셋 = 0x08120000)

---

## 요약: 전체 검증 결과

| # | 검증 항목 | 주소 | 결과 | 불일치 내용 |
|---|----------|------|------|------------|
| 1 | Arp Mode enum | 0x081AEC3C~8C | ⚠️ 부분 불일치 | index 2: "Arp Up" 아님, "Arp UpDown"임 |
| 2 | LFO Waveform enum | 0x081B0FB0~D4 | ⚠️ 부분 불일치 | 7/9만 해당 영역; Saw/SnH는 별도 주소 |
| 3 | LFO Retrig modes | 0x081B0E3C~88 | ✅ 전부 일치 | 8/8 모드 정확 |
| 4 | Voice Mode | 0x081AF500~28 | ✅ 전부 일치 | 5개 문자열 전부 정확 |
| 5 | Poly Steal Mode | 0x081B0F70~A4 | ✅ 전부 일치 | 6/6 전부 정확 |
| 6 | FX 13 type enum | 0x081AF308~7C | ✅ 전부 일치 | 13/13 전부 정확 |
| 7 | Shaper presets | 0x081AF128~88 | ⚠️ 부분 불일치 | 첫 항목 "Shaper"가 아닌 "Preset Shaper"; 25개 발견 |
| 8 | CycEnv parameters | 0x081AF840~80 | ✅ 전부 일치 | 7개 전부 정확 |
| 9 | Mod Matrix sources | 0x081B1BCC~1C | ✅ 전부 일치 | 9/9 전부 정확 |
| 10 | Custom Assign dest | 0x081AEA94 | ⚠️ 주소 불일치 | 실제 Mod Matrix dest는 0x081AEAA4부터 |
| 11 | Tempo subdivisions | 0x081AF0B4~FC | ⚠️ 부분 불일치 | 10개만 해당 범위; 11번째 "1/32T"는 0x081AF0FC에 존재 |
| 12 | Multi Filter 14 modes | 0x081B0D90~E8 | ✅ 전부 일치 | 14/14 전부 정확 |
| 13 | Poly2Mono | 0x081AE128 | ✅ 일치 | 정확 |
| 14 | Multi Filter ptr table | 0x081B1850 | ❌ 불일치 | 해당 영역은 scale names + filter modes 혼합, 순수 14개 포인터 테이블 아님 |

---

## 상세 불일치 분석

### 1. Arp Mode index 2 — "Arp Up" vs "Arp UpDown"

**문서 주장** (Phase 11):
> `0x081AEC50` = `Arp Up` (UpDown 모드에 "Up 재사용")

**실제 바이너리**:
> `0x081AEC50` = **`Arp UpDown`**

**영향**: 문서가 "Arp Up"이 UpDown 모드에 재사용된다고 주장했으나, 실제로는 **독립적인 "Arp UpDown" 문자열**이 존재. 즉 Arp enum은 8개 모드 전부 고유 문자열을 가짐.

| 인덱스 | 문서 주장 | 실제 |
|--------|----------|------|
| 0 | Arp Up | Arp Up ✅ |
| 1 | Arp Down | Arp Down ✅ |
| 2 | **Arp Up** (재사용) | **Arp UpDown** ❌ |
| 3 | Arp Rand | Arp Rand ✅ |
| 4 | Arp Walk | Arp Walk ✅ |
| 5 | Arp Pattern | Arp Pattern ✅ |
| 6 | Arp Order | Arp Order ✅ |
| 7 | Arp Poly | Arp Poly ✅ |

### 2. LFO Waveform — Saw/SnH 위치

**문서 주장** (Phase 11):
> 7개 파형이 0x081B0FB0~0x081B0FDB에 존재; Saw와 SnH는 "공유"됨

**실제 바이너리**:
- 0x081B0FB0~0x081B0FDB에 **7개 파형** (Sin, Tri, Sqr, SlewSNH, ExpSaw, ExpRamp, Shaper) ✅
- `Saw` 독립 문자열: **0x081B0DF4** (Multi Filter 영역 바로 뒤)
- `SnH` 독립 문자열: **0x081B0B24** (Sync Filter 영역)
- LFO Waveform enum은 **포인터 테이블** 방식 (9개 포인터가 각각 다른 주소의 문자열을 참조)
- 바이너리에서 포인터 테이블의 정확한 위치는 확인되지 않음 (여러 후보 존재하나 명확한 9-연속 포인터 시퀀스 미발견)

**결론**: Saw/SnH가 "공유"된다는 문서 설명은 **부분적으로 정확**하나, 실제 독립 문자열이 존재함.

### 3. Shaper Preset 첫 항목 및 총수

**문서 주장** (Phase 11):
> 20개 프리셋 (12 빌트인 + 8 사용자), 첫 항목 = "Shaper"

**실제 바이너리**:
> 첫 항목 = **"Preset Shaper"** (0x081AF128)
> 총 **25개** 항목 (0x081AF128~0x081AF295):
> - "Preset Shaper", Asymmetrical Saw, Unipolar Cosine, Short Pulse, Exponential Square, Decaying Decays, Wobbly, Strum Envelope, Triangle Bounces (9 빌트인)
> - Rhythmic 1~4 (4), Stepped 1~4 (4) = 8개 추가
> - User Shaper 1~8 (8)
> - **합계: 9 + 8 + 8 = 25개**

문서는 "12 빌트인 + 8 사용자 = 20개"라고 했으나, 실제는 17 빌트인 + 8 사용자 = 25개. 첫 항목 이름도 "Shaper"가 아닌 "Preset Shaper".

### 4. Custom Assign Destinations 주소

**문서 주장**: `0x081AEA94` 부근

**실제**: Mod Matrix Custom Assign 목적지 문자열은 **`0x081AEAA4`** ("-Empty-")부터 시작. `0x081AEA94` 영역에는 의미 있는 문자열 없음.

### 5. Tempo Subdivisions 개수

**문서 주장**: 11종 (1/4, 1/8D, 1/4T, 1/8, 1/16D, 1/8T, 1/16, 1/32D, 1/16T, 1/32, 1/32T)

**실제**: 0x081AF0B4~0x081AF0F8 범위에 **10개** (1/4 ~ 1/32). **"1/32T"**는 0x081AF0FC에 존재하므로 총 11개는 맞음. 단 0x081AF0FC는 문서 표기 범위(0x081AF0B4~FC)의 끝점에 해당.

### 6. Multi Filter Pointer Table

**문서 주장**: `0x081B1850`~`0x081B188C`에 14개 필터 모드 포인터

**실제**: 0x081B1850 영역은 **scale names (Global, Major, Minor, Dorian 등)**과 filter modes가 혼합된 포인터 배열. LP36~LP12의 3개 연속 포인터만 0x081B187C에서 확인. 순수 14-엔트리 필터 포인터 테이블은 **해당 주소에 존재하지 않음**.

### 7. Percussive 주소 (Phase 12)

**문서 주장**: `0x081AEBA4` = "Percussive"

**실제**: "Percussive"는 **`0x081AEBAC`**에 위치. 문서와 8바이트 오프셋 차이.

---

## ✅ 정확히 확인된 항목 (불일치 없음)

| 항목 | 주소 범위 | 검증 수 |
|------|----------|---------|
| LFO Retrig 8 modes | 0x081B0E3C~88 | 8/8 ✅ |
| Voice Mode 5 strings | 0x081AF500~28 | 5/5 ✅ |
| Poly Steal Mode 6 types | 0x081B0F70~A4 | 6/6 ✅ |
| FX Type 13 strings | 0x081AF308~7C | 13/13 ✅ |
| CycEnv 7 parameters | 0x081AF840~80 | 7/7 ✅ |
| Mod Matrix 9 sources | 0x081B1BCC~1C | 9/9 ✅ |
| Multi Filter 14 modes | 0x081B0D90~E8 | 14/14 ✅ |
| Poly2Mono | 0x081AE128 | 1/1 ✅ |
| Vibrato 6 strings | 여러 주소 | 6/6 ✅ |
| Voice Envelope 9 params | 0x081AF7E0~34 | 9/9 ✅ |
| VCF 7 modes | 0x081AF4D0~EC | 7/7 ✅ |
| LFO eEditParams 8 items | 0x081AF88C~F8 | 8/8 ✅ |
| Deprecated 4 params | 여러 주소 | 4/4 ✅ |
| Smooth Mod 4 lanes | 0x081B1B8C~BC | 4/4 ✅ |
| Shaper Rate 2 params | 0x081AF544, 554 | 2/2 ✅ |
| Tempo triplet subs 6종 | 0x081AF564~8C | 6/6 ✅ |
| Sustain string | 0x081AEBB8 | 1/1 ✅ |

**총 검증 문자열**: ~130개  
**정확 일치**: ~120개 (92%)  
**불일치/수정 필요**: ~10개 (8%)

---

## 결론

Phase 11/12 문서의 주소 검증은 **대체로 정확**하며, 주요 enum 문자열들의 주소와 내용이 실제 바이너리와 일치. 

**주요 수정 필요 사항**:
1. **Arp index 2**: "Arp Up" 재사용 → **"Arp UpDown" 독립 문자열**로 수정
2. **Shaper 프리셋**: 20개 → **25개** (첫 항목 = "Preset Shaper")
3. **Multi Filter 포인터 테이블 주소**: 0x081B1850 → **해당 주소에 존재하지 않음** (scale names 혼합)
4. **Percussive 주소**: 0x081AEBA4 → **0x081AEBAC**로 수정
5. **Custom Assign 시작 주소**: 0x081AEA94 → **0x081AEAA4**로 수정

---

*검증 도구: `tools/verify_phase11_12_addresses.py`*
*펌웨어 버전: fw4_0_1_2229 (2025-06-18)*
