# `tests/probe/` — the language and kernel probes

Small programs, one question each, asking the compiler whether a shape `meta/specs/` depends on is spellable and
correct, and the kernel whether a layout or a behaviour is what the specifications say. Cycle 0.0.0 wrote and ran
them at compiler `c9baa9e`; its file, `meta/roadmap/0.0/0.0.0.md` (from cycle 0.0's close,
`meta/roadmap/done/0.0/0.0.0.md`), records every verdict.

**They stay, permanently.** A probe is a regression test for a fact this library is built on, so a compiler or
kernel change that breaks one is caught here rather than by a server misbehaving in a later cycle. **A probe is never
deleted**; one whose answer changes is re-measured, and the specification follows (`SK-002`).

## Two kinds, two directories

- **`tests/probe/`** — programs that run. Each states its expected exit in its first line, `// expect-exit: N`, and
  exits with that code at `-O0` and through `opt -O2`; every assertion it fails has a code of its own, below 60, so a
  failure names itself. Probe 12 exits with the size it measures (32); every other one exits 0, which also asserts,
  through D-151, that no `wild` byte leaked. Probes 07 and 08 have a timing dimension and run forty times.
- **`tests/probe/refused/`** — programs the compiler refuses on purpose. Each states the refusal in its first line,
  `// expect-error: NITPICK-<CODE>`, and its verdict is that code at its site and nothing else.

A compiler defect a probe finds would go in a third directory, `tests/probe/defect/`, with its controls: none exists
at the pin.

## The arm codes

Every program's `failsafe` names the floor's six and what its code reaches, with the ecosystem's one convention
(`PLAYBOOK.md` §3 item 8 — 91 `HeapBadRequest`, 92 `HeapOom`, 93 `IntOverflow`, 94 `OutOfBounds`, 95 `Unreachable`,
96 `WildLeak`, 106 `StackExhausted`, 107 `MachineFault`, 108 `DecreasesViolated`, 99 the wildcard) and the two this
cycle adds, `DeadlineExceeded` 111 and `IoEof` 112 (SK-105).

## What the probes found

- **`SIGPIPE` is caught by the floor** (probe 04): a send to a dead peer answers `EPIPE` on the floor's runtime, and
  `MSG_NOSIGNAL` answers it under the default disposition too (SK-101).
- **The `OwnedFd` asymmetry holds** (probes 09, 09b, 10, 10b): refused as a channel element, legal to move into a
  spawn, a borrow across the spawn refused — `SK-035` as read.
- **An errno the prelude does not name is forwarded but not compared** (probes 13, 13b), so connect's protocol is
  spelled without naming `EINPROGRESS` (probe 08) and two accept-loop rows wait on the compiler (SK-104, O-N5).
- **Every layout and size is the specifications'** (probes 01, 02, 03, 12), the address types' sizes now stated
  (SK-102); and **every slot a reader's bytes reach is the read-only view** (probes 06, 06b, 14, 14b, SK-103).
- **No byte is read before it is written** (probe 15): an element of an array declared without an initialiser is
  `NITPICK-ASSIGN-001` where it is read, once for each of the probe's two reads, so its first two lines state the
  code twice; a parser's result carries no byte its path never wrote (`meta/specs/ADDRESS_MODEL.md` A-22's dated
  note).
