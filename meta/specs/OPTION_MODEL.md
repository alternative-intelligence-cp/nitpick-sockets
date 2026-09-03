# Socket options

There is no `setsockopt` in the public surface. There is one function per
option, each taking and returning the type that option actually is.

---

## 1. The decision

**Rule P-1 (SK-026).** Socket options are **typed, one function per option**.
The generic form — `setsockopt(level, name, ptr, len)` — is confined to
`src/option/raw.npk`, is not exported by `src/lib.npk`, and is called by the
typed wrappers and by nothing else.

The generic form is a `void*` and a length. Every mistake it permits is one
this library exists to prevent: passing a `bool` where the kernel wants a
four-byte `int` (which reads three bytes of adjacent stack), passing the wrong
level for a name (which silently sets a different option, or nothing), passing
`SO_LINGER`'s eight-byte structure as a four-byte integer, forgetting that
`SO_RCVBUF` reports back **double** what was set. None of them is a compile
error in C and all of them are unspellable here.

The cost is a function per option and a decision per option — which is the
point. An option nobody has written a wrapper for is an option nobody has
thought about, and `O-P1` is where the ones that were considered and left out
are recorded rather than quietly unavailable.

---

## 2. The shape

```nitpick
// on the builder, before bind — SOCKET_MODEL.md K-12
builder.reuse_addr(bool)     -> SockBuilder
builder.reuse_port(bool)     -> SockBuilder
builder.v6only(bool)         -> SockBuilder
builder.recv_buf(int32)      -> SockBuilder
builder.send_buf(int32)      -> SockBuilder

// on a live socket, any time
stream.nodelay(bool)                 -> Result<NIL>
stream.get_nodelay()                 -> Result<bool>
stream.keepalive(bool)               -> Result<NIL>
stream.keepalive_params(Keepalive)   -> Result<NIL>
sock.get_error()                     -> Result<int32>     // SO_ERROR, §4
udp.broadcast(bool)                  -> Result<NIL>
udp.multicast_ttl(uint8)             -> Result<NIL>
udp.join_group(IpAddr, uint32)       -> Result<NIL>
unix.pass_cred(bool)                 -> Result<NIL>
unix.get_peer_cred()                 -> Result<Ucred>     // ANCILLARY_MODEL.md §6
```

**Rule P-2 — a getter exists only where the answer can differ from what was
set.** `SO_RCVBUF` is the archetype (§3). Where the kernel simply stores what
it was given, a getter is a syscall to learn something the caller already
knows, and the caller keeps its own value.

---

## 3. The options whose behaviour surprises

**Rule P-3 — `SO_RCVBUF` and `SO_SNDBUF` report double.** Linux doubles the
value on set, to account for its own bookkeeping overhead, and `getsockopt`
returns the doubled figure. Setting 8192 and reading back 16384 is correct
behaviour and not a bug. The wrappers document it, do **not** halve the result
(which would be inventing a number the kernel did not report), and the getter
exists precisely so a caller can see what actually happened.

**Rule P-4 — `SO_RCVBUF` is capped by `net.core.rmem_max`**, silently. A set
above the cap succeeds and clamps. `SO_RCVBUFFORCE` bypasses it and needs
`CAP_NET_ADMIN`; it is not in the surface.

**Rule P-5 — `SO_REUSEADDR` does not mean what its name suggests.** On TCP it
permits binding an address in `TIME_WAIT`. It does **not** permit two live
listeners on one address — that is `SO_REUSEPORT`. On UDP the two are less
distinguishable, which is its own reason to name each explicitly.
`SOCKET_MODEL.md` K-15 has the defaults.

**Rule P-6 — `SO_KEEPALIVE` alone is nearly useless.** The kernel's default
idle time is **two hours**; a keepalive that first probes after two hours does
not detect a dead peer in any timeframe an application cares about. The wrapper
therefore comes in two forms: `keepalive(bool)` for the flag alone, and
`keepalive_params(Keepalive{ idle_s, interval_s, count })` which sets
`TCP_KEEPIDLE` (4), `TCP_KEEPINTVL` (5) and `TCP_KEEPCNT` (6) with it. The
documentation on the first points at the second.

**Rule P-7 — `TCP_NODELAY` is a latency/bandwidth trade and the library does
not choose it for you.** `O-T1` in `STREAM_MODEL.md` records the default.

---

## 4. `SO_ERROR`

**Rule P-8.** `SO_ERROR` (`4`) is read-only, and **reading it clears it**.
`STREAM_MODEL.md` T-9 makes it read exactly once on the connect path. It is
exported as `sock.get_error()` because it is also how a caller learns about an
asynchronous error on a connected UDP socket, and because a reader who does not
know it is destructive will be told by the wrapper's documentation.

---

## 5. Options that are deliberately absent

Each of these was considered. Absence here is a decision, and each has its
reason:

| Option | Why not |
|---|---|
| `SO_RCVTIMEO` / `SO_SNDTIMEO` | a second timing mechanism competing with the reactor's deadline — `SAFETY.md` S-11 |
| `SO_LINGER` with a nonzero timeout | makes `close` block, which is a thread-parking wait D-071 forbids — `STREAM_MODEL.md` T-25. The zero-timeout form (send RST) **is** available |
| `SO_RCVBUFFORCE` / `SO_SNDBUFFORCE` | needs `CAP_NET_ADMIN`; a library that offers a privileged operation invites running as root |
| `SO_BINDTODEVICE` | needs `CAP_NET_RAW`, and takes an interface **name** whose resolution is `O-A3` |
| `SO_PRIORITY`, `IP_TOS`, `IPV6_TCLASS` | QoS marking, meaningless without a network that honours it; recorded as `O-P1` |
| `TCP_CORK`, `TCP_QUICKACK` | fine-grained transmission tuning with no consumer, and `TCP_QUICKACK` is not sticky, which is a documentation liability on its own |
| `SO_ATTACH_FILTER` (BPF) | a program loaded into the kernel from a library that promises no C is a claim that needs its own argument |
| `SO_PEEK_OFF`, `SO_ZEROCOPY`, `SO_BUSY_POLL` | no consumer; each is a real feature and each is a separate decision |

**Rule P-9.** Adding one is a decision recorded in `DECISIONS.md`, and the
decision says which of the failure modes in §1 the wrapper's type prevents.

---

## 6. Levels

**Rule P-10.** The four levels this library uses, measured: `SOL_SOCKET` = 1,
`IPPROTO_IP` = 0, `IPPROTO_TCP` = 6, `IPPROTO_IPV6` = 41. The level is a
constant inside each wrapper and is never a parameter — passing the wrong level
for a name is the mistake §1 is about, and a wrapper that took the level would
have re-opened it.

---

## 7. Open items

- **O-P1 — the QoS options** (`IP_TOS`, `IPV6_TCLASS`, `SO_PRIORITY`).
  **Recommendation:** out at 1.0. They are meaningful only on a network that
  honours DSCP, they are trivially added when one appears, and shipping them
  untested implies a guarantee the library cannot make.
- **O-P2 — whether the builder's option setters should return `Result` or
  accumulate.** As written they return `SockBuilder` and a failure is deferred
  to the terminal `bind`/`connect`/`listen`, which makes the chain readable but
  reports the failure away from its cause. **Recommendation:** the builder
  carries the first error and the terminal operation reports it *with the
  option's name attached*, which keeps both the chain and the diagnosis.
  Settled at cycle 0.7.
