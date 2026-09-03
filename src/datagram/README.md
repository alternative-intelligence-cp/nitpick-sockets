# `src/datagram/` — message-oriented sockets

`UdpSocket` and `UnixDatagram`: truncation reported through `MSG_TRUNC` and
never swallowed, connected and unconnected forms, broadcast, multicast, and
`IP_PKTINFO`. Governed by `../../meta/specs/DATAGRAM_MODEL.md`. Built in cycle
0.6.
