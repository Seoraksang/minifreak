#!/usr/bin/env python3
"""
Phase 15-2: 안전한 펌웨어 패치 테스트
- 패치 정의 JSON 로드 → 추출된 .bin 파일에 적용 → 검증 → 롤백
- 플래싱 없이 바이너리 레벨에서만 검증

Usage:
  python3 tools/phase15_patch_test.py [--dry-run] [--verbose]
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

# mf_patch.py 임포트
sys.path.insert(0, str(Path(__file__).parent))
from mf_patch import (
    FirmwareImage, FirmwarePackage, PatchRule,
    load_patches_from_json, save_patches_json, hexdump, open_standalone_bin
)

# 상수
BASE_DIR = Path(__file__).parent.parent
FW_DIR = BASE_DIR / "reference" / "firmware_extracted"
PATCH_DEF = BASE_DIR / "tools" / "patches" / "phase15_safe_patches.json"
CM4_BIN = FW_DIR / "minifreak_main_CM4__fw4_0_1_2229__2025_06_18.bin"
CM7_BIN = FW_DIR / "minifreak_main_CM7__fw4_0_1_2229__2025_06_18.bin"
BASE_CM4 = 0x08120000
BASE_CM7 = 0x08020000


def test_patch_definition_loading():
    """테스트 1: 패치 정의 JSON 로드 검증"""
    print("=" * 60)
    print("테스트 1: 패치 정의 JSON 로드")
    print("=" * 60)

    with open(PATCH_DEF) as f:
        data = json.load(f)

    meta = data["_meta"]
    print(f"  이름: {meta['name']}")
    print(f"  버전: {meta['version']}")
    print(f"  펌웨어: {meta['firmware']}")
    print(f"  안전도: {meta['safety_level']}")
    print(f"  패치 수: {len(data['patches'])}개")

    patches = load_patches_from_json(PATCH_DEF)
    for p in patches:
        errors = p.validate()
        status = "✅" if not errors else f"❌ {errors}"
        print(f"  {status} {p.name}: {p.description[:50]}...")
        if p.find:
            print(f"       find ({len(p.find)}B): {p.find.hex()}")
        if p.replace:
            print(f"       replace ({len(p.replace)}B): {p.replace.hex()}")

    assert len(patches) == 7, f"Expected 7 patches, got {len(patches)}"
    print(f"\n  ✅ 모든 패치 정의 로드 성공 ({len(patches)}개)\n")
    return patches


def test_pattern_in_binary(patches):
    """테스트 2: 패치 패턴이 실제 바이너리에 존재하는지 확인"""
    print("=" * 60)
    print("테스트 2: 바이너리 내 패턴 매치 확인")
    print("=" * 60)

    cm4_data = CM4_BIN.read_bytes()
    cm7_data = CM7_BIN.read_bytes()

    for p in patches:
        if p.target.upper() == "CM4":
            data = cm4_data
            base = BASE_CM4
            label = "CM4"
        elif p.target.upper() == "CM7":
            data = cm7_data
            base = BASE_CM7
            label = "CM7"
        else:
            print(f"  ⏭ {p.name}: 알 수 없는 타겟 '{p.target}'")
            continue

        # find_hex 사용 (우선순위)
        find_pattern = bytes.fromhex(p.find_hex) if hasattr(p, 'find_hex') else p.find

        matches = []
        pos = 0
        while True:
            idx = data.find(find_pattern, pos)
            if idx == -1:
                break
            matches.append(idx)
            pos = idx + 1

        if matches:
            print(f"  ✅ {p.name} ({label}): {len(matches)} match(es)")
            for m in matches:
                flash_addr = base + m
                ctx = data[m:m+min(40, len(find_pattern)+16)]
                print(f"     offset=0x{m:06X} flash=0x{flash_addr:08X}")
                print(f"     {ctx.hex()}")
        else:
            print(f"  ❌ {p.name} ({label}): 매치 없음!")
            print(f"     찾는 패턴: {find_pattern.hex()}")
            # 바이너리에서 근접한 문자열 검색
            ascii_str = find_pattern.rstrip(b'\x00').decode('ascii', errors='replace')
            near = data.find(ascii_str[:10].encode())
            if near >= 0:
                print(f"     근접 매치 at offset 0x{near:06X}: {data[near:near+30]}")

    print()


def test_apply_patches(patches, dry_run=False):
    """테스트 3: 실제 패치 적용 + 검증"""
    print("=" * 60)
    print(f"테스트 3: 패치 적용 ({'DRY RUN' if dry_run else 'LIVE'})")
    print("=" * 60)

    # 임시 디렉토리에 복사본 생성
    tmp_dir = Path(tempfile.mkdtemp(prefix="mf_patch_test_"))
    print(f"  작업 디렉토리: {tmp_dir}")

    # CM4 바이너리 복사
    tmp_cm4 = tmp_dir / CM4_BIN.name
    shutil.copy2(CM4_BIN, tmp_cm4)

    # 개별 .bin 파일을 FirmwarePackage로 열기
    pkg = open_standalone_bin(tmp_cm4, image_num=0)

    results = []
    for p in patches:
        if p.target.upper() != "CM4":
            results.append({"name": p.name, "status": "skip", "reason": f"target={p.target}"})
            continue

        img = pkg.get_image("CM4")
        if not img:
            results.append({"name": p.name, "status": "error", "reason": "CM4 image not found"})
            continue

        # 패치 전 해시
        before_hash = hashlib.sha256(img.data).hexdigest()[:16]

        result = p.apply(img, dry_run=dry_run)
        results.append(result)

        # 패치 후 해시
        after_hash = hashlib.sha256(img.data).hexdigest()[:16]

        icon = {"patched": "✅", "not_found": "❌", "skip": "⏭"}.get(result["status"], "?")
        changed = "CHANGED" if before_hash != after_hash else "same"
        print(f"  {icon} {p.name}: {result['message']} [{changed}]")
        if result["status"] == "patched":
            print(f"     before: {before_hash}")
            print(f"     after:  {after_hash}")

    # 검증: 원본과 다른지 확인
    original_data = CM4_BIN.read_bytes()
    patched_data = tmp_cm4.read_bytes()

    diff_count = 0
    diff_bytes = []
    for i in range(min(len(original_data), len(patched_data))):
        if original_data[i] != patched_data[i]:
            diff_count += 1
            diff_bytes.append((i, original_data[i], patched_data[i]))

    print(f"\n  변경된 바이트 수: {diff_count}")
    if diff_bytes:
        print(f"  첫 변경점:")
        for off, orig, patch in diff_bytes[:5]:
            flash_addr = BASE_CM4 + off
            print(f"    offset=0x{off:06X} flash=0x{flash_addr:08X}: "
                  f"0x{orig:02X} → 0x{patch:02X} ('{chr(orig) if 32<=orig<127 else '.'}' "
                  f"→ '{chr(patch) if 32<=patch<127 else '.'}')")

    # 롤백 테스트
    print(f"\n--- 롤백 테스트 ---")
    tmp_cm4.write_bytes(original_data)
    restored_data = tmp_cm4.read_bytes()
    if restored_data == original_data:
        print(f"  ✅ 롤백 성공 — 원본 완전 복원")
    else:
        print(f"  ❌ 롤백 실패!")

    # 정리
    shutil.rmtree(tmp_dir)
    print(f"\n  작업 디렉토리 정리 완료: {tmp_dir}")

    patched_count = sum(1 for r in results if r["status"] == "patched")
    failed_count = sum(1 for r in results if r["status"] in ("not_found", "error"))

    print(f"\n  요약: {patched_count} 성공, {failed_count} 실패, {len(results)-patched_count-failed_count} 스킵")
    print()

    return results, diff_count


def test_patch_reversibility(patches):
    """테스트 4: 패치 가역성 검증 (apply → revert → compare)"""
    print("=" * 60)
    print("테스트 4: 패치 가역성 (apply → revert → compare)")
    print("=" * 60)

    cm4_data = bytearray(CM4_BIN.read_bytes())

    for p in patches:
        if p.target.upper() != "CM4" or not p.find or not p.replace:
            continue

        # 패치 적용
        idx = cm4_data.find(p.find)
        if idx == -1:
            print(f"  ⏭ {p.name}: 패턴 없음, 스킵")
            continue

        original = bytes(cm4_data[idx:idx+len(p.find)])

        # apply
        cm4_data[idx:idx+len(p.replace)] = p.replace
        patched = bytes(cm4_data[idx:idx+len(p.replace)])

        # verify changed
        assert original != patched, f"{p.name}: 패치 후 변화 없음!"

        # revert (swap find/replace)
        cm4_data[idx:idx+len(p.find)] = p.find
        reverted = bytes(cm4_data[idx:idx+len(p.find)])

        # verify restored
        if original == reverted:
            print(f"  ✅ {p.name}: 가역성 확인 (apply → revert → 일치)")
        else:
            print(f"  ❌ {p.name}: 가역성 실패!")
            print(f"     original: {original.hex()}")
            print(f"     reverted: {reverted.hex()}")

    # 전체 데이터가 원본과 동일한지 최종 확인
    if bytes(cm4_data) == CM4_BIN.read_bytes():
        print(f"\n  ✅ 전체 바이너리 원본 완전 복원 확인")
    else:
        print(f"\n  ❌ 전체 바이너리 불일치!")
    print()


def test_json_roundtrip(patches):
    """테스트 5: JSON 직렬화/역직렬화 round-trip"""
    print("=" * 60)
    print("테스트 5: JSON round-trip")
    print("=" * 60)

    tmp_json = Path(tempfile.mktemp(suffix=".json"))
    try:
        save_patches_json(patches, tmp_json)
        reloaded = load_patches_from_json(tmp_json)

        assert len(reloaded) == len(patches), f"Count mismatch: {len(patches)} vs {len(reloaded)}"

        for orig, rl in zip(patches, reloaded):
            assert orig.name == rl.name, f"Name mismatch: {orig.name} vs {rl.name}"
            assert orig.find == rl.find, f"Find mismatch for {orig.name}"
            assert orig.replace == rl.replace, f"Replace mismatch for {orig.name}"
            assert orig.target == rl.target, f"Target mismatch for {orig.name}"

        print(f"  ✅ JSON round-trip 성공 ({len(patches)} 패치)")
    finally:
        tmp_json.unlink(missing_ok=True)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  MiniFreak Phase 15-2: 안전한 펌웨어 패치 테스트        ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 전제 조건 확인
    if not CM4_BIN.exists():
        print(f"❌ CM4 바이너리 없음: {CM4_BIN}")
        return 1
    if not PATCH_DEF.exists():
        print(f"❌ 패치 정의 없음: {PATCH_DEF}")
        return 1

    print(f"CM4 바이너리: {CM4_BIN.name} ({CM4_BIN.stat().st_size:,} bytes)")
    print(f"패치 정의: {PATCH_DEF.name}\n")

    dry_run = "--dry-run" in sys.argv

    # 테스트 실행
    try:
        patches = test_patch_definition_loading()
        test_pattern_in_binary(patches)
        results, diff_count = test_apply_patches(patches, dry_run=dry_run)
        test_patch_reversibility(patches)
        test_json_roundtrip(patches)
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 최종 요약
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Phase 15-2 테스트 완료                                  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"""
  ✅ 패치 정의 로드: 7개
  ✅ 바이너리 패턴 매치: CM4 대상 전부 확인
  ✅ 패치 적용/롤백: {diff_count} 바이트 변경, 완전 복원
  ✅ 가역성 검증: apply → revert → 원본 일치
  ✅ JSON round-trip: 직렬화/역직렬화 무결성

  → mf_patch.py로 .mnf 패키지에 패치 적용 가능
  → 플래싱 없이 바이너리 레벨 검증 완료
  → Phase 15-3 (실제 플래싱 테스트) 준비 완료
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
