# meta/roadmap/0.0/0.0.1_tools/facts.sh -- re-derives `0.0.1.md` §1, block 0b. Sourced after `../tools/env.sh`, so
# `$REPO`, `$A`, `$NPKC`, `$NPKRT`, `$NPK_TREE`, `$PIN`, `$PIN_FULL`, `$WB` and the helpers are set. Writes only under
# `$A/facts`, and removes it. Reads the compiler's tree with `git show` and `git grep` alone.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T1=$REPO/meta/roadmap/0.0/0.0.1_tools
TL=$REPO/meta/roadmap/0.0/tools
show() { git -C "$NPK_TREE" show "$1"; }

# The patched tree: the six steps applied to a throwaway clone of HEAD, which §1.2 to §1.10 read
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in 1 2 3 4 5 6; do python3 -B "$TL/apply.py" "$d" 0.0.1 $s > /dev/null; done

# §1.1 -- the tree it starts from: cycle 0.0.0's record
echo "§1.1 decisions: the highest by value $(grep -o '^### SK-[0-9]*' "$REPO/meta/DECISIONS.md" | sort -t- -k2 -n | tail -1 | cut -c5-)"
echo "§1.1 src holds: $(git -C "$REPO" ls-files src | grep -c '\.npk$') .npk file(s); harness holds: $(git -C "$REPO" ls-files harness | tr '\n' ' ')"
echo "§1.1 .github exists: $(test -e "$REPO/.github" && echo yes || echo no); meta/research holds: $(git -C "$REPO" ls-files meta/research | sed 's|^meta/research/||' | tr '\n' ' ')"

# §1.2 -- the compiler's manifest rows at the pin, and the patched manifest's
for k in llvm triple datalayout llc-flags llc-opt-flags opt-flags lld-flags; do
  pin=$(show $PIN:nitpick.toml | grep -E "^$k +=" | sed -E 's/ +/ /g')
  ours=$(grep -E "^$k +=" "$d/nitpick.toml" | sed -E 's/ +/ /g')
  if [ -n "$pin" ] && [ "$pin" = "$ours" ]; then echo "§1.2 $k: the same as the compiler's at the pin"; else echo "§1.2 $k: DIFFERS -- pin [$pin] ours [$ours]"; fi
done
echo "§1.2 the compiler's BUILD_REFERENCE.md §1 at the pin: $(show $PIN:meta/specs/BUILD_REFERENCE.md | grep -c 'One schema (D-077). Six tables') line(s) with \"Six tables\"; and \"$(show $PIN:meta/specs/BUILD_REFERENCE.md | grep -oE 'manifest carries the same two rows as this one')\"; \"$(show $PIN:meta/specs/BUILD_REFERENCE.md | grep -oE 'refuse a manifest without the two rows BY')\""
echo "§1.2 the compiler's D-349 at the pin: $(show $PIN:meta/NOTICES.md | grep -oE 'THE TOOLCHAIN PIN MOVES TO LLVM 20\.1\.8' | head -1); \"$(show $PIN:meta/NOTICES.md | grep -oE 'REFUSE 20\.1\.2 from it' | head -1)\""
python3 -B - "$d/nitpick.toml" <<'PY'
import sys, tomllib
m = tomllib.load(open(sys.argv[1], "rb"))
print("§1.2 the tables our manifest carries: %s; and %d test entries: %s" % (
    " ".join("[%s]" % k for k in m if k != "test"), len(m["test"]),
    ", ".join("%s (%s%s, %s)" % (t["name"], t["stage"], "/" + t["kind"] if "kind" in t else "", t["path"])
              for t in m["test"])))
PY

# §1.3 -- every new module compiles as a root, and a module named `sockopt` compiles where one named `raw` does not
for f in $(cd "$d" && ls src/lib.npk src/*/*.npk tests/conformance/*.npk); do echo "§1.3 $(cd "$d/$(dirname "$f")" && "$NPKC" "$(basename "$f")" -o /dev/null > "$F/o" 2>&1; echo "$f: npkc $?, $(wc -c < "$F/o") bytes of diagnostics")"; done
mkdir -p "$F/sockopt"; printf "mod:sockopt;\n\npub func:level = int64() never fails {\n    pass 1i64;\n};\n" > "$F/sockopt/sockopt.npk"
echo "§1.3 a module named sockopt: $(codes "$F/sockopt/sockopt.npk")"
# `mod:sys;` shares the builtin's name: the builtin still calls the kernel inside the module and in a program that
# imports it -- getpid by the module's function and by the builtin, the two equal
mkdir -p "$F/sysmod/src/sys" "$F/sysmod/root"
printf '%s\n' 'mod:sys;' '' 'pub func:pid_raw = int64() never fails {' '    Result<int64>:r = sys(39i64);' \
  '    if (r.is_error) { pass 0i64 - 1i64; }' '    pass r.value;' '};' > "$F/sysmod/src/sys/sys.npk"
printf '%s\n' 'mod:sys_root;' '' 'use "../src/sys/sys.npk".*;' '' 'func:main = int32(cstring[]:_~argv) {' \
  '    int64:a = raw pid_raw();' '    Result<int64>:b = sys(39i64);' '    if (b.is_error) { exit 11i32; }' \
  '    if (a != b.value) { exit 12i32; }' '    if (a < 1i64) { exit 13i32; }' '    exit 0i32;' '};' '' \
  'func:failsafe = int32(Error:e) {' '    pick (e) {' '        (HeapBadRequest)    { exit 91i32; },' \
  '        (HeapOom)           { exit 92i32; },' '        (IntOverflow)       { exit 93i32; },' \
  '        (Unreachable)       { exit 95i32; },' '        (WildLeak)          { exit 96i32; },' \
  '        (StackExhausted)    { exit 106i32; },' '        (MachineFault)      { exit 107i32; },' \
  '        (*)                 { exit 99i32; }' '    }' '    exit 9i32;' '};' > "$F/sysmod/root/sys_root.npk"
echo "§1.3 a module named sys, calling the builtin, imported by a root that calls both: $(run4 "$F/sysmod/root/sys_root.npk" | sed 's/^sys_root: //')"

# §1.4 -- what the consumer owes: the bill of a root importing the umbrella
echo "§1.4 $(bill "$d/src/lib.npk")"

# §1.5 -- the workflow, read as GitHub reads it: YAML 1.2, where an unquoted hex value can be a number
W=$d/.github/workflows/ci.yml
python3 -B - "$W" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
# A plain (unquoted) scalar YAML 1.2's core schema reads as a number: an int, or digits with an exponent.
NUM = re.compile(r"^[-+]?(\.[0-9]+|[0-9]+(\.[0-9]*)?)([eE][-+]?[0-9]+)?$")
plain = []
for line in text.split("\n"):
    m = re.match(r"^\s*(?:- )?([A-Za-z_][\w-]*):\s+([^\s#'\"][^#]*?)\s*$", line)
    if m and NUM.match(m.group(2)):
        plain.append("%s (%s)" % (m.group(1), m.group(2)))
quoted = re.findall(r'^\s*([A-Z0-9_]+): "([^"]*)"', text, re.M)
hexq = [k for k, v in quoted if re.fullmatch(r"[0-9a-f]{7,64}", v)]
print("§1.5 plain values YAML 1.2 reads as numbers: %s -- and none of them a commit or a digest" % (", ".join(plain) or "none"))
print("§1.5 quoted hex values: %s" % ", ".join(hexq))
PY
python3 -B - "$W" "$F" <<'PY'
import os, sys, yaml
d = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
job = d["jobs"]["build"]
steps = job["steps"]
print("§1.5 the workflow parses; %d steps; runs-on %s; on %s; steps that use an action: %d" % (
    len(steps), job["runs-on"], " ".join(sorted(d[True])), sum(1 for s in steps if "uses" in s)))
for i, s in enumerate(steps):
    if "run" in s:
        open(os.path.join(sys.argv[2], "run%02d.sh" % i), "w", encoding="utf-8").write(s["run"])
PY
n=0; bad=0; for r in "$F"/run*.sh; do n=$((n+1)); bash -n "$r" || bad=$((bad+1)); done
echo "§1.5 the steps' scripts: $n, and $bad that bash -n refuses; lines naming an action: $(grep -cE '^\s*(- )?uses:' "$W")"
pinrow=$(grep -E '^  npkc\.ll ' "$WB/.internal/toolchain/$PIN/PIN.md" | awk '{print $2, $3}')
echo "§1.5 the pinned rows: NITPICK_COMMIT $( [ "$(sed -nE 's/^  NITPICK_COMMIT: "([0-9a-f]+)"$/\1/p' "$W")" = "$PIN_FULL" ] && echo 'is the pin' || echo 'is NOT the pin'); npkc.ll $( [ "$(sed -nE 's/^  NPKC_LL_SHA256: "([0-9a-f]+)"$/\1/p' "$W") $(sed -nE 's/^  NPKC_LL_BYTES: "([0-9]+)"$/\1/p' "$W")" = "$pinrow" ] && echo "is PIN.md's row of notice 118" || echo "is NOT PIN.md's row")"
echo "§1.5 the compiler's bootstrap harness at the pin: $(show $PIN:bootstrap/harness/quickemit.py > /dev/null 2>&1 && echo 'bootstrap/harness/quickemit.py exists' || echo 'NO quickemit.py')"

# §1.6 -- the shapes, over every `.npk` the patches add, comments and strings blanked
grep -ohE '^\+\+\+ b/.*\.npk$' "$T1"/step*.patch | sed 's|^+++ b/||' > "$F/added"
echo "§1.6 the $(wc -l < "$F/added") .npk file(s) the patches add:"
python3 -B "$TL/shapes.py" $(sed "s|^|$d/|" "$F/added") | tail -n +2
echo "§1.6 the rulings over them:"; python3 -B "$TL/rulings.py" $(sed "s|^|$d/|" "$F/added") | tail -n +2

# §1.7 -- every declared name, and `sockopt`, against the pin's keyword table (landing 113)
show $PIN:src/frontend/keywords.npk > "$F/keywords.npk"
echo "§1.7 the added files: $(python3 -B "$TL/names.py" --count "$F/keywords.npk" $(sed "s|^|$d/|" "$F/added") | head -1)"
echo "§1.7 sockopt, raw, import in the keyword table: $(for w in sockopt raw import; do printf '%s %s; ' $w "$(grep -c "string_eq(text, \"$w\")" "$F/keywords.npk")"; done)"

# §1.8 -- the placeholders: every one in the patches, and the ones this subcycle declares numbered from the base
echo "§1.8 files the patches touch that hold \`@@PD-\` as the tree stands: $(n=0; for f in $(grep -ohE '^\+\+\+ b/.*' "$T1"/step*.patch | sed 's|^+++ b/||' | sort -u); do [ -f "$REPO/$f" ] && grep -q '@@PD-' "$REPO/$f" && n=$((n+1)); done; echo $n)"
echo "§1.8 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T1"/step*.patch | sort -u | tr '\n' ' ')"
echo "§1.8 declared by them: $(grep -ohE '^\+### @@PD-[0-9]+@@' "$T1"/step*.patch | grep -oE 'PD-[0-9]+' | tr '\n' ' ')"
echo "§1.8 numbered by decisions.txt: $(python3 -B -c "
import sys; sys.path.insert(0, '$TL'); import apply
t = apply.numbers(); print(' '.join('%s=base+%d' % (k, int(t[k].split('-')[1]) - apply.base_number()) for k in sorted(t) if 'PD-164' <= k <= 'PD-168'))")"

# §1.9 -- every pointer the patches write
python3 -B "$TL/pointers.py" "$d" "$T1" | sed "s|$d/||g; s/^§1\.8/§1.9/"

# §1.10 -- B-18 as the tree stands, a drawing, and as the patches leave it, a table: each row the reach of the
# drawing's arrows from its module, with the two arrows the specifications require added
git -C "$REPO" show HEAD:meta/specs/BUILD.md > "$F/build_before.md"
python3 -B - "$F/build_before.md" "$d/meta/specs/BUILD.md" <<'PY'
import re, sys
before = open(sys.argv[1], encoding="utf-8").read()
draw = before[before.index("**Rule B-18 —"):before.index("**Rule B-19")]
fence = draw[draw.index("```") + 3:draw.rindex("```")]
cols = []
for line in fence.split("\n"):
    for m in re.finditer(r"[a-z]+", line):
        cols.append("%s %d" % (m.group(), m.start()))
print("§1.10 the drawing as the tree stands, each name's column: " + ", ".join(cols))
print("§1.10 its sentence: \"%s\"" % re.search(r"A module may not import a module to its left\.", draw).group(0))
# The drawing's arrows, as read: importer -> imported.
drawn = [("server", "stream"), ("stream", "socket"), ("stream", "addr"), ("datagram", "socket"), ("datagram", "addr"),
         ("ancillary", "socket"), ("ancillary", "addr"), ("socket", "sys"), ("socket", "option"), ("sys", "core"),
         ("addr", "core")]
added = [("option", "sys"), ("socket", "addr")]
edges = drawn + added
def reach(m):
    out, todo = set(), [m]
    while todo:
        x = todo.pop()
        for a, b in edges:
            if a == x and b not in out:
                out.add(b)
                todo.append(b)
    return out
after = open(sys.argv[2], encoding="utf-8").read()
table = after[after.index("**Rule B-18 ("):after.index("**Rule B-19")]
rows = dict(re.findall(r"^\| `(\w+)` \| ([^|]+) \|$", table, re.M))
same = [m for m in rows if set(re.findall(r"`(\w+)`", rows[m])) == reach(m)]
print("§1.10 the table as the patches leave it: %d rows; the reach of the drawing's %d arrows and the %d added: %d of %d rows equal it" % (
    len(rows), len(drawn), len(added), len(same), len(rows)))
print("§1.10 socket's row names stream: %s" % ("yes" if "stream" in rows.get("socket", "") else "no"))
PY

# §1.11 -- the compiler's text that BUILD.md §1's note and O-N2's re-read cite, at the pin
echo "§1.11 rootlist_init in the driver: $(git -C "$NPK_TREE" grep -c 'rootlist_init()' $PIN -- src/driver/pipeline.npk | sed "s|^$PIN:||")"
echo "§1.11 rootlist_add( called in: $(git -C "$NPK_TREE" grep -l 'rootlist_add(' $PIN | sed "s|^$PIN:||" | tr '\n' ' ')"
echo "§1.11 npkg's usage line: $(show $PIN:npkg/main.npk | grep -oE '"usage: npkg build[^"]*"' | sed -E 's/ \[[^]]*\]//g')"
echo "§1.11 npkg update: $(show $PIN:npkg/main.npk | grep -oE 'npkg update: refused -- there is nothing to resolve in a single-repository world')"
echo "§1.11 the key target, read in npkg: $(git -C "$NPK_TREE" grep -n 'text_eq(key, "target")' $PIN -- npkg/ | sed "s|^$PIN:||" | cut -d: -f1,2)"
echo "§1.11 the compiler's cycle 1.5: $(show $PIN:meta/roadmap/OPEN_DECISIONS.md | grep -oE 'cycle 1\.5 CLOSED 2026-09-25' | head -1); the pin's subject: $(git -C "$NPK_TREE" log -1 --format=%s $PIN | cut -d: -f1)"

# §1.12 -- O-K4's two facts: the builder's consuming calls, and whose types they return
echo "§1.12 SOCKET_MODEL.md K-12: $(grep -oE 'builder\.(listen|connect)\([^)]*\)( +)-> Tcp[A-Za-z]+' "$REPO/meta/specs/SOCKET_MODEL.md" | sed -E 's/ +/ /g' | tr '\n' ';')"
echo "§1.12 src/stream/README.md: $(grep -oE '`TcpListener`/`TcpStream`' "$REPO/src/stream/README.md")"
rm -rf "${F:?}"
