# Open questions

Everything that is not settled, each with a recommendation, so that nothing
lives only in a conversation. Three prefixes:

| Prefix | Whose |
|---|---|
| `O-x` | **ours** — a design question this project decides, at the cycle named |
| `O-N` | the **compiler's** — a gap in the language or its tooling that `nsockets` needs closed, to be raised as a request. **Reserved: no specification uses `O-N` for its own open item.** |
| `Q-` | the **user's** — a question that wants an answer before the work it gates begins |

A question that gets answered moves to `DECISIONS.md` as a numbered decision
and is struck through here with the decision's number, **never deleted** — the
question is part of the record of how the answer was reached.

**No cycle in this plan is blocked on a question.** What is open below is open
by design: two measurements, three defaults that want a number rather than a
taste, one item gated on the compiler's tooling, and three that are the
compiler's rather than ours.

---

## Q — for the user

### ~~Q-1 — what "unix sockets library" means~~ — **SETTLED, SK-003**
The full BSD socket surface: `AF_UNIX` plus TCP and UDP over IPv4 and IPv6.
DNS out (`SK-024`), TLS out (`SK-025`).

### ~~Q-2 — may these libraries depend on each other~~ — **SETTLED, SK-006**
No. `[dependencies]` stays empty, cross-repository imports do not resolve
anyway (`O-N2`), and the overlaps are recorded where they occur.

### Q-3 — the release cadence and versioning
`nsockets` has no consumers yet, so nothing forces an answer, and
`nitpick-tui` settled the same question as its T-103.
**Recommendation:** adopt T-103's shape verbatim — `0.x` until the compiler
reaches 1.0 and the API has survived cycle 0.9's application; semantic
versioning thereafter; and **adding a public error identity is a major
version** (`SK-034`), which is already recorded here. Settled at cycle 1.0
unless the author wants it earlier.

---

## O-N — the compiler's

Each is a request to be raised in the compiler repository, not something this
project can fix. None blocks planning; one blocks the migration off the
harness.

### O-N1 — `IO_REFERENCE.md` §10 records sockets as unspecified
The language's own I/O specification says: *"Sockets. The stream traits cover
them, but addressing, connection setup, and the `Result` mapping for the
socket-specific error space are not specified here. `ARCHIVE/nsocket` exists
and has not been assessed."*
**This library is the answer.** The ask is a one-line amendment pointing at it
once `nsockets` exists, so the language's specification stops carrying an open
item that has been closed elsewhere.

### O-N2 — `npkg` cannot build a library, and `[dependencies]` resolves to nothing
Measured at the compiler's 1.5.0 and recorded in `specs/BUILD.md` §1.
`npkg build` is the compiler's own bootstrap ladder; `target = "library"` is
accepted by the schema and read by nothing; the loader's dependency-root list
is created empty and `rootlist_add` is called from nowhere.
**Consequence:** `nsockets` builds through its own Python harness (`SK-004`)
and every import is relative until this closes.
**Ask:** `npkg build` honouring `target = "library"`, and the driver populating
the resolver's roots from `[dependencies]`.

### O-N3 — a comment in `types.npk` overstates the `OwnedFd` rule
`type_contains_borrow_recorded`'s comment reads *"…so it may not ride a channel
**or cross a spawn** any more than a Guard may"*, but the implemented spawn rule
is `escape.npk`'s `type_holds_pointer`, which answers **`false`** for
`TY_OWNEDFD` — a move into a spawn **is** legal, and `IO_REFERENCE.md` §6 says
so explicitly. The code is right and the comment is loose.
**Ask:** a one-word amendment, because that comment is exactly where somebody
designing a server will look, and `SK-035` is built on the code's behaviour
rather than the comment's.

### O-N4 — no `sigaction` and no signal-mask primitive in the language
Stated as an observation rather than a request: `nsockets` needs neither
(`MSG_NOSIGNAL` closes its one hazard at the call site, `SAFETY.md` S-3), and
`nitpick-tui` reaches the signal machinery through `signalfd` over raw `sys`
calls. Recorded so that a future language-level signal facility is known to
have one library that wants it and one that does not.

---

## O-x — ours

### Sockets

- **O-K1 — `sendmmsg` / `recvmmsg`.** Batched send and receive; a real
  throughput win for a high-rate UDP consumer, and a second error model per
  message. **Recommendation:** out at 1.0, revisited when a consumer measures a
  need.
- **O-K2 — `SOCK_SEQPACKET` beyond `AF_UNIX`.** SCTP is the only other
  provider and is absent from a stock kernel. **Recommendation:** `AF_UNIX`
  only, which is where the useful case is.
- **O-K3 — whether `sock_adopt` should exist at 1.0.** It is the door for
  socket activation (systemd `LISTEN_FDS`) and for a descriptor received over
  `SCM_RIGHTS`, and it is also the one place `fcntl` appears and the one place
  a caller can hand in something that is not a socket.
  **Recommendation:** yes, with `SOCKET_MODEL.md` K-9's verification, because
  the alternative is that a consumer writes it without the check. Settled at
  cycle 0.2.

### Addresses

- **O-A1 — whether `Ipv6Addr` carries its scope id.** As specified it does,
  which matches `sockaddr_in6` and keeps `IpAddr` self-contained; the
  alternative matches Rust's `Ipv6Addr` and makes the type exactly the wire's
  16 bytes. **Recommendation:** keep it, because a link-local address without a
  scope is a bug waiting to happen. Settled at cycle 0.1's close.
- **O-A2 — CIDR and prefix arithmetic.** `Ipv4Net`, containment tests.
  **Recommendation:** out at 1.0; a clean separate library, and nothing in
  `nsockets` needs it.
- **O-A3 — `%interface` scope names.** Turning `%eth0` into a scope index needs
  `RTM_GETLINK` over a netlink socket, which is a protocol implementation.
  **Recommendation:** parse and format numeric scope ids at 1.0 and say so in
  the parser's documentation, so the gap is visible rather than surprising.
  It also gates `DATAGRAM_MODEL.md` G-16's multicast interface question.

### Streams

- **O-T1 — `TCP_NODELAY`'s default.** Nagle adds up to 40 ms to a
  request/response protocol; disabling it by default costs bandwidth on a bulk
  sender that writes badly. **Recommendation:** leave the kernel's default
  (Nagle on) and make `nodelay(true)` one call, because a library that silently
  changes a transport's behaviour is worse than one that makes you ask. Settled
  at cycle 0.3's close **against a measurement**, not taste.
- **O-T2 — how `stream_write_all` reports a partial count on a deadline.** A
  companion field on the error, or a `Result<int64>` whose value is the count on
  both paths. **Recommendation:** the companion field, because the success path
  should not have to be read as "how much of it succeeded". Settled at 0.3.

### Datagrams

- **O-G1 — `IP_PKTINFO` / `IPV6_RECVPKTINFO`.** A UDP server bound to
  `0.0.0.0` cannot tell which local address a datagram arrived on, so a reply
  can go out with the wrong source. **Recommendation:** in, at cycle 0.6 — a
  datagram library that answers wrongly on a multi-homed host has a hole a
  consumer cannot patch from outside.
- **O-G2 — `SO_TIMESTAMPNS`.** Kernel receive timestamps as ancillary data.
  **Recommendation:** out at 1.0, recorded, and cheap to add once the ancillary
  machinery exists.

### Options

- **O-P1 — the QoS options** (`IP_TOS`, `IPV6_TCLASS`, `SO_PRIORITY`).
  **Recommendation:** out at 1.0. Meaningful only on a network that honours
  DSCP, trivially added when one appears, and shipping them untested implies a
  guarantee the library cannot make.
- **O-P2 — whether the builder's option setters return `Result` or
  accumulate.** As written they return `SockBuilder` and a failure surfaces at
  the terminal `bind`/`connect`/`listen`, which reads well but reports away
  from the cause. **Recommendation:** the builder carries the first error and
  the terminal operation reports it **with the option's name attached**.
  Settled at cycle 0.7.

### Ancillary

- **O-Y1 — the `SCM_RIGHTS` cap.** Sixteen descriptors per message, against the
  kernel's 253, chosen so the fixed control buffer is comfortable.
  **Recommendation:** keep 16 at 1.0; a higher cap costs a bigger fixed buffer
  on every ancillary receive, paid by everyone. Raise it with a measurement if a
  consumer asks.
- **O-Y2 — descriptor passing to a non-`AF_UNIX` peer.** Nothing to do; recorded
  because "can I pass a descriptor over TCP" is asked every time, and the answer
  — no, not on any operating system — belongs in the documentation rather than
  in a reader's memory.

### Concurrency

- **O-C1 — the bounded-accept counter's type.** `atomic<int32>` or plain?
  Tasks are pinned (D-032) so a plain one is correct for a single-executor
  server and wrong the moment somebody runs two.
  **Recommendation:** `atomic<int32>`; one SeqCst operation per accept is
  nothing next to the accept. Settled at cycle 0.8.
- **O-C2 — the join list under ten thousand live connections.** D-207 makes it
  a per-scope LIFO stack. Whether a completed task leaves it promptly, and what
  a scope with ten thousand entries costs, is a **measurement**, and cycle 0.8
  takes it. If the cost is real the answer is a nested scope per batch, which is
  a shape change and wants the measurement first.
- **O-C3 — a `SO_REUSEPORT` multi-executor helper.** The shape works
  (`CONCURRENCY_MODEL.md` C-14) and the library ships no helper.
  **Recommendation:** add one at 0.8 only if cycle 0.9's application wants it;
  a helper for a shape nobody has run is a helper that is wrong.

### Build and test

- **O-B1 — when to migrate off the harness.** Gated on `O-N2`. **No action
  until then**; the harness and `npkg` run side by side with a parity check
  before the harness retires.
- **O-B2 — whether the `network` stage should exist at 1.0.** Everything except
  outbound internet connectivity runs on loopback, and a stage skipped on every
  developer machine is a stage nobody trusts. **Recommendation:** keep it with
  exactly two tests, small enough to run by hand when it matters.

### Safety

- **O-S1 — whether `ESockState` is needed at all.** The typestate makes most
  misuse unspellable; what remains — a second `connect`, an operation after
  `shutdown` — might be better as a forwarded `EINVAL`/`ENOTCONN`, which is
  what the kernel returns anyway and which costs no arm.
  **Recommendation:** keep it for the cases the kernel answers *ambiguously*,
  and drop it if cycle 0.3 finds none. **A budget of three would be better than
  four**, and this is the only realistic way to get there.
