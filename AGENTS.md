# image-codec agent guide

Optional image decoder contracts and a measured RGBA8 baseline, authored in
Ziran. Reuses `std/image.Image`; no Kryon or native codec dependency. AVIF,
AV1 and WebP decoders live in their own packages.

## Layout

- `src/` — exported modules: `api`, `errors`, `limits`, `metadata`, `bytes`,
  `buffer`, `image`, `scheduler`, `benchmark` (see `ziran.toml`).
- `docs/` — `API.md`, `CORPUS.md` (fixtures), `BENCHMARKS.md`.
- `tests/` — `contracts.sh`, `corpus.sh --verify`, `benchmark_contract.sh`,
  `package_import.sh`, plus a `common.sh` helper and the benchmark validator.
- `tools/` — helper tools. No Makefile; the test scripts are the interface.
- `ziran.toml` / `ziran.lock` — identity and locked toolchain; local
  overrides drive the package-import test.

## Commands

Run from the canonical checkout with Ziran at `../../ziran`:

- `build-queue -- sh tests/contracts.sh`
- `build-queue -- sh tests/corpus.sh --verify`
- `build-queue -- sh tests/benchmark_contract.sh`
- `build-queue -- sh tests/package_import.sh`

`ZIRAN_ROOT` and `ZIRAN` select an existing toolchain. Tests use no display,
network, fixture downloads or native codecs; outputs stay under ignored
`build/`. The toolchain must provide `VecResize`/`VecResizeBounded`.

## Pins

- Toolchain: `ziran.lock` pins ziran.git
  `5db3d3c39425d5dfe4bfe4a84e6f6e2e5a810ad0`.
- Consumers import `image_codec/api` (dependency name `image_codec`).

## Question -> file

- What is the API? -> `docs/API.md`, `src/api.zi`.
- Which fixtures? -> `docs/CORPUS.md`, `tests/`.
- Benchmark numbers? -> `docs/BENCHMARKS.md`, `src/benchmark.zi`.
- How do I run everything? -> the four `tests/*.sh` commands above.
