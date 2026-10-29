# The socket primitive

What `nsockets` opens, how it is typed, how long it lives, and what the kernel
surface underneath it is. [`SAFETY.md`](SAFETY.md) states the constraints; this
document states the mechanism.

Everything here is Linux on x86-64, through the language's `sys` builtin. There
is no libc call anywhere and no C structure crosses any boundary — the kernel's
structures are laid out in `buffer` storage by this library, byte offset by
byte offset, and **every number in this document was measured on the target
platform and is re-measured by a running program in cycle 0.0**.

---

## 1. The syscall floor

**Rule K-1.** These, and only these. A syscall not in this table is not made by
this library, and adding one is a decision.

| Call | # | Used for |
|---|---|---|
| `socket` | 41 | create (§3) |
| `connect` | 42 | `STREAM_MODEL.md` §3 |
| `sendto` | 44 | the ordinary send — **always with `MSG_NOSIGNAL`** (S-1) |
| `recvfrom` | 45 | the ordinary receive |
| `sendmsg` | 46 | ancillary send (`ANCILLARY_MODEL.md`) |
| `recvmsg` | 47 | ancillary receive |
| `shutdown` | 48 | half-close (§8) |
| `bind` | 49 | §5 |
| `listen` | 50 | §6 |
| `getsockname` | 51 | the local address after an ephemeral bind |
| `getpeername` | 52 | the peer address |
| `socketpair` | 53 | `AF_UNIX` pairs, and the test substrate |
| `setsockopt` | 54 | `OPTION_MODEL.md` |
| `getsockopt` | 55 | `OPTION_MODEL.md`, and `connect`'s `SO_ERROR` |
| `accept4` | 288 | §7 — **never `accept` (43)**, see S-18 |

`sendmmsg` (307) and `recvmmsg` (299) are **deliberately absent**: they batch
for throughput at the cost of a second, subtly different error model per
message, and no consumer has asked. Recorded as `O-K1`.

**Rule K-2 — the families and types.** `AF_UNIX` = 1, `AF_INET` = 2,
`AF_INET6` = 10. `SOCK_STREAM` = 1, `SOCK_DGRAM` = 2, `SOCK_SEQPACKET` = 5.
`SOCK_NONBLOCK` = 2048 (`0o4000`), `SOCK_CLOEXEC` = 524288 (`0o2000000`) — the
same two bit values `O_NONBLOCK` and `O_CLOEXEC` carry, which is not a
coincidence and is worth knowing when reading a flags word.

**Rule K-3 — protocols.** `IPPROTO_TCP` = 6, `IPPROTO_UDP` = 17,
`IPPROTO_IPV6` = 41 (an option level, not a socket protocol). A `socket()` call
in this library passes the explicit protocol rather than 0: `0` means "the
default for this family and type", which is the same thing right up until it is
not, and naming it costs a constant.

**Rule K-4 — the `sys` contract.** `sys` takes at most six register arguments
after the number, every argument must fit a register, and a pointer becomes a
number only at the trampoline (D-192). The call types as `Result<int64>`; the
kernel's own negative returns land in the error slot (D-141), so `ECONNREFUSED`
arrives as `-111` and reaches the caller unchanged under S-6.

---

## 2. What a socket value is

```nitpick
// The common primitive. Every typed socket in this library holds exactly one
// of these and adds nothing to its representation.
pub struct:Sock = {
    OwnedFd:descr;      // the descriptor — closed by its own drop (S-17)
    uint8:family;       // AF_UNIX | AF_INET | AF_INET6, as created
    uint8:kind;         // SOCK_STREAM | SOCK_DGRAM | SOCK_SEQPACKET
    uint8:shut;         // §8's half-close state: 0 none, 1 read, 2 write, 3 both
    uint8:origin;       // §10: Real or Headless
};
```

**Rule K-5 (SK-011).** `Sock` is **move-only**, because `OwnedFd` is
(TYPE-046). It is
never copied from binding to binding; it is moved, or borrowed as `Sock->`.

**Rule K-6 — `family` and `kind` are recorded, not re-derived.** They could be
had from `getsockopt(SO_DOMAIN)` and `SO_TYPE`, and asking the kernel a
question we answered when we created the socket is a syscall per operation to
learn something we knew. They are `uint8` because the values are small and
because a `Sock` should stay eight bytes plus its descriptor.

**Rule K-7 — nothing in this library holds a socket in an array.** A `Sock`
holds an `OwnedFd`, which is an owning value, so a `Vec<Sock>` would be a
container of move-only elements — legal, but every read out of it is a move.
Where a collection of connections is genuinely wanted, the shape is an
`arena<Sock>` with `Handle<Sock>` (which is what the language provides for
exactly this), and `CONCURRENCY_MODEL.md` §4 says when that is right.

---

## 3. Creation

**Rule K-8 (SK-012).** Every socket is created with
`SOCK_NONBLOCK | SOCK_CLOEXEC` **in the creating call**:

```
socket(family, kind | SOCK_NONBLOCK | SOCK_CLOEXEC, protocol)
socketpair(AF_UNIX, kind | SOCK_NONBLOCK | SOCK_CLOEXEC, 0, sv)
accept4(listener, addr, addrlen, SOCK_NONBLOCK | SOCK_CLOEXEC)
```

Never `socket()` followed by two `fcntl` calls. The reasons, in order:

- **`CLOEXEC` has a race without the atomic form.** Between the `accept` and
  the `fcntl(FD_CLOEXEC)`, any `execve` in any thread leaks the descriptor to
  the child. The kernel added `accept4` and the `SOCK_CLOEXEC` flag precisely
  so this window does not exist, and a library that reintroduces it is making
  a mistake the kernel already fixed.
- **`NONBLOCK` is not optional here.** D-071 makes every wait a task
  suspension; a blocking descriptor in the reactor would park the thread and
  stall every sibling task on that executor.
- **Two syscalls where one will do**, on the accept path, which is the hottest
  path a server has.

**Rule K-9 — `nsockets` never hands out a blocking socket and never accepts
one.** There is no constructor that takes a raw descriptor number from the
caller. A descriptor that arrived from elsewhere — through `SCM_RIGHTS`, from a
supervisor — enters through `sock_adopt`, which **verifies** with
`getsockopt(SO_DOMAIN)`/`SO_TYPE` and **sets** `O_NONBLOCK` and `FD_CLOEXEC`
before returning a `Sock`, and which is the one place `fcntl` appears. The
verification is not ceremony: an adopted descriptor might be a regular file,
and every subsequent operation would fail in a way that names the wrong thing.

---

## 4. The typestate

**Rule K-10 (SK-010).** A `Listener`, a `Stream` and a `Datagram` are
**different types with different operations**. There is no `Socket` value with
a state field.

```nitpick
pub struct:TcpListener  = { Sock:s; };
pub struct:TcpStream    = { Sock:s; };
pub struct:UdpSocket    = { Sock:s; };
pub struct:UnixListener = { Sock:s; };
pub struct:UnixStream   = { Sock:s; };
pub struct:UnixDatagram = { Sock:s; };
pub struct:UnixSeqPacketListener = { Sock:s; };
pub struct:UnixSeqPacket         = { Sock:s; };
```

This is D-072's argument applied unchanged: the compiler rejected a channel
with an `int32` mode field selecting behaviour at every operation, and a
`Socket` with a `state` field is the same shape. Here the payoff is direct —
`accept` on something that never listened, `send` on something that never
connected, and `listen` on a datagram socket are all **unspellable** rather
than runtime errors, and the type is the documentation.

**Rule K-11 — the transitions consume.** `tcp_listen(builder)` consumes an
unbound socket and produces a `TcpListener`; `accept` borrows the listener and
produces a `TcpStream`; `shutdown_write` borrows a stream and marks it. A
transition that consumes cannot leave a value of the old type behind for
somebody to use, which is the property that makes the typestate real rather
than decorative.

**Rule K-12 — the builder is the only place an "unbound socket" exists.**

```nitpick
pub struct:SockBuilder = { Sock:s; };          // move-only, short-lived

tcp_socket_v4() -> SockBuilder                  // socket(AF_INET, SOCK_STREAM|…, IPPROTO_TCP)
builder.reuse_addr(true) -> SockBuilder         // options, before bind
builder.bind(addr)       -> SockBuilder
builder.listen(backlog)  -> TcpListener         // consumes
builder.connect(addr, within) -> TcpStream      // consumes; §3 of STREAM_MODEL
```

Options that must be set **before** `bind` (`SO_REUSEADDR`, `IPV6_V6ONLY`) are
only reachable on the builder, so setting them too late is unspellable too.
Options that may be set at any time are on the concrete types
(`OPTION_MODEL.md` §3).

---

## 5. Binding

**Rule K-13.** `bind(descr, addr_bytes, addr_len)` where the bytes and the
length come from `ADDRESS_MODEL.md`'s encoder. The length is **not**
`sizeof(sockaddr_storage)`: for `AF_UNIX` it is significant to the kernel
(§9), and passing a constant 128 there changes the meaning of the address.

**Rule K-14 — an ephemeral bind is read back.** Binding to port 0 asks the
kernel to choose; the chosen port is only knowable through `getsockname`.
`bind` therefore records the bound address into the builder by calling
`getsockname` immediately, so `listener.local_addr()` is a field read and not a
syscall, and a server that logs its own port does not have to know to ask.

**Rule K-15 (SK-032) — `SO_REUSEADDR` is set by default on a listener, and
`SO_REUSEPORT` never is.**

`SO_REUSEADDR` on a TCP listener means "bind even though a previous connection
is in `TIME_WAIT`". Without it, a server restarted within the `TIME_WAIT`
window fails with `EADDRINUSE` — which is the single most common surprise in
socket programming and is almost never what the operator wanted. It does *not*
permit two live listeners on the same address; that is `SO_REUSEPORT`, which
silently load-balances between processes and is a deployment decision nobody
should get by default. Both are on the builder and either can be set
explicitly.

---

## 6. Listening

**Rule K-16.** `listen(descr, backlog)`. The backlog is a **hint**: the kernel
caps it at `net.core.somaxconn`, and since Linux 5.4 that default is 4096. The
library passes what it is given, does not clamp, and documents that the
effective value is the kernel's business — a library that silently clamped
would make an operator's tuning invisible.

**Rule K-17.** `backlog` of 0 is legal and means "the kernel's minimum", not
"refuse connections". A caller that wants to stop accepting drops the listener.

---

## 7. Accepting

**Rule K-18.** `accept4(descr, addr, addrlen, SOCK_NONBLOCK | SOCK_CLOEXEC)`,
returning a `TcpStream` (or `UnixStream`) **and** the peer's `SocketAddr`. The
address is filled by the kernel into a caller-owned buffer whose length is
passed in and updated on return; a truncated address (returned length greater
than the buffer) is `ESockCapacity`, never a silently short address.

**Rule K-19 (SK-031) — the accept loop's errors are three different things**, and
conflating them is how an accept loop becomes a busy loop or a dead server:

| Return | Meaning | What the loop does |
|---|---|---|
| a descriptor | a connection | handle it |
| `EAGAIN` | nothing pending | `io_ready(listener, EPOLLIN, within)` and retry |
| `EINTR` | a signal cut the call | retry immediately, no wait |
| `ECONNABORTED` | the peer went away between SYN and accept | **retry immediately** — this is not an error about the listener |
| `EMFILE` / `ENFILE` | the process or system is out of descriptors | §7.1 |
| anything else | the listener is broken | fail, forwarded verbatim |

**Rule K-19.1 — `EMFILE` does not kill the server and does not spin.** Out of
descriptors, `accept4` fails immediately and the connection stays pending, so a
naive retry loop spins at 100% CPU accepting nothing. `nsockets`' accept
returns `EMFILE` to the caller **with the connection still pending**, and
`server/` (`CONCURRENCY_MODEL.md` §5) implements the standard answer: back off
for a bounded interval before retrying, so the server degrades instead of
melting. The bound is a named constant, not a guess.

---

## 8. Shutdown, and the difference from drop

**Rule K-20 (SK-019).** `shutdown(descr, how)` with `SHUT_RD` = 0, `SHUT_WR` = 1,
`SHUT_RDWR` = 2. It is **not** the same as dropping the socket and the two are
never conflated:

| | `shutdown(SHUT_WR)` | drop |
|---|---|---|
| Sends FIN | yes | yes |
| Descriptor still open | **yes** | no |
| Can still read | **yes** | no |
| Affects duplicated descriptors | **yes — all of them** | no, only this one |

Half-close is how a protocol says "I have sent everything; tell me what you
have" — HTTP/1 without keep-alive, a `nc -N` pipeline, and every
request/response protocol over a stream that does not frame its own end. A
library without it forces the caller to close and lose the reply.

**Rule K-21.** `Sock.shut` records what was shut down, and an operation the
state forbids fails `ESockState` before the syscall — a `send` after
`SHUT_WR` returns a clear answer rather than `EPIPE`, which would be
indistinguishable from the peer having gone.

**Rule K-22 — `shutdown` on an unconnected socket is `ENOTCONN`**, forwarded.
The library does not pre-check it: the kernel's answer is the accurate one and
a race with the peer's own close makes any pre-check a lie.

---

## 9. Unix-domain addresses have a filesystem side effect

**Rule K-23 (SK-020).** `bind` on a pathname `AF_UNIX` socket **creates a
filesystem entry**, and `close` does **not** remove it. A second `bind` to the
same path fails `EADDRINUSE` even though nothing is listening.

**`nsockets` does not unlink it.** The reasons, in order:

- The path is the **caller's**, chosen by the caller, possibly shared with
  another process, possibly a symlink, possibly in a directory the caller does
  not control. A library that removes files it did not create is a library
  nobody can reason about.
- An unlink at drop time would run at scope exit, which is *also* where a
  correctly-restarting server wants the socket to still exist for a moment.
- `defer` does not run on a trap, so an unlink-at-drop would work exactly on
  the paths where the caller was going to clean up anyway, and not on the ones
  where it mattered.

**Rule K-24 — the spellings the library does provide.** `unix_unlink(path)`,
which is `unlink(2)` and nothing more, so the caller's cleanup is one obvious
call; and `unix_bind_replacing(path)`, which unlinks *then* binds, for the
"restart my own daemon" case — named so that a reader sees the destructive act
in the call.

**Rule K-25 — the abstract namespace has no filesystem entry at all**, and it
is the better answer where portability allows: an address whose first byte is
`0` lives in a kernel-private namespace, disappears when the last descriptor
closes, and cannot be left behind. `ADDRESS_MODEL.md` §5 has its encoding, and
the encoding is where the classic bug lives.

---

## 10. The headless double

**Rule K-26 (SK-029).** `sock_pair_headless(kind)` returns a connected pair over
`socketpair(AF_UNIX, …)` with `origin == Headless` recorded in both.

That is a deliberately weak double compared to `ntui`'s: a `socketpair` is a
*real* kernel socket, so it exercises the real send and receive paths, the real
non-blocking behaviour, the real `MSG_NOSIGNAL` handling and the real reactor —
and it needs no network, no port, no address, and no privilege. It is what
`TESTING.md` §2 builds almost the entire suite on.

**Rule K-27.** `origin` is recorded so a test can assert it and so a diagnostic
can say so, and it changes **no behaviour**. A double whose behaviour differs
from the real thing is a double that certifies the wrong code.

---

## 11. Open items

- **O-K1 — `sendmmsg` / `recvmmsg`.** Batched send and receive, a real
  throughput win for a high-rate UDP consumer, and a second error model per
  message. **Recommendation:** out at 1.0, revisited when a consumer measures a
  need. Recorded so the absence is a decision.
- **O-K2 — `SOCK_SEQPACKET` beyond `AF_UNIX`.** SCTP is the only other
  provider and is not present on most kernels. **Recommendation:** `AF_UNIX`
  only, which is where the useful case (message framing plus reliability plus
  `SCM_RIGHTS`) actually is.
- **O-K3 — whether `sock_adopt` should exist at 1.0.** It is the door for
  socket activation (systemd `LISTEN_FDS`) and for a descriptor received over
  `SCM_RIGHTS`, and it is also the one place `fcntl` appears and the one place
  a caller can hand in something that is not a socket. **Recommendation:** yes,
  with the verification K-9 requires, because the alternative is that a
  consumer writes it themselves without the check.
