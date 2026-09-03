# Cycle 0.7 — Options

**`src/option/`: the typed surface completed, and `raw.npk` confined.**

## Decisions in

`SK-026`. Settled.

**Open questions to settle:** `O-P1` (the QoS options — recommendation: out),
`O-P2` (how the builder reports an option failure).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.7.0 | **`raw.npk` and the confinement** | `check_no_raw_setsockopt` live and seen to fail |
| 0.7.1 | **The stream options** — `TCP_NODELAY`, keepalive and its three parameters | a keepalive that actually detects a dead peer |
| 0.7.2 | **The buffer and error options** — `SO_RCVBUF`/`SO_SNDBUF`, `SO_ERROR` | the doubling documented and asserted |
| 0.7.3 | **The builder's error shape** — `O-P2` | an option failure reported with the option's name |
| 0.7.4 | **Close** | `done/0.7/`, `0.8.0.md` written |

## Checklist

### 0.7.0 — confinement
- [ ] `src/option/raw.npk` holding the only `setsockopt`/`getsockopt` calls
- [ ] **not re-exported by `src/lib.npk`** — a consumer cannot reach it
- [ ] `check_no_raw_setsockopt` live, with the 0.0.3 self-check case un-pended
- [ ] every typed wrapper's level is a constant **inside** the wrapper and never
      a parameter (P-10)

### 0.7.1 — the stream options
- [ ] `nodelay(bool)` and `get_nodelay()`
- [ ] `O-T1`'s measurement re-confirmed here if 0.3 deferred it, and the default
      recorded
- [ ] `keepalive(bool)`, and **`keepalive_params(Keepalive{idle_s, interval_s,
      count})`** setting `TCP_KEEPIDLE`/`TCP_KEEPINTVL`/`TCP_KEEPCNT` (4/5/6)
- [ ] the documentation on `keepalive(bool)` **pointing at the parameters
      form**, because the kernel's default idle is two hours and a keepalive
      that first probes then is useless (P-6)
- [ ] a test that sets a 1-second idle and detects a peer killed with `SIGKILL`

### 0.7.2 — buffers and errors
- [ ] `recv_buf(int32)` / `send_buf(int32)` on the builder, with getters
- [ ] **the doubling asserted**: set 8192, read back 16384, and the wrapper does
      **not** halve it (P-3)
- [ ] the `net.core.rmem_max` clamp documented, and a test that a large set
      succeeds and clamps rather than failing (P-4)
- [ ] `sock.get_error()` for `SO_ERROR`, documented as **destructive** (P-8)
- [ ] `SO_LINGER` with timeout zero only (RST on close); the nonzero form
      absent, with the reason in the documentation (T-25)

### 0.7.3 — the builder's error shape
- [ ] `O-P2` decided and recorded
- [ ] the builder carrying the first error, and the terminal
      `bind`/`connect`/`listen` reporting it **with the option's name
      attached** — so the chain stays readable and the diagnosis stays at the
      cause
- [ ] a test that sets an unsupported option and asserts the failure names it

### 0.7.4 — close
- [ ] `O-P1` decided and recorded
- [ ] `OPTION_MODEL.md` §5's absent-options table reconciled against what
      actually shipped — an option that got added silently is exactly what that
      table exists to prevent
- [ ] findings written; `0.8.0.md` written; archived

## Gate

`check_no_raw_setsockopt` green and seen to fail; the `SO_RCVBUF` doubling
asserted; and a keepalive that detects a dead peer inside a test's patience.

## Watch for

- **`SO_RCVBUF` reporting double is correct behaviour**, and the wrapper must
  not "fix" it by halving — that would be inventing a number the kernel did not
  report. The getter exists precisely so a caller can see what happened.
- **An option added without a decision is the thing this cycle exists to
  prevent.** `OPTION_MODEL.md` §5 lists what was considered and left out; adding
  one means adding a row to `DECISIONS.md` saying which failure mode the
  wrapper's type prevents.
