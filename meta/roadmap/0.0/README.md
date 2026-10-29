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
row by row, every block of 0.0.0 … 0.0.3 run again at the new pin. **T7c4, 2026-10-24**, gave every dated line
those four files' patches add the landing run's date (below), and cut 0.0.4's three patches; **T7c4b, 2026-10-25**,
measured the claims T7c4 had written unrun, re-cut those patches where a claim was false or a twin stale, and planned and
rehearsed 0.0.4 at `2e1cb4a`; **T7c5, 2026-10-25**, the pass's last planner, planned and rehearsed 0.0.5 at `2e1cb4a`,
brought the landing table below to every file, and retook the earlier files' `check_refs` lines from a run in plan
order (`0.0.5.md` §13); **fix round 2, 2026-10-25**, answered the final plan verification's findings at their
sources and added the two checks its last section records. No subcycle has started.

| File | At `2e1cb4a` |
|---|---|
| [0.0.0](0.0.0.md) | **yes**, adopted — probes measured, five patches, blocks with filled Expects |
| [0.0.1](0.0.1.md) | **yes**, adopted — the layout, the skeleton, the manifest, CI and the currency table; six patches, blocks with filled Expects |
| [0.0.2](0.0.2.md) | **yes**, adopted — the harness, part 1: the runner, its two scans and their controls, `repro`, three stages, the probes as suites, CI's summary and LLVM by content; three patches, the mutants, blocks with filled Expects |
| [0.0.3](0.0.3.md) | **yes**, adopted — the harness, part 2: the `check` stage and the `parse` sweep, `loopback` and `network`, the self-check beside its controls, nine tree checks and `--only`; two patches, the mutants, blocks with filled Expects |
| [0.0.4](0.0.4.md) | **yes**, planned at `2e1cb4a` — `src/core/`: `limits.npk` held to the bounds the specifications state, `Vec<T: Copy>` checking its own indexes with every generic instantiated where the call-edge scan reads it, `Bytes` through its buffer's checked index with no view; three patches, the mutants, the loop sweep, blocks with filled Expects |
| [0.0.5](0.0.5.md) | **yes**, planned at `2e1cb4a` — the close, in two dispatches: every verdict reconciled by reading, three permanent files' citations of a cycle file's section replaced, the sweep and the citations, the findings, a full run and the census of every program, `READY-TO-CLOSE`; then the close audit triaged, `0.1/0.1.0.md` and the archive; two patches, blocks with filled Expects; its execution is the libraries' seat's |

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
| @@PD-176@@ | 0.0.4 | `limits.npk` holds every bound a specification states with its value; `check_constants_named` holds it to them both ways, and refuses a bound's value as a literal only where no kernel value shares it |
| @@PD-177@@ | 0.0.4 | the containers check their own indexes and trap `OutOfBounds`; `Bytes` through its buffer's checked index, with no view; `put_uint` divides by nothing; an obligation is a comment unless a decision accepts its arm; every generic instantiated where the call-edge scan reads it |
| PD-178 | 0.0.5 | **unused**: 0.0.5 proposes no decision |

## The pin, and what each landing would move

**The pin is `2e1cb4a`**, landings 83 … 140 (the workbench's `.internal/toolchain/2e1cb4a/PIN.md`, CARRIES and NOT
CARRIED). This cycle was planned at `c9baa9e`, landing 118, and adopted `2e1cb4a` before any subcycle started (T7a,
2026-10-23), so a landing the pin carries is measured, not predicted; a landing it does not carry is named with the
place it would move this plan, so that **the next adoption is this list, not a search**. A re-pin is taken **between
subcycles**, never inside one (the early ecosystem audit's EC9).

**Carried, 104 … 118** — what each moves, measured at `c9baa9e` by 0.0.0's blocks, and again at `2e1cb4a` by the
adoption (below): nothing moved but what row 115 names.

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
| 113 (DEF-235 and its company) | a keyword declared as a name of any kind is `PARSE-001` | **checked against the pin's `src/frontend/keywords.npk`, 170 words**: no declared name of 0.0.0's 663 or 0.0.1's 15 is one (`tools/names.py`); `ucred`'s `pid`/`uid`/`gid` and a module named `raw` are (@@PD-160@@, EC7), so the generic option form's file is `sockopt.npk` (@@PD-165@@) |
| 114 (DEF-250) | a bare module-level binding is `TYPE-055` | **nothing**: every one `fixed`, initialised (`tools/rulings.py`) |
| 115 (DEF-251 (i)) | every `define` carries `null_pointer_is_valid` | **every emission moves in text**; the cycle records no IR digest or byte count, and CI's `npkc.ll` row (0.0.1) is the pin's notice's, 140's since the adoption (118's before it). A byte comparison across 105 and 115 reads through the compiler's `meta/roadmap/1.6/tools/attrnorm.py` and `dropnorm.py`, and across 126 through its `sitenorm.py --site-path-cap` (row 126 below), each by `git show 2e1cb4a:` |
| 116 (DEF-252) | a view a callee stores is held to the holder's block | **nothing**: no callee stores a view |
| 117 (D-353) | a `comptime` value parameter is `TYPE-095` | **nothing**: none written |
| 118 (DEF-253, DEF-254) | a `Self->` method through a bound links; a default's sibling call links | **probe 06 measures it**: an `async` `Self->` `write` through a bound runs; no default calls a sibling (`tools/shapes.py`) |

**Carried since the adoption, 119 … 140** — each read at its own sha in the compiler's `meta/NOTICES.md` while it was
not yet carried (`463cf93`, landing 128, for 119 … 128; `c72639f`, landing 137, for 129 … 137; `a3c873c`, landing 139,
for 138 and 139, by the earlier planners), and 140 at `2e1cb4a`; `0.0.1.md` §10, `0.0.2.md` §11 and `0.0.3.md` §11 name
each subcycle's places. Each row's last column is now **what the adoption measured here**, at `2e1cb4a` on 2026-10-23:
every block of 0.0.0 … 0.0.3 run in plan order in a stand-in, each the same as at `c9baa9e` but for the lines each
file's §1 names; and the old-pin leg — every `.npk` of the patched tree, 33, and every fixture of the self-check, 105,
compiled by both pins' `npkc` from its own directory: the same exit, codes and sites at both, and every emission that
compiles at both, 108, different in text and the same through the compiler's `meta/roadmap/1.6/tools/sitenorm.py
--site-path-cap`, landing 126's normaliser. **"Nothing moved" below is that measurement**, never a notice's census: the
compiler's census reads the libraries' trees, where this plan's programs are not yet, since they are still its patches.

| Landing | What it does | What the adoption measured here |
|---|---|---|
| 119 `34979dc` (D-355, F61) | `NULL` for a plain pointer or an `Optional` is `TYPE-096`; "maybe no pointer" is `T->?` with `NIL` | **nothing moved**: 0.0.0 … 0.0.3 write no `NULL` (`tools/rulings.py`), and every pointer field of a kernel-structure mirror is `wild`, where `NULL` stays legal; DEF-257's `(NULL)` arm is not written. 0.0.4's `vec_free` writes one, into `Vec`'s `wild` field, measured legal where a plain field's is `TYPE-096` (`0.0.4.md` §1.7) |
| 120 `0156326` (D-360, F62) | `??!`, an `Optional`'s unwrap-or-trap | **nothing moved**: not used |
| 121 `f9a9428` (D-361, F63) | a value of wild provenance enters a plain pointer slot only through `=>! T->`, else `TYPE-097` | **nothing moved**: every `wild` value the probes make goes into a `wild` slot or is dereferenced in place, and a view's `.ptr` goes to `sys`, which is no pointer slot; 0.0.2's floor-writer and 0.0.3's `scan-floor-write` fixture fill the floor's `write`'s `wild any->` slot, as before. The `#ptr_add` sites are the probes' 63, listed by `tools/shapes.py`, and `src/` has none: the library's count starts at zero and stays few and listed, never confined to `wild` context on `BUILTIN_REFERENCE.md`'s sentence, which landing 128 struck. 0.0.4's `src/core/` writes no `#ptr_add`, and its five `=>!`, all in `vec.npk`, are between `wild` slots or a narrowing (`0.0.4.md` §1.15) |
| 122 `29e93a9` (D-357) | a `comptime func:` is compile-time only, `TYPE-098` | **nothing moved**: none written |
| 123 `284402d` (D-356) | a payload-less variant is a constant outside the evaluator | **nothing moved**: no initialiser names a variant |
| 124 `ccf7f95` (D-359) | the orphan rule, `TYPE-099` | **nothing moved**: every `impl` sits beside its type (`tools/rulings.py`) |
| 125 `2b95bb4` (DEF-234 (a), (b)) | a driver method takes a byte payload; `use mod.f;` binds its member | **nothing moved**: no `extern` driver; every import is by path, which the parser's new single-name walk never enters, so `harness/lexical.py`'s reading of `use` holds |
| 126 `e709f77` (DEF-242, DEF-263) | the site table holds the emission's sites; `site_path` answers a view | **every emission moved, and nothing else**: the 108 pairs, each the same through `sitenorm.py --site-path-cap`; no block compares IR across pins, and 0.0.2's `repro` compares two builds at one pin, byte-identical |
| 127 `1670427` (D-339, DEF-181) | the lock walk's holes closed | **nothing moved**: no lock in the probes, and probe 09's channel is refused at its annotation as before; 0.0.3's `scan-lock` fixture, which holds a `Guard` and calls nothing while it does, compiles as before and its case is caught. With 128 it moved O-N3's comment in the compiler's `src/frontend/types.npk` from line 1733 at `c9baa9e`, "cross a spawn", to its line 1756 at `2e1cb4a`, 21 lines and 2, its text the same — `0.0.0.md` §1.2's line |
| 128 `463cf93` (D-341, F70) | a `buffer` gets the checked `b[i]` and `b[lo...hi]`; a `#wild_slice` over a header's `.ptr` is a view of its owner (`BORROW-015`, `BORROW-001`); `#ptr_add`'s "`wild` context" sentence struck | **nothing moved** in 0.0.0 … 0.0.3, which write no `buffer` index and no `#wild_slice`. **0.0.4's `Bytes` is designed to it**: no raw `.ptr[i]`, no `#wild_slice` over `.ptr` held across a write — `nitpick-time`'s `bytes.npk` holds the shape that breaks; measured, a buffer's index traps 94, its `.ptr`'s does not, and a range freezes the buffer for its block against an overwrite and against a write at any index the compiler cannot place outside the range (`0.0.4.md` §1.4) |
| 129 `17d26ad` (DEF-244) | the source manager keys a file by its identity, so a root imported back from a sibling is one module | **nothing moved**: no module imports another back; 0.0.2's `repro` reads byte-identical IR from two directories |
| 130 `c1e20e8` (DEF-245, DEF-260) | a declaration whose header fails is one report | **nothing moved**: each refused probe, and each of the self-check's 23 refused fixtures, reports the same codes at the same sites at both pins, which the exact-code rule (0.0.2) judges |
| 131 `b1a23b8`, 137 `c72639f` (DEF-255, DEF-267) | the qualified trait call reaches a bound and a pointer receiver; awaited and spawned | **nothing moved**: every trait method is called with the dotted form |
| 132 `6f0f518` (DEF-256) | a consuming `pick`'s binding re-assigned after a move is live again | **nothing moved**: none written |
| 133 `c230073` (DEF-257, D-362) | a `pick` does not select on a pointer; the pipe operators struck | **nothing moved**: every `pick` selects an `Error` or an enum; no pipe |
| 134 `a73b68d` (DEF-178, DEF-187) | a `pick`'s value pattern is a constant of the selector's type | **nothing moved**: no value pattern written |
| 135 `0280fc9` (DEF-190, DEF-182) | a numeral's digit run ends in a digit; an attribute decorates only what keeps one | **nothing moved**: no numeral holds an `_`, and probe 12's `derive(Copy)` decorates structs; the lexer's change is to numerals, which `harness/lexical.py` does not mirror |
| 136 `19d674b` (DEF-258, DEF-259, DEF-261) | a keyword is never a parameter's name; a local `T:keyword` is `PARSE-001`; a function modifier stands before `func:` alone | **nothing moved**: no declared name of the patched tree or of the self-check's fixtures is a keyword (`tools/names.py`, against the pin's `src/frontend/keywords.npk`, 170 words, byte-identical at the two pins); 0.0.2's mutant `thread-in-library` and 0.0.3's `scan-thread` fixture write `thread async func:`, which compiles at both pins |
| 138 `2a9d601` (DEF-272) | an explicit `<-` is a place step to the escape and aliasing analyses: a callee's store, write, view or move through `(<-a)[i]` enters their summaries and the aliasing walk's parties, and a destination through a pointer local is `BORROW-002` | **nothing moved**: the eight probes that store through `<-` into `wild` storage — 02, 03, 04, 07, 08, 10, 11 and 12 — compile and run as before; no fixture of the self-check writes through `<-` |
| 139 `a3c873c` (DEF-265, DEF-271) | after a failed expression a struct literal's braces are the expression's; a block without its `{` reads nothing | **nothing moved**: 0.0.3's `parse-not-parsing` fixture, a statement missing its `;`, is `NITPICK-PARSE-001` at 5:1 at both pins (`0.0.3.md` §1.3); no probe holds a parse error |
| 140 `2e1cb4a` (DEF-275) | a pointer local's value handed to a callee is checked against the views through it, as `@place` always was | **the pin**: CI's three rows take its notice's (0.0.1); no program is refused anew; its reading tool, `--dump-refs FILE`, joins `npkc`'s usage — `0.0.3.md` §1.2's line |

**Not carried** — landed on the compiler's `main` after the pin, up to `249eae9`, landing 161: 141 … 151 by the
adoption's dispatch's `ls-remote` (03:03:02 on 2026-10-23), 152 … 156 by T7c4's (03:00:48 on 2026-10-24), 157 … 161 by
T7c4b's (03:00:15 on 2026-10-25), each with the Workspace compiler clone's ref, and 161 the compiler's `main` still at
T7c5's dispatch (12:51:03 on 2026-10-25); each read in its commit and at its own sha in the compiler's `meta/NOTICES.md`,
and where each would move this plan. **The rows are for every file**: 0.0.5 writes no program, so the shapes are counted
over every program the cycle compiles at 0.0.4's record — 191, the tree's 72 `.npk` and the self-check's 119 fixtures,
read with comments and strings blanked as `tools/shapes.py` reads them — by `0.0.5_tools/census.py`, which 0.0.5's
block 3 runs after the close's full run; the adoption's counts, over the 138 programs 0.0.0 … 0.0.3 held then,
stand beside them where a row gives both:

| Landing | What it does | Where it would move this plan |
|---|---|---|
| 141 `6370cae` (DEF-268) | a function declared inside a body is one report, `PARSE-001` at `func` naming D-018 | **nowhere written**: the five `func:` within braces of the 191 programs are methods of `impl` blocks (probes 06 and 06b), none inside a body (the census's `func-in-body`, 0 of 5) |
| 142 `79cd363` (DEF-176), 150 `ea571d5` (DEF-276) | a non-folding chain at the depth bound compiles; the emitter holds every chain at the bound | **nothing**: no chain near the bound; 150's notice reads every emission byte-identical |
| 143 `753e783` (DEF-184, DEF-177) | a type nested past 256 levels is `PARSE-012`; after a `.`, anything but a member's name is `PARSE-001` | **nothing**: 218 member dots over the 138 programs, by the adoption's count, and 434 over the 191, by the census's, each followed by a name — one by `acquire`, the `scan-lock` fixture's mutex call, one of the four keywords the parser takes after a dot (D-056), and the census's only dot before a word of the pin's keyword table |
| 144 `6451911` (DEF-185, DEF-186, DEF-188, DEF-240) | a macro body declares only what an expansion emits; a macro takes no type arguments; `npkg`'s stage list is one list | **re-read**: no macro written (the census's `macro`, 0); `npkg/manifest.npk`'s read of the `target` key moves from its line 96 at `2e1cb4a` to 119 at `6451911` — 0.0.1's block 0b, §1.11 — and its `schema_allows` is unchanged (0.0.2's §1.2, 0.0.3's §1.9) |
| 145 `9c08ccc`, 148 `aba4a69`, 149 `50ebf7d` (DEF-269, DEF-279, DEF-277) | the verified build's encoder and statement walk hold at their bounds | **nothing**: nothing here runs `--obligations` or `--elide` |
| 146 `915f427` (DEF-274, S-134's R4) | an atomic's methods lower through a pointer; `npkc FILE --reach OUT` writes the identities a `failsafe` must name | **re-read**: no atomic written (the census's `atomic`, 0); `npkc`'s usage gains `[--reach FILE]` — 0.0.3's block 0b, §1.2, and its sentence — another file written beside the IR, so still no mode that stops after the parser (@@PD-173@@'s reading) |
| 147 `d422c1e` (DEF-270, DEF-280) | a generic `comptime func:` names its type parameter in a type under evaluation; `move` folds in a comptime body | **nothing**: no `comptime` (`tools/rulings.py`; the census's `comptime`, 0) |
| 151 `9eaf3b6` (D-363 R1) | a `pick` arm names several values with one body; a value repeated in a `pick` is `PICK-004`; a path over a selector that is no enum is `TYPE-007` | **nothing written**: 59 `pick`s over the 138 programs, by the adoption's count, and 99 over the 191, by the census's, none with a list and none repeating a value (`pick-list` and `pick-repeat`, 0 each); every program compiles at the pin, so none holds the shape the emitter died on |
| 152 `538c596` (DEF-278, DEF-281) | a body nested in a body is walked once per level; a `give` below an arm's top level, of another type than the `pick`'s, is `TYPE-007`, and a value-`pick` arm that can reach its end without `give` is `FLOW-001` | **nothing written**: no `give` in any of the 191 programs (the census's `give`, 0) |
| 153 `ea1307c` (DEF-282, DEF-285) | the `?.` and `#ptr_add` chains' stack; a repeated arm's `PICK-004` stands at the alternative, with a note | **nothing**: no `pick` repeats a value (the census's `pick-repeat`, 0), and the emission of `#ptr_add` is the same in effect |
| 154 `5136096` (DEF-287) | a field of a binding the frame owns is that binding's storage; a view of a pointer parameter's pointee stored into a local's field, an element or a by-value parameter's field freezes the pointee, `BORROW-015` at its write | **nothing written**: no view is stored into a field or an element in any of the 191 programs (the census's `view-stored`, 0); its 11 views are bare locals — probe 06's two, probe 14's, the baseline floor-writer's and two refusal fixtures' — and call arguments: `bytes_extend`'s from `bytes_extend_str` and two units, probe 14b's refused one, and `bytes_take`'s `string_from_bytes`, which goes straight to `string_concat` |
| 155 `02856cf` (DEF-288, DEF-290) | a `for` binding is a block-scoped local to the escape and aliasing analyses; `t.p = @t.a; pass t;` is `BORROW-001` | **nothing written**: the 191 programs' 18 `for` headers — six in `src/core/`, five in 0.0.4's units, four in probe 02 and three in probe 12 — each bind an `int64` counter over a range, none of whose views or addresses is taken; and no field is assigned an address, `t.p = @t.a` |
| 156 `a5693a6` (DEF-296, DEF-289's first face) | a store through an indirection lands where the indirection points: a pointee written while a view stored that way lives is `BORROW-015` | **nothing written**: no view is stored through a pointer local, a pointer field, a slice's element or a callee in any of the 191 programs (`view-stored`, 0) |
| 157 `5cc1fb9` (DEF-289's second face) | a store through a slice parameter's element lands in the caller's storage: `BORROW-015`, and a frame view stored through a slice the call cannot name `BORROW-009` | **nothing written that its notice names**: none of the 191 programs' 11 slice parameters is written through an element — seven are `fixed`; probe 06's two plain `uint8[]:dest`s are `pull`'s, handed on to `read`, and `read`'s, which reaches the kernel only as `dest.ptr` and `dest.len` in a `sys` call; and the other two plain ones are the refused probes 06b's and 14b's. Probe 06's `await pull(@rd, dest)` hands a frame address beside a `uint8[]`, whose elements can hold no pointer; the libraries' seat's census of F99 found none of 157's shapes in these patches (at `128a03c`). **At the adoption that carries 157, probe 06 is compiled first** |
| 158 `8e33737` (DEF-300) | a store through a range of named storage is a store into that storage | **nothing written**: the 191 programs' four ranges — probe 06's `space[0i64...8i64]` and probe 14's three — are each held as a slice local or handed to a `fixed` parameter, and the language writes through none |
| 159 `51b6d82` (DEF-297, DEF-301, DEF-303) | a write through a slice local, a slice field, a range, a call's result or a ternary is checked at each storage the slice views; a range's element is its storage's | **nothing written**: no write through a slice local, a slice field, a range, a call's result or a ternary in the 191 programs; their five slice locals not `fixed` — probe 06's `dest`, probe 14's `plain`, two refusal fixtures' and the `scan-environment` fixture's `cstring[]` — are read or handed on, and `bytes_extend_str` hands `bytes_extend` `string_bytes(s)`, a call's result `bytes_extend` only reads. Probe 06's kernel write through `dest.ptr` is no write of the language's |
| 160 `954c21a` (DEF-302) | a write through a pointer is a write to its target, checked both ways against a view of it by another name | **nothing written**: the 191 programs' 20 writes through `<-` are the probes' 02, 03, 04, 07, 08, 10, 11 and 12, each into `wild` storage no view reads; `bytes_take`'s view of `b`'s pointee is consumed by `string_concat` before its write `b.len = 0i64`, through the same name, and no view is live across a write through a pointer (`0.0.4.md` §12) |
| 161 `249eae9` (DEF-305) | a call-result pointer is resolved by its return provenance; a slice reached through a pointer, by the pointee's chain | **nothing written**: the one function whose result is a pointer, probe 08's `loopback`, returns a `wild` block it allocates itself from a `uint16`, so its three call results borrow no argument; and no slice is reached through a pointer |

**At the adoption that carries any landing past the pin, 0.0.1's CI moves**: its three rows that pin the compiler —
`NITPICK_COMMIT`, `NPKC_LL_SHA256`, `NPKC_LL_BYTES` — take the new notice's, and `LLVM_VERSION`, with the manifest's
`llvm` row, only if a landing moves the compiler's D-349 (`0.0.1.md` §10, which also names what each item not yet
landed would move) — and a new LLVM pin is a new research digest (@@PD-172@@). **And 0.0.2's harness is re-read**:
`harness/runtime_symbols.tsv` stops the run on any global symbol of the runtime it does not class, so a landing that
rebuilds the floor (D-358, not landed by 161: no notice 119 … 161 names it) is classed before a run can be green, and
build step 1's printed counts move with it (`0.0.2.md` §11).

**The adoption of `2e1cb4a` was taken on 2026-10-23 (T7a), before any subcycle started**, and measured. CI's rows are
`2e1cb4adef79…` and notice 140's `npkc.ll` row, `00730602…`, 32569732 B; `LLVM_VERSION` stays 20.1.8, since no landing
119 … 140 moves the compiler's D-349. `npkrt.o` is byte-identical at the two pins (`c8e5033a…`, 72 656 B), so the
runtime table classes the same 119 globals and build step 1 prints the same counts. The self-check's 105 fixtures
compile to the same codes and sites at both pins. Every block of 0.0.0 … 0.0.3 reads as at `c9baa9e` but block 0a's
commit line, 0.0.0's §1.2 lines (their label, and O-N3's comment, moved from line 1733 to 1756), 0.0.1's §1.5 and §1.11 (the pin's own
rows and subject) and 0.0.3's §1.2 (`npkc`'s usage, with `--dump-refs`), each retaken from a run. No verdict moved,
and no compiler defect was found.

**The dated-lines round, 2026-10-24 (T7c4)**, by the workbench `PLAYBOOK.md` §7, the libraries' seat's convention of
2026-10-23: every dated line 0.0.0 … 0.0.3's patches add — 50 dated notes, 23 of them naming the pin, 4 markers, the
openings of the 17 decisions and the decision log's third heading — writes `@@DATE@@`, which `apply.py` replaces with
the landing run's one date, kept in `.internal/w00/<subcycle>.date` from the subcycle's first step to its record; a pin
named beside such a date moves with it, `c9baa9e` to `2e1cb4a` on 27 lines. The nine decisions whose evidence names
`c9baa9e` keep it, each with a dated note beneath recording the adoption's re-measurement of 2026-10-23 — for
@@PD-173@@, that `npkc`'s usage names `--dump-refs` too. The records of where a measurement was made keep their dates
and pins: eleven lines naming `c9baa9e`, nine dated ones and the two quotations of `nitpick-regex`'s RX-245. And
`apply.py` reads a dated line in a later step's or subcycle's context, and in a removed line, against the tree, so a
patch cut today applies over an earlier run of any day. 0.0.4's patches write `@@DATE@@` from the start, in 15 added
lines — 4, 10 and 1 in its three steps (`0.0.4.md` §1.16).

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
| a qualified trait call through a bound (DEF-255, open at `c9baa9e`; fixed by landing 131, which the pin carries) | every trait method called with the dotted form |
| a `buffer` read or written through an untied view (D-341, carried from landing 128: a `#wild_slice` over `.ptr` is a view of its owner, `BORROW-015` across a write) | no `#wild_slice`; every byte of `Bytes` through its buffer's checked index, and `.ptr` once, in `bytes_take`'s copy (Addition 1; `0.0.4.md` §1.14) |
| the nine safety rules of `PLAYBOOK.md` §2's notes of 2026-10-23 and 2026-10-24: a `for` binding's view or address, a collection written inside a `for` over it, `@` of a pointer parameter, a pointer carried out of a `for`, a pointee's view stored, viewed storage written through another name, a range's element written, a pointer into a `List`, `Vec` or `Bytes` held across a growth, a value lent to a spawn | none written: each read against 0.0.4's code (`0.0.4.md` §1.15); and over every program the cycle compiles, 0.0.5's census (its block 3) finds three spawns — probe 10's, which moves its descriptor in, probe 10b's refused borrow (`BORROW-004`) and the `scan-thread` fixture's, which hands an `int32` — and no `shared_arena` and no `List<` |
| `PLAYBOOK.md` §2's open rows | the read-only view in every reader slot (@@PD-161@@); no part of a `fixed` binding written; every path leaving explicitly; `main` exactly `int32(cstring[]:_~argv)`; each `Result` tested alone; `#size_of` measured, never summed |

## What the audits found owed, and where each is carried

**The pin audit's SL-1 … SL-6** (`meta/audits/nitpick-sockets-pin-7e91730-2026-10-09.md` in the workbench), **the
planning guide's §3.2 items and its gap table** (`.internal/credits/out/plan-brief-sockets-0.0-2026-10-15.md` and the
2026-10-09 brief it refreshes), and **the ecosystem audit's ten sockets items** (`meta/audits/ecosystem-2026-10-15.md`,
each defined in `ecosystem-early-2026-10-09.md`; re-derived by searching it for "sockets" and by subject):

| Item | Carried by | How |
|---|---|---|
| SL-1, read-only byte parameters | 0.0.0 step 3 | **FIXED**: A-5, A-14, A-22, Z-2, the 0.1 checklist; probes 14, 14b (@@PD-161@@) |
| SL-2, `Bytes::view()` | 0.0.4 step 3 | **FIXED** (@@PD-177@@): no view; the bytes leave one at a time or as `bytes_take`'s owned copy, and a range of the body would stop its growth and its appends for the range's block |
| SL-3 and E2-4, LLVM 20.1.8 and the manifest's rows | 0.0.1 steps 3, 4 | **FIXED** (@@PD-166@@): `[toolchain]`'s `llvm`, `triple` and `datalayout` as the compiler's manifest gives them at the pin, worded as `nitpick-regex`'s; `CLAUDE.md`, `README.md`; CI asserts the tools |
| SL-4, `fixed` on the stream checklists | 0.0.0 step 3 | **FIXED**: the 0.3 checklist; probe 06b's `TYPE-014` |
| SL-5, "cycle 1.5" labels | 0.0.1 step 6; 0.0.4 | **FIXED** at four sites: `README.md`, `BUILD.md` §1, `specs/README.md`, O-N2, with `SK-004`'s dated note; `VERIFICATION.md`'s line on "the compiler's cycle 1.5", its table of the compiler's 1.5 subcycles, Z-4 and Z-5, and `SAFETY.md` S-16's "discharge in cycle 1.5": **FIXED** in 0.0.4 step 2, each line kept with its dated note, with EK1 (@@PD-177@@) |
| SL-6, "fixed" as a size | 0.0.0 step 3 | **FIXED**: eleven lines in nine places, the pin audit's ten less `SK-022`'s settled text, which is left |
| NH-1 and EC1, the `SIGPIPE` premise | 0.0.0 step 1 | **FIXED** at every site of the audit's list and their twins by subject (@@PD-159@@) |
| NH-2, the Bridge quotation | 0.0.0 step 1 | **FIXED**: `SAFETY.md` §2's dated note reads both sentences at the pin |
| NH-3, "`exit 0` asserts every descriptor closed" | 0.0.0 §1.3; 0.0.3 step 1 | measured false (D-151 sees no descriptor); **FIXED** in 0.0.3: `TESTING.md` V-14's case struck with the measurement (@@PD-174@@) |
| NH-5 and G1, the manifest's target rows | 0.0.1 step 3; 0.0.2 step 1 | **FIXED**: the rows (@@PD-166@@); the harness held to them, B-1a (@@PD-169@@) |
| NH-7 and EK1, `VERIFICATION.md` Z-1 | 0.0.4 step 2 | **FIXED** (@@PD-177@@): Z-1a — an obligation a comment unless a decision accepts the arm its live clause costs, as regex's P-1b and parse's P-1a — and every obligation of `src/core/` measured to compile live |
| NH-8 and EC2, what an index does | 0.0.4 step 2 | **FIXED**: `SAFETY.md`'s row, `VERIFICATION.md` §2's note and `CLAUDE.md`'s line say which index traps, measured (`0.0.4.md` §1.4) |
| NH-9, an identity's payload | not this cycle's | no step of cycle 0.0 raises an identity; cycles 0.3 and 0.4 meet `ESockCapacity`'s length, and `PLAYBOOK.md` §2's row stands |
| NH-10 and G3, G4, the compiler's tools as judges | 0.0.2 step 1; 0.0.3 | **FIXED** in 0.0.2: no separate compilation, the allowlist from `npkrt.o` (@@PD-169@@), a call-edge scan from a table of the whole runtime (@@PD-170@@), the refusals judged by `npkc` (@@PD-171@@); **FIXED** in 0.0.3: the `parse` sweep and the `check` stage judged by `npkc`, `accept` struck (@@PD-173@@) |
| NH-11 and G8, the floor and the loops | 0.0.0; 0.0.2 step 1; 0.0.4 | every probe names the floor's six (0.0.0 §1.4); **FIXED** for the harness's templates, the three baseline programs naming the floor's six, with no loop; the planting sweep that every loop of `src/` is reached: **FIXED** in 0.0.4, its block 4l, six loops each reached by a unit, beside its control |
| NH-12 and G13, the containers | 0.0.4 steps 2, 3 | **FIXED**: `Vec<T: Copy>`, which the address types satisfy (probe 12), and `Bytes` (@@PD-177@@) |
| NH-13 and EC7, names and `raw.npk` | 0.0.0 step 2; 0.0.1 step 1; 0.0.3 | **FIXED**: `BUILD.md` §7 measured (@@PD-160@@); `src/option/sockopt.npk` on the eight lines outside the plans and `SK-026` marked (@@PD-165@@); `0.0.3.md`'s own line, re-derived |
| NH-14, `cstring` paths | not this cycle's | no step of cycle 0.0 writes a path parameter; cycle 0.4's `unix_unlink` decides it |
| E2-10, counts against sets | 0.0.0 step 4 | **FIXED** here: `ROADMAP.md`'s and `OPEN_QUESTIONS.md`'s counts dropped. `LIBRARIES.md`'s `nitpick-sockets` row is the workbench's (W-16), the orchestrator's |
| E2-13 and G14, `CURRENCY.md` and the research | 0.0.0 gate item 7; 0.0.1 step 5; 0.0.2 step 3 | **FIXED**: the three requests in 0.0.0 §13; the gate is cycle 0.0's first work dispatch; `CURRENCY.md` and its three research rows (@@PD-168@@); 0.0.2 checks the Python row and LLVM's by content, the latter from its own request (`0.0.2.md` §13) |
| E2-15, `CLAUDE.md`'s empty heading | 0.0.1 step 6 | **FIXED**: the paragraph under "What this is" |
| EC3 and G6, "every public `error:`" | 0.0.0 step 4; 0.0.3 | **FIXED** at its cost sentences (`SAFETY.md`:20, "an identity never raised costs nothing"; `CONTRIBUTING.md`:47, "Every identity this library's code can raise"), measured (@@PD-163@@), with S-8's twins by subject, `src/addr/README.md` and the 1.0 checklist's line; **FIXED** in 0.0.3: `TESTING.md` §5's row and the check, keyed by module and name, and S-8's five-module sentence (@@PD-175@@) |
| ED2, local `O-N` ids | 0.0.0 step 4 | **FIXED**: O-N1, O-N3, O-N4 and the new fifth each say its id is this repository's own |
| G2, CI; EK2 by subject | 0.0.1 step 4; 0.0.2 step 3 | **FIXED** (@@PD-167@@): LLVM asserted, the compiler at the pin and clean, `npkc.ll`'s row, every hex value quoted, and no action to pin; in 0.0.2, the harness step's unqualified green summary, and LLVM's tarball by content — its size and sha256 from a research digest, checked before it is unpacked (@@PD-172@@) |
| G5, one reading of source | 0.0.3 steps 1, 2 | **FIXED**: `harness/lexical.py`, every tree check over blanked bytes with a control naming its banned form in a comment, and every sentence that called a check a grep (@@PD-175@@) |
| G7, the bill from `REACH-003` | 0.0.0 §1.4; cycle 0.2 | measured; `check_failsafe_arms` from cycle 0.2, its oracle named on every run's `later` line |
| G9, refusals their own dispatch | 0.0.0; 0.0.1 step 3 | **FIXED**: `tests/probe/` and `refused/`, and the manifest's `probe` and `probe-refused` |
| G10, transcripts and status | 0.0.0; 0.0.2 | every verdict an Expect from a run; status never through a pipe (0.0.0 §2); the harness prints each exit and code itself, and CI reads its status on its own line (0.0.2) |
| G11, the self-check | 0.0.3 step 1 | **FIXED**: 54 live cases, each beside a control, 1 pending printed as pending (@@PD-174@@) |
| G12, the managed-memory gate | 0.0.0 §1.3; 0.0.2 step 1; 0.0.4 | D-151 sees only `wild`; **FIXED** in 0.0.2: `mem-cap-mib`, after the floor program under the same cap (B-6a, @@PD-171@@); **FIXED** in 0.0.4: `Vec`'s leak pair under D-151, and `Bytes`' buffer under a 64 MiB cap |
| G15, the close | 0.0.5 | **planned**: the first dispatch reports `READY-TO-CLOSE`; the close audit (W-22) runs, and the second dispatch triages it, writes `0.1/0.1.0.md` and archives; each REPORT block committed (W-20) and never edited (W-28), and a verifier before the board moves (W-21); the gate names the audit |
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
| 3 | verification clauses (Z-1, Z-4, Z-5) | settled by 0.0.4's step 2 (@@PD-177@@): Z-1a — an obligation is a comment unless a decision accepts its arm, the live clauses' three arms measured — and Z-4's and Z-5's spellings measured at the pin, each with a dated note; with EK1 |
| 4 | how error detail reaches a caller | not this cycle's (NH-9) |
| 5 | how errno names are declared | settled by 0.0.0: none can be, nor compared but against the prelude's or another error (@@PD-162@@); `check_error_budget` keys every identity a `fail` site raises by (module, name), and a forwarded errno is none (0.0.3, @@PD-175@@) |
| 6 | driving `async` from a probe | settled: `async func:main`, probes 06, 07, 08, 10 |
| 7 | a `fixed uint8[]`'s pointer and length into `sendto` | settled: `wsrc.ptr` and `wsrc.len`, probe 06 |
| 8 | `fd` and `int32` at the reactor | settled: `(o.value) =>! int32`, probes 06 and 07 |
| 9 | `cstring` paths (NH-14) | not this cycle's |
| 10 | `view()` and what `Bytes` is over | settled by 0.0.4's step 2 (@@PD-177@@): `Bytes` over a managed `buffer`, every byte through its checked index (D-341), and no view |
| 11 | is sockets security-sensitive | settled: yes; its three research items gate cycle 0.0's first work dispatch (0.0.0 gate item 7, §13); recorded by 0.0.1 (@@PD-168@@) |
| 12 | where CI sits | settled by 0.0.1 (@@PD-167@@): GitHub's `ubuntu-24.04`, whose loopback CI's first step binds, a currency row its first run checks; no test needs a user namespace; and the `loopback` stage binds it before its first unit, never skipped (0.0.3, @@PD-173@@) |
| 13 | names | settled for 0.0.0 … 0.0.3 (`names.py`, `BUILD.md` §7; 0.0.3's self-check fixtures read too); `NSOCK_*`'s two lists settled by 0.0.4's step 1 (@@PD-176@@): the three bounds a specification states with a value, a fourth with its consumer, five struck |
| 14 | the compiler's stale comments | the orchestrator's to raise (W-27): 0.0.0 §10, §12 |
| 15 | nothing has been run | every block of each file at the pin ran, in plan order, in a stand-in (each file's account of how it was written; `0.0.5.md` §13) |
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
- **The first writing listed `limits.npk`'s bounds twice, and differently**: this README four "and the deadline
  defaults", its 0.0.4.md nine; and that file had `check_constants_named` hold every bound's number off the rest of
  `src/`, where its own specifications state 16 as `SO_PASSCRED` and three structures' size and 50 as `listen`'s
  syscall number: three bounds, held both ways, and a value refused as a literal only where no kernel value shares it
  (@@PD-176@@).
- **`TESTING.md` V-14's self-check had a case for a socket left open at exit, which D-151 was to trap**, where 0.0.0
  measured that it does not: the case is struck, and the self-check is its own list (@@PD-174@@). And the first
  writing's 0.0.3 had its `parse` and `check` stages judged by the compiler's tools "built once per run", where nothing
  here builds the compiler (@@PD-173@@).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| [0.0.0](0.0.0.md) | **The language probes** — twenty programs asking the compiler and the kernel whether the design is spellable, five of them `SK-013`'s and `SK-035`'s | a verdict per probe, the specifications amended by them |
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
- [ ] `probe01_sys_socket.npk`, `probe02_sockaddr_layout.npk`, `probe03_cmsg_layout.npk`, `probe12_pod_addr_array.npk` — the layouts, and `SocketAddr`'s 32 bytes (@@PD-160@@); `refused/probe15_unassigned_read.npk` — a read before a write, `NITPICK-ASSIGN-001` at both reads (A-22's dated note)
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
- [ ] `src/core/limits.npk` — the three bounds a specification states with a value, each beside its rule, and `check_constants_named` holding the file to them both ways (@@PD-176@@)
- [ ] `src/core/vec.npk` — `Vec<T: Copy>`, every accessor at `0`, `count - 1` and `count`, a misuse trapping `OutOfBounds`; every generic instantiated by `tests/unit/generic_instances.npk`, whose emission build step 2 scans (@@PD-177@@)
- [ ] `src/core/bytes.npk` — `Bytes`, every byte through its buffer's checked index and no view (D-341), `put_uint` by subtraction, a million bytes in twenty reallocations (@@PD-177@@)
- [ ] every obligation a comment in the syntax it would take, compiling live, with a unit standing in (`VERIFICATION.md` Z-1a); each mutant red by what guards its facet; every loop of `src/` reached by a unit (G8)

### 0.0.5 — close
- [ ] every probe verdict of `0.0.0.md` §6 reconciled against the specifications **by reading them**, probe 04 and the set 09, 09b, 10 and 10b by name
- [ ] three permanent files cite a decision or nothing where they cited a cycle file's section (T7v2's F5); the sweep's candidates and the citations read
- [ ] the cycle's findings written as a numbered list; a full green run, its output quoted, and the census of every program; `READY-TO-CLOSE`
- [ ] the close audit run (W-22) and triaged, every finding fixed or declined with its reason
- [ ] `0.1/0.1.0.md` written execution-grade before the cycle closes, its gate naming the three research digests with their dates
- [ ] cycle moved to `done/0.0/`, `ROADMAP.md`, `README.md` and `CLAUDE.md` updated, `check_refs` clean, the record checked

## Gate

**The cycle is complete when**: every probe has a recorded verdict, its consequences written into the specifications —
**with probes 04, 09, 09b, 10 and 10b recorded against `SK-013` and `SK-035`**; a full `harness/run.py` is green; the
self-check proves the harness fails in every live way it names and reports the pending ones as pending; and
`src/core/` has its suites. **And a close audit (W-22) that has seen the tree it accepts**: the close's worker triages
every finding it reports, the close's REPORT block is committed (W-20) and never edited (W-28), and a verifier re-runs
it before the board moves (W-21). A gate written as a list of green things is one a green run meets: `nitpick-regex`'s
cycle 0.0 met every other clause of its gate at a close its audit refused (its `meta/roadmap/done/0.0/README.md`).

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
  traps under D-151 — which sees `wild` bytes and nothing else: not a descriptor (0.0.0 §1.3), and not a `buffer`, which
  `Bytes`' leak unit holds under a memory cap (0.0.4).

## Fix rounds 2 and 3: the two checks' record

**Fix round 2** (T7fix2, 2026-10-25) answered the final plan verification's findings 1, 2, 3, 4, 5, 6, 9 and 13 at
their sources, and built the two checks its rulings asked for. Both are kept in [`tools/`](tools/), so any later pass
re-runs them at its tip: (a) `lines.py`, every file:line citation of the plan resolved against the tree it names, and
(b) `twins.py`, every correction's twins swept by the exact strings it changed. Each has a `control`, which plants the
cases it must catch and the cases it must not, and a `run`, which prints its denominator; **`run` does not run its
control**, so a later pass runs both, control first, as the block below lists them. Both skip this section by its
heading. In a clone outside the workbench each takes `--wb <workbench>
--npk <compiler clone>`. Beside the exact strings, 0.0.4's sweep gains the subject *what the call-edge scan reads*,
with its twin, and 0.0.5's first subject reads every line that cites a cycle file's plan, section, gate item, step or
block. **A word pattern finds a claim only in the words it spells, and cannot find an other-worded twin of it**: that
is why the exact-string sweep (b) exists beside the patterns, and why each pattern is proved on a twin line that
plants one other wording, no more (`tools/sweep.py`, and the header of each `sweep_patterns.txt`).

```text
python3 -B meta/roadmap/0.0/tools/lines.py control "$REPO"
python3 -B meta/roadmap/0.0/tools/lines.py run "$REPO"
python3 -B meta/roadmap/0.0/tools/twins.py control "$REPO"
python3 -B meta/roadmap/0.0/tools/twins.py run "$REPO"
```

**The exit statuses, one meaning each, which a later pass reads: it never reads the printed tally alone.** `lines.py`:
0, every citation resolves and holds; 1, a HIT, a STOP (a command it runs fails, or a step's patch does not apply to
the tree it builds) or, from `control`, a check that failed; 2, a usage error. `twins.py run`: 0, every hit EARLIER or LOG; 1, a stop
— an UNCLASSED hit, a data file not in its form, or, from `control`, a check that failed; 2, a usage error; 3, a hit
classed STALE and none UNCLASSED — a text the plan fixed at its source has come back, or `--before` found the sites a
round fixes. A STALE hit beside an UNCLASSED one is 1, and the counts say both. `control` exits 0 when every check holds
and 1 when one fails, and plants each case it proves.

**(a) The citation check.** Round 2's control planted 13 sound citations, one per form and the pin's O-N3 comment, and
each held. It planted 7 stale or empty ones, and each was a HIT (round 3's plants more: below). It reads 61 files of the
plan: the subcycle files, this README, every patch's added and context lines, and every tool. The checks' data and the
other tools' planted and clean files are skipped by name.

- **At the round's base, `fd47ba3`**, with the final tools copied in, it finds 402 citations: `path:N` 263, "line N of
  path" 2, "`path`'s line N" 4, a named file's line 5, `path` N in the sweep tables 128, and a bare `:N` 0. 257 of
  them are in fenced blocks, which `blocks.py compare` resolves when the blocks run. Of the 105 resolved here (45 of
  them sweep-table rows), 57 hold and **48 are HITs**. Each was fixed at its source:
  - *the line no longer holds its text*, 10: O-N3's note in 0.0.0's `step1.patch` and `step4.patch`, and the landing
    127 row, at `types.npk:1733`, blank at the pin (finding 1, the positive control the plan held); the SL-5 row's
    five sites, which moved at 0.0.4's step 2; EC3's `CONTRIBUTING.md`:46, blank there; and `0.0.3.md` §6's
    `TESTING.md` 197, whose two matches on one line the row counted once;
  - *the sentence names nothing its line holds*, 34: `0.0.0.md` §1's O-N3 lines (2), `0.0.1.md` §8's SL-5 sites (4),
    `0.0.4.md` §11's SL-5 row (4), `0.0.5.md` §1.2's nine lines (7), §1.5's three (2) and §5's sites and citations
    (13), and this README's E2-10 and EC3 rows (2). Each now quotes or names what its line holds;
  - *no tree, or two*, 4: `0.0.0.md` §11's bare `types.npk`, which ends two of the compiler's files; `0.0.4.md` §2's
    two exit codes, read as lines; and the landing 128 row's line of `nitpick-time`'s file, with no commit named,
    dropped.
- **At round 2's tip, `5862558`,** it found 425 citations: `path:N` 278, "line N of path" 2, "`path`'s line N" 3, a named
  file's line 8, `path` N 134, and a bare `:N` 0. 273 of them were in fenced blocks. Of the 94 resolved here (49
  sweep-table rows), **94 held and none was a HIT**.

**(b) The twin sweep by exact strings.** At round 2's tip its table, `tools/twins.tsv`, held 118 rows from 16 commits.
Each row gives a correction's old string exactly as it was removed, the new one, and the commit that made it: T7fix1's,
T7a's, T7c4's dated lines, T7c4b's, T7c5's, the verification's (12), and round 2's own (`fd47ba3..`, or the step that
makes it). Its classes, `tools/twins_classes.txt`, class each hit STALE (a twin a round fixes at its source, found only
before the fix), EARLIER (a statement about an earlier cut, said as such, or a tree before the step that corrects it)
or LOG (a record the decision log keeps by its rule). An UNCLASSED hit is a stop. Round 2's control: the provenance of
115 rows of 115 held, each old string more often before its commit than at it, and 3 rows name no commit, each saying
why; a planted twin is found and its correction is not; and the classes' self-test reads 6 of 6 as planted. It sweeps
the plan's 46 files at the tip, the 21 patches' added and context lines, and the distinct file texts of the six trees
the subcycles leave, 217 at `fd47ba3` and 219 here. It also reads the decision log's lines that cite a cycle file's
section, by 0.0.5's first sweep subject. **Its scope is what a correction removed.** A passage a correction leaves
understated, by an addition that says more than the passage does, has no old string to find: it needs a check of its own
or a reviewer's eye, and the table takes its row by hand when one is found (fix round 3's B-2 drawing, the call-edge
clause that 0.0.4's step 2 extends to one test).

- **At `fd47ba3`** (`run --before`) it finds 108 hits:
  - **STALE 61**, every one a site this round fixed at its source: finding 1's O-N3 note and its twins 11, finding 2's
    call-edge scan and the counts its mark moves 15, findings 3 and 4's counts 4, finding 5's member dot 3, finding
    6's loops 5, finding 9's patch names 7, check (a)'s citations 14, 0.0.0's moved sweep site 1, and the plan
    folder's file count 1;
  - EARLIER 35;
  - LOG 36, 24 of them the log's section citations read through `fd47ba3`'s own pattern. Those are T7v3's 24, which
    missed 669 and 823 … 824 (finding 4);
  - UNCLASSED 0.
- **At round 2's tip, `5862558`,** it found 50 hits and 29 section citations. **STALE 0, UNCLASSED 0**, and each kept hit
  by its row (round 3's table, below, has one row more):

| Row, its old string | Class | Hits |
|---|---|---|
| "owes exactly one arm" | LOG | 6: @@PD-163@@'s account of S-8, in 0.0.0's `step4.patch` and the log of each tree |
| "which cycle 0.0.4's `Vec<T>` will be" | LOG | 6: @@PD-175@@'s forecast under its dated note, in the patches and trees that carry it, and `0.0.4.md` §7 |
| the log's lines that cite a cycle file's section | LOG | 29 on 28 lines: `0.0.5.md` §5's first row, and §14's author item |
| "LLVM 20.1.2" | EARLIER | 8: the setup-era manifest, as history — `0.0.1.md`, this README's opening, 0.0.1's sweep pattern, and `CLAUDE.md` and `README.md` before 0.0.1 |
| "notice 118" | EARLIER | 1: `0.0.1.md`, the old pin's row until the adoption |
| the three section citations 0.0.5's step 2 replaces | EARLIER | 14: `0.0.5.md`'s account of them, `citations.py`'s planted form, and the patches and trees before 0.0.5's step 2 |
| npkc's usage at `c9baa9e` | EARLIER | 3: @@PD-173@@'s text, in its patch and trees, with its dated note |
| "No library code exists yet" | EARLIER | 2: 0.0.1's sweep pattern, and `CLAUDE.md` before 0.0.1's step 6 |
| the call-edge scan's reading, as 0.0.2 wrote it | EARLIER | 10: 0.0.2's and 0.0.3's patches and trees, before 0.0.4's step 2 |

**Fix round 3** (T7fix3, 2026-10-28) answered the deferred findings of T7v4 and T7v3 that the libraries' seat ruled into
it, each at its source, and changed the two checks and five tools beside them. What follows is the checks and tools as it
left them, and their output at its tip; the figures above are round 2's. Each tool below exits non-zero on everything it
reports as wrong, and each control plants a case the old code got wrong. It sits under round 2's heading, as one
section: `lines.py` reads each heading afresh, so a heading inside the record would end its skip.

- **(a) `lines.py`.** The commands are the block's, the exit statuses as above. It reads a capitalised `Line N of path`,
  `Its line N`, `Probe NN's line N` and `The X.Y roadmap's line N` as it reads the lower-case forms; its pattern matched
  lower case only, and read none of the four in the plan. Its control plants 17 sound citations (the 13, and the four
  capitalised) and 10 stale or empty ones (the 7, and three capitalised): each sound one is found and holds, each stale
  one is a HIT. At this tip it reads the same 61 files and finds the same 425 citations by the same forms, since the
  plan holds no capitalised one: 94 resolved here (49 sweep-table rows), **94 hold and none is a HIT**, exit 0.
- **(b) `twins.py`.** The commands are the block's, the exit statuses as above, with 3 for a STALE hit and no UNCLASSED
  one. Its control plants, beside round 2's, the four statuses a `run` can give, through the functions `run` reports
  with, and a README of four lines whose record's heading is the third. Each is as planted: **exit statuses 4 of 4** (a
  restored stale text 3, an unclassed hit 1, a classed earlier one 0, a stale hit beside an unclassed one 1; the old code
  gave 0 for the first), **the record's range 3–4** (the old code read 3–5, one line past the file), the provenance 139
  of 139 rows with 3 naming no commit, a planted twin found and its correction not, and the classes 6 of 6. Its table
  holds 142 rows from 17 commits: round 3 adds 23 rows, `5862558..`, each a correction's old string taken from its diff
  (a2 5, a3 2, b1 3, b2 5, c3 1, c4 5, c5 1, c8 1), and a2's `step:0.0.4/2` row for B-2's drawing in `BUILD.md`, which
  0.0.4's step 2 extends to one test. The denominator is as above: 46 plan files, 21 patches, 219 file texts.
  - **At `5862558`** (`run --before`, the final tools copied into a clone there) it finds 94 hits, exit 3: **STALE 41**,
    each a site this round fixes at its source (a2 6, a3 2, b1 8, b2 12, c3 1, c4 7, c5 4, c8 1), EARLIER 41, LOG 41
    (29 of them the log's section citations), UNCLASSED 0.
  - **At this tip** it finds 53 hits and 29 section citations on 28 lines, exit 0: **STALE 0, UNCLASSED 0**. The 23 new
    rows have no hit, so no twin of what round 3 removed survives anywhere the plan's text reaches. Each kept hit, by its
    row (round 2's table, and one row more):

| Row, its old string | Class | Hits |
|---|---|---|
| "owes exactly one arm" | LOG | 6: @@PD-163@@'s account of S-8, in 0.0.0's `step4.patch` and the log of each tree |
| "which cycle 0.0.4's `Vec<T>` will be" | LOG | 6: @@PD-175@@'s forecast under its dated note, in the patches and trees that carry it, and `0.0.4.md` §7 |
| the log's lines that cite a cycle file's section | LOG | 29 on 28 lines: `0.0.5.md` §5's first row, and §14's author item |
| "LLVM 20.1.2" | EARLIER | 8: the setup-era manifest, as history — `0.0.1.md`, this README's opening, 0.0.1's sweep pattern, and `CLAUDE.md` and `README.md` before 0.0.1 |
| "notice 118" | EARLIER | 1: `0.0.1.md`, the old pin's row until the adoption |
| the three section citations 0.0.5's step 2 replaces | EARLIER | 14: `0.0.5.md`'s account of them, `citations.py`'s planted form, and the patches and trees before 0.0.5's step 2 |
| npkc's usage at `c9baa9e` | EARLIER | 3: @@PD-173@@'s text, in its patch and trees, with its dated note |
| "No library code exists yet" | EARLIER | 2: 0.0.1's sweep pattern, and `CLAUDE.md` before 0.0.1's step 6 |
| the call-edge scan's reading, as 0.0.2 wrote it | EARLIER | 10: 0.0.2's and 0.0.3's patches and trees, before 0.0.4's step 2 |
| B-2's drawing in `BUILD.md`, as 0.0.2 wrote it | EARLIER | 3: 0.0.2's `step1.patch` and the trees of 0.0.2 and 0.0.3, before 0.0.4's step 2 extends its clause to one test |

- **`tools/rulings.py`** (0.0.0's block 0b): `python3 -B rulings.py [--sites] <file>...`, and `--selftest`. It reads a
  module-level binding by the qualifier its line leads with (`fixed`, `const`, `wild`, `wildx`, `stack` or none), and
  STOPs, printed last, on a binding-shaped line at depth 0 led by any other word (an attribute, `limit<…>`, a second
  qualifier, `nodrop`, `move`, `sealed`, a type it does not spell) and on a file it cannot read. Exit 0: every such line
  was read; 1: a STOP. The old reader counted neither `wild int8->:g3;` nor a `stack` binding, and said nothing.
  `--selftest` (exit 0, or 1 when one is not as planted) plants 17 bindings, 7 unread forms, 5 places where none fires
  and an unreadable file, and reads 17 of 17, 7 of 7, 5 of 5 and the file's STOP with `main`'s status 1; the block
  prints its exit. Denominator: the 19 `.npk` files the patches add, 132 bindings and no STOP. Over the compiler's 1084
  `.npk` files at `2e1cb4a` it counts 6 bindings with no initialiser (the old reader 5), 2 `stack` ones (old 0), and
  stops on 5 lines, each a form it does not read: `nodrop fixed` and `move fixed` (`tests/analysis/rejection/moves.npk`:123
  and :147), `fixed int32[#three()]` (`tests/backend/programs/macro_walk_positions.npk`:47), `fixed sealed`
  (`tests/types/rejection/field_qual_position.npk`:25) and `fixed wild` (`tests/types/rejection/null_plain_pointer.npk`:45).
- **`0.0.4_tools/obligations.py`** (0.0.4's block 0b): `python3 -B obligations.py <npkc> <scratch dir> <module.npk>...`.
  It reads each `// obligation:` comment strictly (the clause, its continuations indented ten columns or more, then a
  bare `//` or the function's head, which ends `never fails {`), and a line it cannot place is a STOP by name, before
  anything is compiled: the old reader dropped a continuation indented under ten columns, so a count could read "12;
  compile: 12" with a clause cut short. Exit 0: every obligation compiles live; 1: npkc refuses one, a STOP, or a control
  failed; 2: a usage error. Its controls run first, on every run: the reader 10 of 10 (a sound clause with its
  continuation read, and nine planted forms, each a STOP) and the compile 2 of 2 (a sound planted obligation compiles
  live; one naming `resultz` is refused, `NITPICK-RESOLVE-002`). Denominator: `vec.npk` and `bytes.npk`, 24 of 24
  compile live, no STOP.
- **`tools/apply.py selftest`** (0.0.0's block 0a): exit 0 when each case is as planted, 1 when one is not. A dated
  context line it cannot read to one date is a STOP by its own name: `nowhere`, `with more than one date` (on two lines)
  or `with two different dates on the one line` (the old code called that one `nowhere`). It plants 6 cases in a temp
  dir, and reads 6 of 6: a date, one date twice on a line, each of the three STOPs, and a missing line left as it is when
  not strict.
- **`research_fresh`, in `tools/env.sh`** (each subcycle's block 0a): `research_fresh <name or path>...` prints each
  digest's `As of` line and heading, then `digests within 90 days of today: N of M`, and returns 0 when N is M and
  non-zero when a digest is stale or has no date (a security digest is stale after 90 days, the research skill; exactly 90
  is fresh). The comparator masks dates, so the old loop could not DIFF on a stale digest; the count line can. Controls,
  in 0.0.0's block 0a: a copy 90 days old reads 1 of 1, exit 0; one 91 days old, 0 of 1, exit 1; one with no `As of`
  line, 0 of 1, exit 1. Denominator: 3 of 3 digests in 0.0.0 and 0.0.1, 4 of 4 from 0.0.2.
- **`harness/stages.py`**, by 0.0.3's `step1.patch`: the sweep skips `.git`, `build` and `.internal` only directly under
  the entry's path (@@PD-173@@'s "So" paragraph says "the entry's own"). Its self-check case `parse-not-parsing` plants
  its hit under `sub/build/`, which the old filter, skipping the name at any depth, passed with 0 files swept; the case
  count is unchanged, and the Expect of 0.0.3's block 1 and 0.0.4's blocks 1, 2 and 3 are retaken.
- **`tools/blocks.py`, `tools/sweep.py` and each `sweep_patterns.txt`**: documentation only. `blocks.py`'s docstring
  names the comparator's masks (seconds, free memory, dates whatever they say, `check_refs`'s counts, the white space at
  a line's end on both sides) and the `# (any)` line; `sweep.py`'s docstring and each header say a word pattern cannot
  find an other-worded twin.
- **Left for 0.0.0's execution**: `STREAM_MODEL.md`:143's `EMFILE|ENFILE`, which sockets' own question N-5 renames
  `TooManyOpenFiles|FileTableFull`. 0.0.0's block 6 reads the line, and a scratch sweep with the rename moves its "an
  unnamed errno compared" count from 20 to 18 and its §7 row; step 4's dated note under T-12 names the same errno rows. Round (i) took
  it instead, below.

**Round (i) of 0.0.0's amendments** (T15, continued by T15c, 2026-10-29) answered the libraries' seat's ruling (1):
the seven checks that printed a finding and exited 0 now exit non-zero on everything they report as wrong, one meaning
per status, and each has a planted control that the old code passed with 0 and the new one refuses. **A later pass
reads each status, never the printed tally alone.**

- **`tools/names.py`**: 0, no declared name is a keyword; 3, a keyword-named declaration, each listed; 1, a STOP — a
  missing argument or a file it cannot read. 0.0.0's block 0b (§1.7) prints the statuses of its planted and clean
  controls: 3 and 0, where the old code gave 0 and 0.
- **`tools/pointers.py`**: 0, every rule the added lines cite is defined and every section they cite resolves; 3, one
  does not, named on its `undefined:` or `sections that do not resolve:` line; 1, a STOP — a missing argument, a tools
  dir holding no `step*.patch`, or a file it cannot read. It had no control: 0.0.0's block 0b (§1.9) plants a patch
  citing `Z-99` and `STREAM_MODEL.md` §99, which exits 3 (the old code 0), and one citing S-1 and `SAFETY.md` §1, which
  exits 0.
- **`tools/shapes.py`**: 0, no shape a plan must not write; 3, one, by its count; 1, a STOP — no file given, or a file
  it cannot read. The four it lists for reading are not findings: an attribute, an `exit` operand, a plain `uint8[]`
  and `#ptr_add`. It no longer reads a `mod:` line's name as a builtin named, not called: `mod:sys;`, a module's name,
  was that shape's 1 line in 0.0.1's added files and its 16 in the self-check's fixtures, so the line leaves 0.0.1's
  block 0b, 0.0.3's block 1 and 0.0.4's block 3; its clean control gains a `mod:sys;` line, which the old code counted
  as the shape. 0.0.0's block 0b (§1.6) prints the statuses of its planted and clean controls: 3 and 0, where the old
  code gave 0 and 0.
- **`0.0.2_tools/mutants.py`, `0.0.3_tools/mutants.py` and `0.0.4_tools/mutants.py`**: 0, every row ended its way — the
  unchanged tree and each control the other way GREEN (0.0.2's `library-shapes-allowed`, 0.0.3's
  `network-unit-skipped`; 0.0.4 has none), every other mutant red; 3, one did not: a mutant that must be red exited 0,
  so it survived, or a GREEN row was red; 1, a STOP, a mutant not made and not run, which outranks a 3, or an error the
  tool does not catch. Each has a `selftest`, which its block (0.0.2's 4m, 0.0.3's 3m, 0.0.4's 4m) runs first: it
  plants the outcome sets through the function `main` reports with, a survivor, a red GREEN row, a STOP and a STOP
  beside a survivor among them, and reads each status as planted, where the old code returned 0 for every set.
- **`tools/sweep.py`**, by the libraries' seat's D2: `run` exits 0 when it has listed the candidates, and **0 means
  listed, never clean**. A candidate is not a finding (`0.0.0.md` §4's step 6): the plan's sweep table gives each its
  verdict, and the block's Expect holds every candidate line, so a new or a lost one is a DIFF, and a DIFF is a stop.
  `run`'s last line counts them, `listed: <n> candidate(s) from <m> pattern(s)`, and `control` prints its plant's
  line, so each subcycle's sweep block gains those two lines. Both modes exit 1 on a STOP: a missing argument, where
  the old code exited 2; or an input they cannot read — a root that is not a checkout's top, where the old code listed
  nothing or a part and exited 0 (over a tree exported without its `.git`: 0 files, every pattern 0, exit 0), or a
  patterns file missing, holding no pattern or holding one the transform makes unmatchable. `control` exits 0 when
  every check holds and 1 when one fails, and plants the root that is not a checkout's top, its `meta/`.
- **`tools/lines.py`** keeps its code (T7v5's finding 1): its 1 has three causes, a HIT, a STOP and a failed control,
  which its docstring and the exit statuses above now name.

Its second commit made the rename sockets' own question N-5 asked for, with the names the compiler settled
(nitpick-libs_27's ruling of 2026-10-25): `STREAM_MODEL.md`:143, T-12's sketch, reads `TooManyOpenFiles|FileTableFull`
where it read `EMFILE|ENFILE`, its arrow at column 47, and stays spec text, since no `.npk` names the five before
DEF-286's re-pin reaches sockets. Step 4's dated note under T-12 names the two new identities beside `ConnAborted` as
none the prelude declares at the pin, a line longer. 0.0.0's block 6 loses T-12's two `EMFILE|ENFILE` candidates, "an
unnamed errno compared" going from 20 to 18 and its `listed:` total from 54 to 52, so its Expect is retaken, 104 lines
to 102, and §7's count and row move with it; the other five sweeps read the same. No hunk of any patch carries
`STREAM_MODEL.md`:143 as context.

Its third commit carried the research gate's rulings (the libraries' seat's entry of 2026-10-29, and its D1 and D3 that
day): every finding of the three digests is held where its subject is decided, and the two that ask the language a
question are probes of 0.0.0. No decision is taken.

- **`ADDRESS_MODEL.md`**: A-19's refusal table gains `010.0.0.1` and `1.2.3.04`, the spellings where it and
  POSIX.1-2024 part, and its sentence names the behaviour, glibc's `inet_pton` (measured at 2.39) and RFC 3986's
  `dec-octet`, deliberately stricter than POSIX (Austin Group Defect 1573). A-20 reads its dotted-quad tail by A-19's
  rules, so `::ffff:010.0.0.1` is refused. `SK-036` takes a dated note, its text unchanged.
- **`ANCILLARY_MODEL.md` N-19**, at the end of §2: the `cmsghdr` walk checks before it subtracts. Its lengths are
  `uint64`; a header shorter than 16 bytes or longer than what remains is `ESockProtocol`; the step is
  `min(align8(cmsg_len), rem)`; and an empty final header is visited, then refused.
- **`TESTING.md`**: V-9 gains A-20's and A-13's cases, each beside the boundary it must still accept, and V-12's
  `cmsghdr` reader five fixed buffers, each with its verdict. A-19's two new rows need none of their own: V-9 makes
  every spelling in its table a test.
- **0.0.0**: P1' is §1.4's `payload_len(15u64)`, a `uint64` subtraction below zero, `IntOverflow` (exit 93) at both
  legs, since the language has no `usize`. P3' is probe 15, the next number in the probe scheme, at step 2:
  `tests/probe/refused/probe15_unassigned_read.npk` reads an element of a local `uint8[16]` and of a struct's
  `uint8[108]` field before anything writes them, and both reads are `NITPICK-ASSIGN-001`, so the language closes the
  gate's D3 and A-22 takes a dated note; step 2's text gives the other branches. Block 0a prints each digest's sha256,
  and §10 hands the gate's currency rows to `CURRENCY.md` when 0.0.1 is re-cut (D1).

Its fourth commit cut 0.0.0 into runs (the libraries' seat's ruling (iii)), on `nitpick-parse` 0.0.2's model: six
runs, each a fresh worker — run 1 the research gate's commit and step 0, runs 2 … 5 steps 1 … 4 one each, run 6 steps
5 and 6 — each step committed and pushed with its entry in the execution record, which is its hand-off (`0.0.0.md`
§0). The title is committed with step 0's entry, so no run leaves the tree dirty for the next. The run's date file,
which `apply.py` writes at step 1 and reads at steps 2 … 4, is kept between runs and removed at step 5, which sets the
title `DONE`; step 6 sweeps after step 5's commit and closes the record with the REPORT block and this file's 0.0.0
boxes, whose step-2 box now names probe 15. No block's command or Expect moved, and 0.0.0's blocks read `SAME` with
the runs' commits.
