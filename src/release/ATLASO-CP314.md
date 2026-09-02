# Atlaso CPython 3.14 compatibility wheel

This fork publishes temporary standard CPython 3.14 wheels for
`onepassword-sdk 0.4.1` on behalf of the Atlaso project. The compatibility
matrix mirrors every platform shipped by upstream 0.4.1:

- Windows x86-64;
- macOS x86-64 and ARM64; and
- manylinux 2.32 x86-64 and AArch64.

These are not official 1Password releases and are never uploaded to PyPI.

The release workflow rebuilds the exact PyPI source distribution twice with
CPython 3.14.7 for each target on native hosted runners and requires
byte-identical output. Pinning the patch release prevents runner image rollout
timing from changing the recorded build runtime between replicas. It
compares each packaged native library and generated UniFFI binding with the
matching official CPython 3.13 wheel, performs a native import and FFI contract
check, scans all verified inputs, extracted files, native libraries, and
completed wheels, emits one aggregate SPDX SBOM, and records canonical GitHub
build provenance. The package name and version remain unchanged.

The compatibility release exists only until 1Password publishes the eligible
official CPython 3.14 wheel set. The immutable Windows-only `.1` release remains
available for existing consumers; the complete five-target matrix is published
under the new immutable `.2` release. Upstream support is tracked by
[1Password/onepassword-sdk-python#244](https://github.com/1Password/onepassword-sdk-python/issues/244),
and Atlaso integration is tracked by
[mdaneri/Atlaso#610](https://github.com/mdaneri/Atlaso/issues/610).

The source and included binaries remain subject to the upstream MIT license and
1Password API terms. The compatibility release does not imply endorsement or
support by 1Password. Sanitized desktop authorization and Environment access
evidence is recorded for the Windows artifact. The hosted macOS and Linux
builds validate imports, native-library loading, and the UniFFI contract without
accessing secrets.
