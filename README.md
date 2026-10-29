# nsockets

BSD sockets for **[Nitpick](https://github.com/alternative-intelligence-cp/nitpick)** —
the safety-critical systems language. The package is `nsockets` (`SK-001`). AF_UNIX, TCP and UDP over IPv4 and IPv6,
straight to the kernel. No libc, no C, no dependency of any kind.

> **Status: planning.** No code yet. The specification set is in
> [`meta/specs/`](meta/specs/) and the plan in
> [`meta/roadmap/`](meta/roadmap/), written in that order and by that
> discipline — specs first, then a cycle map, then execution-grade subcycles,
> then code. The compiler itself is at cycle 1.5 (verification); this library
> is planned now so that implementation can start the day the language stops
> moving.

---

## Why another socket library

Because the parts of a socket API that are hardest to get right are the parts
every C-shaped wrapper leaves to the caller, and Nitpick makes them checkable.

**A write to a dead peer cannot kill your process.** In C, and in every
library that wraps `write(2)` without thinking about it, sending on a socket
whose peer has gone raises `SIGPIPE` and the default disposition is to
terminate. Nitpick's runtime catches `SIGPIPE` with a handler that returns, so
on it that send answers `EPIPE` — and this library does not lean on the
runtime for it: **every send `nsockets` issues carries `MSG_NOSIGNAL`, without
exception**, so the failure arrives as `EPIPE` in `Result.err` where the caller
can see it, whatever the process's disposition is. Its probe 04 measures
both.

**A socket cannot outlive the scope that must close it.** Every socket is an
`OwnedFd`, so the close *is* the drop and there is no `close` in the surface.
The language enforces the rest: an `OwnedFd` is refused as a channel element,
so a connection cannot be queued into a worker pool and then leaked when the
queue outlives its owner. The server model that remains — accept, then spawn a
task bounded by the accepting scope — is the one the language will let you
write, and it is also the one that cannot leak a descriptor.

**A wrong state is unspellable, not merely wrong.** A `Listener`, a `Stream`
and a `Datagram` are different types with different operations. There is no
`Socket` with a mode field to be in the wrong state, no `send` on something
that has not connected, and no `accept` on something that has not listened.

**Every wait is bounded and every wait is a task suspension.** There is no
unbounded `accept`, no unbounded `recv`, and no operation that parks the OS
thread. Readiness comes from the language's epoll reactor, so one stalled peer
stalls nothing else.

**Nothing is inherited by accident.** Every descriptor is created
non-blocking and close-on-exec *atomically*, in the `socket()` and `accept4()`
call itself — never by a follow-up `fcntl` with a window in between.

---

## What it will provide

| Layer | Contents |
|---|---|
| **sys** | the x86-64 socket syscalls and their constants, each carrying the header it came from |
| **addr** | `Ipv4Addr`, `Ipv6Addr`, `IpAddr`, `SocketAddr`, `UnixAddr` — parsing, formatting, and the kernel structures laid out byte by byte |
| **socket** | the common primitive: creation, binding, options, the `OwnedFd` lifetime, and the headless double |
| **stream** | `TcpListener` / `TcpStream` / `UnixListener` / `UnixStream` — connect with its `EINPROGRESS` protocol, accept, half-close, and the prelude's `Reader`/`Writer` traits |
| **datagram** | `UdpSocket` / `UnixDatagram` — connected and unconnected, truncation reported never swallowed, broadcast and multicast |
| **option** | typed socket options: one function per option, no untyped `setsockopt` in the surface |
| **ancillary** | `SCM_RIGHTS` descriptor passing and `SCM_CREDENTIALS` peer identity, over one audited `msghdr` |
| **server** | the accept-then-spawn loop, with backpressure and the `EMFILE` rule |

**Not in scope, by decision**: DNS resolution (a wire protocol and a parser,
not a socket — [`SK-024`](meta/DECISIONS.md)), and TLS (a cryptographic
artifact that wants its own audit — [`SK-025`](meta/DECISIONS.md)). Both are
named rather than implied, so nobody has to guess.

---

## Layout

```
src/          # THE LIBRARY — Nitpick source only
  core/       #   bytes, growable storage, the named bounds
  sys/        #   syscall numbers and kernel constants
  addr/       #   addresses: the types, the parsers, the kernel layouts
  socket/     #   the common primitive and its lifetime
  option/     #   typed socket options
  stream/     #   connection-oriented sockets
  datagram/   #   message-oriented sockets
  ancillary/  #   SCM_RIGHTS and SCM_CREDENTIALS
  server/     #   the accept-then-spawn loop
tests/        # probe, conformance, unit, rejection, fixtures
harness/      # the Python build and test runner, until `npkg` can build a library
tools/        # generators and instruments
examples/     # runnable demonstrations, built and run by the harness
meta/specs/   # the design authority
meta/roadmap/ # the plan, in numbered cycles
docs/         # user-facing documentation, written at 1.0
```

## Specification

[`meta/specs/`](meta/specs/) is the authority on behaviour, and
[`meta/DECISIONS.md`](meta/DECISIONS.md) records every settled design decision
with its reasoning — start there when something looks unusual, because it is
recorded why.

## Plan

[`meta/roadmap/ROADMAP.md`](meta/roadmap/ROADMAP.md) is the cycle map. A cycle
is a folder, a subcycle is a file inside it, and a finished cycle moves to
`meta/roadmap/done/`.

## Requirements

Linux on x86-64, the Nitpick compiler, and LLVM 20.1.2 — the same toolchain the
compiler pins. Nothing else, at build time or at run time.

## Licence

Apache 2.0. See [`LICENSE`](LICENSE).
