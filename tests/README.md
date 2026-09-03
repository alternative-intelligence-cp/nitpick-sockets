# `tests/`

| Directory | Stage | Contents |
|---|---|---|
| `probe/` | `program` | the cycle-0.0 language and kernel probes; **never deleted** |
| `conformance/` | `accept` | the public API compiles in a program that only imports it |
| `unit/` | `program` | the pure layers, judged by exit code |
| `unit/net/` | `loopback` | the socket layers, over `socketpair` and `127.0.0.1` |
| `unit/extern/` | `network` | the two tests that need an outside host |
| `rejection/` | `check` | programs the compiler must refuse, with exactly the expected codes |
| `fixtures/` | `fixture` | captured wire bytes and fuzz corpora, byte-stable |

Every test binds to **port 0** and uses the **abstract namespace** for
`AF_UNIX`. Expectations live in the test file. Governed by
`../meta/specs/TESTING.md`.
