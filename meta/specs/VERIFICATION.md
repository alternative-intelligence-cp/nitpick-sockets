# Verification obligations

> **Rule prefix:** the rules in this document are `Z-n`. `Q-n` is reserved
> ecosystem-wide for a question addressed to the project's author
> (`../OPEN_QUESTIONS.md`), so this document does not use it.

The compiler's cycle 1.5 makes `prove`, `requires`/`ensures`, `limit<Rules>`
and Z3 real. Its orchestration rules say that **every branch records its own
verification obligations and the orchestrator merges them** (R9), because
obligations discovered in a branch and never collected are the cheapest way to
lose the campaign.

This document is `nsockets`' list. It is written **before** the code and kept
current as the code lands.

---

## 1. Where this stands

| Compiler subcycle | What it gives us | Our state |
|---|---|---|
| 1.5.0 (done) | the SMT writer, z3 under a pinned profile, the obligation manifest, `llvm.assume` elision | §3's bounds obligations are already decidable |
| 1.5.1 | `limit<R>` names resolve, `Rules` bodies type, contract expressions type | §5 becomes writable |
| 1.5.2 | `limit<Rules>` live | §5 lands |
| 1.5.3 | contracts live | §3 and §4's clauses land |
| 1.5.4 | `prove` / `assert_static` | §6 lands |

**Rule Z-1.** Until a construct is live, its obligation is stated **as a
comment beside the code in the exact syntax it will take**, and is enforced by
a property test. The switch is then deleting a comment marker rather than
inventing the clause. The compiler's rungs refuse the constructs by name today,
so a premature `ensures` is a build failure and not a silent no-op.

---

## 2. What the language discharges for free

Worth stating, because it is most of the list:

- **Every index into a slice, array or `buffer` is bounds-checked** and traps
  (D-070) — so a wrong offset into a `sockaddr` is a crash, not a read of
  adjacent memory. That single fact removes the entire class of bug that CVEs
  in C socket code are made of.
- **Every plain integer `+ - *` traps on overflow** (D-210) — so a length
  arithmetic mistake in the ancillary walk is a crash, not a short read.
- **`OwnedFd`'s drop is the close** (D-185) — so a descriptor cannot be
  forgotten on a normal path.
- **`exit 0` with a live `wild` allocation traps** (D-151) — so a leak in a
  test is a failing test.
- **Owning values are move-only** (TYPE-046) — so no socket is aliased.
- **`Result<T>` everywhere** with no unchecked unwrap outside a `never fails`
  callee (D-163) — so no errno is dropped.

The obligations below are the ones that remain.

---

## 3. Bounds — the largest class

**Rule Z-2 — every kernel-structure field access goes through one accessor per
field** (`SAFETY.md` S-16), and the accessor carries the obligation:

```nitpick
func:sin_port_at = uint16(fixed uint8[]:sa)
    requires (sa.len >= 16i64)
    never fails { … };
```

Discharging it makes every `sockaddr_in` read safe by construction and elides
the runtime bound check, which is D-218.9's payoff.

| Site | Obligation |
|---|---|
| `sockaddr_in` field reads | `sa.len >= 16` |
| `sockaddr_in6` field reads | `sa.len >= 28` |
| `sockaddr_un` path read | `sa.len >= 2 && sa.len <= 110` |
| the decode dispatch | the family byte is read before anything else, and only within a 2-byte minimum |
| `Vec<T>` `at`/`set` | index `< count` |
| `Bytes` append | `len + n <= cap` after the reserve |

**Rule Z-3 — the `cmsghdr` walk is the obligation that matters most**, because
it is a loop over kernel-supplied lengths and it is the only place in this
library where attacker-adjacent binary data drives an offset:

```nitpick
// invariant, at the top of every iteration:
//   off >= 0 && off + 16 <= controllen
//   cmsg_len >= 16 && off + cmsg_len <= controllen
// variant: controllen - off, strictly decreasing
```

The variant is what makes the loop terminate: a `cmsg_len` of 0 — which a
hostile or buggy sender can produce — would otherwise loop forever at the same
offset. **The library refuses a `cmsg_len` below 16 before advancing**, and the
`prove` at that site is the difference between a hang and a compile-time
guarantee.

---

## 4. Contracts on the boundary functions

**Rule Z-4.** Three shapes, written as `ensures` when 1.5.3 lands:

```nitpick
pub func:addr_encode = int64(SocketAddr:a, uint8[]:dest)
    requires (dest.len >= 28i64)              // the largest family
    ensures  (result >= 16i64 && result <= 28i64);

pub func:unix_encode = int64(UnixAddr:a, uint8[]:dest)
    requires (dest.len >= 110i64)
    ensures  (result >= 2i64 && result <= 110i64);

pub func:hton16 = uint16(uint16:v)
    ensures  (ntoh16(result) == v);           // the pair is an involution
```

The last one is small and worth having: an involution is exactly the property a
byte-swap should have, it is trivially decidable, and getting it wrong is a
silent wrong-port bug.

---

## 5. `limit<Rules>`

**Rule Z-5.** When 1.5.2 lands:

```nitpick
Rules:Port      = { $ >= 0u16; $ <= 65535u16; };     // total, but names the intent
Rules:Backlog   = { $ >= 0i32; };
Rules:UnixLen   = { $ >= 0u8;  $ <= 108u8; };
Rules:FdCount   = { $ >= 0i32; $ <= 16i32; };        // ANCILLARY_MODEL.md N-5
Rules:AddrLen   = { $ >= 2i64; $ <= 128i64; };
```

`UnixLen` and `FdCount` are the two that carry weight: the first is what makes
`ADDRESS_MODEL.md` A-13's refusal structural, and the second is what makes the
ancillary control buffer's size provably sufficient.

---

## 6. `prove` sites

**Rule Z-6.**

| Site | Proof |
|---|---|
| after `addr_decode` | the family is one of 1, 2, 10 — nothing else reaches the switch |
| after `addr_encode` | the returned length is what the family's table says |
| in the `cmsghdr` walk | Z-3's invariant, at the top of each iteration |
| after a `recvmsg` | every descriptor in the control payload is wrapped in an `OwnedFd` before any refusal path is taken (N-9) |
| after `hton16`/`ntoh16` | the involution |
| in the accept loop | the retry count is bounded, so `ECONNABORTED` cannot spin forever |

**Rule Z-7 — N-9's ordering is the one that is a *safety* property rather than
a correctness one.** "Every received descriptor is owned before anything can
fail" is provable as a straight-line fact about one function, it is exactly the
kind of thing a reviewer's eye slides over, and getting it wrong leaks a
descriptor permanently.

---

## 7. Termination

**Rule Z-8.** Every loop, and its variant:

| Loop | Variant |
|---|---|
| `cmsghdr` walk | `controllen - off`, strictly decreasing (Z-3) |
| address parse | bytes remaining |
| address format | groups remaining |
| `write_all` | bytes remaining, plus the deadline |
| every retry loop | the monotonic deadline |
| accept loop | **does not terminate, by design** — Z-9 |

**Rule Z-9.** The accept loop and the poll loop do not terminate, and their
obligation is different: **every iteration terminates**, and every wait inside
one is bounded by a deadline. There is no unbounded wait anywhere in this
library, which is `SAFETY.md` S-10 and is what makes the statement possible.

---

## 8. What cannot be proven, and is stated instead

**Rule Z-10 — the honest claim.** Following the compiler's TCB doctrine
(`TCB.md`, D-218.11: *verified middle-end plus validated floor*), `nsockets`'
verification claim covers **its own arithmetic, its own memory discipline, and
the descriptor-ownership property**. It does not and cannot cover:

- **the kernel.** `bind` does what the kernel does; `MSG_NOSIGNAL` suppresses
  the signal because the kernel says so.
- **the peer.** Every byte that arrives is untrusted, and the library's claim is
  that it cannot be made to trap or leak by them — not that they are honest.
- **the network.** Delivery, ordering beyond what the transport guarantees, and
  timing are not properties this library has.
- **`llc` and `ld.lld`**, which the compiler names as trusted components.

The residue is enumerated rather than mitigated, which is the seL4 precedent
the compiler cites.

---

## 9. The handoff

**Rule Z-11.** When the compiler's verified build reaches libraries,
`nsockets` hands over: this document's obligation list, the
`nitpick.obligations` rows its own build produces, and the property tests that
stood in for each unproven row. The closing cycle owns that handoff.
