# Cycle 0.8 — The server

**`src/server/`: accept-then-spawn, bounded accept, the `EMFILE` back-off, and
`poll_set`.** Composition rather than mechanism — every piece exists by 0.7,
and this cycle assembles them, takes a measurement, and adds the two loops
nobody should write twice.

## Decisions in

`SK-031`, `SK-035`. Settled — and `SK-035` was confirmed by execution in 0.0.0's
probes 09 and 10, which is why this cycle can be planned at all.

**Open questions to settle:** `O-C1` (the counter's type), `O-C2` (**a
measurement**: what a scope with ten thousand joined tasks costs), `O-C3`
(a `SO_REUSEPORT` helper — only if 0.9 asks).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.8.0 | **The accept-then-spawn loop** | a server handling concurrent connections, each in its own task |
| 0.8.1 | **`server_accept_bounded`** — the live-connection ceiling | a server that stops accepting rather than accumulating |
| 0.8.2 | **The `EMFILE` back-off** | a server that degrades instead of melting |
| 0.8.3 | **`poll_set`** — many sockets, one task | a proxy shape without a task per connection |
| 0.8.4 | **The measurement** — `O-C2` | a number, recorded, and a shape change only if it demands one |
| 0.8.5 | **Close** | `done/0.8/`, `0.9.0.md` written |

## Checklist

### 0.8.0 — the loop
- [ ] `serve` in the shape of `CONCURRENCY_MODEL.md` C-8: accept, then
      `drop handle(move(a.stream), a.peer)`
- [ ] a comment at the `move` naming `SK-035` and probe 10, because that one
      token is the whole reason the shape is what it is
- [ ] a handler's error reaching the enclosing scope's join and being observable
      (D-163), asserted by a test whose handler fails
- [ ] **a test that a stream cannot be sent through a channel** — a rejection
      test asserting `NITPICK-TYPE-057`, so the constraint the design rests on
      has a test rather than a memory
- [ ] concurrent connections handled concurrently, asserted by interleaving
- [ ] `// stress: 40`

### 0.8.1 — bounded accept
- [ ] `server_accept_bounded(listener, max_live, within)` with a live count
- [ ] `O-C1` decided: `atomic<int32>` or plain
- [ ] above the ceiling, **the loop stops accepting** and connections stay in
      the kernel's backlog where they belong (C-10)
- [ ] **`max_live` has no default** and is a required parameter, because the
      right number is the deployment's
- [ ] a test that opens `max_live + 10` connections and asserts the extra ten
      are pending rather than accepted, and are served once earlier ones finish

### 0.8.2 — the `EMFILE` back-off
- [ ] `EMFILE`/`ENFILE` from `accept4` returned with the connection pending
      (K-19.1)
- [ ] `NSOCK_EMFILE_BACKOFF` (50 ms, a named constant) before a retry
- [ ] **a test that actually exhausts the descriptor table** — `setrlimit`
      through `sys`, then accept — and asserts the server stays alive, does not
      spin, and recovers when descriptors free up
- [ ] the library logs nothing; it returns the condition and the count (C-11)

### 0.8.3 — `poll_set`
- [ ] `poll_set` over up to `NSOCK_POLLSET_MAX` descriptors, using `io_watch`
      for all but one and `suspend_io` for the last (C-4, C-13)
- [ ] **every watched descriptor's `io_unwatch` on every exit path**, including
      the error paths — the thing every consumer would get wrong, which is why
      the loop is in the library
- [ ] an `arena<TcpStream>` + `Handle<TcpStream>` example holding the
      connections (C-12)
- [ ] a proxy-shaped test: two sockets in one task, bytes forwarded both ways

### 0.8.4 — the measurement
- [ ] **`O-C2`**: a server with 100, 1 000 and 10 000 live spawned handlers, and
      the cost of the scope's join list measured — memory, and the time to join
      at scope exit
- [ ] the numbers recorded in this file, with the machine they were taken on
- [ ] **a shape change only if the measurement demands one.** If a scope with
      ten thousand entries is expensive, the answer is a nested scope per batch
      of connections — and that is a decision recorded here, not a guess made in
      advance

## Gate

A server handling concurrent connections with a handler failure observable; a
bounded accept proven to leave connections pending; an `EMFILE` exhaustion the
server survives; and `O-C2`'s numbers recorded.

## Watch for

- **`SK-035` is a language constraint, not a preference**, and the rejection
  test in 0.8.0 is what keeps it visible. Somebody will eventually try to add a
  worker pool; the test is what tells them why they cannot, in one line, at
  compile time.
- **The `EMFILE` test needs `setrlimit`** through `sys` and must restore the
  limit afterwards, or every subsequent test in the same process runs out of
  descriptors. It is the one test in the suite that changes process-wide state.
- **`O-C2` is a measurement and the plan does not pre-judge it.** Writing "we
  will use a nested scope" now would be guessing; taking the number and then
  deciding is the whole point of scheduling it here.
