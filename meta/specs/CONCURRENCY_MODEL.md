# Concurrency

How a wait happens, and what shape a server can have. The second half is not a
matter of taste: the language decides it, and the decision is sharper than in
any other language this library could have been written in.

---

## 1. Every wait is a task suspension

**Rule C-1.** `nsockets` never parks a thread. Every socket is non-blocking
(`SOCKET_MODEL.md` K-8), every operation that would block returns `EAGAIN`,
and the library suspends the **task** through the language's epoll reactor:

```nitpick
await io_ready(descr, events, within)          // one descriptor
await io_ready2(fda, eva, fdb, evb, within)    // two
```

`EPOLLIN` is `1` and `EPOLLOUT` is `4` — the values the prelude's own
`ByteReader` and `ByteWriter` pass. `io_ready` registers one-shot, parks, and
**removes the registration on every exit path** through a `defer`, so a
registration lives exactly as long as its wait.

**Rule C-2 — readiness is a hint and the syscall is always retried.** A resume
from `io_ready` says something was signalled, not that the operation will
succeed: a spurious wake, a datagram consumed by another task, an error
condition. Every call site loops (`STREAM_MODEL.md` T-6). This is D-184's
stated contract.

**Rule C-3 — `EPOLLERR` and `EPOLLHUP` are always reported** whether or not
they were requested, so a wait on `EPOLLIN` returns when the peer resets. The
library does not inspect the returned event mask — it re-tries the syscall,
which reports the real condition with a real errno. Reading the mask would be a
second, less accurate source of truth.

**Rule C-4 — waiting on several sockets is `io_watch` plus one `suspend_io`**,
not a channel merge. The language has no `select` across channels (D-072) and
needs none here: `io_watch(fd, events)` arms a descriptor without parking, and
one `suspend_io` then parks for all of them. The compiler's Bridge waits on
three descriptors this way. Fan-in over N sockets in one task is therefore
expressible, bounded, and needs nothing this library has to invent.

---

## 2. What a socket may cross

Two language rules, measured in the compiler's own source, and they point in
opposite directions. Both matter. *(2026-10-29: and run, at compiler `2e1cb4a`,
by cycle 0.0.0's probes 09, 09b, 10 and 10b — an `OwnedFd`, and a struct
holding one, are `NITPICK-TYPE-057` as channel elements; a move into a spawned
task compiles and runs; a borrow across the spawn is `NITPICK-BORROW-004`.)*

**Rule C-5 — an `OwnedFd` is refused as a channel element.**
`chan_elem_verdict_recorded` in `src/frontend/types.npk` answers
`CHAN_ELEM_FD` for `TY_OWNEDFD`, and `type_contains_borrow_recorded` answers
`true` for it — so a **struct holding one** is refused too, transitively. The
compiler's comment states the reasoning: *"An OwnedFd — and so every stream
holding one — is SCOPE-BOUND: the scope that owns it closes it, so it may not
ride a channel."* `IO_REFERENCE.md` §6 says the same about streams. The
diagnostic is `NITPICK-TYPE-057`.

**Rule C-6 — an `OwnedFd` *may* be moved into a spawned task.**
`type_holds_pointer` in `src/frontend/analysis/escape.npk` answers **`false`**
for `TY_OWNEDFD`, with the comment *"an OwnedFd is a descriptor NUMBER
(D-185)"* — so it does not trip D-004's "a borrow cannot cross a spawn". A
**move** is legal; a **borrow** of a socket across a spawn is still refused,
like every borrow. `IO_REFERENCE.md` §6 states it directly: *"A MOVE into a
spawn is legal (D-185): the join (D-062) bounds the thread by the creating
scope, so closing responsibility stays inside it."*

**Rule C-7 — together, those two decide the server model, and there is only
one.** A connection can be handed to a task. It cannot be put in a queue. So:

| Shape | Legal? | |
|---|---|---|
| accept → **spawn a task, moving the stream in** | **yes** | C-6 |
| accept → push the stream onto a channel for a worker pool | **no** | C-5 |
| accept → store the stream in a `Vec` that outlives the scope | no | it is move-only and the scope owns it |
| accept → handle it inline, one at a time | yes | trivially |

The middle row is what almost every socket library in every other language
does, and it is unspellable here. That is not a limitation to work around: a
worker queue is precisely a structure in which a connection's closing scope is
no longer the scope that accepted it, which is the property the language is
refusing. `nsockets` builds on the shape the language permits and documents why
the other one is absent, so nobody spends a day trying to defeat the checker.

---

## 3. The server loop

**Rule C-8 (SK-035) — the shape, and the whole of it:**

```nitpick
async func:serve = NIL(TcpListener->:lis, Duration:idle) {
    while (true) {
        Accepted:a = relay await tcp_accept(lis, idle);
        drop handle(move(a.stream), a.peer);   // spawns; the move is C-6
    }
};
```

`drop handle(…)` on an `async` callee spawns it (`CONCURRENCY_REFERENCE.md`
§2.2). The task's error is **not** discarded — D-163 routes it to the enclosing
scope's join, which relays the first child error verbatim after every child has
finished. A handler that fails is therefore observable, which is what makes
this a server rather than a place where errors go to die.

**Rule C-9 — a spawned task cannot outlive the scope that spawned it**
(D-062), and scope exit joins every unfinished one under the executor's
mandatory deadline (D-083). For a server that is exactly right: `serve`'s scope
is the program's lifetime, and shutting it down joins every live connection
under a deadline rather than severing them.

**Rule C-10 — the connection count is bounded by something, and the library
says by what.** Every spawned handler is an entry on the scope's join list
until it finishes. A server accepting faster than it completes accumulates
frames without bound, and the failure mode is memory rather than an error. The
library therefore ships `server_accept_bounded`, which holds a live-connection
count in an `atomic<int32>` and stops accepting — leaving connections in the
kernel's backlog, where they belong — above a caller-supplied maximum. The
maximum is a parameter with no default, because the right number is the
deployment's and a library that guessed would be wrong quietly.

**Rule C-11 — the `EMFILE` back-off is part of the loop.**
`SOCKET_MODEL.md` K-19.1: out of descriptors, `accept4` fails immediately with
the connection still pending, so a naive retry spins. `server_accept_bounded`
waits `NSOCK_EMFILE_BACKOFF` (a named constant, 50 ms) before retrying, which
turns a melt into a degradation. It also logs nothing, because a library does
not own an application's diagnostics — it returns the condition and the count.

---

## 4. When a collection of sockets is genuinely wanted

**Rule C-12.** A proxy, a multiplexer or a poller holds many connections in one
task rather than one task each. A `Vec<TcpStream>` is legal (they are
move-only, so every read out is a move, which is awkward but not forbidden);
the better shape is `arena<TcpStream>` with `Handle<TcpStream>`, which is what
the language provides for exactly this — generation-checked indices, no
aliasing, and a stale handle answers `StaleHandle` rather than dangling.

**Rule C-13.** Such a task waits with `io_watch` over each descriptor and one
`suspend_io` (C-4). `nsockets` provides the loop as `poll_set`, bounded at
`NSOCK_POLLSET_MAX` descriptors, because the alternative is every consumer
writing the same `io_watch` fan-out and getting the `io_unwatch` on the error
path wrong.

---

## 5. Threads

**Rule C-14 — `nsockets` creates no threads.** It suspends tasks, and tasks are
pinned to the thread that spawned them (D-032). An application that wants
several executors creates several threads, each with its own listener on a
`SO_REUSEPORT` socket — which is the shape that actually scales, because the
kernel does the load balancing and no socket crosses a thread.

**Rule C-15 — a socket must not be used from two tasks concurrently**, and the
language mostly prevents it: a `Sock` is move-only, and a borrow cannot cross a
spawn (D-004). What remains possible is two tasks in the *same* scope both
holding `TcpStream->` borrows, which the checker permits and which is a race
the library cannot see. The rule is stated, the documentation says it, and the
shape that avoids it is the one C-8 already recommends: one task owns the
stream.

---

## 6. Open items

- **O-C1 — whether `server_accept_bounded`'s counter should be an
  `atomic<int32>` or a plain one.** Tasks are pinned to a thread (D-032) and
  the accept loop is one task, so a plain `int32` would be correct for a
  single-executor server and wrong the moment somebody runs two.
  **Recommendation:** `atomic<int32>`, at the cost of one SeqCst operation per
  accept — which is nothing next to the accept itself. Settled at cycle 0.8.
- **O-C2 — the join list's behaviour under ten thousand live connections.**
  D-207 makes the join list a per-scope LIFO stack; whether a completed task
  leaves it promptly, and what a scope with ten thousand entries costs, is a
  **measurement** and cycle 0.8 takes it. If the cost is real the answer is a
  nested scope per batch of connections, which is a shape change and wants the
  measurement first.
- **O-C3 — `SO_REUSEPORT` multi-executor servers.** The shape works and is
  described in C-14, but the library ships no helper for it. **Recommendation:**
  add one at 0.8 only if cycle 0.9's application wants it; a helper for a shape
  nobody has run is a helper that is wrong.
