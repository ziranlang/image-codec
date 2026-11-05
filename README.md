# image-codec

Optional image decoder contracts and a measured RGBA8 baseline, authored in
Ziran. The package reuses `std/image.Image` and has no Kryon or native codec
dependency. AVIF, AV1 and WebP decoders are supplied by separate packages.

Consumers import `image_codec/api` when the dependency is named `image_codec`.
Exports also expose individual ordinary modules. See [API](docs/API.md),
[fixtures](docs/CORPUS.md) and [benchmarks](docs/BENCHMARKS.md).

From this canonical checkout, with Ziran at `../../ziran`:

```sh
build-queue -- sh tests/contracts.sh
build-queue -- sh tests/corpus.sh --verify
build-queue -- sh tests/benchmark_contract.sh
build-queue -- sh tests/package_import.sh
```

`ZIRAN_ROOT` and `ZIRAN` select an existing toolchain. Tests use no display,
network, fixture downloads or native codecs. Package import uses local
overrides; a toolchain that requires committed HEADs rejects an unborn package.
Direct module tests exercise the same source without a milestone commit.
Generated outputs stay under ignored `build/`.
The rebuilt toolchain must provide `VecResize` and `VecResizeBounded`; a version string alone does
not identify this development capability before upstream integration.
