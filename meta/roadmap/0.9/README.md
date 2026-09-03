# Cycle 0.9 — The dogfood application

**A real program, in `examples/`, written against the library as a consumer.**

## Why a cycle

Because an example written by the person who wrote the API is weak evidence: it
demonstrates the features the author was thinking about. A program with a
purpose finds what is missing, what is awkward, and what is wrong — and finds
it before a 1.0 that would have to keep it.

## What to build

**A TCP proxy with an `AF_UNIX` admin socket.** Chosen deliberately over a
prettier demo because it exercises, in one program with a reason to exist,
almost everything the library has:

| Feature | Exercises |
|---|---|
| listen and accept on TCP | the accept loop, `ECONNABORTED`, the bounded ceiling |
| connect to an upstream | `SK-014`'s full `EINPROGRESS` path, including failures |
| forward bytes both ways | `Reader`/`Writer`, partial writes, `write_all` |
| a peer that closes one direction | half-close, `IoEof`, `SK-019` |
| an upstream that dies mid-transfer | `EPIPE` through `MSG_NOSIGNAL` — `SK-013` under real conditions |
| an admin socket over `AF_UNIX` | abstract binding, `SO_PEERCRED` authorisation |
| `admin: pass me a listening socket` | `SCM_RIGHTS` end to end, and `sock_adopt` |
| many connections at once | `SK-035`'s accept-then-spawn, and `O-C2`'s numbers under a real load |
| a descriptor-exhaustion run | the `EMFILE` back-off |
| IPv4 and IPv6 upstreams | dual-stack, `IPV6_V6ONLY`, `SK-037`'s mapped-address rule |

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.9.0 | **The program** — written straight through, recording every friction | a working proxy, and a numbered findings list |
| 0.9.1 | **The findings, triaged** | a decision per finding |
| 0.9.2 | **The fixes** | the library changed where the finding survived triage |
| 0.9.3 | **Close** | `done/0.9/`, `0.10.0.md` written |

## Checklist

### 0.9.0 — the program
- [ ] written **without changing the library**, so every friction is recorded
      rather than smoothed over as it appears
- [ ] every awkwardness written down as it is met, numbered, with the line that
      caused it
- [ ] runs against a real upstream, against one that refuses, against one that
      dies mid-transfer, and under a thousand concurrent connections
- [ ] the admin socket authorising by `SO_PEERCRED` uid, with the
      pid-is-not-a-capability rule honoured (N-17)
- [ ] a listening socket handed to the proxy over `SCM_RIGHTS` and adopted —
      the socket-activation shape, which is `O-K3`'s justification
- [ ] `NSOCK_RECORD`-style transcripts of each scenario committed as replay
      fixtures where the shape allows

### 0.9.1 — triage
- [ ] every finding classified: **defect** (the library is wrong), **gap** (the
      library is missing something a consumer reasonably needs), or **cost**
      (the library is right and this is what the design costs)
- [ ] every `cost` written into the documentation, because an accepted cost
      nobody warned about is a defect in the documentation
- [ ] every `gap` sized, and either scheduled into 0.10 or recorded as post-1.0
- [ ] **`O-C3` revisited**: did this program want a `SO_REUSEPORT` helper? A
      decision either way, with the code that would have used it

### 0.9.2 — the fixes
- [ ] the defects fixed, each with a regression test
- [ ] the scheduled gaps closed
- [ ] `specs/` amended where a finding contradicted it, with a decision recorded
      in the same commit

## Gate

A proxy a person would actually run, and a triaged findings list with a
decision per entry.

## Watch for

- **The temptation to fix as you write.** The value of this cycle is the
  *record* of what was awkward; a friction smoothed over in the moment is a
  friction the next user meets too.
- **"It needs a feature" is usually "the example needs a helper".** A gap is
  only a gap if it cannot be written in the application in a reasonable number
  of lines.
- **This is where `SK-035` gets its real test.** A proxy is exactly the shape
  that wants a worker pool in every other language, and writing it under the
  accept-then-spawn constraint is the honest evidence for whether the
  constraint is livable.
