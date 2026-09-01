# Atlaso CPython 3.14 compatibility wheel

This fork publishes a temporary Windows x86-64 CPython 3.14 wheel for
`onepassword-sdk 0.4.1` on behalf of the Atlaso project. It is not an official
1Password release and is never uploaded to PyPI.

The release workflow rebuilds the exact PyPI source distribution twice on
independent hosted Windows runners, requires byte-identical output, compares
the packaged DLL and generated UniFFI binding with the official CPython 3.13
wheel, scans the candidate, emits an SPDX SBOM, and records GitHub build
provenance. The package name and version remain unchanged.

The release exists only until 1Password publishes an official
`cp314-cp314-win_amd64` wheel that satisfies Atlaso's dependency maturity
policy. Upstream support is tracked by
[1Password/onepassword-sdk-python#244](https://github.com/1Password/onepassword-sdk-python/issues/244),
and Atlaso integration is tracked by
[mdaneri/Atlaso#610](https://github.com/mdaneri/Atlaso/issues/610).

The source and included binaries remain subject to the upstream MIT license
and 1Password API terms. The compatibility release does not imply endorsement
or support by 1Password.
