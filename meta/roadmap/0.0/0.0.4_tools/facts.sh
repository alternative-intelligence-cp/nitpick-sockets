# meta/roadmap/0.0/0.0.4_tools/facts.sh -- re-derives `0.0.4.md` §1, block 0b. Sourced after `../tools/env.sh`, so
# `$REPO`, `$A`, `$NPKC`, `$NPKRT`, `$NPK_TREE`, `$PIN`, `$WB` and the helpers are set. Writes only under `$A/facts`,
# and removes it. Reads the compiler's tree with `git show` alone. Prints no path above the repository: every scratch
# path is cut to its name. The tree it starts from is 0.0.3's record; `$d` is a throwaway clone with this subcycle's
# three patches applied, where every program that imports `src/core/` is written.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T4=$REPO/meta/roadmap/0.0/0.0.4_tools
TL=$REPO/meta/roadmap/0.0/tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in 1 2 3; do python3 -B "$TL/apply.py" "$d" 0.0.4 $s > /dev/null; done
show() { git -C "$NPK_TREE" show "$1"; }
FS='func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (IntOverflow)       { exit 93i32; },
        (OutOfBounds)       { exit 94i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'
# the contract arms, beside the floor's: PLAYBOOK.md §3 item 8's codes
FSC=$(printf '%s\n' "$FS" | sed 's/^        (\*)                 { exit 99i32; }$/        (LimitViolated)     { exit 109i32; },\n        (RequiresViolated)  { exit 116i32; },\n        (EnsuresViolated)   { exit 117i32; },\n        (*)                 { exit 99i32; }/')
# prog <dir> <name> <use-line or ""> <declarations> <main body>: a program with the floor's arms and the two index
# ones, or with `$FSX` as its `failsafe` where the caller sets it
prog() {
  local use="" decl=""
  mkdir -p "$1"
  [ -n "$3" ] && use="$3"$'\n\n'
  [ -n "$4" ] && decl="$4"$'\n'
  printf 'mod:%s;\n\n%s%sfunc:main = int32(cstring[]:_~argv) {\n%s\n    exit 0i32;\n};\n\n%s\n' "$2" "$use" "$decl" \
    "$5" "${FSX:-$FS}" > "$1/$2.npk"
}
# heapcount <binary>: the runtime's own allocation count, `NPK_HEAP_STATS`'s `count=`
heapcount() { NPK_HEAP_STATS=1 "$1" 2>&1 >/dev/null | grep -oE 'count=[0-9]+' | cut -d= -f2; }

# §1.1 -- the tree it starts from: cycle 0.0.3's record
echo "§1.1 src/core/ holds: $(cd "$REPO/src/core" && ls *.npk | tr '\n' ' ')"
echo "§1.1 tests/unit/: $(find "$REPO/tests/unit" -maxdepth 1 -name '*.npk' 2>/dev/null | wc -l) .npk file(s)"
python3 -B - "$REPO/nitpick.toml" <<'PY'
import sys, tomllib
m = tomllib.load(open(sys.argv[1], "rb"))
print("§1.1 nitpick.toml's [[test]] entries: %d (%s)" % (len(m["test"]), ", ".join(
    "%s %s%s" % (t["name"], t["stage"], "/" + t["kind"] if "kind" in t else "") for t in m["test"])))
PY
python3 -B - "$REPO" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import treecheck
line, bad = treecheck.check_constants_named(sys.argv[1])
print("§1.1 check_constants_named, as the tree stands: %s; %d finding(s)" % (line.split("; ")[-1], len(bad)))
PY

# §1.2 -- the bounds: the first writing's two lists, and what the specifications state
echo "§1.2 the first writing's cycle README (main's d385991, the checklist's line): $(git -C "$REPO" show d385991:meta/roadmap/0.0/README.md | grep -m1 'limits.npk` — every named bound' | grep -oE 'NSOCK_[A-Z_]+|and the deadline defaults' | tr '\n' ' ')"
echo "§1.2 the first writing's 0.0.4.md (d385991, its §4): $(git -C "$REPO" show d385991:meta/roadmap/0.0/0.0.4.md | awk '/^## 4\./,/^## 5\./' | grep -oE 'NSOCK_[A-Z_]+' | sort -u | wc -l) names: $(git -C "$REPO" show d385991:meta/roadmap/0.0/0.0.4.md | awk '/^## 4\./,/^## 5\./' | grep -oE 'NSOCK_[A-Z_]+' | tr '\n' ' ')"
echo "§1.2 C-11 as the tree stands: $(grep -c 'NSOCK_EMFILE_BACKOFF` (a named constant, 50 ms)' "$REPO/meta/specs/CONCURRENCY_MODEL.md") line(s) reading \`NSOCK_EMFILE_BACKOFF\` (a named constant, 50 ms)"
echo "§1.2 the bounds meta/specs/ states as \`NSOCK_<NAME>\` = n, after step 1: $(cd "$d/meta/specs" && grep -oE '`NSOCK_[A-Z_]+` = [0-9]+' *.md | sed -E 's/^([A-Z_]+\.md):`(NSOCK_[A-Z_]+)` = ([0-9]+)$/\2 = \3 (\1)/' | sort | tr '\n' ';' | sed 's/;$//; s/;/; /g')"
echo "§1.2 a bound meta/specs/ names with no value anywhere: $(cd "$d/meta/specs" && comm -23 <(grep -ohE '`NSOCK_[A-Z_]+`' *.md | tr -d '`' | sort -u) <(grep -ohE '`NSOCK_[A-Z_]+` = [0-9]+' *.md | grep -oE 'NSOCK_[A-Z_]+' | sort -u) | tr '\n' ' ')"
echo "§1.2 the first writing's other five in meta/specs/: $(grep -ohE 'NSOCK_(ADDR_MAX|DEFAULT_BACKLOG|CONNECT_TIMEOUT|ACCEPT_TIMEOUT|IO_TIMEOUT)' "$d"/meta/specs/*.md | wc -l) mention(s)"
echo "§1.2 NSOCK_POLLSET_MAX in the cycle map's checklists: $(cd "$d/meta/roadmap" && grep -l 'NSOCK_POLLSET_MAX' */README.md | grep -v '^0\.0/' | tr '\n' ' ')"
echo "§1.2 src/core/limits.npk, after step 1: $(grep -oE '^pub fixed int64:NSOCK_[A-Z_]+ = [0-9]+i64;' "$d/src/core/limits.npk" | sed -E 's/^pub fixed int64:(NSOCK_[A-Z_]+) = ([0-9]+)i64;$/\1 = \2/' | tr '\n' ';' | sed 's/;$//; s/;/; /g')"

# §1.3 -- the value rule against the kernel's values: what shares a bound's number, and the old rule over a planted tree
python3 -B - "$d" <<'PY'
import os, sys
root = sys.argv[1]; sys.path.insert(0, os.path.join(root, "harness"))
import treecheck
calls, consts = treecheck._k1(root)
sizes = treecheck._stated_sizes(root)
for v in (256, 16, 50):
    share = sorted("%s (a kernel constant)" % k for k, x in consts.items() if x == v)
    share += sorted("%s (K-1's syscall number)" % k for k, x in calls.items() if x == v)
    share += sorted("%s (a structure's size)" % n for n, b, _ in sizes if b == v)
    print("§1.3 what a bound's number %d is beside: %s" % (v, "; ".join(share) or "nothing a specification states"))
PY
mkdir -p "$F/plant"
for t in old new; do
  p=$F/plant/$t; mkdir -p "$p"
  if [ $t = old ]; then git -C "$REPO" archive HEAD | tar -x -C "$p"
  else ( cd "$d" && git ls-files -z | tar --null -T - -cf - ) | tar -x -C "$p"; fi
  cp "$d/src/core/limits.npk" "$p/src/core/limits.npk"
  printf '\npub fixed int64:SO_PASSCRED = 16i64;\npub fixed int64:SYS_LISTEN = 50i64;\n' >> "$p/src/sys/sys.npk"
  printf '\n// `sockaddr_in` is 16 bytes (ADDRESS_MODEL.md), planted as the literal.\npub func:addr_sin_len = int64() never fails {\n    pass 16i64;\n};\n' >> "$p/src/addr/addr.npk"
  python3 -B - "$p" "$t" <<'PY'
import os, sys
root, which = sys.argv[1], sys.argv[2]; sys.path.insert(0, os.path.join(root, "harness"))
import treecheck
line, bad = treecheck.check_constants_named(root)
who = "0.0.3's check_constants_named" if which == "old" else "the patched tree's"
print("§1.3 %s over the planted tree (the three bounds; src/sys/ declaring SO_PASSCRED = 16 and SYS_LISTEN = 50; "
      "src/addr/ passing sockaddr_in's size, 16): %d finding(s)%s" % (who, len(bad), "" if not bad else " -- " + "; ".join(bad)))
if which == "new":
    print("§1.3 its line, after src/sys/'s: %s" % line.split(" constant(s) in src/sys/; ", 1)[-1])
PY
done

# §1.4 -- what an index does, at both legs: a pointer's is checked by nothing; a slice's, an array's and a buffer's trap
X=$F/index
prog "$X" wild_index "" "" "    wild int8->:mem = alloc(32i64);
    wild int64->:p = mem =>! wild int64->;
    discard(p[9i64]);
    dalloc(mem);"
prog "$X" ptr_index "" "" "    buffer:b = buffer_new(4i64);
    discard(b.ptr[9i64]);"
prog "$X" slice_index "" "" "    fixed uint8[]:s = string_bytes(\"abcd\");
    int64:i = 4i64;
    discard(s[i]);"
prog "$X" array_index "" "" "    int64[4]:a = [1i64, 2i64, 3i64, 4i64];
    int64:i = 4i64;
    discard(a[i]);"
prog "$X" buffer_read "" "" "    buffer:b = buffer_new(4i64);
    int64:i = 4i64;
    discard(b[i]);"
prog "$X" buffer_param_write "" "struct:S = { buffer:buf; };

func:poke = NIL(S->:s, int64:i) never fails {
    s.buf[i] = 7u8;
    pass NIL;
};
" "    S:s = S{ buf: buffer_new(4i64) };
    drop poke(@s, 4i64);"
prog "$X" buffer_param_read "" "struct:S = { buffer:buf; };

func:peek = uint8(S->:s, int64:i) never fails {
    pass s.buf[i];
};
" "    S:s = S{ buf: buffer_new(4i64) };
    discard(raw peek(@s, 4i64));"
for f in wild_index ptr_index slice_index array_index buffer_read buffer_param_write buffer_param_read; do echo "§1.4 $(run4 "$X/$f.npk")"; done
rng() { prog "$X" "$1" "" "${3:-}" "    buffer:b = buffer_new(8i64);
    int64:i = 5i64;
    {
        fixed uint8[]:v = b[0i64...4i64];
$2
    }"; }
rng range_out_const_live "        b[5i64] = 1u8;
        discard(v[0i64]);"
rng range_in_const_after "        discard(v[0i64]);
        b[1i64] = 7u8;"
rng range_variable_after "        discard(v[0i64]);
        b[i] = 7u8;"
rng range_overwrite_after "        discard(v[0i64]);
        b = buffer_new(16i64);"
prog "$X" range_callee_after "" "struct:S = { buffer:buf; int64:len; };

func:grow = NIL(S->:s) never fails {
    s.buf = buffer_new(16i64);
    pass NIL;
};
" "    S:s = S{ buf: buffer_new(8i64), len: 0i64 };
    {
        fixed uint8[]:v = s.buf[0i64...4i64];
        discard(v[0i64]);
        drop grow(@s);
    }"
echo "§1.4 a range of a buffer, b[0i64...4i64], held by v in a block, and in that block:"
echo "§1.4   b[5i64] written, a constant index outside the range, while v lives: $(codes "$X/range_out_const_live.npk")"
echo "§1.4   b[1i64] written, inside the range, after v's last use: $(codes "$X/range_in_const_after.npk")"
echo "§1.4   b[i] written, i a local holding 5, after v's last use: $(codes "$X/range_variable_after.npk")"
echo "§1.4   b overwritten after v's last use: $(codes "$X/range_overwrite_after.npk")"
echo "§1.4   the same overwrite by a callee handed the holder's address: $(codes "$X/range_callee_after.npk")"

# §1.5 -- what a live clause and a division cost every consumer, and what each traps at run time
C5=$F/clauses; mkdir -p "$C5"
printf 'mod:req;\n\npub func:req_f = int64(int64:x) never fails requires x >= 0i64 {\n    pass x;\n};\n' > "$C5/req.npk"
printf 'mod:ens;\n\npub func:ens_f = int64(int64:x) never fails ensures result >= 0i64 {\n    pass x;\n};\n' > "$C5/ens.npk"
printf 'mod:lim;\n\nRules<int64>:Small = { $ >= 0i64, $ <= 9i64 };\n\npub struct:Box = { limit<Small> int64:n; };\n\npub func:lim_f = Box(int64:x) never fails {\n    pass Box{ n: x };\n};\n' > "$C5/lim.npk"
printf 'mod:div;\n\npub func:div_f = int64(int64:x) never fails {\n    pass x / 2i64;\n};\n' > "$C5/div.npk"
printf 'mod:via;\n\nuse "./div.npk".*;\n\npub func:via_f = int64(int64:x) never fails {\n    pass raw div_f(x);\n};\n' > "$C5/via.npk"
for f in req ens lim div via; do echo "§1.5 a consumer of $(bill "$C5/$f.npk")"; done
FSX=$FSC prog "$C5" req_run 'use "./req.npk".*;' "" "    discard(raw req_f(0i64 - 1i64));"
FSX=$FSC prog "$C5" ens_run "" "func:neg = int64(int64:x) never fails ensures result >= 0i64 {
    pass 0i64 - x;
};
" "    discard(raw neg(5i64));"
FSX=$FSC prog "$C5" lim_run 'use "./lim.npk".*;' "" "    Box:b = raw lim_f(10i64);
    discard(b.n);"
for f in req_run ens_run lim_run; do echo "§1.5 $(run4 "$C5/$f.npk")"; done
mkdir -p "$F/pre/src/core" "$F/pre/tests/unit"
python3 -B - "$d/src/core/vec.npk" "$F/pre/src/core/vec.npk" <<'PY'
import sys
t = open(sys.argv[1], encoding="utf-8").read()
old = "pub func:vec_at<T: Copy> = T(Vec<T>:v, int64:i) never fails {"
assert t.count(old) == 1
open(sys.argv[2], "w", encoding="utf-8").write(t.replace(old, old[:-1] + "requires v.cap > 0i64 && i >= 0i64 && i < v.count {"))
PY
for v in comment live; do
  src=$d; [ $v = live ] && src=$F/pre
  FSX=$FSC prog "$src/tests/unit" "zz_pre_$v" 'use "../../src/core/vec.npk".*;' "" "    Vec<int64>:v = raw vec_init::<int64>(4i64);
    drop vec_push(@v, 1i64);
    discard(raw vec_at(v, v.count));
    drop vec_free(@v);"
  echo "§1.5 vec_at at i == count, its obligation a $v: $(run4 "$src/tests/unit/zz_pre_$v.npk" | sed "s/^zz_pre_$v: //")"
  rm -f "$src/tests/unit/zz_pre_$v.npk"
done

# §1.6 -- the specification's spellings: VERIFICATION.md Z-2, Z-4 and Z-5, as written and as each compiles
Z=$F/spell; mkdir -p "$Z"
blockof() { awk -v r="$1" '$0 ~ r {f=1} f && /^```nitpick/ {g=1; next} g && /^```/ {exit} g' "$d/meta/specs/VERIFICATION.md"; }
{ echo 'mod:z2;'; echo; blockof '^[*][*]Rule Z-2 ' | sed 's/never fails { … };/never fails {\n    pass 0u16;\n};/'; } > "$Z/z2.npk"
echo "§1.6 Z-2's shape, given a body: $(codes "$Z/z2.npk")"
sed 's/^mod:z2;/mod:z2_order;/; /^    requires (sa.len >= 16i64)$/d; s/^func:sin_port_at = uint16(fixed uint8\[\]:sa)$/func:sin_port_at = uint16(fixed uint8[]:sa) never fails requires (sa.len >= 16i64)/; /^    never fails {$/s/^    never fails {$/    {/' "$Z/z2.npk" > "$Z/z2_order.npk"
echo "§1.6 the same, \`never fails\` before \`requires\`: $(codes "$Z/z2_order.npk")"
{ echo 'mod:z4;'; echo; blockof '^[*][*]Rule Z-4[.]'; } > "$Z/z4.npk"
echo "§1.6 Z-4's block as written: $(codes "$Z/z4.npk")"
{ echo 'mod:z4_two;'; echo; blockof '^[*][*]Rule Z-4[.]' | sed -n '1,8p'; } > "$Z/z4_two.npk"
echo "§1.6 its first two shapes: $(codes "$Z/z4_two.npk")"
{ echo 'mod:z4_typed;'; echo; echo 'struct:SocketAddr = { uint16:family; };'; echo 'struct:UnixAddr = { uint16:family; };'; echo; blockof '^[*][*]Rule Z-4[.]' | sed -n '1,8p'; } > "$Z/z4_typed.npk"
echo "§1.6 the two, SocketAddr and UnixAddr declared: $(codes "$Z/z4_typed.npk")"
third=$(blockof '^[*][*]Rule Z-4[.]' | sed -n '9,10p')
printf 'mod:z4_third;\n\n%s\n' "$third" > "$Z/z4_third.npk"
for v in plain:never_fails:bare pure:pure_never_fails:bare plain:never_fails:raw pure:pure_never_fails:raw; do
  IFS=: read -r kind mods call <<< "$v"
  body=$third; [ "$call" = raw ] && body=$(printf '%s' "$third" | sed 's/(ntoh16(result) == v)/(raw ntoh16(result) == v)/')
  printf 'mod:z4_%s_%s;\n\nfunc:ntoh16 = uint16(uint16:v) %s {\n    pass v;\n};\n\n%s\n' "$kind" "$call" "${mods//_/ }" "$body" > "$Z/z4_${kind}_$call.npk"
done
echo "§1.6 the third alone: $(codes "$Z/z4_third.npk")"
for v in plain_bare pure_bare plain_raw pure_raw; do echo "§1.6 the third, ntoh16 ${v%_*} and called ${v#*_}: $(codes "$Z/z4_$v.npk")"; done
printf 'mod:z5;\n\n%s\n' "$(blockof '^[*][*]Rule Z-5[.]' | sed -n '1p' | sed 's/ *\/\/.*$//')" > "$Z/z5.npk"
echo "§1.6 Z-5's first rule as written, $(sed -n '3p' "$Z/z5.npk"): $(codes "$Z/z5.npk")"
printf 'mod:z5_typed;\n\nRules<uint16>:Port = { $ >= 0u16, $ <= 65535u16 };\n' > "$Z/z5_typed.npk"
echo "§1.6 the spelling with its type and commas, Rules<uint16>:Port = { \$ >= 0u16, \$ <= 65535u16 };: $(codes "$Z/z5_typed.npk")"

# §1.7 -- the containers' shapes, from a unit's place: move-only, hidden, sealed, the Copy bound, NULL
U=$d/tests/unit
FSX= prog "$U" zz_vec_copy 'use "../../src/core/vec.npk".*;' "" "    Vec<int64>:v = raw vec_init::<int64>(2i64);
    Vec<int64>:w = v;
    drop vec_free(@w);"
FSX= prog "$U" zz_bytes_copy 'use "../../src/core/bytes.npk".*;' "" "    Bytes:b = raw bytes_init(4i64);
    Bytes:c = b;"
FSX= prog "$U" zz_plain_copy "" "struct:Plain = { wild int64->:items; int64:count; int64:cap; };
" "    Plain:a = Plain{ items: NULL, count: 0i64, cap: 0i64 };
    Plain:b = a;
    discard(b.count);"
FSX= prog "$U" zz_sizes 'use "../../src/core/vec.npk".*;' "struct:Plain = { wild int64->:items; int64:count; int64:cap; };
" "    if (#size_of<Vec<int64>>() != #size_of<Plain>()) { exit 10i32; }
    if (#size_of<Plain>() != 24i64) { exit 11i32; }"
FSX= prog "$U" zz_vec_hidden 'use "../../src/core/vec.npk".*;' "" "    Vec<int64>:v = raw vec_init::<int64>(2i64);
    drop vec_push(@v, 1i64);
    int64:x = v.items[0i64];
    drop vec_free(@v);"
FSX= prog "$U" zz_bytes_hidden 'use "../../src/core/bytes.npk".*;' "" "    Bytes:b = raw bytes_init(4i64);
    uint8:x = b.buf[0i64];"
FSX= prog "$U" zz_vec_sealed 'use "../../src/core/vec.npk".*;' "" "    Vec<int64>:v = raw vec_init::<int64>(2i64);
    v.count = 5i64;
    drop vec_free(@v);"
FSX= prog "$U" zz_bytes_sealed 'use "../../src/core/bytes.npk".*;' "" "    Bytes:b = raw bytes_init(4i64);
    b.len = 3i64;"
FSX= prog "$U" zz_sealed_read 'use "../../src/core/vec.npk".*;' "" "    Vec<int64>:v = raw vec_init::<int64>(2i64);
    int64:n = v.count + v.cap;
    drop vec_free(@v);"
FSX= prog "$U" zz_owning 'use "../../src/core/vec.npk".*;' "" "    Vec<string>:v = raw vec_init::<string>(2i64);
    drop vec_free(@v);"
FSX= prog "$U" zz_unbound 'use "../../src/core/vec.npk".*;' "func:first<T> = T(Vec<T>:v) never fails {
    pass raw vec_at(v, 0i64);
};
" "    Vec<int64>:v = raw vec_init::<int64>(2i64);
    drop vec_push(@v, 7i64);
    if ((raw first::<int64>(v)) != 7i64) { exit 10i32; }
    drop vec_free(@v);"
sed 's/^mod:zz_unbound;/mod:zz_bound;/; s/^func:first<T> =/func:first<T: Copy> =/' "$U/zz_unbound.npk" > "$U/zz_bound.npk"
FSX= prog "$U" zz_null_plain "" "struct:Q = { int64->:p; };
" "    Q:q = Q{ p: NULL };"
for f in zz_vec_copy zz_bytes_copy zz_plain_copy zz_vec_hidden zz_bytes_hidden zz_vec_sealed zz_bytes_sealed zz_sealed_read zz_owning zz_unbound zz_bound zz_null_plain; do echo "§1.7 $(codes "$U/$f.npk" | sed 's/^zz_//')"; done
echo "§1.7 $(run4 "$U/zz_sizes.npk" | sed 's/^zz_//') -- 0 is Vec<int64> the size of the same three fields, 24 bytes"
echo "§1.7 $(run4 "$U/zz_bound.npk" | sed 's/^zz_//')"

# §1.8 -- the allocator's ceiling, through vec_init, and the literal envelope
FSX= prog "$U" zz_past_ceiling 'use "../../src/core/vec.npk".*;' "" "    Vec<int64>:v = raw vec_init::<int64>(17592186044417i64);
    drop vec_free(@v);"
sed 's/^mod:zz_past_ceiling;/mod:zz_at_ceiling;\n\/\/ mem-cap-mib: 4096/; s/17592186044417i64/17592186044416i64/' "$U/zz_past_ceiling.npk" > "$U/zz_at_ceiling.npk"
echo "§1.8 vec_init of 2^44 + 1 int64s, 2^47 + 8 bytes: $(run4 "$U/zz_past_ceiling.npk" | sed 's/^zz_past_ceiling: //')"
echo "§1.8 vec_init of 2^44 int64s, 2^47 bytes: $(run4 "$U/zz_at_ceiling.npk" | sed 's/^zz_at_ceiling: //')"
LX=$F/lex
for v in "i64_max|fixed int64:I64_MAX = 9223372036854775807i64;" "i64_min|fixed int64:I64_MIN = -9223372036854775808i64;" \
         "u64_past_i64|fixed uint64:U = 9223372036854775808u64;" "u64_ten19|fixed uint64:TEN19 = 10000000000000000000u64;" \
         "u64_max|fixed uint64:U64_MAX = 18446744073709551615u64;"; do
  prog "$LX" "${v%%|*}" "" "${v#*|}
" ""
  echo "§1.8 ${v#*|} $(codes "$LX/${v%%|*}.npk" | sed 's/^[a-z0-9_]*\.npk: //')"
done

# §1.9 -- every obligation made live, one at a time, each module compiled alone
python3 -B "$T4/obligations.py" "$NPKC" "$F/obligations" "$d/src/core/vec.npk" "$d/src/core/bytes.npk" | sed 's/^/§1.9 /'

# §1.10 -- the generic instances: a module compiled alone emits none of its generics; the instantiating unit, each
( cd "$d/src/core" && "$NPKC" vec.npk -o "$F/vec.ll" )
echo "§1.10 vec.npk compiled alone defines, of its own functions: $(grep -oE '^define [^@]*@"?npk\.vec\.[A-Za-z_]+[<"(]' "$F/vec.ll" | grep -oE 'npk\.vec\.[A-Za-z_]+' | sort -u | tr '\n' ' ')"
( cd "$d/tests/unit" && "$NPKC" generic_instances.npk -o "$F/gi.ll" )
echo "§1.10 generic_instances.npk's emission defines: $(grep -oE '^define [^@]*@"npk\.vec\.vec_[A-Za-z_]+<[^>]*>' "$F/gi.ll" | grep -oE '@"npk\.vec\.vec_[A-Za-z_]+<[^>]*>' | sort -u | wc -l) function instance(s), as $(grep -oE '^define [^@]*@"npk\.vec\.vec_at<[^>]*>' "$F/gi.ll" | grep -oE 'npk\.vec\.vec_at<[^>]*>' | head -1)"

# §1.11 -- what a consumer of each module of src/core/ owes, and the same Bytes dividing
for f in limits vec bytes; do echo "§1.11 a consumer of $(bill "$d/src/core/$f.npk")"; done
cp "$d/src/core/bytes.npk" "$F/bytes_div.npk"
printf '\n// planted: a digit by division, as a put_uint by division would find it.\npub func:bytes_digit = uint8(uint64:v) never fails {\n    pass ((v %% 10u64) =>! uint8) + 48u8;\n};\n' >> "$F/bytes_div.npk"
sed -i 's/^mod:bytes;/mod:bytes_div;/' "$F/bytes_div.npk"
printf 'mod:div_user;\n\nuse "./bytes_div.npk".*;\n\npub func:div_user_f = uint8(uint64:v) never fails {\n    pass raw bytes_digit(v);\n};\n' > "$F/div_user.npk"
echo "§1.11 a consumer of the same file with a digit by \`%\`, $(bill "$F/bytes_div.npk")"
echo "§1.11 a consumer of a module that imports it, $(bill "$F/div_user.npk")"

# §1.12 -- allocation: a thousand renderings into a sink with room, by put_uint and by int_to_string
FSX= prog "$U" zz_put 'use "../../src/core/bytes.npk".*;' "" "    Bytes:b = raw bytes_init(4096i64);
    for (int64:i in 0i64...1000i64) {
        drop bytes_put_uint(@b, (i =>! uint64));
    }
    if (b.len != 2890i64) { exit 10i32; }"
sed 's/^mod:zz_put;/mod:zz_its;/; s/^        drop bytes_put_uint(@b, (i =>! uint64));$/        string:t = int_to_string(i);\n        drop bytes_extend_str(@b, t);/' "$U/zz_put.npk" > "$U/zz_its.npk"
for f in zz_put zz_its; do echo "§1.12 $(run4 "$U/$f.npk" | sed 's/^zz_//'); NPK_HEAP_STATS count=$(heapcount "$A/run4/$f")"; done

# §1.13 -- G8's plant: an int64 overflow first in a loop's body traps at both legs; an `exit` outside main is refused
G8=$F/g8
prog "$G8" g8_plant "" "" "    int64:t = 0i64;
    for (int64:k in 0i64...3i64) {
        int64:g8_planted = (k - k) + 9223372036854775807i64 + 1i64;
        t = t + k;
    }
    if (t != 3i64) { exit 10i32; }"
printf 'mod:g8_exit;\n\nfunc:g8_f = int64(int64:n) never fails {\n    exit 93i32;\n    pass n;\n};\n' > "$G8/g8_exit.npk"
echo "§1.13 $(run4 "$G8/g8_plant.npk")"
echo "§1.13 an \`exit\` in a function other than main and failsafe: $(codes "$G8/g8_exit.npk")"

# §1.14 -- the shapes, the rulings and the names over every .npk the patches add, and the read-only view
added=$(grep -ohE '^\+\+\+ b/.*\.npk$' "$T4"/step*.patch | sed 's|^+++ b/||' | sort -u)
echo "§1.14 .npk files the patches add: $(echo "$added" | wc -l) ($(echo "$added" | grep -c '^src/') under src/core/, $(echo "$added" | grep -c '^tests/unit/') under tests/unit/); remove: $(grep -B3 -hE '^\+\+\+ /dev/null' "$T4"/step*.patch | grep -oE '^--- a/.*\.npk$' | sed 's|^--- a/||' | tr '\n' ' ')"
( cd "$d" && python3 -B "$TL/shapes.py" $added ) | sed 's/^/§1.14 shapes: /'
( cd "$d" && python3 -B "$TL/rulings.py" $added ) | sed 's/^/§1.14 rulings: /'
show "$PIN:src/frontend/keywords.npk" > "$F/keywords.npk"
( cd "$d" && python3 -B "$TL/names.py" --count "$F/keywords.npk" $(git ls-files '*.npk') ) | sed 's/^/§1.14 the patched tree: /'
python3 -B - "$d" <<'PY'
import os, re, sys
root = sys.argv[1]; sys.path.insert(0, os.path.join(root, "harness"))
import lexical
code = lexical.blank(lexical.read(os.path.join(root, "src", "core", "bytes.npk")))
print("§1.14 bytes.npk's code: `.ptr` %d time(s), `#ptr_add` %d, `#wild_slice` %d, a range `[...]` %d"
      % (len(re.findall(r"\.ptr\b", code)), code.count("#ptr_add"), code.count("#wild_slice"), len(re.findall(r"\[[^\]]*\.\.\.[^\]]*\]", code))))
PY

# §1.15 -- the safety rules of PLAYBOOK.md §2's notes (2026-10-23 and 2026-10-24), read against every .npk the patches
# add: each shape they bind, counted in the code as the compiler reads it
python3 -B - "$d" $added <<'PY2'
import os, re, sys
root, files = sys.argv[1], sys.argv[2:]
sys.path.insert(0, os.path.join(root, "harness"))
import lexical
code = {f: lexical.blank(lexical.read(os.path.join(root, f))) for f in files}
src = [f for f in files if f.startswith("src/")]
fors = [(f, m.group(1)) for f in files for m in re.finditer(r"\bfor\s*\(\s*([A-Za-z_]\w*)\s*:\s*\w+\s+in\s+[^)]*\.\.\.", code[f])]
others = sum(len(re.findall(r"\bfor\s*\(", code[f])) for f in files) - len(fors)
print("§1.15 for bindings: %d, each over a range: %s; any other for: %d" % (len(fors), ", ".join(sorted({t for _, t in fors})), others))
ptrs = {}
for f in src:
    for m in re.finditer(r"^(?:pub )?func:\w+(?:<[^>]*>)? = [^(]*\(([^)]*)\)", code[f], re.M):
        for q in re.findall(r"([A-Za-z_][\w<>: ]*)->:(\w+)", m.group(1)):
            ptrs[(os.path.basename(f), q[0].strip() + "->:" + q[1])] = ptrs.get((os.path.basename(f), q[0].strip() + "->:" + q[1]), 0) + 1
print("§1.15 pointer parameters under src/: %s" % "; ".join("%s %s x%d" % (f, q, n) for (f, q), n in sorted(ptrs.items())))
print("§1.15 under src/: `@` %d; a range [lo...hi] %d; string_bytes( %d; string_from_bytes( %d; a view bound to a local or a field: %d"
      % (sum(c.count("@") for f, c in code.items() if f in src),
         sum(len(re.findall(r"\[[^\]\n]*\.\.\.[^\]\n]*\]", code[f])) for f in src),
         sum(code[f].count("string_bytes(") for f in src), sum(code[f].count("string_from_bytes(") for f in src),
         sum(len(re.findall(r"(fixed )?uint8\[\]:\w+\s*=|\.\w+\s*=\s*string_(from_)?bytes\(", code[f])) for f in src)))
print("§1.15 in every added file: spawn %d; shared_arena %d; List< %d; #ptr_add %d; #wild_slice %d"
      % tuple(sum(c.count(w) for c in code.values()) for w in ("spawn", "shared_arena", "List<", "#ptr_add", "#wild_slice")))
for f in src:
    print("§1.15 %s: `=>!` %d" % (os.path.basename(f), code[f].count("=>!")))
PY2

# §1.16 -- the placeholders: the decision labels and the run's date
echo "§1.16 files the patches touch that hold \`@@PD-\` or \`@@DATE@@\` as the tree stands: $(n=0; for f in $(grep -ohE '^\+\+\+ b/.*' "$T4"/step*.patch | sed 's|^+++ b/||' | sort -u); do [ -f "$REPO/$f" ] && grep -qE '@@PD-|@@DATE@@' "$REPO/$f" && n=$((n+1)); done; echo $n)"
echo "§1.16 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T4"/step*.patch | sort -u | tr '\n' ' ')"
echo "§1.16 declared by them: $(grep -ohE '^\+### @@PD-[0-9]+@@' "$T4"/step*.patch | grep -oE 'PD-[0-9]+' | tr '\n' ' ')"
echo "§1.16 numbered by decisions.txt: $(python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1]); import apply
t = apply.numbers(); print(' '.join('%s=base+%d' % (k, int(t[k].split('-')[1]) - apply.base_number()) for k in sorted(t) if 'PD-176' <= k <= 'PD-177'))" "$TL")"
echo "§1.16 added lines carrying @@DATE@@: $(for s in 1 2 3; do printf 'step%s %s; ' $s "$(grep -cE '^\+[^+].*@@DATE@@' "$T4/step$s.patch")"; done | sed 's/; $//')"

# §1.17 -- every pointer the patches' added lines write
python3 -B "$TL/pointers.py" "$d" "$T4" | sed 's/^§1\.8 /§1.17 /'
# `pointers.py` reads an id as a letter and a number alone, so a lettered one -- `Z-1a`, `B-2a` -- is read here
lettered=$(grep -hE '^\+[^+]' "$T4"/step*.patch | grep -oE '(^|[^A-Za-z0-9-])[A-Z]-[0-9]+[a-z]\b' | grep -oE '[A-Z]-[0-9]+[a-z]' | sort -u)
echo "§1.17 lettered rules cited by the added lines: $(echo "$lettered" | wc -w) -- $(for r in $lettered; do f=$(grep -lE "^\*\*Rule $r\b" "$d"/meta/specs/*.md | head -1); printf '%s(%s) ' "$r" "$( [ -n "$f" ] && basename "$f" || echo 'no rule here')"; done)"

# §1.18 -- the interpreter
echo "§1.18 $(python3 --version)"
rm -rf "${F:?}"
