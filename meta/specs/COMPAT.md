# Compatibility

What `nsockets` targets, what it is tested against, and what a claim in this
document means.

---

## 1. What a row means

**Rule W-1.** A kernel or environment appears in §3 only when the `loopback`
stage has been run on it and its result is recorded. An environment with no
recorded run is not listed, however well it is expected to work.

**Rule W-2 — three tiers**, and they say different things:

| Tier | Means |
|---|---|
| **Verified** | the `loopback` stage was run on it and passed, with the run recorded in `meta/research/` |
| **Expected** | Linux with the syscalls §2 names; should work; bugs accepted as bugs |
| **Unsupported** | stated, with the reason |

---

## 2. The floor

**Rule W-3 (SK-003) — Linux on x86-64, and the syscalls in
`SOCKET_MODEL.md` §1.** The
oldest kernel this library can run on is decided by its newest requirement:

| Requirement | Since |
|---|---|
| `accept4` | Linux 2.6.28 |
| `SOCK_NONBLOCK` / `SOCK_CLOEXEC` on `socket()` | Linux 2.6.27 |
| `MSG_CMSG_CLOEXEC` | Linux 2.6.23 |
| `SO_REUSEPORT` | Linux 3.9 |
| `epoll` (the language's reactor) | long predates all of these |

So the floor is **Linux 3.9**, and in practice anything a Nitpick program runs
on. `SO_REUSEPORT` is the only item that reaches that high and it is optional;
without it the library still works and `reuse_port(true)` fails `ENOPROTOOPT`,
forwarded.

**Rule W-4 — x86-64 only at 1.0** (`SK-007`). The syscall numbers are
architecture-specific and the structure layouts are not: `aarch64` Linux needs
a different `src/sys/` table and nothing else, which makes it the first port to
consider and a small one. `SOCKET_MODEL.md` §1's table is the whole of what
changes.

**Rule W-5 — no other operating system.** A BSD `sockaddr` carries an `sa_len`
byte where Linux carries the high byte of the family, `SO_NOSIGPIPE` replaces
`MSG_NOSIGNAL`, `accept4` is `accept` plus flags with different spelling, and
there is no `SCM_CREDENTIALS`. That is a port with real design content, and a
`#cfg` sprinkled through this library would be worse than a second `src/sys/`
written deliberately.

---

## 3. The matrix

Filled as the `loopback` stage is run; cycle 0.10 completes it. Every cell is a
recorded run.

| Environment | Tier | IPv4 | IPv6 | `AF_UNIX` | abstract ns | `SCM_RIGHTS` | `SCM_CREDENTIALS` |
|---|---|---|---|---|---|---|---|
| Linux 6.x, x86-64, bare | — | | | | | | |
| Linux 6.x, x86-64, container (default netns) | — | | | | | | |
| Linux 6.x, x86-64, container (no IPv6) | — | | | | | | |
| Linux 5.15 LTS, x86-64 | — | | | | | | |
| WSL2 | — | | | | | | |
| Linux 6.x, `aarch64` | — | *post-1.0* | | | | | |

**Rule W-6 — the no-IPv6 container row is not decoration.** A container with
IPv6 disabled fails `socket(AF_INET6, …)` with `EAFNOSUPPORT`, and a library
that treats that as a fatal error is a library that will not start in half of
CI. The row exists so the behaviour is measured rather than assumed, and
`ADDRESS_MODEL.md` A-10's explicit `IPV6_V6ONLY` is what keeps a dual-stack
listener from being the default that breaks there.

**Rule W-7 — the abstract-namespace column is Linux-only and is marked as
such.** It is the recommended form for Unix sockets in this library
(`SOCKET_MODEL.md` K-25) *and* the least portable thing in it, and both are
true at once.

---

## 4. Unsupported, with reasons

| Not supported | Reason |
|---|---|
| DNS / hostname resolution | `SK-024` — a wire protocol and a parser, with its own security surface |
| TLS | `SK-025` — a cryptographic artifact that wants its own audit |
| Raw sockets (`SOCK_RAW`) | needs `CAP_NET_RAW`; a library that offers a privileged operation invites running as root |
| Netlink (`AF_NETLINK`) | a protocol, not a socket API; interface enumeration is `O-A3` |
| Packet sockets (`AF_PACKET`) | as raw sockets |
| SCTP, DCCP | not present on a stock kernel; `SOCK_SEQPACKET` over `AF_UNIX` covers the local case |
| Windows, macOS, BSD | W-5 |
| 32-bit Linux | the structure layouts and the syscall numbers both differ, and no consumer has asked |

---

## 5. Degradation

**Rule W-8.** Where a feature is absent the kernel says so and the errno is
forwarded (`SAFETY.md` S-6): `EAFNOSUPPORT` for a disabled family,
`ENOPROTOOPT` for a missing option, `EPERM` for a privileged one. The library
adds no capability detection and no silent fallback — a caller that must run
on a kernel without `SO_REUSEPORT` asks for it and handles the refusal, which
is one branch, visible, where a silent fallback would be a behaviour change
nobody could see.
