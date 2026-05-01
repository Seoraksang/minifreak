# Phase 10-6: 잔여 Low 항목 CM4 바이너리 문자열 분석

**분석 대상**: `minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin` (CM4 펌웨어)  
**보조 대상**: `minifreak_ui_ribbon__fw1_0_0_2229__2025_06_18.bin` (Touch Strip)  
**검색 방법**: `strings -n 5 <binary> | grep -i <keyword>`  
**분석일**: 2026-05-01

---

## 1. Reset Out GPIO

**상태**: ⚠️ 부분 발견

| 키워드 | 발견 여부 | 검색 결과 |
|--------|----------|----------|
| reset | ✅ | `Settings are reset`, `VCA_Offset_Reset`, `Env Reset`, `Reset Settings` |
| reset_out | ❌ | 미발견 |
| PULSE | ✅ | `Short Pulse`, `PulseWidth` |
| TRIG | ✅ | `Retrig Src`, `LFO1 Retrig`, `LFO2Retrig`, `Retrig Mode`, `Slow Trig`, `Wide Trig`, `Mono Trig` |

**분석**:
- `Clock Out Type` 문자열이 존재하므로 클럭 출력 타입 설정 UI가 있음 (Reset Out 포함 가능)
- `PulseWidth`, `Short Pulse`는 클럭 리셋 펄스 관련
- `reset_out`이라는 명시적 문자열은 없으나, `Clock Out Type`의 enum 값들(예: Clock/Reset/Gate/Run)은 리버스 엔지니어링으로 확인 필요
- `Retrig` 계열은 LFO 리트리거이므로 Reset Out GPIO와는 별개

---

## 2. Clock PPQ

**상태**: ✅ 발견

| 키워드 | 발견 여부 | 검색 결과 |
|--------|----------|----------|
| PPQ | ✅ | `24PPQ`, `48PPQ` |
| CLK | ✅ | `ClkHandler` (함수명) |
| clock_div | ❌ | 미발견 |
| clock | ✅ | `Ext. Clock`, `Clocks Send`, `Clock Out Type`, `Clock In Type`, `Clock Source` |

**분석**:
- PPQ 해상도: 24PPQ, 48PPQ (2가지 모드 지원)
- 클럭 소스: `Ext. Clock`, `Clock Source`
- 클럭 입출력 타입: `Clock Out Type`, `Clock In Type`
- `Clocks Send`: 클럭 전송 설정
- `clock_div`라는 명시적 문자열 없음 — 내부 변수명일 가능성

---

## 3. Knob Catch

**상태**: ✅ 발견

| 키워드 | 발견 여부 | 검색 결과 |
|--------|----------|----------|
| catch | ✅ | `Knob Catch` (UI 레이블), 이스터에그 텍스트 |
| knob | ✅ | `Knob Panel`, `Knob Catch`, `Knob Send CC` |
| Jump | ❌ | 미발견 (Catch 모드의 반대값) |
| Hook | ❌ | 미발견 |
| Scale | ✅ | `Scale`, `Global Scale`, `Scale Config` 등 (음계 관련) |

**분석**:
- `Knob Catch`가 명시적 UI 레이블로 존재
- `Jump` (Catch off) 값은 enum 내부값일 가능성 — 바이너리에서는 UI 표시 문자열만 남음
- `Knob Panel`: 노브 패널 설정
- `Knob Send CC`: 노브 CC 전송 설정

---

## 4. AT Curve (Aftertouch Curve)

**상태**: ✅ 발견

| 키워드 | 발견 여부 | 검색 결과 |
|--------|----------|----------|
| aftertouch | ✅ | `Aftertouch`, `Aftertouch Curve` |
| AT_ | ❌ | 미발견 (내부 접두사) |
| at_sens | ❌ | 미발견 |
| AT Sens | ❌ | 미발견 (그러나 관련 항목 있음) |
| AT curve | ❌ | 미발견 (대소문자 차이) |

**관련 발견 항목**:
- `Aftertouch` — AT 소스로 존재 (`Velo/AT`, `Velo + AT`, `Matrix Src VeloAT`)
- `Aftertouch Curve` — AT 커브 UI 레이블
- `AT End Sens` — AT 종료 감도
- `AT Start Sens` — AT 시작 감도
- `Touch Button Sens` — 터치 버튼 감도 (관련)

**분석**:
- AT Curve는 `Aftertouch Curve`로 확실히 존재
- 감도 파라미터: `AT End Sens`, `AT Start Sens` (시작/종료 감도 분리)
- 커브 타입 (Linear, Exponential Square, S Curve)은 Velocity Curve와 공유 가능

---

## 5. FX Insert/Send

**상태**: ✅ 발견 (부분)

| 키워드 | 발견 여부 | 검색 결과 |
|--------|----------|----------|
| fx_send | ❌ | 미발견 |
| fx_insert | ❌ | 미발견 |
| dry_wet | ❌ | 미발견 |
| send_level | ❌ | 미발견 (그러나 `Send Level` 존재) |
| insert | ✅ | `Insert` |
| send | ✅ | `Send Level`, `Clocks Send`, `Transport Send`, `Knob Send CC` |

**관련 발견 항목**:
- `Delay Routing` — 딜레이 라우팅
- `Reverb Routing` — 리버브 라우팅
- `old FX3 Routing` — 구버전 FX3 라우팅 (레거시)
- `Matrix Routing` — 매트릭스 라우팅

**분석**:
- `Send Level`이 존재하므로 FX Send 레벨 제어 있음
- `Insert` 문자열 존재 — FX 인서트 모드 관련
- `dry_wet` 내부 변수명은 미발견 — UI에 노출되지 않는 파라미터
- `Delay Routing`, `Reverb Routing`이 FX 라우팅(Insert/Send)을 담당하는 것으로 추정

---

## 6. Scale / Chord / ModQuant

**상태**: ✅ 발견

| 키워드 | 발견 여부 | 검색 결과 |
|--------|----------|----------|
| quantize | ❌ | 미발견 (Mod Quant 내부명) |
| pentatonic | ✅ | `Pentatonic`, `Minor Penta`, `Major Penta` |
| blues | ✅ | `Blues` |
| dorian | ✅ | `Dorian` |
| chord | ✅ | `Chorder`, `Chords`, `Chord En`, `Chord Length`, `Chord Strum`, `Chord Vel>Notes`, `Chord Offset` |
| scale | ✅ | `Scale`, `Global Scale`, `User Scale`, `Scale Config`, `Scaler`, `Global Scale Edit`, `User Scale Edit`, `User Scale Note` |

**발견된 음계 목록**:
- `Major`, `Minor`, `Dorian`, `Mixolydian`, `Blues`, `Pentatonic`
- `Chromatic`, `Phrygian Dom`, `Minor 9th`, `Major 9th`
- `Minor Penta`, `Major Penta`

**분석**:
- 12종 이상의 프리셋 음계 + User Scale 지원
- Chorder 기능 풍부: Enable, Length, Strum, Vel>Notes, Offset
- `quantize` 문자열 없음 — UI에서는 `Scale` 또는 `Scaler`로 표시

---

## 7. MIDI Routing

**상태**: ✅ 발견 (부분)

| 키워드 | 발견 여부 | 검색 결과 |
|--------|----------|----------|
| local | ✅ | `Local Control` |
| routing | ✅ | `Matrix Routing`, `Delay Routing`, `Reverb Routing`, `old FX3 Routing` |
| local_on | ❌ | 미발견 (내부 변수명) |
| midi_to | ❌ | 미발견 |

**분석**:
- `Local Control`이 MIDI 로컬 온/오프 기능
- `routing` 계열은 주로 FX 라우팅에 사용됨 (Delay/Reverb)
- `midi_to` 등 MIDI 라우팅 관련 명시적 문자열 없음
- MIDI 라우팅은 `MNF_KeyRouter` 클래스(심볼)로 구현될 가능성

---

## 8. Velocity Curve

**상태**: ✅ 발견

| 키워드 | 발견 여부 | 검색 결과 |
|--------|----------|----------|
| velocity | ✅ | `Velocity`, `Velocity Curve`, `Lowest Velo` |
| vel_curve | ❌ | 미발견 (내부 변수명) |
| vel_response | ❌ | 미발견 |
| linear | ✅ | `Linear` |
| logarithm | ❌ | 미발견 |

**관련 커브 타입 문자열** (여러 커브에서 공유):
- `Linear`
- `Exponential Square`
- `S Curve`

**관련 Velocity 파라미터**:
- `Velo > Env Amnt`, `Velo > VCA`, `Velo > Env`, `Velo > Time`, `Velo > VCF`
- `Chord Vel>Notes`
- `Lowest Velo`
- `Matrix Src VeloAT`

**분석**:
- `Velocity Curve` UI 레이블 확실히 존재
- 커브 타입: Linear, Exponential Square, S Curve (3종)
- Velocity가 Matrix 소스 및 다양한 엔벨로프/필터 모듈레이션 대상으로 사용됨

---

## 9. Audio In Mode

**상태**: ✅ 발견

| 키워드 | 발견 여부 | 검색 결과 |
|--------|----------|----------|
| audio_in | ❌ | 미발견 (내부 변수명) |
| line | ❌ | ` at line ` (에러 메시지, 관련 없음) |
| mic | ❌ | `Rhythmic 1~4` (일부 매칭, 관련 없음) |
| Audio In | ✅ | `Audio In`, `No Audio In` |
| input_mode | ❌ | 미발견 (그러나 `Input Mode` 존재) |
| gain | ✅ | `Input Gain` |

**관련 발견 항목**:
- `Audio In`, `No Audio In` — 오디오 입력 활성화/비활성화
- `Input Mode` — 입력 모드 선택
- `Input Gain` — 입력 게인
- `Input Channel` — 입력 채널
- `AUDIO Config`, `AUDIO Interface` — 오디오 설정

**분석**:
- Audio In 기능이 완전히 구현되어 있음
- `Input Mode`, `Input Gain`, `Input Channel` 3개 파라미터로 구성
- 실제 모드 값(Line/Mic 등)은 enum 내부값으로 확인 필요

---

## 10. Touch Strip (ui_ribbon 바이너리)

**상태**: ❌ 미발견 (ui_ribbon 바이너리) / ⚠️ 부분 (CM4)

| 키워드 | ui_ribbon | CM4 |
|--------|-----------|-----|
| mode | ❌ | — |
| touch | ❌ | `Touch Button Sens` |
| strip | ❌ | — |
| ribbon | ❌ | — |
| pitch | ❌ | `Pitch Wheel`, `Bend Range` |
| mod | ❌ | `Mod Wheel` |

**ui_ribbon 바이너리 분석**:
- 파일 크기: 69,232 bytes (매우 작음)
- 최소 길이 3 이상 문자열: 2,782개 (대부분 ARM 명령어 아티팩트)
- **읽을 수 있는 문자열이 전혀 없음** — 순수 펌웨어/부트로더일 가능성
- Touch Strip 모드 관련 문자열은 CM4 메인 펌웨어에 있을 가능성 높음

**CM4에서 관련 발견**:
- `Mod Wheel`, `Pitch Wheel` — 휠 컨트롤러
- `Bend Range` — 피치 벤드 범위
- `Touch Button Sens` — 터치 버튼 감도
- `MNF_WheelsController` 클래스 — 휠/스트립 컨트롤러 클래스

**분석**:
- Touch Strip 모드(Pitch Bend / Mod Wheel / CC 등)는 CM4 메인 펌웨어에서 처리
- ui_ribbon은 하드웨어 터치 감지만 담당 (문자열 없는 것으로 보아)
- 명시적 "strip mode" 문자열 없음 — `MNF_WheelsController` 클래스 분석 필요

---

## 요약표

| # | 항목 | 상태 | 핵심 발견 |
|---|------|------|----------|
| 1 | Reset Out GPIO | ⚠️ 부분 | `Clock Out Type`, `PulseWidth` 존재. reset_out 명칭 없음 |
| 2 | Clock PPQ | ✅ | `24PPQ`, `48PPQ`, `Clock Out/In Type`, `Clock Source` |
| 3 | Knob Catch | ✅ | `Knob Catch` UI 레이블. Jump/Hook 값은 enum 내부 |
| 4 | AT Curve | ✅ | `Aftertouch Curve`, `AT End Sens`, `AT Start Sens` |
| 5 | FX Insert/Send | ✅ | `Send Level`, `Insert`, `Delay/Reverb Routing` |
| 6 | Scale/Chord | ✅ | 12+ 음계, Chorder (6개 파라미터), User Scale |
| 7 | MIDI Routing | ⚠️ 부분 | `Local Control` 존재. 상세 MIDI 라우팅 문자열 없음 |
| 8 | Velocity Curve | ✅ | `Velocity Curve`, Linear/Exponential Square/S Curve |
| 9 | Audio In Mode | ✅ | `Input Mode`, `Input Gain`, `Input Channel` |
| 10 | Touch Strip | ❌/⚠️ | ui_ribbon에 문자열 없음. CM4에 `Mod Wheel`, `Pitch Wheel` |

## 다음 단계 제안

1. **Ghidra 분석**: `Clock Out Type` enum 분석 → Reset Out GPIO 핀맵 확인
2. **MNF_WheelsController**: Touch Strip 모드 처리 로직 분석
3. **Delay/Reverb Routing**: FX Insert/Send 라우팅 구조 분석
4. **MNF_KeyRouter**: MIDI 라우팅 내부 구조 분석
5. **Enum 역추적**: Jump/Hook, Line/Mic, On/Off 등 UI에 노출되지 않는 enum 값 확인
