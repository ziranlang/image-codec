#!/usr/bin/env python3
"""Rewrite docs/validation.json; tests/all.sh runs this only after every suite passed."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
toolchain = Path(os.environ.get("ZIRAN_ROOT", str(root / "../../ziran"))).resolve()
bindir = Path(os.environ.get("ZIRAN", str(toolchain / "build/bin/ziran"))).parent
binaries = {name: bindir / name for name in ("ziran", "zi2c", "zi2go", "zi2zx")}
if "ZIRAN_ZX" in os.environ:
    binaries["zi2zx"] = Path(os.environ["ZIRAN_ZX"])
commands = ["sh tests/contracts.sh", "sh tests/corpus.sh --verify", "sh tests/benchmark_contract.sh", "sh tests/package_import.sh"]


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(65536), b""):
            hasher.update(block)
    return hasher.hexdigest()


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


head = git(root, "rev-parse", "HEAD").stdout.strip() or None
dirty = bool(git(root, "status", "--porcelain", "--untracked-files=normal").stdout.strip())
branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or None
# Committed means the tested tree is exactly HEAD; pushed means that HEAD is on the remote-tracking branch.
committed = head is not None and not dirty
pushed = committed and git(root, "merge-base", "--is-ancestor", "HEAD", f"origin/{branch}").returncode == 0
source_globs = ("src/*.zi", "tests/*.zi", "tests/*.py", "tests/*.sh", "docs/benchmark.schema.json", "ziran.toml")
receipt = {
    "snapshot_after_local_tests_utc": datetime.now(timezone.utc).isoformat(),
    "package_root": str(root),
    "package_branch": branch,
    "package_commit": head if committed else None,
    "package_base_commit": head,
    "tracked_or_untracked_changes_present": dirty,
    "committed": committed,
    "pushed": pushed,
    "released": False,
    "installed": False,
    "github_checks": "none run",
    "local_tests": [{"command": f"build-queue -- {c}", "result": "passed"} for c in commands],
    "generated_by": "build-queue -- sh tests/all.sh (tests/validation_receipt.py runs only after all suites pass)",
    "toolchain": {
        "root": str(toolchain),
        "version": subprocess.check_output([str(binaries["ziran"]), "--version"], text=True).strip(),
        "head": git(toolchain, "rev-parse", "HEAD").stdout.strip(),
        "tracked_sources_dirty": git(toolchain, "diff", "--quiet").returncode != 0,
        "binary_sha256": {name: digest(path) for name, path in binaries.items()},
    },
    "source_sha256": {str(p.relative_to(root)): digest(p) for g in source_globs for p in sorted(root.glob(g)) if p.is_file()},
    "mandatory_manifest_sha256": digest(root / "tests/fixtures/manifest.json"),
    "toolchain_unchanged_across_suite": True,
}
(root / "docs/validation.json").write_text(json.dumps(receipt, indent=2) + "\n")
print("image-codec local validation receipt saved; no GitHub checks implied")
