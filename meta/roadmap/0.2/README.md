# Cycle 0.2 — The socket primitive

**`src/sys/` and `src/socket/`: the syscall table, `Sock`, the builder, `bind`,
`listen`, `sock_adopt`, and the `socketpair` double.** The first cycle that
opens a descriptor — and the cycle where `SK-013`'s send path lands.

## Decisions in

`SK-010`, `SK-011`, `SK-012`, `SK-013`, `SK-015`, `SK-016`, `SK-029`,
`SK-032`, `SK-033`. All settled.

**Open questions to settle:** `O-K3` (should `sock_adopt` exist at 1.0?
recommendation: yes, with K-9's verification).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.2.0 | **`src/sys/`** — the syscall numbers and kernel constants, each carrying its header | every constant exercised by a program that asserts its *effect*, not its value |
| 0.2.1 | **`Sock` and creation** — the atomic flags, the typestate scaffolding, the `socketpair` double | a connected pair, both ends non-blocking and CLOEXEC |
| 0.2.2 | **The send and receive path** — `sendto`/`recvfrom` with `MSG_NOSIGNAL` | `check_msg_nosignal` live and seen to fail; the `SIGPIPE` regression test green |
| 0.2.3 | **The builder** — pre-bind options, `bind`, `listen`, the ephemeral read-back | a listener on port 0 that knows its own port |
| 0.2.4 | **`sock_adopt` and `shutdown`** | an adopted descriptor verified; the half-close state machine |
| 0.2.5 | **Close** | `done/0.2/`, `0.3.0.md` written |

## Checklist

### 0.2.0 — `src/sys/`
- [ ] the fifteen syscall numbers from `SOCKET_MODEL.md` §1, each with the header it came from as a comment
- [ ] the families, types, protocols, flag bits, option names and levels
- [ ] **`accept` (43) is absent** and a comment says why (`SK-012`)
- [ ] this module declares **no error of its own** — every failure is an errno (`SAFETY.md` S-8)
- [ ] `check_constants_named` extended: no kernel constant outside this module

### 0.2.1 — `Sock` and creation
- [ ] `socket`, `socketpair` and (later) `accept4` all with `SOCK_NONBLOCK | SOCK_CLOEXEC` **in the creating call** (`SK-012`)
- [ ] a test asserting both flags on a freshly created socket, and that **no `fcntl` was issued** — checked by strace-free means: a counter in the wrapper, asserted zero
- [ ] `Sock` with its four recorded fields; move-only; `#size_of` asserted
- [ ] `sock_pair_headless(kind)` with `origin == Headless` and **no behavioural difference** (`SK-029`)
- [ ] the drop closes the descriptor, proven by `/proc/self/fd`

### 0.2.2 — the send and receive path
- [ ] `sendto` and `recvfrom` wrappers, **`MSG_NOSIGNAL` unconditional** (`SK-013`)
- [ ] the retry loop shape from `STREAM_MODEL.md` T-6: `EINTR` retries, `EAGAIN` waits on readiness, everything else forwards
- [ ] **`check_msg_nosignal` goes live**, with a whitelist of zero, and the 0.0.3 self-check case that proves it bites is un-pended
- [ ] **`check_no_floor_write` goes live**
- [ ] the `SIGPIPE` regression test (`specs/TESTING.md` §3), both legs, as a permanent suite entry rather than only a probe
- [ ] `// stress: 40` on the send/receive round trip

### 0.2.3 — the builder
- [ ] `SockBuilder`, move-only, short-lived
- [ ] the three pre-bind options: `SO_REUSEADDR`, `SO_REUSEPORT`, `IPV6_V6ONLY` — **and only those here**; the rest wait for 0.7
- [ ] `SO_REUSEADDR` default **on** for a listener, `SO_REUSEPORT` default **off** (`SK-032`), each with a test
- [ ] `IPV6_V6ONLY` set explicitly on every IPv6 socket, never left to the sysctl (`SK-028`)
- [ ] `bind`, with the `addrlen` from 0.1's encoder and **not** `sizeof(sockaddr_storage)`
- [ ] the ephemeral read-back: `bind` to port 0 then `getsockname` immediately, so `local_addr()` is a field read (K-14)
- [ ] `listen`, backlog passed through unclamped, with the `somaxconn` note in the documentation
- [ ] a restart test: bind, close, rebind within `TIME_WAIT`, succeeding because of `SO_REUSEADDR`

### 0.2.4 — `sock_adopt` and `shutdown`
- [ ] `O-K3` decided and recorded
- [ ] `sock_adopt` verifying with `SO_DOMAIN`/`SO_TYPE` **and** setting `O_NONBLOCK`/`FD_CLOEXEC` — the one place `fcntl` appears (K-9)
- [ ] adopting a regular file refused, with the verification naming what it found
- [ ] `shutdown` with the three `how` values; `Sock.shut` recorded
- [ ] an operation the shut state forbids fails `ESockState` **before** the syscall (K-21)
- [ ] `shutdown` on an unconnected socket forwards `ENOTCONN` without a pre-check (K-22)

## Gate

`check_msg_nosignal` green, seen to fail, and covering a non-empty input; the
`SIGPIPE` regression test green on both legs; and a `socketpair` round trip
under `// stress: 40`.

## Watch for

- **This is the cycle where `SK-013` becomes real.** Every send site written
  here sets the precedent for every one after it, and `check_msg_nosignal` is
  what makes the precedent permanent. Write the check's input before the first
  send, not after.
- **`raw` is the unwrap keyword** and this cycle talks about raw sockets and raw
  descriptors constantly. `descr` is the spelling.
- **The `addrlen` passed to `bind` is not a constant.** For `AF_UNIX` it is
  significant to the kernel, and passing 110 for an abstract address binds the
  wrong name (0.1.2's finding, applied here).
