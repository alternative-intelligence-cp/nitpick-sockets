# `harness/` — the build and test runner

Python, because `npkg` cannot build a library yet
(`../meta/specs/BUILD.md` §1) and zero-dependency governs the artifact, not the
workbench. It retires into `npkg` the way `bootstrap/harness/` does in the
compiler repository. Built in cycles 0.0.2 and 0.0.3.

It carries no marker the compiler's grammar does not. *(2026-10-29: it was to
carry `// expect-signal: N`, for the `SIGPIPE` test, which SK-101 retires —
at compiler `2e1cb4a` that test's send answers `EPIPE`, and nothing in the
suite dies by a signal.)*
