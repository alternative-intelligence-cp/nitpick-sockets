# Testing

The instruments. The compiler project's recurring finding is that **the checks
that diff two lists found the holes and the tests did not**, and that a suite
which only ever agrees with what it is handed reports green while checking
nothing. This document is `nsockets`' answer to both.

---

## 1. The stages

[`BUILD.md`](BUILD.md) §3 lists them; this is what each is *for*.

| Stage | Answers |
|---|---|
| `parse` | every source in the tree is readable by the real parser |
| `accept` | the public API compiles in a program that only imports it |
| `check` | every documented refusal actually refuses, with exactly its code |
| `program` | the pure layers do what they say — addresses, parsing, formatting |
| `loopback` | the socket layers do what they say, over `socketpair` and `127.0.0.1` |
| `network` | the two things that genuinely need an outside host |

---

## 2. `socketpair` is the substrate, and it is a strong one

**Rule V-1.** Almost the entire suite runs over `socketpair(AF_UNIX, …)` and
loopback. That is a much better position than `ntui`'s: a `socketpair` is a
**real kernel socket**, so the tests exercise the real non-blocking behaviour,
the real `EAGAIN`, the real reactor, the real `MSG_NOSIGNAL` handling, and the
real `SCM_RIGHTS` path — with no network, no port, no privilege and no outside
machine.

What `socketpair` and loopback cover:

| Behaviour | Covered by |
|---|---|
| send, receive, partial writes, `EAGAIN` | `socketpair` |
| `SIGPIPE` / `MSG_NOSIGNAL` (§3) | `socketpair`, one end closed |
| half-close and `IoEof` | `socketpair` |
| `SCM_RIGHTS`, `SCM_CREDENTIALS` | `socketpair` |
| the whole datagram path incl. truncation | `AF_UNIX` `SOCK_DGRAM` pair |
| listen, accept, `ECONNABORTED` | loopback TCP |
| `connect`'s `EINPROGRESS` path | loopback TCP, and a connect to a closed port for the failure leg |
| IPv4 and IPv6 addressing end to end | `127.0.0.1` and `[::1]` |
| socket options | any socket |

What it does not cover, and what the `network` stage is for: a route to an
external host, and a real DNS-free outbound connect over the internet. That is
**two tests**.

**Rule V-2 — a skipped `network` stage says so, loudly, on its own line, with
the reason.** A suite that silently skips is a suite that is green on a machine
where it ran nothing.

**Rule V-3 — every test binds to port 0 and reads back the port**
(`SOCKET_MODEL.md` K-14). A test with a hardcoded port fails when two runs
overlap, which is exactly what `// stress: 40` and a parallel CI do. There is no
hardcoded port anywhere in the suite and a tree check greps for one.

**Rule V-4 — every Unix-domain test uses the abstract namespace.** No
filesystem entry, nothing to unlink, nothing left behind by a test that
crashed, and no collision between concurrent runs when the name carries the
pid. `.gitignore` still excludes `*.sock` because the day somebody writes a
pathname test is the day one gets left behind.

---

## 3. The `SIGPIPE` test is the one that must exist

**Rule V-5.** A test that:

1. makes a `socketpair`;
2. closes one end;
3. sends on the other **without** `MSG_NOSIGNAL`, in a child process, and
   asserts the child **died of signal 13**;
4. sends on another pair **with** `MSG_NOSIGNAL` and asserts it returns
   `EPIPE` (`-32`) in `Result.err`.

This is the one test in the suite that proves a *specification claim* rather
than a behaviour: `SAFETY.md` §2 asserts that the runtime installs no `SIGPIPE`
disposition and that the default is lethal, and that claim is load-bearing for
every send in the library. If a future compiler release starts ignoring
`SIGPIPE` at `_start`, step 3 fails, and the library learns that its central
rule has become belt-and-braces rather than essential — which is worth knowing
either way.

**Rule V-6.** Step 3 needs a subprocess, because the whole point is that the
process dies. The harness runs it as a separate program whose expected outcome
is death by signal, and the marker is `// expect-signal: 13` — one addition to
the compiler's marker grammar, and the only one this library makes.

---

## 4. Property tests

**Rule V-7 — parse ∘ format is the identity** on every valid address
(`ADDRESS_MODEL.md` A-25), over a generated corpus: every IPv4 address in a
sampled sweep, every IPv6 shape from RFC 4291 and RFC 5952's examples, every
`UnixAddr` kind. It is this library's cheapest oracle.

**Rule V-8 — format is canonical**, so `format(parse(format(x))) == format(x)`
holds for *any* accepted input spelling, not just canonical ones. That is the
property that actually catches a formatter bug, because the round trip in V-7
would pass a formatter that consistently emitted the same wrong thing.

**Rule V-9 — the strict-parser corpus is a rejection corpus.** Every spelling
in `ADDRESS_MODEL.md` A-19's refusal table is a test that asserts `ESockAddr`,
because "we refuse octal octets" is a security claim and an untested security
claim is a comment.

**Rule V-10 — the encode/decode round trip over the kernel.** For each family:
encode an address, `bind` a socket to it, `getsockname` it back, decode, and
compare to what went in. That closes the loop through the actual kernel rather
than through this library's own idea of the layout, and it is what would catch
a wrong offset that both the encoder and the decoder agreed on.

---

## 5. What the harness checks about the tree

Not tests. Checks that diff the library against the thing that describes it,
run on every full invocation.

| Check | Diffs |
|---|---|
| `check_error_budget` | the count and names of public `error:` declarations against `SAFETY.md` §3's table — four, and the names |
| `check_failsafe_arms` | the generated per-module arm list against a program that imports each module and compiles its `failsafe` |
| `check_layering` | every `use` edge against `BUILD.md` §6's diagram |
| `check_msg_nosignal` | **every `sendto`/`sendmsg` call site in `src/` passes `MSG_NOSIGNAL`** — the mechanical enforcement of S-1, and the most valuable check in this list |
| `check_no_floor_write` | no call to the floor's `write` on a socket descriptor anywhere in `src/` (S-2) |
| `check_no_raw_setsockopt` | `setsockopt` appears only in `src/option/raw.npk` (P-1) |
| `check_constants_named` | no bare syscall number or kernel constant outside `src/sys/`; no bound outside `src/core/limits.npk` |
| `check_struct_sizes` | every structure size a spec table states is asserted by a probe |
| `check_no_hardcoded_port` | no port literal in the suite except 0 (V-3) |
| `check_specs_current` | reports, does not fail: spec citations that no longer resolve |

**Rule V-11.** `check_msg_nosignal` is the one that matters most, because S-1
is a rule about **every call site** and a rule about every call site is a rule
that will be broken by the twentieth one. It is a grep with a whitelist of
zero.

---

## 6. Fuzzing

**Rule V-12.** Two fuzz targets, both pure and both needing no kernel:

- **the address parsers** — random bytes and structured mutations of valid
  addresses, asserting: never traps, always terminates, never accepts a
  spelling A-19's table refuses, and `parse` never returns an address whose
  `format` differs from the input's canonical form.
- **the `cmsghdr` reader** — random control buffers, asserting: never traps,
  never reads past `msg_controllen`, never returns a descriptor it did not
  receive, and closes every descriptor on every refusal path (N-10, N-11).

The second is the important one. It is the library's only parser of
attacker-adjacent binary data, and its failure mode is a leaked or
double-closed descriptor rather than a wrong answer.

**Rule V-13.** A fuzz input that found something is committed as a permanent
fixture.

---

## 7. The harness is tested

**Rule V-14 (the self-check).** `harness/selfcheck.py` feeds the harness wrong
expectations and requires it to report every one as a failure:

- a `program` case with the wrong `expect-exit`;
- a `check` case expecting a code the compiler does not report;
- a `check` case that reports a code no expectation names (the D-237 rule);
- a `loopback` case that leaves a socket open at exit (D-151 should trap it);
- a `// expect-signal: 13` case whose program exits normally;
- a `parse` case that does not parse;
- a tree check fed a deliberate violation — a `sendto` without `MSG_NOSIGNAL`.

**Rule V-15.** The self-check runs first in every full invocation. A harness
that has not proven it can fail has not proven anything.

---

## 8. Stress

**Rule V-16.** `// stress: 40` on: every accept, every connect (both legs),
every ancillary round trip, the `EMFILE` back-off, and the bounded accept
loop. A red under stress is a **stop sign, never a retry** — every
timing-shaped defect the compiler found looked like flakiness first.

---

## 9. What is not tested, and is stated instead

**Rule V-17.** The library cannot test, and does not claim:

- **a real network's behaviour** — packet loss, reordering, MTU discovery, a
  middlebox that resets idle connections. Loopback has none of them.
- **the kernel.** `bind` does what the kernel does.
- **another host's stack.** Interoperability with a non-Linux peer is asserted
  by the wire format being the wire format, and by nothing this suite runs.

Enumerated rather than mitigated, which is the compiler's own TCB doctrine
(`VERIFICATION.md` §7) and the only honest shape for a claim of this kind.
