# Cycle 0.0 — Foundations

**The probes, the harness, and `src/core/`.** Nothing in this cycle opens a
socket in anger. What it produces is the ability to find out whether the rest
of the plan is buildable, and the machinery every later cycle is tested by.

## Why this shape

Two of the compiler project's most expensive lessons decide this cycle's
contents:

- **"A construct that parses is not a construct that works."** Its cycle 0.4
  was mostly repair, and every repair dated to the cycle that had parsed the
  construct. **Two of this library's foundations were read out of compiler
  source rather than run**: that `SIGPIPE` is lethal because nothing installs a
  disposition (`SK-013`), and that an `OwnedFd` is refused as a channel element
  but may be moved into a spawn (`SK-035`). Both are load-bearing for the whole
  design. 0.0.0 runs them.
- **"Diagnostics come first, not last — they are how every later cycle is
  tested."** Here that is the harness. A suite written after the code is a
  suite shaped by the code.

## Decisions in

`SK-001`, `SK-002`, `SK-004`, `SK-005`, `SK-006`, `SK-007`, `SK-013`,
`SK-016`, `SK-035`. All settled. **Nothing in this cycle is blocked on a
question.**

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| [0.0.0](0.0.0.md) | **The language probes** — twelve programs asking the compiler whether the design is spellable, two of them load-bearing | a recorded verdict per probe, and any design change the answers force |
| [0.0.1](0.0.1.md) | **The skeleton** — the module layout, `src/lib.npk`, the manifest's test table, CI | `npkc` compiles an empty library and a program that imports it |
| [0.0.2](0.0.2.md) | **The harness, part 1** — build, the `program` stage, the toolchain pin | one test program builds, links, runs, and its exit code is judged |
| [0.0.3](0.0.3.md) | **The harness, part 2** — `parse`, `accept`, `check`, `loopback`, `network`; the self-check; the tree checks | the self-check proves the harness can fail, seven ways |
| [0.0.4](0.0.4.md) | **`src/core/`** — `Vec<T>`, `Bytes`, `limits.npk` | the primitives, with their suites and their obligations written |
| [0.0.5](0.0.5.md) | **Close** — the findings, the spec amendments the probes forced, the handoff to 0.1 | `done/0.0/`, and 0.1 openable by a fresh session |

## Checklist

### 0.0.0 — the probes
- [ ] `probe/probe01_sys_socket.npk` — `socket()` with `SOCK_NONBLOCK|SOCK_CLOEXEC` through `sys`, then `socketpair`, asserting both descriptors are ≥ 3 and non-blocking
- [ ] `probe/probe02_sockaddr_layout.npk` — `sockaddr_in` (16), `sockaddr_in6` (28), `sockaddr_un` (110) laid out in a `buffer`, `bind`ed, `getsockname`ed back, compared field by field, with a sentinel one byte past the end untouched
- [ ] `probe/probe03_cmsg_layout.npk` — `msghdr` (56), `iovec` (16), `cmsghdr` (16), `ucred` (12) asserted; a `sendmsg`/`recvmsg` round trip over a `socketpair` with no ancillary payload
- [ ] **`probe/probe04_sigpipe.npk` — a send to a closed peer WITHOUT `MSG_NOSIGNAL`, in a child, asserting the child died of signal 13; and WITH it, asserting `EPIPE` in `Result.err`** — the probe that proves `SK-013` is load-bearing
- [ ] `probe/probe05_ownedfd_drop.npk` — `own_fd` on a socket, scope exit, and `/proc/self/fd` showing it closed; then `release_fd` + explicit `close` observing the verdict
- [ ] `probe/probe06_reader_writer.npk` — a struct holding an `OwnedFd` implementing the prelude's `Reader` and `Writer`, driven through a generic bound and through `dyn`
- [ ] `probe/probe07_io_ready.npk` — `io_ready` on a socket for `EPOLLIN` and `EPOLLOUT`, and `io_ready2` over two descriptors, with a deadline that expires
- [ ] `probe/probe08_connect_inprogress.npk` — a non-blocking connect to a **closed** port on loopback: `EINPROGRESS`, wait writable, `SO_ERROR` == `ECONNREFUSED`, and a second `SO_ERROR` read returning 0
- [ ] **`probe/probe09_ownedfd_channel.npk` — an `OwnedFd`, and a struct holding one, as a channel element; expected REFUSED `NITPICK-TYPE-057`, with the diagnostic recorded verbatim**
- [ ] **`probe/probe10_ownedfd_spawn.npk` — an `OwnedFd` MOVED into a spawned task; expected ACCEPTED — and a BORROW of one across a spawn; expected refused** — together these two are `SK-035`
- [ ] `probe/probe11_scm_rights.npk` — a descriptor passed over a `socketpair` with `MSG_CMSG_CLOEXEC`, used at the far end, and its `FD_CLOEXEC` asserted set
- [ ] `probe/probe12_pod_addr_array.npk` — a `Vec<SocketAddr>`-shaped array of 128-byte POD values: fill, read, copy, and a `#size_of` assertion
- [ ] a verdict line per probe recorded in `0.0.0.md`, with the exact diagnostic where one was refused
- [ ] every design consequence written into `meta/specs/` **and** `meta/DECISIONS.md` before 0.0.1 starts

### 0.0.1 — the skeleton
- [ ] `src/lib.npk` exists and `pub use`s nothing yet (`use` is not transitive, so the surface is a deliberate list)
- [ ] every `src/` subdirectory has a placeholder module that parses, so the `parse` stage has something to sweep
- [ ] `nitpick.toml`'s `[[test]]` table has its first entries
- [ ] a consumer program under `tests/conformance/` imports `src/lib.npk` by relative path and compiles
- [ ] CI: a workflow running `harness/run.py` on push, with LLVM 20.1.2 and the compiler at a **pinned commit**
- [ ] `CLAUDE.md` and `CONTRIBUTING.md` re-read against 0.0.0's verdicts and extended

### 0.0.2 — the harness, part 1
- [ ] `harness/run.py`: the manifest reader, the toolchain pin check, the module-graph walk
- [ ] the build pipeline — `npkc` → `opt` (check leg) → `llc` → the undefined-symbol scan → `ld.lld`
- [ ] the undefined-symbol scan as a **build step**, not a test (B-2) — and it earns its keep here: a socket library is exactly where somebody reaches for `htons`
- [ ] the `program` stage at -O0 and again under `opt -O2`, same exit required (B-3)
- [ ] `// expect-exit:`, `// stress: N`, `// argv:` honoured
- [ ] **`// expect-signal: N`** — the one marker this library adds to the compiler's grammar, for probe 04 (`TESTING.md` V-6)
- [ ] the `repro` check: two builds from different working directories, byte-identical IR
- [ ] one real test program green

### 0.0.3 — the harness, part 2
- [ ] the `parse` stage over every `.npk` in the tree, each file once
- [ ] the `accept` and `check` stages with the **exact-code** rule (B-8)
- [ ] the `loopback` stage
- [ ] the `network` stage, skipped **loudly** with its reason when unavailable (V-2)
- [ ] `--only`, and output that says twice that a filtered run concludes nothing
- [ ] `harness/selfcheck.py` with all seven cases from `specs/TESTING.md` V-14
- [ ] the self-check runs **first** in every full invocation
- [ ] `check_layering` — every `use` edge against `specs/BUILD.md` §6's diagram
- [ ] `check_error_budget` reading `specs/SAFETY.md` §3's table
- [ ] `check_constants_named`, `check_no_hardcoded_port`, `check_struct_sizes` (each with nothing to check yet, which is the right answer, not a reason to skip)
- [ ] **`check_msg_nosignal` and `check_no_floor_write` and `check_no_raw_setsockopt` written now**, even though `src/` has no send site yet — they go live the day 0.2 writes one, and writing them before there is anything to grep is what stops the first site being the exception

### 0.0.4 — `src/core/`
- [ ] `src/core/limits.npk` — every named bound in one file: `NSOCK_CMSG_MAX`, `NSOCK_SCM_MAX_FDS`, `NSOCK_EMFILE_BACKOFF`, `NSOCK_POLLSET_MAX`, and the deadline defaults
- [ ] `src/core/vec.npk` — `Vec<T>`: `init`, `reserve`, `push`, `pop`, `at`, `set`, `truncate`, `clear`, `free`
- [ ] `Vec<T>` exercised at both `T` shapes: a scalar and an owning value with `move T:v`
- [ ] `src/core/bytes.npk` — `Bytes`: `init`, `push`, `extend`, `put_uint`, `len`, `view`, `take`, `clear`, `free`
- [ ] `put_uint` allocation-free and correct at 0, 1, 9, 10, 99, 100, and `uint64` maximum
- [ ] `Bytes` growth amortised linear, proven by a test that appends a million bytes and bounds the reallocation count
- [ ] every accessor's bounds obligation written as a comment in the `requires`/`ensures` syntax it will take (`specs/VERIFICATION.md` Z-1)
- [ ] property tests standing in for each written obligation

### 0.0.5 — close
- [ ] every probe verdict recorded, every forced spec amendment landed
- [ ] the harness self-check green, the full run green
- [ ] `meta/DECISIONS.md` updated with anything the probes settled
- [ ] `0.1/0.1.0.md` written execution-grade before the cycle closes
- [ ] cycle moved to `done/0.0/`

## Gate

**The cycle is complete when**: a full `harness/run.py` is green; the
self-check proves the harness fails seven ways; `src/core/` has its suites; and
every probe has a recorded verdict — **with probes 04, 09 and 10 confirming
`SK-013` and `SK-035`, or the specifications amended to match what they
actually found.**

## Watch for

- **Probe 04 is the one to run first**, and it is the one whose *failure* would
  be the most interesting result in the cycle. If `SIGPIPE` turns out not to be
  lethal — because a future runtime ignores it at `_start`, or because the
  executor's own machinery masks it — then `SK-013` becomes belt-and-braces
  rather than essential, and that is worth knowing before the rest of the
  library is written around it. Either way it is a **finding**, recorded, not a
  reason to change the rule: `MSG_NOSIGNAL` costs nothing and stays.
- **Probes 09 and 10 must be run as a pair**, because the interesting fact is
  the *asymmetry*. Either alone is half the story, and the half that is missing
  is the one that decides the server model.
- **A probe that fails is a finding, not an obstacle.** Record the exact
  diagnostic, decide the design change, amend the specification, and only then
  continue. Working around a compiler refusal in library code is what the
  compiler's R6 forbids.
- **The reserved words** in `specs/BUILD.md` §7 will bite immediately: a probe
  about sockets wants locals called `fd`, `raw`, `in`, `any` and `buffer`, and
  none of them is available.
- **`Vec<T>` is `wild` storage** and every path out of a function that took some
  must release it, or `exit 0` traps under D-151. Every probe and every suite
  program exits 0 on purpose, so a leak on any path turns a pass into a trap.
