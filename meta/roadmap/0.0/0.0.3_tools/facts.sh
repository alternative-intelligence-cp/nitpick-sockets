# meta/roadmap/0.0/0.0.3_tools/facts.sh -- re-derives `0.0.3.md` §1, block 0b. Sourced after `../tools/env.sh`, so
# `$REPO`, `$A`, `$NPKC`, `$NPKRT`, `$NPK_TREE`, `$PIN`, `$WB` and the helpers are set. Writes only under `$A/facts`,
# and removes it. Reads the compiler's tree with `git show` alone. Prints no path above the repository: every scratch
# path is cut to its name.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T3=$REPO/meta/roadmap/0.0/0.0.3_tools
TL=$REPO/meta/roadmap/0.0/tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in 1 2; do python3 -B "$TL/apply.py" "$d" 0.0.3 $s > /dev/null; done
show() { git -C "$NPK_TREE" show "$1"; }
FS='func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'

# §1.1 -- the tree it starts from: cycle 0.0.2's record
echo "§1.1 harness holds: $(git -C "$REPO" ls-files harness | sed 's|^harness/||' | tr '\n' ' ')"
echo "§1.1 the runner judges: $(grep -oE '^JUDGED = \{.*\}' "$REPO/harness/run.py" | grep -oE '\("[a-z]+", (None|"[a-z]+")\)' | tr -d '()"' | sed 's/, None//; s/, /\//' | tr '\n' ' ')"
python3 -B - "$REPO/nitpick.toml" <<'PY'
import sys, tomllib
m = tomllib.load(open(sys.argv[1], "rb"))
print("§1.1 nitpick.toml's [[test]] entries: %d (%s)" % (len(m["test"]), ", ".join(
    "%s %s%s" % (t["name"], t["stage"], "/" + t["kind"] if "kind" in t else "") for t in m["test"])))
PY
for t in tests/rejection tests/unit tests/unit/net tests/unit/extern; do
  printf '§1.1 %s: %s\n' "$t/" "$( [ -d "$REPO/$t" ] && echo "$(find "$REPO/$t" -maxdepth 1 -name '*.npk' | wc -l) .npk file(s)" || echo 'absent')"
done

# §1.2 -- the compiler's judges of `parse`, `check` and `accept` at the pin, and what `npkc` offers instead
for t in parse_check check; do
  echo "§1.2 the compiler's tools/$t.npk at the pin: a $(git -C "$NPK_TREE" cat-file -t "$PIN:tools/$t.npk"), $(show "$PIN:tools/$t.npk" | wc -l) lines, its main $(show "$PIN:tools/$t.npk" | grep -m1 -oE '(async )?func:main')"
done
echo "§1.2 npkc's usage: $(cd "$F" && "$NPKC" --help 2>&1 | grep -m1 '^usage:')"

# §1.3 -- the codes and sites of the self-check's fixtures, each a root on its own
mkdir -p "$F/fx"
printf 'mod:noparse;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32\n};\n\n%s\n' "$FS" > "$F/fx/noparse.npk"
printf 'mod:plainbind;\n\nint64:COUNTER = 0i64;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n\n%s\n' "$FS" > "$F/fx/plainbind.npk"
printf 'mod:twocodes;\n\nint64:COUNTER = 0i64;\n\nfunc:main = int32(cstring[]:_~argv) {\n    string:s = string_concat("ab", "c");\n    uint8[]:p = string_bytes(s);\n    exit 0i32;\n};\n\n%s\n' "$FS" > "$F/fx/twocodes.npk"
printf 'mod:fine;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n\n%s\n' "$FS" > "$F/fx/fine.npk"
for f in noparse plainbind twocodes fine; do echo "§1.3 $(codes "$F/fx/$f.npk")"; done

# §1.4 -- an identity is a module and a name: what a consumer owes, by NITPICK-REACH-003's own list
for v in imported declared; do
  mkdir -p "$F/id-$v/src/socket" "$F/id-$v/src/stream" "$F/id-$v/root"
  printf 'mod:socket;\n\npub error:ESockState;\n\npub func:sock_check = int64(int64:x) {\n    if (x < 0i64) { fail ESockState; }\n    pass x;\n};\n' > "$F/id-$v/src/socket/socket.npk"
  own=""; [ "$v" = declared ] && own='pub error:ESockState;\n\n'
  printf "mod:stream;\n\nuse \"../socket/socket.npk\".*;\n\n${own}pub func:stream_check = int64(int64:x) {\n    if (x > 9i64) { fail ESockState; }\n    pass x;\n};\n" > "$F/id-$v/src/stream/stream.npk"
  printf 'mod:root;\n\nuse "../src/stream/stream.npk".*;\nuse "../src/socket/socket.npk".*;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > "$F/id-$v/root/root.npk"
  echo "§1.4 stream raising ESockState, $( [ $v = imported ] && echo 'socket'"'"'s, through its import' || echo 'its own declaration'): a consumer owes $(cd "$F/id-$v/root" && "$NPKC" root.npk -o /dev/null 2>&1 | grep -oE '[0-9]+ identities: [^-]*' | sed 's/ *$//')"
done

# §1.5 -- the reader against the compiler: a `use` after a comment's CR, in a block comment and in a string, and an
# escaped path; `npkc` compiles the file with the escaped path's file present and the others' absent, and refuses it
# with that file absent; and `lexical.imports()` reads the escaped path and no other
mkdir -p "$F/rd/src/core" "$F/rd/src/sys"
printf 'mod:sys;\n\npub fixed int64:SYS_SOCKET = 41i64;\n' > "$F/rd/src/sys/sys.npk"
printf 'mod:core;\n\n// use "../server/server.npk".*;\r use "../server/server.npk".*;\n/* use "../server/server.npk".*; */\nfixed int64:K = 0i64; // "use \\"../server/server.npk\\""\nuse "..\\x2fsys/sys.npk".*;\n\npub func:core_n = int64() never fails {\n    pass SYS_SOCKET;\n};\n' > "$F/rd/src/core/core.npk"
echo "§1.5 the reader's fixture, src/server/ absent: $(codes "$F/rd/src/core/core.npk")"
python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1]); import lexical
print('§1.5 lexical.imports() reads: %s' % lexical.imports(lexical.read(sys.argv[2])))" "$d/harness" "$F/rd/src/core/core.npk"
mv "$F/rd/src/sys/sys.npk" "$F/rd/src/sys/sys.away"
echo "§1.5 the same, src/sys/sys.npk absent too: $(codes "$F/rd/src/core/core.npk")"

# §1.6 -- the floor's `write`: a module cannot declare its own, and the prelude's ByteWriter calls it
printf 'mod:wr;\n\npub func:write = int64(int64:x) never fails {\n    pass x;\n};\n' > "$F/fx/wr.npk"
echo "§1.6 a module declaring func:write: $(codes "$F/fx/wr.npk")"
mkdir -p "$F/bw"
printf 'mod:bw;\n\npub async func:bw_send = int64(int64:descr, fixed uint8[]:wire) {\n    ByteWriter:w = ByteWriter{ sink: own_fd((descr =>! int32) =>! fd) };\n    int64:n = await w.write(wire, raw duration_ms(100i64)) ?! Unreachable;\n    pass n;\n};\n' > "$F/bw/bw.npk"
printf 'mod:floor;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n\n%s\n' "$FS" > "$F/bw/floor.npk"
( cd "$F/bw" && "$NPKC" bw.npk -o bw.ll && "$NPKC" floor.npk -o floor.ll )
python3 -B - "$d/harness" "$F/bw/floor.ll" "$F/bw/bw.ll" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import irscan
base = irscan.edges(open(sys.argv[2]).read())
f = irscan.findings(open(sys.argv[3]).read(), base, "bw.npk")
print("§1.6 a module holding the prelude's ByteWriter: the call-edge scan's findings: %d -- %s" % (len(f), f[0].split(" -- ")[0] if f else "none"))
PY

# §1.7 -- a socket left open at a clean exit: D-151 sees no descriptor (cycle 0.0.0's shape)
printf "mod:open_at_exit;\n\nfunc:main = int32(cstring[]:_~argv) {\n    Result<int64>:r = sys(41i64, 2i64, 526337i64, 6i64);\n    if (r.is_error) { exit 10i32; }\n    exit 0i32;\n};\n\n%s\n" "$FS" > "$F/fx/open_at_exit.npk"
echo "§1.7 a socket left open at a clean exit: $(run4 "$F/fx/open_at_exit.npk" | sed 's/^open_at_exit: //')"

# §1.8 -- the loopback the `loopback` stage runs over, and an address no interface here holds
python3 -B - <<'PY'
import socket
for fam, addr in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1"), (socket.AF_INET, "192.0.2.1")):
    s = socket.socket(fam, socket.SOCK_STREAM)
    try:
        s.bind((addr, 0)); print("§1.8 a TCP socket bound to %s port 0: yes" % addr)
    except OSError as e:
        print("§1.8 a TCP socket bound to %s port 0: no, errno %d" % (addr, e.errno))
    finally:
        s.close()
PY

# §1.9 -- the manifest reader's schema is the compiler's `schema_allows` at the pin, table for table, key for key
show "$PIN:npkg/manifest.npk" > "$F/manifest.npk"
python3 -B - "$F/manifest.npk" "$d/harness" <<'PY'
import re, sys
sys.path.insert(0, sys.argv[2])
import manifest
body = open(sys.argv[1], encoding="utf-8").read()
fn = body[body.index("func:schema_allows"):]
fn = fn[:fn.index("\n};")]
theirs, any_key, sec = {}, set(), None
for line in fn.split("\n"):
    m = re.search(r'text_eq\(section, "([^"]+)"\)\) \{ pass true; \}', line)
    if m:
        any_key.add(m.group(1)); continue
    m = re.search(r'text_eq\(section, "([^"]+)"\)', line)
    if m:
        sec = m.group(1); theirs[sec] = set(); continue
    m = re.search(r'text_eq\(key, "([^"]+)"\)', line)
    if m:
        theirs[sec].add(m.group(1))
print("§1.9 schema_allows at the pin and harness/manifest.py's schema: %s" % (
    "the same" if theirs == manifest.SCHEMA and any_key == manifest.ANY_KEY else "DIFFERENT"))
PY

# §1.10 -- the authorities the tree checks read, counted apart from the checks
S=$d/meta/specs
echo "§1.10 BUILD.md B-18's table: $(awk '/^\*\*Rule B-18/,/^\*\*Rule B-19/' "$S/BUILD.md" | grep -cE '^\| `[a-z]+` \|') rows"
echo "§1.10 SAFETY.md §3's table: $(awk '/^## 3\./,/^## 4\./' "$S/SAFETY.md" | grep -cE '^\| `E[A-Za-z]+` \|') identities ($(awk '/^## 3\./,/^## 4\./' "$S/SAFETY.md" | grep -oE '^\| `E[A-Za-z]+` \|.*\| `src/[a-z]+/` \|$' | sed -E 's/^\| `([A-Za-z]+)` \|.*\| `(src\/[a-z]+\/)` \|$/\1 \2/' | tr '\n' ';' | sed 's/;$//'))"
echo "§1.10 SOCKET_MODEL.md K-1's table: $(awk '/^\*\*Rule K-1\./,/^\*\*Rule K-2 /' "$S/SOCKET_MODEL.md" | grep -cE '^\| `[a-z0-9]+` \| [0-9]+ \|') calls; the kernel constants meta/specs/ states, a bound's NSOCK_ aside: $(cat "$S"/*.md | grep -oE '`[A-Z][A-Z0-9_]+` (= |\()[0-9]+' | grep -v '^`NSOCK_' | sed -E 's/^`([A-Z0-9_]+)`.*/\1/' | sort -u | wc -l) names ($(cat "$S"/*.md | grep -oE '`[A-Z][A-Z0-9_]+` (= |\()[0-9]+' | grep -v '^`NSOCK_' | wc -l) statements)"
echo "§1.10 sizes stated in meta/specs/: headings $(cat "$S"/*.md | grep -cE '^### `[a-z_0-9]+` — [0-9]+ bytes'), declarations $(cat "$S"/*.md | grep -cE '^pub (struct|enum):[A-Za-z0-9]+ *=.*// *[0-9]+ bytes'), prose $(cat "$S"/*.md | grep -cE '`struct [a-z]+`: \*\*[0-9]+ bytes\*\*')"
echo "§1.10 sizes the probes assert: by comparison $(cat "$d"/tests/probe/*.npk "$d"/tests/probe/refused/*.npk | grep -cE '#size_of<[A-Za-z0-9]+>\(\) *(!=|==) *[0-9]+i64'), by exit $(grep -lE 'exit \(width =>! int32\)' "$d"/tests/probe/*.npk | wc -l)"

# §1.11 -- the shapes and names: the patches add or change no `.npk`; every declared name of the patched tree read
echo "§1.11 .npk files the patches add or change: $(grep -ohE '^\+\+\+ b/.*\.npk$' "$T3"/step*.patch | sort -u | wc -l)"
show "$PIN:src/frontend/keywords.npk" > "$F/keywords.npk"
( cd "$d" && python3 -B "$TL/names.py" --count "$F/keywords.npk" $(git ls-files '*.npk') ) | sed 's/^/§1.11 the patched tree: /'

# §1.12 -- the placeholders, and §1.13 -- every pointer the patches' added lines write
echo "§1.12 files the patches touch that hold \`@@PD-\` as the tree stands: $(n=0; for f in $(grep -ohE '^\+\+\+ b/.*' "$T3"/step*.patch | sed 's|^+++ b/||' | sort -u); do [ -f "$REPO/$f" ] && grep -q '@@PD-' "$REPO/$f" && n=$((n+1)); done; echo $n)"
echo "§1.12 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T3"/step*.patch | sort -u | tr '\n' ' ')"
echo "§1.12 declared by them: $(grep -ohE '^\+### @@PD-[0-9]+@@' "$T3"/step*.patch | grep -oE 'PD-[0-9]+' | tr '\n' ' ')"
echo "§1.12 numbered by decisions.txt: $(python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1]); import apply
t = apply.numbers(); print(' '.join('%s=base+%d' % (k, int(t[k].split('-')[1]) - apply.base_number()) for k in sorted(t) if 'PD-173' <= k <= 'PD-175'))" "$TL")"
python3 -B "$TL/pointers.py" "$d" "$T3" | sed 's/^§1\.8 /§1.13 /'

# §1.14 -- the interpreter
echo "§1.14 $(python3 --version)"
rm -rf "${F:?}"
