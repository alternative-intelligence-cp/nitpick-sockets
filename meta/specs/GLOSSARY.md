# Glossary

One word per concept, one concept per word. Where the socket world uses a word
two ways, this table says which one `nsockets` means.

| Term | Means, in `nsockets` |
|---|---|
| **descriptor** | the kernel's integer. Never "fd" in prose, because `fd` is a type keyword. |
| **`Sock`** | the common primitive: an `OwnedFd` plus its recorded family, kind and shutdown state. |
| **socket** | a `Sock` or one of the typed values holding one. Never the syscall — that is `socket(2)`. |
| **stream** | a connection-oriented socket. Never a byte stream in the `Reader`/`Writer` sense; that is a **byte stream**. |
| **datagram** | a message-oriented socket, and also one message. Disambiguated by "socket" or "message" wherever both readings fit. |
| **peer** | the other end. Never "remote" — a Unix socket has a peer and no remoteness. |
| **address** | a value of `SocketAddr` or `UnixAddr`. Never a hostname (this library has none) and never a pointer. |
| **encode** / **decode** | between an address value and the kernel's `sockaddr` bytes. |
| **`addrlen`** | the length passed to or returned by a syscall. Significant for `AF_UNIX`; never `sizeof(sockaddr_storage)`. |
| **half-close** | `shutdown(SHUT_WR)`. Distinct from **close**, which is the drop. |
| **truncation** | a datagram larger than the buffer it was received into. Always reported, never silent. |
| **ancillary** | control data alongside a message: `SCM_RIGHTS`, `SCM_CREDENTIALS`. |
| **the reactor** | the language's epoll-based readiness mechanism, reached through `io_watch`, `io_ready` and `suspend_io`. |
| **readiness** | what `io_ready` returns: a hint that a retry is worth making. Never a guarantee. |
| **the floor** | the language's runtime, `runtime/npkrt.ll`. |
| **the budget** | the four public error identities (`SAFETY.md` §3), and the rule that there are four. |
| **arm** | one `pick` case in a consuming program's `failsafe`. |
| **forwarded** | an errno returned in `Result.err` exactly as the kernel gave it, costing no arm. |
| **the double** | a `socketpair` with `origin == Headless`. A real kernel socket, not a simulation. |
| **loopback** | `127.0.0.1` / `[::1]`. Needs no network; distinct from **network**, which needs an outside host. |

## Words deliberately not used

| Not used | Because |
|---|---|
| "fd" in prose | `fd` is a type keyword; the word is **descriptor** |
| "client" / "server" as types | they are roles, not types. A `TcpStream` is a `TcpStream` whichever end made it |
| "blocking" for a wait | every wait is a **task suspension**; nothing in this library blocks a thread |
| "connection" for a `UdpSocket` | a connected datagram socket has a default peer, not a connection |
| "handle" for a descriptor | `Handle<T>` is the language's arena index |
| "buffer" for a byte slice | `buffer` is a type keyword; a slice is a **slice** and a `Bytes` is a `Bytes` |
| "timeout" for a deadline | the parameter is a `Duration:within` and the failure is `DeadlineExceeded`; `SO_RCVTIMEO` is a different thing and is absent |
| "async" as an adjective for the API | every operation is `async`; saying so adds nothing |
