from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "swir.project002.capture-evidence.v1"
FORBIDDEN_FILE_SUFFIXES = {
    ".nes", ".rom", ".fds", ".unf", ".unif", ".sav", ".srm", ".state", ".mss", ".zip", ".7z", ".rar",
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".exe", ".dll",
}
FORBIDDEN_KEYS = {
    "rom", "rom_path", "rom_file", "source_path", "capture_path", "save_state", "save_path", "emulator_path",
    "absolute_path", "local_path", "pixel_data", "image_bytes", "base64",
}
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"^[A-Za-z]:[\\/]"),
    re.compile(r"^/(?:home|Users|mnt|media|tmp|var|opt)/"),
    re.compile(r"^\\\\[^\\]+\\"),
)


def _looks_absolute(value: str) -> bool:
    return any(pattern.search(value) for pattern in ABSOLUTE_PATH_PATTERNS)


def _walk(value, errors: list[str], where: str = "root") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in FORBIDDEN_KEYS:
                errors.append(f"forbidden key at {where}: {key}")
            _walk(item, errors, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk(item, errors, f"{where}[{index}]")
    elif isinstance(value, str):
        if _looks_absolute(value):
            errors.append(f"absolute local path at {where}")
        if len(value) > 512_000:
            errors.append(f"oversized string payload at {where}")


def validate_evidence(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    privacy = data.get("privacy_contract")
    if not isinstance(privacy, dict):
        errors.append("privacy_contract missing")
    else:
        expected = {
            "contains_rom": False,
            "contains_save_state": False,
            "contains_capture_pixels": False,
            "contains_emulator_binary": False,
            "contains_absolute_local_paths": False,
            "metadata_only": True,
        }
        for key, expected_value in expected.items():
            if privacy.get(key) is not expected_value:
                errors.append(f"privacy_contract.{key} must be {expected_value}")
    hd = data.get("hd_pack")
    if not isinstance(hd, dict):
        errors.append("hd_pack missing")
    else:
        fingerprint = str(hd.get("capture_fingerprint", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            errors.append("hd_pack.capture_fingerprint must be sha256 hex")
        images = hd.get("images", [])
        if not isinstance(images, list):
            errors.append("hd_pack.images must be a list")
        else:
            for index, row in enumerate(images):
                if not isinstance(row, dict):
                    errors.append(f"hd_pack.images[{index}] must be an object")
                    continue
                allowed = {"name", "present", "bytes", "sha256", "width", "height", "mode"}
                extra = set(row) - allowed
                if extra:
                    errors.append(f"hd_pack.images[{index}] has unsupported fields: {sorted(extra)}")
    _walk(data, errors)
    return errors


def validate_file(path: Path) -> list[str]:
    target = Path(path)
    errors: list[str] = []
    if target.suffix.lower() != ".json":
        return ["evidence file must be JSON"]
    if target.stat().st_size > 5 * 1024 * 1024:
        errors.append("evidence JSON exceeds 5 MiB metadata limit")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return ["evidence root must be an object"]
    errors.extend(validate_evidence(data))
    return errors


def validate_evidence_tree(path: Path) -> list[str]:
    root = Path(path)
    if root.is_file():
        return validate_file(root)
    errors: list[str] = []
    json_files: list[Path] = []
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        suffix = item.suffix.lower()
        if suffix in FORBIDDEN_FILE_SUFFIXES:
            errors.append(f"forbidden payload file: {item.relative_to(root).as_posix()}")
        if suffix == ".json":
            json_files.append(item)
    if not json_files:
        errors.append("no capture evidence JSON found")
    for item in json_files:
        for error in validate_file(item):
            errors.append(f"{item.relative_to(root).as_posix()}: {error}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Project #002 privacy-safe capture evidence")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    errors = validate_evidence_tree(args.path)
    if errors:
        print("CAPTURE EVIDENCE: BLOCKED")
        for error in errors:
            print(f"- {error}")
        return 2
    print("CAPTURE EVIDENCE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
