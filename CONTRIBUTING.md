# Contributing

`nsockets` is planned before it is written, and the plan is in the repository.
That is unusual and it is deliberate: the specifications catch design mistakes
that would otherwise be found by writing the wrong code twice.

## Before you write anything

Read, in this order:

1. `meta/specs/SAFETY.md` — the constraints
2. `meta/specs/README.md` — the index and the reading order
3. `meta/DECISIONS.md` — why things are the way they are
4. `meta/roadmap/ROADMAP.md`, then the current cycle's `README.md`

## The shape of a change

**Every change belongs to a subcycle.** The current cycle's `README.md` has the
checklist; a change that is not on it either goes on it or is a finding to be
recorded first.

**A specification change is a decision.** If your change requires the library to
behave differently from what `meta/specs/` says, the specification is amended
and a numbered decision recorded in `meta/DECISIONS.md`, **in the same commit**.
A settled decision's text is never rewritten — supersede it with a new one.

**Every change is green under the full harness.** `--only` is for iterating and
never for concluding.

## The four things that will surprise you

1. **Every send must carry `MSG_NOSIGNAL`.** Not "should" — the floor's runtime
   catches `SIGPIPE`, so on it a plain send to a dead peer answers `EPIPE`, but
   under the default disposition, which a host may restore, the same send
   terminates the process (a mutant of probe 04, cycle 0.0.0's block 0b). `check_msg_nosignal` greps every `sendto`/`sendmsg` site in
   `src/` with a whitelist of zero, and it will catch you. Do not use the
   runtime floor's `write` on a socket, and do not copy the prelude's
   `ByteWriter` impl, which does.

2. **A connection cannot be sent through a channel.** The compiler refuses it
   (`NITPICK-TYPE-057`), transitively for anything holding an `OwnedFd`. A
   worker pool that queues accepted connections is unspellable. Accept, then
   spawn a task and **move** the stream into it — that is legal, and it is the
   only server shape the language permits. `meta/specs/CONCURRENCY_MODEL.md` §2
   has the two compiler rules and where they live in its source.

3. **Every identity this library's code can raise becomes a mandatory `pick`
   arm in every consuming program's `failsafe`** — public or private, qualified
   by its module, beside the floor's six (SK-105). The budget is four, it is a
   ceiling, and adding a fifth is a major version. Kernel errnos are forwarded
   verbatim and cost nothing — that is the mechanism that keeps the budget
   small, and it is why `ECONNREFUSED` is not an identity.

4. **The library will not unlink your Unix socket path.** `bind` creates a
   filesystem entry that `close` does not remove, and removing files a library
   did not create is not a library's business. Use the abstract namespace, or
   call `unix_unlink` yourself. It is the one thing this library asks you to
   clean up after it.

## Tests

- **Expectations live in the test file**, as markers, and assert on codes and
  exit codes — never on message text.
- **A negative test with no expectation is a failing test.**
- **Unexpected diagnostics fail a test as surely as missing ones.**
- **Bind to port 0 and read the port back.** No hardcoded ports; a tree check
  greps for them.
- **Use the abstract namespace for `AF_UNIX` tests.** Nothing to unlink, nothing
  left behind by a crash, no collision between concurrent runs.
- **Anything with a timing dimension runs forty times**, not once.
- **A red under stress is a stop sign, never a retry.**

## Compiler defects

You will find them; the library is written against a compiler that is itself
under construction. **Record the reproduction, stop, and raise it in the
compiler repository.** Do not work around it in library code: a workaround
buried here outlives the bug, is never removed, and is indefensible at
verification time.

## Style

Match the surrounding code. Public names carry their module's short prefix;
types are PascalCase; constants are SCREAMING_SNAKE. `meta/specs/BUILD.md` §7
lists the reserved words that read like ordinary names and the substitutes this
library uses instead — use those.
