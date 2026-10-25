# meta/roadmap/0.0/0.0.5_tools/facts.sh -- re-derives `0.0.5.md` §1, block 0b. Sourced after `../tools/env.sh`, so
# `$REPO`, `$A`, `$TOOLS` and the helpers are set. Writes only under `$A/facts`, and removes it. Reads no compiler file.
# Prints no path above the repository. The tree it starts from is cycle 0.0.4's record; `$d` is a throwaway clone with
# this subcycle's step 1 applied, then the archive's move and its step 2, by the moved tools -- where every pointer the
# two patches' added lines write is read.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T5=$REPO/meta/roadmap/0.0/0.0.5_tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
python3 -B "$TOOLS/apply.py" "$d" 0.0.5 1 > /dev/null
git -C "$d" mv meta/roadmap/0.0 meta/roadmap/done/0.0
python3 -B "$d/meta/roadmap/done/0.0/tools/apply.py" "$d" 0.0.5 2 > /dev/null

# §1.1 -- the tree it starts from: cycle 0.0.4's record
echo "§1.1 src/core/ holds: $(cd "$REPO/src/core" && ls *.npk | tr '\n' ' ')"
echo "§1.1 tests/unit/: $(find "$REPO/tests/unit" -maxdepth 1 -name '*.npk' | wc -l) .npk file(s); tests/probe/: $(find "$REPO/tests/probe" -maxdepth 1 -name '*.npk' | wc -l); tests/probe/refused/: $(find "$REPO/tests/probe/refused" -maxdepth 1 -name '*.npk' | wc -l)"
python3 -B - "$REPO/nitpick.toml" <<'PY'
import sys, tomllib
m = tomllib.load(open(sys.argv[1], "rb"))
print("§1.1 nitpick.toml's [[test]] entries: %d (%s)" % (len(m["test"]), ", ".join(
    "%s %s%s" % (t["name"], t["stage"], "/" + t["kind"] if "kind" in t else "") for t in m["test"])))
PY

# §1.2 -- what step 1 reads: 0.0.0.md §6's verdicts, and the specifications' lines that rest on 04, 09 and 10 by name
python3 -B - "$REPO" <<'PY'
import glob, os, re, sys
root = sys.argv[1]
text = open(os.path.join(root, "meta/roadmap/0.0/0.0.0.md"), encoding="utf-8").read()
sec = text[text.index("\n## 6. "):text.index("\n## 7. ")]
rows = [r for r in sec.split("\n") if re.match(r"^\| \**\d\d[a-z]?\** \|", r)]
acc = sum(1 for r in rows if "| ACCEPTED" in r)
ref = sum(1 for r in rows if "| REFUSED" in r)
print("§1.2 0.0.0.md §6's verdict rows: %d -- ACCEPTED %d, REFUSED %d; by name: %s" % (
    len(rows), acc, ref, " ".join(re.match(r"^\| \**(\d\d[a-z]?)", r).group(1) for r in rows if r.startswith("| **"))))
cite = re.compile(r"SK-013|SK-035|\bprobes? 0?4\b|\bprobes? (?:0?9|10)\b|\bprobes 0?9")
for f in sorted(glob.glob(os.path.join(root, "meta/specs/*.md"))):
    n = [i for i, line in enumerate(open(f, encoding="utf-8"), 1) if cite.search(line)]
    if n:
        print("§1.2 %s: %d line(s) naming SK-013, SK-035 or probes 04, 09, 10 -- %s" % (
            os.path.basename(f), len(n), " ".join(map(str, n))))
PY

# §1.3 -- the findings' sources: each subcycle file's list found at planning, and the README's disagreements
for f in 0.0.0 0.0.1 0.0.2 0.0.3 0.0.4; do
  printf '%s %s; ' "$f" "$(awk '/Found at planning/{f=1} f && /^> [0-9]+\. /{c++} /^\*\*Gate for starting/{f=0} END{print c+0}' "$REPO/meta/roadmap/0.0/$f.md")"
done | sed 's/; $//; s/^/§1.3 found at planning: /'; echo
echo "§1.3 the cycle README's places the first writing disagreed with itself: $(awk '/^## The places the first writing disagreed/{f=1;next} /^## /{f=0} f && /^- /{c++} END{print c+0}' "$REPO/meta/roadmap/0.0/README.md")"

# §1.4 -- the research folder: what it holds, CURRENCY.md's research rows, each digest's date
echo "§1.4 meta/research/ holds: $(git -C "$REPO" ls-files meta/research | sed 's|^meta/research/||' | tr '\n' ' ')"
echo "§1.4 CURRENCY.md's research rows: $(grep -c '^| Research item' "$REPO/meta/research/CURRENCY.md")"
for f in security-defects security-guidance security-vectors llvm-20.1.8-tarball; do
  echo "§1.4 $f.md: $(grep -m1 -oE 'As of [0-9]{4}-[0-9]{2}-[0-9]{2}' "$REPO/meta/research/$f.md" 2>/dev/null || echo MISSING)"
done

# §1.5 -- every place outside this folder that names a file in it, or cites a place inside one of its plans
python3 -B "$T5/citations.py" "$REPO" | sed 's/^/§1.5 /'

# §1.6 -- OPEN_QUESTIONS.md: the entries struck with a decision, and the ones open
python3 -B - "$REPO/meta/OPEN_QUESTIONS.md" <<'PY'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
struck = re.findall(r"^### ~~([A-Z]-\d+|O-[A-Z]+\d+)\b", t, re.M)
heads = re.findall(r"^### (O-N\d+)\b", t, re.M)
items = re.findall(r"^- \*\*(O-[A-Z]\d+)\b", t, re.M)
print("§1.6 struck: %s; open: %d -- %s" % (" ".join(struck) or "none", len(heads) + len(items), " ".join(heads + items)))
PY

# §1.7 -- the placeholders: the decision labels and the run's date
echo "§1.7 files the patches touch that hold \`@@PD-\` or \`@@DATE@@\` as the tree stands: $(n=0; for f in $(grep -ohE '^\+\+\+ b/.*' "$T5"/step*.patch | sed 's|^+++ b/||' | sort -u); do [ -f "$REPO/$f" ] && grep -qE '@@PD-|@@DATE@@' "$REPO/$f" && n=$((n+1)); done; echo $n)"
echo "§1.7 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T5"/step*.patch | sort -u | tr '\n' ' ')"
echo "§1.7 declared by them: $(x=$(grep -ohE '^\+### @@PD-[0-9]+@@' "$T5"/step*.patch | grep -oE 'PD-[0-9]+' | tr '\n' ' '); echo "${x:-none}")"
echo "§1.7 added lines carrying @@DATE@@: $(for s in 1 2; do printf 'step%s %s; ' $s "$(grep -cE '^\+[^+].*@@DATE@@' "$T5/step$s.patch")"; done | sed 's/; $//')"

# §1.8 -- every pointer the patches' added lines write, against the tree they leave
python3 -B "$d/meta/roadmap/done/0.0/tools/pointers.py" "$d" "$d/meta/roadmap/done/0.0/0.0.5_tools"
echo "§1.8 .npk files the patches add or change: $(grep -cE '^\+\+\+ b/.*\.npk$' "$T5"/step*.patch | awk -F: '{s+=$2} END{print s+0}')"

# §1.9 -- the interpreter
echo "§1.9 $(python3 --version)"
rm -rf "${F:?}"
