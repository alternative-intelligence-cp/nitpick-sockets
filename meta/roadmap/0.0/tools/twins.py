#!/usr/bin/env python3
"""Cycle 0.0 -- THE TWIN SWEEP BY EXACT STRINGS, fix round 2's check (b) (management_3's ruling of 2026-10-25): each
correction the plan records as made, and each this round makes, is swept for its twins by the exact identifiers and
strings it changed, over every surface the plan's text reaches.

    python3 -B twins.py run     "$REPO"     # every old string's hits, each classed; an UNCLASSED hit is a stop
    python3 -B twins.py run     "$CLONE" --before   # a clone at the round's base, fd47ba3, with these tools copied
                                            # in: a hit of the round's own rows that no line classes is STALE
    python3 -B twins.py control "$REPO"     # each row's provenance; a planted twin found and its new string not;
                                            # the classes' self-test

THE TABLE, `twins.tsv` beside this tool: one row per correction, `old <TAB> new <TAB> commit <TAB> note` -- the old
string exactly as the correction removed it, the new one, the commit that made it (a commit of this plan's branch;
`step:<sub>/<n>` for a correction a step patch makes in the tree; `fd47ba3..` for fix round 2's own, read against the
plan folder as the checkout holds it; `-` for one no commit holds, its note saying why), and what it corrected. A
number too common to sweep alone is swept with the identifier beside it -- the file's name and the line number together,
never the bare number -- and the note says so. A string matches where its text, read through `sweep.py`'s transform -- markers and emphasis gone, lines
joined by one space -- occurs, case ignored; a row with a fifth column `raw` matches its text as written, on one line,
case kept (a date note's opening `*(`, which the transform would strip to a bare parenthesis).

THE SURFACES: (1) `tip`, every file of the plan folder as the checkout holds it, but the patches (surface 2), this
tool's two data files and the README's section that records the two checks' output; (2) `patch`, every patch's added
and context lines, each run of them joined as the file it belongs to reads it; (3) `tree`, the tree each subcycle's
patches leave, built as `lines.py` builds it (applied in plan order through `apply.py`), but the plan folder, which is
surface 1 -- a line the same in several trees is printed once, with the subcycles whose trees hold it.

THE SECTION CITATIONS (the verification of 2026-10-25, its finding 4): every match in the decision log, in the tree
the last patch leaves, of 0.0.5's sweep subject "a cycle file's section cited by a permanent file" -- a cycle file's
`§N`, its gate item, a bare `step N` or `block N` (but `build step N`, the harness's own name) -- each with its class.

THE CLASSES, `twins_classes.txt` beside this tool, one per line: `<CLASS> | <surface>[@<subcycles>]:<path glob> |
<fragment>` -- a hit is that class when its surface is the one named (`*` for any; `tree@0.0.0,0.0.1` only when every
tree that holds the line is one of those named; `log` for the section citations), its path matches the glob and its
sentence holds the fragment, read through the same transform, case ignored (`re:` before a fragment makes it a regular
expression over that text). Three classes: STALE, a twin fix round 2 fixes at its source (so found only before the fix);
EARLIER, a statement about an earlier cut, a pin, a date or a run, said as such; LOG, a record the decision log keeps
by its rule. A hit no line classes is UNCLASSED, and an UNCLASSED hit is a stop: exit 1.
"""
import fnmatch
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as L  # noqa: E402 -- the trees, built once, the same way
from sweep import joined, strip  # noqa: E402 -- the one transform

SECTION_SUBJECT = "a cycle file's section cited by a permanent file"
CLASSES = ("STALE", "EARLIER", "LOG")


def norm(s):
    return re.sub(r"\s+", " ", strip(s)).strip().lower()


def table(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 4:
                parts.append("")
            if len(parts) != 5 or not parts[0].strip() or parts[4] not in ("", "raw"):
                raise SystemExit("STOP: twins.tsv:%d is not `old<TAB>new<TAB>commit<TAB>note[<TAB>raw]`" % n)
            rows.append(tuple(p.strip() for p in parts[:4]) + (n, parts[4] == "raw"))
    return rows


def classes(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip() or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.rstrip("\n").split(" | ")]
            if len(parts) != 3 or parts[0] not in CLASSES or ":" not in parts[1]:
                raise SystemExit("STOP: twins_classes.txt:%d is not `<CLASS> | <surface>:<glob> | <fragment>`" % n)
            frag = parts[2] if parts[2].startswith("re:") else norm(parts[2])
            out.append((parts[0], parts[1], frag, n))
    return out


def sentence_at(text, a, b):
    """The sentence of joined text around [a, b): back to a full stop or a cell's bar, forward to the next."""
    lo = max(text.rfind(". ", 0, a), text.rfind(" | ", 0, a), text.rfind("; ", 0, a), a - 400, 0)
    hi = [x for x in (text.find(". ", b), text.find(" | ", b), text.find("; ", b)) if x >= 0]
    hi = min(hi + [b + 400, len(text)])
    return text[lo:hi]


def classify(cls, surface, path, sent, subs=None):
    s = norm(sent)
    for c, glob, frag, n in cls:
        sf, _, pg = glob.partition(":")
        sf, _, only = sf.partition("@")
        if sf not in (surface, "*") or not fnmatch.fnmatch(path, pg):
            continue
        if only and not (subs and set(subs) <= set(only.split(","))):
            continue
        if (re.search(frag[3:], s) if frag.startswith("re:") else frag in s):
            return c, n
    return "UNCLASSED", None


# -------------------------------------------------------------------------------------------------- the surfaces --

def record_lines(plan):
    """The README's lines of the section recording the two checks' output: (first, last), or None."""
    p = os.path.join(plan, "README.md")
    lines = open(p, encoding="utf-8").read().split("\n")
    a = next((i for i, x in enumerate(lines, 1) if L.RECORD_HEADING.match(x)), None)
    if a is None:
        return None
    b = next((i for i, x in enumerate(lines, 1) if i > a and x.startswith("## ")), len(lines) + 1)
    return a, b - 1


def without_record(body):
    """A README's text with the section recording the two checks' output blanked, as every surface reads it."""
    lines = body.split("\n")
    a = next((i for i, x in enumerate(lines) if L.RECORD_HEADING.match(x)), None)
    if a is None:
        return body
    b = next((i for i, x in enumerate(lines) if i > a and x.startswith("## ")), len(lines))
    return "\n".join(lines[:a] + [""] * (b - a) + lines[b:])


def tip_texts(plan):
    out = []
    rec = record_lines(plan)
    for root, ds, fs in os.walk(plan):
        ds.sort()
        for f in sorted(fs):
            rel = os.path.relpath(os.path.join(root, f), plan)
            if f in L.SKIP_NAMES or f.endswith(".patch") or "__pycache__" in rel:
                continue
            lines = open(os.path.join(root, f), encoding="utf-8", errors="replace").read().split("\n")
            if rel == "README.md" and rec:
                lines = [("" if rec[0] <= i <= rec[1] else x) for i, x in enumerate(lines, 1)]
            out.append(("tip", "meta/roadmap/0.0/" + rel, lines, None))
    return out, rec


def patch_texts(plan):
    out = []
    for root, ds, fs in os.walk(plan):
        ds.sort()
        for f in sorted(x for x in fs if x.endswith(".patch")):
            rel = os.path.relpath(os.path.join(root, f), plan)
            body = open(os.path.join(root, f), encoding="utf-8").read().split("\n")
            lines = [""] * len(body)
            for i, x in enumerate(body):
                if x[:1] in ("+", " ") and not x.startswith("+++ "):
                    lines[i] = x[1:]
            out.append(("patch", rel, lines, None))
    return out


def tree_texts(trees):
    subs = sorted(trees.after)
    seen = {}
    for sub in subs:
        ref = trees.after[sub]
        out = L.sh("git", "-C", trees.dest, "ls-tree", "-r", trees.tree[ref])
        for line in out.split("\n"):
            if not line:
                continue
            meta, path = line.split("\t", 1)
            blob = meta.split()[2]
            if re.match(r"meta/roadmap/(done/)?0\.0/", path):
                continue
            seen.setdefault((path, blob), []).append(sub)
    texts = []
    for (path, blob), subs_ in sorted(seen.items()):
        raw = subprocess.run(["git", "-C", trees.dest, "cat-file", "-p", blob], capture_output=True).stdout
        if b"\0" in raw:
            continue
        texts.append(("tree", path, raw.decode("utf-8", "replace").split("\n"), subs_))
    return texts


def sweep(rows, texts, cls):
    """{row index: [(class, surface, path, line, subcycles)]}, a tree line once per text it reads the same in."""
    hits = {i: [] for i in range(len(rows))}
    olds = [(i, norm(r[0])) for i, r in enumerate(rows) if not r[5]]
    raws = [(i, r[0]) for i, r in enumerate(rows) if r[5]]
    for surface, path, lines, subs in texts:
        text, where = joined(lines)
        low = text.lower()
        for i, old in raws:
            for n, line in enumerate(lines, 1):
                if old in line:
                    k = next(j for j, w in enumerate(where) if w >= n) if any(w >= n for w in where) else 0
                    sent = sentence_at(text, k, k + 1)
                    c, cn = classify(cls, surface, path, sent, subs)
                    hits[i].append((c, surface, path, n, subs, cn, sent))
        for i, old in olds:
            start = 0
            while True:
                k = low.find(old, start)
                if k < 0:
                    break
                sent = sentence_at(text, k, k + len(old))
                c, cn = classify(cls, surface, path, sent, subs)
                hits[i].append((c, surface, path, where[k], subs, cn, sent))
                start = k + 1
    # a tree line the same across subcycles is one hit: merge by (path, line text)
    for i in hits:
        merged, order = {}, []
        for h in hits[i]:
            key = (h[1], h[2], h[3]) if h[1] != "tree" else (h[1], h[2], h[3], tuple(h[4]))
            if key not in merged:
                merged[key] = h
                order.append(key)
        hits[i] = [merged[k] for k in order]
    return hits


def section_lines(trees, cls):
    import sweep as S
    pats = dict(S.patterns(trees.dest, "0.0.5"))
    rx = pats[SECTION_SUBJECT]
    text = L.sh("git", "-C", trees.dest, "show", "%s:meta/DECISIONS.md" % trees.tree[trees.last]).split("\n")
    j, where = joined(text)
    out = []
    for m in rx.finditer(j):
        sent = sentence_at(j, m.start(), m.end())
        c, cn = classify(cls, "log", "meta/DECISIONS.md", sent)
        out.append((c, where[m.start()], m.group(0), cn, sent))
    return out


# --------------------------------------------------------------------------------------------------------- run --

def layout(argv):
    repo, wb, npk = L.layout(argv)
    trees = L.Trees(repo, wb, npk)
    trees.build()
    return repo, trees


def run(argv):
    repo, trees = layout(argv)
    rows = table(os.path.join(HERE, "twins.tsv"))
    cls = classes(os.path.join(HERE, "twins_classes.txt"))
    tips, rec = tip_texts(trees.plan)
    texts = tips + patch_texts(trees.plan) + tree_texts(trees)
    n = {s: sum(1 for t in texts if t[0] == s) for s in ("tip", "patch", "tree")}
    print("denominator: %d row(s) of twins.tsv from %d commit(s); %d plan file(s) at the tip, %d patch(es)' added and "
          "context lines, %d distinct file text(s) of the six trees the subcycles leave (the plan folder out); skipped "
          "by name: %s, and the README's lines %s, the two checks' record" % (
              len(rows), len({r[2] for r in rows}), n["tip"], n["patch"], n["tree"], ", ".join(L.SKIP_NAMES),
              "%d–%d" % rec if rec else "(none yet)"))
    hits = sweep(rows, texts, cls)
    if "--before" in argv:
        print("before: the round's base -- a hit of a row of fix round 2's own (`fd47ba3..`, or a step's correction "
              "whose note gives it to fix round 2) that no class line classes is a site the round fixes at its source: "
              "STALE")
        for i, r in enumerate(rows):
            if r[2] == "fd47ba3.." or r[3].startswith("fix round 2"):
                hits[i] = [("STALE",) + h[1:5] + ("base",) + h[6:] if h[0] == "UNCLASSED" else h for h in hits[i]]
    tally = {c: 0 for c in CLASSES + ("UNCLASSED",)}
    for i, r in enumerate(rows):
        hs = hits[i]
        print("%s  ->  %s  [%s]: %d hit(s)" % (r[0], r[1], r[2], len(hs)))
        for c, surface, path, line, subs, cn, sent in hs:
            tally[c] += 1
            tag = " [classes:%d]" % cn if isinstance(cn, int) else (" [the round's own site]" if cn else "")
            print("  %-9s %s:%s:%d%s%s" % (c, surface, path, line, " (trees of %s)" % ", ".join(subs) if subs else "",
                                           tag))
            if c == "UNCLASSED":
                print("            %r" % sent[:240])
    sec = section_lines(trees, cls)
    nl = len({x[1] for x in sec})
    print("section citations in the decision log, the tree the last patch leaves: %d match(es) on %d line(s)" % (
        len(sec), nl))
    for c, line, txt, cn, sent in sec:
        tally[c] += 1
        print("  %-9s meta/DECISIONS.md:%d %r%s" % (c, line, txt, " [classes:%d]" % cn if cn else ""))
        if c == "UNCLASSED":
            print("            %r" % sent[:240])
    print("result: %d row(s), %d hit(s) -- %s; and %d section citation(s) on %d line(s) of the decision log" % (
        len(rows), sum(len(v) for v in hits.values()), ", ".join("%s %d" % (c, tally[c]) for c in tally), len(sec),
        nl))
    return 1 if tally["UNCLASSED"] else 0


# ----------------------------------------------------------------------------------------------------- control --

def flat(name, body):
    """A file's text as the sweep reads it: a patch's lines without their diff markers, every file through the
    transform, its lines joined."""
    lines = body.split("\n")
    if name.endswith(".patch"):
        lines = [x[1:] if x[:1] in ("+", "-", " ") and not x.startswith(("+++ ", "--- ")) else "" for x in lines]
    return norm(joined(lines)[0])


def snapshot(repo, commit):
    """The plan folder's text at a commit (or the checkout's, for None), one (raw, joined and normalized) pair per
    file; the README's record of the two checks blanked, as every surface reads it."""
    if commit is None:
        out = []
        plan = L.plan_dir(repo)
        for root, ds, fs in os.walk(plan):
            for f in fs:
                if f in L.SKIP_NAMES or "__pycache__" in root:
                    continue
                body = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
                if f == "README.md" and root == plan:
                    body = without_record(body)
                out.append((body, flat(f, body)))
        return out
    ls = L.sh("git", "-C", repo, "ls-tree", "-r", commit, "--", "meta/roadmap/0.0")
    ents = [(x.split()[2], x.split("\t")[1]) for x in ls.split("\n") if x and not x.endswith(L.SKIP_NAMES)]
    blobs = [b for b, _ in ents]
    r = subprocess.run(["git", "-C", repo, "cat-file", "--batch"], input=("\n".join(blobs) + "\n").encode(),
                       capture_output=True)
    data, out, i = r.stdout, [], 0
    while i < len(data):
        nl = data.index(b"\n", i)
        size = int(data[i:nl].split()[2])
        body = data[nl + 1:nl + 1 + size].decode("utf-8", "replace")
        if ents[len(out)][1] == "meta/roadmap/0.0/README.md":
            body = without_record(body)
        out.append((body, flat(ents[len(out)][1], body)))
        i = nl + 1 + size + 1
    return out


def control(argv):
    repo, _, _ = L.layout(argv)
    rows = table(os.path.join(HERE, "twins.tsv"))
    cls = classes(os.path.join(HERE, "twins_classes.txt"))
    ok = True
    cache = {}

    def count(commit, s, raw):
        if commit not in cache:
            cache[commit] = snapshot(repo, commit)
        return sum(t[0 if raw else 1].count(s) for t in cache[commit])
    bad, none, trees, steps = [], [], None, []

    def tree_count(ref, s, raw_):
        key = ("tree", ref)
        if key not in cache:
            out = L.sh("git", "-C", trees.dest, "ls-tree", "-r", trees.tree[ref])
            texts = []
            for line in out.split("\n"):
                if line and not re.search(r"\tmeta/roadmap/(done/)?0\.0/", line):
                    raw = subprocess.run(["git", "-C", trees.dest, "cat-file", "-p", line.split()[2]],
                                         capture_output=True).stdout
                    if b"\0" not in raw:
                        body = raw.decode("utf-8", "replace")
                        texts.append((body, flat(line.split("\t")[1], body)))
            cache[key] = texts
        return sum(t[0 if raw_ else 1].count(s) for t in cache[key])
    for old, new, commit, note, n, raw in rows:
        o = old if raw else norm(old)
        if commit == "-":
            none.append("  NONE       twins.tsv:%d %r -- %s" % (n, old, note))
            continue
        if commit.startswith("step:"):
            if trees is None:
                trees = L.Trees(repo, *L.layout(argv)[1:])
                trees.build()
                steps = ["base"] + sorted(k for k in trees.tree if k != "base")
            sub, k = commit[5:].split("/")
            i = steps.index((sub, int(k)))
            before, after = tree_count(steps[i - 1], o, raw), tree_count(steps[i], o, raw)
            if not before > after:
                bad.append("  PROVENANCE twins.tsv:%d %r at %s: %d in the tree before it, %d after" % (
                    n, old, commit, before, after))
            continue
        if commit.endswith(".."):
            before, after = count(commit[:-2], o, raw), count(None, o, raw)
        else:
            before, after = count(commit + "^", o, raw), count(commit, o, raw)
        if not before > after:
            bad.append("  PROVENANCE twins.tsv:%d %r at %s: %d before, %d after" % (n, old, commit, before, after))
    print("provenance: %d of %d row(s) hold -- each old string more often in the plan folder before its commit than at it,"
          " or in the tree before its step than after it; %d row(s) with no commit, each said why" % (
              len(rows) - len(bad) - len(none), len(rows) - len(none), len(none)))
    for b in bad + none:
        print(b)
    ok = ok and not bad
    # a planted twin is found and its new string is not
    old, new = rows[0][0], rows[0][1]
    assert not rows[0][5]
    planted = [("tip", "planted.md", ["A planted sentence that repeats it: %s, word for word." % old], None),
               ("tip", "planted.md", ["A planted sentence with the correction: %s, word for word." % new], None)]
    h = sweep([rows[0]], planted, cls)[0]
    found_old = any(x[3] == 1 and x[2] == "planted.md" for x in h)
    lines_hit = sorted({x[3] for x in h})
    good = lines_hit == [1] if norm(old) not in norm(new) else bool(lines_hit)
    print("planted: the first row's old string in a sentence -> %s; its new string in another -> %s" % (
        "found" if found_old else "NOT FOUND", "not found" if good else "FOUND"))
    ok = ok and found_old and good
    # the classes' self-test: a line that classes a planted hit, and none for another; a tree line held by a later
    # tree than its line names; a regular expression
    test = [("EARLIER", "tip:planted.md", norm("at an earlier cut"), 1),
            ("EARLIER", "tree@0.0.0:planted.md", norm("before its fix"), 2),
            ("LOG", "log:planted.md", r"re:\d{4}-\d{2}-\d{2}, cycle 0\.0\.\d step \d", 3)]
    got = [classify(test, "tip", "planted.md", "said at an earlier cut, as such")[0],
           classify(test, "tip", "planted.md", "a sentence no line classes")[0],
           classify(test, "tree", "planted.md", "a tree line before its fix", ["0.0.0"])[0],
           classify(test, "tree", "planted.md", "a tree line before its fix", ["0.0.0", "0.0.1"])[0],
           classify(test, "log", "planted.md", "**2026-10-25, cycle 0.0.4 step 2.**")[0],
           classify(test, "log", "planted.md", "cycle 0.0.4's step 2")[0]]
    want = ["EARLIER", "UNCLASSED", "EARLIER", "UNCLASSED", "LOG", "UNCLASSED"]
    print("classes: %d of %d planted hits classed as their lines say -- a line's fragment, none, a tree line in the "
          "trees its line names and in one more, a regular expression and a near miss: %s" % (
              sum(a == b for a, b in zip(got, want)), len(want), ", ".join(got)))
    ok = ok and got == want
    print("control: %s" % ("every row's provenance holds, the planted twin is found and its correction is not, and the "
                           "classes read as written" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("run", "control"):
        print(__doc__)
        sys.exit(2)
    sys.exit(run(sys.argv) if sys.argv[1] == "run" else control(sys.argv))
