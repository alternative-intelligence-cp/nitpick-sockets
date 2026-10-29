# Safety, signals, errors, and descriptors

The constraints. Read this first: most designs that look reasonable for a
socket library die on one of §1's rules, and the two that shape `nsockets`
most — the `SIGPIPE` rule and the error budget — have no analogue in any other
language's socket library, so there is nothing to copy.

---

## 1. What the language imposes

Each row is a language decision, not ours. The consequence column is what it
costs a library that talks to the kernel over descriptors.

| Language rule | Where | Consequence for `nsockets` |
|---|---|---|
| **The runtime catches `SIGPIPE` with a handler that returns** | measured, §2 (probe 04) | a send to a dead peer answers `EPIPE` on the floor's runtime, and kills a process whose disposition is the default. **Every send carries `MSG_NOSIGNAL`**, which answers `EPIPE` under either. §2 |
| `defer` does **not** run on a trap | D-014 | a socket open at trap time is closed by process exit and by nothing else. §6 |
| A trap is a **whole-program** event; no task resumes | D-063 | there is no "the connection task cleans up" |
| `failsafe`'s `pick` must **name** every error that can reach it | REACH-002 | every identity a reachable `fail` raises — public or private, qualified by its module — is an arm every consuming program owes, beside the floor's six and what its code reaches; an identity never raised costs nothing (measured, §3). §3 |
| Reachability is **import-scoped** | 1.4.8's `nsys` note | module decomposition decides what a consumer's `failsafe` owes. §3 |
| An `OwnedFd` is **refused as a channel element** | TYPE-057, D-235; measured, probes 09 and 09b | a connection cannot be queued to a worker pool. This decides the server model outright. `CONCURRENCY_MODEL.md` §3 |
| An `OwnedFd` does **not** hold a pointer | `escape.npk`, D-185; measured, probes 10 and 10b | a **move** into a spawned task *is* legal, and a borrow across the spawn is `BORROW-004`. The two rules together are the whole concurrency story. `CONCURRENCY_MODEL.md` §3 |
| Owning values are **move-only** | TYPE-046 | no binding-to-binding copies of an `OwnedFd`; a socket is consumed or borrowed, never duplicated by assignment |
| Borrows are second class | D-004 | a byte view handed to `send` cannot be stored, returned, or held across an `await` |
| A successful `exit 0` with live `wild` allocations **traps** | D-151 | every `wild` byte an ancillary buffer takes is paired on every path. §6 |
| Plain integer `+ - *` **traps** on overflow | D-210 | a length arithmetic mistake is a crash, not a short read. §5 |
| Array, slice and buffer indexing is bounds-checked and traps | D-070 | an out-of-range read into a `sockaddr` is a *crash*, not a leak of adjacent memory |
| Every blocking operation carries a **mandatory deadline** | D-056, D-176 | there is no unbounded `accept`, `connect`, `recv` or `send`. §4 |
| Blocking is **task** suspension, never thread parking | D-071 | every wait goes through `io_ready` / `suspend_io`. `CONCURRENCY_MODEL.md` §1 |
| Inherited descriptors 0/1/2 stay **blocking** | D-071, D-185 | `nsockets` never touches them and never hands one out as a socket |
| There are **no closures** | D-018 | an accept loop is a loop, not a callback registration |
| There is **no `select`** across channels | D-072 | fan-in over several sockets is one `suspend_io` over several watched descriptors, not a channel merge |
| `async` functions can never be `never fails` | D-163 | `raw await …` is unspellable; `relay` / `?\|` / `?!` are the spellings |
| A library **cannot declare a flag family** | D-230 | `SocketFlags`, `MsgFlags` and the option words are plain integers with named constants, not `TY_FLAGS` types |

---

## 2. `SIGPIPE`, and why every send is `MSG_NOSIGNAL`

**The failure this exists to prevent.** A process writes to a socket whose
peer has closed. The kernel raises `SIGPIPE`. `SIGPIPE`'s default disposition
is to **terminate the process** — not to return an error, not to route through
`failsafe`, not to run a `defer`. The program is gone, mid-transaction, with
whatever it was holding.

**What the floor's runtime does, measured at compiler `c9baa9e`** (probe 04,
`tests/probe/probe04_sigpipe.npk`, at `-O0` and through `opt -O2`). It catches
`SIGPIPE` with a handler that returns: `runtime/npkrt.ll`'s `npk_fault_arm`
installs it at startup (the compiler's DEF-68), and `rt_sigaction(SIGPIPE,
NULL, &prior)` reads it back — neither `SIG_DFL` nor `SIG_IGN`, its flags
`SA_RESTORER | SA_ONSTACK | SA_RESTART`. So on the floor's runtime a send with
no flags to a dead peer **answers `EPIPE`** and the program lives, and so do
the same send with `MSG_NOSIGNAL`, the floor's `write` on the socket, and a
`write` to a pipe whose reader is gone — all four the same error. Under the
default disposition, set by the probe itself, the `MSG_NOSIGNAL` send still
answers `EPIPE`, and with no flags it **dies by signal 13** (its mutant, cycle 0.0.0's block 0b).

*(Corrected 2026-10-29 by SK-101. This paragraph said the runtime installs
no signal disposition for anything — a search of `npkrt.ll` found no
`rt_sigaction` call — which was true of the runtime it was read in: there is
none at the compiler's `3d15ac9`, and the handler came with its `b7244d2f`. It
quoted the compiler's Bridge, `lib/nbridge.npk`: "a plain write to a socketpair
whose peer died raises SIGPIPE, which terminates the runtime by default" — a
comment that predates the handler and still reads so at `2e1cb4a` — and "the
first EPIPE schedule proved it by taking the whole process down", which that
file says of `?!`, an unwrap that traps on an `EPIPE` result, not of the
signal.)*

**Rule S-1 (SK-013, SK-101).** **Every send `nsockets` issues carries
`MSG_NOSIGNAL`.** Without exception, on every family, on every socket type,
on the ancillary path as well as the ordinary one. The failure then arrives
as `EPIPE` (`-32`) in `Result.err`, where a caller can see it and act —
whatever the process's disposition is, the floor's handler or the default.

**Rule S-2.** `nsockets` therefore **does not use the runtime floor's
`write`** on a socket, and neither may an impl of the prelude's `Writer` trait
over one. The floor's `write` is `write(2)`, which raises `SIGPIPE` on a socket
exactly as it does in C — answered `EPIPE` by the floor's handler (probe 04),
fatal under the default disposition (its mutant, cycle 0.0.0's block 0b) — and
has no flags word to carry `MSG_NOSIGNAL`; the only send primitives this library uses are
`sendto` (syscall 44) and `sendmsg` (syscall 46), both with `MSG_NOSIGNAL` in
the flags word. This is the single most likely rule to be broken by accident,
because `ByteWriter` in the prelude *does* use the floor's `write` and looks
like the thing to copy — it writes to a file, where the hazard does not exist.

**Rule S-3.** `nsockets` **blocks no signals and installs no handler.** It has
no need to: `MSG_NOSIGNAL` closes the one hazard at each call site rather than
process-wide, and process-wide signal state is not a library's to change.

> **A limitation stated rather than mitigated.** `MSG_NOSIGNAL` covers what
> this library sends. It does not cover a `write(2)` an *application* issues on
> a descriptor it obtained by `release_fd`, and it cannot. The public
> documentation says so where `release_fd` is described, and the escape hatch
> is that an application taking a raw descriptor has taken responsibility for
> it — which is what `release_fd` means.

---

## 3. The error budget

**Rule S-4 (SK-015).** REACH-002 makes every `error:` that can reach
`failsafe` a named arm the consuming program's `failsafe` must carry. **The number of public
error identities `nsockets` declares is a hard budget, and it is four.**

| Error | Raised when | Declared in |
|---|---|---|
| `ESockAddr` | an address could not be parsed, or does not fit its family's kernel structure | `src/addr/` |
| `ESockState` | an API was used out of order in a way the type system could not prevent — a second `connect`, a `bind` after `listen`, an operation on a socket whose peer half is shut down | `src/socket/` |
| `ESockCapacity` | a constant-capacity structure is full — the ancillary control buffer, a received address longer than its family allows | `src/socket/` |
| `ESockProtocol` | received ancillary data is not what the wire promised — `MSG_CTRUNC`, a `cmsghdr` of the wrong level or type, a control length the kernel could not have produced | `src/ancillary/` |

**Rule S-5 — four is a ceiling, not a target**, and adding a fifth is a
**major** version change (`SK-034`): a new identity is a new mandatory arm in
every consuming program's `failsafe`, which the compiler enforces, so it is a
source break in every consumer.

**Rule S-6 — kernel errnos are forwarded verbatim**, `fail r.err`, exactly as
`lib/nsys.npk` does. A forwarded errno is a dynamic operand and does not
enlarge the reachable set, so it costs no `failsafe` arm. **This is why the
budget is four rather than forty**: `ECONNREFUSED`, `EADDRINUSE`, `EPIPE`,
`ETIMEDOUT`, `EHOSTUNREACH`, `EMFILE` and the rest of the socket error space
are the kernel's words, they reach the caller unchanged, and they cost nothing.

**Rule S-7 — end of stream is the prelude's `IoEof`.** A stream read that
returns zero bytes because the peer sent FIN reports `IoEof` (`-4096`), the
identity `IO_REFERENCE.md` §2 already defines and the floor's own `read`
already returns. `nsockets` declares no end-of-stream error of its own, and a
caller that already handles `IoEof` from a file handles it from a socket
unchanged.

**Rule S-8 — module decomposition is part of the budget**, because REACH is
import-scoped:

- `src/sys/` declares **no error at all** — every failure is an errno.
- `src/addr/` declares **`ESockAddr` only**. A program that parses and formats
  addresses and never opens a socket owes one arm of this library's — `ESockAddr`,
  qualified by its module — beside the floor's six and what the parser's code
  reaches (`IntOverflow`, `OutOfBounds`), measured by cycle 0.0.0's block 0b
  (SK-105).
- `src/socket/`, `src/stream/`, `src/datagram/`, `src/option/`, `src/server/`
  declare `ESockState` and `ESockCapacity`.
- `src/ancillary/` declares `ESockProtocol`.

**Rule S-9.** The exact arm set a consuming program owes, per import, is
generated into the documentation and checked by a conformance test that builds
a program importing each public module and asserts its `failsafe` compiles with
exactly the documented arms and no more. An out-of-date arm list is the kind of
document that goes stale silently, so it is derived, not written.

---

## 4. Deadlines

**Rule S-10.** Every `nsockets` operation that can wait takes a
`Duration:within` and returns `DeadlineExceeded` when it expires. There is no
unbounded `connect`, no unbounded `accept`, no unbounded `recv` and no
unbounded `send`.

**Rule S-11 — the deadline is the reactor's, never the socket's.**
`SO_RCVTIMEO` and `SO_SNDTIMEO` are **never set** by this library and are not
in the option surface (`OPTION_MODEL.md` §5). A socket-level timeout would be a
second timing mechanism with different semantics from the first — it applies to
a blocking call this library never makes, it interacts badly with a partially
completed `send`, and having two ways to bound a wait means every reader has to
ask which one is in force.

**Rule S-12.** A deadline that expires is never silently retried and never
turns into a longer deadline. `DeadlineExceeded` reaches the caller, and a
partially completed operation reports what it completed (`STREAM_MODEL.md` §6).

---

## 5. Arithmetic

**Rule S-13.** Lengths are `int64` where they meet the kernel, because that is
the syscall return type and a short count is an ordinary answer. Ports are
`uint16`, which is exactly the wire's width and makes an out-of-range port
unspellable. Address bytes are `uint8`.

**Rule S-14.** Byte-order conversion happens in **one place**
(`ADDRESS_MODEL.md` §6) and every port and every IPv4 word goes through it.
Overflow traps under D-210, so a swap written with a shift and a mask is a
trap waiting to be found rather than a silent corruption — which is an
improvement, and is why the conversion is one audited function and not an
idiom scattered through the tree.

**Rule S-15.** Nothing in this library divides by a value it has not proven
non-zero on the same path.

**Rule S-16.** Every read of a kernel structure goes through one accessor per
field, and the accessor is where the offset lives. Callers do not index the
raw bytes. This is what makes the layout one obligation to discharge in cycle
1.5 rather than several hundred, and it is what makes an offset change a
one-line change.

---

## 6. Resources

**Rule S-17 — every socket is an `OwnedFd`.** The close *is* the drop
(D-185), so there is no `close` in the surface. `close(release_fd(move s))` is
the spelling for a caller that must observe close's verdict — the move defuses
the drop, so no double close is spellable.

**Rule S-18 — a socket is created non-blocking and close-on-exec atomically**
(`SK-012`). `SOCK_NONBLOCK | SOCK_CLOEXEC` in the `socket()` and
`socketpair()` calls; `accept4()` with the same flags rather than `accept()`.
Never a follow-up `fcntl`: between the `accept` and the `fcntl` there is a
window in which a concurrent `execve` leaks the descriptor to a child, and the
kernel offers the atomic form precisely so nobody has to reason about it.

**Rule S-19 — a trap leaks descriptors, and that is stated rather than
mitigated.** `defer` does not run on a trap and no drop runs either, so a
socket open when a trap fires is closed by process exit and by nothing else.
Unlike a terminal, that is harmless: the kernel reclaims every descriptor at
exit, a listening socket's port is released, and a connected peer sees a reset.
There is therefore **no restore registry in this library**, and its absence is
a decision (`SK-033`) rather than an omission — `ntui` needs one because a
terminal's state outlives the process, and a socket's does not.

**Rule S-20 — the one thing that does outlive the process is a bound Unix
socket path.** `bind` on `AF_UNIX` creates a filesystem entry that `close` does
not remove. `nsockets` does **not** unlink it: an unlink is a filesystem side
effect on a path the caller chose, possibly shared, possibly a symlink, and a
library that removes files it did not create is a library nobody can reason
about. The rule, the spelling and the reasoning are in `SOCKET_MODEL.md` §9,
and it is the one place this library asks an application to clean up after it.

**Rule S-21 — `nsockets` spawns no processes and creates no threads.** It
suspends tasks. An application that wants a thread per connection creates it,
and `CONCURRENCY_MODEL.md` §3 says what the language permits.

**Rule S-22 — ancillary buffers are constant-size and stack-shaped.** The control
buffer for a `sendmsg`/`recvmsg` is a stack array of constant size, sized by
`ANCILLARY_MODEL.md` §4's bound, not a growable allocation, so the ancillary
path takes no `wild` bytes and cannot trip D-151 on any exit path.

---

## 7. What an application owes

Stated once, here, and repeated in the public documentation:

1. **Carry the `failsafe` arms your imports require** (S-9 generates the list).
2. **Unlink a Unix socket path you bound**, when you are finished with it
   (S-20). The library gives you the spelling; it will not do it behind your
   back.
3. **If you take a raw descriptor with `release_fd`, you own the `SIGPIPE`
   hazard on it** (S-2's note).
4. **Reap what you spawn** — D-188 traps a clean exit that left a registered
   child, and a program that forks a helper to hand a socket to still owes
   that.

---

## 8. Open items

- **O-S1 — whether `ESockState` is needed at all.** The typestate
  (`SOCKET_MODEL.md` §4) makes most misuse unspellable, and what remains —
  a second `connect`, an operation after `shutdown` — might be better as a
  forwarded `EINVAL`/`ENOTCONN`, which is what the kernel returns anyway and
  which costs no arm. **Recommendation:** keep it for the cases the kernel
  answers *ambiguously*, and drop it if cycle 0.3 finds none. Settled at 0.3's
  close, and a budget of three would be better than four.
