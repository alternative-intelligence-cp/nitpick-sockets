# CLAUDE.md

Guidance for Claude Code sessions working in this repository.

## What this is

`nsockets` — a BSD sockets library for **Nitpick**, the safety-critical systems
language at `../../nitpick`. **Status: planning.** No library code exists yet.
The specifications and the plan do.

## Read these first, in this order

1. **`meta/specs/SAFETY.md`** — the constraints and where they come from. Most
   proposals that look reasonable in the abstract die on one of §1's rules.
2. **`meta/specs/README.md`** — the index and the reading order for the rest.
3. **`meta/DECISIONS.md`** — every settled design decision with its reasoning.
   **Read this before proposing a change**, because it is recorded why.
4. **`meta/roadmap/ROADMAP.md`** — the cycle map; then the current cycle's
   `README.md`.
5. **`meta/OPEN_QUESTIONS.md`** — what is not settled, each with a
   recommendation.

`../PLAYBOOK.md` (beside the library checkouts) is the shared house style for
every Nitpick library, if you have the sibling checkouts.

## The two rules this library exists around

**1. Every send carries `MSG_NOSIGNAL`** (`SK-013`). The Nitpick runtime
installs **no** signal disposition — a search of `runtime/npkrt.ll` finds no
`rt_sigaction` — so `SIGPIPE`'s default is live and its default is to terminate
the process. The compiler's own Bridge records the consequence: *"the first
EPIPE schedule proved it by taking the whole process down."*

The corollary that will be broken by accident: **this library does not use the
runtime floor's `write` on a socket**, and neither may an impl of the prelude's
`Writer`. `impl:ByteWriter:Writer` in the prelude *does* use it and looks like
the thing to copy — it writes to a file, where the hazard does not exist.
`check_msg_nosignal` greps every send site with a whitelist of zero.

**2. A connection cannot cross a channel, but can be moved into a spawn**
(`SK-035`). `chan_elem_verdict_recorded` refuses `TY_OWNEDFD` as a channel
element (`NITPICK-TYPE-057`), transitively for any struct holding one;
`type_holds_pointer` in `escape.npk` answers `false` for it, so a **move** into
a spawned task is legal. Together they make **accept-then-spawn the only
expressible server model** — a worker pool pulling connections off a queue is
unspellable, and correctly so.

## The other rules that are not negotiable

- **The specifications are the authority** (`SK-002`). Code that disagrees with
  `meta/specs/` is a defect in the code. A specification that turns out to be
  wrong is amended by a decision recorded in `meta/DECISIONS.md`, in the same
  commit.
- **A settled decision's text is never rewritten.** Supersede it with a new
  numbered decision that says why.
- **Four public error identities, and four is a ceiling** (`SK-015`).
  REACH-002 makes every one an arm every consuming program's `failsafe` must
  name. Kernel errnos are **forwarded verbatim** and cost nothing — that is why
  the budget can be four rather than forty.
- **No dependencies** (`SK-006`). Not the compiler's `lib/nbridge.npk`, which
  is the best `SCM_RIGHTS` oracle in the tree and is still not a dependency.
  Read it; do not import it.
- **Every socket is created non-blocking and close-on-exec atomically**
  (`SK-012`), in the `socket()`/`socketpair()`/`accept4()` call. Never a
  follow-up `fcntl`.
- **Never work around a compiler defect.** Record the reproduction, stop, and
  raise it. This is the compiler's own R6.

## The compiler constraints that shape everything

Full statement in `meta/specs/SAFETY.md` §1. The ones that bite hardest here:

- `defer` does **not** run on a trap; `failsafe` is the only code guaranteed to
  run. For sockets that is harmless (`SK-033`) — the kernel reclaims
  descriptors — and it is why this library has no restore registry.
- Owning values are **move-only**; borrows are second class and never escape.
- Plain integer overflow **traps**; indexing traps; division by zero traps.
- Every blocking operation carries a **mandatory deadline**, and every wait is a
  task suspension through the reactor.
- There is **no `select`** across channels — fan-in is `io_watch` plus one
  `suspend_io`.
- An `async` function can never be `never fails`, so `raw await …` is
  unspellable; use `relay`, `?|` or `?!`.

## Reserved words that read like ordinary names

`meta/specs/BUILD.md` §7 has the table. The ones this domain wants most:
`fd`, `raw`, `in`, `any`, `buffer`, `move`, `end`, `limit`, `error`, `on`,
`thread`, `channel`, `atomic`, `is`, `is_err`, `never`, `fails`, `with`,
`where`, `as`, `mod`, `unit`, `oflags`, `prot`, `mflags`, `fmode`.

**The substitutes this library uses**, so the tree stays consistent: `descr`
for a raw descriptor number; `sock` for a `Sock`; `sink`/`src` for a byte
destination and origin; `wire` for a byte slice crossing the kernel boundary;
`hi` for an upper bound; `backlog_max` rather than `limit`; `addr_any` rather
than `any`; `cap` for a buffer capacity.

Three shapes that surprise a C or Rust habit: adjacent string literals do not
concatenate; `discard(x);` takes parentheses and `defer { … }` takes no
trailing semicolon; declarations end `};` and control-flow blocks do not.

## Building and testing

**`npkg` cannot build this yet** (`meta/specs/BUILD.md` §1): it is the
compiler's own bootstrap ladder, and `[dependencies]` resolves to nothing.
`harness/run.py` is the runner until that changes (`SK-004`). Until cycle 0.0.2
lands it, probes are run by hand — `meta/roadmap/0.0/0.0.0.md` §2 has the
command.

Almost the whole suite runs over `socketpair` and loopback: no network, no
port, no privilege. The `network` stage is two tests and is skipped loudly.

The compiler is at `../../nitpick`. Build it per its own `CLAUDE.md`. LLVM
20.1.2 exactly; `llvm-config --version` to check.

## Where things go

```
src/       the library, Nitpick only, layered per meta/specs/BUILD.md §6
tests/     probe, conformance, unit, rejection, fixtures
harness/   the Python build and test runner, until npkg can
tools/     generators and instruments
examples/  runnable demonstrations, built and run by the harness
docs/      user-facing documentation, written at cycle 1.0
meta/      specs, decisions, open questions, the roadmap, research
.internal/ gitignored scratch — never commit anything from here
```

## When you find something

- A **compiler defect**: record the reproduction, stop, raise it. Do not work
  around it.
- A **specification error**: fix the specification and record the decision, in
  the same commit as the code that revealed it.
- A **finding that is neither**: write it into the current subcycle's execution
  record. This project's execution records are load-bearing.
