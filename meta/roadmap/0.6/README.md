# Cycle 0.6 — Datagrams

**`src/datagram/`: `UdpSocket`, `UnixDatagram`, truncation, connected sockets,
broadcast, multicast, and `IP_PKTINFO`.**

## Decisions in

`SK-021` (truncation reported via `MSG_TRUNC`), and `DATAGRAM_MODEL.md` G-1's
recorded departure from the typestate rule. Settled.

**Open questions to settle:** `O-G1` (`IP_PKTINFO` — recommendation: in),
`O-G2` (`SO_TIMESTAMPNS` — recommendation: out), and `O-A3`'s answer gates
`G-16`'s multicast interface question.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.6.0 | **`UdpSocket` and `UnixDatagram`** — send, receive, the connected/unconnected split | a datagram round trip over both families |
| 0.6.1 | **Truncation** — `MSG_TRUNC` on every receive | a datagram larger than its buffer reported with its true length |
| 0.6.2 | **Connected datagram sockets** — the default peer, the receive filter, `AF_UNSPEC` | an `ECONNREFUSED` delivered on a connected UDP socket |
| 0.6.3 | **Broadcast and multicast** | a join, a send, a receive, and the interface named explicitly |
| 0.6.4 | **`IP_PKTINFO`** | a multi-homed reply going out with the right source |
| 0.6.5 | **Close** | `done/0.6/`, `0.7.0.md` written |

## Checklist

### 0.6.0 — the types
- [ ] `UdpSocket` and `UnixDatagram`, each with a recorded `connected` flag
      (G-1) — **and the departure from `SK-010` explained in the module header**
- [ ] `send` refused on an unconnected socket and `send_to` on a connected one,
      both `ESockState`, both before the syscall
- [ ] `sendto` with **`MSG_NOSIGNAL`** — a Unix datagram socket whose peer has
      gone raises `SIGPIPE` too, and this is the case most likely to be
      forgotten (G-2)
- [ ] **no `datagram_send_all`**, and a comment saying why: a datagram send is
      all-or-nothing and a short count would be a kernel bug (G-3)
- [ ] `EMSGSIZE` forwarded, with the practical ceilings in the documentation
- [ ] a round trip over UDP on loopback and over an abstract `AF_UNIX` pair
- [ ] `UnixDatagram` binding both ends so a reply has somewhere to go (G-18)

### 0.6.1 — truncation
- [ ] **every receive passes `MSG_TRUNC`** (32), so the kernel returns the
      datagram's true length (G-8)
- [ ] `returned > cap` → `ESockCapacity` with the true length as a companion
      field, and the truncated bytes still available
- [ ] a test sending 4096 bytes into a 512-byte buffer and asserting **4096** is
      reported — the classic UDP bug, closed
- [ ] a comment where `MSG_TRUNC` is passed, saying it means something entirely
      different on a stream socket and is never passed on one (G-9)
- [ ] `datagram_peek_len` as a zero-length `MSG_PEEK | MSG_TRUNC` receive (G-10)
- [ ] **a zero-length datagram received as a datagram, not as end of stream**
      (G-6) — the mirror of `STREAM_MODEL.md` T-14, and the opposite answer

### 0.6.2 — connected datagram sockets
- [ ] `connect` setting a default peer, and the socket receiving **only** from
      it — asserted by a third party sending and being ignored (G-11)
- [ ] `datagram_disconnect` via `AF_UNSPEC`, clearing `connected` (G-12)
- [ ] an asynchronous `ECONNREFUSED` delivered on a connected UDP socket after
      an ICMP port-unreachable, and **not** delivered on an unconnected one

### 0.6.3 — broadcast and multicast
- [ ] `SO_BROADCAST` off by default; a broadcast send without it failing
      `EACCES`, asserted (G-13)
- [ ] `IP_ADD_MEMBERSHIP` / `IP_DROP_MEMBERSHIP`, `IP_MULTICAST_TTL` (default
      **1**, documented), `IP_MULTICAST_LOOP`
- [ ] the IPv6 twins at level `IPPROTO_IPV6`
- [ ] **the interface index is required and has no default** (G-15), because
      passing 0 asks the kernel to choose by routing table and a join that works
      in development listens on the wrong interface in production
- [ ] a loopback multicast join, send and receive — which works on `lo` with
      `IP_MULTICAST_LOOP` and needs no external network

### 0.6.4 — `IP_PKTINFO`
- [ ] `O-G1` decided and recorded
- [ ] `IP_PKTINFO` / `IPV6_RECVPKTINFO` received as ancillary data through
      0.5's `msghdr`
- [ ] the local address a datagram arrived on, reported to the caller
- [ ] sending a reply **from** that address, so a multi-homed server's reply has
      the right source
- [ ] a test with two loopback addresses (`127.0.0.1` and `127.0.0.2`) proving
      the reply's source matches the request's destination

## Gate

A 4096-byte datagram into a 512-byte buffer reported as `ESockCapacity` with
the true length; a zero-length datagram received as a datagram; and a
multi-homed reply going out with the right source.

## Watch for

- **`MSG_TRUNC` means two different things** depending on socket type, and this
  cycle passes it on every datagram receive and on no stream receive. A shared
  helper across the two kinds would be wrong for one of them.
- **"Read returned zero" is end-of-stream on a stream and a real datagram on a
  datagram.** Two rules, opposite answers, and both written down for exactly
  that reason.
- **`127.0.0.2` is a real loopback address** on Linux and needs no
  configuration, which is what makes the multi-homed `IP_PKTINFO` test runnable
  in CI.
