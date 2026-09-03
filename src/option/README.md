# `src/option/` — typed socket options

One function per option, each taking the type that option actually is. The
generic `setsockopt` lives in `raw.npk`, is not re-exported, and is called by
the typed wrappers and by nothing else. Governed by
`../../meta/specs/OPTION_MODEL.md`. Built in cycles 0.2 (the three pre-bind
options) and 0.7 (the rest).
