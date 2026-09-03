# Roadmap — the cycle map

The specification set (`meta/specs/`) is written and the decisions it rests on
are in `meta/DECISIONS.md`. This is the plan built on them.

**`SK-001` … `SK-037` are settled.** What remains open in
`../OPEN_QUESTIONS.md` is open *by design*: two measurements taken in the
cycles that can take them, three defaults that want a number rather than a
taste, one item gated on the compiler's tooling, and four that are the
compiler's rather than ours. **No cycle in this plan is blocked on a decision.**

## How this is organised

- **A cycle is a folder** — `0.0/`, `0.1/`, … — focused on **one topic**.
- **A subcycle is a file inside it** — `0.0.0.md`, `0.0.1.md`, … — one workable
  chunk of that topic, written execution-grade before its code is touched.
- **A finished cycle moves to `done/`**, so the active work stays easy to find.
- **Commit after every subcycle. Push at the end of every cycle.**
- **Every cycle's README carries a checklist.** Tick items as they land; the
  checklist is the cycle's state.

This convention is the compiler repository's, deliberately, so that a session
moving between the two reads one thing. **Each cycle's opening subcycle file is
written at the previous cycle's close**, by the session that just learned what
that cycle taught; cycle 0.0 is the exception, written up front because there
is no previous cycle.

---

## The constraints that shape everything

**`nsockets` cannot be built by `npkg` today**, and cross-repository imports do
not resolve (`specs/BUILD.md` §1, `../OPEN_QUESTIONS.md` O-N2):

> **`harness/` is the build and test runner, and every import is relative,
> until the compiler's tooling closes O-N2.**

And the two that shape the *design*:

> **The Nitpick runtime installs no `SIGPIPE` disposition, so a plain send to a
> dead peer kills the process** — which makes `MSG_NOSIGNAL` on every send this
> library's headline rule (`SK-013`).
>
> **An `OwnedFd` is refused as a channel element but may be moved into a
> spawn** — which makes accept-then-spawn the only expressible server model
> (`SK-035`).

Both were measured in the compiler's own source, not assumed, and both are
enforced mechanically rather than by discipline: `check_msg_nosignal` greps
every send site, and the second is enforced by the compiler itself.

---

## Phase 0 — the library, built bottom-up

Almost every cycle is testable over `socketpair` and loopback — no network, no
port, no privilege (`specs/TESTING.md` §2). That is what makes the ordering
free to follow the dependencies rather than the risk.

| Cycle | Topic | Gated on |
|---|---|---|
| **0.0** | **Foundations** — the language probes, the harness, `src/core/` | — |
| **0.1** | **Addresses** — `Ipv4Addr` … `UnixAddr`, the kernel layouts, parsing, formatting, byte order | 0.0 |
| **0.2** | **The socket primitive** — `src/sys/`, `Sock`, the builder, the headless double | 0.0, 0.1 |
| **0.3** | **Streams** — connect with `EINPROGRESS`, listen, accept, `Reader`/`Writer`, half-close | 0.2 |
| **0.4** | **Unix domain** — pathname and abstract, stream and seqpacket, peer credentials | 0.2, 0.3 |
| **0.5** | **Ancillary data** — the one `msghdr`, `SCM_RIGHTS`, `SCM_CREDENTIALS` | 0.4 |
| **0.6** | **Datagrams** — UDP v4/v6, Unix datagram, truncation, broadcast, multicast | 0.3, 0.5 |
| **0.7** | **Options** — the typed surface completed | 0.3, 0.6 |
| **0.8** | **The server** — accept-then-spawn, bounded accept, the `EMFILE` back-off, `poll_set` | 0.3, 0.7 |
| **0.9** | **The dogfood application** — a real program written against the library as a consumer | 0.8 |
| **0.10** | **Hardening** — the fuzz sweep, the stress sweep, the compatibility matrix, the obligations | 0.9 |
| **1.0** | **Release** — documentation, the API freeze, the `failsafe` arm contract, versioning | 0.10 |

---

## What each cycle produces

### 0.0 — Foundations
The **language probes** first: twelve small programs that ask the compiler
whether the shapes `meta/specs/` depends on are spellable. Two of them are the
reason this cycle exists — **probe 04 proves `SIGPIPE` is lethal** (and so that
`SK-013` is load-bearing rather than belt-and-braces), and **probes 09 and 10
prove the `OwnedFd` channel refusal and the spawn move**, which is `SK-035`'s
entire foundation. Then the harness, the manifest's test table, CI, and
`src/core/`.

**The cycle's own gate:** every probe has a recorded verdict, and the harness
self-check proves it can fail seven ways.

### 0.1 — Addresses
`src/addr/`: the five types, the kernel encoders and decoders with every offset
asserted, `hton`/`ntoh` in one module, the strict parsers, the RFC 5952
canonical formatters.

**The cycle's own gate:** parse ∘ format is the identity over a generated
corpus, format is canonical over any accepted spelling, every refusal in
`ADDRESS_MODEL.md` A-19's table is a passing rejection test, and an encode →
`bind` → `getsockname` → decode round trip through the real kernel returns what
went in.

### 0.2 — The socket primitive
`src/sys/` (the syscall table, every number carrying its header), `Sock`, the
builder with its pre-bind options, `bind`, `listen`, `sock_adopt`, and the
`socketpair` double. **`SK-013`'s send path lands here** — `sendto` with
`MSG_NOSIGNAL` — with `check_msg_nosignal` live from the first send site.

**The cycle's own gate:** a `socketpair` round trip; the `SIGPIPE` test from
`specs/TESTING.md` §3 passing both legs; `check_msg_nosignal` green and seen to
fail.

### 0.3 — Streams
`src/stream/`: `TcpListener`, `TcpStream`, connect's full `EINPROGRESS`
protocol including the `SO_ERROR` read, accept with `K-19`'s error table,
`Reader`/`Writer`, `write_all`, half-close, `IoEof`.

**The cycle's own gate:** a loopback client and server exchanging bytes both
ways, a connect to a closed port reporting `ECONNREFUSED` (not success), a
half-close producing `IoEof` on the peer, and every one of them under
`// stress: 40`.

### 0.4 — Unix domain
`src/stream/unix.npk`: `UnixListener`/`UnixStream`, the seqpacket pair,
pathname and abstract binding, `unix_unlink` and `unix_bind_replacing`,
`SO_PEERCRED`.

**The cycle's own gate:** an abstract-namespace address whose encoded length is
asserted byte for byte (`ADDRESS_MODEL.md` A-12 is the classic bug and the test
is what proves it closed), and a 108-byte path refused.

### 0.5 — Ancillary data
`src/ancillary/`: the one `msghdr`, `CMSG_LEN` versus `CMSG_SPACE`,
`SCM_RIGHTS` with `MSG_CMSG_CLOEXEC`, `SCM_CREDENTIALS`, and `N-9`'s
ownership-before-validation ordering.

**The cycle's own gate:** a descriptor passed over a `socketpair` and used at
the far end; `MSG_CTRUNC` producing `ESockProtocol` with every received
descriptor closed; and the `cmsghdr` fuzzer clean over a million inputs.

### 0.6 — Datagrams
`src/datagram/`: `UdpSocket`, `UnixDatagram`, `MSG_TRUNC` truncation reporting,
connected sockets, `SO_BROADCAST`, multicast joins, and `O-G1`'s `IP_PKTINFO`.

**The cycle's own gate:** a datagram larger than its buffer reported as
`ESockCapacity` **with the true length**, and a zero-length datagram received as
a datagram rather than as end of stream.

### 0.7 — Options
`src/option/`: the typed surface completed, `raw.npk` confined and
`check_no_raw_setsockopt` live, `O-T1` settled against a measurement, `O-P2`'s
builder-error shape decided.

### 0.8 — The server
`src/server/`: the accept-then-spawn loop, `server_accept_bounded` with its
counter, the `EMFILE` back-off, and `poll_set`. **`O-C2`'s measurement is taken
here** — what a scope with ten thousand joined tasks costs.

### 0.9 — The dogfood application
A real program in `examples/`, substantial enough to find what examples do not:
a TCP proxy with an admin socket over `AF_UNIX` — which exercises streams,
Unix sockets, descriptor passing, the bounded accept loop, half-close, and
`poll_set`, all in one program that has a purpose. Written as a consumer, with
every friction recorded and triaged.

### 0.10 — Hardening
The fuzz corpus swept, `// stress: 40` on everything with a timing dimension,
`specs/COMPAT.md`'s matrix filled with recorded runs, and
`specs/VERIFICATION.md`'s obligation list reconciled against what the code
generates.

### 1.0 — Release
`docs/` written, the public API frozen and enumerated, the `failsafe` arm
contract published per module, examples, and `Q-3`'s version policy.

---

## Post-1.0, as a map rather than a plan

| Cycle | Topic |
|---|---|
| **1.1** | `aarch64` Linux — a different `src/sys/` table and nothing else (`SK-007`) |
| **1.2** | `sendmmsg`/`recvmmsg` and `SO_TIMESTAMPNS`, if a consumer measures a need (`O-K1`, `O-G2`) |
| **1.3** | Verified build — `nsockets`' obligations through the compiler's `npkg verify`, once that reaches libraries |

---

## Ordering notes

- **The probes come first, in 0.0**, and two of them are load-bearing rather
  than reassurance: `SIGPIPE`'s lethality and the `OwnedFd` channel/spawn
  asymmetry are the foundations of `SK-013` and `SK-035`, and both were read
  out of compiler source rather than run. A probe that contradicts either
  changes the library.
- **The harness comes first too**, for the compiler's stated reason about
  diagnostics: it is how every later cycle is tested, and a suite written after
  the code is a suite shaped by the code.
- **Addresses precede the socket** because they are pure computation, fully
  testable with no kernel, and nothing can `bind` without them.
- **Options are split.** The three the builder needs before `bind` —
  `SO_REUSEADDR`, `SO_REUSEPORT`, `IPV6_V6ONLY` — land in 0.2 with the builder,
  because a listener cannot be correct without them. The rest wait for 0.7,
  when the things they apply to exist.
- **Ancillary data waits for Unix domain**, because `SCM_RIGHTS` only works
  over `AF_UNIX` and testing it needs a `UnixStream` or a `socketpair`.
- **The server is late** because it is composition rather than mechanism: every
  piece exists by 0.7 and 0.8 assembles them, measures `O-C2`, and adds the two
  loops nobody should write twice.
- **`O-T1` and `O-C2` are measurements, not preferences**, and the cycles that
  take them say so rather than guessing now.
- **A decision precedes the cycle that needs it.** Each cycle's README lists its
  open questions; a cycle whose questions are open is not ready to start.
- **Verification obligations are written from cycle 0.0 onward**, in the syntax
  they will take, with property tests standing in. The compiler's R9 is
  explicit that obligations discovered and never collected are the cheapest way
  to lose the campaign.

---

## What to expect, from the compiler's experience

**A construct that parses is not a construct that works.** Most of the
compiler's cycle 0.4 was repair, and every repair dated to the cycle that had
parsed the construct. Here: a socket call that compiles is not a socket call
that survives a peer disappearing at the wrong moment, and `// stress: 40` on
every timing-shaped test is the analogue of the sweep that found those.

**An analysis that is right on straight-line code and wrong after a merge
passes every test written the easy way.** Here: a `connect` that is right on
loopback (where it completes immediately) and wrong over a network (where it
returns `EINPROGRESS`), and an accept loop that is right until a client resets
between SYN and accept. Both have a dedicated test in the plan, because neither
is found by testing the easy way.

**Every hole was found by a check that diffs two lists, and none by a test.**
`specs/TESTING.md` §5 is this library's list, and `check_msg_nosignal` is the
one that matters most: `SK-013` is a rule about every call site, and a rule
about every call site will be broken at the twentieth one.

**A suite that only ever agrees with what it is handed is worse than no
suite.** The harness self-check is not optional and runs first.

---

## The cycle-numbering convention

Cycle numbers sort lexically only up to `0.9`; `0.10` sorts before `0.2` in a
plain listing. **The table above is authoritative over lexical order**, which
is the compiler's own resolution of the same problem and the reason it declined
to renumber.
