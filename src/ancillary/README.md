# `src/ancillary/` — control data

The one `msghdr` in the library, `SCM_RIGHTS` descriptor passing and
`SCM_CREDENTIALS` peer identity. Declares **`ESockProtocol`** and nothing else
does. The library's only parser of attacker-adjacent binary data, and the
reason the fuzzer exists. Governed by `../../meta/specs/ANCILLARY_MODEL.md`.
Built in cycle 0.5.
