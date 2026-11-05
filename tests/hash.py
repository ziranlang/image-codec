#!/usr/bin/env python3
"""Offline, streaming digest and provenance validation for the pinned corpus."""
import hashlib
import json
from pathlib import Path
import re
import sys

def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            value.update(block)
    return value.hexdigest()

def validate_manifest(manifest):
    if manifest.get("schema_version") != 1 or not manifest.get("fixtures"):
        raise ValueError("missing corpus schema/fixtures")
    paths = set()
    for entry in manifest["fixtures"]:
        path = entry.get("path", "")
        if not path or Path(path).is_absolute() or ".." in Path(path).parts or path in paths:
            raise ValueError("unsafe/duplicate fixture path")
        paths.add(path)
        if not re.fullmatch(r"[0-9a-f]{64}", entry.get("sha256", "")) or type(entry.get("bytes")) is not int or entry["bytes"] < 0:
            raise ValueError(f"invalid digest/size: {path}")
        provenance = entry.get("provenance", {})
        if not all(provenance.get(key) for key in ("repository", "revision", "path", "method")):
            raise ValueError(f"missing provenance: {path}")
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", provenance["revision"]):
            raise ValueError(f"unresolved source revision: {path}")
        rights = entry.get("rights", {})
        if rights.get("status") == "repository-license":
            if not rights.get("license") or not rights.get("notice"):
                raise ValueError(f"missing license/notice: {path}")
        elif rights.get("status") != "owner-provided" or rights.get("redistribution") != "unverified":
            raise ValueError(f"missing rights assessment: {path}")
        if entry.get("role") == "encoded":
            if "dimensions" not in entry or not entry.get("profile") or not entry.get("expectation"):
                raise ValueError(f"missing image expectation: {path}")
            expected = entry["expectation"]
            if expected.get("kind") not in ("pixels", "samples", "reject", "unsupported"):
                raise ValueError(f"invalid expectation: {path}")
            if expected["kind"] in ("reject", "unsupported") and not expected.get("error"):
                raise ValueError(f"missing rejection: {path}")
            if expected["kind"] == "reject" and not expected.get("malformed_class"):
                raise ValueError(f"missing malformed class: {path}")
            if expected["kind"] in ("pixels", "samples") and not expected.get("golden"):
                raise ValueError(f"missing golden: {path}")
            if expected["kind"] != "reject":
                dimensions = entry["dimensions"]
                if not isinstance(dimensions, list) or len(dimensions) != 2 or not all(type(v) is int and v > 0 for v in dimensions):
                    raise ValueError(f"invalid dimensions: {path}")
    by_path = {entry["path"]: entry for entry in manifest["fixtures"]}
    for entry in manifest["fixtures"]:
        notice = entry["rights"].get("notice")
        if notice and notice not in paths:
            raise ValueError(f"missing license file: {notice}")
        golden = entry.get("expectation", {}).get("golden")
        if golden:
            if golden not in by_path:
                raise ValueError(f"unlisted golden: {golden}")
            expected = entry["expectation"]
            width, height = expected.get("sample_grid", entry["dimensions"])
            if by_path[golden]["bytes"] != width * height * 4:
                raise ValueError(f"wrong golden size: {golden}")

def verify(root):
    root = Path(root).resolve()
    manifest_path = root / "manifest.json"
    pin = (root / "manifest.sha256").read_text().split()
    if len(pin) != 2 or pin[1] != "manifest.json" or digest(manifest_path) != pin[0]:
        raise ValueError("manifest digest mismatch")
    manifest = json.loads(manifest_path.read_text())
    validate_manifest(manifest)
    listed = {entry["path"] for entry in manifest["fixtures"]} | {"manifest.json", "manifest.sha256"}
    actual = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}
    if listed != actual:
        raise ValueError("corpus inventory differs from pinned manifest")
    for entry in manifest["fixtures"]:
        path = root / entry["path"]
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"missing/unsafe fixture: {entry['path']}")
        if path.stat().st_size != entry["bytes"] or digest(path) != entry["sha256"]:
            raise ValueError(f"fixture digest/size mismatch: {entry['path']}")
    return manifest

if __name__ == "__main__":
    try:
        result = verify(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "fixtures")
        print(f"Corpus verified: {len(result['fixtures'])} offline files, digests, provenance, rights and expectations")
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise SystemExit(str(error))
