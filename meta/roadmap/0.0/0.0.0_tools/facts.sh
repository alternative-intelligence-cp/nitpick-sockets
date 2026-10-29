# meta/roadmap/0.0/0.0.0_tools/facts.sh -- re-derives `0.0.0.md` §1, block 0b. Sourced after `../tools/env.sh`, so
# `$REPO`, `$A`, `$NPKC`, `$NPKRT`, `$NPK_TREE`, `$PIN` and the helpers are set. Writes only under `$A/facts`, and
# removes it. Reads the compiler's tree with `git show` alone.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T0=$REPO/meta/roadmap/0.0/0.0.0_tools
TL=$REPO/meta/roadmap/0.0/tools
show() { git -C "$NPK_TREE" show "$1"; }

# §1.1 -- the tree it starts from
echo "§1.1 tests/probe holds: $(git -C "$REPO" ls-files tests/probe | tr '\n' ' ')"
echo "§1.1 decisions: $(grep -c '^### SK-' "$REPO/meta/DECISIONS.md") headings, the highest by value $(grep -o '^### SK-[0-9]*' "$REPO/meta/DECISIONS.md" | sort -t- -k2 -n | tail -1 | cut -c5-)"

# §1.2 -- the compiler's own text that the patches cite, read at the pin
echo "§1.2 at $PIN, npkrt.ll installs SIGPIPE's handler: $(show $PIN:runtime/npkrt.ll | grep -c 'call i64 @npk_sys6(i64 13, i64 13, i64 %ap, i64 0, i64 8, i64 0, i64 0)') call, flags $(show $PIN:runtime/npkrt.ll | grep -m1 -oE 'store i64 469762048, ptr %a1'), handler $(show $PIN:runtime/npkrt.ll | grep -A2 -E '^define internal void @npk_pipe_handler' | grep -c 'ret void') returning"
for c in 3d15ac9 c3bdae2; do echo "§1.2 at $c, npkrt.ll's rt_sigaction mentions: $(show $c:runtime/npkrt.ll | grep -c rt_sigaction)"; done
# the commit that brought SIGPIPE's handler: none in its parent, the handler in it, and its subject
echo "§1.2 npkrt.ll's npk_pipe_handler mentions: $(for c in 3d15ac9 b7244d2f^ b7244d2f c3bdae2 $PIN; do printf 'at %s %s; ' "$c" "$(show $c:runtime/npkrt.ll | grep -c npk_pipe_handler)"; done)b7244d2f is $(git -C "$NPK_TREE" show -s --format=%s b7244d2f | grep -oE '^1\.5\.8 step 3: THE LAST NET \(D-307; DEF-68 fixed\)')"
echo "§1.2 at $PIN, runtime/ against 7e91730: $(git -C "$NPK_TREE" diff 7e91730 $PIN -- runtime/ | wc -l) line(s) of diff"
echo "§1.2 at $PIN, nbridge.npk: $(show $PIN:lib/nbridge.npk | grep -m1 -oE 'socketpair whose peer died raises SIGPIPE, which terminates the') | $(show $PIN:lib/nbridge.npk | grep -m1 -oE 'unwrap-or-TRAP: right in a test.s main, wrong in this tier')"
echo "§1.2 at $PIN, types.npk:1756: $(show $PIN:src/frontend/types.npk | sed -n '1756p' | sed -E 's/^ +//')"
echo "§1.2 at $PIN, the prelude's named errnos: $(show $PIN:src/prelude/prelude.npk | grep -oE '^pub error:(WouldBlock|Interrupted|NotFound|Exists|CrossDevice) = [0-9]+i32;' | tr '\n' ' ')"
echo "§1.2 at $PIN, the prelude's Writer: $(show $PIN:src/prelude/prelude.npk | grep -m1 -oE 'async func:write = int64\(Self->:self, fixed uint8\[\]:wsrc, Duration:within\);')"
show $PIN:src/frontend/keywords.npk > "$F/keywords.npk"
echo "§1.2 at $PIN, keywords.npk: $(grep -oE 'string_eq\(text, "[^"]+"\)' "$F/keywords.npk" | sort -u | wc -l) words, $(git -C "$NPK_TREE" diff 7e91730 $PIN -- src/frontend/keywords.npk | wc -l) line(s) of diff against 7e91730"

# §1.3 -- three shapes measured in scratch: a prelude name declared again, a module named `raw`, and a socket left
# open at a clean exit
fs='func:failsafe = int32(Error:e) {\n    pick (e) {\n        (HeapBadRequest) { exit 91i32; },\n        (HeapOom) { exit 92i32; },\n        (Unreachable) { exit 95i32; },\n        (WildLeak) { exit 96i32; },\n        (StackExhausted) { exit 106i32; },\n        (MachineFault) { exit 107i32; },\n        (*) { exit 99i32; }\n    }\n    exit 9i32;\n};\n'
printf "mod:prelude_name;\n\nfixed int64:O_CLOEXEC = 524288i64;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n\n$fs" > "$F/prelude_name.npk"
mkdir -p "$F/raw"; printf "mod:raw;\n\npub func:level = int64() never fails {\n    pass 1i64;\n};\n" > "$F/raw/raw.npk"
printf "mod:open_at_exit;\n\nfunc:main = int32(cstring[]:_~argv) {\n    Result<int64>:r = sys(41i64, 2i64, 526337i64, 6i64);\n    if (r.is_error) { exit 10i32; }\n    exit 0i32;\n};\n\n$fs" > "$F/open_at_exit.npk"
echo "§1.3 $(codes "$F/prelude_name.npk")"
echo "§1.3 $(codes "$F/raw/raw.npk")"
echo "§1.3 a socket left open at a clean exit: $(run4 "$F/open_at_exit.npk" | sed 's/^open_at_exit: //')"

# §1.4 -- what a consumer of each module shape owes: NITPICK-REACH-003, the compiler as the oracle
mkdir -p "$F/bill"
printf '%s\n' 'mod:forward_shape;' '' 'pub func:close_descr = int64(int64:descr) {' '    Result<int64>:r = sys(3i64, descr);' \
  '    if (r.is_error) { fail r.err; }' '    pass r.value;' '};' > "$F/bill/forward_shape.npk"
printf '%s\n' 'mod:identity_shape;' '' 'pub error:ESockAddr;' 'pub func:port_check = int64(int64:port) {' \
  '    if (port > 65535i64) { fail ESockAddr; }' '    pass port;' '};' > "$F/bill/identity_shape.npk"
printf '%s\n' 'mod:private_shape;' '' 'error:ESockState;' 'pub func:once = int64(int64:n) {' \
  '    if (n > 1i64) { fail ESockState; }' '    pass n;' '};' > "$F/bill/private_shape.npk"
printf '%s\n' 'mod:unraised_shape;' '' 'pub error:ESockCapacity;' 'pub func:same = int64(int64:n) never fails {' \
  '    pass n;' '};' > "$F/bill/unraised_shape.npk"
printf '%s\n' 'mod:decoder_shape;' '' 'pub func:family_of = int64(fixed uint8[]:src) never fails {' \
  '    if (src.len < 2i64) { pass 0i64 - 1i64; }' '    pass (src[0i64] => int64) | ((src[1i64] => int64) << 8i64);' '};' \
  '' 'pub func:payload_len = uint64(uint64:cmsg_len) never fails {' '    pass cmsg_len - 16u64;' '};' \
  > "$F/bill/decoder_shape.npk"
printf '%s\n' 'mod:wait_shape;' '' 'pub async func:readable = NIL(int32:descr) {' \
  '    Result<NIL>:w = await io_ready(descr, 1i32, raw duration_ms(10i64));' '    if (w.is_error) { fail w.err; }' \
  '    pass NIL;' '};' > "$F/bill/wait_shape.npk"
for m in forward_shape identity_shape private_shape unraised_shape decoder_shape wait_shape; do echo "§1.4 $(bill "$F/bill/$m.npk")"; done
# ... and the research gate's P1': the decoder's `uint64` subtraction below zero, `cmsg_len - 16` for a `cmsg_len` of 15,
# traps as `IntOverflow` -- the failsafe's 93 -- at both legs; a wrap would exit 11 (`ANCILLARY_MODEL.md` N-19)
printf '%s\n' 'mod:payload_15;' '' 'use "./decoder_shape.npk".*;' '' 'func:main = int32(cstring[]:_~argv) {' \
  '    uint64:n = raw payload_len(15u64);' '    if (n == 0u64) { exit 10i32; }' '    exit 11i32;' '};' '' \
  'func:failsafe = int32(Error:e) {' '    pick (e) {' '        (HeapBadRequest) { exit 91i32; },' \
  '        (HeapOom) { exit 92i32; },' '        (IntOverflow) { exit 93i32; },' '        (OutOfBounds) { exit 94i32; },' \
  '        (Unreachable) { exit 95i32; },' '        (WildLeak) { exit 96i32; },' '        (StackExhausted) { exit 106i32; },' \
  '        (MachineFault) { exit 107i32; },' '        (*) { exit 99i32; }' '    }' '    exit 9i32;' '};' > "$F/bill/payload_15.npk"
echo "§1.4 a uint64 subtraction below zero, payload_len(15u64): $(run4 "$F/bill/payload_15.npk" | sed 's/^payload_15: //')"

# The patched tree: the five steps applied to a throwaway clone of HEAD, which §1.5 to §1.9 read
d=$A/facts/tree; rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
for s in 1 2 3 4 5; do python3 -B "$TL/apply.py" "$d" 0.0.0 $s > /dev/null; done

# §1.5 -- probe 04's power, in three mutants of it: under the default disposition its leg 4 sets, that leg's send with
# no flags dies by signal 13, and so does the floor's `write` in the send's place; and the probe started under the
# default disposition, as a runtime with no handler leaves it, exits 11 in its first leg, before any send
sed -e 's/^mod:probe04_sigpipe;/mod:probe04_mutant;/' \
  -e 's/Result<int64>:r4 = sys(SYS_SENDTO, a, one, 1i64, MSG_NOSIGNAL, 0i64, 0i64);/Result<int64>:r4 = sys(SYS_SENDTO, a, one, 1i64, 0i64, 0i64, 0i64);/' \
  "$d/tests/probe/probe04_sigpipe.npk" > "$F/probe04_mutant.npk"
echo "§1.5 probe 04's leg 4 with no flags: $(grep -c 'r4 = sys(SYS_SENDTO, a, one, 1i64, 0i64' "$F/probe04_mutant.npk") line(s) changed; $(run4 "$F/probe04_mutant.npk" | sed 's/^probe04_mutant: //')"
sed -e 's/^mod:probe04_sigpipe;/mod:probe04_write_mutant;/' \
  -e 's/Result<int64>:r4 = sys(SYS_SENDTO, a, one, 1i64, MSG_NOSIGNAL, 0i64, 0i64);/Result<int64>:r4 = write((a =>! int32) =>! fd, one, 1i64);/' \
  "$d/tests/probe/probe04_sigpipe.npk" > "$F/probe04_write_mutant.npk"
echo "§1.5 probe 04's leg 4 with the floor's write: $(grep -c 'r4 = write((a =>! int32) =>! fd, one, 1i64);' "$F/probe04_write_mutant.npk") line(s) changed; $(run4 "$F/probe04_write_mutant.npk" | sed 's/^probe04_write_mutant: //')"
sed -e 's/^mod:probe04_sigpipe;/mod:probe04_default_mutant;/' \
  -e 's/^func:main = int32(cstring\[\]:_~argv) {$/&\n    wild int8->:act0 = calloc(1i64, 32i64); Result<int64>:rd0 = sys(SYS_RT_SIGACTION, SIGPIPE, act0, 0i64, 8i64); dalloc(act0); if (rd0.is_error) { exit 30i32; }/' \
  "$d/tests/probe/probe04_sigpipe.npk" > "$F/probe04_default_mutant.npk"
echo "§1.5 probe 04 started under SIG_DFL, as a runtime with no handler leaves it: $(grep -c 'rd0 = sys(SYS_RT_SIGACTION, SIGPIPE, act0, 0i64' "$F/probe04_default_mutant.npk") line(s) added; $(run4 "$F/probe04_default_mutant.npk" | sed 's/^probe04_default_mutant: //')"

# §1.6 -- the shapes, over every `.npk` the patches add, comments and strings blanked; the scanners proved first
echo "§1.6 the planted control:"; python3 -B "$TL/shapes.py" "$TL/shapes_planted.txt" | tail -n +2
echo "§1.6 the clean control:"; python3 -B "$TL/shapes.py" "$TL/shapes_clean.txt" | tail -n +2
python3 -B "$TL/shapes.py" "$TL/shapes_planted.txt" > /dev/null; e=$?
python3 -B "$TL/shapes.py" "$TL/shapes_clean.txt" > /dev/null; echo "§1.6 the shapes' exits: the planted control $e, the clean control $?"
mkdir -p "$F/added"
for s in 1 2 3 4 5; do grep -oE '^\+\+\+ b/.*\.npk$' "$T0/step$s.patch" | sed 's|^+++ b/||' >> "$F/added/list"; done
echo "§1.6 the $(wc -l < "$F/added/list") .npk file(s) the patches add:"
python3 -B "$TL/shapes.py" $(sed "s|^|$d/|" "$F/added/list") | tail -n +2
echo "§1.6 and where the plain views and the operands not spelled as an int32 literal are:"
python3 -B "$TL/shapes.py" --sites $(sed "s|^|$d/|" "$F/added/list") | sed "s|$d/||g" \
  | grep -E '^  (a plain|exit operand: (`|a cast))' | tr -s ' '
echo "§1.6 the rulings' planted control:"; python3 -B "$TL/rulings.py" "$TL/rulings_planted.txt" | tail -n +2
echo "§1.6 the rulings' clean control:"; python3 -B "$TL/rulings.py" "$TL/rulings_clean.txt" | tail -n +2
rs=$(python3 -B "$TL/rulings.py" --selftest); echo "§1.6 the rulings' STOP control, exit $?: $rs"
echo "§1.6 the rulings over the added files:"; python3 -B "$TL/rulings.py" $(sed "s|^|$d/|" "$F/added/list") | tail -n +2

# §1.7 -- every declared name against the pin's keyword table (landing 113), the scanner proved first
echo "§1.7 the names' planted control: $(python3 -B "$TL/names.py" "$F/keywords.npk" "$TL/names_planted.txt" | head -1)"
echo "§1.7 the names' clean control: $(python3 -B "$TL/names.py" "$F/keywords.npk" "$TL/names_clean.txt" | head -1)"
python3 -B "$TL/names.py" "$F/keywords.npk" "$TL/names_planted.txt" > /dev/null; e=$?
python3 -B "$TL/names.py" "$F/keywords.npk" "$TL/names_clean.txt" > /dev/null; echo "§1.7 the names' exits: the planted control $e, the clean control $?"
echo "§1.7 the added files: $(python3 -B "$TL/names.py" --count "$F/keywords.npk" $(sed "s|^|$d/|" "$F/added/list") | head -1)"

# §1.8 -- the placeholders: no file the patches touch holds one before they apply, and every one has a number
n=0; for f in $(grep -ohE '^\+\+\+ b/.*' "$T0"/step*.patch | sed 's|^+++ b/||' | sort -u); do
  [ -f "$REPO/$f" ] && grep -q '@@PD-' "$REPO/$f" && { echo "§1.8 holds a placeholder already: $f"; n=$((n+1)); }
done
echo "§1.8 files the patches touch that hold \`@@PD-\` as the tree stands: $n"
echo "§1.8 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T0"/step*.patch | sort -u | tr '\n' ' ')"
echo "§1.8 numbered by decisions.txt: $(python3 -B -c "
import sys; sys.path.insert(0, '$TL'); import apply
t = apply.numbers(); print(' '.join('%s=base+%d' % (k, int(t[k].split('-')[1]) - apply.base_number()) for k in sorted(t) if k <= 'PD-163'))")"

# §1.9 -- every rule and section the added lines cite exists in the tree the patches leave; first its controls, a
# patch citing a rule no specification defines and a section no file holds, and one citing S-1 and its section
mkdir -p "$F/ptr/planted" "$F/ptr/clean"
printf '%s\n' '+++ b/planted.md' '+the rule Z-99 and `STREAM_MODEL.md` §99' > "$F/ptr/planted/step1.patch"
printf '%s\n' '+++ b/clean.md' '+the rule S-1 and `SAFETY.md` §1' > "$F/ptr/clean/step1.patch"
for c in planted clean; do
  python3 -B "$TL/pointers.py" "$d" "$F/ptr/$c" > "$F/ptr/$c.out"; e=$?
  echo "§1.9 the pointers' $c control, exit $e: $(grep -E '^§1\.8 (undefined|sections that do not resolve):' "$F/ptr/$c.out" | sed 's/^§1\.8 //' | paste -sd ';' | sed 's/;/; /g')"
done
python3 -B "$TL/pointers.py" "$d" "$T0" | sed "s|$d/||g; s/^§1\.8/§1.9/"
rm -rf "${d:?}" "${F:?}"
