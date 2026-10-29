# Cycle 1.0 — Release

**Documentation, the API freeze, the `failsafe` arm contract, and versioning.**

## Decisions in

`SK-034` (adding an error identity is a major version). `Q-3`'s version policy
is settled here if the author has not settled it earlier.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 1.0.0 | **The API freeze** — the public surface enumerated in one file | `src/lib.npk` as the contract |
| 1.0.1 | **The `failsafe` contract** — the generated per-import arm list | a consumer knows exactly what importing costs |
| 1.0.2 | **The guide** — `docs/` | a person can build a server from the documentation alone |
| 1.0.3 | **Examples** | every example built and run by the harness |
| 1.0.4 | **Versioning** — `Q-3` published | a stated policy, including what a major version means |
| 1.0.5 | **Close** | `done/1.0/`, the post-1.0 map reviewed |

## Checklist

### 1.0.0 — the API freeze
- [ ] `src/lib.npk` lists every public name, one per line, grouped by module
- [ ] each reviewed: is it needed, is it named right, does it belong at this
      layer?
- [ ] anything not needed removed **now** — removing a public name after 1.0 is
      a major version
- [ ] a conformance test that imports the umbrella and touches every name, so a
      removal breaks a test rather than a user
- [ ] `raw.npk` confirmed **not** re-exported (`SK-026`)

### 1.0.1 — the `failsafe` contract
- [ ] the per-import arm list generated (`SAFETY.md` S-9) and published in
      `docs/`
- [ ] `check_failsafe_arms` proving the published list is what a program
      actually owes
- [ ] **the four identities stated as the contract**, with `SK-034`'s rule that
      a fifth is a major version — the one thing about `nsockets` a consumer
      most needs to know, and a rule no library in another language has to state
- [ ] the fact that **a program that parses addresses and never opens a socket
      owes one arm of this library's** stated prominently — `ESockAddr`,
      qualified by its module, beside the floor's six and what the parser's code
      reaches (`SAFETY.md` S-8, SK-105)

### 1.0.2 — the guide
- [ ] getting started: an echo server in under thirty lines
- [ ] the model: typestate, the builder, `OwnedFd` lifetimes, deadlines
- [ ] **the two rules a consumer must know**: `MSG_NOSIGNAL` is handled for you
      *unless you take a raw descriptor* (`SAFETY.md` S-2's note), and a bound
      Unix socket path is yours to unlink (`SK-020`)
- [ ] **the server chapter**: accept-then-spawn, why a worker pool over a
      channel is not expressible, and what to do instead — with the compiler
      diagnostic quoted, so a reader who hits it recognises it
- [ ] the compatibility matrix, as measured
- [ ] a page on what `nsockets` deliberately does not do and why: no DNS, no
      TLS, no raw sockets, no netlink, no `sendmmsg` — each pointing at its
      decision

### 1.0.3 — examples
- [ ] an echo server and client (TCP)
- [ ] a Unix-domain request/response service with `SO_PEERCRED` authorisation
- [ ] a descriptor-passing pair
- [ ] a UDP responder demonstrating truncation handling
- [ ] the 0.9 proxy, cleaned up
- [ ] **every example built and run by the harness**, so a broken example is a
      red run

### 1.0.4 — versioning
- [ ] `Q-3` settled and recorded
- [ ] `SK-034`'s rule published: adding a public error identity is a **major**
      version, because it is a compiler-enforced source break in every consumer
- [ ] the current identity count (four) published beside it, so a consumer can
      see the budget rather than infer it

## Gate

A person who has not seen the code can build a working server from `docs/`
alone, and every example is green in the harness.

## After

The post-1.0 map in `ROADMAP.md`: `aarch64` (1.1), the batched syscalls and
timestamps if a consumer measures a need (1.2), and the verified build (1.3)
once the compiler's `npkg verify` reaches libraries.
