# Streams

Connection-oriented sockets: `TcpStream`, `TcpListener`, `UnixStream`,
`UnixListener`, and the `SOCK_SEQPACKET` pair. How a connection is made, how
bytes move, and how it ends.

---

## 1. The shape

```nitpick
pub struct:TcpStream    = { Sock:s; SocketAddr:peer; SocketAddr:local; };
pub struct:TcpListener  = { Sock:s; SocketAddr:local; };
pub struct:UnixStream   = { Sock:s; UnixAddr:peer; UnixAddr:local; };
pub struct:UnixListener = { Sock:s; UnixAddr:local; };
```

**Rule T-1 — the addresses are recorded at construction, not asked for.** They
are read once by `getsockname`/`getpeername` at the moment the connection is
made and stored, so `stream.peer()` is a field read. A caller logging every
connection's peer should not be making a syscall to do it, and the address
cannot change under a connected socket.

**Rule T-2.** All four are move-only (they hold a `Sock`, which holds an
`OwnedFd`) and none of them can be a channel element (`SAFETY.md` §1,
`CONCURRENCY_MODEL.md` §3).

---

## 2. Reader and Writer

**Rule T-3 (SK-027).** `TcpStream` and `UnixStream` implement the **prelude's**
`Reader` and `Writer` traits, unchanged:

```nitpick
impl:TcpStream:Reader = {
    async func:read = int64(TcpStream->:self, uint8[]:dest, Duration:within) { … };
};
impl:TcpStream:Writer = {
    async func:write = int64(TcpStream->:self, fixed uint8[]:wsrc, Duration:within) { … };
    async func:flush = NIL(TcpStream->:self, Duration:_~within) { pass NIL; };
};
```

This is the headline interoperability property: everything already written
against `Reader`/`Writer` — the prelude's `TextReader`, `TextWriter`,
`LineBufWriter`, a `dyn Writer` diagnostic sink, anything a consumer wrote for
files — works over a socket with no change. `IO_REFERENCE.md` §10 records
sockets as an open item in the language's own I/O specification; this is the
answer to it.

**Rule T-4 — `flush` is `pass NIL` and that is correct.** Nothing is buffered
at this layer. Buffering is a *type* you compose (`LineBufWriter<TcpStream>`),
which is D-072's rule and the prelude's own shape — `ByteWriter`'s `flush` is
`pass NIL` for the same reason.

**Rule T-5 — the `Writer` impl uses `sendto`, not the floor's `write`.**
`SAFETY.md` S-2. This is the rule most likely to be broken by somebody copying
`impl:ByteWriter:Writer` out of the prelude, which uses `write(2)` because it
writes to a file. On a socket, `write(2)` raises `SIGPIPE` and terminates the
process. **The two impls cannot share a body**, and a comment at both sites
says so.

**Rule T-6 — the retry loop is the prelude's shape**, and only the syscall
differs:

```
give_up = mono_now() + within.ns
loop:
    r = sendto(descr, ptr, len, MSG_NOSIGNAL, NULL, 0)
    if !r.is_error         -> pass r.value            // may be SHORT; see §6
    if r.err == Interrupted -> retry immediately
    if r.err == WouldBlock  -> rem = give_up - mono_now()
                               if rem <= 0 -> fail DeadlineExceeded
                               await io_ready(descr, EPOLLOUT, rem)
                               retry
    otherwise               -> fail r.err             // forwarded verbatim
```

`EPOLLIN` is `1` and `EPOLLOUT` is `4` — the values the prelude's own
`ByteReader`/`ByteWriter` pass to `io_ready`.

**Rule T-7 — a resume from `io_ready` means readiness was *signalled*, not
that the operation will succeed.** The syscall is always retried; a retry that
still says `EAGAIN` waits again on the time that remains. This is D-184's
stated contract and it is why the loop is a loop.

---

## 3. Connect

**Rule T-8 (SK-014) — the `EINPROGRESS` protocol, in full.** On a non-blocking
socket `connect` almost never completes immediately. The sequence is:

1. `connect(descr, addr, addrlen)`.
2. **`0`** — connected immediately. This happens for `AF_UNIX` and for a
   loopback TCP connection, and a library that only tested against a remote
   host will not have exercised it.
3. **`EINPROGRESS`** (`-115`) — the handshake is running. Wait for the socket
   to become **writable**: `io_ready(descr, EPOLLOUT, remaining)`.
4. On readiness, **`getsockopt(SOL_SOCKET, SO_ERROR)`**. This is the step that
   matters: the socket becomes writable on **both** success and failure, so a
   library that treats writability as success reports a connected socket for a
   connection that was refused.
   - `SO_ERROR == 0` → connected.
   - otherwise → **fail with that errno**, forwarded verbatim, so a caller sees
     `ECONNREFUSED` (`-111`), `ETIMEDOUT` (`-110`) or `EHOSTUNREACH` (`-113`)
     and can tell them apart.
5. **`EINTR`** — the handshake continues in the background. Do **not** re-call
   `connect`; go to step 3. A second `connect` on a socket already connecting
   returns `EALREADY`, and a loop that retries on `EINTR` by re-calling
   `connect` spins on `EALREADY` forever.
6. **`EAGAIN` on `AF_UNIX`** — the listener's backlog is full. This one *is*
   retryable by re-calling `connect` after a wait, and it is the one case where
   the two families genuinely differ.
7. Deadline expiry at any point → `DeadlineExceeded`, and the socket is
   dropped (its descriptor closed) rather than left half-connecting.

**Rule T-9.** `SO_ERROR` is **read exactly once** and reading it clears it.
A second read returns 0 and would report success for a failed connection.

**Rule T-10.** After a successful connect, `getsockname` and `getpeername` are
called once to fill `local` and `peer` (T-1). For an ephemeral local port this
is the only way to know it.

---

## 4. Listen and accept

**Rule T-11.** `accept` borrows the listener and produces a stream plus the
peer address (`SOCKET_MODEL.md` §7), through `accept4` with
`SOCK_NONBLOCK | SOCK_CLOEXEC`.

**Rule T-12 — the accept loop's shape**, with K-19's error table applied:

```
loop:
    r = accept4(listener, storage, &len, SOCK_NONBLOCK|SOCK_CLOEXEC)
    if !r.is_error          -> a stream
    if r.err == Interrupted  -> retry immediately
    if r.err == ConnAborted  -> retry immediately          // not our problem
    if r.err == WouldBlock   -> io_ready(listener, EPOLLIN, rem); retry
    if r.err == TooManyOpenFiles|FileTableFull-> fail it: the caller backs off (K-19.1)
    otherwise                -> fail r.err
```

**Rule T-13 — `ECONNABORTED` is not an error about the listener.** The peer
sent a SYN and then reset before the accept. Failing the accept loop on it kills
a server because a client pressed Ctrl-C at the wrong moment, and it is a
documented, expected condition. Retrying immediately is correct.

---

## 5. Reading, and end of stream

**Rule T-14 — a stream read of zero bytes is end of stream, and it is reported
as `IoEof`** (`-4096`, the prelude's identity — `SAFETY.md` S-7). It is
**never** returned as a successful read of zero, because a caller cannot
distinguish "the peer is done" from "nothing to read" in a zero, which is
exactly the ambiguity `IO_REFERENCE.md` §2 exists to remove and exactly the
defect the compiler's own notes record removing three times.

**Rule T-15.** `read` into a zero-length slice returns zero without a syscall
and is **not** `IoEof`. Zero asked is zero delivered — the floor's own rule.

**Rule T-16 — after `IoEof`, further reads keep returning `IoEof`.** The
condition is sticky as far as this library is concerned; it does not become an
error and it does not become a zero.

---

## 6. Partial writes

**Rule T-17 — `write` returns what the kernel took, and a short count is not
an error.** A `send` of 64 KiB on a stream may take 8 KiB. That is the POSIX
contract, the prelude's `Writer` contract, and the shape every correct caller
already handles.

**Rule T-18 (SK-018) — `stream_write_all` is the loop, and it is in the
library** so
that no consumer writes it again:

```nitpick
async func:stream_write_all = NIL(TcpStream->:s, fixed uint8[]:src, Duration:within);
```

It advances by what was accepted, re-waits on `EPOLLOUT` for the remainder, and
**on a deadline reports how many bytes it had delivered** — because a caller
that has sent half a message needs to know that, and a bare
`DeadlineExceeded` would leave the protocol state unknowable. The count rides
as a field on the error's companion value, not as a new error identity
(`SAFETY.md` S-5).

**Rule T-19 — a partial write followed by a failure is not a rollback.** The
bytes the kernel took are gone into the connection. The library says so; there
is nothing else true to say.

---

## 7. Half-close

**Rule T-20.** `stream_shutdown_write(s)` sends FIN and leaves the socket
readable (`SOCKET_MODEL.md` §8). This is what a request/response protocol over
a stream needs: send the request, half-close so the peer sees end of input,
read the reply.

**Rule T-21.** After `shutdown_write`, a `write` fails `ESockState` rather than
`EPIPE`, so "I shut this down myself" is distinguishable from "the peer went
away". After `shutdown_read`, a `read` returns `IoEof`.

**Rule T-22 — `shutdown` affects every descriptor for the connection**, not
just this one, because it acts on the socket rather than on the file
description. Where a descriptor has been duplicated — passed over `SCM_RIGHTS`,
inherited by a child — that is a shared effect, and it is stated because
"close is per-descriptor, shutdown is per-socket" is the asymmetry that
surprises people.

---

## 8. Linger, and what closing actually does

**Rule T-23.** Dropping a stream closes the descriptor. With the default
`SO_LINGER` (off), the kernel sends any queued data and the FIN in the
background, and the close returns immediately. **The close does not tell you
the data arrived**, and no close on any platform does.

**Rule T-24 — a caller that must know the peer received everything reads for
it.** `shutdown_write`, then read until `IoEof`. That is the only mechanism
that works, and the library documents it in one place rather than letting
`SO_LINGER` look like it does the job.

**Rule T-25 — `SO_LINGER` with a nonzero timeout is not in the option
surface** (`OPTION_MODEL.md` §5). It makes `close` block for up to the timeout,
which is a thread-parking wait this library does not have a way to express
(D-071) and does not want. `SO_LINGER` with timeout **zero** — send RST
instead of FIN, discard queued data — *is* available, because it is an
instantaneous, deliberate, occasionally necessary act with no wait in it.

---

## 9. `SOCK_SEQPACKET`

**Rule T-26.** `AF_UNIX` `SOCK_SEQPACKET` is supported and is the best
transport for a local protocol: connection-oriented and reliable like a stream,
message-framed like a datagram, and it carries `SCM_RIGHTS`. The compiler's own
Bridge would be a natural consumer.

**Rule T-27 — a `SeqPacket` receive is a whole message or an error.** A message
too large for the supplied buffer is **truncated and reported**
(`DATAGRAM_MODEL.md` §4's rule, applied here), never silently cut. It does not
implement `Reader`/`Writer`: those traits are byte-stream shaped, a partial
read of a message is meaningless, and forcing a message type through a byte
interface is how framing gets lost.

---

## 10. Open items

- **O-T1 — `TCP_NODELAY`'s default.** Nagle's algorithm coalesces small writes
  and adds up to 40 ms of latency to a request/response protocol; disabling it
  by default costs bandwidth on a bulk sender that writes badly.
  **Recommendation:** leave the kernel's default (Nagle **on**) and make
  `nodelay(true)` one call, because a library that silently changes a
  transport's behaviour is worse than one that makes you ask. Settled at cycle
  0.3's close, against a measurement rather than taste.
- **O-T2 — whether `stream_write_all`'s partial count should be a field on an
  error companion or a different return shape** (`Result<int64>` where the
  value is the count on both paths). **Recommendation:** the companion field,
  because the success path should not have to be read as "how much of it
  succeeded". Settled at 0.3.
