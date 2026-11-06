#!/bin/sh
set -eu
. "$(dirname -- "$0")/common.sh"
test -x "$ziran"
out="$root/build/scratch/package-import"
mkdir -p "$out/src"
cp tests/package_import.zi "$out/src/main.zi"
cat > "$out/ziran.toml" <<'TOML'
[package]
name = "image-codec-import-test"
entry = "src/main.zi"
[toolchain]
git = "https://github.com/ziranlang/ziran.git"
ref = "master"
[dependencies.image_codec]
git = "https://github.com/ziranlang/image-codec.git"
ref = "master"
TOML
cat > "$out/ziran.local.toml" <<TOML
[overrides]
image_codec = "$root"
ziran = "$toolchain"
TOML
cd "$out"
"$ziran" lock --offline
"$ziran" check
"$ziran" run
"$ziran" ir --project --entry main:main -o "$out/ir" src/main.zi
"$ziran" bundle --root "$out/ir" --module-path "$out/ir" --entry main:main -o "$out/saved.zx" "$out/ir/main.zir"
test "$("$zi2zx" run --vm "$out/saved.zx")" = 0
"$ziran" build --target=c --exe --entry main:main --root "$out/ir" --module-path "$out/ir" -o "$out/saved-native" "$out/ir/main.zir"
"$out/saved-native/main"
printf '%s\n' 'image-codec ordinary package import: local override, exports, source/saved IR and native/direct VM passed'
