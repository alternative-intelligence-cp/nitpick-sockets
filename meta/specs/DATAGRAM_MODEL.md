# Datagrams

Message-oriented sockets: `UdpSocket` and `UnixDatagram`. Shorter than
[`STREAM_MODEL.md`](STREAM_MODEL.md) because there is less machinery, and
sharper because the failure modes are less forgiving.

---

## 1. The shape

```nitpick
pub struct:UdpSocket    = { Sock:s; SocketAddr:local; bool:connected; };
pub struct:UnixDatagram = { Sock:s; UnixAddr:local; bool:connected; };
```

**Rule G-1 — a datagram socket is one type whether or not it is connected**,
and `connected` is a recorded fact rather than a mode that selects behaviour.
That is a departure from the typestate rule (`SK-010`) and it is deliberate:
`connect` on a datagram socket sets a default peer and can be *undone*
(`connect` to `AF_UNSPEC`), it does not change what the socket is, and a caller
routinely wants both `send` and `send_to` on the same socket. Making them two
types would mean a conversion in both directions and a caller writing it in
every loop.

What `connected` *is* used for: refusing `send` (no address) on an unconnected
socket and refusing `send_to` on a connected one, both `ESockState`, both
before the syscall. The kernel's own answers there — `EDESTADDRREQ` and
`EISCONN` — are correct but arrive as a surprise.

---

## 2. Send

**Rule G-2.** `sendto(descr, ptr, len, MSG_NOSIGNAL, addr, addrlen)` for the
unconnected form and the same with a null address for the connected form.
`MSG_NOSIGNAL` on both: a `AF_UNIX` datagram socket whose peer has gone raises
`SIGPIPE` exactly as a stream does (`SAFETY.md` §2), and this is the case most
likely to be forgotten because "UDP has no connection" makes it sound
impossible.

**Rule G-3 — a datagram send is all-or-nothing.** There is no short write on a
datagram socket: the kernel takes the whole message or fails. A send that
returns fewer bytes than offered is a kernel bug, and the library treats it as
one — it is an internal-consistency failure, not a partial send to be looped
over. There is therefore **no `datagram_send_all`**, and its absence is
correct rather than an omission.

**Rule G-4 — `EMSGSIZE` is the message-too-large answer** and is forwarded
verbatim. For UDP over IPv4 the practical ceiling is 65507 bytes; the
*useful* ceiling is the path MTU less headers, and anything above roughly 1472
bytes on a typical link will fragment. The library does not fragment, does not
discover the MTU, and does not advise — it forwards the kernel's verdict, and
the documentation says the numbers so a caller can choose.

---

## 3. Receive

**Rule G-5.** `recvfrom(descr, ptr, cap, flags, addr, &addrlen)` returns the
datagram's length and fills the sender's address. Every receive on an
unconnected socket reports **who sent it**, and a caller that ignores that on a
UDP socket has written an amplification target.

**Rule G-6 — a zero-length datagram is a real datagram.** UDP permits an empty
payload, and a receive of 0 bytes on a datagram socket means "a datagram
arrived and it was empty" — **not** end of stream. This is the mirror of
`STREAM_MODEL.md` T-14 and it is the opposite answer, which is exactly why both
are written down: a shared "read returned zero" helper across the two socket
kinds would be wrong for one of them.

**Rule G-7 — a datagram socket never reports `IoEof`.** There is no end of
stream. A `UnixDatagram` whose peer closed reports `ECONNREFUSED` on the next
send, and nothing on receive.

---

## 4. Truncation is reported, never swallowed

**Rule G-8 (SK-021) — the classic UDP bug, closed by construction.**
`recvfrom` into a buffer smaller than the datagram **discards the remainder and
returns the buffer's size**, with no indication anything was lost. A caller
that asked for 512 bytes and got 512 bytes cannot tell a 512-byte datagram from
a 4096-byte one.

`nsockets` closes it: **every receive passes `MSG_TRUNC`** (`32`), which makes
the kernel return **the datagram's true length** rather than the copied length,
while still copying only what fits. The library then compares:

| Condition | Result |
|---|---|
| `returned <= cap` | a complete datagram of `returned` bytes |
| `returned > cap` | `ESockCapacity`, with the true length as a companion field, and the truncated bytes available to a caller that wants them |

**Rule G-9.** `MSG_TRUNC` on a **datagram** socket means "tell me the real
length". `MSG_TRUNC` on a **stream** socket means something entirely different
(discard the data), and this library never passes it on a stream. Stated
because the same flag name doing two unrelated things is a trap.

**Rule G-10 — a caller who genuinely wants to peek** uses `MSG_PEEK` (`2`),
which leaves the datagram queued. `datagram_peek_len(s)` is the spelling for
"how big is the next one", implemented as a zero-length `MSG_PEEK | MSG_TRUNC`
receive, so a caller can size a buffer exactly once.

---

## 5. Connected datagram sockets

**Rule G-11.** `connect` on a datagram socket does not handshake. It sets a
default peer, so `send` needs no address, and it makes the socket **receive
only from that peer** — which is the property that matters and the one people
forget. It also makes asynchronous errors (`ICMP port unreachable` →
`ECONNREFUSED`) deliverable, which they are not on an unconnected socket.

**Rule G-12.** `datagram_disconnect(s)` connects to `AF_UNSPEC`, which is the
documented way to undo it. It clears `connected`.

---

## 6. Broadcast and multicast

**Rule G-13.** `SO_BROADCAST` (`6`) is off by default in the kernel and stays
off unless asked. A broadcast send without it is `EACCES`, and that refusal is
a feature.

**Rule G-14 — multicast is four options and a decision about the interface**:

| Option | Level | Value | What |
|---|---|---|---|
| `IP_ADD_MEMBERSHIP` | `IPPROTO_IP` | 35 | join a group on an interface |
| `IP_DROP_MEMBERSHIP` | `IPPROTO_IP` | 36 | leave |
| `IP_MULTICAST_TTL` | `IPPROTO_IP` | 33 | hop limit — **default 1**, i.e. this link only |
| `IP_MULTICAST_LOOP` | `IPPROTO_IP` | 34 | do we receive our own sends |

and the IPv6 twins `IPV6_JOIN_GROUP` (20) / `IPV6_LEAVE_GROUP` (21) /
`IPV6_MULTICAST_HOPS` / `IPV6_MULTICAST_LOOP` at level `IPPROTO_IPV6` (41).

**Rule G-15 — a join names its interface explicitly.** `ip_mreqn` carries an
interface index, and passing 0 asks the kernel to choose by routing table —
which on a multi-homed host chooses differently depending on the routes, so a
join that works in development silently listens on the wrong interface in
production. `nsockets` requires the index and provides no default.

**Rule G-16 — multicast is planned but scheduled late** (cycle 0.6's second
half), because the interface-index question needs `O-A3`'s answer to be
usable from a name rather than a number.

---

## 7. Unix datagrams

**Rule G-17.** `AF_UNIX` `SOCK_DGRAM` is reliable and ordered — it is not UDP
with a path. Messages are never lost or reordered, `EMSGSIZE` is the only size
failure, and a send to a full receive queue blocks (or `EAGAIN`s, here). That
makes it a genuinely good local IPC transport and worth having distinct
documentation from UDP's, which is why this section exists.

**Rule G-18 — a Unix datagram socket must bind to receive replies.** An
unbound `AF_UNIX` datagram socket has no address, so a peer has nowhere to send
to, and `recvfrom` reports an unnamed sender (`ADDRESS_MODEL.md` A-15). A
request/reply pattern binds both ends — usually one to an abstract address, so
there is nothing to unlink (`SOCKET_MODEL.md` §9).

**Rule G-19.** `SCM_RIGHTS` and `SCM_CREDENTIALS` work over Unix datagrams and
are `ANCILLARY_MODEL.md`'s business; the send and receive paths there are
`sendmsg`/`recvmsg` rather than `sendto`/`recvfrom`, and they carry the same
`MSG_NOSIGNAL` and the same `MSG_TRUNC` discipline.

---

## 8. Open items

- **O-G1 — `IP_PKTINFO` / `IPV6_RECVPKTINFO`.** A UDP server bound to `0.0.0.0`
  cannot tell which of its local addresses a datagram arrived on, so a reply
  can go out with the wrong source address. The fix is receiving the ancillary
  `IP_PKTINFO` and sending it back. It is a real bug for a multi-homed DNS-like
  server and pure overhead for everything else. **Recommendation:** in, at
  cycle 0.6, because a datagram library that cannot answer correctly on a
  multi-homed host has a hole a consumer cannot patch from outside.
- **O-G2 — `SO_TIMESTAMPNS`.** Kernel receive timestamps, as ancillary data.
  Wanted by anything measuring latency. **Recommendation:** out at 1.0,
  recorded, and cheap to add later since the ancillary machinery exists.
