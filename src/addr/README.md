# `src/addr/` — addresses

`Ipv4Addr` … `UnixAddr`, the kernel `sockaddr` encodings byte by byte,
`hton`/`ntoh` in one module, the strict parsers and the RFC 5952 formatters.
Pure computation: no descriptors, no kernel. Declares **`ESockAddr` only**, so
a program that parses addresses and never opens a socket owes one `failsafe`
arm. Governed by `../../meta/specs/ADDRESS_MODEL.md`. Built in cycle 0.1.
