# Ancillary data

Descriptor passing and peer identity over `AF_UNIX`, through one audited
`msghdr`. The compiler's own Bridge already does this
(`../nitpick/lib/nbridge.npk` §"SCM_RIGHTS: the one place msghdr exists"), and
that code is this section's oracle — the layouts below match it because they
are the same kernel.

---

## 1. The structures, measured

x86-64, measured on the target platform on 2026-09-03.

### `msghdr` — 56 bytes

| Offset | Size | Field | Note |
|---|---|---|---|
| 0 | 8 | `msg_name` | `NULL` on a connected socket |
| 8 | 8 | `msg_namelen` + pad | the `int32` and its padding as one word |
| 16 | 8 | `msg_iov` | → the `iovec` array |
| 24 | 8 | `msg_iovlen` | |
| 32 | 8 | `msg_control` | → the control buffer, `NULL` when none |
| 40 | 8 | `msg_controllen` | |
| 48 | 8 | `msg_flags` + pad | **written by the kernel on receive** |

### `iovec` — 16 bytes

| Offset | Size | Field |
|---|---|---|
| 0 | 8 | `iov_base` |
| 8 | 8 | `iov_len` |

### `cmsghdr` — 16 bytes, then the payload

| Offset | Size | Field |
|---|---|---|
| 0 | 8 | `cmsg_len` — **the header plus the payload**, not the payload |
| 8 | 4 | `cmsg_level` |
| 12 | 4 | `cmsg_type` |
| 16 | … | the payload, aligned to 8 |

**Rule N-1 — `msg_namelen` and `msg_flags` are declared as one 8-byte word
each**, covering the `int32` and its padding. That is layout-identical to the
C structure on this ABI, it saves the Nitpick struct a raft of pad fields, and
it is exactly what `nbridge.npk` does. A test asserts the total is 56.

**Rule N-2 — `cmsg_len` counts the header.** `CMSG_LEN(n)` is `16 + n`;
`CMSG_SPACE(n)` is that rounded up to a multiple of 8. For one descriptor:
`cmsg_len = 20`, `CMSG_SPACE = 24`. These two being different is the source of
most `SCM_RIGHTS` bugs — `msg_controllen` on **send** is the `SPACE`, and
`cmsg_len` inside the header is the `LEN`.

---

## 2. The one `msghdr`

**Rule N-3.** There is exactly one place in this library that lays out a
`msghdr`, and every ancillary send and receive goes through it. `nbridge.npk`
says the same about itself, in its section title, for the same reason: the
layout is fiddly, the alignment rules are unobvious, and three copies would
be three chances to get `CMSG_SPACE` wrong in one of them.

**Rule N-4 — the control buffer is a fixed-size stack array**
(`SAFETY.md` S-22), sized `NSOCK_CMSG_MAX` = 256 bytes. That holds
`SCM_RIGHTS` for up to 60 descriptors, or `SCM_CREDENTIALS`, or both. It takes
no `wild` bytes, so the ancillary path cannot trip D-151 on any exit path.

**Rule N-5.** `NSOCK_SCM_MAX_FDS` = 16 descriptors per message. The kernel's
own limit is `SCM_MAX_FD` = 253; sixteen is this library's, it is a named
constant, and it is chosen so the control buffer bound in N-4 is comfortable
rather than exact. A request for more is `ESockCapacity` before the syscall.

**Rule N-19 — the `cmsghdr` walk checks before it subtracts.** A received
control buffer is walked one header at a time over N-4's array, and every
length in the walk is a `uint64`, whose subtraction below zero traps as
`IntOverflow` rather than wrapping (`SAFETY.md` §1, D-210). So the order of the
checks is what keeps a legitimate buffer from trapping and a hostile one from
being read past `msg_controllen`. At each header, with `rem` the bytes from it
to `msg_controllen`:

- `rem < 16` ends the walk: no header fits in what remains.
- `cmsg_len < 16` is `ESockProtocol`, and so is `cmsg_len > rem`; each closes
  what the receive has wrapped (N-9). Both compare with `rem` and never form
  `offset + cmsg_len`, a sum that a `cmsg_len` near 2⁶⁴ would overflow.
- The payload is `cmsg_len − 16` bytes, a subtraction those two checks make
  safe.
- The step to the next header is `min(align8(cmsg_len), rem)`. The last
  header's tail padding may be absent — a 20-byte buffer carries one
  descriptor with none, as the kernel delivers it into a buffer that size —
  and an aligned length is never subtracted from a smaller remainder.
  `align8` cannot wrap, since `cmsg_len ≤ rem ≤ 256`.
- A header whose `cmsg_len` is 16 and which ends exactly at `msg_controllen`
  is visited, never skipped. Its empty payload is no decoded type's: an
  `SCM_RIGHTS` payload is a positive multiple of 4 bytes and an
  `SCM_CREDENTIALS` payload exactly 12 (N-13), so either is `ESockProtocol`,
  and a header of another level or type is N-11's.
- The header is decoded by indexing the byte array — `cmsg_len` the eight
  bytes at its offset 0, `cmsg_level` and `cmsg_type` the four at 8 and 12 —
  never through a struct view laid over the bytes.

---

## 3. `SCM_RIGHTS` — passing descriptors

**Rule N-6.** `SOL_SOCKET` (1) / `SCM_RIGHTS` (1), payload an array of `int32`
descriptor numbers.

**Rule N-7 — a message carrying descriptors must carry at least one byte of
ordinary data.** A zero-length `sendmsg` with only ancillary data is legal on
some kernels and silently drops the ancillary on others, and on a
`SOCK_STREAM` socket a zero-length send is a no-op that sends nothing at all.
The library refuses `ESockState` rather than producing a message whose
behaviour depends on the kernel version, and every send it makes carries at
least one payload byte.

**Rule N-8 — the descriptors arrive as *new* descriptors in the receiving
process.** They are not the sender's numbers; the kernel allocates fresh ones.
They arrive **without** `FD_CLOEXEC` unless the receive asked for
`MSG_CMSG_CLOEXEC` (`0x40000000`), and `nsockets` **always passes it** — the
same reasoning as `SOCKET_MODEL.md` K-8: the atomic form exists so that no
window between receive and `fcntl` can leak a descriptor across an `execve`.

**Rule N-9 — a received descriptor is owned the moment it arrives, and the
receive path must not lose it.** Between `recvmsg` returning and the library
wrapping the number in an `OwnedFd`, a failure would leak it — permanently,
because nothing else knows the number. The receive therefore wraps **before**
it validates anything else, and every subsequent refusal in the same function
closes what it wrapped. This is the one place in the library where the order of
two statements is a resource-safety property, and a comment at the site says
so.

**Rule N-10 — `MSG_CTRUNC` (`8`) is a protocol failure, not a warning.** The
kernel sets it when the control buffer was too small, which means it **closed**
the descriptors it could not deliver — or delivered some of them, and a caller
that ignores the flag has a descriptor it does not know it owns. `nsockets`
fails `ESockProtocol`, closes every descriptor it did receive, and says how
many were expected. `nbridge.npk` reaches the same verdict from the same
reasoning ("a half-received descriptor is a leak the kernel already made").

**Rule N-11 — a `cmsghdr` of an unexpected level or type is
`ESockProtocol`**, and any descriptors in it are closed first. A peer that
sends `SCM_CREDENTIALS` where `SCM_RIGHTS` was expected is either confused or
hostile, and neither is a reason to keep the payload.

**Rule N-12 — descriptor passing works over `SOCK_STREAM`, `SOCK_DGRAM` and
`SOCK_SEQPACKET`**, `AF_UNIX` only. On a stream the ancillary data is bound to
a **byte position**, so a reader using a large buffer can receive the
descriptor along with bytes from a later message — which is one more reason
`SOCK_SEQPACKET` is the better transport for a protocol that passes
descriptors (`STREAM_MODEL.md` §9).

---

## 4. `SCM_CREDENTIALS` — peer identity

**Rule N-13.** `SOL_SOCKET` (1) / `SCM_CREDENTIALS` (2), payload a
`struct ucred`: **12 bytes**, `pid` at 0, `uid` at 4, `gid` at 8, each an
`int32`/`uint32` — measured by cycle 0.0's probe 03, whose Nitpick mirror names
the fields `cpid`, `cuid` and `cgid`: `pid`, `uid` and `gid` are keywords at the
pin, and a keyword declared as a name of any kind is `NITPICK-PARSE-001`
(SK-102). The library's `Ucred` uses the same three names.

**Rule N-14 — the receiver must have set `SO_PASSCRED` (16) first**, or no
credentials arrive. It is not automatic and there is no error to tell you: the
message simply has no `SCM_CREDENTIALS` header. The library's
`unix_recv_with_cred` sets it on the socket if it is not set, once, and records
that it did.

**Rule N-15 — the kernel validates credentials, and that is the whole point.**
A sender may only claim its own pid, uid and gid, or values it has
`CAP_SYS_ADMIN`/`CAP_SETUID`/`CAP_SETGID` to claim. So an arriving `ucred` is
*trustworthy* in a way almost nothing else on a socket is, which makes it the
correct basis for a local authorisation decision — and makes it worth having
even though it is Linux-specific.

**Rule N-16 — `SO_PEERCRED` (17) is the simpler alternative and this library
offers both.** `getsockopt(SO_PEERCRED)` returns the peer's credentials **as
they were at `connect`/`listen` time**, with no ancillary machinery and no
`SO_PASSCRED`. It is right for "who connected to me"; `SCM_CREDENTIALS` is
right for "who sent *this message*", which differs on a datagram socket with
several senders. The documentation says which is which, because reaching for
the wrong one produces an authorisation check that is correct in testing and
wrong under load.

**Rule N-17 — a pid is not a capability.** A `ucred`'s `cpid` may have exited and
been reused by the time the receiver acts on it. `uid` and `gid` do not have
that problem. The library states this where `ucred` is documented, because
"check the pid against a list of allowed processes" is a natural and wrong
thing to write.

---

## 5. Not supported

**Rule N-18.** `SCM_RIGHTS` and `SCM_CREDENTIALS` are the whole ancillary
surface at 1.0. `SCM_SECURITY` (SELinux contexts), `SO_TIMESTAMP*`
(`O-G2`), and `IP_PKTINFO` (`O-G1`) each need the same machinery and each is
its own decision. The `msghdr` layer is built so that adding one is a
`cmsghdr` reader and nothing else.

---

## 6. Open items

- **O-Y1 — whether `SCM_RIGHTS` should cap at 16 or expose the kernel's 253.**
  Sixteen is a named constant chosen for a comfortable control buffer.
  **Recommendation:** keep 16 at 1.0 and raise it with a measurement if a
  consumer asks; a higher cap costs a bigger fixed buffer on every ancillary
  receive, paid by everyone.
- **O-Y2 — descriptor passing to a process that is not `AF_UNIX`-adjacent.**
  Nothing to do; recorded because "can I pass a descriptor over TCP" is asked
  every time and the answer — no, not on any operating system — belongs in the
  documentation rather than in a reader's memory.
