#!/usr/bin/env python3
"""Explicit deterministic binary fixture derivation; never invoked by tests."""
import json
from pathlib import Path
from hash import digest

ROOT = Path(__file__).resolve().parent / "fixtures"
manifest = json.loads((ROOT / "manifest.json").read_text())
source_path = "webp/lossless.webp"
source = next(entry for entry in manifest["fixtures"] if entry["path"] == source_path)
data = (ROOT / source_path).read_bytes()
for name, derived, classification, method in (
    ("webp/truncated.webp", data[:-1], "TruncatedInput", "remove final byte without repairing declared RIFF size"),
    ("webp/malformed.webp", b"BAD!" + data[4:], "MalformedInput", "replace RIFF signature with BAD!; preserve remaining bytes"),
):
    path = ROOT / name
    if path.exists():
        raise SystemExit(f"refusing to overwrite {path}")
    path.write_bytes(derived)
    manifest["fixtures"].append({"path": name, "sha256": digest(path), "bytes": len(derived), "role": "encoded", "format": "webp",
                                "dimensions": None, "profile": "damaged VP8L fixture", "rights": source["rights"],
                                "provenance": {**source["provenance"], "method": method, "parent_sha256": source["sha256"]},
                                "expectation": {"kind": "reject", "error": classification, "malformed_class": Path(name).stem}})
manifest["fixtures"].sort(key=lambda entry: entry["path"])
path = ROOT / "manifest.json"
path.write_text(json.dumps(manifest, indent=2) + "\n")
(ROOT / "manifest.sha256").write_text(digest(path) + "  manifest.json\n")
print("Derived two binary WebP rejection fixtures; source preserved")
