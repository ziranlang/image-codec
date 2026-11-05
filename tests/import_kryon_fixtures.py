#!/usr/bin/env python3
"""Explicit local import. Never run by build or corpus verification; no fetches."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parents[2] / "kryonlabs/kryon"
OUT = ROOT / "tests/fixtures"

def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            value.update(block)
    return value.hexdigest()

def main():
    from PIL import Image, __version__ as pillow_version
    if OUT.exists():
        raise SystemExit("fixtures already exist; review changes before importing again")
    OUT.mkdir()
    revision = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    entries = []
    for format_name in ("avif", "webp"):
        destination = OUT / format_name
        destination.mkdir()
        for source in sorted((SOURCE / "tests/fixtures" / format_name).iterdir()):
            if not source.is_file():
                continue
            if source.name.startswith("jungle-title"):
                continue # optional owner asset is imported separately, never distributed
            target = destination / source.name
            shutil.copyfile(source, target)
            role = "encoded" if source.suffix in (".avif", ".webp") else "golden" if source.suffix == ".rgba" else "provenance" if source.suffix == ".md" else "expectation"
            entry = {"path": str(target.relative_to(OUT)), "sha256": digest(target), "bytes": target.stat().st_size,
                     "role": role, "format": format_name,
                     "provenance": {"repository": "https://github.com/kryonlabs/kryon", "revision": revision,
                                    "path": str(source.relative_to(SOURCE)), "method": "byte-for-byte local copy"},
                     "rights": {"status": "repository-license", "license": "BSD-3-Clause", "notice": "provenance/KRYON-LICENSE"}}
            if role == "encoded" and format_name == "avif":
                rejection = {"oversized": "LimitExceeded", "pixel-limit": "LimitExceeded", "bad-crop": "MalformedInput",
                             "truncated": "TruncatedInput", "malformed": "MalformedInput"}.get(source.stem)
                if rejection:
                    entry["dimensions"] = None
                    entry["profile"] = "damaged AVIF copy of generated fixture"
                    entry["expectation"] = {"kind": "reject", "error": rejection, "malformed_class": source.stem}
                else:
                    width, height, tolerance = map(int, source.with_suffix(".txt").read_text().split())
                    depth = 10 if source.stem.endswith("10") and not source.stem.startswith("transform") else 12 if source.stem.endswith("12") else 8
                    entry["dimensions"] = [width, height]
                    entry["profile"] = f"{depth}-bit " + ("monochrome" if source.stem.startswith("gray") else "YUV444")
                    entry["expectation"] = {"kind": "pixels", "golden": f"avif/{source.stem}.rgba", "max_byte_error": tolerance,
                                            "frame_policy": "first-complete-frame", "source_frames": 2 if source.stem == "animated" else 1}
            if role == "encoded" and format_name == "webp":
                with Image.open(source) as image:
                    width, height = image.size
                    frames = getattr(image, "n_frames", 1)
                    image.seek(0)
                    golden = destination / (source.stem + ".rgba")
                    golden.write_bytes(image.convert("RGBA").tobytes())
                entry["dimensions"] = [width, height]
                entry["profile"] = "VP8L" if source.stem == "lossless" else "VP8 with ALPH" if source.stem == "lossy-alpha" else "animated VP8" if frames > 1 else "VP8"
                entry["expectation"] = {"kind": "unsupported" if frames > 1 else "pixels", "golden": f"webp/{source.stem}.rgba",
                                        "max_byte_error": 0 if source.stem == "lossless" else 3, "source_frames": frames,
                                        "frame_policy": "still-only"}
                if frames > 1:
                    entry["expectation"]["error"] = "UnsupportedCapability"
                entries.append({"path": str(golden.relative_to(OUT)), "sha256": digest(golden), "bytes": golden.stat().st_size,
                                "role": "golden", "format": "rgba8", "rights": entry["rights"],
                                "provenance": {"repository": "https://github.com/kryonlabs/kryon", "revision": revision,
                                               "path": str(source.relative_to(SOURCE)), "method": f"Pillow {pillow_version} WebP decoder; first frame RGBA8 oracle"}})
            entries.append(entry)
    provenance = OUT / "provenance"
    provenance.mkdir()
    for source, name in ((SOURCE / "LICENSE", "KRYON-LICENSE"), (SOURCE / "tests/generate_avif_fixtures.py", "generate_avif_fixtures.py")):
        target = provenance / name
        shutil.copyfile(source, target)
        entries.append({"path": str(target.relative_to(OUT)), "sha256": digest(target), "bytes": target.stat().st_size,
                        "role": "provenance", "format": "text", "rights": {"status": "repository-license", "license": "BSD-3-Clause", "notice": "provenance/KRYON-LICENSE"},
                        "provenance": {"repository": "https://github.com/kryonlabs/kryon", "revision": revision, "path": str(source.relative_to(SOURCE)), "method": "byte-for-byte local copy"}})
    manifest = OUT / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": 1, "fetch_policy": "never during build or verification",
                                    "fixtures": sorted(entries, key=lambda item: item["path"])}, indent=2) + "\n")
    (OUT / "manifest.sha256").write_text(digest(manifest) + "  manifest.json\n")
    print(f"Imported {len(entries)} pinned files; originals preserved")

if __name__ == "__main__":
    main()
