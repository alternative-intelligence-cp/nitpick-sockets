# Cycle 0.3 — Streams

**`src/stream/`: `TcpListener`, `TcpStream`, connect's `EINPROGRESS` protocol,
accept, the prelude's `Reader`/`Writer`, `write_all`, half-close.** The cycle
that makes the library usable.

## Decisions in

`SK-010`, `SK-014`, `SK-018`, `SK-019`, `SK-027`, `SK-031`. All settled; two rows of `SK-031`'s table wait on the compiler's answer to O-N5 (SK-104).

**Open questions to settle:** `O-T1` (`TCP_NODELAY`'s default — **against a
measurement**), `O-T2` (how `write_all` reports a partial count), `O-S1`
(whether `ESockState` earns its place, which decides whether the budget can
drop to three).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.3.0 | **`TcpStream` and the `Reader`/`Writer` impls** | a `socketpair`-backed stream driven through `dyn Writer` |
| 0.3.1 | **Connect** — the full `EINPROGRESS` protocol | a connect to a closed port reporting `ECONNREFUSED`, not success |
| 0.3.2 | **Listen and accept** — K-19's error table | a loopback server accepting under `// stress: 40` |
| 0.3.3 | **`write_all` and partial writes** | a large send over a small socket buffer, delivered whole |
| 0.3.4 | **Half-close and `IoEof`** | a request/response exchange ending in a half-close |
| 0.3.5 | **Close** | `done/0.3/`, `0.4.0.md` written |

## Checklist

### 0.3.0 — `TcpStream` and the traits
- [ ] `TcpStream` with its recorded `peer` and `local` (T-1)
- [ ] `impl:TcpStream:Reader` and `impl:TcpStream:Writer` with the prelude's **exact** signatures — `Self->`, `async`, `Duration:within`, `fixed uint8[]:wsrc` on `write` (`NITPICK-TYPE-014` otherwise, probe 06b) and `Writer`'s `flush` (TYPE-048 requires the impl to keep the trait's `async`; SK-103)
- [ ] **the `Writer` impl uses `sendto` with `MSG_NOSIGNAL`, not the floor's `write`** (T-5), with a comment at the site saying why it cannot share `ByteWriter`'s body
- [ ] `flush` is `pass NIL` and a comment says why that is correct (T-4)
- [ ] a `TcpStream` driven through `dyn Writer`, and through `TextWriter<TcpStream>` — the interoperability property `SK-027` exists for
- [ ] `check_no_floor_write` covering the new impls

### 0.3.1 — connect
- [ ] the full sequence from `STREAM_MODEL.md` T-8: immediate success, `EINPROGRESS`, wait `EPOLLOUT`, `SO_ERROR` **once** — spelled, at the pin, without naming `EINPROGRESS`: a second `connect` after the wait answers the outcome (SK-104, probe 08)
- [ ] **a connect to a closed loopback port reporting `ECONNREFUSED`** — the test that proves writability is not success
- [ ] a second `SO_ERROR` read returning 0, asserted, so the read-once rule has a test (T-9)
- [ ] `EINTR` during connect does **not** re-call `connect` (T-8.5); a test that a re-call would spin on `EALREADY`
- [ ] `EAGAIN` on `AF_UNIX` (full backlog) **is** retried — the one place the families differ
- [ ] the deadline expiring drops the socket rather than leaving it half-connecting
- [ ] `getsockname`/`getpeername` filled once on success (T-10)
- [ ] `// stress: 40` on both the success and the failure legs

### 0.3.2 — listen and accept
- [ ] `accept4` with `SOCK_NONBLOCK | SOCK_CLOEXEC`, returning a stream **and** the peer address
- [ ] a truncated returned address is `ESockCapacity`, never a silently short address (K-18)
- [ ] K-19's error table implemented arm by arm, each with a test:
  - [ ] `EINTR` retries immediately
  - [ ] **`ECONNABORTED` retries immediately** — the test connects and resets before the accept, and asserts the server survives (T-13) — **waits on O-N5** (SK-104)
  - [ ] `EAGAIN` waits on `EPOLLIN`
  - [ ] `EMFILE` is returned with the connection still pending (K-19.1) — **waits on O-N5** (SK-104)
- [ ] a loopback accept loop under `// stress: 40`

### 0.3.3 — `write_all` and partial writes
- [ ] `write` returns what the kernel took; a short count is not an error (T-17)
- [ ] `stream_write_all` advancing by what was accepted and re-waiting on `EPOLLOUT`
- [ ] `O-T2` decided: how the partial count rides on a deadline failure
- [ ] a test that fills the socket buffer (a small `SO_SNDBUF`, a peer that does not read) and asserts `write_all` delivers everything once the peer drains
- [ ] a test that asserts the delivered count on a deadline expiry

### 0.3.4 — half-close and `IoEof`
- [ ] a stream read of zero bytes reported as **`IoEof`**, never as a successful zero (T-14)
- [ ] a read into a zero-length slice returning zero and **not** `IoEof` (T-15)
- [ ] `IoEof` sticky on subsequent reads (T-16)
- [ ] `stream_shutdown_write` sending FIN and leaving the socket readable
- [ ] a write after `shutdown_write` failing `ESockState`, not `EPIPE` (T-21)
- [ ] a full request/response exchange: send, half-close, read to `IoEof`
- [ ] `O-S1` decided — does `ESockState` earn its place, or can the budget drop to three?

### 0.3.5 — close
- [ ] `O-T1` decided **against a measurement**: a request/response round trip timed with Nagle on and off, and the number recorded
- [ ] findings written; `0.4.0.md` written; archived

## Gate

A loopback client and server exchanging bytes both ways; a connect to a closed
port reporting `ECONNREFUSED`; a half-close producing `IoEof` on the peer; and
every one of them green under `// stress: 40`.

## Watch for

- **Loopback connects usually complete immediately**, so the `EINPROGRESS` path
  is exercised by the *failure* leg and by a connect to a host that drops
  packets. A suite that only tests the success leg on loopback has not tested
  `SK-014` at all — this is exactly the compiler's "right on straight-line code,
  wrong after a merge" lesson in this library's terms.
- **`ECONNABORTED` will not appear on its own.** The test has to cause it: connect
  and reset, in a tight loop, until the accept sees one. It is worth the effort,
  because failing the loop on it is how a server dies from a client pressing
  Ctrl-C.
- **`end` and `in` are keywords**, and a stream cycle wants both.
