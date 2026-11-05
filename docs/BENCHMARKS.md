# Measured file-to-pixel baseline

```sh
build-queue -- sh tests/benchmark_contract.sh
mkdir -p out
build/bin/bench --input tests/fixtures/avif/rgba8.rgba \
  --expected tests/fixtures/avif/rgba8.rgba --width 8 --height 6 \
  --iterations 7 --report out/report.json
```

The stable executable is `build/bin/bench`. It offers `--provider rgba8` and
`--mode warm`. Absent codecs and cold-cache mode fail without writing a new
report. AVIF/WebP parsing, native oracles, corpus discovery and cache eviction
are not implemented. Encoded providers can use the ordinary `DecodeProcedure`
argument of `BenchmarkFile`; this package never imports them automatically.

`BenchmarkFile(path,expected,metadata,options*,provider,iterations)` opens,
reads/closes input, invokes the provider, compares every pixel with the golden,
and records an FNV-1a 64-bit pixel hash before any timed iteration. Samples
include open, bounded reads, close, decode and input/output allocation. Golden
comparison, hashing, destruction and report writing are untimed. Every timed
output is checked again. Width, height and byte length must also match.

Preflight warms input and allocator. This is a warm run, with no cold disk,
startup or cache eviction claim. Iterations are bounded to 1..1024 and use the
standard monotonic nanosecond clock. Wall latency includes scheduling.
`SummarizeTimings` sorts samples, computes nearest-rank p50/p95, checks total
overflow and derives throughput from pixels times iterations divided by total
time. Zero-duration totals yield null throughput. The budget must be idle on
entry; its peaks are reset, then observed peak workers across preflight/timed
calls are reported. No threads are created.

`BenchmarkJSON` emits [schema version 1](benchmark.schema.json), including
sorted real `samples_ns`, input/output bytes, pixels, p50/p95/total wall
nanoseconds, pixels/second, observed workers, output hash/algorithm, mode,
timing scope and tool versions. Pass the actual compiler's version text with
`--toolchain-version`; an absent version is JSON null.

CPU-time/pixel, peak RSS, allocations, energy and CPU capabilities are
uninstrumented and always null in schema 1, each with an `unavailable` reason.
Wall time is never CPU time; reservations are never RSS; vector capacity is
never allocation count. Future instruments require separate tests/schema work.

Tests run the real native runner from source and saved IR, compare repeated-run
correctness fields rather than noisy timings, validate required fields and
derived statistics, reject invented metrics, reject a wrong same-size golden
before timing, and reject absent providers/cold-cache mode. Pure statistics
and hash cases run through source/saved IR in the portable VM. Native-only
file/timer imports are not claimed in a capability-free VM.
