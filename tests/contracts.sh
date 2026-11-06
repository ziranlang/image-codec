#!/bin/sh
set -eu
. "$(dirname -- "$0")/common.sh"
test -x "$ziran" && test -x "$zi2zx"
out="$root/build/scratch/contracts"
mkdir -p "$out"
"$ziran" check --root tests --module-path "image_codec=$root/src" --module-path "std=$toolchain/std" tests/contracts.zi
"$ziran" ir --root tests --module-path "image_codec=$root/src" --module-path "std=$toolchain/std" -o "$out/ir" tests/contracts.zi
"$ziran" bundle --root tests --module-path "image_codec=$root/src" --module-path "std=$toolchain/std" --entry contracts:SelfTest -o "$out/source.zx" tests/contracts.zi
test "$("$ziran" run "$out/source.zx")" = 0
test "$("$zi2zx" run --vm "$out/source.zx")" = 0
"$ziran" bundle --root "$out/ir" --module-path "$out/ir" --entry contracts:SelfTest -o "$out/saved.zx" "$out/ir/contracts.zir"
test "$("$ziran" run "$out/saved.zx")" = 0
test "$("$zi2zx" run --vm "$out/saved.zx")" = 0
for form in source saved; do
    input="$root/tests/contracts.zi"
    set -- --root tests --module-path "image_codec=$root/src" --module-path "std=$toolchain/std"
    if test "$form" = saved; then input="$out/ir/contracts.zir"; set -- --root "$out/ir" --module-path "$out/ir"; fi
    "$ziran" build --target=c --exe --entry contracts:main "$@" -o "$out/$form" "$input"
    "$out/$form/contracts"
    "$ziran" build --target=go --pkg main "$@" -o "$out/$form-go" "$input"
    cat > "$out/$form-go/main.go" <<'GO'
package main
func main() { if Contracts_SelfTest() != 0 { panic("image-codec contract differs") } }
GO
    mkdir -p "$root/build/scratch/go-tmp" "$root/build/cache/go"
    GO111MODULE=off GOMAXPROCS=2 GOTMPDIR="$root/build/scratch/go-tmp" GOCACHE="$root/build/cache/go" go build -o "$out/$form-go/contracts-test" "$out/$form-go"/*.go
    "$out/$form-go/contracts-test"
done
"$ziran" build --target=c --no-main --entry contracts:AllocationFailure --root tests --module-path "image_codec=$root/src" --module-path "std=$toolchain/std" -o "$out/allocation-failure" tests/contracts.zi
"${CC:-cc}" -std=c99 -I"$toolchain/include" -I"$out/allocation-failure" "$out/allocation-failure"/*.c tests/allocation_failure.c -Wl,--wrap=realloc -lm -o "$out/allocation-failure/test"
"$out/allocation-failure/test"
cat > "$out/invalid-owned.zi" <<'ZI'
#import "image_codec/api"
#program_export
main :: () -> s32 {
    metadata: ImageMetadata; metadata.width = 1; metadata.height = 1
    result := AllocateImage(metadata, DefaultLimits(), null)
    moved := result
    return ifx result.is_ok then 1 else 0
}
ZI
if "$ziran" check --root "$out" --module-path "image_codec=$root/src" --module-path "std=$toolchain/std" "$out/invalid-owned.zi" >"$out/invalid-owned.log" 2>&1; then
    printf '%s\n' 'owned image result was usable after move' >&2; exit 1
fi
rg -q 'used after moving' "$out/invalid-owned.log"
printf '%s\n' 'image-codec contracts: source, saved IR, portable VM and native C/Go passed'
