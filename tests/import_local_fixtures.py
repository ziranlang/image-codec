#!/usr/bin/env python3
"""Explicit local owner-asset import into ignored storage; no fetching."""
import json
from pathlib import Path
import shutil
import subprocess
from hash import digest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parents[2] / "kryonlabs/kryon"
OUT = ROOT / "tests/local-fixtures"

def main():
    subprocess.run(["git", "check-ignore", "tests/local-fixtures/probe"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    if OUT.exists():
        raise SystemExit("local fixtures already exist; refusing to overwrite")
    (OUT / "avif").mkdir(parents=True)
    revision = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    entries = []
    for name in ("jungle-title.avif", "jungle-title-samples.rgba"):
        source = SOURCE / "tests/fixtures/avif" / name
        target = OUT / "avif" / name
        shutil.copyfile(source, target)
        entry = {"path": "avif/" + name, "sha256": digest(target), "bytes": target.stat().st_size,
                 "role": "encoded" if name.endswith(".avif") else "golden", "format": "avif",
                 "rights": {"status": "owner-provided", "license": None, "redistribution": "unverified"},
                 "provenance": {"repository": "https://github.com/kryonlabs/kryon", "revision": revision,
                                "path": "tests/fixtures/avif/" + name, "method": "byte-for-byte local copy; excluded from distributable corpus"}}
        if name.endswith(".avif"):
            entry.update(dimensions=[1024, 1536], profile="8-bit opaque YUV420",
                         expectation={"kind": "samples", "golden": "avif/jungle-title-samples.rgba", "sample_grid": [8, 8], "max_byte_error": 3})
        entries.append(entry)
    manifest = OUT / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": 1, "fetch_policy": "explicit local import only; never during build", "fixtures": entries}, indent=2) + "\n")
    (OUT / "manifest.sha256").write_text(digest(manifest) + "  manifest.json\n")
    print("Imported two optional owner fixtures into ignored local storage")

if __name__ == "__main__":
    main()
