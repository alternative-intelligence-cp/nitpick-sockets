# `src/stream/` — connection-oriented sockets

`TcpListener`/`TcpStream`/`UnixListener`/`UnixStream` and the seqpacket pair:
connect with its full `EINPROGRESS` protocol, accept, half-close, and the
prelude's `Reader`/`Writer` traits. Governed by
`../../meta/specs/STREAM_MODEL.md`. Built in cycles 0.3 and 0.4.
