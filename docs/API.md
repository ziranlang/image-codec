# Decoder foundation

Import `image_codec/api` (dependency alias `image_codec`). Standalone tests
pass `--module-path image_codec=src` and
`--module-path std="$ZIRAN_ROOT/std"`. The named standard
library path separates this package's `image` module from `std/image`.

## Result and ownership

`DecodeResult` contains `is_ok`, `image: std/image.Image`, `metadata:
ImageMetadata`, and `error: DecodeError`. Check `is_ok` before reading output.
`DecodeFailure(error)` returns no pixels. `AllocateImage(metadata,limits,token)`
returns a fallible, zero-filled, tight RGBA8 image; it does no decoding. The
owned Vec storage uses one bulk `VecResizeBounded(storage,bytes,bytes)` and drops
automatically. Its backing capacity equals the requested byte count, including
non-power-of-two images; allocator overhead/RSS are not covered by this bound.
Cancellation is checked before/after allocation. Move a result or its image once;
explicitly clone for an independent copy. No alternate pixel type is defined.

`BorrowedBytes { data: []u8 }` and `BorrowBytes(data)` borrow input synchronously.
`ByteRange(input,offset,count)` checks signed bounds before slicing and returns
`(BorrowedBytes, DecodeError)`. Ziran's mutable slice is not const: the caller
keeps backing storage alive and unchanged until every decoder/view returns.

`Plane` owns `storage: Vec(u8)` and describes `width`, `height`, byte `stride`
and `sample_bytes`. `PlaneView` has the same layout and borrowed `data: []u8`.
A plane holds one component, with 1-byte or little endian 2-byte samples.
`ValidatePlane(view,limits)` checks layout, span and dimension/working-byte
limits; it does not infer subsampling or bit depth. Construct a view from live
caller-owned storage. Current `VecSlice` cannot borrow arbitrary pointer-backed
Vec fields, so no unsafe automatic pointer-to-plane view helper is promised.

`OutputBuffer { data: []u8, stride: s64 }` borrows caller-owned RGBA8 output.
`ValidateOutput(output,width,height,limits)` allows padding and requires
`(height-1)*stride + width*4` bytes. `CopyImageToOutput(image*,output,limits,token)`
leaves padding untouched, validates before writing, and checks cancellation per
row. Source and destination must not overlap. Cancellation during work can
leave complete rows written; pre-cancellation and invalid layout write nothing.
This borrowed buffer never becomes the owned `DecodeResult.image`.

## Limits and metadata

`DefaultLimits()` sets 256 MiB input, 32768 per dimension, 67108864 pixels,
256 MiB output, 512 MiB engine scratch, 1 MiB metadata, 4096 source frames,
one decoded frame and one worker. Caps are positive except
`max_metadata_bytes`, which may be zero. Zero never means unlimited.
`ValidateLimits`, `ValidateInputSize`, `ValidateDimensions`, `ValidateMetadata`
and `ValidateDecodedFrames` return structured errors.
`RequiredSpan(width,height,sample_bytes,stride)` checks multiplication overflow.
Scratch, metadata, input and output are separate budgets, not a process RSS
guarantee. Providers reserve engine scratch and enforce container/metadata caps
before allocation.

`ImageMetadata` describes transformed output width/height, source bit depth,
alpha presence, source premultiplication, source `frame_count`, optional CICP
color fields guarded by `color_known`, and retained `metadata_bytes`.
Zero source depth/frame count means unknown. Color fields matter only when
`color_known` is true. `frame_count` is the source total; `max_decoded_frames`
bounds requested work. A two-frame source can return one frame under defaults.
No ICC/EXIF payload, HDR rendering, animation playback, transform interpretation
or color conversion is implemented by these records. Engines explicitly reject
unsupported features.

## Workers and cancellation

`DecodeOptions { limits, cancellation: *Cancellation, workers: *WorkerBudget,
color_mode }` is made with `DefaultOptions()`. `ValidateOptions` checks limits,
the optional worker budget, color mode, then cancellation. Null cancellation
means none; null workers means serial caller execution. Both pointed-to values
must outlive every operation using them.

`Cancellation { requested: bool }`, `Cancel(token*)` and
`CancellationError(token*)` provide cooperative checkpoints. This state is
single-threaded and non-atomic. Threaded engines adapt their atomic tokens or
serialize access; they cannot read/write this flag concurrently.

`NewWorkerBudget(limits)` counts every execution lane including the caller.
`AcquireWorker`/`ReleaseWorker` enforce the cap and update `peak_workers`.
`ReserveWorkingBytes`/`ReleaseWorkingBytes` track scratch and
`peak_working_bytes`. Failed reservations leave counts unchanged. Providers
release successful leases on every exit. These accounting helpers launch no
threads and supply no allocator or locks. Concurrent access needs provider
synchronization.

## Providers and errors

`DecodeProcedure` is an ordinary procedure type:

```zi
(input: BorrowedBytes, metadata: ImageMetadata,
 options: *DecodeOptions) -> DecodeResult
```

A container codec can expose its own parsing facade and adapt to this procedure
without a global plugin registry. `DecodeRGBA8` handles already decoded tight
RGBA8 bytes, checks exact length, depth 8, straight alpha, limits and cancellation,
and returns independent owned pixels. It leases one worker when supplied.
`StrictColor` is supported. `FastColor` and other source representations return
`UnsupportedCapability`. It does not identify or decode encoded formats.

`DecodeError { code: s32, offset: s64 }` carries a byte offset or -1 when unknown.
Use `Error(code,offset)` and `ErrorText(code)`. Codes are `DecodeOK`,
`InvalidLimits`, `InvalidInput`, `TruncatedInput`, `MalformedInput`,
`UnsupportedCapability`, `LimitExceeded`, `OutputTooSmall`, `DecodeCancelled`,
`AllocationFailed`, `WorkerBudgetExceeded`, `InputOutputFailed` and
`CorrectnessMismatch`. Unknown codes return "unknown error" text.
`DecodeFailure(Error(DecodeOK))` becomes `InvalidInput`.

Native tests inject one failed allocation and verify `AllocationFailed`, empty
output and one bulk allocation attempt. Limit/overflow failures also pass.
This is deterministic allocator fault injection, not OS out-of-memory recovery;
Go may terminate on physical exhaustion.

## Example

```zi
#import "image_codec/api"
options := DefaultOptions()
workers := NewWorkerBudget(options.limits)
options.workers = *workers
metadata: ImageMetadata
metadata.width = 1; metadata.height = 1
metadata.source_bit_depth = 8; metadata.frame_count = 1
rgba: [4]u8 = .[20, 40, 60, 255]
result := DecodeRGBA8(BorrowBytes(rgba[:]), metadata, *options)
// Check result.is_ok; result.image owns pixels until moved or dropped.
```
