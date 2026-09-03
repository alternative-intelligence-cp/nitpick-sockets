# `src/sys/` — the syscall vocabulary

The x86-64 socket syscall numbers and the kernel constants, each carrying the
header it came from. **Declares no error of its own** — every failure is an
errno, forwarded verbatim. Governed by `../../meta/specs/SOCKET_MODEL.md` §1.
Built in cycle 0.2.0.
