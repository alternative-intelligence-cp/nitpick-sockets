# Cycle 0.4 — Unix domain

**`UnixListener`, `UnixStream`, the seqpacket pair, pathname and abstract
binding, and peer credentials.** Everything `AF_UNIX` except descriptor
passing, which is 0.5.

## Decisions in

`SK-020`, `SK-023`. Settled. The stream machinery is 0.3's, reused rather than
rewritten.

**Open questions to settle:** none. `O-K2` (`SOCK_SEQPACKET` beyond `AF_UNIX`)
is already recommended out.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.4.0 | **`UnixStream` and `UnixListener`** | the 0.3 machinery over `AF_UNIX`, with no second implementation |
| 0.4.1 | **Binding** — pathname, abstract, `unix_unlink`, `unix_bind_replacing` | the filesystem side effect visible and the abstract form recommended |
| 0.4.2 | **`SOCK_SEQPACKET`** | a message received whole, and one too large reported |
| 0.4.3 | **Peer credentials** — `SO_PEERCRED` | a connecting process's uid asserted |
| 0.4.4 | **Close** | `done/0.4/`, `0.5.0.md` written |

## Checklist

### 0.4.0 — the stream types
- [ ] `UnixStream` / `UnixListener` over the **same** connect, accept, read,
      write and half-close bodies as 0.3 — a tree check that the two families
      share their implementation rather than duplicating it
- [ ] `impl:UnixStream:Reader` / `Writer`, with `MSG_NOSIGNAL` (a Unix stream
      raises `SIGPIPE` exactly as a TCP one does)
- [ ] connect's `AF_UNIX` differences: immediate success is the norm, and
      `EAGAIN` means a full backlog and **is** retryable (T-8.6)
- [ ] `// stress: 40` on a connect/accept round trip

### 0.4.1 — binding
- [ ] pathname binding, with the encoded `addrlen` from 0.1.2
- [ ] **abstract binding, and it is the recommended form** — no filesystem
      entry, nothing to leave behind (K-25)
- [ ] a bound pathname socket leaving a filesystem entry that `close` does not
      remove — **asserted by a test**, because that is the surprising fact
      `SK-020` is about
- [ ] a second bind to the same path failing `EADDRINUSE` even with nothing
      listening
- [ ] `unix_unlink(path)` — `unlink(2)` and nothing more
- [ ] `unix_bind_replacing(path)` — unlink then bind, named so the destructive
      act is visible at the call site
- [ ] **the library does not unlink at drop**, asserted by a test that drops a
      bound socket and finds the path still there (`SK-020`)
- [ ] every test in this cycle uses the abstract namespace, so nothing is left
      behind by a crash (`specs/TESTING.md` V-4)

### 0.4.2 — `SOCK_SEQPACKET`
- [ ] a connected seqpacket pair, message framing preserved
- [ ] a message larger than the receive buffer **reported, not truncated
      silently** — `MSG_TRUNC` applied as `DATAGRAM_MODEL.md` G-8 requires
- [ ] **no `Reader`/`Writer` impl** (T-27), with a comment saying why: a partial
      read of a message is meaningless and forcing a message type through a byte
      interface is how framing gets lost
- [ ] two messages sent back to back and received as two, never coalesced

### 0.4.3 — peer credentials
- [ ] `SO_PEERCRED` (17) returning a 12-byte `ucred`, offsets asserted
- [ ] a test that forks a child, connects from it, and asserts the parent sees
      the child's pid and its own uid
- [ ] the documentation distinguishing `SO_PEERCRED` (who connected) from
      `SCM_CREDENTIALS` (who sent this message), which 0.5 adds (N-16)
- [ ] **the "a pid is not a capability" warning** in the `ucred` documentation
      (N-17)

## Gate

An abstract-namespace address whose encoded length is asserted byte for byte;
a bound pathname socket proven to leave its filesystem entry behind; and a
seqpacket message received whole.

## Watch for

- **The abstract-namespace encoding is the classic bug** and 0.1.2 built the
  encoder; this cycle is where it meets the kernel. Two abstract names differing
  only past the intended length must be different addresses, and if they are
  not, the `addrlen` is wrong.
- **`AF_UNIX` connect usually succeeds immediately**, which means the
  `EINPROGRESS` machinery is barely exercised here — and the one case that does
  exercise it, a full backlog, needs a listener that is not accepting. Worth
  constructing deliberately.
- **Do not add a second stream implementation.** The temptation is real because
  the address type differs; the answer is that the address type is a parameter.
