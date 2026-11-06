#!/bin/sh
set -eu
. "$(dirname -- "$0")/common.sh"
test -x "$ziran" && test -x "$zi2zx"
out="$root/build/scratch/benchmark"
mkdir -p "$out"
"$ziran" check --root tools --module-path "image_codec=$root/src" --module-path "std=$toolchain/std" tools/bench.zi
"$ziran" build --target=c --exe --entry bench:main --root tools --module-path "image_codec=$root/src" --module-path "std=$toolchain/std" -o "$root/build/bin" tools/bench.zi
"$ziran" ir --root tests --module-path "image_codec=$root/src" --module-path "std=$toolchain/std" -o "$out/ir" tests/benchmark.zi
for form in source saved; do
    input="$root/tests/benchmark.zi"
    set -- --root tests --module-path "image_codec=$root/src" --module-path "std=$toolchain/std"
    if test "$form" = saved; then input="$out/ir/benchmark.zir"; set -- --root "$out/ir" --module-path "$out/ir"; fi
    "$ziran" bundle "$@" --entry benchmark:SelfTest -o "$out/$form.zx" "$input"
    test "$("$ziran" run "$out/$form.zx")" = 0
    test "$("$zi2zx" run --vm "$out/$form.zx")" = 0
    "$ziran" build --target=c --exe --entry benchmark:main "$@" -o "$out/$form-native" "$input"
    "$out/$form-native/benchmark"
done
version=$("$ziran" --version)
for run in first second; do
    if test "$run" = second; then
        "$ziran" ir --root tools --module-path "image_codec=$root/src" --module-path "std=$toolchain/std" -o "$out/runner-ir" tools/bench.zi
        "$ziran" build --target=c --exe --entry bench:main --root "$out/runner-ir" --module-path "$out/runner-ir" -o "$root/build/bin" "$out/runner-ir/bench.zir"
    fi
    build/bin/bench --input tests/fixtures/avif/rgba8.rgba --expected tests/fixtures/avif/rgba8.rgba --width 8 --height 6 --iterations 7 --report "$out/$run.json" --toolchain-version "$version"
done
python3 tests/benchmark_validate.py "$out/first.json" "$out/second.json"
# A different but same-size golden must fail preflight without creating a report.
status=0
build/bin/bench --input tests/fixtures/avif/rgba8.rgba --expected tests/fixtures/avif/opaque.rgba --width 8 --height 6 --report "$out/mismatch.json" >"$out/mismatch.log" 2>&1 || status=$?
test "$status" = 12
rg -q '^correctness mismatch$' "$out/mismatch.log"
test ! -e "$out/mismatch.json"
status=0
build/bin/bench --input tests/fixtures/avif/rgba8.rgba --expected tests/fixtures/avif/rgba8.rgba --width 8 --height 6 --mode cold --report "$out/cold.json" >"$out/cold.log" 2>&1 || status=$?
test "$status" = 5
test ! -e "$out/cold.json"
status=0
build/bin/bench --input tests/fixtures/webp/lossless.webp --expected tests/fixtures/webp/lossless.rgba --width 3 --height 2 --provider webp --report "$out/unsupported.json" >"$out/unsupported.log" 2>&1 || status=$?
test "$status" = 5
test ! -e "$out/unsupported.json"
printf '%s\n' 'image-codec benchmark: native file-to-pixel runner and portable source/saved-IR statistics passed'
