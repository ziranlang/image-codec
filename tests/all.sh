#!/bin/sh
# Full local suite; the receipt is written only after every step passes (set -e).
set -eu
. "$(dirname -- "$0")/common.sh"
sha256sum "$ziran" "$run_vm" > "$root/build/scratch/toolchain-before.sha256"
sh tests/contracts.sh
sh tests/corpus.sh --verify
sh tests/benchmark_contract.sh
sh tests/package_import.sh
sha256sum -c "$root/build/scratch/toolchain-before.sha256"
ZIRAN_ROOT="$toolchain" ZIRAN="$ziran" ZIRAN_VM="$run_vm" python3 tests/validation_receipt.py
