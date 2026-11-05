#!/bin/sh
set -eu
. "$(dirname -- "$0")/common.sh"
if test "${1:-}" = --verify-local; then
    python3 tests/hash.py tests/local-fixtures
    exit 0
fi
test "${1:-}" = --verify || { printf '%s\n' 'usage: sh tests/corpus.sh --verify [or --verify-local for optional owner fixtures]' >&2; exit 2; }
python3 tests/hash.py tests/fixtures
python3 tests/corpus_contract.py
