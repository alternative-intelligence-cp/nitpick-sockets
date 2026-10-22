# meta/roadmap/0.0/0.0.2_tools/facts.sh -- re-derives `0.0.2.md` §1, block 0b. Sourced after `../tools/env.sh`, so
# `$REPO`, `$A`, `$NPKC`, `$NPKRT`, `$NPK_TREE`, `$PIN`, `$WB` and the helpers are set. Writes only under `$A/facts`,
# and removes it. Reads the compiler's tree with `git show` alone. Prints no path above the repository: every scratch
# path is cut to its name.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T2=$REPO/meta/roadmap/0.0/0.0.2_tools
TL=$REPO/meta/roadmap/0.0/tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in 1 2 3; do python3 -B "$TL/apply.py" "$d" 0.0.2 $s > /dev/null; done
cut_paths() { sed -e "s|$d/||g" -e "s|$F/||g" -e "s|$REPO/||g"; }
show() { git -C "$NPK_TREE" show "$1"; }
FS='func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (IntOverflow)       { exit 93i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'

# §1.1 -- the tree it starts from: cycle 0.0.1's record, and this subcycle's research gate
echo "§1.1 harness holds: $(git -C "$REPO" ls-files harness | tr '\n' ' ')"
echo "§1.1 the stub says: $(cd "$REPO" && python3 -B harness/run.py)"
python3 -B - "$REPO/nitpick.toml" "$REPO/.github/workflows/ci.yml" <<'PY'
import sys, tomllib, yaml
m = tomllib.load(open(sys.argv[1], "rb"))
steps = yaml.safe_load(open(sys.argv[2]))["jobs"]["build"]["steps"]
print("§1.1 nitpick.toml's [[test]] entries: %d (%s); ci.yml's steps: %d" % (len(m["test"]), ", ".join(
    "%s %s%s" % (t["name"], t["stage"], "/" + t["kind"] if "kind" in t else "") for t in m["test"]), len(steps)))
PY
g=$REPO/meta/research/llvm-20.1.8-tarball.md
echo "§1.1 the research gate's digest: llvm-20.1.8-tarball.md $(grep -m1 -oE 'As of [0-9]{4}-[0-9]{2}-[0-9]{2}' "$g" 2>/dev/null || echo MISSING); $(heading "$g"); lines naming the tarball's sha256 and size: $(grep -cE '^LLVM-20\.1\.8-Linux-X64\.tar\.xz sha256 [0-9a-f]{64} bytes [0-9]+$' "$g" 2>/dev/null)"

# §1.2 -- the manifest's schema is the compiler's `schema_allows` at the pin, table for table, key for key
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
same = theirs == manifest.SCHEMA and any_key == manifest.ANY_KEY
print("§1.2 schema_allows at the pin: %d tables with keys (%s) and %s with any key; harness/manifest.py: %s"
      % (len(theirs), " ".join(sorted(theirs)), " ".join(sorted(any_key)), "the same" if same else "DIFFERENT"))
PY

# §1.3 -- the stage names: BUILD_REFERENCE.md §7.1's table at the pin, and this library's two; the markers: every one
# `npkg/expect.npk` reads at the pin, each in exactly one of the harness's two lists
show "$PIN:meta/specs/BUILD_REFERENCE.md" > "$F/br.md"
show "$PIN:npkg/expect.npk" > "$F/expect.npk"
python3 -B - "$F/br.md" "$F/expect.npk" "$d/harness" <<'PY'
import re, sys
sys.path.insert(0, sys.argv[3])
import expect, manifest
t = open(sys.argv[1], encoding="utf-8").read()
sec = t[t.index("### 7.1 Test targets"):t.index("### 7.2")] if "### 7.2" in t else t[t.index("### 7.1 Test targets"):]
names = set(re.findall(r"^\| `([a-z]+)`", sec, re.M))
print("§1.3 the stages §7.1's table names: %d (%s); the harness adds %s" % (
    len(names), " ".join(sorted(names)), " ".join(sorted(manifest.KNOWN_STAGES - names))))
e = open(sys.argv[2], encoding="utf-8").read()
read = re.findall(r'text_starts_with\(body, "([a-z-]+:?)"\)', e)
judged, refused = set(expect.MARKERS_JUDGED), set(expect.MARKERS_REFUSED)
whole = all((m in judged) != (m in refused) for m in read)
print("§1.3 npkg/expect.npk reads %d markers; the harness judges %d of them (%s), refuses the other %d by name, and every one is in exactly one list: %s" % (
    len(read), len(judged & set(read)), " ".join(m for m in read if m in judged), len(refused & set(read)), "yes" if whole else "NO"))
print("§1.3 the harness's own: judged %s; refused %s" % (" ".join(sorted(judged - set(read))) or "none",
                                                          " ".join(sorted(refused - set(read))) or "none"))
PY

# §1.4 -- the scans' controls, by llvm-nm, and the harness's ELF reader beside it
for p in floor syscaller floorwriter; do
  ( cd "$d/harness/baseline" && "$NPKC" $p.npk -o "$F/$p.ll" ) && llc -O0 -filetype=obj -relocation-model=static "$F/$p.ll" -o "$F/$p.o"
  llvm-nm --undefined-only "$F/$p.o" | awk '{print $2}' | sort > "$F/$p.nm"
done
echo "§1.4 llvm-nm: the floor's object has $(wc -l < "$F/floor.nm") undefined symbols ($(tr '\n' ' ' < "$F/floor.nm" | sed 's/ $//')); the syscaller's $(wc -l < "$F/syscaller.nm"), the difference $(comm -3 "$F/floor.nm" "$F/syscaller.nm" | tr -d '\t' | tr '\n' ' ' | sed 's/ $//'); the floor-writer's $(wc -l < "$F/floorwriter.nm"), the difference $(comm -3 "$F/floor.nm" "$F/floorwriter.nm" | tr -d '\t' | tr '\n' ' ' | sed 's/ $//')"
python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1])
import elf
ok = all(elf.Obj(sys.argv[2] + '/%s.o' % p).undefined() == open(sys.argv[2] + '/%s.nm' % p).read().split() for p in ('floor', 'syscaller', 'floorwriter'))
print('§1.4 harness/elf.py reads the same three sets: %s' % ('yes' if ok else 'NO'))
" "$d/harness" "$F"

# §1.5 -- the runtime classed whole: every global symbol of the pinned runtime object -- all a module's call can
# resolve to -- one row of runtime_symbols.tsv, and no row anything else (llvm-nm, apart from the harness's reader)
llvm-nm --defined-only --extern-only "$NPKRT" | awk '{print $3}' | sort -u > "$F/rt.nm"
python3 -B - "$F/rt.nm" "$d/harness/runtime_symbols.tsv" "$(llvm-nm --defined-only "$NPKRT" | wc -l)" <<'PY'
import collections, sys
g = set(open(sys.argv[1]).read().split())
rows = [l.rstrip("\n").split("\t") for l in open(sys.argv[2], encoding="utf-8") if l.strip() and not l.startswith("#")]
names = [r[0] for r in rows]
whole = len(names) == len(set(names)) and set(names) == g
print("§1.5 the runtime object defines %s symbols, %d of them global -- every global one a row of runtime_symbols.tsv, and no row anything else: %s" % (
    sys.argv[3], len(g), "yes" if whole else "NO"))
for half, label in (("deny", "denied, by facet"), ("library", "the library's own"), ("floor", "the floor")):
    c = collections.Counter(r[1].split(": ", 1)[1] for r in rows if r[1].startswith(half + ": "))
    print("§1.5 %s: %s -- %d" % (label, "; ".join("%s %d" % kv for kv in sorted(c.items())), sum(c.values())))
PY

# §1.6 -- one module per root; and what a module compiled alone names: `npk_failsafe` where its code can trap, and,
# for a module of the library's own shapes, call edges the scan reads as the library's or the floor's
mkdir -p "$F/sep"
printf '%s\n' 'mod:helper;' '' 'pub func:helper_twice = int32(int32:x) never fails {' '    pass x * 2i32;' '};' > "$F/sep/helper.npk"
printf '%s\n' 'mod:root;' '' 'use "./helper.npk".*;' '' 'func:main = int32(cstring[]:_~argv) {' '    exit (raw helper_twice(21i32));' '};' '' "$FS" > "$F/sep/root.npk"
( cd "$F/sep" && "$NPKC" root.npk -o root.ll ) && llc -O0 -filetype=obj -relocation-model=static "$F/sep/root.ll" -o "$F/sep/root.o" \
  && ld.lld -static "$F/sep/root.o" "$NPKRT" -o "$F/sep/root"
"$F/sep/root"; rc=$?
echo "§1.6 a root importing a module: its emission DEFINES the imported function $(grep -c '^define .*@"npk\.helper\.helper_twice"' "$F/sep/root.ll") time(s); linked as one object and npkrt.o, it exits $rc"
printf '%s\n' 'mod:plain;' '' 'pub func:one = int64() never fails {' '    pass 1i64;' '};' > "$F/sep/plain.npk"
printf '%s\n' 'mod:adds;' '' 'pub func:add = int64(int64:a, int64:b) {' '    pass a + b;' '};' > "$F/sep/adds.npk"
printf '%s\n' 'mod:waits;' '' 'pub async func:wait_readable = NIL(int32:descr) {' '    Result<NIL>:w = await io_ready(descr, 1i32, raw duration_ms(1000i64));' \
  '    if (w.is_error) { fail w.err; }' '    pass NIL;' '};' > "$F/sep/waits.npk"
for m in plain adds waits; do
  ( cd "$F/sep" && "$NPKC" $m.npk -o $m.ll ) && llc -O0 -filetype=obj -relocation-model=static "$F/sep/$m.ll" -o "$F/sep/$m.o"
  echo "§1.6 a module compiled alone, $m.npk: its object names npk_failsafe: $(llvm-nm --undefined-only "$F/sep/$m.o" | awk '{print $2}' | grep -cx npk_failsafe)"
done
printf '%s\n' 'mod:libshape;' '' 'fixed int64:SYS_SENDTO = 44i64;' 'fixed int64:MSG_NOSIGNAL = 16384i64;' '' \
  'pub async func:wait_readable = NIL(int32:descr) {' '    Result<NIL>:w = await io_ready(descr, 1i32, raw duration_ms(1000i64));' '    if (w.is_error) { fail w.err; }' '    pass NIL;' '};' '' \
  'pub async func:handler = NIL(move OwnedFd:o) {' '    wild int8->:one = calloc(1i64, 8i64);' '    <-one = 55i8;' \
  '    Result<int64>:r = sys(SYS_SENDTO, o.value, one, 1i64, MSG_NOSIGNAL, 0i64, 0i64);' '    dalloc(one);' '    if (r.is_error) { fail r.err; }' '    pass NIL;' '};' '' \
  'pub async func:serve = NIL(int64:descr) {' '    OwnedFd:o = own_fd((descr =>! int32) =>! fd);' '    drop handler(move(o));' '    pass NIL;' '};' '' \
  'pub func:hold = int64(int64:descr) {' '    OwnedFd:o = own_fd((descr =>! int32) =>! fd);' '    pass 0i64;' '};' > "$F/sep/libshape.npk"
( cd "$F/sep" && "$NPKC" libshape.npk -o libshape.ll )
python3 -B - "$d/harness" "$F/floor.ll" "$F/sep/libshape.ll" <<'PY'
import collections, sys
sys.path.insert(0, sys.argv[1])
import irscan
base = irscan.edges(open(sys.argv[2]).read())
new = irscan.edges(open(sys.argv[3]).read()) - base
rt = {c for _, c in new if c in irscan.CLASSES}
cls = collections.Counter(irscan.CLASSES[c][0].split(":")[0] for c in rt)
others = sorted({c for _, c in new} - rt)
print("§1.6 a module of the library's shapes -- a wait through io_ready, a spawn moving an OwnedFd in, a held OwnedFd, a sys call -- compiled alone: %d call edges the floor program does not have, to %d runtime symbols (%s) and %s; the scan flags %d" % (
    len(new), len(rt), ", ".join("%s %d" % kv for kv in sorted(cls.items())), " ".join(others) or "nothing else",
    len(irscan.findings(open(sys.argv[3]).read(), base, "libshape"))))
print("§1.6 the scope join's npk_thread_join, called from: %s" % (" ".join(sorted({f for f, c in new if c == "npk_thread_join"})) or "nothing"))
PY
printf '%s\n' 'mod:lockmade;' '' 'pub func:made = int32() {' '    Mutex<int32, 3i32>:m = mutex(0i32) ?! Unreachable;' '    pass 0i32;' '};' > "$F/sep/lockmade.npk"
( cd "$F/sep" && "$NPKC" lockmade.npk -o lockmade.ll )
python3 -B - "$d/harness" "$F/floor.ll" "$F/sep/lockmade.ll" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import irscan
base = irscan.edges(open(sys.argv[2]).read())
new = irscan.edges(open(sys.argv[3]).read()) - base
print("§1.6 a module that makes a Mutex and never holds it, compiled alone: %d call edge(s) the floor program does not have, to %s -- %s; the scan flags %d" % (
    len(new), " ".join(sorted({c for _, c in new})), "; ".join(sorted({irscan.CLASSES[c][0] for _, c in new})),
    len(irscan.findings(open(sys.argv[3]).read(), base, "lockmade"))))
PY

# §1.7 -- repro: the conformance consumer from two copies, with the manifest and without (inside the repository)
for w in with without; do
  for c in a bb/deeper; do
    k="$F/rp-$w/$c"; mkdir -p "$k/tests"; cp -r "$d/src" "$k/"; cp -r "$d/tests/conformance" "$k/tests/"
    [ "$w" = with ] && cp "$d/nitpick.toml" "$k/"
    ( cd "$k/tests/conformance" && "$NPKC" import.npk -o "$F/rp-$w-$(echo $c | tr / _).ll" )
  done
  echo "§1.7 the consumer from two copies $w the manifest: $(cmp -s "$F/rp-$w-a.ll" "$F/rp-$w-bb_deeper.ll" && echo 'byte-identical' || echo 'two different modules')"
done

# §1.8 -- the markers: every file of the suites the patched manifest declares, read by the patched reader
python3 -B - "$d" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import expect, manifest
m = manifest.read(os.path.join(sys.argv[1], "nitpick.toml"))
for t in m.tests:
    files = []
    for rel in manifest.paths_of(t):
        top = os.path.join(sys.argv[1], rel)
        files += sorted(os.path.join(top, f) for f in os.listdir(top) if f.endswith(".npk"))
    es = [expect.read(f) for f in files]
    bad = [e.path for e in es if not e.readable]
    if t.get("kind") == "negative":
        tail = "expect-error %s" % " ".join(",".join(c for c, _, _ in e.errors) for e in es)
    else:
        tail = "expect-exit %s; stress %s; capped %d" % (" ".join(str(e.exit) for e in es),
            " ".join("%s x%d" % (os.path.basename(e.path)[:7], e.stress) for e in es if e.stress > 1) or "none",
            sum(1 for e in es if e.mem_cap_mib))
    print("§1.8 %s (%s%s): %d file(s), %d unreadable; %s" % (t["name"], t["stage"], "/" + t["kind"] if "kind" in t else "",
                                                          len(es), len(bad), tail))
PY

# §1.9 -- the cap's control: the floor program under caps, so a cap a unit names is known to leave the loader room
ld.lld -static "$F/floor.o" "$NPKRT" -o "$F/floor"
echo "§1.9 the floor program under an address-space cap, its exit as the shell reads it: $(for mib in 1 4 8 16 64; do ( ulimit -v $((mib * 1024)); "$F/floor" > /dev/null 2>&1 ) 2> /dev/null; printf '%s MiB %s; ' $mib $?; done | sed 's/; $//')"

# §1.10 -- the shapes, over the .npk files the patches add or change
python3 -B "$TL/shapes.py" $(grep -ohE '^\+\+\+ b/.*\.npk$' "$T2"/step*.patch | sed "s|^+++ b/|$d/|" | sort -u) | cut_paths | sed 's/^/§1.10 /'
echo "§1.10 the rulings over them: $(python3 -B "$TL/rulings.py" $(grep -ohE '^\+\+\+ b/.*\.npk$' "$T2"/step*.patch | sed "s|^+++ b/|$d/|" | sort -u) | tail -n +2 | sed 's/^ *//' | tr '\n' ';')"

# §1.11 -- landing 113's rule on names: every declared name in every `.npk` of the patched tree, held to the pin's
# keyword table (the scanner proved on its planted and clean controls by cycle 0.0.0's block 0b)
show "$PIN:src/frontend/keywords.npk" > "$F/keywords.npk"
( cd "$d" && python3 -B "$TL/names.py" --count "$F/keywords.npk" $(git ls-files '*.npk') ) | sed 's/^/§1.11 the patched tree: /'

# §1.12 -- the placeholders, and §1.13 -- every pointer the patches' added lines write
echo "§1.12 files the patches touch that hold \`@@PD-\` as the tree stands: $(n=0; for f in $(grep -ohE '^\+\+\+ b/.*' "$T2"/step*.patch | sed 's|^+++ b/||' | sort -u); do [ -f "$REPO/$f" ] && grep -q '@@PD-' "$REPO/$f" && n=$((n+1)); done; echo $n)"
echo "§1.12 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T2"/step*.patch | sort -u | tr '\n' ' ')"
echo "§1.12 declared by them: $(grep -ohE '^\+### @@PD-[0-9]+@@' "$T2"/step*.patch | grep -oE 'PD-[0-9]+' | tr '\n' ' ')"
echo "§1.12 numbered by decisions.txt: $(python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1]); import apply
t = apply.numbers(); print(' '.join('%s=base+%d' % (k, int(t[k].split('-')[1]) - apply.base_number()) for k in sorted(t) if 'PD-169' <= k <= 'PD-172'))" "$TL")"
python3 -B "$TL/pointers.py" "$d" "$T2" | sed 's/^§1\.8 /§1.13 /'

# §1.14 -- the workflow, read as GitHub reads it; its harness step's logic run against two stand-in runners; and its
# install step's run against a stand-in tarball, the digest's line right, one digit off, and missing -- `curl` a
# stand-in that copies the tarball, `HOME` the scratch, so nothing is fetched and nothing written outside it
W=$d/.github/workflows/ci.yml
python3 -B - "$W" "$F" <<'PY'
import os, re, sys, yaml
t = open(sys.argv[1], encoding="utf-8").read()
dd = yaml.safe_load(t)
steps = dd["jobs"]["build"]["steps"]
hexq = [k for k, v in re.findall(r'^\s*([A-Z0-9_]+): "([^"]*)"', t, re.M) if re.fullmatch(r"[0-9a-f]{7,64}", v)]
rows = list(dd["env"])
print("§1.14 the workflow parses; %d steps; steps that use an action: %d; env rows %d (%s), quoted %d; quoted hex values: %s" % (
    len(steps), sum(1 for s in steps if "uses" in s), len(rows), " ".join(rows),
    len(re.findall(r'^  [A-Z][A-Z0-9_]*: "', t, re.M)), ", ".join(hexq)))
for s in steps:
    if s.get("name") == "Run the harness":
        open(os.path.join(sys.argv[2], "harness_step.sh"), "w").write(s["run"])
    if str(s.get("name", "")).startswith("Install LLVM"):
        open(os.path.join(sys.argv[2], "install_step.sh"), "w").write(s["run"])
PY
for s in harness_step install_step; do bash -n "$F/$s.sh" && echo "§1.14 the $(echo $s | tr _ ' ')'s script: bash -n accepts it"; done
for k in green short; do
  mkdir -p "$F/ci-$k/harness"
  [ "$k" = green ] && printf 'print("harness: GREEN -- a stand-in")\n' > "$F/ci-$k/harness/run.py"
  [ "$k" = short ] && printf 'print("ok    a runner that stopped short")\n' > "$F/ci-$k/harness/run.py"
  ( cd "$F/ci-$k" && RUNNER_TEMP="$F/ci-$k" bash "$F/harness_step.sh" > "$F/ci-$k.out" 2>&1 ); rc=$?
  echo "§1.14 the harness step over a runner that prints $( [ $k = green ] && echo 'the green summary last' || echo 'no summary' ): exit $rc -- $(tail -n 1 "$F/ci-$k.out" | cut_paths)"
done
mkdir -p "$F/tb/LLVM-20.1.8-Linux-X64/bin" "$F/stub"
printf 'a stand-in\n' > "$F/tb/LLVM-20.1.8-Linux-X64/bin/llc"
tar -cJf "$F/stand-in.tar.xz" -C "$F/tb" LLVM-20.1.8-Linux-X64
printf '#!/bin/bash\nwhile [ $# -gt 0 ]; do [ "$1" = -o ] && { cp "%s" "$2"; exit 0; }; shift; done; exit 2\n' "$F/stand-in.tar.xz" > "$F/stub/curl"
chmod +x "$F/stub/curl"
sha=$(sha256sum "$F/stand-in.tar.xz" | cut -d' ' -f1); bytes=$(stat -c '%s' "$F/stand-in.tar.xz")
off="$( [ "${sha:0:1}" = 0 ] && echo "1${sha:1}" || echo "0${sha:1}")"
for k in right off missing; do
  w="$F/ci-llvm-$k"; mkdir -p "$w/meta/research" "$w/hm" "$w/tmp"
  case $k in
    right)   line="LLVM-20.1.8-Linux-X64.tar.xz sha256 $sha bytes $bytes" ;;
    off)     line="LLVM-20.1.8-Linux-X64.tar.xz sha256 $off bytes $bytes" ;;
    missing) line="the tarball's digest, in no line the step can read" ;;
  esac
  printf '# a stand-in — research digest\n\n**As of 2026-10-21.**\n\n## Answer\n\n%s\n' "$line" > "$w/meta/research/llvm-20.1.8-tarball.md"
  ( cd "$w" && PATH="$F/stub:$PATH" HOME="$w/hm" RUNNER_TEMP="$w/tmp" LLVM_VERSION=20.1.8 LLVM_DIGEST=meta/research/llvm-20.1.8-tarball.md \
      bash "$F/install_step.sh" > "$w.out" 2>&1 ); rc=$?
  echo "§1.14 the install step, the digest's line $k: exit $rc; unpacked: $(test -f "$w/hm/llvm/bin/llc" && echo yes || echo no) -- $(head -n 1 "$w.out" | sed -E 's/[0-9a-f]{64}/<sha256>/g; s/ [0-9]+ B / <n> B /g; s|/[^ ]*/meta/research|meta/research|g' | cut_paths)"
done

# §1.15 -- the interpreter
echo "§1.15 $(python3 --version)"
rm -rf "${F:?}"
