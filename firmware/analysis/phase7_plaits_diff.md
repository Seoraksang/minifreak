# Phase 7-2: Plaits ↔ MiniFreak CM7 비교 분석

> **분석 날짜**: 2026-04-25
> **상태**: 부분 완료 — 소스 분석 완료, 바이너리 매칭 제한적

---

## 1. Plaits 소스코드 분석 완료

`phase7_plaits_source_map.md`에 589줄 상세 분석 완료:
- **Base Engine vtable**: 5 슬롯 (dtor + Init/Reset/LoadUserData/Render)
- **24개 엔진 등록** (engine/ 16개 + engine2/ 6개 + 드럼 3개)
- **EngineParameters**: 24바이트 (trigger, note, timbre, morph, harmonics, accent)
- **PostProcessingSettings**: 12바이트 (out_gain, aux_gain, already_enveloped)

### MiniFreak에 사용된 것으로 추정되는 엔진 (13종)

| # | Plaits Engine | MiniFreak 오실레이터 | out_gain | aux_gain | 확신도 |
|---|--------------|---------------------|----------|----------|--------|
| 0 | VirtualAnalogVCFEngine (engine2) | Virtual Analog | 1.0 | 1.0 | ★★★★★ |
| 1 | PhaseDistortionEngine (engine2) | Phase Distortion | 0.7 | 0.7 | ★★★★★ |
| 2-4 | SixOpEngine ×3 (engine2) | FM (3변형) | 1.0 | 1.0 | ★★★★★ |
| 5 | WaveTerrainEngine (engine2) | Wave Terrain | 0.7 | 0.7 | ★★★★☆ |
| 6 | StringMachineEngine (engine2) | String Machine | 0.8 | 0.8 | ★★★★☆ |
| 7 | ChiptuneEngine (engine2) | Chiptune | 0.5 | 0.5 | ★★★★☆ |
| 8 | VirtualAnalogEngine | — (VCF로 대체?) | 0.8 | 0.8 | ★★★☆☆ |
| 9 | WaveshapingEngine | Waveshaping | 0.7 | 0.6 | ★★★★☆ |
| 10 | FMEngine | — (SixOp로 대체?) | 0.6 | 0.6 | ★★★☆☆ |
| 11 | GrainEngine | Grain | 0.7 | 0.6 | ★★★★☆ |
| 12 | AdditiveEngine | Additive | 0.8 | 0.8 | ★★★★☆ |
| 13 | WavetableEngine | Wavetable | 0.6 | 0.6 | ★★★★☆ |
| 14 | ChordEngine | Chord | 0.8 | 0.8 | ★★★★☆ |
| 15 | SpeechEngine | Speech | -0.7 | 0.8 | ★★★★☆ |
| 16 | SwarmEngine | Swarm | -3.0 | 1.0 | ★★★★★ |
| 17 | NoiseEngine | Noise | -1.0 | -1.0 | ★★★★☆ |
| 18 | ParticleEngine | Particle | -2.0 | 1.0 | ★★★★☆ |
| 19 | StringEngine | — (StringMachine으로 대체?) | -1.0 | 0.8 | ★★★☆☆ |
| 20 | ModalEngine | Modal | -1.0 | 0.8 | ★★★★☆ |
| 21-23 | Drum Engines ×3 | ❌ 미사용 (드럼 없음) | 0.8 | 0.8 | ★★★★★ |

> **참고**: MiniFreak에는 드럼 엔진이 없고(순수 신디사이저), engine2의 새로운 엔진들을 사용. 기존 engine/의 일부는 대체됨.

---

## 2. CM7 바이너리 서치 결과

### 2.1 바이너리 특성
- **완전 스트립** — C++ RTTI 심볼 없음 (CM4와 차이)
- **문자열 최소화** — 시스템 에러 메시지만 존재 (FreeRTOS, errno)
- **이름 없는 함수** — 모든 함수가 `FUN_xxxxxxxx`
- **nameof 라이브러리 사용** — enum→문자열 변환용이지만, 컴파일 타임에 상수로 폴딩됨

### 2.2 발견된 Plaits 관련 상수

| 상수 | 주소 | 설명 |
|------|------|------|
| `48000.0` | 0x56E68 | kSampleRate — Plaits 기본 샘플레이트 |
| `32768.0` | 0x56E80 | Q15 고정소수점 스케일 팩터 |
| `440.0` | 0x42E7C | A4 튜닝 기준 (MIDI note 69) |
| `0.6667` | 0x42E78 | 2/3 — 엔진 파라미터 계수 |
| `32.0` | 0x56E70 | 블록 사이즈 또는 버퍼 크기 |
| `-0.5035` | 0x56E60 | 필터 계수 (biquad?) |

### 2.3 발견되지 않은 것
| 대상 | 원인 |
|------|------|
| PostProcessingSettings 테이블 | Arturia가 구조체를 수정했거나, 코드 내에 상수로 인라인 |
| Sine LUT | stmlib 라이브러리가 아닌 자체 수학 라이브러리 사용 가능 |
| Formant 주파수 테이블 | Speech 엔진이 수정되었거나 상수 분리 |
| Diffuser 지연 라인 크기 | Particle 엔진이 완전히 재작성되었을 가능성 |
| 엔진 클래스 이름 문자열 | nameof는 컴파일 타임 상수라 런타임에 문자열 없음 |

### 2.4 `48000.0` 컨텍스트 분석
```
0x56E60: -0.503527     ← 필터 계수 (DC blocking?)
0x56E64:  1.360000     ← 게인/스케일
0x56E68: 48000.000     ← kSampleRate
0x56E6C:  0.000183     ← 1/5461 ≈ 오디오 버퍼 관련
0x56E70: 32.000000     ← 버퍼 크기 (32 samples = 0.67ms @ 48kHz)
0x56E74: 0x0806D558    ← 코드 포인터 (Thumb-2, even)
0x56E78:  0.000244     ← 1/4096 ≈ 파라미터 해상도
0x56E7C:  0.000021     ← 작은 상수 (노이즈 플로어?)
0x56E80: 32768.000     ← Q15 스케일
```

### 2.5 `440.0` 컨텍스트 분석
```
0x42E74: 0x01010001    ← 구조체/플래그 (1, 1, 0, 1 패턴)
0x42E78:  0.666667     ← 2/3
0x42E7C: 440.000000    ← A4 튜닝 기준
0x42E80:  0.004583     ← 1/218 ≈ MIDI note-to-freq 변환 계수
0x42E84: 0x30800000    ← 코드/데이터
0x42E88:  0.050000     ← 1/20 = LFO 최소 레이트?
0x42E8C:  0.006667     ← 1/150
0x42E90:  0.032784     ← ≈ 1/30.5
0x42E94:  0.451000     ← 특정 파라미터 기본값
```

---

## 3. 결론

### Arturia의 Plaits 포크 분석
1. **코드는 포크했지만 상당히 수정** — PostProcessingSettings 구조체, 엔진 등록 테이블, 상수 배열 모두 재배치됨
2. **컴파일러 최적화가 공격적** — 상수가 인라인되고, 구조체가 분해됨 (GCC -O2/-O3)
3. **엔진 추가/삭제** — 드럼 엔진 3개 제거, engine2의 새 엔진 7개 추가
4. **샘플레이트 동일** — 48kHz는 Plaits와 동일
5. **440Hz 튜닝 유지** — 표준 A4 튜닝

### 바이너리에서 엔진 식별 방법
직접적인 상수 매칭은 어려우나, **Ghidra를 통한 함수 레벨 분석**으로 식별 가능:
1. **vtable 기반**: 이전 Phase 2에서 13개 vtable을 이미 식별
2. **함수 크기/복잡도**: SixOp(가장 큼) vs Chiptune(작음) 등
3. **하위 함수 호출 패턴**: FM 엔진은 operator 함수 호출, Speech는 LPC 함수 호출 등
4. **상수 참조**: 440.0, 48000.0, 32768.0을 참조하는 함수 그룹

### 다음 단계
- Ghidra에서 CM7 함수들을 Plaits 소스의 `Render()` 함수들과 **수동으로 매칭**
- 각 엔진의 `Render()` 함수 특징 (루프 구조, 하위 함수 호출)을 바이너리에서 찾기
- 특히 **SixOpEngine**(가장 복잡)과 **SwarmEngine**(unique gain=-3.0)부터 우선

---

## 4. 산출물

| 파일 | 내용 |
|------|------|
| `phase7_plaits_source_map.md` | Plaits 소스 전체 엔진 분석 (589줄, 28KB) |
| `phase7_plaits_diff.md` | 본 문서 — 소스↔바이너리 비교 결과 |
