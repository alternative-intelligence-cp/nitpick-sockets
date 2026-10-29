# Design decisions

Every settled design decision for `nsockets`, with the reasoning, the
alternatives that were considered, and the date. **This is the file to read when
something in the specifications looks unusual**, because it is recorded why.

Referenced as `SK-nnn` from the specifications. `D-nnn` in those documents
refers to the **compiler's** `meta/specs/DECISIONS.md`; those are language
decisions and are not ours to amend.

**Rule: a settled decision's text is never rewritten.** A decision that turns
out to be wrong is superseded by a new one that says so and says why; the old
text stays, dated, because it records what was true when it was made. This is
the compiler's D-085/D-202 pattern.

---

## Foundations

### SK-001 — the library is `nsockets`; the repository is `nitpick-sockets`
**2026-09-03.** The module prefix, every public symbol's prefix, and the
eventual package name are `nsockets`, matching the ecosystem's `n`-prefix
convention (`nfs`, `nproc`, `nio`, `nvec`, `nsys`, `ncolor`) and the name the
project's author gave it in `.internal/idea.txt`. The repository keeps the
longer name because a repository name is a search term.

### SK-002 — the specifications are the authority
**2026-09-03.** Code that disagrees with `meta/specs/` is a defect in the code.
A specification that is wrong is amended by a decision recorded here, never by
editing the text and moving on. The compiler's own cycle notes record the same
finding repeatedly — the compiler and the thing that describes it have to be
diffed, because reading either alone never reveals the gap — and
`TESTING.md` §5's checks are that diff, applied here.

### SK-003 — the full BSD socket surface; DNS and TLS are out
**2026-09-03, settling the reading of `.internal/idea.txt`.** The idea file
says "unix sockets library"; the project's author settled that this means the
full BSD surface: `AF_UNIX` plus TCP and UDP over IPv4 and IPv6, addressing,
`bind`/`listen`/`accept`/`connect`, socket options, `SCM_RIGHTS`, and every
wait through the reactor.

*Reasoning:* "production grade" and the archived consumers point the same way —
`nhttp`, `nwebsocket` and `ndns` each needed IP sockets, and the archived
`nsocket` (142 lines of untyped `int64` wrappers) is what they had. The narrow
reading would have produced a library nothing network-facing could be built on.

*Out, by name rather than by implication:* DNS (`SK-024`) and TLS (`SK-025`).

*Alternatives:* `AF_UNIX` only — rejected above; full surface plus a resolver —
rejected as `SK-024`.

### SK-004 — `harness/` builds and tests `nsockets` until `npkg` can
**2026-09-03.** Measured at the compiler's 1.5.0: `npkg build` is the
compiler's own bootstrap ladder with no generic-project path, and
`[dependencies]` is parsed but the loader's dependency-root list is created
empty and `rootlist_add` is called from nowhere. A Python harness drives
`npkc`, `llc` and `ld.lld` directly, mirroring `bootstrap/harness/`'s
relationship to `npkg`, and retires the same way.

*Not a dependency violation:* zero-dependency governs the artifact, not the
workbench — the compiler's `ORCHESTRATION.md` §6 says so in as many words.

### SK-005 — `nsockets` declares its own storage primitives
**2026-09-03.** `Vec<T>`, `Bytes` and `limits.npk` live in `src/core/` and are
ours. The compiler's `List<T>` is a compiler internal whose own header says it
exists for the compiler's tables, and reaching into another project's `src/`
couples this library's correctness to a file that is not a published interface.
`Vec<T>` is `List<T>`'s shape, deliberately, because that shape is right and
has been exercised across twenty-two families.

### SK-006 — no dependencies, and `[dependencies]` stays empty
**2026-09-03.** The language and its prelude, and nothing else. Including, by
name: **not the compiler's `lib/nbridge.npk`**, which is the best `SCM_RIGHTS`
oracle in the tree and is still not a dependency — it is compiler-internal, it
is scheduled to move to an `nlibc` sibling, and it declares Bridge-specific
errors that REACH-002 would land in every consumer's `failsafe`. `nsockets`
reads it and writes its own. Also not `lib/nsys.npk`, and not a sibling
library.

### SK-007 — Linux on x86-64 only, at 1.0
**2026-09-03.** The syscall numbers are architecture-specific and the structure
layouts are not, so `aarch64` Linux needs a different `src/sys/` table and
nothing else — the first port to consider, and a small one. A BSD port is a
different `sockaddr` (with an `sa_len` byte), `SO_NOSIGPIPE` instead of
`MSG_NOSIGNAL`, and no `SCM_CREDENTIALS`; that is a port with real design
content and it gets its own decision rather than a `#cfg`.

---

## The socket

### SK-010 — typestate: `Listener`, `Stream` and `Datagram` are different types
**2026-09-03.** There is no `Socket` value with a state field. `accept` on
something that never listened, `send` on something that never connected, and
`listen` on a datagram socket are **unspellable** rather than runtime errors.

*Reasoning:* this is D-072's argument applied unchanged. The compiler rejected a
channel with an `int32` mode field selecting behaviour at every operation — "the
mode-field pattern" — and a `Socket` with a `state` field is the same shape. The
payoff here is direct and the type is the documentation.

*The one departure*, recorded because it is a departure: a datagram socket is
**one type whether or not it is connected** (`DATAGRAM_MODEL.md` G-1), because
`connect` there sets a default peer, is reversible, does not change what the
socket is, and a caller routinely wants both `send` and `send_to` on the same
value.

*Alternatives:* one `Socket` type with a state enum — rejected above; a
type-parameter typestate (`Socket<Listening>`) — rejected as more machinery
than four struct declarations for the same guarantee.

### SK-011 — every socket is an `OwnedFd`; there is no `close` in the surface
**2026-09-03.** The close *is* the drop (D-185).
`close(release_fd(move s))` is the spelling for a caller that must observe
close's verdict — the move defuses the drop, so no double close is spellable.

*(2026-10-29, cycle 0.0.0: RUN at compiler `2e1cb4a` — `own_fd` on a socket closes it at the block's end; an owner
handed to `release_fd(move(o))` is vacated, so its block's end closes nothing (the compiler's landing 105 drops an
address-taken owner unconditionally, and a moved-out slot's drop is a no-op); `close` on the bare number answers
success, and a second `close` the same error as a witness close of a number never opened (`tests/probe/probe05_ownedfd_drop.npk`).
This decision holds as written.)*

### SK-012 — non-blocking and close-on-exec are set atomically at creation
**2026-09-03.** `SOCK_NONBLOCK | SOCK_CLOEXEC` in the `socket()`,
`socketpair()` and `accept4()` calls. Never `socket()` followed by two `fcntl`
calls.

*Reasoning:* between an `accept` and a follow-up `fcntl(FD_CLOEXEC)` there is a
window in which any `execve` in any thread leaks the descriptor to a child. The
kernel added `accept4` and the `SOCK_CLOEXEC` flag precisely so that window
does not exist, and a library that reintroduces it is making a mistake the
kernel already fixed. `NONBLOCK` is not optional either: D-071 makes every wait
a task suspension, and a blocking descriptor in the reactor parks the thread.

*Consequence:* `accept` (syscall 43) is never called; `accept4` (288) always is.
The one place `fcntl` appears is `sock_adopt` (`SOCKET_MODEL.md` K-9), where a
descriptor arrived from outside and there is nothing atomic to do.

*(2026-10-29, cycle 0.0.0: RUN at compiler `2e1cb4a` — a TCP socket, an IPv6 datagram socket and a `socketpair`, each
created with `SOCK_NONBLOCK | SOCK_CLOEXEC` in the creating call, read back non-blocking and close-on-exec by
`fcntl` with no follow-up call (`tests/probe/probe01_sys_socket.npk`). This decision holds as written.)*

### SK-013 — every send carries `MSG_NOSIGNAL`, without exception
> **SUPERSEDED IN PART by SK-101 (2026-10-29): its stated fact.** At compiler `2e1cb4a` the floor catches
> `SIGPIPE` with a handler that returns (probe 04); the rule stands, with its reason restated there.
**2026-09-03. The library's headline safety rule.**

*The fact it rests on, measured rather than assumed:* **the Nitpick runtime
installs no signal disposition for anything.** A search of `runtime/npkrt.ll`'s
3 400 lines finds no `rt_sigaction` call, so `SIGPIPE`'s default is live and
its default is to **terminate the process**. The compiler's own Bridge records
the consequence in its source: *"MSG_NOSIGNAL always: a plain write to a
socketpair whose peer died raises SIGPIPE, which terminates the runtime by
default — the exact event this architecture exists to prevent"*, and, in the
same file, *"the first EPIPE schedule proved it by taking the whole process
down."*

*So:* every send `nsockets` issues — `sendto`, `sendmsg`, on every family, on
every socket type, on the ancillary path as well as the ordinary one — passes
`MSG_NOSIGNAL` (`16384`). The failure then arrives as `EPIPE` (`-32`) in
`Result.err`.

*The corollary that will be broken by accident:* this library **does not use
the runtime floor's `write`** on a socket, and neither may an impl of the
prelude's `Writer` trait over one. The floor's `write` is `write(2)`, which
raises `SIGPIPE` on a socket exactly as it does in C. `impl:ByteWriter:Writer`
in the prelude *does* use it, and looks like the thing to copy, because it
writes to a file where the hazard does not exist. The two impls cannot share a
body.

*Alternatives:* ignoring `SIGPIPE` process-wide at library initialisation —
rejected because process-wide signal state is not a library's to change and
because a library that silently alters a program's signal disposition is a
library that breaks somebody's `SIGPIPE`-based pipeline shutdown.
`SO_NOSIGPIPE` — does not exist on Linux.

*Enforced mechanically*: `check_msg_nosignal` greps every `sendto`/`sendmsg`
call site in `src/`, with a whitelist of zero (`TESTING.md` V-11), because a
rule about every call site is a rule that will be broken by the twentieth one.

### SK-014 — connect's `EINPROGRESS` protocol, including the `SO_ERROR` read
**2026-09-03.** On a non-blocking socket, `connect` returning `EINPROGRESS`
means the handshake is running; the socket becomes **writable** on both success
and failure, so writability is not the answer. The library waits for
`EPOLLOUT`, then reads `getsockopt(SOL_SOCKET, SO_ERROR)` **exactly once**, and
a non-zero value is failed with that errno forwarded verbatim.

*Reasoning:* a library that treats writability as success reports a connected
socket for a refused connection, which is the single most common bug in
hand-written non-blocking connect code. Reading `SO_ERROR` twice is the second
most common — the read clears it, so the second returns 0 and reports success.

*Also settled here:* `EINTR` during connect does **not** mean re-call
`connect` — the handshake continues, and a re-call returns `EALREADY`, on which
a naive retry loop spins forever. `EAGAIN` on `AF_UNIX` (a full backlog) *is*
the one retryable case, and it is the only place the two families differ.

### SK-015 — the error budget is four
**2026-09-03.** `ESockAddr`, `ESockState`, `ESockCapacity`, `ESockProtocol`.

*Reasoning:* REACH-002 makes every `error:` that can reach `failsafe` a named
arm every consuming program's `failsafe` must carry, and forgetting one is a
compile error. Four rather than forty because **kernel errnos are forwarded
verbatim** (`SAFETY.md` S-6): `ECONNREFUSED`, `EADDRINUSE`, `EPIPE`,
`ETIMEDOUT`, `EMFILE` and the rest of the socket error space are the kernel's
words, they reach the caller unchanged, and a forwarded errno is a dynamic
operand that costs no arm. End of stream is the prelude's existing `IoEof`.

*Four is a ceiling*, and a fifth is a major version (`SK-034`).

*Alternatives:* one identity with a detail field, as a parser would have —
rejected because these four genuinely differ to a *shutdown handler*: a
malformed address is a programming error, a capacity failure is a tuning
problem, and a protocol violation on an ancillary channel is a security event.
Mapping every errno to an identity — rejected as forty arms per consumer.

### SK-016 — every kernel layout is measured, and asserted by a running program
**2026-09-03.** Structure sizes, field offsets, syscall numbers and constant
values in the specifications were measured on the target platform on
2026-09-03 and are re-asserted by cycle 0.0's probes.

*Reasoning:* the tui library's `TERMINAL_MODEL.md` D-7 records the shape of
this class of bug — the kernel's `termios` is 36 bytes and glibc's is 60, and a
library that talks to the kernel while reading glibc's headers is wrong by 24
bytes. The socket equivalents are `sockaddr_un` (110, not 128) and `cmsghdr`'s
`CMSG_LEN` versus `CMSG_SPACE`. A comment stating a size is a comment; a
program that round-trips it through the kernel is a measurement.

*(2026-10-29, cycle 0.0.0, SK-102: the running programs exist — `sockaddr_in` 16, `sockaddr_in6` 28,
`sockaddr_un` 110 and `sockaddr_storage` 128 laid out as Nitpick structs and round-tripped through `bind` and
`getsockname` with a sentinel past each end (probe 02), `msghdr` 56, `iovec` 16, `cmsghdr` 16 and `ucred` 12 through
`sendmsg` and `recvmsg` (probe 03), and the address types' own sizes (probe 12) — every one as the specifications
state it.)*

### SK-017 — byte-order conversion lives in one module
**2026-09-03.** `src/addr/order.npk`, four functions, and every port, every
IPv4 word and every `sin6_flowinfo` goes through one of them. Nothing else in
the library shifts or masks an address field.

*Reasoning:* `sockaddr_in6` has `sin6_flowinfo` in **network** order and
`sin6_scope_id` in **host** order, adjacent, same width. That is the ABI, and a
"swap everything on the way out" idiom gets it wrong. One module with a
per-field table is auditable; it is also the single file a big-endian port
would change.

### SK-018 — a partial write is not an error, and `write_all` reports its count
**2026-09-03.** `write` returns what the kernel took. `stream_write_all` is in
the library so no consumer writes it again, and **on a deadline it reports how
many bytes it had delivered** — as a companion field on the error, not as a new
error identity — because a caller that has sent half a message needs to know
that and a bare `DeadlineExceeded` leaves the protocol state unknowable.

### SK-019 — half-close is explicit and is not the same as drop
**2026-09-03.** `shutdown(SHUT_WR)` sends FIN and leaves the socket readable;
drop closes the descriptor. Half-close is how a request/response protocol over
a stream says "I have sent everything", and a library without it forces the
caller to close and lose the reply. `shutdown` additionally affects **every**
descriptor for the connection, where close affects one — an asymmetry stated
because it surprises people.

### SK-020 — the library does not unlink a bound Unix socket path
**2026-09-03.** `bind` on a pathname `AF_UNIX` socket creates a filesystem
entry that `close` does not remove, and `nsockets` does not remove it either.

*Reasoning:* the path is the caller's, chosen by the caller, possibly shared,
possibly a symlink, possibly in a directory the caller does not control. A
library that removes files it did not create is a library nobody can reason
about. An unlink at drop would also run at scope exit — where a restarting
server wants the socket to still exist for a moment — and would *not* run on a
trap, so it would work exactly on the paths where the caller was going to clean
up anyway.

*What is provided instead:* `unix_unlink(path)`, and
`unix_bind_replacing(path)` for the restart case, named so the destructive act
is visible at the call site. And the recommendation that a Unix socket use the
**abstract namespace**, which has no filesystem entry to leave behind at all.

*This is the one thing this library asks an application to clean up after it*,
and it is stated in `SAFETY.md` §7 rather than left in a footnote.

### SK-021 — datagram truncation is reported, never swallowed
**2026-09-03.** Every datagram receive passes `MSG_TRUNC` (`32`), which makes
the kernel return the datagram's **true** length while copying only what fits;
a returned length above the buffer's capacity is `ESockCapacity` with the true
length attached.

*Reasoning:* a plain `recvfrom` into a small buffer discards the remainder and
returns the buffer's size, so a caller that asked for 512 and got 512 cannot
tell a 512-byte datagram from a 4096-byte one. That is the classic UDP bug and
the kernel already provides the flag that closes it.

*Note:* `MSG_TRUNC` means something entirely different on a **stream** socket
(discard the data), and this library never passes it on one.

### SK-022 — every address type is a plain value with no owning field
**2026-09-03.** No `string`, no `buffer`, no `Path`. `UnixAddr` inlines its
108 bytes.

*Reasoning:* an owning field would make every address move-only (TYPE-046) and
refuse it as a channel element (TYPE-057), so a `Vec<SocketAddr>` would be a
container of moves and an address could not be sent to another task. Addresses
are small, fixed-size and copied constantly; inlining 108 bytes is the cheap
answer to all of it.

*(2026-10-29, cycle 0.0.0, SK-102: measured at compiler `2e1cb4a` — 4 096 `SocketAddr` values in a `wild` array,
filled, read back through a `pick`, copied whole by value and read through a generic `T: Copy` function, with every
address type derived `Copy` (probe 12). This decision holds as written.)*

### SK-023 — `UnixAddr` is not a `Path`
**2026-09-03.** The prelude's `Path` (D-051, D-054) requires an **absolute**
path — `path_parse` fails `BadPath` on anything whose first byte is not `/` —
and an abstract-namespace address is not a filesystem object at all. Unix
socket addresses are routinely relative and routinely abstract, so `Path` is
the wrong type twice over. `unix_addr_from_path(Path)` exists for callers who
genuinely have an absolute path and want the check.

*(2026-10-29, cycle 0.0.0, SK-103: the byte slice `unix_addr_path` takes is the read-only view, `fixed uint8[]`,
so a caller holding a `string` passes `string_bytes(s)` — `ADDRESS_MODEL.md` A-14 says so; this decision's choice of a
byte slice over `Path` holds as written.)*

### SK-024 — no DNS
**2026-09-03.** No `getaddrinfo`, no `/etc/hosts`, no resolver.

*Reasoning:* a hostname is not an address. Resolving one is a wire protocol
(DNS), a file parser (`/etc/hosts`, `/etc/resolv.conf`, `nsswitch.conf`), a
cache with its own invalidation, and a security surface with its own history —
none of which is a socket. It belongs in a library that can be audited as what
it is, and the archived `ndns` is where that work would start.

*Consequence stated rather than implied:* `socket_addr_parse` takes an address.
A consumer that needs a hostname resolves it and hands over the result.

### SK-025 — no TLS
**2026-09-03.** For the same shape of reason and more forcefully: a TLS
implementation is a cryptographic artifact whose correctness argument is
entirely different from a socket library's, it wants its own audit and its own
threat model, and bundling one would put this library's name on a guarantee it
cannot make. `TcpStream` implements `Reader`/`Writer` (`SK-027`), which is
exactly the seam a TLS layer wraps.

### SK-026 — socket options are typed, one function per option
**2026-09-03.** There is no `setsockopt` in the public surface; the generic
form is confined to `src/option/raw.npk` and is not re-exported.

*Reasoning:* the generic form is a `void*` and a length, and every mistake it
permits is one this library exists to prevent — a `bool` where the kernel wants
a four-byte `int`, the wrong level for a name, `SO_LINGER`'s eight-byte
structure passed as an integer, and the fact that `SO_RCVBUF` reports back
double what was set. None of them is a compile error in C; all are unspellable
here.

*Cost accepted:* a function per option, and a decision per option — which is
the point. `OPTION_MODEL.md` §5 records the ones considered and left out, so an
absent option is a decision rather than an oversight.

### SK-027 — `TcpStream` and `UnixStream` implement the prelude's `Reader`/`Writer`
**2026-09-03.** Unchanged, with the trait's own `Self->` receiver and `async`
signature.

*Reasoning:* everything already written against those traits — `TextReader`,
`TextWriter`, `LineBufWriter`, a `dyn Writer` sink, anything a consumer wrote
for files — then works over a socket with no change. `IO_REFERENCE.md` §10
records sockets as an open item in the language's own I/O specification; this
is the answer to it, and it is the library's headline interoperability
property.

*The rider, which is `SK-013`'s corollary:* the `Writer` impl uses `sendto`
with `MSG_NOSIGNAL` and **not** the floor's `write`, so it cannot share a body
with the prelude's `ByteWriter` impl.

*(2026-10-29, cycle 0.0.0, SK-103: RUN at compiler `2e1cb4a` — a struct holding an `OwnedFd` implements the
prelude's `Reader` and `Writer` with their exact signatures, `fixed uint8[]:wsrc` and `Writer`'s `flush` among them, its
`write` a `sendto` with `MSG_NOSIGNAL` from the view's own `.ptr` and `.len`, and it runs through a generic bound and
through `dyn Writer` (`tests/probe/probe06_reader_writer.npk`); an implementation that drops the `fixed` is
`NITPICK-TYPE-014` (`refused/probe06b_impl_drops_fixed.npk`). This decision holds as written.)*

### SK-028 — `IPV6_V6ONLY` is set explicitly, never left to the sysctl
**2026-09-03.** Every IPv6 socket sets it to whatever the caller asked for.
The builder's default is **v6only on**.

*Reasoning:* `/proc/sys/net/ipv6/bindv6only` varies by distribution, so a
listener whose address family depends on it behaves differently on two machines
running the same binary. A program that wants dual-stack should say so, and a
program that does not should not get it by accident.

### SK-029 — the headless double is a real `socketpair`
**2026-09-03.** `sock_pair_headless(kind)` returns a connected pair over
`socketpair(AF_UNIX, …)`, with `origin == Headless` recorded and **no
behavioural difference**.

*Reasoning:* a `socketpair` is a real kernel socket, so it exercises the real
send and receive paths, the real non-blocking behaviour and the real reactor,
while needing no network, no port and no privilege. That is a much stronger
double than a simulation, and a double whose behaviour differs from the real
thing certifies the wrong code.

### SK-030 — `loopback` and `network` are separate test stages
**2026-09-03.** Loopback and `socketpair` need no route, no DNS, no privilege
and no outside machine, and cover essentially the whole library. The `network`
stage is the small residue that genuinely needs the internet — two tests — and
is skipped **loudly**.

*Reasoning:* a CI failure that means "this machine has no network" trains
people to ignore red, which is the most expensive thing a suite can do.

### SK-031 — the accept loop's error table, and `EMFILE` backs off
**2026-09-03.** `EINTR` and `ECONNABORTED` retry immediately; `EAGAIN` waits on
`EPOLLIN`; `EMFILE`/`ENFILE` are returned to the caller **with the connection
still pending**, and `server/` backs off for a bounded interval before
retrying.

*Reasoning:* `ECONNABORTED` means a peer sent SYN and reset before the accept —
failing the loop on it kills a server because a client pressed Ctrl-C. `EMFILE`
leaves the connection pending, so a naive retry spins at 100% CPU accepting
nothing; a bounded back-off turns a melt into a degradation.

### SK-032 — `SO_REUSEADDR` on by default for listeners; `SO_REUSEPORT` never
**2026-09-03.** Without `SO_REUSEADDR`, a server restarted within the
`TIME_WAIT` window fails `EADDRINUSE` — the most common surprise in socket
programming and almost never what the operator wanted. It does **not** permit
two live listeners; that is `SO_REUSEPORT`, which silently load-balances
between processes and is a deployment decision nobody should get by default.

### SK-033 — there is no restore registry, and its absence is a decision
**2026-09-03.** `ntui` needs a `failsafe`-reachable restore record because a
terminal's state outlives the process. A socket's does not: the kernel reclaims
every descriptor at exit, a listening port is released, and a connected peer
sees a reset. So a trap leaks descriptors and that is **harmless**, stated in
`SAFETY.md` S-19 rather than mitigated with machinery that would buy nothing.

*The one exception is `SK-020`'s Unix socket path*, which does outlive the
process — and the answer there is not to unlink it either.

### SK-034 — adding a public error identity is a MAJOR version
**2026-09-03.** REACH-002 makes a new identity a new mandatory `pick` arm in
every consuming program's `failsafe`, which the compiler enforces — so it is a
source break in every consumer. This is the practical teeth behind `SK-015`'s
budget of four: the budget is not a style guide, it is the thing that keeps the
major version from moving.

### SK-035 — the server model is accept-then-spawn, because it is the only one
**2026-09-03.** Two language rules, measured in the compiler's own source,
decide it between them:

- **An `OwnedFd` is refused as a channel element.**
  `chan_elem_verdict_recorded` (`src/frontend/types.npk`) answers
  `CHAN_ELEM_FD` for `TY_OWNEDFD`, and `type_contains_borrow_recorded` answers
  `true`, so a **struct holding one** is refused transitively. The compiler's
  comment gives the reasoning: *"An OwnedFd — and so every stream holding one —
  is SCOPE-BOUND: the scope that owns it closes it."*
- **An `OwnedFd` may be moved into a spawned task.** `type_holds_pointer`
  (`src/frontend/analysis/escape.npk`) answers **`false`** for `TY_OWNEDFD` —
  *"an OwnedFd is a descriptor NUMBER (D-185)"* — so it does not trip D-004's
  spawn rule. `IO_REFERENCE.md` §6 states it: *"A MOVE into a spawn is legal."*

So a connection can be handed to a task and cannot be put in a queue. A worker
pool pulling connections off a channel — which is what almost every socket
library in every other language does — is **unspellable here**, and correctly
so: it is precisely a structure in which a connection's closing scope is no
longer the scope that accepted it.

*The library builds the shape the language permits and documents why the other
is absent*, so nobody spends a day trying to defeat the checker.

*(2026-10-29, cycle 0.0.0: both rules RUN at compiler `2e1cb4a`, at `-O0` and through `opt -O2` — an `OwnedFd`,
and a struct holding one, are `NITPICK-TYPE-057` at the channel's annotation (`tests/probe/refused/probe09_ownedfd_channel.npk`,
`probe09b_holder_channel.npk`; the struct's diagnostic names the struct, not its field); a task handed one by
`move` sends on it and its drop closes it before the spawner's join (`tests/probe/probe10_ownedfd_spawn.npk`); and a
borrow of one across the spawn is `NITPICK-BORROW-004` (`refused/probe10b_borrow_spawn.npk`). This decision holds
as written.)*

### SK-036 — address parsing is strict, `inet_pton`-shaped and not `inet_aton`-shaped
**2026-09-03.** `ipv4_parse` accepts exactly four decimal octets, 0–255, with
**no leading zeros**, and refuses `127.1`, `0177.0.0.1`, `0x7f.0.0.1` and
whitespace.

*Reasoning:* `inet_aton` treats a leading zero as octal, so `010.0.0.1` is
`8.0.0.1`. A parser that accepts more than one spelling of an address is a
parser that lets a validator and a connector disagree, and that difference has
produced CVEs in more than one language's standard library. The refusal table
is a **test corpus**, not a comment (`TESTING.md` V-9), because an untested
security claim is a comment.

*(2026-10-29, cycle 0.0's research gate: "`inet_pton`-shaped" is glibc's `inet_pton`, measured at 2.39, and RFC
3986 §3.2.2's `dec-octet` grammar, which both refuse a leading zero at any length. That is deliberately stricter than
POSIX.1-2024, whose `inet_pton` allows a leading zero within three digits (Austin Group Defect 1573), so the refusal
table gains `010.0.0.1` and `1.2.3.04`, the spellings where this decision and POSIX part (`ADDRESS_MODEL.md` A-19),
and A-20 reads its dotted-quad tail by the same rules. The decision holds as written.)*

### SK-037 — IPv4-mapped IPv6 addresses are never silently converted
**2026-09-03.** A dual-stack listener reports an IPv4 peer as
`SocketAddr.V6` holding `::ffff:a.b.c.d`, exactly as the kernel reported it.
`ipv6_to_v4_mapped(a)` is the explicit conversion and returns `Ipv4Addr?`.

*Reasoning:* an application comparing a peer address against an allowlist must
know which representation it is comparing. The bugs in this area are all of the
form "the check saw `::ffff:127.0.0.1` and the allowlist held `127.0.0.1`", and
an automatic conversion is what makes them invisible.

---

# The second batch — ratified 2026-09-03

### SK-100 — the version policy is `nitpick-tui`'s T-103, adopted verbatim
**2026-09-03, settling Q-3.** `0.x` until the compiler reaches its own 1.0 and
the API has survived cycle 0.9's application; semantic versioning thereafter;
and **adding a public error identity is a major version**, which SK-034 already
records for this library.

*Adopted verbatim rather than restated*, and that is the point of the decision:
the error-identity rule is a property of the *language* — REACH-002 makes a new
identity a compiler-enforced source break in every consumer — so every library
in this ecosystem has the same rule, and five libraries each phrasing it
slightly differently would be five chances for one of them to phrase it wrong.

Where a future library needs a different policy, it says so against this one.

---

# The third batch — cycle 0.0's probes, 2026-10-29 at compiler `2e1cb4a`

Proposed by cycle 0.0's plan, each in the step whose measurement forces it, and numbered at the libraries' seat's
review. Each records the alternatives it declines and its reversal.

### SK-101 — the floor catches `SIGPIPE`; every send still carries `MSG_NOSIGNAL`, and nothing dies by a signal
**2026-10-29, cycle 0.0.0 step 1, probe 04. Supersedes `SK-013` in part: its stated fact. The rule stands.**

*What was measured* (`tests/probe/probe04_sigpipe.npk`, at compiler `c9baa9e`, at `-O0` and through `opt -O2`): the
floor's runtime installs a handler for `SIGPIPE` at startup — `rt_sigaction(SIGPIPE, NULL, &prior)` reads a handler
that is neither `SIG_DFL` nor `SIG_IGN`, with the flags `SA_RESTORER | SA_ONSTACK | SA_RESTART` that
`runtime/npkrt.ll`'s `npk_fault_arm` installs (the compiler's DEF-68) — and that handler returns. A `sendto` with a
flags word of 0 to a socketpair whose peer is closed answers an error and the program lives; the same send with
`MSG_NOSIGNAL`, the floor's `write` on the socket, and a `write` to a pipe whose reader is closed answer the same
error, the pipe's `EPIPE`; and under the default disposition, set by the probe itself, the `MSG_NOSIGNAL` send
answers `EPIPE` again, where the same send with no flags dies by signal 13, and so does the floor's `write` in its
place (two mutants of the probe, each a shell's status 141). `SK-013`'s stated fact — the runtime installs no signal
disposition, so `SIGPIPE`'s default is live — was true of the runtime it was read in and is false here: `npkrt.ll`
has no `rt_sigaction` at the compiler's `3d15ac9`, and its `SIGPIPE` handler came with the compiler's `b7244d2f`
(1.5.8 step 3, DEF-68's fix), whose parent has none; it is there at `c3bdae2` and at the pin.

*(Re-measured at `2e1cb4a`, 2026-10-23, in the adoption: the same.)*

*So:* every send `nsockets` issues still carries `MSG_NOSIGNAL`, and the reason is the default disposition rather
than the runtime: on the floor's runtime a send to a dead peer answers `EPIPE` either way, but a process's
disposition is the default whenever its host restores it or its runtime stops overriding it, and `MSG_NOSIGNAL`
makes this library's sends safe under every one of those, at the cost of one flag. `SAFETY.md` S-2 stands, its
reason restated: the floor's `write` on a socket answers `EPIPE` under the handler and kills under the default, and
has no flags word for `MSG_NOSIGNAL`. S-3 stands: the library installs no handler and blocks no signal — the
runtime's handler is the runtime's. `check_msg_nosignal` and `check_no_floor_write` stand as planned.

*And the marker:* `// expect-signal: N` (`TESTING.md` V-6) is retired. Its one consumer was the leg of probe 04 that
was to die by signal 13, and at this pin nothing in the suite is expected to die by a signal. `TESTING.md` V-5's test
is probe 04's legs.

*Alternatives declined:* **keep `SK-013`'s premise and read the probe as an anomaly** — the probe exists to replace a
reading with a measurement; **drop `MSG_NOSIGNAL` as belt-and-braces** — it costs one flag per send, and the
floor's handler is not this library's to rely on; **keep `// expect-signal:` with a probe that restores the default
disposition and dies on purpose** — it would test the kernel's default action, not this library or this language,
and a marker with no subject of its own is a marker nobody keeps working.

*Reversal:* if a later runtime stops installing the handler, probe 04 exits 11 in its first leg, which reads the
disposition as `SIG_DFL`, before any send — red on that pin's first run, as the probe started under `SIG_DFL` exits
11 at this one (a third mutant); there a send with no flags dies by signal 13, as the no-flags mutant does here; and
a decision restores `SK-013`'s premise and the marker, with probe 04 its consumer.

### SK-102 — the kernel layouts and the address types at their measured sizes; the names the pin refuses are not used
**2026-10-29, cycle 0.0.0 step 2, probes 01, 02, 03 and 12.**

*What was measured* at compiler `c9baa9e`, at `-O0` and through `opt -O2`: the kernel structures, declared as
Nitpick structs with natural alignment, are the kernel's sizes and round-trip through it — `sockaddr_in` 16,
`sockaddr_in6` 28, `sockaddr_un` 110 (an `AF_UNIX` socket autobinds into the abstract namespace, 2 + 1 + 5 bytes),
`sockaddr_storage` 128 (probe 02); `msghdr` 56, `iovec` 16, `cmsghdr` 16, `ucred` 12 (probe 03). The address types
of `ADDRESS_MODEL.md` §1, each derived `Copy`, measure `Ipv4Addr` 4 and `Ipv6Addr` 20 as stated there, and — stated
nowhere until now — `IpAddr` 24, `SocketAddrV4` 6, `SocketAddrV6` 28, `SocketAddr` 32 and `UnixAddr` 110: a
payload enum is an `int32` tag and then its widest payload (probe 12). And three of `ucred`'s field names, `pid`,
`uid` and `gid`, are keywords at the pin — landing 113 refuses a keyword declared as a name of any kind,
`NITPICK-PARSE-001` — as are `old`, `result`, `release`, `range` and the rest `specs/BUILD.md` §7 now lists; a name
the prelude declares, such as `O_CLOEXEC`, is `NITPICK-RESOLVE-001` when declared again.

*(Re-measured at `2e1cb4a`, 2026-10-23, in the adoption: the same.)*

*So:* `ADDRESS_MODEL.md` §1 states each address type's measured size and derives `Copy` on each; probe 02 and probe
12, not probe 03, are the programs that assert them (its first sentence said probe 03); the library's `Ucred` names
its fields `cpid`, `cuid` and `cgid`; and `specs/BUILD.md` §7 is the measured table, `channel` struck from it (it is
not a keyword).

*Alternatives declined:* **sum the sizes from field widths** — `PLAYBOOK.md` §2's rule, and the enum's tag is
exactly what a sum leaves out; **keep the kernel's C names for `ucred` with a prefix applied only where the compiler
objects** — a public type whose fields are named by exception is a type every reader re-learns; **state no sizes in
the specification** — a `Vec<SocketAddr>`'s memory is a sum a consumer does, and probe 12 asserts each.

*Reversal:* none for the sizes, which are measurements — a later pin that moves one reddens probe 02, 03 or 12 on its
first run, and the specification follows. If a later compiler frees `pid`, `uid` or `gid` as names, the fields keep
the names they have, since renaming a public field is a major version.

### SK-103 — every slot a reader's bytes reach is the read-only view; a writer's is plain
**2026-10-29, cycle 0.0.0 step 3, probes 06, 06b, 14 and 14b. The pin audit's SL-1 and SL-4; SL-6 beside them.**

*What was measured* at compiler `c9baa9e`, at `-O0` and through `opt -O2`: a decoder over `fixed uint8[]:src` takes
`string_bytes` of a `string` (the read-only view since the compiler's landing 103, D-351), a plain view of a local
array, and a range of either (probe 14); the same decoder over a plain `uint8[]:src` refuses `string_bytes(s)`,
`NITPICK-TYPE-007` at the argument (probe 14b). An implementation of the prelude's `Writer` takes `fixed
uint8[]:wsrc` exactly as the trait does — dropping the `fixed` is `NITPICK-TYPE-014` (probe 06b) — and its `write`
hands the view's own `.ptr` and `.len` to `sendto` (probe 06). A `Reader`'s `dest` is a plain `uint8[]`: it writes.

*(Re-measured at `2e1cb4a`, 2026-10-23, in the adoption: the same.)*

*So:* every parameter this library declares over bytes it only reads is `fixed uint8[]` — `addr_decode`,
`unix_decode`, `unix_addr_path`, every parser (A-5, A-14, A-22), every kernel-structure accessor (`VERIFICATION.md`
Z-2's `sin_port_at`), and cycle 0.1's checklist, with a test that `socket_addr_parse(string_bytes(s))` compiles —
and every parameter it writes stays a plain `uint8[]`: `addr_encode`'s and `unix_encode`'s `dest`, a receive's
`dest`. The stream implementations' checklist (cycle 0.3) names `fixed uint8[]:wsrc` and `flush`. And the bare word
`fixed` is the keyword's: a size is "constant-size", never "fixed" (SL-6: eleven lines in nine places, the pin
audit's ten less `SK-022`'s settled text).

*Alternatives declined:* **keep plain `uint8[]` and let a caller copy a `string` into a buffer first** — every call
from a `string` would allocate, the cost A-22 exists to avoid; **a `string` overload beside each parser** — two
entry points per parser where one view serves both callers; **plain `uint8[]` everywhere and a `fixed` copy at the
edge** — a copy per call to undo a type the compiler hands out.

*Reversal:* if a later compiler lets `string_bytes` fill a plain slot, nothing need move: a `fixed` parameter takes a
plain view too (probe 14). If it removes the read-only view, the parameters return to `uint8[]` by a later decision,
probe 14 reddening first.
