# Offline image corpus

`tests/fixtures/manifest.json` pins every file's SHA-256, size, role, origin,
source revision and rights assessment. `manifest.sha256` pins the manifest.
Encoded entries record dimensions/profile and full RGBA goldens, sample grids,
expected rejection or unsupported capability. Verification checks integrity and
expectations; it does not claim AVIF/WebP decoding before providers exist.

Original AVIF/WebP binaries were copied unchanged from canonical Kryon. Tiny
AVIF goldens come from independently known pixels/geometry; the copied generator
and README preserve the recipe and libavif version. WebP first-frame RGBA oracle
files record the Pillow version on each entry. VP8 lossy fixtures allow byte
tolerance; the RGBA baseline benchmark itself requires exact bytes. WebP
animation is unsupported for the future still-only authored provider, retaining
a first-frame oracle for bridges. AVIF animation retains first-frame expectations.

The BSD notice is copied under `fixtures/provenance`. The default corpus has
69 licensed/generated fixture and provenance files. Jungle asset/sample rights
are owner-provided with redistribution unverified, so their two local copies
and separate pinned manifest live under ignored `tests/local-fixtures`.
They are excluded from the distributable mandatory corpus. Optionally run
`python3 tests/import_local_fixtures.py` and
`build-queue -- sh tests/corpus.sh --verify-local` for that local comparison;
neither runs during normal tests. No broader license is invented.

Two WebP rejection fixtures are deterministic derivatives: remove the lossless
source's last byte or replace RIFF with `BAD!`. Entries retain the parent digest
and transformation. AVIF rejections cover damaged crop, truncation, malformed
container, per-axis and total-pixel limits. Profile labels describe source
fixtures, not decoder support claims.

```sh
build-queue -- sh tests/corpus.sh --verify
```

Verification is offline and streams bounded chunks. Negative tests use ignored
`build/scratch` copies and reject missing files, changed bytes/manifest and
absent provenance/rights. Nothing is fetched or regenerated during a build.

Maintenance is explicit: `python3 tests/import_kryon_fixtures.py` requires an
absent destination and copies canonical source fixtures;
`python3 tests/derive_fixtures.py` then adds two malformed binaries. Review
manifest and pin updates together. Both refuse to overwrite existing fixtures.
