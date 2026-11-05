#!/usr/bin/env python3
import copy
import json
from pathlib import Path
import shutil
import tempfile
from hash import validate_manifest, verify

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "tests/fixtures"
manifest = verify(source)

def rejected(action):
    try:
        action()
    except (ValueError, OSError):
        return
    raise AssertionError("invalid corpus accepted")

for field in ("rights", "provenance", "sha256"):
    broken = copy.deepcopy(manifest)
    del broken["fixtures"][0][field]
    rejected(lambda: validate_manifest(broken))
with tempfile.TemporaryDirectory(dir=ROOT / "build/scratch", prefix="corpus-") as name:
    root = Path(name) / "fixtures"
    shutil.copytree(source, root)
    victim = root / manifest["fixtures"][0]["path"]
    original = victim.read_bytes()
    victim.unlink()
    rejected(lambda: verify(root))
    victim.write_bytes(original + b"changed")
    rejected(lambda: verify(root))
    victim.write_bytes(original)
    extra = root / "unlisted.bin"
    extra.write_bytes(b"unlisted")
    rejected(lambda: verify(root))
    extra.unlink()
    (root / "manifest.json").write_text(json.dumps({"schema_version": 2}))
    rejected(lambda: verify(root))
print("Corpus negative cases: missing file, changed bytes, manifest pin and absent rights/provenance rejected")
