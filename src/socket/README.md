# `src/socket/` — the primitive

`Sock`, the builder, creation with atomic `SOCK_NONBLOCK|SOCK_CLOEXEC`, `bind`,
`listen`, `shutdown`, `sock_adopt`, and the `socketpair` double. The send and
receive path with **`MSG_NOSIGNAL` unconditional** lives here. Governed by
`../../meta/specs/SOCKET_MODEL.md`. Built in cycle 0.2.
