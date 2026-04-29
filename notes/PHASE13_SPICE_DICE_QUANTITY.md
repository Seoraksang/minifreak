# Phase 13: Spice/Dice 확률 LUT 정량 분석

**분석 날짜**: 2026-04-27  
**펌웨어**: CM7 `minifreak_main_CM7` fw4_0_1_2229, CM4 `minifreak_main_CM4` fw4_0_1_2229  
**분석 방법**: 바이너리 패턴 스캔 + VST XML 교차검증

---

## 요약

| 항목 | 매뉴얼 명시 | 펌웨어 LUT | 결과 |
|------|-----------|-----------|------|
| Walk 25/50/25 | ✅ | 하드코딩 없음 (런타임 계산) | ⚠️ 간접 증거만 |
| Mutate 75/5/5/5/5/3/2 | ✅ | 하드코딩 없음 | ⚠️ 간접 증거만 |
| Rand Oct 75/15/7/3 | ✅ | 하드코딩 없음 | ⚠️ 간접 증거만 |
| Spice 지수 분포 | 명시 없음 | ✅ CM7 float32 LUT | ✅ 구조 확인 |

---

## 1. CM7 베이스 주소 검증

| 항목 | 값 |
|------|-----|
| DFU image size (offset 0x08) | 524,096 bytes (0x7FF40) |
| Vector table offset | 0x40 |
| Initial SP | 0x20020000 (AXI SRAM) |
| Reset Vector | 0x08007F91 (Thumb mode) |
| **CM7 이미지 베이스** | **0x08000000** ✅ |
| 최대 주소 | 0x0807FFA0 |

---

## 2. Spice 지수적 확률 LUT @ `0x08067FDC`

**형식**: float32 쌍, 지수적 증가 분포  
**크기**: 32 float32 values (128 bytes)

### 상위 16 values:
| Index | float32 | 비고 |
|-------|---------|------|
| 0 | 0.000117 | |
| 1 | 0.000543 | ×4.6 |
| 2 | 0.001856 | ×3.4 |
| 3 | 0.003101 | ×1.7 |
| 4 | 0.023466 | ×7.6 (점프) |
| 5 | 0.029326 | |
| 6 | 0.141838 | ×4.8 |
| 7 | 0.478989 | |
| 8 | 0.766594 | |
| 9 | 6.257803 | ×8.2 (점프) |
| 10 | 7.289140 | |
| 11 | 37.064400 | ×5.1 |
| 12 | 124.128899 | |
| 13 | 188.263687 | |
| 14 | 1682.122314 | ×8.9 (큰 점프) |
| 15 | 1794.144409 | |

**기하평균 비율**: ~3.01 (지수적 증가 확인)  
**용도**: Spice 파라미터가 낮을 때 미세한 변화, 높을 때 큰 변화를 주는 지수적 분포

### uint8 byte pair 분석:
- Even offsets: `[167, 246, 229, 14, 16, 243, 114, 75, 239, 192, ...]` — 불규칙
- Odd offsets: `[56, 56, 57, 58, 58, 58, 59, 59, 59, 60, ...]` — **+1씩 증가** (float32 상위 바이트 = 지수 비트)

**결론**: Phase 9에서 uint8로 읽은 것은 float32의 하위/상위 바이트 분리로, 실제로는 **float32 지수 확률 분포 테이블**. 매뉴얼에 정량값 명시 없으나, 분포 형태는 지수적.

---

## 3. Walk 25/50/25 LUT — 하드코딩 없음

### 매뉴얼 명시
> Walk mode: 25% up, 50% same, 25% down

### 검색 결과

| 검색 방법 | 바이너리 | 결과 |
|-----------|---------|------|
| `[64, 128, 64]` (exact) | CM4 | 4건 — **전부 ARM Thumb2 명령어 immediate** |
| `[64, 127, 64]` (near) | CM4 | 5건 — **전부 ARM Thumb2 명령어 immediate** |
| `[63, 127, 63]` (exact) | CM7 | 1건 — Thumb2 명령어 |
| 3-value 패턴 (합=255, 25/50/25%) | CM4 | 6건 (spacing=1) |
| 3-value 패턴 (합=255, 25/50/25%) | CM7 | 11건 (spacing=1) |

### 명령어 분석 (CM4 `0x081AD9F1`)
```
40 FF 7F 00 40 FF 7F FF 7F FF 7F 00 40 FF 7F
```
- `0x40 0xFF 0x7F` = Thumb2 `MOV.W R8, #0x7F` (명령어 인코딩)
- `0x00 0x40` = Thumb2 `MOVS R0, R8`

**결론**: Walk 확률값 [64, 127, 64]는 펌웨어에 **하드코딩된 LUT로 존재하지 않음**. ARM 명령어의 immediate value로 우연히 매치됨. Walk 확률은 **런타임에 계산**되거나 **함수 내에서 상수로 직접 사용**됨.

### 간접 증거
- CM4에 "Arp Walk" 문자열 존재 @ `0x081AEC68` ✅
- mf_enums.py에 Walk mode index=4 정의 ✅
- Walk 확률 25/50/25는 매뉴얼에만 명시, 펌웨어에서는 런타임 계산으로 추정

---

## 4. Mutate 75/5/5/5/5/3/2 — 하드코딩 없음

### 검색 결과
| 검색 패턴 | CM4 | CM7 |
|-----------|-----|-----|
| `[75, 5, 5, 5, 5, 3, 2]` (raw) | 0건 | 0건 |
| `[192, 13, 13, 13, 13, 8, 5]` (u8 ×256/100) | 0건 | 0건 |

**결론**: Mutate 확률 LUT 하드코딩 없음. 런타임 계산.

### 간접 증거
- CM4에 "Arp Mutate" 문자열 @ `0x081AEC30` ✅
- VST XML에 `Arp_Mutate` 파라미터 존재 (On/Off toggle, 확률값 없음)

---

## 5. Rand Oct 75/15/7/3 — 하드코딩 없음

### 검색 결과
| 검색 패턴 | CM4 | CM7 |
|-----------|-----|-----|
| `[75, 15, 7, 3]` (raw) | 0건 | 0건 |
| `[192, 38, 18, 8]` (u8 ×256/100) | 0건 | 0건 |

**결론**: Rand Oct 확률 LUT 하드코딩 없음.

### 간접 증거
- CM4에 "Arp Rand Oct" 문자열 @ `0x081AEC20` ✅
- VST XML에 `Arp_Rand_Oct` 파라미터 존재 (On/Off toggle)

---

## 6. CM7 Env Time Scale LUT @ `0x0806D330`

**형식**: float32, 256 values  
**용도**: 엔벨로프 타임 스케일링 (Spice/Dice와 무관)

```
2.0, 1.5, 1.333, 1.0, 0.75, 0.667, 0.5, 0.375, 0.333, 0.25, ...
```
음악적 time division (whole, dotted, half, quarter, ...)

---

## 7. VST XML 교차검증

| XML 파일 | Spice/Dice 관련 파라미터 |
|----------|------------------------|
| minifreak_vst_params.xml | `Spice` (range 0~99), `Arp_Mutate` (On/Off), `Arp_Rand_Oct` (On/Off), `Arp_Ratchet` (On/Off) |
| minifreak_internal_params.xml | `Dice_Seed` (range 0~64) |
| 12_Sequencer & Arpeggiator.xml | "Spice adjusts the amount of randomization", "Dice randomizes the sequence/arpeggio" |

**VST XML에 Spice/Dice의 확률 분포 값(25/50/25 등)은 없음.** 확률은 펌웨어 소스 코드 내에 하드코딩 상수로 존재할 가능성이 높으나, 컴파일 최적화로 인해 독립 LUT가 아닌 함수 내 inline 상수로 처리됨.

---

## 8. CM4 Spice/Dice/Arp 문자열 클러스터

```
0x081AEBF0: "lots"           ← UI 표시용
0x081AEBF8: "Dice"           ← Spice/Dice 기능
0x081AEC00: "Spice"          
0x081AEC08: "Arp Repeat"     ← Arp 수식어
0x081AEC14: "Arp Ratchet"
0x081AEC20: "Arp Rand Oct"
0x081AEC30: "Arp Mutate"
0x081AEC3C: "Arp Up"         ← Arp 모드
0x081AEC44: "Arp Down"
0x081AEC50: "Arp UpDown"
0x081AEC5C: "Arp Rand"
0x081AEC68: "Arp Walk"
0x081AEC74: "Arp Pattern"
0x081AEC80: "Arp Order"
0x081AEC8C: "Arp Poly"
```

**중요**: "Dice"와 "Spice"가 Arp 수식어(Repeat/Ratchet/Rand Oct/Mutate) 바로 앞에 위치. 이는 Spice/Dice가 Arp/Seq randomization의 일부로 처리됨을 시사.

또한 `0x081B5718`: `"SpiceDice"` — 클래스/모듈명으로 확인.

---

## 결론 및 재현도 영향

### 핵심 발견
1. **Spice 지수 LUT @ `0x08067FDC`** — CM7 float32, 32 entries, 기하평균 비율 ~3.0 ✅
2. **Walk/Mutate/Rand Oct 확률값은 펌웨어에 하드코딩 LUT로 존재하지 않음** — 런타임 계산 또는 함수 내 inline 상수
3. **Phase 9에서 식별한 `0x080546C4` (Walk LUT)은 사인파 테이블** (float32 sin values) — 오류 수정 필요
4. **VST XML에도 확률 분포 값 없음** — 매뉴얼이 유일한 출처

### 재현도 영향
| 항목 | 이전 | 변경 | 사유 |
|------|------|------|------|
| Spice/Dice | 88% | **88% (변동 없음)** | LUT 구조는 확인했으나 정량값 비교 불가 |
| 종합 일치도 | 96.0% | **96.0% (변동 없음)** | Spice/Dice 가중치 3% × 0% 향상 = 0% |

### Phase 9 오류 수정
- ❌ `0x080546C4` = "Walk 8슬롯×8step" → **실제: 사인파 테이블** (float32 sin values)
- ✅ `0x08067FDC` = "지수적 확률 분포" → **확인: float32 지수 LUT (Spice 용도)**

### 권고
- Walk/Mutate/Rand Oct 확률값 추출은 **Ghidra 디컴파일로 함수 내 상수 검색**이 필요 (정적 분석)
- 또는 **JTAG 런타임 트레이싱**으로 확률 분포 실측 (Phase 14+)

---

*Phase 13-1 분석 완료: 2026-04-27*  
*LUT dump: `firmware/analysis/spice_dice_lut_dump.json`*
