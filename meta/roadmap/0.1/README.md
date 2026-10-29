# Cycle 0.1 — Addresses

**`src/addr/`: the five types, the kernel encodings, byte order, the parsers
and the formatters.** The layer with no descriptors in it — pure computation
over values, fully testable with no kernel, and the only module besides
`src/sys/` a program can import without owning a socket.

> **`0.1.0.md` is written execution-grade at cycle 0.0's close** (0.0.5, step
> 4). That is the convention for every cycle: the opening subcycle file is
> written by the cycle before it, by the session that just learned what that
> cycle taught.

## Why here

Nothing can `bind` without an address, and this layer needs nothing from
anything. It is also where the strongest cheap oracle in the library lives —
parse ∘ format is the identity — so getting it first means every later cycle
has a trustworthy way to say what it is talking to.

## Decisions in

`SK-016`, `SK-017`, `SK-022`, `SK-023`, `SK-028`, `SK-036`, `SK-037`. All
settled.

**Open questions to settle in this cycle:** `O-A1` (does `Ipv6Addr` carry its
scope id? recommendation: yes).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.1.0 | **The types and byte order** — the five values, `src/addr/order.npk` | `#size_of` asserted for each; the involution property green |
| 0.1.1 | **Encode and decode** — `sockaddr_in`/`in6`/`un`, every offset | the kernel round trip: encode → `bind` → `getsockname` → decode |
| 0.1.2 | **`UnixAddr`** — the three kinds and the abstract encoding | the abstract length asserted byte for byte; a 108-byte path refused |
| 0.1.3 | **Parsing** — strict IPv4, RFC 4291 IPv6, the bracketed host:port form | every refusal in A-19's table is a passing rejection test |
| 0.1.4 | **Formatting** — RFC 5952 canonical | canonical over any accepted spelling |
| 0.1.5 | **Close** | `done/0.1/`, `0.2.0.md` written |

## Checklist

### 0.1.0 — the types and byte order
- [ ] `Ipv4Addr`, `Ipv6Addr`, `IpAddr`, `SocketAddrV4`, `SocketAddrV6`, `SocketAddr`, `UnixAddr`
- [ ] **no owning field in any of them** (`SK-022`); `check_no_owning_addr` added to the tree checks
- [ ] `#size_of` asserted for each, and the numbers recorded in `ADDRESS_MODEL.md` §1
- [ ] octets stored in **network** order, ports in **host** order (A-2), stated in each type's comment
- [ ] `src/addr/order.npk` with `hton16`/`ntoh16`/`hton32`/`ntoh32` and **nothing else in the library shifting an address field**
- [ ] the involution property (`ntoh16(hton16(x)) == x`) as a property test over every `uint16`
- [ ] `O-A1` decided and recorded

### 0.1.1 — encode and decode
- [ ] `addr_encode` / `addr_decode` — one pair, and nothing else touches the bytes (A-5)
- [ ] every offset from `ADDRESS_MODEL.md` §2, each behind its own accessor over `fixed uint8[]` (`SAFETY.md` S-16, SK-103)
- [ ] `sin_zero` zeroed on every encode (A-6), so two encodings of one address compare equal
- [ ] `sin6_flowinfo` swapped, `sin6_scope_id` **not** — the adjacent-fields-opposite-conventions case, with its own test
- [ ] the returned length is the `addrlen` to pass, and is never `sizeof(sockaddr_storage)`
- [ ] an unknown family decodes to `ESockAddr` (A-7)
- [ ] **the kernel round trip**: encode → `bind` a loopback socket → `getsockname` → decode → compare, for `AF_INET` and `AF_INET6`
- [ ] `check_struct_sizes` goes live

### 0.1.2 — `UnixAddr`
- [ ] the three kinds — unnamed, pathname, abstract — and the `addrlen` each produces (A-11)
- [ ] **the abstract encoding asserted byte for byte**: `sun_path[0] == 0`, `addrlen == 2 + 1 + len`, and a test that binds two abstract names differing only in trailing bytes and asserts they are different addresses (A-12)
- [ ] a 108-byte path refused `ESockAddr` with the length in the message (A-13)
- [ ] a 107-byte path accepted, with its NUL
- [ ] `unix_addr_from_path(Path)` for absolute paths; `unix_addr_path(fixed uint8[])` for everything else (A-14)
- [ ] an unnamed address round-trips through `getsockname` on a `socketpair` end (A-15)

### 0.1.3 — parsing
- [ ] `ipv4_parse` strict: four decimal octets, 0–255, **no leading zeros**
- [ ] **every spelling in A-19's refusal table is a rejection test** — `127.1`, `0177.0.0.1`, `010.0.0.1`, `1.2.3.04`, `0x7f.0.0.1`, `1.2.3.4.5`, `1.2.3.`, `+1.2.3.4`, leading whitespace — because an untested security claim is a comment
- [ ] `ipv6_parse` per RFC 4291 §2.2: eight groups, at most one `::`, the trailing dotted-quad form, the `%scope` suffix
- [ ] `socket_addr_parse` with the bracketed IPv6 form; unbracketed IPv6-with-port refused (A-21)
- [ ] every parser takes `fixed uint8[]`, not `string`, and allocates nothing (A-22); `socket_addr_parse(string_bytes(s))` compiles (SK-103)

### 0.1.4 — formatting
- [ ] appends to a `Bytes`, never `string_concat` in a loop (A-23)
- [ ] RFC 5952 canonical IPv6: lowercase, no leading zeros, `::` on the **longest** zero run (leftmost on a tie), never on a run of one, `::ffff:1.2.3.4` for mapped (A-24)
- [ ] `parse ∘ format` is the identity over a generated corpus (A-25)
- [ ] `format ∘ parse ∘ format == format` over **any accepted spelling**, which is the property that actually catches a formatter bug
- [ ] `ipv6_to_v4_mapped` explicit, returning `Ipv4Addr?`, never automatic (`SK-037`)

## Gate

The kernel round trip green for both IP families; every A-19 refusal a passing
test; and both round-trip properties green over a generated corpus.

## Watch for

- **`sin6_flowinfo` and `sin6_scope_id` are adjacent, the same width, and have
  opposite byte-order conventions.** That is the ABI. A "swap everything on the
  way out" implementation is wrong and will pass a naive test, because a scope
  id of 0 swaps to 0.
- **The abstract-namespace length is the classic bug** (A-12) and passing
  `sizeof(struct sockaddr_un)` produces a name with 107 trailing NULs that
  nothing will ever connect to. The test that catches it binds two names
  differing only past the intended length.
- **`any` is a type keyword** and `INADDR_ANY` is a thing this cycle talks
  about constantly. `addr_any` is the spelling (`specs/BUILD.md` §7).
