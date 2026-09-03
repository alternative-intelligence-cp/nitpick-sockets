# Cycle 0.10 — Hardening

**The fuzz sweep, the stress sweep, the compatibility matrix, and the
verification obligations reconciled.** Everything the plan deferred to "before
release", collected.

## Decisions in

`SK-016`, and `specs/VERIFICATION.md` in full.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.10.0 | **The fuzz sweep** — the address parsers and the `cmsghdr` reader | a hundred million inputs across both, clean |
| 0.10.1 | **The stress sweep** — `// stress: 40` on everything with a timing dimension | forty runs, same answer, every time |
| 0.10.2 | **The compatibility matrix** — recorded runs per environment | every row Verified or removed |
| 0.10.3 | **The verification reconciliation** | an obligation list that is true |
| 0.10.4 | **The audit** — a read of the whole tree against the specifications | a findings list, and the specifications corrected |
| 0.10.5 | **Close** | `done/0.10/`, `1.0.0.md` written |

## Checklist

### 0.10.0 — fuzz
- [ ] the address parsers: random bytes and structured mutations, asserting
      never traps, always terminates, **never accepts a spelling A-19's table
      refuses**, and `format(parse(x))` is canonical
- [ ] the `cmsghdr` reader: random control buffers, asserting never traps,
      never reads past `msg_controllen`, never returns a descriptor it did not
      receive, and **closes every descriptor on every refusal path**
- [ ] a hundred million inputs across both, clean
- [ ] every corpus that found something committed permanently

### 0.10.1 — stress
- [ ] `// stress: 40` on: connect (both legs), accept, the `SIGPIPE` regression,
      every ancillary round trip, the bounded accept loop, the `EMFILE`
      back-off, and `poll_set`
- [ ] **a red under stress is a stop sign, never a retry** — every timing-shaped
      defect the compiler found looked like flakiness first

### 0.10.2 — the compatibility matrix
- [ ] a recorded `loopback` run for every environment in `specs/COMPAT.md` §3
- [ ] **an environment with no recorded run is removed from the table**, not
      downgraded (W-1)
- [ ] the no-IPv6 container row exercised deliberately, because a library that
      dies on `EAFNOSUPPORT` will not start in half of CI (W-6)
- [ ] the abstract-namespace column marked Linux-only (W-7)

### 0.10.3 — verification
- [ ] `specs/VERIFICATION.md`'s obligation list read against the code, entry by
      entry
- [ ] every obligation the code generates that the list does not name, added
- [ ] every obligation the list names that the code does not generate, removed
      or scheduled
- [ ] the contracts written as comments (Z-1) checked to be syntactically what
      they will be — by pasting one into a scratch file and confirming the
      compiler's rung refuses it **by name** rather than parsing it as something
      else
- [ ] the property tests standing in for each, present and green
- [ ] the whole list handed forward as `meta/OBLIGATIONS.md`, ready for the
      compiler's verified build (Z-11)

### 0.10.4 — the audit
- [ ] every specification document read against the code that implements it
- [ ] every numbered rule either implemented, refused with a reason, or struck
      by a decision
- [ ] the tree checks' coverage reviewed: **is there a document nothing diffs
      against?**
- [ ] `check_specs_current`'s backlog drained
- [ ] `check_msg_nosignal`'s input confirmed non-empty and covering every send
      site in the tree — the rule the whole library rests on, checked one last
      time before it is frozen

## Gate

Every tree check green; every claimed environment backed by a recorded run; and
the obligation list true.

## Watch for

- **The audit is the cycle's most valuable part and the easiest to shorten.**
  The compiler's cycle 0.6 found every one of its holes this way and none of
  them by a test.
- **A specification rule with no implementation and no refusal is the failure
  this cycle exists to find.** It is the dormant-rule pattern, and the compiler
  found it three times.
