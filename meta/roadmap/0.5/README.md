# Cycle 0.5 — Ancillary data

**`src/ancillary/`: the one `msghdr`, `SCM_RIGHTS`, `SCM_CREDENTIALS`.** The
smallest cycle in the plan and the one with the most ways to leak a descriptor.

## Decisions in

`SK-015` (`ESockProtocol` is declared here and nowhere else), `SK-016`.
Settled.

**Open questions to settle:** `O-Y1` (the 16-descriptor cap —
recommendation: keep it).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.5.0 | **The one `msghdr`** — layout, `CMSG_LEN` vs `CMSG_SPACE`, the walk | a `sendmsg`/`recvmsg` round trip with no ancillary payload |
| 0.5.1 | **`SCM_RIGHTS`** — send, receive, `MSG_CMSG_CLOEXEC`, the ownership ordering | a descriptor passed and used at the far end |
| 0.5.2 | **The refusal paths** — `MSG_CTRUNC`, wrong level, wrong type | every refusal closing every descriptor it received |
| 0.5.3 | **`SCM_CREDENTIALS`** — `SO_PASSCRED`, `ucred` | a message's sender identified and the kernel's validation relied on |
| 0.5.4 | **The `cmsghdr` fuzzer** | a million random control buffers, clean |
| 0.5.5 | **Close** | `done/0.5/`, `0.6.0.md` written |

## Checklist

### 0.5.0 — the one `msghdr`
- [ ] `MsgHdr` (56), `IoVec` (16), `CMsg` (16 + payload) as Nitpick structs over
      one fixed block, `#size_of` asserted for each
- [ ] `msg_namelen` and `msg_flags` as single 8-byte words covering the `int32`
      and its padding (N-1) — layout-identical, and what the compiler's Bridge
      does
- [ ] **one place lays out a `msghdr`** (N-3), and a tree check says so
- [ ] `CMSG_LEN(n) == 16 + n` and `CMSG_SPACE(n)` rounded to 8, **as separate
      named functions**, because conflating them is the most common
      `SCM_RIGHTS` bug (N-2)
- [ ] the control buffer a fixed 256-byte stack array (N-4), taking no `wild`
      bytes
- [ ] the `cmsghdr` walk with its invariant and variant written as comments in
      the syntax they will take (`specs/VERIFICATION.md` Z-3)
- [ ] **a `cmsg_len` below 16 refused before advancing** — the guard that turns
      a hostile zero-length header from a hang into an error

### 0.5.1 — `SCM_RIGHTS`
- [ ] send with one descriptor, `msg_controllen = CMSG_SPACE(4)`,
      `cmsg_len = CMSG_LEN(4) = 20`
- [ ] **at least one payload byte always** (N-7); a zero-length ancillary send
      refused `ESockState`
- [ ] receive with **`MSG_CMSG_CLOEXEC`** always (N-8), and the received
      descriptor's `FD_CLOEXEC` asserted set
- [ ] **the ownership ordering** (N-9): every received descriptor wrapped in an
      `OwnedFd` **before** any validation, with a comment at the site saying the
      order is a resource-safety property
- [ ] up to `NSOCK_SCM_MAX_FDS` (16) descriptors in one message; a request for
      more refused `ESockCapacity` **before** the syscall
- [ ] a descriptor passed over a `socketpair`, a `UnixStream` and a
      `UnixDatagram`, and used at the far end in each
- [ ] `// stress: 40`

### 0.5.2 — the refusal paths
- [ ] `MSG_CTRUNC` (8) → `ESockProtocol`, **with every received descriptor
      closed** and the expected count reported (N-10)
- [ ] a `cmsghdr` of the wrong level or type → `ESockProtocol`, descriptors
      closed first (N-11)
- [ ] a test that deliberately under-sizes the control buffer and asserts both
      the refusal and that `/proc/self/fd` shows no leak
- [ ] `check_error_budget` confirming `ESockProtocol` is declared **only** in
      this module (`SAFETY.md` S-8)

### 0.5.3 — `SCM_CREDENTIALS`
- [ ] `SO_PASSCRED` (16) set on the receiver, once, and recorded (N-14)
- [ ] a 12-byte `ucred` decoded, offsets asserted
- [ ] a test that forks a child which sends a message, and asserts the parent
      sees the child's pid, uid and gid
- [ ] a test that a sender **cannot** claim another uid without capability —
      the kernel's validation, which is the whole reason `ucred` is trustworthy
      (N-15)
- [ ] the documentation distinguishing this from `SO_PEERCRED` (N-16) and
      carrying the pid-is-not-a-capability warning (N-17)

### 0.5.4 — the fuzzer
- [ ] `tools/fuzz_cmsg.py` driving the `cmsghdr` reader with random control
      buffers
- [ ] the four invariants: never traps; never reads past `msg_controllen`;
      never returns a descriptor it did not receive; **closes every descriptor
      on every refusal path**
- [ ] a million inputs clean
- [ ] any input that found something committed as a permanent fixture

## Gate

A descriptor passed over a `socketpair` and used at the far end; `MSG_CTRUNC`
producing `ESockProtocol` with every received descriptor closed and no leak;
and the fuzzer clean over a million inputs.

## Watch for

- **This is the library's only parser of attacker-adjacent binary data**, and
  its failure mode is a leaked or double-closed descriptor rather than a wrong
  answer. The fuzzer is not optional.
- **`CMSG_LEN` and `CMSG_SPACE` are different numbers** (20 and 24 for one
  descriptor) and `msg_controllen` on send is the *space* while `cmsg_len`
  inside the header is the *len*. Getting them the wrong way round produces a
  message that works on one kernel and not another.
- **N-9's ordering is two statements in the right order** and nothing about the
  code makes the order look important. The comment is what carries it, and the
  `prove` in `specs/VERIFICATION.md` Z-6 is what will eventually enforce it.
- **The compiler's `lib/nbridge.npk` is the oracle**, not the dependency. Read
  it; do not import it (`SK-006`).
