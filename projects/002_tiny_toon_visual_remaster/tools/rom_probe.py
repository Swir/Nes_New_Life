from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path

KNOWN_SHA1 = "110796622e50c2e8c20b1430acadc5bae5f36586"


@dataclass(frozen=True)
class RomInfo:
    path: str
    filename: str
    size: int
    format: str
    prg_rom_bytes: int
    chr_rom_bytes: int
    mapper: int
    submapper: int | None
    trainer: bool
    battery: bool
    mirroring: str
    sha1: str
    sha256: str
    md5: str
    crc32: str
    payload_sha1: str
    known_project_rom: bool
    chr_offset: int
    chr_tile_count: int


def parse_rom(path: str | Path) -> tuple[RomInfo, bytes]:
    p = Path(path).expanduser().resolve()
    data = p.read_bytes()
    if len(data) < 16 or data[:4] != b"NES\x1a":
        raise ValueError("Not a valid iNES/NES 2.0 ROM (missing NES<1A> header).")

    h = data[:16]
    nes2 = (h[7] & 0x0C) == 0x08
    trainer = bool(h[6] & 0x04)
    battery = bool(h[6] & 0x02)
    mapper = (h[6] >> 4) | (h[7] & 0xF0)
    submapper = None

    if nes2:
        mapper |= (h[8] & 0x0F) << 8
        submapper = h[8] >> 4
        prg_units = h[4] | ((h[9] & 0x0F) << 8)
        chr_units = h[5] | ((h[9] >> 4) << 8)
        if (h[9] & 0x0F) == 0x0F or (h[9] >> 4) == 0x0F:
            raise ValueError("NES 2.0 exponent/multiplier ROM sizes are not supported by this tool yet.")
        prg_size = prg_units * 16384
        chr_size = chr_units * 8192
        fmt = "NES 2.0"
    else:
        prg_size = h[4] * 16384
        chr_size = h[5] * 8192
        fmt = "iNES 1.0"

    mirroring = "four-screen" if h[6] & 0x08 else ("vertical" if h[6] & 0x01 else "horizontal")
    payload_offset = 16 + (512 if trainer else 0)
    chr_offset = payload_offset + prg_size
    expected = chr_offset + chr_size
    if len(data) < expected:
        raise ValueError(f"ROM is truncated: expected at least {expected} bytes, got {len(data)}.")

    sha1 = hashlib.sha1(data).hexdigest()
    info = RomInfo(
        path=str(p), filename=p.name, size=len(data), format=fmt,
        prg_rom_bytes=prg_size, chr_rom_bytes=chr_size, mapper=mapper, submapper=submapper,
        trainer=trainer, battery=battery, mirroring=mirroring,
        sha1=sha1, sha256=hashlib.sha256(data).hexdigest(), md5=hashlib.md5(data).hexdigest(),
        crc32=f"{zlib.crc32(data) & 0xFFFFFFFF:08x}",
        payload_sha1=hashlib.sha1(data[payload_offset:expected]).hexdigest(),
        known_project_rom=(sha1 == KNOWN_SHA1), chr_offset=chr_offset, chr_tile_count=chr_size // 16,
    )
    return info, data


def decode_chr_tile(tile: bytes) -> list[int]:
    if len(tile) != 16:
        raise ValueError("NES CHR tile must be exactly 16 bytes.")
    pixels: list[int] = []
    for y in range(8):
        lo, hi = tile[y], tile[y + 8]
        for x in range(8):
            bit = 7 - x
            pixels.append(((hi >> bit) & 1) * 2 + ((lo >> bit) & 1))
    return pixels


def export_chr(info: RomInfo, data: bytes, output: Path, scale: int = 4, tiles_per_sheet: int = 256) -> Path:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for CHR export. Run: pip install Pillow") from exc

    if info.chr_rom_bytes <= 0:
        raise ValueError("This ROM has no CHR ROM to export.")
    if scale < 1 or scale > 16:
        raise ValueError("Scale must be between 1 and 16.")

    output.mkdir(parents=True, exist_ok=True)
    chr_data = data[info.chr_offset:info.chr_offset + info.chr_rom_bytes]
    palette = [(12, 15, 24, 0), (75, 85, 99, 255), (170, 180, 190, 255), (245, 245, 240, 255)]
    manifest: dict[str, object] = {
        "source": info.filename, "source_sha1": info.sha1,
        "warning": "ROM-derived reference images. Keep local; do not commit or redistribute.",
        "tile_count": info.chr_tile_count, "scale": scale, "tiles_per_sheet": tiles_per_sheet, "sheets": [],
    }

    cols = 16
    rows = math.ceil(tiles_per_sheet / cols)
    for start in range(0, info.chr_tile_count, tiles_per_sheet):
        end = min(start + tiles_per_sheet, info.chr_tile_count)
        image = Image.new("RGBA", (cols * 8, rows * 8), (0, 0, 0, 0))
        px = image.load()
        for tile_index in range(start, end):
            local = tile_index - start
            tx, ty = (local % cols) * 8, (local // cols) * 8
            decoded = decode_chr_tile(chr_data[tile_index * 16:tile_index * 16 + 16])
            for y in range(8):
                for x in range(8):
                    px[tx + x, ty + y] = palette[decoded[y * 8 + x]]
        if scale != 1:
            image = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
        sheet_name = f"chr_{start:04x}_{end - 1:04x}.png"
        image.save(output / sheet_name)
        manifest["sheets"].append({"file": sheet_name, "start_tile": start, "end_tile": end - 1})

    manifest_path = output / "chr_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def human(info: RomInfo) -> str:
    return "\n".join([
        f"ROM: {info.filename}", f"Format: {info.format}", f"Size: {info.size} bytes",
        f"PRG ROM: {info.prg_rom_bytes} bytes", f"CHR ROM: {info.chr_rom_bytes} bytes ({info.chr_tile_count} tiles)",
        f"Mapper: {info.mapper}" + (f" / submapper {info.submapper}" if info.submapper is not None else ""),
        f"Mirroring: {info.mirroring}", f"Trainer: {'yes' if info.trainer else 'no'}",
        f"Battery: {'yes' if info.battery else 'no'}", f"SHA-1: {info.sha1}", f"SHA-256: {info.sha256}",
        f"CRC32: {info.crc32}", f"Project fingerprint match: {'YES' if info.known_project_rom else 'NO'}",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a NES ROM and optionally export local CHR reference sheets.")
    parser.add_argument("rom", help="Path to user-supplied .nes ROM")
    parser.add_argument("--json", action="store_true", help="Print metadata as JSON")
    parser.add_argument("--export-chr", type=Path, help="Local output folder for ROM-derived CHR reference PNGs")
    parser.add_argument("--scale", type=int, default=4, help="CHR reference export scale (default: 4)")
    args = parser.parse_args()
    try:
        info, data = parse_rom(args.rom)
        print(json.dumps(asdict(info), indent=2) if args.json else human(info))
        if args.export_chr:
            manifest = export_chr(info, data, args.export_chr, args.scale)
            print(f"\nCHR references exported locally: {manifest.parent}")
            print("WARNING: these PNGs are derived from the ROM; do not commit or redistribute them.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
