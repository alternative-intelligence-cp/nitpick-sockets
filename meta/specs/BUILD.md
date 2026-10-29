# Building, testing, and the module conventions

How `nsockets` is built today, how it will be built when the tooling catches
up, and the file-and-import conventions everything in `src/` follows.

---

## 1. What cannot build this yet, measured

Read at the compiler's commit for cycle 1.5.0 (2026-09-03):

- **`npkg build` is the compiler's own bootstrap ladder.** It assembles
  `runtime/npkrt.ll` and `bootstrap/seed/stage1.ll` into a builder, has that
  builder compile `[build] entry`, scans, links, and names the result `npkc`.
  There is no generic-project path and no `target = "library"` behaviour; the
  key is accepted by the schema and read by nothing.
- **`[dependencies]` resolves to nothing.** The loader's dependency-root list
  (`RootList`, `src/frontend/resolve_path.npk`) is created empty in
  `src/driver/pipeline.npk` and `rootlist_add` is never called from anywhere,
  so a `use "nsockets/socket.npk"` path resolves against an empty set. Only
  `./` and `../` paths work.
- **`npkg` has no `install` and no `update`.**

**Decision SK-004: `harness/` builds and tests `nsockets` until `npkg` can, and
retires into it.** That is precisely the relationship `bootstrap/harness/` has
to `npkg` in the compiler repository, including the part where both run side by
side and a parity stage holds them to each other before the older one is
retired. Writing the harness in Python is not a dependency violation:
**zero-dependency governs the artifact, not the workbench** (the compiler's
`ORCHESTRATION.md` §6 says so in as many words, about valgrind).

---

## 2. The build, step by step

```
src/lib.npk  (and every module it reaches by `use`)
   → npkc              →  build/nsockets.ll      the emitted LLVM IR text
   → opt -O2           →  build/nsockets.opt.ll  only on the check leg
   → llc               →  build/nsockets.o       at the manifest's flags
   → undefined-symbol scan against the runtime allowlist
   → ld.lld -static    →  build/<program>        one program object + npkrt.o
```

**Rule B-1.** Every tool invocation is built from `nitpick.toml`'s
`[toolchain]` lists. No tool ever runs at its own defaults — `llc` defaults to
`-O2` and would optimise a build the manifest declined, which cost the compiler
project a measured 25× on one module.

**Rule B-2.** The undefined-symbol scan is a **build step, not a test**. Every
object is scanned and the build fails on any undefined symbol outside the
runtime allowlist derived from `runtime/npkrt.ll`'s own `define`s plus `main`.
For this library it earns its keep twice over: a socket library is exactly
where somebody would reach for `htons` or `inet_pton` out of habit, and the
scan is what makes "no libc, ever" a structural property rather than a
convention.

**Rule B-3.** The optimised leg runs on every program, every time: the same
program re-emitted through `opt -O2` + `llc -O2` must produce the **same exit
code**, and the zero-dependency scan is repeated on the optimised object
because `opt` may mint libcalls. This is the compiler's 1.3.8 instrument, and
its first run there found a real defect that had passed for six cycles.

**Rule B-4 — reproducibility.** Two builds of the same tree from different
working directories produce byte-identical IR. `nsockets` inherits this from
the compiler (D-078, D-204, D-236) and the harness has a `repro` stage that
measures it.

---

## 3. Test stages

The harness mirrors the compiler's stage vocabulary
(`BUILD_REFERENCE.md` §7.1) so that the eventual move to `npkg` is a change of
runner and not a change of suite.

| Stage | Directory | Passes when |
|---|---|---|
| `parse` | every `.npk` in the tree | accepted by `tools/parse_check` with no diagnostic |
| `accept` | `tests/conformance/` | accepted by `tools/check` in silence |
| `check` | `tests/rejection/` | refused by the frontend with **exactly** the expected codes |
| `program` | `tests/unit/` | emitted, scanned, assembled, linked, run at -O0 and again under `opt -O2`, the same exit both times |
| `loopback` | `tests/unit/net/` | as `program`, over `127.0.0.1` / `[::1]` / `socketpair` — **no external host, no privilege** |
| `network` | `tests/unit/extern/` | as `program`, but needs an outside host; **skipped with a loud line** when unavailable, never silently |
| `fixture` | `tests/fixtures/` | built and never run; its uppercased stem becomes an `// argv:` token |

**Rule B-5 (SK-030) — `loopback` is not `network`.** Loopback and `socketpair` need no
route, no DNS, no privilege and no outside machine, so they run in CI, in a
container, and on a laptop with the wifi off — and they cover essentially the
whole library (`TESTING.md` §2). The `network` stage is the small residue that
genuinely needs the internet, and keeping the two separate is what stops a CI
failure that means nothing.

**Rule B-6 — expectations live in the test file.** The marker grammar is the
compiler's, marker for marker:

```
// expect-exit: 7            the exit a run must produce (0 when absent)
// expect-error: NITPICK-TYPE-057
// expect-error-at: 14:9
// stress: 40                run it that many times, the SAME answer every time
// argv: …
```

**Rule B-7 — assert on codes and exit codes, never on message text.**

**Rule B-8 — unexpected diagnostics fail a test as surely as missing ones**
(D-237). The set of codes a rejection test reports must **equal** the set its
expectations name.

**Rule B-9 — the harness is itself tested.** `TESTING.md` §7.

**Rule B-10 — anything with a timing dimension runs 40 times**, not once.
`// stress: 40`. For this library that is most of it: every accept, every
connect, every ancillary round trip. Two of the compiler's most serious
defects hid behind single green runs and neither reproduced in fewer than about
twenty.

---

## 4. Dependencies

**Rule B-11 (SK-006).** `nsockets` depends on the language, its prelude, and
nothing else. `[dependencies]` is empty and stays empty until a decision says
otherwise. That includes, specifically and deliberately:

- **not the compiler's `lib/nbridge.npk`**, which is the best oracle in the
  tree for `SCM_RIGHTS` and is still not a dependency. It is compiler-internal,
  it is on its way out of that repository into an `nlibc` sibling, and it
  declares Bridge-specific errors that would land in every consumer's
  `failsafe` under REACH-002. `nsockets` reads it and writes its own.
- **not the compiler's `lib/nsys.npk`.** Same reasoning. The syscall numbers
  `nsockets` needs are x86-64 ABI facts, declared in `src/sys/` with the same
  shape `nsys` uses and with the header each came from named.
- **not a sibling library.** `nitpick-time` would be a natural source of a
  `Duration` helper and is not one; the prelude's `Duration` is what every
  deadline takes.

**Rule B-12.** The prelude is fair game and is used heavily: `Duration`,
`OwnedFd`, `own_fd`/`release_fd`, `Reader`/`Writer`, the named errnos
(`WouldBlock`, `Interrupted`, `NotFound`, `Exists`), `IoEof`,
`DeadlineExceeded`, `io_ready`/`io_ready2`, `Ordering`, and the seven derivable
traits. Every module has it bound with no import.

---

## 5. Storage primitives

**Rule B-13 (SK-005).** `nsockets` declares its own, in `src/core/`, for the
reason B-11 gives: a library must not import a compiler's internals.

- **`Vec<T>`** — `{ wild T->:items; int64:count; int64:cap; }`, the compiler's
  `List<T>` in shape because that shape is right and has been exercised across
  twenty-two families.
- **`Bytes`** — an owning byte sink over `buffer`, with `push`, `extend`,
  `put_uint`, `take`. Address formatting appends to one of these rather than
  concatenating strings (`ADDRESS_MODEL.md` A-23); the compiler measured the
  quadratic version of exactly that shape at 17 minutes of a 56-minute run.
- **`limits.npk`** — every named bound in one file.

**Rule B-14.** `nsockets` declares no other container. A collection of live
connections is an `arena<T>` with `Handle<T>` (`CONCURRENCY_MODEL.md` §4),
which is what the language provides for it.

---

## 6. Modules, files, and imports

**Rule B-15.** One module per file, and **a file's `mod:` name must equal its
basename** — the loader reports `NITPICK-RESOLVE-005` at line 1 otherwise, and
says nothing about the name.

**Rule B-16.** Public names carry their module's short prefix:
`addr_parse`, `sock_adopt`, `tcp_connect`, `unix_bind`, `scm_send_fd`. A
`pub struct` takes PascalCase (`TcpStream`, `UnixAddr`). Constants are
`SCREAMING_SNAKE`.

**Rule B-17 — imports are relative today** (§1), and a **consumer** imports
`src/lib.npk` by a relative path. `src/lib.npk` is the umbrella and re-exports
the public surface deliberately, one line per name, because `use` is not
transitive (`MODULE_REFERENCE.md` §2.3) — which makes the public surface a list
in one file that a reviewer can read.

**Rule B-18 — the layering, and the direction of every arrow.**

```
     server ──► stream ──┐
                         ├──► socket ──► sys ──┐
   datagram ─────────────┤        │            │
                         │        ▼            ▼
  ancillary ─────────────┘     option        core
                         │                     ▲
                         └──► addr ────────────┘
```

`core` depends on nothing. `sys` depends on `core`. `addr` depends on `core`
and on nothing else — which is what makes it importable by a program that never
opens a socket (`SAFETY.md` S-8). A module may not import a module to its left.

**Rule B-19 — a `use` cycle is legal** (D-086) and is still a decomposition
mistake. The harness has a check.

---

## 7. Reserved words that will bite

The compiler's list, filtered to the ones a socket library reaches for:

| Wanted as a name | Actually |
|---|---|
| `fd` | one of the five kernel identifier **types** (D-042) |
| `buffer` | the owning byte cell **type** |
| `raw` | the unwrap keyword — and `raw` sockets are a thing this domain talks about |
| `move`, `drop`, `pass`, `fail`, `relay`, `give`, `pick`, `fall` | keywords |
| `end` | the `when`/`then`/`end` terminator |
| `in` | the `for … in` keyword — and "in" is the natural name for an inbound buffer |
| `limit` | the verification keyword — and a backlog limit wants it |
| `any` | the type — and `INADDR_ANY` is a thing |
| `on` | a keyword |
| `error` | the declaration keyword; `Result`'s field is `.err` |
| `thread`, `atomic`, `joins`, `gives` | concurrency keywords (`channel` is not one: the keyword is the type, `Channel`) |
| `unit` | the unit-declaration keyword |
| `oflags`, `prot`, `mflags`, `fmode` | the four flag-family type keywords |
| `is`, `is_err`, `defaults`, `as`, `with`, `where`, `never`, `fails` | keywords |
| `pid`, `uid`, `gid`, `tid` | keywords — and `ucred`'s three fields want the first three (`cpid`, `cuid`, `cgid`) |
| `old`, `result`, `release`, `acquire`, `range`, `stack`, `cfg`, `arena`, `hidden`, `sealed`, `decreases`, `unbounded` | keywords — `old` is the name a saved disposition reaches for (`prior`) |

*(Measured 2026-10-29 at compiler `2e1cb4a`, SK-102: every word in this table checked against the pin's
`src/frontend/keywords.npk`, 170 words, the same at `7e91730`; from the compiler's landing 113 a keyword declared as
a name of ANY kind — a field, a parameter, a module — is `NITPICK-PARSE-001`. The row naming `channel` among the
keywords was wrong: it is not one.)* **A name the prelude declares cannot be declared again** —
`fixed int64:O_CLOEXEC = …;` is `NITPICK-RESOLVE-001` — so the prelude's `O_*`, `S_*`, `MAP_*` and `PROT_*`
names are not this library's to define, and a constant that wants one takes another (`PIPE_CLOEXEC`).

**The names this library uses instead**, fixed here so they are used
consistently: `descr` for a raw descriptor number; `sock` for a `Sock`; `sink`
for a byte destination and `src` for a byte origin; `wire` for a byte slice
crossing the kernel boundary; `hi` for an upper bound; `backlog_max` rather
than `limit`; `addr_any` rather than `any`; `cap` for a buffer capacity (not a
capability — this library has none).

---

## 8. Three more shapes that are not what a C or Rust habit expects

- **Adjacent string literals do not concatenate.** `"a" "b"` is two literals.
- **`discard(expr);` takes parentheses; `defer { … }` takes no trailing
  semicolon.** Both wrong forms are parse errors.
- **Struct/trait/impl/function declarations end `};`. Control-flow blocks do
  not.**

---

## 9. Open items

- **O-B1 — when `npkg` can build a library.** Gated on the compiler; tracked as
  `O-N2` in `../OPEN_QUESTIONS.md`.
- **O-B2 — whether the `network` stage should exist at 1.0 at all.** Everything
  except DNS-free outbound connectivity can be tested on loopback, and a stage
  that is skipped on every developer machine is a stage nobody trusts.
  **Recommendation:** keep it, with exactly two tests in it (an outbound TCP
  connect to a caller-supplied host:port, and an IPv6 one), so that it is small
  enough to run by hand when it matters.
