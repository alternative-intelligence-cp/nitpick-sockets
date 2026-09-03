# `src/server/` — the accept loop

Accept-then-spawn, the bounded live-connection ceiling, the `EMFILE` back-off,
and `poll_set`. Composition rather than mechanism. Governed by
`../../meta/specs/CONCURRENCY_MODEL.md`. Built in cycle 0.8.
