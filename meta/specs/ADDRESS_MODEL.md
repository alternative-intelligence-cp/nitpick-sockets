# Addresses

The address types, their kernel encodings, and the parsers and formatters. This
is the layer with no descriptors in it: pure computation over values, testable
with no kernel at all, and the only module besides `src/sys/` that a program can
import without owning a socket.

**Every offset and size in this document was measured on the target platform on
2026-09-03** and is re-asserted by a running program in cycle 0.0's probe 03
(`SK-016`).

---

## 1. The types

```nitpick
pub struct:Ipv4Addr = { uint8[4]:octets; };                      // 4 bytes
pub struct:Ipv6Addr = { uint8[16]:octets; uint32:scope; };       // 20 bytes
pub enum:IpAddr     = { V4(Ipv4Addr); V6(Ipv6Addr); };

pub struct:SocketAddrV4 = { Ipv4Addr:ip; uint16:port; };
pub struct:SocketAddrV6 = { Ipv6Addr:ip; uint16:port; uint32:flow; };
pub enum:SocketAddr     = { V4(SocketAddrV4); V6(SocketAddrV6); };

pub struct:UnixAddr = {
    uint8[108]:path;   // the kernel's sun_path, verbatim
    uint8:len;         // bytes of `path` that are significant, 0..108
    uint8:kind;        // 0 unnamed, 1 pathname, 2 abstract
};
```

**Rule A-1 (SK-022) — every address type is a plain value with no owning
field.** No
`string`, no `buffer`, no `Path`. That is what lets an address sit in an array,
be copied from binding to binding, ride a channel, and cross a spawn — none of
which an owning value can do (TYPE-046, TYPE-057). `UnixAddr` inlines its 108
bytes for exactly this reason; the alternative, a `string`, would make every
address move-only and every `Vec<SocketAddr>` a container of moves.

**Rule A-2 — octets are stored in network order**, which is the order they
appear in a dotted-quad and in the wire. `Ipv4Addr{ octets: [127,0,0,1] }` is
`127.0.0.1` with no swap anywhere. The one value that is *not* in network order
in the Nitpick struct is the **port**, which is stored in host order because
that is what a program reasons about, and swapped exactly once at the kernel
boundary (§6).

**Rule A-3 — `Ipv6Addr` carries its scope id** because a link-local address
without one is not routable and the kernel's `sockaddr_in6` has a field for it.
Dropping it would make `fe80::1%eth0` unrepresentable, and link-local is where
IPv6 on a LAN actually lives.

---

## 2. The kernel structures, measured

### `sockaddr_in` — 16 bytes

| Offset | Size | Field | Order |
|---|---|---|---|
| 0 | 2 | `sin_family` (= 2) | host |
| 2 | 2 | `sin_port` | **network** |
| 4 | 4 | `sin_addr` | **network** |
| 8 | 8 | `sin_zero` — must be zero | — |

### `sockaddr_in6` — 28 bytes

| Offset | Size | Field | Order |
|---|---|---|---|
| 0 | 2 | `sin6_family` (= 10) | host |
| 2 | 2 | `sin6_port` | **network** |
| 4 | 4 | `sin6_flowinfo` | **network** |
| 8 | 16 | `sin6_addr` | **network** |
| 24 | 4 | `sin6_scope_id` | **host** |

**`sin6_scope_id` is in host order and `sin6_flowinfo` is in network order.**
They are adjacent fields of the same width in the same structure with opposite
conventions. This is not a mistake in this document; it is the ABI, and it is
the single most likely place in this library to write a swap that should not be
there. The scope id's host order is why A-2 says the swap happens in one place
with a per-field table rather than "swap everything on the way out".

### `sockaddr_un` — 110 bytes

| Offset | Size | Field |
|---|---|---|
| 0 | 2 | `sun_family` (= 1) |
| 2 | 108 | `sun_path` |

### `sockaddr_storage` — 128 bytes

The receiving buffer for `accept4`, `recvfrom` and `getpeername`, big enough
for any family. `nsockets` uses it as a fixed 128-byte array and decodes by
reading `family` at offset 0 first.

**Rule A-4.** Every one of those sizes is asserted by a probe that fills a
structure, hands it to the kernel, reads it back, and checks a sentinel written
one byte past the end is untouched. A comment stating a size is a comment; a
program that round-trips it is a measurement.

---

## 3. Encoding and decoding

**Rule A-5 — one encoder and one decoder, and nothing else touches the bytes.**

```nitpick
addr_encode(SocketAddr, uint8[]:dest) -> int64        // bytes written = the addrlen to pass
addr_decode(uint8[]:src, int64:len)   -> SocketAddr   // family read from offset 0
unix_encode(UnixAddr, uint8[]:dest)   -> int64
unix_decode(uint8[]:src, int64:len)   -> UnixAddr
```

The returned length is the `addrlen` the syscall takes. It is **not** the
structure's size for `AF_UNIX` (§5) and it is not `sizeof(sockaddr_storage)`
for anything.

**Rule A-6 — `sin_zero` is zeroed on every encode.** The kernel ignores it on
input, but a caller comparing two encoded addresses byte for byte gets the
right answer only if the padding is deterministic, and a test that compares
encodings is a test worth being able to write.

**Rule A-7 — a decode of an unknown family is `ESockAddr`**, not a guess and
not a zero address. `getpeername` on a socket in an unexpected family is a
condition a caller wants to know about.

---

## 4. IPv4-mapped IPv6

**Rule A-8.** A dual-stack IPv6 listener (`IPV6_V6ONLY` off) accepts IPv4
connections, and the kernel reports their peer address as an IPv6 address of
the form `::ffff:a.b.c.d`. `nsockets` reports **what the kernel reported** — a
`SocketAddr.V6` — and never silently rewrites it to a `V4`.

**Rule A-9 (SK-037).** The conversion exists and is explicit: `ipv6_to_v4_mapped(a)`
returns `Ipv4Addr?`, `NIL` when the address is not in the mapped range.
Automatic conversion is refused because an application that compares a peer
address against an allowlist must know which representation it is comparing —
and the security bugs in this area are all of the form "the check saw
`::ffff:127.0.0.1` and the allowlist held `127.0.0.1`".

**Rule A-10 (SK-028) — `IPV6_V6ONLY` is set explicitly on every IPv6 socket**, to
whatever the caller asked for, and never left to the system default.
`/proc/sys/net/ipv6/bindv6only` varies by distribution, and a listener whose
address family depends on a sysctl is a listener that behaves differently on
two machines with the same binary. The builder's default is **v6only on**,
because a program that wants dual-stack should say so.

---

## 5. `UnixAddr`, and the abstract namespace

**Rule A-11 — three kinds, and the encoding differs for each.**

| Kind | `sun_path` | `addrlen` passed |
|---|---|---|
| **unnamed** | not used | `2` |
| **pathname** | the path bytes, NUL-terminated | `2 + len + 1` |
| **abstract** | `0` then `len` bytes, **no terminator** | `2 + 1 + len` |

**Rule A-12 — the abstract encoding is where the classic bug lives.** An
abstract address is `sun_path[0] == 0` followed by `len` bytes, and **the
kernel uses exactly `addrlen - 2` bytes of `sun_path`** — trailing NULs are
*significant*. Passing `sizeof(struct sockaddr_un)` as the length for an
abstract address therefore binds a name with 107 trailing NUL bytes in it,
which is a different name from the one intended and which nothing else will
ever connect to. The library computes the length from the name and never from
the structure.

**Rule A-13 — a pathname is at most 107 bytes**, not 108: the terminating NUL
occupies the last. A 108-byte path is `ESockAddr`, refused at the encode, with
the length in the message. Silently truncating a path is how a daemon binds
somewhere nobody looks.

**Rule A-14 (SK-023) — `UnixAddr` is not a `Path`.** The prelude's `Path` (D-051,
D-054) requires an **absolute** path — `path_parse` fails `BadPath` on anything
whose first byte is not `/` — and an abstract address is not a filesystem
object at all. Unix socket addresses are routinely relative (`./app.sock`) and
routinely abstract, so `Path` is the wrong type twice over. `unix_addr_path`
takes a byte slice; `unix_addr_from_path(Path)` exists as the convenience for
callers who genuinely have an absolute path and want the check.

**Rule A-15 — an unnamed address is a real answer.** `getsockname` on a
`socketpair` end, or on a client `AF_UNIX` socket that never bound, returns
`addrlen == 2` and no path. That is `kind == 0`, not an error, and a caller
formatting it gets `"<unnamed>"`.

---

## 6. Byte order

**Rule A-16 (SK-017).** Conversion between host and network order happens in
**one module**, `src/addr/order.npk`, in four functions:

```nitpick
hton16(uint16) -> uint16      ntoh16(uint16) -> uint16
hton32(uint32) -> uint32      ntoh32(uint32) -> uint32
```

and every port, every IPv4 word and every `sin6_flowinfo` goes through one of
them. Nothing else in the library shifts or masks an address field.

**Rule A-17 — the implementation is a byte permutation, not arithmetic.**
`hton16(p)` is `(p >> 8) | ((p & 0xFF) << 8)` computed in `uint16`, which under
D-210 traps on overflow — and cannot overflow, because a shift is not an
arithmetic operation and the mask bounds the operand. Stated because the
obvious "multiply by 256" spelling *would* trap, and somebody will try it.

**Rule A-18 — x86-64 is little-endian and the library does not pretend
otherwise.** These four functions are unconditional swaps. A big-endian port
would make them identity, and that is a port's change to make in one file — the
reason the conversion is centralised is as much this as it is auditability.

---

## 7. Parsing

**Rule A-19 (SK-036) — `ipv4_parse` is strict.** Exactly four decimal octets separated
by dots, each 0–255, **no leading zeros**, nothing else. In particular it
refuses:

| Refused | Because |
|---|---|
| `127.1` | the "short form" a `inet_addr` accepts and nobody means |
| `0177.0.0.1` | leading zeros are **octal** in `inet_aton`, and `010.0.0.1` is `8.0.0.1` — a real source of allowlist bypasses |
| `010.0.0.1` | a leading zero within three digits: POSIX.1-2024's `inet_pton` accepts it as 10, `inet_aton` reads 8 |
| `1.2.3.04` | the same, in the last octet |
| `0x7f.0.0.1` | hex octets, same family of bug |
| `1.2.3.4.5`, `1.2.3.` | wrong shape |
| `+1.2.3.4`, ` 1.2.3.4` | sign, whitespace |

This is glibc's `inet_pton` behaviour (measured at 2.39) and RFC 3986 §3.2.2's
`dec-octet` grammar, rather than `inet_aton`'s, and it is deliberately stricter
than POSIX.1-2024, whose `inet_pton` allows a leading zero within three digits
(Austin Group Defect 1573). The difference between the `inet_pton` and
`inet_aton` behaviours has produced CVEs in more than one language's standard
library. A parser that accepts more than one spelling of an address is a parser
that lets a validator and a connector disagree.

**Rule A-20 — `ipv6_parse` implements RFC 4291 §2.2 exactly**: eight
colon-separated groups of one to four hex digits, at most one `::`, an optional
trailing IPv4 dotted-quad form for the last 32 bits, and an optional `%scope`
suffix. Uppercase and lowercase hex both accepted; nothing else. The
dotted-quad is read by A-19's rules, so `::ffff:010.0.0.1` is refused, as RFC
3986's `IPv4address` and glibc's `inet_pton` refuse it.

**Rule A-21 — `socket_addr_parse` takes the bracketed form for IPv6**:
`1.2.3.4:80` and `[::1]:80`. `::1:80` is ambiguous — it is a valid IPv6 address
in its own right — and the bracket form is what every RFC and every tool uses.
Unbracketed IPv6 with a port is `ESockAddr`.

**Rule A-22 — a parser is a pure function over `uint8[]`** and allocates
nothing. It takes a byte slice, not a `string`, so a caller parsing out of a
buffer does not build one first.

---

## 8. Formatting

**Rule A-23 — formatting appends to a `Bytes`** (`core/`), never builds a
`string` per call. `string_concat` allocates, and formatting an address is
otherwise a natural place to write the quadratic loop the compiler measured in
its own tool runner. `addr_to_string` exists as the convenience and calls the
appending form.

**Rule A-24 — IPv6 formatting is RFC 5952 canonical**: lowercase hex, no
leading zeros in a group, `::` replacing the **longest** run of zero groups
(the leftmost on a tie), never replacing a run of exactly one group, and the
IPv4-mapped form printed as `::ffff:1.2.3.4`. Canonical output is what makes
two addresses comparable as text, and non-canonical output is what makes a log
grep miss.

**Rule A-25 — parse ∘ format is the identity on every valid address**, and
that round trip is a property test over a generated corpus (`TESTING.md` §4).
It is this library's cheapest oracle and it costs nothing to have.

---

## 9. What is deliberately absent

- **Name resolution.** No `getaddrinfo`, no `/etc/hosts`, no DNS
  (`SK-024`). A hostname is not an address, resolving one is a wire protocol
  and a parser with its own failure modes and its own security surface, and it
  belongs in a library that can be audited as that. `socket_addr_parse` takes
  an address and says so.
- **`/etc/services`.** A port is a number.
- **CIDR and subnet arithmetic.** Genuinely useful and genuinely a different
  library; recorded as `O-A2` rather than smuggled in.
- **Interface enumeration** (`getifaddrs`, `if_nametoindex`). A scope id is
  carried as a number; turning `%eth0` into that number needs
  `RTM_GETLINK` over a netlink socket, which is a protocol implementation.
  Recorded as `O-A3`.

---

## 10. Open items

- **O-A1 — whether `Ipv6Addr` should be 16 bytes with the scope kept in
  `SocketAddrV6` instead.** As specified the scope rides with the address,
  which matches `sockaddr_in6` and keeps `IpAddr` self-contained; the
  alternative matches Rust's `Ipv6Addr` and makes the type exactly the wire's
  16 bytes. **Recommendation:** keep the scope on the address, because a
  link-local address without one is a bug waiting to happen and separating them
  makes it easy to drop. Settled at cycle 0.1's close.
- **O-A2 — CIDR / prefix arithmetic.** `Ipv4Net`, `Ipv6Net`, containment tests.
  **Recommendation:** out at 1.0; it is a clean separate library and nothing in
  `nsockets` needs it.
- **O-A3 — `%interface` scope names.** Requires netlink. **Recommendation:**
  parse and format numeric scope ids at 1.0; accept a name only when something
  needs it, and say so in the parser's documentation so the gap is visible.
