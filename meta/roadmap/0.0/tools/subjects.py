#!/usr/bin/env python3
"""Cycle 0.0 -- THE TWIN CHECK BY SUBJECT (the workbench `PLAYBOOK.md` §12's twins bullet, tightened 2026-10-31 by
`management_10`'s standing rule of 04:34): a corrected claim's twins are found by what the claim is ABOUT, not by the
corrected text's words, and every claim the check finds must carry its correction or be classed.

    python3 -B subjects.py run     "$REPO" <subcycle> [--at <commit>] [--row <id>] [--bare <id>] [--only-bare]
    python3 -B subjects.py control "$REPO" <subcycle>

THE TABLE, `<subcycle>_tools/subjects.txt`, one directive a line, its fields split at " | " (a regular expression
holds `|` with no space beside it), `#` a comment:

    row: <id> | <the claim, in a few words>
    base: <id> | <commit> | <path> | <line> | <what the base claim is>
    names: <id> | <regex>          the claim's subject: the things it is about, by any name they go by
    says: <id> | <regex>           what the claim says of them, in any wording a twin may take
    corrected: <id> | <regex>      the dated correction a claim's section holds when it carries one; `-` for a
                                   claim corrected in place, by a slip's rule, which has no note to carry
    scope: <id> | <regex>          the paths the row reads, when not every file but the cycle 0.0 plans'
    plant: <id> | <kind> | <text>  a twin the check must find; `\\n` is a line break. Kinds: missed (a verifier's
                                   plant a word list missed), reworded, split (across lines), part (one part of the
                                   subject alone), own (this plan's own, in other words)
    class: <id> | <CLASS> | <path glob> | <fragment> [| corrected]

A HIT is a sentence that names the subject and says the claim: inside one block of a file -- a paragraph, a list
item, a table row's cell, a heading; a `bash` or `text` fence, a command or a run's output, is none -- read through
`sweep.py`'s transform (markers and emphasis gone, the block's lines joined by one space, so a claim a line break
splits is one string), the sentence runs between full stops (". ", "? ", "! ") or a table cell's bars, and it is a
hit when `names` and `says` both match it, case ignored. A hit is printed as `<path>:<first line>-<last line>` of
its sentence.

ITS SECTION is everything between the headings around it. A hit CARRIES ITS CORRECTION when its section holds a
block that `corrected` matches -- a settled text never rewritten, with its dated note beside it.

ITS CLASS is the first `class` line of its row whose glob matches its path and whose fragment its sentence holds (read
through the same transform, case ignored; `re:` makes the fragment a regular expression), and whose last field, if it
is `corrected`, the hit's section meets. The classes are the sweep's (`0.0.0.md` §7's, and two more): D, a settled
decision's own text, with its marker or dated note beside it; N, a dated note quoting the old claim, or a rule whose
dated note says how the pin changes it; T, the new text, naming the old claim as history or stating what is true at
the pin; H, a site a later subcycle owes; A, accurate as it stands. A hit no line classes is BARE: a claim that does
not carry its correction, which is what this check exists to find, and its exit is 1.

THE FILES: every file `git ls-files` lists in the root (and every untracked one not ignored), or `git ls-tree` at
`--at <commit>`, read there by `git show` -- but the cycle 0.0 plans, tools and patches (`0.0.0.md`, the cycle's one
landed record, is read), `LICENSE`, and a research digest (its first line a digest's heading). A `.npk` file is read
for its comments alone, and the subcycle's own plan up to its execution record, which its work writes as it runs.
`--row` reads one row; `--bare <id>` removes, from the section holding that row's base claim (found at `--at`'s
commit by its line, and elsewhere by the same sentence), every block `corrected` matches: the claim
as it would stand without its dated correction. `--only-bare` prints, of the hits, the BARE ones alone.

`control`, per row: the base claim at its commit is a hit, and its class; that hit with `--bare`, BARE; on the tree
as it stands, the same sentence carrying its correction is classed and, with `--bare`, BARE (a row whose claim was
corrected in place, by a slip's rule, has no such sentence on the tree, and says so); then every plant, written to
a file of its own that no class line names, found and BARE, with the row's hit rate. Then the reader's branches, each
planted and each a STOP: a directive not in its form, a field naming a row the table does not declare, a row missing
a part, a pattern the transform makes unmatchable, an unknown class, a commit that cannot be read, and a root that is
not a checkout's top.

THE EXIT STATUSES. `run`: 0, every hit classed; 1, a hit BARE; 2, a STOP -- an input it cannot read, a table not in
its form, or a usage error. `control`: 0 when every check holds, 1 when one does not, 2 on a STOP outside the planted
ones. The block that runs this prints each status on its own line.
"""
import fnmatch
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sweep import joined, strip, unmatchable  # noqa: E402 -- the one transform, and its refusals

CLASSES = ("D", "N", "T", "H", "A")
KINDS = ("missed", "reworded", "split", "part", "own")
FIELDS = {"row": 2, "base": 5, "names": 2, "says": 2, "corrected": 2, "scope": 2, "plant": 3, "class": (4, 5)}
NEVER = re.compile(r"(?!)")
DIGEST = re.compile(r"^# .+ — research digest\s*$")
HEADING = re.compile(r"^\s{0,3}#{1,6} ")
ITEM = re.compile(r"^\s*([-*+]|\d+\.) ")
SKIP = re.compile(r"(^|/)meta/roadmap/(done/)?0\.0/(?!0\.0\.0\.md$)|\.patch$|^LICENSE$")


class Stop(Exception):
    pass


# ------------------------------------------------------------------------------------------------------ the table --

def parse(text, where="subjects.txt"):
    rows, order = {}, []
    for n, line in enumerate(text.split("\n"), 1):
        if not line.strip() or line.startswith("#"):
            continue
        kind, sep, rest = line.partition(": ")
        if not sep or kind not in FIELDS:
            raise Stop("%s:%d is not a directive (`row:`, `base:`, `names:`, `says:`, `corrected:`, `plant:`, "
                       "`class:`)" % (where, n))
        parts = [p.strip() for p in rest.split(" | ")]
        want = FIELDS[kind]
        if (len(parts) not in want) if isinstance(want, tuple) else len(parts) != want:
            raise Stop("%s:%d: `%s:` takes %s field(s), not %d" % (where, n, kind, want, len(parts)))
        if any(not p for p in parts):
            raise Stop("%s:%d: an empty field" % (where, n))
        rid = parts[0]
        if kind == "row":
            if rid in rows:
                raise Stop("%s:%d: row `%s` declared twice" % (where, n, rid))
            rows[rid] = {"title": parts[1], "plants": [], "classes": []}
            order.append(rid)
            continue
        if rid not in rows:
            raise Stop("%s:%d: `%s:` names row `%s`, which no `row:` line declares above it" % (where, n, kind, rid))
        r = rows[rid]
        if kind == "base":
            if not parts[3].isdigit():
                raise Stop("%s:%d: a base line that is not a number" % (where, n))
            r["base"] = (parts[1], parts[2], int(parts[3]), parts[4])
        elif kind == "corrected" and parts[1] == "-":
            r[kind] = NEVER
        elif kind == "scope":
            r[kind] = re.compile(parts[1])
        elif kind in ("names", "says", "corrected"):
            why = unmatchable(parts[1])
            if why:
                raise Stop("%s:%d: row `%s`'s %s pattern holds %s, which the transform removes"
                           % (where, n, rid, kind, why))
            r[kind] = re.compile(parts[1], re.I)
        elif kind == "plant":
            if parts[1] not in KINDS:
                raise Stop("%s:%d: a plant of kind `%s`, not one of %s" % (where, n, parts[1], ", ".join(KINDS)))
            r["plants"].append((parts[1], parts[2].replace("\\n", "\n")))
        elif kind == "class":
            if parts[1] not in CLASSES:
                raise Stop("%s:%d: class `%s`, not one of %s" % (where, n, parts[1], " ".join(CLASSES)))
            if len(parts) == 5 and parts[4] != "corrected":
                raise Stop("%s:%d: a class line's fifth field is `corrected` or nothing" % (where, n))
            frag = parts[3] if parts[3].startswith("re:") else norm(parts[3])
            r["classes"].append((parts[1], parts[2], frag, len(parts) == 5))
    if not order:
        raise Stop("%s declares no row" % where)
    for rid in order:
        missing = [k for k in ("base", "names", "says", "corrected") if k not in rows[rid]]
        if missing:
            raise Stop("%s: row `%s` has no %s" % (where, rid, ", ".join(missing)))
    return rows, order


def norm(s):
    return re.sub(r"\s+", " ", strip(s)).strip().lower()


# ------------------------------------------------------------------------------------------------------ the files --

def git(root, *args):
    p = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True)
    return p.returncode, p.stdout


def listing(root, at, everything=False):
    code, top = git(root, "rev-parse", "--show-toplevel")
    if code or os.path.realpath(top.strip()) != os.path.realpath(root):
        raise Stop("%s is not a checkout's top -- the check would read no file, or a part of them" % root)
    if at:
        code, out = git(root, "ls-tree", "-r", "--name-only", at)
        if code:
            raise Stop("commit `%s` cannot be read in %s" % (at, root))
        names = out.split("\n")
    else:
        names = (git(root, "ls-files")[1].split("\n")
                 + git(root, "ls-files", "--others", "--exclude-standard")[1].split("\n"))
    return sorted(f for f in set(names) if f and (everything or not SKIP.search(f)))


def read(root, at, path):
    if at:
        code, out = git(root, "show", "%s:%s" % (at, path))
        if code:
            raise Stop("%s:%s cannot be read" % (at, path))
        return out
    p = os.path.join(root, path)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def texts(root, at, sub=None):
    """{path: lines} of every file the check reads; the subcycle's own plan read up to its execution record, which
    its work writes as it runs and no Expect can hold (blanked, so its lines keep their numbers)."""
    own = "meta/roadmap/0.0/%s.md" % sub if sub else None
    out = {}
    for f in listing(root, at, everything=True):
        t = read(root, at, f)
        if t is None:
            continue
        lines = t.split("\n")
        if lines and DIGEST.match(lines[0]):
            continue
        if f.endswith((".o", ".png", ".gz")):
            continue
        if f.endswith(".npk"):
            lines = [x if x.lstrip().startswith("//") else "" for x in lines]
        if f == own:
            cut = next((i for i, x in enumerate(lines) if x.startswith("## Execution record")), len(lines))
            lines = lines[:cut] + [""] * (len(lines) - cut)
        out[f] = lines
    return out


# ------------------------------------------------------------------------------------------- blocks and sentences --

def blocks(lines):
    """[(first line, last line, is a heading)], 1-based, every non-blank line in exactly one block, but the lines of a
    `bash` or `text` fence: a plan's command or a run's output, which states no claim (a sketch's fence is read)."""
    out, cur, fence, skip = [], None, False, False
    for n, x in enumerate(lines, 1):
        s = x.strip()
        if s.startswith("```"):
            fence, skip = (False, False) if fence else (True, s[3:].strip() in ("bash", "text"))
            cur = None
            continue
        if not s or skip:
            cur = None
            continue
        if HEADING.match(x) or s.startswith("|"):
            out.append([n, n, bool(HEADING.match(x))])
            cur = None
            continue
        if cur is None or ITEM.match(x):
            cur = [n, n, False]
            out.append(cur)
        else:
            cur[1] = n
    return [tuple(b) for b in out]


SENT = re.compile(r"(?<=[.?!])\s+(?=\S)|\s\|\s")


def sentences(lines, a, b):
    """(text, first line, last line) of each sentence of the block a..b, through the transform."""
    t, where = joined(lines[a - 1:b])
    out, start = [], 0
    for m in list(SENT.finditer(t)) + [None]:
        end = m.start() if m else len(t)
        s = t[start:end].strip(" |")
        if s:
            lo = where[start] if start < len(where) else 1
            hi = where[end - 1] if 0 < end <= len(where) else lo
            out.append((s, a - 1 + lo, a - 1 + hi))
        start = m.end() if m else len(t)
    return out


def sections(bl):
    """For each block's index, the indices of the blocks of its section: a heading opens one, and holds it."""
    sec, ids = 0, []
    for b in bl:
        sec += 1 if b[2] else 0
        ids.append(sec)
    return {i: [j for j in range(len(bl)) if ids[j] == ids[i]] for i in range(len(bl))}


def hits(row, lines):
    """[(sentence, first, last, carries its correction)] in one file's lines."""
    bl = blocks(lines)
    owner = sections(bl)
    out = []
    for i, (a, b, _) in enumerate(bl):
        for s, lo, hi in sentences(lines, a, b):
            if row["names"].search(s) and row["says"].search(s):
                sec = owner.get(i, range(i, i + 1))
                carries = any(row["corrected"].search(joined(lines[bl[j][0] - 1:bl[j][1]])[0]) for j in sec)
                out.append((s, lo, hi, carries))
    return out


def in_scope(row, path):
    """A row reads the files its `scope:` names, or else every file but SKIP's."""
    return row["scope"].search(path) if "scope" in row else not SKIP.search(path)


def classify(row, path, sentence, carries):
    s = norm(sentence)
    for cls, glob, frag, needs in row["classes"]:
        if not fnmatch.fnmatch(path, glob):
            continue
        if needs and not carries:
            continue
        if (re.search(frag[3:], s, re.I) if frag.startswith("re:") else frag in s):
            return cls
    return "BARE"


def bare(row, files, base_sentence):
    """Remove, from the section holding the base claim's sentence, every block `corrected` matches."""
    path = row["base"][1]
    lines = files.get(path)
    if lines is None:
        return False
    bl = blocks(lines)
    owner = sections(bl)
    for i, (a, b, _) in enumerate(bl):
        if any(norm(s) == base_sentence for s, _, _ in sentences(lines, a, b)):
            lines = list(lines)
            for j in owner.get(i, range(i, i + 1)):
                ja, jb, _ = bl[j]
                if row["corrected"].search(joined(lines[ja - 1:jb])[0]):
                    for k in range(ja - 1, jb):
                        lines[k] = ""
            files[path] = lines
            return True
    return False


def base_sentence(row, root):
    """The base claim's sentence at its commit, through the transform: the hit whose lines hold the base line."""
    commit, path, line, _ = row["base"]
    t = read(root, commit, path)
    for s, lo, hi, _ in hits(row, t.split("\n")):
        if lo <= line <= hi:
            return norm(s), lo, hi
    return None


# ------------------------------------------------------------------------------------------------------- the modes --

def table(root, sub):
    p = os.path.join(root, "meta", "roadmap", "0.0", sub + "_tools", "subjects.txt")
    if not os.path.isfile(p):
        raise Stop("%s has no subjects.txt" % sub)
    with open(p, encoding="utf-8") as fh:
        return parse(fh.read(), sub + "_tools/subjects.txt")


def run(root, sub, at=None, only=None, strip_row=None, quiet=False, only_bare=False):
    rows, order = table(root, sub)
    for rid in (only, strip_row):
        if rid and rid not in rows:
            raise Stop("no row `%s`" % rid)
    files = texts(root, at, sub)
    if strip_row:
        found = base_sentence(rows[strip_row], root)
        if not found or not bare(rows[strip_row], files, found[0]):
            raise Stop("row `%s`'s base claim is not in this tree, so it cannot be made bare" % strip_row)
    if not quiet:
        print("denominator: %d file(s)%s -- every tracked or added file but the cycle 0.0 plans, tools and patches "
              "(0.0.0.md's record read), LICENSE and the research digests; a .npk file's comments alone; a row with "
              "a scope reads its own" % (sum(1 for f in files if not SKIP.search(f)), " at %s" % at if at else ""))
    total_bare = 0
    for rid in order:
        if only and rid != only:
            continue
        row = rows[rid]
        counts = {c: 0 for c in CLASSES + ("BARE",)}
        lines_out = []
        mine = [p for p in sorted(files) if in_scope(row, p)]
        if "scope" in row and not quiet:
            print("%s: its scope, %d file(s)" % (rid, len(mine)))
        for path in mine:
            for s, lo, hi, carries in hits(row, files[path]):
                c = classify(row, path, s, carries)
                counts[c] += 1
                if c == "BARE" or not only_bare:
                    lines_out.append("  %s %s:%d-%d" % (c, path, lo, hi))
        total_bare += counts["BARE"]
        if not quiet:
            print("%s: %s -- %d hit(s): %s" % (rid, row["title"], sum(counts.values()),
                                               ", ".join("%s %d" % (c, counts[c]) for c in CLASSES + ("BARE",))))
            for x in lines_out:
                print(x)
    if not quiet:
        print("BARE: %d -- %s" % (total_bare, "exit 1" if total_bare else "exit 0"))
    return 1 if total_bare else 0


def control(root, sub):
    rows, order = table(root, sub)
    ok = True
    here = texts(root, None, sub)
    for rid in order:
        row = rows[rid]
        commit, path, line, what = row["base"]
        found = base_sentence(row, root)
        if not found:
            print("%s: base claim %s:%d at %s (%s): NOT A HIT" % (rid, path, line, commit, what))
            ok = False
            continue
        sent, lo, hi = found
        at_base = texts(root, commit, sub)
        carried = [c for s, a, b, c in hits(row, at_base[path]) if norm(s) == sent]
        cls = classify(row, path, sent, carried[0] if carried else False)
        bare(row, at_base, sent)
        cls_bare = classify(row, path, sent, any(c for s, a, b, c in hits(row, at_base[path]) if norm(s) == sent))
        print("%s: base claim %s:%d-%d at %s (%s): a hit, %s; without its correction, %s"
              % (rid, path, lo, hi, commit, what, cls, cls_bare))
        ok = ok and cls_bare == "BARE"
        now = dict(here)
        on_tree = [(s, a, b, c) for s, a, b, c in hits(row, now.get(path, [])) if norm(s) == sent]
        if on_tree:
            s, a, b, c = on_tree[0]
            cls_now = classify(row, path, s, c)
            bare(row, now, sent)
            c2 = any(cc for ss, aa, bb, cc in hits(row, now[path]) if norm(ss) == sent)
            cls_now_bare = classify(row, path, s, c2)
            print("%s: on this tree at %s:%d-%d: %s; without its correction, %s"
                  % (rid, path, a, b, cls_now, cls_now_bare))
            ok = ok and cls_now != "BARE" and cls_now_bare == "BARE"
        else:
            print("%s: on this tree the base claim's sentence is gone -- corrected in place, by a slip's rule" % rid)
        got = 0
        for n, (kind, text) in enumerate(row["plants"], 1):
            fake = {"PLANT/%s-%d.md" % (rid, n): text.split("\n")}
            hs = hits(row, fake["PLANT/%s-%d.md" % (rid, n)])
            res = [classify(row, "PLANT/%s-%d.md" % (rid, n), s, c) for s, a, b, c in hs]
            hit = bool(hs) and all(r == "BARE" for r in res)
            got += hit
            print("  plant %d (%s): %s" % (n, kind, "found, BARE" if hit else "NOT FOUND"))
        if row["plants"]:
            print("%s: plants found %d of %d" % (rid, got, len(row["plants"])))
            ok = ok and got == len(row["plants"])
    # the reader's branches, each planted
    planted = [
        ("a directive not in its form", "row x | y\n"),
        ("a field naming an undeclared row", "names: x | a\n"),
        ("a row missing a part", "row: x | y\nnames: x | a\nsays: x | b\ncorrected: x | c\n"),
        ("a pattern the transform makes unmatchable",
         "row: x | y\nbase: x | HEAD | f | 1 | z\nnames: x | `a`\nsays: x | b\ncorrected: x | c\n"),
        ("an unknown class",
         "row: x | y\nbase: x | HEAD | f | 1 | z\nnames: x | a\nsays: x | b\ncorrected: x | c\nclass: x | Q | * | a\n"),
    ]
    stops = 0
    for what, text in planted:
        try:
            parse(text, "planted")
            print("  reader: %s -- READ, NOT A STOP" % what)
        except Stop:
            stops += 1
            print("  reader: %s -- a STOP" % what)
    for what, fn in (("a commit that cannot be read", lambda: listing(root, "0" * 40)),
                     ("a root that is not a checkout's top", lambda: listing(os.path.join(root, "meta"), None))):
        try:
            fn()
            print("  reader: %s -- READ, NOT A STOP" % what)
        except Stop:
            stops += 1
            print("  reader: %s -- a STOP" % what)
    print("the reader's branches: %d of 7 planted, each a STOP" % stops)
    ok = ok and stops == 7
    print("control: %s" % ("every check holds -- exit 0" if ok else "a check fails -- exit 1"))
    return 0 if ok else 1


def main(argv):
    if len(argv) < 3 or argv[0] not in ("run", "control"):
        print(__doc__, file=sys.stderr)
        return 2
    mode, root, sub, rest = argv[0], os.path.realpath(argv[1]), argv[2], argv[3:]
    opts = {}
    while rest:
        if rest[0] == "--only-bare" and mode == "run":
            opts["--only-bare"] = True
            rest = rest[1:]
            continue
        if rest[0] not in ("--at", "--row", "--bare") or len(rest) < 2 or mode != "run":
            print(__doc__, file=sys.stderr)
            return 2
        opts[rest[0]] = rest[1]
        rest = rest[2:]
    try:
        if mode == "control":
            return control(root, sub)
        return run(root, sub, opts.get("--at"), opts.get("--row"), opts.get("--bare"),
                   only_bare=opts.get("--only-bare", False))
    except Stop as e:
        print("STOP: %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
