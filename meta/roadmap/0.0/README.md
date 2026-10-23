# Cycle 0.0 — Foundations

**The probes, the harness, and `src/core/`.** Nothing in this cycle opens a socket in anger. What it produces is the
ability to find out whether the rest of the plan is buildable, and the machinery every later cycle is tested by.

**Re-derived at compiler `c9baa9e` by the Team seat's planners — T7 for 0.0.0 and T7b for 0.0.1 (2026-10-18), T7c2
for 0.0.2 (2026-10-21), T7c3 for 0.0.3 (2026-10-22) —** one subcycle file at a time, each committed and pushed as it reaches the pin; 0.0.0 and
0.0.1 corrected by fix round 1 (2026-10-21) where the first plan verification found them wrong, and 0.0.1's steps 4
and 5 by 0.0.2's planner, so that each says what CI pins at its step. The six files were written at the repository's setup (2026-09-03), against
the compiler's cycle 1.5 and LLVM 20.1.2; each is re-measured at the pin, with what the audits found owed carried into
the step that owes it (the owed-items table below). **`c9baa9e` was the libraries' one re-pin of 2026-10-16**,
landing 118's commit, by the author's word on the workbench's question 32 (2026-10-15 12:04:21), committed at the
workbench's `4540f20`; this cycle was planned at it from the start. **The pin is now `2e1cb4a`**, landing 140's commit,
the libraries' next re-pin, by the author's word of 2026-10-22 03:49:41, taken on 2026-10-22 and committed at the
workbench's `4db3f92`; **T7a adopted it here on 2026-10-23, before any subcycle started**, by the landing table below,
row by row, every block of 0.0.0 … 0.0.3 run again at the new pin. No subcycle has started.

| File | At `2e1cb4a` |
|---|---|
| [0.0.0](0.0.0.md) | **yes**, adopted — probes measured, five patches, blocks with filled Expects |
| [0.0.1](0.0.1.md) | **yes**, adopted — the layout, the skeleton, the manifest, CI and the currency table; six patches, blocks with filled Expects |
| [0.0.2](0.0.2.md) | **yes**, adopted — the harness, part 1: the runner, its two scans and their controls, `repro`, three stages, the probes as suites, CI's summary and LLVM by content; three patches, the mutants, blocks with filled Expects |
| [0.0.3](0.0.3.md) | **yes**, adopted — the harness, part 2: the `check` stage and the `parse` sweep, `loopback` and `network`, the self-check beside its controls, nine tree checks and `--only`; two patches, the mutants, blocks with filled Expects |
| [0.0.4](0.0.4.md) | **not yet** — the setup-era text; the pass's continuation re-derives it, at `2e1cb4a` |
| [0.0.5](0.0.5.md) | **not yet** — as 0.0.4; its execution, the close, is the libraries' seat's |

A file marked *not yet* is a target, not a plan: its steps are re-derived at the pin before anything is dispatched from
it, and where it disagrees with the files re-derived before it, those files and the tables below govern.

## Why this shape

Two of the compiler project's most expensive lessons decide this cycle's contents:

- **"A construct that parses is not a construct that works."** Its cycle 0.4 was mostly repair, and every repair dated
  to the cycle that had parsed the construct. **Two of this library's foundations were read out of compiler source
  rather than run**: that `SIGPIPE` is lethal because nothing installs a disposition (`SK-013`), and that an `OwnedFd`
  is refused as a channel element but may be moved into a spawn (`SK-035`). Both are load-bearing for the whole
  design. 0.0.0 runs them — **and at the pin the first reading is false**: the floor catches `SIGPIPE` with a handler
  that returns, so `SK-013`'s rule stands for another reason (@@PD-159@@), while `SK-035` holds as read.
- **"Diagnostics come first, not last — they are how every later cycle is tested."** Here that is the harness. A suite
  written after the code is a suite shaped by the code.

## Decisions in

`SK-001`, `SK-002`, `SK-004`, `SK-005`, `SK-006`, `SK-007`, `SK-013`, `SK-016`, `SK-026`, `SK-035`. All settled.

**And the ones this cycle proposes**, from PD-159 on, in the Team seat's block for this repository, **PD-159 …
PD-178**, which `nitpick-libs_19` confirmed at 18:51:47 on 2026-10-15 — each landing in the subcycle step that first
needs it and numbered at the review (`tools/decisions.txt`, which gains a line as each subcycle's file reaches the pin).
Each is settled with a recommendation and states its reversal; **none is left open for the author.**

| PD | Subcycle | Decides |
|---|---|---|
| @@PD-159@@ | 0.0.0 | the floor catches `SIGPIPE`; every send still carries `MSG_NOSIGNAL`; `// expect-signal:` retired |
| @@PD-160@@ | 0.0.0 | the kernel layouts and the address types at their measured sizes, `Copy` derived; the names the pin refuses not used |
| @@PD-161@@ | 0.0.0 | every slot a reader's bytes reach is `fixed uint8[]`; a writer's is plain |
| @@PD-162@@ | 0.0.0 | an errno is compared only with the prelude's identities or another error; connect by a second `connect`; two accept rows wait on the compiler |
| @@PD-163@@ | 0.0.0 | what a consumer of each module shape owes, measured; the tests' arm codes 111 and 112 |
| @@PD-164@@ | 0.0.1 | the layering is a table of what each module may import; the drawing's two missing arrows added |
| @@PD-165@@ | 0.0.1 | the generic option form lives in `src/option/sockopt.npk`, because `raw` is a keyword |
| @@PD-166@@ | 0.0.1 | the manifest at the pin: LLVM 20.1.8 with the compiler's target rows, and its first three test entries |
| @@PD-167@@ | 0.0.1 | CI runs no third-party action; it pins the compiler by commit, LLVM by version and the runner image by name — LLVM's tarball by content from 0.0.2 (@@PD-172@@) |
| @@PD-168@@ | 0.0.1 | one currency table; the library is security-sensitive, and its three research items gate cycle 0.0's work |
| @@PD-169@@ | 0.0.2 | the build is one module per root, held to the target rows, scanned on both legs, and reproducible from two directories |
| @@PD-170@@ | 0.0.2 | the call-edge scan holds the library to the runtime facets its rules give it, from a table of the whole runtime |
| @@PD-171@@ | 0.0.2 | the runner judges `program`, `compile`/`positive` and `compile`/`negative`, and reads one marker of its own |
| @@PD-172@@ | 0.0.2 | LLVM's release tarball is pinned by content: its size and sha256 from a research digest, checked before it is unpacked |
| @@PD-173@@ | 0.0.3 | the `check` stage and the `parse` sweep are judged by `npkc`; `accept` is struck; `loopback` is never skipped, and `network` is skipped loudly |
| @@PD-174@@ | 0.0.3 | the self-check catches every live case beside its control, before anything judges the library; a filtered run concludes nothing |
| @@PD-175@@ | 0.0.3 | the tree checks read the specifications' tables and the source through one reader; an identity is a module and a name |
| PD-176 … PD-178 | 0.0.4 … 0.0.5 | the continuation's, as each file reaches the pin |

## The pin, and what each landing would move

**The pin is `c9baa9e`**, landings 83 … 118 (the workbench's `.internal/toolchain/c9baa9e/PIN.md`, CARRIES and NOT
CARRIED). This cycle was planned at it, so a landing it carries is measured, not predicted; a landing it does not carry
is named with the place it would move this plan, so that **the next adoption is this list, not a search**. A re-pin is
taken **between subcycles**, never inside one (the early ecosystem audit's EC9).

**Carried, 104 … 118** — what each moves, measured at `c9baa9e` by 0.0.0's blocks:

| Landing | What it does | What it moves here |
|---|---|---|
| 104 (DEF-249) | an `exit` operand is held to `int32` | **nothing**: every operand an `int32` (0.0.0 §1.6) |
| 105 (DEF-159) | an address-taken owner drops unconditionally; the emission of such a function moves | **no answer**: probe 05's released `OwnedFd` is a no-op drop, measured; no IR digest is recorded |
| 106 (D-342 R1, D-343) | an enum values every variant or none; a macro parameter the body declares is refused | **nothing**: no valued variant, no macro |
| 107 (DEF-243) | a builtin named as a value is `TYPE-054` | **nothing**: every builtin is called |
| 108 (DEF-202) | an aggregate binding may name another | **not used**: every module binding a scalar literal |
| 109 (D-352) | `failsafe`'s `pick` found through bare blocks | **not used**: every `failsafe` opens with its `pick` |
| 110 (DEF-226) | `pick (r.is_error)` carries the check out | **nothing**: `if (r.is_error)` throughout |
| 111 (DEF-233, DEF-238) | a stray `give`/`fall` and a `frac` write are refused | **nothing**: none written |
| 112 (DEF-232) | a `NIL` member is zero-sized | **nothing**: no `NIL` field |
| 113 (DEF-235 and its company) | a keyword declared as a name of any kind is `PARSE-001` | **checked against the pin's `src/frontend/keywords.npk`, 170 words**: no declared name of 0.0.0's 651 or 0.0.1's 15 is one (`tools/names.py`); `ucred`'s `pid`/`uid`/`gid` and a module named `raw` are (@@PD-160@@, EC7), so the generic option form's file is `sockopt.npk` (@@PD-165@@) |
| 114 (DEF-250) | a bare module-level binding is `TYPE-055` | **nothing**: every one `fixed`, initialised (`tools/rulings.py`) |
| 115 (DEF-251 (i)) | every `define` carries `null_pointer_is_valid` | **every emission moves in text**; the cycle records no IR digest or byte count, and CI's `npkc.ll` row (0.0.1) is notice 118's. A byte comparison across pins reads through the compiler's `meta/roadmap/1.6/tools/attrnorm.py` and `dropnorm.py`, both by `git show c9baa9e:` |
| 116 (DEF-252) | a view a callee stores is held to the holder's block | **nothing**: no callee stores a view |
| 117 (D-353) | a `comptime` value parameter is `TYPE-095` | **nothing**: none written |
| 118 (DEF-253, DEF-254) | a `Self->` method through a bound links; a default's sibling call links | **probe 06 measures it**: an `async` `Self->` `write` through a bound runs; no default calls a sibling (`tools/shapes.py`) |

**Not carried** — landed on the compiler's `main` after the pin (`463cf93` by its local ref at 05:43:11 on
2026-10-18, for 119 … 128; `c72639f`, landing 137, by the 0.0.2 dispatch's `ls-remote` and the Workspace clone's local
ref on 2026-10-21, for 129 … 137; `a3c873c`, landing 139, by the 0.0.3 dispatch's `ls-remote` and the Workspace clone's
ref on 2026-10-22, for 138 and 139; each read at its own sha in the compiler's `meta/NOTICES.md`), and where each would
move this plan (`0.0.2.md` §11 and `0.0.3.md` §11 have each subcycle's places for every one; the self-check's
fixtures, which `npkc` compiles at every full run from 0.0.3, are named where a landing reaches one):

| Landing | What it does | Where it would move this plan |
|---|---|---|
| 119 `34979dc` (D-355, F61) | `NULL` for a plain pointer or an `Optional` is `TYPE-096`; "maybe no pointer" is `T->?` with `NIL` | **nowhere written**: the cycle writes no `NULL` (`tools/rulings.py`), and every pointer field of a kernel-structure mirror is `wild`, where `NULL` stays legal; DEF-257's `(NULL)` arm is not written |
| 120 `0156326` (D-360, F62) | `??!`, an `Optional`'s unwrap-or-trap | **not used** |
| 121 `f9a9428` (D-361, F63) | a value of wild provenance enters a plain pointer slot only through `=>! T->`, else `TYPE-097` | **nowhere written**: every `wild` value the probes make goes into a `wild` slot or is dereferenced in place; a view's `.ptr` goes to `sys`, which is no pointer slot. The `#ptr_add` sites are the probes' 63, listed by `tools/shapes.py`, and `src/` has none: the library's count starts at zero and stays few and listed, never confined to `wild` context on `BUILTIN_REFERENCE.md`'s sentence, which landing 128 struck; 0.0.2's floor-writer fills the floor's `write`'s `wild any->` slot with its view's `.ptr`, and 0.0.3's `scan-floor-write` fixture with a `wild int8->` |
| 122 `29e93a9` (D-357) | a `comptime func:` is compile-time only, `TYPE-098` | **nothing**: none written |
| 123 `284402d` (D-356) | a payload-less variant is a constant outside the evaluator | **nothing**: no initialiser names a variant |
| 124 `ccf7f95` (D-359) | the orphan rule, `TYPE-099` | **nothing**: every `impl` sits beside its type (`tools/rulings.py`) |
| 125 `2b95bb4` (DEF-234 (a), (b)) | a driver method takes a byte payload; `use mod.f;` binds its member | **nothing**: no `extern` driver; 0.0.1's consumer imports by path |
| 126 `e709f77` (DEF-242) | the site table holds the emission's sites | **emission only**: no IR is compared |
| 127 `1670427` (D-339, DEF-181) | the lock walk's holes closed | **nothing** in the probes: no lock; probe 09's channel is refused at its annotation. **Re-read** for 0.0.3's `scan-lock` fixture, which holds a `Guard` and calls nothing while it does |
| 128 `463cf93` (D-341, F70) | a `buffer` gets the checked `b[i]` and `b[lo...hi]`; a `#wild_slice` over a header's `.ptr` is a view of its owner (`BORROW-015`, `BORROW-001`); `#ptr_add`'s "`wild` context" sentence struck | **nowhere in 0.0.0**, which writes no `buffer` index and no `#wild_slice`; notice 128 counts no sockets site. **0.0.4's `Bytes` is designed to it**: no raw `.ptr[i]`, no `#wild_slice` over `.ptr` held across a write — nitpick-time's `bytes.npk` line 140 is the shape that breaks |
| 129 `17d26ad` (DEF-244) | the source manager keys a file by its identity, so a root imported back from a sibling is one module | **nothing measured**: its row says the shown path is unchanged (D-236) and every program it compared byte-identical; no module imports another back; 0.0.2's `repro` step re-reads it |
| 130 `c1e20e8` (DEF-245, DEF-260) | a declaration whose header fails is one report | **nothing**: each refused probe, and each of 0.0.3's refusal fixtures, reports one diagnostic per site at the pin, which the exact-code rule (0.0.2) re-reads at the adoption |
| 131 `b1a23b8`, 137 `c72639f` (DEF-255, DEF-267) | the qualified trait call reaches a bound and a pointer receiver; awaited and spawned | **nothing**: every trait method is called with the dotted form |
| 132 `6f0f518` (DEF-256) | a consuming `pick`'s binding re-assigned after a move is live again | **nothing**: none written |
| 133 `c230073` (DEF-257, D-362) | a `pick` does not select on a pointer; the pipe operators struck | **nothing**: every `pick` selects an `Error` or an enum; no pipe |
| 134 `a73b68d` (DEF-178, DEF-187) | a `pick`'s value pattern is a constant of the selector's type | **nothing**: no value pattern written |
| 135 `0280fc9` (DEF-190, DEF-182) | a numeral's digit run ends in a digit; an attribute decorates only what keeps one | **nothing**: no numeral holds an `_`; probe 12's `derive(Copy)` decorates structs |
| 136 `19d674b` (DEF-258, DEF-259, DEF-261) | a keyword is never a parameter's name; a local `T:keyword` is `PARSE-001`; a function modifier stands before `func:` alone | **nothing measured**: no declared name of 0.0.0's, 0.0.1's, 0.0.2's or 0.0.3's patched tree, or of 0.0.3's self-check fixtures, is a keyword (`tools/names.py`); 0.0.2's mutant `thread-in-library` and 0.0.3's `scan-thread` fixture write `thread async func:`, as the compiler's own test does at the pin |
| 138 `2a9d601` (DEF-272) | an explicit `<-` is a place step to the escape and aliasing analyses: a callee's store, write, view or move through `(<-a)[i]` enters their summaries and the aliasing walk's parties, and a destination through a pointer local is `BORROW-002` | **re-read**: eight probes store through `<-` into `wild` storage — 02, 03, 04, 07, 08, 10, 11 and 12 — which those analyses now step through; no fixture of 0.0.3's self-check writes through `<-` |
| 139 `a3c873c` (DEF-265, DEF-271) | after a failed expression a struct literal's braces are the expression's; a block without its `{` reads nothing | **re-read**: 0.0.3's `parse-not-parsing` fixture, a statement missing its `;`, `NITPICK-PARSE-001` at 5:1 (`0.0.3.md` §1.3); no probe holds a parse error |

**At the adoption that carries any landing past the pin, 0.0.1's CI moves**: its three rows that pin the compiler —
`NITPICK_COMMIT`, `NPKC_LL_SHA256`, `NPKC_LL_BYTES` — take the new notice's, and `LLVM_VERSION`, with the manifest's
`llvm` row, only if a landing moves the compiler's D-349 (`0.0.1.md` §10, which also names what each item not yet
landed would move) — and a new LLVM pin is a new research digest (@@PD-172@@). **And 0.0.2's harness is re-read**:
`harness/runtime_symbols.tsv` stops the run on any global symbol of the runtime it does not class, so a landing that
rebuilds the floor (D-358, not landed) is classed before a run can be green, and build step 1's printed counts move
with it (`0.0.2.md` §11).

## The shapes this cycle does not write

From the brief's list of shapes `7e91730` accepts and a later landing refuses or fixes, and `PLAYBOOK.md` §2's rows open
at the pin; each subcycle's facts block counts the lexical ones over what its patches add, with scanners proved on
planted and clean controls (`tools/shapes.py`, `rulings.py`, `names.py`).

| Shape | How the cycle keeps clear of it |
|---|---|
| a mixed enum; a macro parameter the body declares; a builtin named as a value; `give`/`fall` outside an arm or in a `defer`; a `frac` write; a `NIL` field | none written (`shapes.py`) |
| a store through a held `@x` after `move(x)` | no `@` held in a binding (`shapes.py`) |
| an `exit` operand not exactly `int32` | every operand counted (0.0.0 §1.6) |
| a bare or plain module-level binding; `comptime`; an orphan `impl`; `NULL` | every module binding `fixed` with an initialiser; none of the rest (`rulings.py`) |
| a name that is a keyword at 113, or a prelude name declared again | every declared name read against the pin's table (`names.py`); `RESOLVE-001` names in `specs/BUILD.md` §7 |
| a generic value parameter; a trait default calling a sibling on `self` | none written (`shapes.py`) |
| a qualified trait call through a bound (DEF-255, open) | every trait method called with the dotted form |
| a `buffer` read or written through an untied view (D-341 not carried) | no `#wild_slice`; `.ptr` only behind 0.0.4's checked accessors (Addition 1) |
| `PLAYBOOK.md` §2's open rows | the read-only view in every reader slot (@@PD-161@@); no part of a `fixed` binding written; every path leaving explicitly; `main` exactly `int32(cstring[]:_~argv)`; each `Result` tested alone; `#size_of` measured, never summed |

## What the audits found owed, and where each is carried

**The pin audit's SL-1 … SL-6** (`meta/audits/nitpick-sockets-pin-7e91730-2026-10-09.md` in the workbench), **the
planning guide's §3.2 items and its gap table** (`.internal/credits/out/plan-brief-sockets-0.0-2026-10-15.md` and the
2026-10-09 brief it refreshes), and **the ecosystem audit's ten sockets items** (`meta/audits/ecosystem-2026-10-15.md`,
each defined in `ecosystem-early-2026-10-09.md`; re-derived by searching it for "sockets" and by subject):

| Item | Carried by | How |
|---|---|---|
| SL-1, read-only byte parameters | 0.0.0 step 3 | **FIXED**: A-5, A-14, A-22, Z-2, the 0.1 checklist; probes 14, 14b (@@PD-161@@) |
| SL-2, `Bytes::view()` | 0.0.4 | a view, if any, tied to D-341's freeze; the write path takes `fixed uint8[]` (@@PD-161@@'s rule) |
| SL-3 and E2-4, LLVM 20.1.8 and the manifest's rows | 0.0.1 steps 3, 4 | **FIXED** (@@PD-166@@): `[toolchain]`'s `llvm`, `triple` and `datalayout` as the compiler's manifest gives them at the pin, worded as `nitpick-regex`'s; `CLAUDE.md`, `README.md`; CI asserts the tools |
| SL-4, `fixed` on the stream checklists | 0.0.0 step 3 | **FIXED**: the 0.3 checklist; probe 06b's `TYPE-014` |
| SL-5, "cycle 1.5" labels | 0.0.1 step 6; 0.0.4 | **FIXED** at four sites: `README.md`, `BUILD.md` §1, `specs/README.md`, O-N2, with `SK-004`'s dated note; `VERIFICATION.md` 7, 22 … 26, 102 and 125 and `SAFETY.md` 193 … 194, "discharge in cycle 1.5", with EK1 (0.0.4) |
| SL-6, "fixed" as a size | 0.0.0 step 3 | **FIXED**: eleven lines in nine places, the pin audit's ten less `SK-022`'s settled text, which is left |
| NH-1 and EC1, the `SIGPIPE` premise | 0.0.0 step 1 | **FIXED** at every site of the audit's list and their twins by subject (@@PD-159@@) |
| NH-2, the Bridge quotation | 0.0.0 step 1 | **FIXED**: `SAFETY.md` §2's dated note reads both sentences at the pin |
| NH-3, "`exit 0` asserts every descriptor closed" | 0.0.0 §1.3; 0.0.3 step 1 | measured false (D-151 sees no descriptor); **FIXED** in 0.0.3: `TESTING.md` V-14's case struck with the measurement (@@PD-174@@) |
| NH-5 and G1, the manifest's target rows | 0.0.1 step 3; 0.0.2 step 1 | **FIXED**: the rows (@@PD-166@@); the harness held to them, B-1a (@@PD-169@@) |
| NH-7 and EK1, `VERIFICATION.md` Z-1 | 0.0.4 | an obligation a comment unless a decision accepts the arm its live clause costs, as regex's P-1b and parse's P-1a |
| NH-8 and EC2, what an index does | 0.0.4 | `SAFETY.md`'s row, `VERIFICATION.md` §2 and `CLAUDE.md` with the containers' measured accessors |
| NH-9, an identity's payload | not this cycle's | no step of cycle 0.0 raises an identity; cycles 0.3 and 0.4 meet `ESockCapacity`'s length, and `PLAYBOOK.md` §2's row stands |
| NH-10 and G3, G4, the compiler's tools as judges | 0.0.2 step 1; 0.0.3 | **FIXED** in 0.0.2: no separate compilation, the allowlist from `npkrt.o` (@@PD-169@@), a call-edge scan from a table of the whole runtime (@@PD-170@@), the refusals judged by `npkc` (@@PD-171@@); **FIXED** in 0.0.3: the `parse` sweep and the `check` stage judged by `npkc`, `accept` struck (@@PD-173@@) |
| NH-11 and G8, the floor and the loops | 0.0.0; 0.0.2 step 1; 0.0.4 | every probe names the floor's six (0.0.0 §1.4); **FIXED** for the harness's templates, the three baseline programs naming the floor's six, with no loop; the planting sweep that every loop of `src/` is reached, 0.0.4, with the first loop |
| NH-12 and G13, the containers | 0.0.4 | `Vec<T: Copy>`, which the address types satisfy (probe 12) |
| NH-13 and EC7, names and `raw.npk` | 0.0.0 step 2; 0.0.1 step 1; 0.0.3 | **FIXED**: `BUILD.md` §7 measured (@@PD-160@@); `src/option/sockopt.npk` on the eight lines outside the plans and `SK-026` marked (@@PD-165@@); `0.0.3.md`'s own line, re-derived |
| NH-14, `cstring` paths | not this cycle's | no step of cycle 0.0 writes a path parameter; cycle 0.4's `unix_unlink` decides it |
| E2-10, counts against sets | 0.0.0 step 4 | **FIXED** here: `ROADMAP.md`'s and `OPEN_QUESTIONS.md`'s counts dropped. `LIBRARIES.md:14` is the workbench's (W-16), the orchestrator's |
| E2-13 and G14, `CURRENCY.md` and the research | 0.0.0 gate item 7; 0.0.1 step 5; 0.0.2 step 3 | **FIXED**: the three requests in 0.0.0 §13; the gate is cycle 0.0's first work dispatch; `CURRENCY.md` and its three research rows (@@PD-168@@); 0.0.2 checks the Python row and LLVM's by content, the latter from its own request (`0.0.2.md` §13) |
| E2-15, `CLAUDE.md`'s empty heading | 0.0.1 step 6 | **FIXED**: the paragraph under "What this is" |
| EC3 and G6, "every public `error:`" | 0.0.0 step 4; 0.0.3 | **FIXED** at its cost sentences (`SAFETY.md`:20, `CONTRIBUTING.md`:46), measured (@@PD-163@@), with S-8's twins by subject, `src/addr/README.md` and the 1.0 checklist's line; **FIXED** in 0.0.3: `TESTING.md` §5's row and the check, keyed by module and name, and S-8's five-module sentence (@@PD-175@@) |
| ED2, local `O-N` ids | 0.0.0 step 4 | **FIXED**: O-N1, O-N3, O-N4 and the new fifth each say its id is this repository's own |
| G2, CI; EK2 by subject | 0.0.1 step 4; 0.0.2 step 3 | **FIXED** (@@PD-167@@): LLVM asserted, the compiler at the pin and clean, `npkc.ll`'s row, every hex value quoted, and no action to pin; in 0.0.2, the harness step's unqualified green summary, and LLVM's tarball by content — its size and sha256 from a research digest, checked before it is unpacked (@@PD-172@@) |
| G5, one reading of source | 0.0.3 steps 1, 2 | **FIXED**: `harness/lexical.py`, every tree check over blanked bytes with a control naming its banned form in a comment, and every sentence that called a check a grep (@@PD-175@@) |
| G7, the bill from `REACH-003` | 0.0.0 §1.4; cycle 0.2 | measured; `check_failsafe_arms` from cycle 0.2, its oracle named on every run's `later` line |
| G9, refusals their own dispatch | 0.0.0; 0.0.1 step 3 | **FIXED**: `tests/probe/` and `refused/`, and the manifest's `probe` and `probe-refused` |
| G10, transcripts and status | 0.0.0; 0.0.2 | every verdict an Expect from a run; status never through a pipe (0.0.0 §2); the harness prints each exit and code itself, and CI reads its status on its own line (0.0.2) |
| G11, the self-check | 0.0.3 step 1 | **FIXED**: 54 live cases, each beside a control, 1 pending printed as pending (@@PD-174@@) |
| G12, the managed-memory gate | 0.0.0 §1.3; 0.0.2 step 1; 0.0.4 | D-151 sees only `wild`; **FIXED** in 0.0.2: `mem-cap-mib`, after the floor program under the same cap (B-6a, @@PD-171@@); the containers' leak tests, 0.0.4 |
| G15, the close | 0.0.5 | the audit before it (W-22), the REPORT, a verifier |
| G16, every command run | this pass | every block of each file at the pin run in a stand-in; denominators printed |
| G17, reproducibility | 0.0.2 step 1 | **FIXED**: the `repro` step's copies each carry the manifest (B-4's re-read, @@PD-169@@), and its mutant without one is red |
| G18, numbers by command | 0.0.0 gate item 3 | the decision number read by `PLAYBOOK.md` §7's command; no `O-N` id assigned to the registry by a worker |
| G19, the re-export hazard | retired | the planning guide's §3.3: compiler DEF-7, fixed at `94874ce` |
| G20, `check_specs_current` | 0.0.3 step 1 | **FIXED**: it fails the run (@@PD-175@@) |

## The planning guide's open points, and each one's answer

| # | Point | Answer |
|---|---|---|
| 1 | which compiler | `2e1cb4a`, adopted on 2026-10-23 before any subcycle started; planned at `c9baa9e`, the one re-pin of 2026-10-16, from the start |
| 2 | `SK-013` after the handler | settled by 0.0.0: the rule kept, its fact superseded, V-5 rewritten around probe 04, the marker retired (@@PD-159@@); 0.0.2's runner fails a file carrying it by name (@@PD-171@@), and 0.0.3's self-check proves it (@@PD-174@@) |
| 3 | verification clauses (Z-1, Z-4, Z-5) | handed to 0.0.4, with EK1 |
| 4 | how error detail reaches a caller | not this cycle's (NH-9) |
| 5 | how errno names are declared | settled by 0.0.0: none can be, nor compared but against the prelude's or another error (@@PD-162@@); `check_error_budget` keys every identity a `fail` site raises by (module, name), and a forwarded errno is none (0.0.3, @@PD-175@@) |
| 6 | driving `async` from a probe | settled: `async func:main`, probes 06, 07, 08, 10 |
| 7 | a `fixed uint8[]`'s pointer and length into `sendto` | settled: `wsrc.ptr` and `wsrc.len`, probe 06 |
| 8 | `fd` and `int32` at the reactor | settled: `(o.value) =>! int32`, probes 06 and 07 |
| 9 | `cstring` paths (NH-14) | not this cycle's |
| 10 | `view()` and what `Bytes` is over | handed to 0.0.4, designed to D-341 |
| 11 | is sockets security-sensitive | settled: yes; its three research items gate cycle 0.0's first work dispatch (0.0.0 gate item 7, §13); recorded by 0.0.1 (@@PD-168@@) |
| 12 | where CI sits | settled by 0.0.1 (@@PD-167@@): GitHub's `ubuntu-24.04`, whose loopback CI's first step binds, a currency row its first run checks; no test needs a user namespace; and the `loopback` stage binds it before its first unit, never skipped (0.0.3, @@PD-173@@) |
| 13 | names | settled for 0.0.0 … 0.0.3 (`names.py`, `BUILD.md` §7; 0.0.3's self-check fixtures read too); `NSOCK_*`'s two lists handed to 0.0.4 |
| 14 | the compiler's stale comments | the orchestrator's to raise (W-27): 0.0.0 §10, §12 |
| 15 | nothing has been run | every block of each file at the pin ran, in plan order, in a stand-in |
| 16 | landing 105 and probe 05 | settled: a released owner's drop closes nothing, probe 05 |

## The places the first writing disagreed with itself

- **`ADDRESS_MODEL.md` said its sizes are re-asserted by probe 03**, which measures the message structures; probe 02
  and probe 12 assert them (step 2 corrects it).
- **The checklist's probe 12 held "128-byte POD values"** and its section "a 20-byte and a 6-byte payload": a
  `SocketAddr` is 32 bytes, over payloads of 6 and 28 (probe 12).
- **The plan's probe 04 was to die by signal 13 in a child**, and the harness was to grow a marker for it: at the pin
  nothing dies, and the marker is retired (@@PD-159@@).
- **`BUILD.md` B-18's drawing gave `option` and `socket` fewer arrows than the specifications need**, and its sentence
  read columns that put `datagram` left of `server`: 0.0.1 states the layering as a table (@@PD-164@@).
- **`SOCKET_MODEL.md` K-12's builder returns `stream`'s types from `socket`**, which the table does not let `socket`
  import: held as an `O-K` entry for cycle 0.2 (0.0.1 step 1).
- **The first writing's 0.0.1 was to show CI's `network` skip line**, at a subcycle whose harness is a stub: the two
  stages are 0.0.3's, and 0.0.1's CI binds the runner's loopback itself (@@PD-167@@).
- **`BUILD.md` §2's drawing linked a library object between the library and every program**, and B-2 derived its
  allowlist from `runtime/npkrt.ll`'s text: `npkc` emits one module per root, and the link resolves against the
  runtime object (@@PD-169@@). And the first writing's 0.0.2 judged the `program` stage alone, while its 0.0.0 wrote
  refusals among the probes: 0.0.1's manifest gives them an entry of their own (@@PD-166@@), which 0.0.2's runner
  judges (@@PD-171@@).
- **`SAFETY.md` S-8 had five modules declare the two identities S-4's table declares once, in `src/socket/`** — ten
  identities by the compiler's count, and `option`'s row of B-18's table does not reach `socket`: one declaration,
  raised through its import (@@PD-175@@).
- **`TESTING.md` V-14's self-check had a case for a socket left open at exit, which D-151 was to trap**, where 0.0.0
  measured that it does not: the case is struck, and the self-check is its own list (@@PD-174@@). And the first
  writing's 0.0.3 had its `parse` and `check` stages judged by the compiler's tools "built once per run", where nothing
  here builds the compiler (@@PD-173@@).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| [0.0.0](0.0.0.md) | **The language probes** — nineteen programs asking the compiler and the kernel whether the design is spellable, five of them `SK-013`'s and `SK-035`'s | a verdict per probe, the specifications amended by them |
| [0.0.1](0.0.1.md) | **The skeleton** — the module layout, `src/lib.npk`, the manifest's toolchain rows and test table, CI, `CURRENCY.md` | `npkc` compiles an empty library and a program that imports it |
| [0.0.2](0.0.2.md) | **The harness, part 1** — build and its two scans, the `program` stage and both `compile` kinds, the toolchain pin, `repro`, CI's summary and LLVM by content | every probe builds, links, runs or is refused, and is judged; every scan seen red by its mutant |
| [0.0.3](0.0.3.md) | **The harness, part 2** — the `parse` sweep and the `check` stage, `loopback`, `network`, the self-check, the tree checks | the self-check proves the harness can fail in every live way it names |
| [0.0.4](0.0.4.md) | **`src/core/`** — `Vec<T>`, `Bytes`, `limits.npk` | the primitives, with their suites and their obligations written |
| [0.0.5](0.0.5.md) | **Close** — the findings, the handoff to 0.1 | `done/0.0/`, and 0.1 openable by a fresh session |

## Checklist

The 0.0.1 … 0.0.5 items are the re-derivation's targets, drawn from the owed items and 0.0.0's verdicts; each file
states its own acceptance when it reaches the pin, and where the two differ, the file at the pin governs.

### 0.0.0 — the probes
- [ ] the research gate's three digests filed before any probe runs (0.0.0 gate item 7, §13)
- [ ] `probe04_sigpipe.npk` — the floor's handler read; a send to a dead peer answers `EPIPE`, with and without `MSG_NOSIGNAL`; under `SIG_DFL` `MSG_NOSIGNAL` keeps the program alive (@@PD-159@@)
- [ ] `refused/probe09_ownedfd_channel.npk` and `probe09b_holder_channel.npk` — `NITPICK-TYPE-057`; `probe10_ownedfd_spawn.npk` runs and `refused/probe10b_borrow_spawn.npk` is `NITPICK-BORROW-004` — `SK-035`, run as a pair
- [ ] `probe01_sys_socket.npk`, `probe02_sockaddr_layout.npk`, `probe03_cmsg_layout.npk`, `probe12_pod_addr_array.npk` — the layouts, and `SocketAddr`'s 32 bytes (@@PD-160@@)
- [ ] `probe05_ownedfd_drop.npk`, `probe06_reader_writer.npk` with `refused/probe06b_impl_drops_fixed.npk`, `probe14_view_codec.npk` with `refused/probe14b_view_into_plain.npk` — ownership, the traits, the view (@@PD-161@@)
- [ ] `probe07_io_ready.npk` and `probe08_connect_inprogress.npk` forty times a leg; `probe11_scm_rights.npk`; `refused/probe13_errno_declared.npk` and `probe13b_errno_number.npk` (@@PD-162@@, @@PD-163@@)
- [ ] every verdict in `0.0.0.md` §6 re-measured, SAME, and every consequence in `meta/specs/` and `meta/DECISIONS.md` in the commit of its verdict
- [ ] `tests/probe/README.md`; block 6's sweep read

### 0.0.1 — the skeleton
- [ ] `BUILD.md` B-18 as a table of what each module may import (@@PD-164@@); the generic option form's file `src/option/sockopt.npk` (@@PD-165@@, EC7)
- [ ] `src/lib.npk` exists and `pub use`s nothing yet (`use` is not transitive, so the surface is a deliberate list)
- [ ] every `src/` subdirectory has a placeholder module that compiles, its header stating its row of the table
- [ ] `nitpick.toml`'s `[toolchain]` at LLVM 20.1.8 with the `triple` and `datalayout` rows, and three `[[test]]` entries — `conformance`, `probe` and `probe-refused` (@@PD-166@@)
- [ ] a consumer program under `tests/conformance/` imports `src/lib.npk` by relative path and compiles, links, runs and exits 0
- [ ] CI: a workflow running no action — `harness/run.py`'s stub on push, LLVM 20.1.8 asserted, the compiler at the pinned commit and its emission asserted, the runner's loopback bound, every hex value quoted (@@PD-167@@) — green on the push
- [ ] `meta/research/CURRENCY.md`, its three research rows and every external fact the specifications state (@@PD-168@@)
- [ ] `CLAUDE.md` and `CONTRIBUTING.md` re-read against 0.0.0's verdicts and extended; `CLAUDE.md`'s empty heading filled

### 0.0.2 — the harness, part 1
- [ ] the research gate's LLVM digest filed before any block runs (`0.0.2.md` gate item 7, §13)
- [ ] `harness/run.py`: the manifest reader held to the compiler's schema, the interpreter and the toolchain held to the manifest's pin and target rows (@@PD-169@@, @@PD-171@@) — `npkc` walks each root's module graph itself
- [ ] the build pipeline — one module per root and `npkrt.o` — with the undefined-symbol scan and a call-edge scan from a table of the whole runtime as build steps, their controls seen on every run (@@PD-169@@, @@PD-170@@)
- [ ] the `program` stage and `compile`/`positive` at -O0 and again under `opt -O2`, same exit required, and `compile`/`negative` by the exact-code rule; `expect-exit`, `stress` and `mem-cap-mib` honoured — `expect-signal` refused (@@PD-159@@, @@PD-171@@)
- [ ] the `repro` check: two builds from different working directories, each copy with its manifest
- [ ] 0.0.0's `tests/probe/` and `refused/` green as the first suites, probes 07, 08 and 11 forty runs a leg
- [ ] every check seen red by its mutant (block 4m)
- [ ] CI: the harness step asserting the unqualified green summary; LLVM's release tarball checked by its size and sha256 against the research digest before it is unpacked, `CURRENCY.md`'s row checked (@@PD-172@@) — green on the push

### 0.0.3 — the harness, part 2
- [ ] the parse sweep, its entry required, and the `check` stage, judged by `npkc` by the **exact-code** rule 0.0.2's `compile`/`negative` uses (@@PD-171@@, @@PD-173@@); `accept` struck
- [ ] the `loopback` stage, never skipped; the `network` stage, skipped **loudly** with its reason (V-2) (@@PD-173@@)
- [ ] `--only`, and output that says twice that a filtered run concludes nothing (@@PD-174@@)
- [ ] `harness/selfcheck.py`, its 54 live cases each caught beside a control that passes and its pending one printed as pending, before anything judges the library (@@PD-174@@)
- [ ] the nine tree checks — `check_layering`, `check_error_budget` keyed by module and name, `check_constants_named`, `check_no_hardcoded_port`, `check_msg_nosignal`, `check_no_floor_write`, `check_no_raw_setsockopt`, `check_struct_sizes`, `check_specs_current` — each with what it read, through `harness/lexical.py` (@@PD-175@@)
- [ ] every sentence that called a check a grep, and every permanent file that cited a cycle file's block, corrected; block 3m's mutants each red by the check it breaks

### 0.0.4 — `src/core/`
- [ ] `src/core/limits.npk` — every named bound in one file, each with its rule
- [ ] `src/core/vec.npk` — `Vec<T: Copy>`, every accessor boundary-tested, a misuse trapping `OutOfBounds`
- [ ] `src/core/bytes.npk` — `Bytes`, `put_uint` allocation-free, growth counted, no raw `.ptr[i]` and no `#wild_slice` held across a write (D-341)
- [ ] every obligation written as a comment in the syntax it would take, with a unit standing in

### 0.0.5 — close
- [ ] every probe verdict reconciled against the specifications **by reading them**, 04, 09 and 10 by name
- [ ] the cycle's findings written as a numbered list; the close audit run and triaged (W-22); a full green run, its output quoted
- [ ] `0.1/0.1.0.md` written execution-grade before the cycle closes, its gate naming the three research digests with their dates
- [ ] cycle moved to `done/0.0/`, `ROADMAP.md` updated

## Gate

**The cycle is complete when**: every probe has a recorded verdict, its consequences written into the specifications —
**with probes 04, 09, 09b, 10 and 10b recorded against `SK-013` and `SK-035`**; a full `harness/run.py` is green; the
self-check proves the harness fails in every live way it names and reports the pending ones as pending; and
`src/core/` has its suites.

## Watch for

- **Probe 04 is the one whose answer moved.** At the pin the floor catches `SIGPIPE`, so the send path's rule rests on
  the default disposition, not the runtime's; its leg 4 is the leg that would see `MSG_NOSIGNAL` lost (0.0.0 §1.5).
- **Probes 09, 09b, 10 and 10b are read as a set**, because the interesting fact is the asymmetry: a channel refuses
  what a spawn accepts by move and refuses by borrow.
- **A probe that fails is a finding, not an obstacle.** Record the exact diagnostic, decide the design change, amend
  the specification, and only then continue. Working around a compiler refusal in library code is what the compiler's
  R6 forbids.
- **The reserved words, and the prelude's names, bite immediately**: `old`, `result`, `release`, `pid` and the
  prelude's `O_CLOEXEC` met the probes' first drafts. `specs/BUILD.md` §7 is the measured table.
- **An errno the prelude does not name cannot be compared.** Every protocol that must tell errnos apart is spelled
  against the prelude's five, or waits on the compiler (@@PD-162@@).
- **`Vec<T>`'s block is `wild` storage** and every path out of a function that took some must release it, or `exit 0`
  traps under D-151 — which sees `wild` bytes and nothing else: not a descriptor (0.0.0 §1.3).
