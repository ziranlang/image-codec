#!/bin/sh
# Build-producing callers run under build-queue. No display is used.
set -eu
unset DISPLAY WAYLAND_DISPLAY WAYLAND_SOCKET XAUTHORITY DBUS_SESSION_BUS_ADDRESS DBUS_SYSTEM_BUS_ADDRESS SESSION_MANAGER
unset XDG_SESSION_ID XDG_SESSION_TYPE XDG_SESSION_CLASS XDG_SESSION_DESKTOP XDG_CURRENT_DESKTOP XDG_RUNTIME_DIR
unset DESKTOP_SESSION DESKTOP_STARTUP_ID ICEAUTHORITY SSH_AUTH_SOCK ZIRAN_PROFILE
export ZIRAN_DESKTOP_RECOVERY=0 HARMONY_DESKTOP_RECOVERY=0 YUE_DESKTOP_RECOVERY=0
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
toolchain=${ZIRAN_ROOT:-$root/../../ziran}
ziran=${ZIRAN:-$toolchain/build/bin/ziran}
zi2zx=${ZIRAN_ZX:-$(dirname -- "$ziran")/zi2zx}
mkdir -p "$root/build/scratch/tmp" "$root/build/bin" "$root/build/cache"
export TMPDIR="$root/build/scratch/tmp" XDG_CACHE_HOME="$root/build/cache" ZIRAN_NATIVE_CACHE="$root/build/cache/native"
export GOTOOLCHAIN=local GOMAXPROCS=2 GOFLAGS=-p=2
ulimit -c 0
cd "$root"
