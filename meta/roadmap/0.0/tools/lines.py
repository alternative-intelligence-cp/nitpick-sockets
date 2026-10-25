#!/usr/bin/env python3
"""Cycle 0.0 -- THE CITATION CHECK, fix round 2's check (a) (management_3's ruling of 2026-10-25): every file:line
citation the plan makes is resolved mechanically against the tree it names, and the cited line must hold the text the
sentence cites.

    python3 -B lines.py run     "$REPO"      # every citation, by form, with its tree, its line and what it holds
    python3 -B lines.py control "$REPO"      # each form planted in a scratch file and found; a sound citation of
                                             # each passes, a stale one is a HIT, a clause naming nothing is a HIT

THE SET. Every citation of a file with a line number or a range in the plan's own files -- `0.0.0.md` ... `0.0.5.md`
and the README -- in every step patch's added and context lines, and in the plan's tools (`tools/`, `<sub>_tools/`,
docstrings and comments with the rest of their text). The forms, each counted on its own:
  * `path:N` and `path:N–M` (an en dash or a hyphen), the path in backticks or bare;
  * `line N of path`, `lines N–M of path`;
  * `path`'s line N, `path` line N, `path` from line N;
  * a named file's line: `its line N` (the file named last before it in the same unit), `probe NN's line N`
    (`tests/probe/NN*.npk`), `the X.Y roadmap's line N` (`meta/roadmap/X.Y/README.md`);
  * `path` N -- a file in backticks and a bare number, with its list (`7, 22 … 26, 102 and 125`, `15 ×2`): the sweep
    tables' form; a number followed by a unit (`B`, `bytes`, `files`, `lines` ...) is not one;
  * a bare `:N` or `:N–M` after a file named earlier in the same unit.
The checks' own data -- `twins.tsv`, `twins_classes.txt`, and the planted and clean files of the other tools -- are
skipped by name, and so is the README's section that records the two checks' output; the run prints what it skips.

THE TREE. A path is looked up in this repository's tree, then the compiler's, then the workbench's: its exact path, or
else the one file whose path ends with it; a path no tree holds, or that ends more than one file of a tree, is a HIT.
  * the compiler: the commit the clause names right after the citation (`at `c9baa9e``), else the pin, read with
    `git --no-optional-locks -C $NPK_TREE show <commit>:<path>`;
  * this repository: a step patch's line is read at the tree that patch leaves; a subcycle file's prose at the tree
    the subcycle starts from, but its sweep section at the tree its sweep runs at; the README at the tree the last
    patch leaves. The trees are built here: a `git clone --shared` of the repository's HEAD under
    `$REPO/.internal/w00/lines/`, the plan folder copied in as the checkout holds it, every patch applied in plan order
    through `apply.py`, and each step's tree taken by `git write-tree`;
  * the workbench: its files as its clone holds them.

WHAT THE LINE MUST HOLD. The cited text is what the citation's clause -- from the previous citation, or the sentence's
start, to the next, or the sentence's end -- quotes or names: a quoted string ("…" or “…”), a string in backticks that
is not a path or a commit, or a label (a decision's `SK-n`, a placeholder `@@PD-n@@` read through `decisions.txt` as
`apply.py` writes it, a rule's or an entry's name such as `B-2a` or `O-N3`). A string holds when it starts on the cited
line (or in the range), read through `sweep.py`'s transform with case ignored, an ellipsis splitting it into parts that
must follow in order; a label holds when it is on the line or the line lies in its entry. A citation holds when one of
its texts does, and the run prints which. A clause that names nothing checkable is a HIT, and so is one none of whose
texts the line holds.

THE SWEEP TABLES. A row of a subcycle's sweep table -- `| subject | n | sites |` in the section headed "The sweep's
candidates" -- cites every candidate its subject's pattern finds. It is resolved by running that subcycle's sweep
(`sweep.py run`) at the tree it runs at (SWEEP_AT, from each subcycle file's step table): the row's sites, each with its
`×k`, must be exactly the subject's candidates, and its count their number; a row that differs is a HIT.

THE BLOCKS. A citation in a fenced block -- a command, or an Expect, which is a run's output -- is counted by form and
resolved by the block comparator, `blocks.py compare`, when the blocks are run: not here.

Exit 0 when every citation resolves and holds, 1 when one is a HIT, 2 on a usage error.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from apply import numbers  # noqa: E402 -- the one reading of decisions.txt
from sweep import strip  # noqa: E402 -- the one transform of a line, the sweep's

PIN = "2e1cb4a"
# The step after which each subcycle's sweep block runs: its last patch, but 0.0.5's, whose step2.patch is the close's.
SWEEP_AT = {"0.0.0": 5, "0.0.1": 6, "0.0.2": 3, "0.0.3": 2, "0.0.4": 3, "0.0.5": 1}
SKIP_NAMES = ("twins.tsv", "twins_classes.txt")
SKIP_SUFFIX = ("_planted.txt", "_clean.txt")
RECORD_HEADING = re.compile(r"^## .*the two checks' record", re.I)

EXT = r"(?:npk|md|py|sh|yml|yaml|toml|txt|tsv|ll|json|patch|c|h)"
FILE = r"(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_-][A-Za-z0-9_.-]*\." + EXT + r"(?![A-Za-z0-9_])|\.gitignore"
N = r"\d{1,5}"
DASH = r"\s?[–-]\s?"
UNIT = (r"(?:B|KiB|MiB|GiB|bytes?|files?|lines?|tracked|programs?|words?|identities|candidates?|of|runs?|cases?|"
        r"entries|rows?|hunks?|sites?|modules?|symbols?|edges?|tests?|probes?|steps?|blocks?|s|ms|%)\b")
NUMLIST = (N + r"(?:\s?×\s?\d+)?(?:(?:,\s|\sand\s|\s?(?:…|\.\.\.)\s?|" + DASH + r")" + N + r"(?:\s?×\s?\d+)?)*")
FORMS = [
    ("path:N", re.compile(r"`?(?P<f>" + FILE + r")`?:(?P<a>" + N + r")(?:" + DASH + r":?(?P<b>" + N + r"))?(?![\d:])")),
    ("line N of path", re.compile(r"\blines? (?P<a>" + N + r")(?:" + DASH + r"(?P<b>" + N + r"))? (?:of|in) `?(?P<f>"
                                  + FILE + r")")),
    ("path's line N", re.compile(r"`(?P<f>" + FILE + r")`(?:'s)? (?:from )?lines? (?P<a>" + N + r")(?:" + DASH
                                 + r"(?P<b>" + N + r"))?\b")),
    ("named line N", re.compile(r"\b(?P<who>probe \d\d[a-z]?|the \d\.\d+ roadmap|its)(?:'s)? lines? (?P<a>" + N
                                + r")(?:" + DASH + r"(?P<b>" + N + r"))?\b")),
    ("`path` N", re.compile(r"`(?P<f>" + FILE + r")` (?P<list>" + NUMLIST + r")(?![\d.,/:]\d|\.\d| ?" + UNIT
                            + r"|-)")),
    ("bare :N", re.compile(r"(?<=[\s(])(?P<colon>:)(?P<a>" + N + r")(?:" + DASH + r"(?P<b>" + N + r"))?(?![\d:])")),
]
FORM_NAMES = [f for f, _ in FORMS]
FILE_ANY = re.compile(r"`?(" + FILE + r")`?")
SHA = re.compile(r"^[0-9a-f]{7,40}$")
LABEL = re.compile(r"@@PD-\d+@@|\b(?:SK|D|DEF|PD)-\d+\b|\b[A-Z]{1,3}-[A-Z]?\d+[a-z]?\b")
QUOTE = re.compile(r"\"([^\"]{3,}?)\"|“([^”]{3,}?)”|`([^`]{3,}?)`")
SENT_END = re.compile(r"(?<=[.;!?])\s+(?=[A-Z`*(\"“])|;\s|\s\|\s")


def sh(*a, cwd=None, ok=False):
    r = subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)
    if r.returncode and not ok:
        raise SystemExit("STOP: %s failed: %s" % (" ".join(a[:6]), (r.stderr or r.stdout).strip()[:300]))
    return r.stdout


def plan_dir(root):
    d = os.path.join(root, "meta", "roadmap", "0.0")
    return d if os.path.isdir(d) else os.path.join(root, "meta", "roadmap", "done", "0.0")


def steps(plan):
    out = []
    for d in sorted(os.listdir(plan)):
        m = re.fullmatch(r"(0\.0\.\d+)_tools", d)
        if m:
            ns = sorted(int(x[4:-6]) for x in os.listdir(os.path.join(plan, d)) if re.fullmatch(r"step\d+\.patch", x))
            out += [(m.group(1), n) for n in ns]
    return out


class Trees:
    """The trees: this repository's at each step (built by applying the patches), the compiler's, the workbench's."""

    def __init__(self, repo, wb, npk):
        self.repo, self.wb, self.npk = repo, wb, npk
        self.plan = plan_dir(repo)
        self.blobs, self.lists = {}, {}
        self.tree = {}
        self.sweeps = {}
        base, order = numbers_table(self.plan)
        self.pd_to_sk = {"@@%s@@" % pd: "SK-%03d" % (base + k + 1) for k, pd in enumerate(order)}

    def build(self):
        a = os.path.join(self.repo, ".internal", "w00", "lines")
        dest = os.path.join(a, "chain")
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        os.makedirs(a, exist_ok=True)
        head = sh("git", "-C", self.repo, "rev-parse", "HEAD").strip()
        sh("git", "clone", "-q", "--shared", "--no-checkout", self.repo, dest)
        sh("git", "-C", dest, "checkout", "-q", "--detach", head)
        rel = os.path.relpath(self.plan, self.repo)
        shutil.rmtree(os.path.join(dest, rel))
        shutil.copytree(self.plan, os.path.join(dest, rel))
        sh("git", "-C", dest, "add", "-A", rel)
        differ = [x for x in sh("git", "-C", dest, "diff", "--cached", "--name-only", "HEAD").split("\n") if x]
        self.tree["base"] = sh("git", "-C", dest, "write-tree").strip()
        print("trees: HEAD %s, the plan folder as the checkout holds it (%d file(s) differ from HEAD); every patch "
              "applied in plan order by apply.py" % (head[:7], len(differ)))
        prev = "base"
        self.after = {}
        for sub, n in steps(self.plan):
            out = sh("python3", "-B", os.path.join(HERE, "apply.py"), dest, sub, str(n), ok=True)
            if not out.startswith("APPLY"):
                raise SystemExit("STOP: %s step%d did not apply: %s" % (sub, n, out.strip()))
            t = sh("git", "-C", dest, "write-tree").strip()
            self.tree[(sub, n)] = t
            self.after[sub] = (sub, n)
            prev = (sub, n)
            if SWEEP_AT.get(sub) == n:
                self.sweeps[sub] = parse_sweep(sh("python3", "-B", os.path.join(HERE, "sweep.py"), "run", dest, sub))
        self.last = prev
        self.dest = dest
        print("steps: %d applied; sweeps run at %s" % (
            len(self.tree) - 1, ", ".join("%s after step%d.patch" % (s, SWEEP_AT[s]) for s in sorted(self.sweeps))))

    def start_of(self, sub):
        subs = sorted({s for s, _ in steps(self.plan)})
        i = subs.index(sub)
        return "base" if i == 0 else self.after[subs[i - 1]]

    def files(self, where):
        if where not in self.lists:
            kind, ref = where
            if kind == "repo":
                out = sh("git", "-C", self.dest, "ls-tree", "-r", "--name-only", self.tree[ref])
            elif kind == "npk":
                out = sh("git", "--no-optional-locks", "-C", self.npk, "ls-tree", "-r", "--name-only", ref)
            elif kind == "lib":
                out = sh("git", "--no-optional-locks", "-C", os.path.join(self.wb, "nitpick-" + ref[0]), "ls-tree",
                         "-r", "--name-only", ref[1], ok=True)
            else:
                out = sh("git", "--no-optional-locks", "-C", self.wb, "ls-files")
            self.lists[where] = [x for x in out.split("\n") if x]
        return self.lists[where]

    def find(self, where, path):
        fs = self.files(where)
        if path in fs:
            return [path]
        return [f for f in fs if f.endswith("/" + path)]

    def lines(self, where, path):
        key = (where, path)
        if key not in self.blobs:
            kind, ref = where
            if kind == "repo":
                t = sh("git", "-C", self.dest, "show", "%s:%s" % (self.tree[ref], path))
            elif kind == "npk":
                t = sh("git", "--no-optional-locks", "-C", self.npk, "show", "%s:%s" % (ref, path))
            elif kind == "lib":
                t = sh("git", "--no-optional-locks", "-C", os.path.join(self.wb, "nitpick-" + ref[0]), "show",
                       "%s:%s" % (ref[1], path))
            else:
                with open(os.path.join(self.wb, path), encoding="utf-8", errors="replace") as fh:
                    t = fh.read()
            self.blobs[key] = t.split("\n")
        return self.blobs[key]


def numbers_table(plan):
    base, order = None, []
    with open(os.path.join(plan, "tools", "decisions.txt"), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            m = re.fullmatch(r"base SK-(\d+)", line)
            if m:
                base = int(m.group(1))
            elif re.fullmatch(r"PD-\d+", line):
                order.append(line)
    return base, order


def parse_sweep(out):
    res, cur = {}, None
    for line in out.split("\n"):
        m = re.match(r"^(.+): (\d+) candidate\(s\) in \d+ file\(s\)$", line)
        if m:
            cur = norm_subject(m.group(1))
            res[cur] = {}
        elif line.startswith("  ") and cur is not None:
            f, _, n = line.strip().rpartition(":")
            res[cur][(f, int(n))] = res[cur].get((f, int(n)), 0) + 1
    return res


def norm_subject(s):
    return re.sub(r"\s+", " ", s.replace("`", "").replace("*", "")).strip().lower()


# ---------------------------------------------------------------------------------------------------- the units --

def units_of_md(name, text):
    """(kind, first line, [(line number, text)], section heading) for each unit of a markdown file."""
    out, cur, fence, heading, skip = [], [], False, "", False

    def flush(kind="prose"):
        if cur:
            out.append((kind, cur[0][0], list(cur), heading))
            cur.clear()
    for i, line in enumerate(text.split("\n"), 1):
        if line.startswith("```"):
            flush()
            fence = not fence
            continue
        if fence:
            if not skip:
                out.append(("block", i, [(i, line)], heading))
            continue
        if line.startswith("#"):
            flush()
            heading = line
            skip = bool(RECORD_HEADING.match(line)) and name == "README.md"
            if skip:
                print("skipped by name: README.md's section %r" % line.strip())
        if skip:
            continue
        if not line.strip():
            flush()
            continue
        if line.startswith("|"):
            flush()
            out.append(("row", i, [(i, line)], heading))
            continue
        if re.match(r"^\s*(?:[-*]|\d+\.)\s", line) and cur:
            flush()
        cur.append((i, line))
    flush()
    return out


def units_of_patch(text):
    """(kind, patch line, [(patch line number, text)], target file, start line in the target) per run of lines."""
    out, cur, target = [], [], None

    def flush():
        if cur:
            out.append(("patch", cur[0][0], list(cur), target))
            cur.clear()
    for i, line in enumerate(text.split("\n"), 1):
        if line.startswith("diff --git ") or line.startswith("@@") or line.startswith("--- ") or \
                line.startswith("index ") or line.startswith("+++ "):
            flush()
            if line.startswith("+++ "):
                target = line[6:] if line.startswith("+++ b/") else None
            continue
        if line[:1] not in ("+", " "):
            flush()
            continue
        body = line[1:]
        if not body.strip() or body.startswith("|") or body.startswith("#"):
            flush()
            if body.strip():
                out.append(("patch", i, [(i, body)], target))
            continue
        cur.append((i, body))
    flush()
    return out


def units_of_tool(text):
    out, cur = [], []
    for i, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            if cur:
                out.append(("tool", cur[0][0], list(cur), None))
                cur = []
            continue
        cur.append((i, line))
    if cur:
        out.append(("tool", cur[0][0], list(cur), None))
    return out


# ------------------------------------------------------------------------------------------------ the citations --

def joined(lines):
    """The unit's text, its lines joined by one space, and the source line of each character."""
    parts, where = [], []
    for n, t in lines:
        s = t.strip()
        while s.startswith(">"):
            s = s[1:].lstrip()
        if parts:
            parts.append(" ")
            where.append(n)
        parts.append(s)
        where.extend([n] * len(s))
    return "".join(parts), where


def expand(lst, each=True):
    """`7, 22 … 26, 102 and 125` and `15 ×2` -> [(line, multiplicity)]: a range expanded line by line (a sweep row's
    candidates), or, not `each`, kept as one citation of its lines, (first, -(last - first)) (a sentence's range)."""
    out = []
    toks = re.findall(r"(\d+)(?:\s?×\s?(\d+))?|(…|\.\.\.|[–-])", lst)
    rng = False
    for a, k, dash in toks:
        if dash:
            rng = True
            continue
        n = int(a)
        if rng and out and not each:
            lo = out[-1][0]
            out[-1] = (lo, -(n - lo))
            rng = False
            continue
        if rng and out:
            lo = out[-1][0]
            out += [(x, 1) for x in range(lo + 1, n + 1)]
            if k:
                out[-1] = (n, int(k))
            rng = False
            continue
        out.append((n, int(k) if k else 1))
    return out


def citations(text):
    """[(form, start, end, path or None, who, [(line, mult)])] in the unit's text, in order; overlapping matches are
    read once, the earlier form in FORMS first."""
    found = []
    taken = []
    for form, rx in FORMS:
        for m in rx.finditer(text):
            s, e = m.start(), m.end()
            if any(s < b and a < e for a, b in taken):
                continue
            g = m.groupdict()
            if form == "`path` N":
                lines = expand(g["list"], each=False)
            else:
                a = int(g["a"])
                b = int(g["b"]) if g.get("b") else a
                if b < a:
                    continue
                lines = [(x, 1) for x in range(a, b + 1)]
                if b > a:
                    lines = [(a, -(b - a))]          # a range: one citation of lines a..b
            who = g.get("who")
            path = g.get("f")
            if form == "bare :N":
                prev = [x for x in FILE_ANY.finditer(text[:s]) if s - x.end() < 120]
                if not prev:
                    continue
                path = prev[-1].group(1)
            if form == "named line N" and who == "its":
                prev = list(FILE_ANY.finditer(text[:s]))
                if not prev:
                    found.append((form, s, e, None, who, lines))
                    taken.append((s, e))
                    continue
                path = prev[-1].group(1)
            found.append((form, s, e, path, who, lines))
            taken.append((s, e))
    return sorted(found, key=lambda c: c[1])


def sentence(text, s, e):
    """The bounds of the sentence holding text[s:e]."""
    lo, hi = 0, len(text)
    for m in SENT_END.finditer(text):
        if m.end() <= s:
            lo = m.end()
        elif m.start() >= e:
            hi = m.start()
            break
    return lo, hi


def clause(text, cits, k):
    """The bounds of citation k's clause: from the previous citation, or its sentence's start, to the next, or its
    sentence's end."""
    s, e = cits[k][1], cits[k][2]
    lo, hi = sentence(text, s, e)
    if k and cits[k - 1][2] > lo:
        lo = cits[k - 1][2]
    if k + 1 < len(cits) and cits[k + 1][1] < hi:
        hi = cits[k + 1][1]
    return lo, hi


def spans(text):
    """Every quoted span of a unit's text, paired over the whole unit: backticks, straight and curly double quotes."""
    out = []
    for ch in ("`", '"'):
        pos = [i for i, c in enumerate(text) if c == ch]
        for i in range(0, len(pos) - 1, 2):
            out.append((pos[i], pos[i + 1] + 1, text[pos[i] + 1:pos[i + 1]]))
    for m in re.finditer(r"“([^”]*)”", text):
        out.append((m.start(), m.end(), m.group(1)))
    return out


def texts_of(text, lo, s, e, hi, path, pd_to_sk):
    """The checkable texts a clause names: quoted strings, backticked strings but paths and commits, and labels --
    those after the citation first, then those before it."""
    out = []
    sp = [x for x in spans(text) if x[0] >= lo and x[1] <= hi and (x[1] <= s or x[0] >= e)]
    for part in (lambda x: x[0] >= e, lambda x: x[1] <= s):
        for a, b, t in sorted((x for x in sp if part(x)), key=lambda x: x[0]):
            t = t.strip().strip(",.;:")
            if len(t) < 3 or FILE_ANY.fullmatch(t) or SHA.match(t) or t == path or re.fullmatch(r"[\d\s.,×…–-]+", t):
                continue
            out.append(("label", t) if LABEL.fullmatch(t) else ("text", t))
    for a, b in ((e, hi), (lo, s)):
        for m in LABEL.finditer(text[a:b]):
            t = m.group(0)
            if not any(t in x for _, x in out):
                out.append(("label", t))
    seen, res = set(), []
    for kind, t in out:
        for pd, sk in pd_to_sk.items():
            t = t.replace(pd, sk)
        if (kind, t) not in seen:
            seen.add((kind, t))
            res.append((kind, t))
    return res


def norm(s):
    return re.sub(r"\s+", " ", strip(s)).strip().lower()


def lead(line):
    """A line past its leading markdown markers -- `#`, `>`, `|`, `-`, `*`, `[` and spaces -- read without a regex."""
    i = 0
    while i < len(line) and line[i] in " \t#>|*-[":
        i += 1
    return line[i:]


_ENTRIES = {}


def entry_lines(lines, label):
    key = (id(lines), label)
    if key not in _ENTRIES:
        _ENTRIES[key] = _entry_lines(lines, label)
    return _ENTRIES[key]


def _entry_lines(lines, label):
    """The lines of `label`'s entry in a file: from a line that starts with it (past markdown markers) to the line
    before the next such start of any label, or the next heading."""
    start = re.compile(r"(?:Rule )?" + re.escape(label) + r"\b")
    anyl = re.compile(r"(?:Rule )?(?:SK|D|[A-Z]{1,3})-[A-Z]?\d+[a-z]?\b")
    res = set()
    i = 0
    while i < len(lines):
        if start.match(lead(lines[i])):
            res.add(i + 1)
            j = i + 1
            while j < len(lines) and not anyl.match(lead(lines[j])) and not lines[j].startswith("#"):
                res.add(j + 1)
                j += 1
            i = j
        else:
            i += 1
    return res


def holds(lines, a, span, kind, t):
    """Whether text t starts on line a (or in a..a+span) of lines, or label t is there or its entry holds the lines."""
    last = a + span
    if a < 1 or last > len(lines):
        return False
    if kind == "label":
        if any(re.search(r"\b" + re.escape(t) + r"\b", lines[x - 1]) for x in range(a, last + 1)):
            return True
        ent = entry_lines(lines, t)
        return all(x in ent for x in range(a, last + 1))
    parts = [norm(p) for p in re.split(r"…|\.\.\.", t) if norm(p)]
    if not parts:
        return False
    chunk, starts = "", []
    for x in range(a, min(len(lines), last + 4) + 1):
        s = norm(lines[x - 1])
        if chunk:
            chunk += " "
        starts.append((x, len(chunk)))
        chunk += s
    limit = next((off for x, off in starts if x == last + 1), len(chunk) + 1)
    rx = re.compile(r"\s*.*?".join(re.escape(q) for q in parts), re.S)
    m = rx.search(chunk)
    while m:
        if m.start() < limit:
            return True
        m = rx.search(chunk, m.start() + 1)
    return False


# ------------------------------------------------------------------------------------------------- the checking --

class Check:
    def __init__(self, trees):
        self.t = trees
        self.by_form = {f: 0 for f in FORM_NAMES}
        self.by_kind = {}
        self.ok, self.hits, self.block = [], [], 0
        self.sweep_rows = 0

    def where(self, path, sha):
        """[(where, real path)] for a cited path, or a reason."""
        t = self.t
        cands = []
        for kind, ref in (("repo", self.repo_ref), ("npk", sha or PIN), ("wb", None)):
            if kind == "wb" and not t.wb:
                continue
            got = t.find((kind, ref), path)
            if got:
                cands.append(((kind, ref), got))
        if not cands:
            return None, "no tree holds %s" % path
        (where, got) = cands[0]
        if len(got) > 1:
            return None, "%s ends %d files of the %s tree: %s" % (path, len(got), where[0], ", ".join(got[:4]))
        return (where, got[0]), None

    def resolve(self, src, unit_kind, text, where_of_char, cits, k, repo_ref):
        form, s, e, path, who, lines = cits[k]
        self.by_form[form] += 1
        self.by_kind[unit_kind] = self.by_kind.get(unit_kind, 0) + 1
        at = "%s:%d" % (src[0], src[1](where_of_char[s]))
        if unit_kind == "block":
            self.block += 1
            return
        lo, hi = clause(text, cits, k)
        before, after = text[lo:s], text[e:hi]
        slo, shi = sentence(text, s, e)
        whole = text[slo:shi]
        sub = getattr(self, "cur_sub", None)
        if sub and "this subcycle leaves" in whole:
            repo_ref = self.t.after[sub]
        m = re.search(r"`?step(\d+)\.patch`? leaves", whole)
        if sub and m and (sub, int(m.group(1))) in self.t.tree:
            repo_ref = (sub, int(m.group(1)))
        self.repo_ref = repo_ref
        sha = None
        m = re.match(r"\s?\)?,?\s*(?:\(|,)?\s*at (?:compiler )?`([0-9a-f]{7,40})`", after)
        if m:
            sha = m.group(1)
        lib = re.search(r"`?nitpick-([a-z]+)`?'s\s[^|;]{0,40}$", before)
        if lib and lib.group(1) != "sockets" and path:
            got = re.search(r"`([0-9a-f]{7,40})`", before + after)
            if not got:
                self.by_form[form] += 0
                self.hits.append("HIT  %s %s: `nitpick-%s`'s %s, another library's file, and no commit named" % (
                    at, form, lib.group(1), path))
                return
            wh = ("lib", (lib.group(1), got.group(1)))
            fs = self.t.find(wh, path)
            if len(fs) != 1:
                self.hits.append("HIT  %s %s: `nitpick-%s` at %s holds %d files named %s" % (
                    at, form, lib.group(1), got.group(1), len(fs), path))
                return
            return self.check_lines(at, form, wh, fs[0], (text, lo, s, e, hi), path, lines)
        if who and who != "its":
            if who.startswith("probe"):
                nn = who.split()[1]
                path = "tests/probe/%s" % nn
            else:
                path = "meta/roadmap/%s/README.md" % who.split()[1]
        if path is None:
            self.hits.append("HIT  %s %s: names no file" % (at, form))
            return
        if who and who.startswith("probe"):
            fs = [f for f in self.t.files(("repo", repo_ref)) if re.match(r"tests/probe/probe%s[_.]" % path.split("/")[-1], f)]
            loc = (("repo", repo_ref), fs[0]) if len(fs) == 1 else None
            why = None if loc else "probe %s names %d files" % (path, len(fs))
        else:
            loc, why = self.where(path, sha)
        if loc is None:
            self.hits.append("HIT  %s %s: %s" % (at, form, why))
            return
        (wh, real) = loc
        return self.check_lines(at, form, wh, real, (text, lo, s, e, hi), path, lines)

    def check_lines(self, at, form, wh, real, bounds, path, lines):
        flines = self.t.lines(wh, real)
        tree = tree_name(wh)
        texts = texts_of(*bounds, path, self.t.pd_to_sk)
        for ln, mult in lines:
            span = -mult if mult < 0 else 0
            cite = "%s:%d%s" % (real, ln, "–%d" % (ln + span) if span else "")
            if ln + span > len(flines):
                self.hits.append("HIT  %s %s -> %s %s: past the file's end (%d lines)" % (at, form, tree, cite,
                                                                                           len(flines)))
                continue
            if not texts:
                self.hits.append("HIT  %s %s -> %s %s: the clause names nothing checkable; the line reads %r"
                                 % (at, form, tree, cite, flines[ln - 1].strip()[:90]))
                continue
            good = [t for t in texts if holds(flines, ln, span, t[0], t[1])]
            if good:
                self.ok.append("OK   %s %s -> %s %s holds %s" % (at, form, tree, cite, quote(good[0])))
            else:
                self.hits.append("HIT  %s %s -> %s %s: holds none of %s; the line reads %r" % (
                    at, form, tree, cite, ", ".join(quote(t) for t in texts[:4]), flines[ln - 1].strip()[:90]))

    def sweep_row(self, src, row, sub):
        cells = [c.strip() for c in row.strip().strip("|").split(" | ")]
        if len(cells) < 3 or not re.fullmatch(r"\d+", cells[1]):
            return False
        self.sweep_rows += 1
        n = int(cells[1])
        found = self.t.sweeps.get(sub, {})
        subjects = [norm_subject(cells[0])] if n else [norm_subject(x) for x in cells[0].split(", ")]
        at = "%s:%d" % src
        for subj in subjects:
            if subj not in found:
                self.hits.append("HIT  %s sweep row: no subject %r in %s's sweep" % (at, subj, sub))
                return True
        if n == 0:
            nz = [s for s in subjects if found[s]]
            if nz:
                self.hits.append("HIT  %s sweep row: %s found %s" % (at, nz, [sum(found[s].values()) for s in nz]))
            else:
                self.ok.append("OK   %s sweep row: %d subject(s), 0 candidates, as %s's sweep finds" % (
                    at, len(subjects), sub))
            return True
        want = found[subjects[0]]
        files = sorted({f for f, _ in want})
        got, bad, cur = {}, [], None
        for m in re.finditer(r"`(" + FILE + r")` (" + NUMLIST + r")(?![\d.]| ?" + UNIT + r")|(?:(?<=^)|(?<=; )|"
                             r"(?<=\), )|(?<=, and ))(" + NUMLIST + r")(?![\d.]| ?" + UNIT + r")", cells[2]):
            if m.group(1):
                cur = m.group(1)
                lst = m.group(2)
            else:
                lst = m.group(3)
                if cur is None:
                    bad.append(lst)
                    continue
            real = [f for f in files if f == cur or f.endswith("/" + cur)]
            if len(real) != 1:
                bad.append("%s (%s)" % (cur, "no candidate's file" if not real else "ambiguous"))
                continue
            for ln, k in expand(lst):
                got[(real[0], ln)] = got.get((real[0], ln), 0) + k
        total = sum(got.values())
        if got == want and total == n and not bad:
            self.ok.append("OK   %s sweep row %r: %d candidate(s), each at its line, as %s's sweep finds" % (
                at, subjects[0], n, sub))
        else:
            miss = sorted(set(want) - set(got))
            extra = sorted(set(got) - set(want))
            mult = sorted(x for x in set(got) & set(want) if got[x] != want[x])
            self.hits.append("HIT  %s sweep row %r: row says %d, sites %d, sweep %d; missing %s; not found %s; "
                             "multiplicity %s; unread %s" % (at, subjects[0], n, total, sum(want.values()),
                                                             fmt(miss), fmt(extra), fmt(mult), bad))
        return True


def tree_name(wh):
    if wh[0] == "lib":
        return "nitpick-%s@%s" % wh[1]
    if wh[0] == "repo":
        return "repo@" + (wh[1] if wh[1] == "base" else "%s/step%d" % wh[1])
    return "compiler@%s" % wh[1] if wh[0] == "npk" else "workbench"


def fmt(xs):
    return "[" + ", ".join("%s:%d" % x for x in xs) + "]"


def quote(t):
    return ("%s %s" % ("label", t[1])) if t[0] == "label" else '"%s"' % t[1][:60]


def scan(chk, trees, files, plan):
    """Scan (name, kind, text) files; kind is 'md', 'patch' or 'tool'."""
    for name, kind, text in files:
        if kind == "md":
            sub = name[:-3] if re.fullmatch(r"0\.0\.\d+\.md", name) else None
            chk.cur_sub = sub
            for ukind, first, lines, heading in units_of_md(name, text):
                body, where = joined(lines)
                cits = citations(body)
                if not cits:
                    continue
                if sub and "the sweep's candidates" in heading.lower():
                    ref = (sub, SWEEP_AT[sub])
                    if ukind == "row" and chk.sweep_row((name, first), body, sub):
                        for c in cits:
                            chk.by_form[c[0]] += 1
                            chk.by_kind["sweep row"] = chk.by_kind.get("sweep row", 0) + 1
                        continue
                elif sub:
                    ref = trees.start_of(sub)
                else:
                    ref = trees.last
                for k in range(len(cits)):
                    chk.resolve((name, lambda x: x), ukind, body, where, cits, k, ref)
        elif kind == "patch":
            chk.cur_sub = None
            sub, n = name.split("/")
            ref = (sub.replace("_tools", ""), int(n[4:-6]))
            for ukind, first, lines, target in units_of_patch(text):
                body, where = joined(lines)
                cits = citations(body)
                for k in range(len(cits)):
                    chk.resolve((name, lambda x: x), "patch", body, where, cits, k, ref)
        else:
            for ukind, first, lines, _ in units_of_tool(text):
                body, where = joined(lines)
                cits = citations(body)
                for k in range(len(cits)):
                    chk.resolve((name, lambda x: x), "tool", body, where, cits, k, trees.last)


def plan_files(plan):
    out, skipped = [], []
    for root, ds, fs in os.walk(plan):
        ds.sort()
        for f in sorted(fs):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, plan)
            if f in SKIP_NAMES or f.endswith(SKIP_SUFFIX):
                skipped.append(rel)
                continue
            if "__pycache__" in rel:
                continue
            with open(p, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            kind = "md" if f.endswith(".md") else "patch" if f.endswith(".patch") else "tool"
            out.append((rel, kind, text))
    return out, skipped


def report(chk, nfiles, skipped):
    total = sum(chk.by_form.values())
    print("denominator: %d file(s) of the plan read -- %s; skipped by name: %s" % (
        nfiles, "the subcycle files and the README, every patch's added and context lines, every tool", ", ".join(skipped)))
    print("citations by form: %s; %d in all" % (", ".join("%s %d" % (f, chk.by_form[f]) for f in FORM_NAMES), total))
    print("citations by kind: %s; %d of them in fenced blocks, resolved by blocks.py compare when the blocks run" % (
        ", ".join("%s %d" % (k, v) for k, v in sorted(chk.by_kind.items())), chk.block))
    for line in chk.ok:
        print(line)
    for line in chk.hits:
        print(line)
    print("result: %d citation(s) resolved here (%d sweep row(s)), %d hold, %d HIT(s)" % (
        len(chk.ok) + len(chk.hits), chk.sweep_rows, len(chk.ok), len(chk.hits)))
    return 1 if chk.hits else 0


def layout(argv):
    repo = os.path.realpath(argv[2])
    wb = os.path.realpath(os.path.join(repo, ".."))
    npk = os.path.realpath(os.path.join(wb, "..", "nitpick"))
    for i, a in enumerate(argv):
        if a == "--wb":
            wb = os.path.realpath(argv[i + 1])
        if a == "--npk":
            npk = os.path.realpath(argv[i + 1])
    return repo, wb, npk


def run(argv):
    repo, wb, npk = layout(argv)
    trees = Trees(repo, wb, npk)
    trees.build()
    files, skipped = plan_files(trees.plan)
    chk = Check(trees)
    scan(chk, trees, files, trees.plan)
    return report(chk, len(files), skipped)


def control(argv):
    repo, wb, npk = layout(argv)
    trees = Trees(repo, wb, npk)
    trees.build()
    # a sound line and a stale one, from the trees themselves: a line of the decision log at the base, and the pin's
    # O-N3 comment, the plan's own positive control (finding 1 of the verification of 2026-10-25)
    dl = trees.lines(("repo", "base"), "meta/DECISIONS.md")
    n = next(i for i, x in enumerate(dl, 1) if len(x.split()) >= 6 and not x.startswith("#"))
    words = " ".join(strip(dl[n - 1]).split()[:5])
    stale = next(i for i, x in enumerate(dl, 1) if i > n + 2 and words.lower() not in strip(x).lower() and x.strip())
    tp = trees.lines(("npk", PIN), "src/frontend/types.npk")
    m = next(i for i, x in enumerate(tp, 1) if "cross a spawn" in x)
    # a probe's line and the 0.1 roadmap's, each a named line of the tree the README is read at
    final = ("repo", trees.last)
    probe = next(f for f in trees.files(final) if re.match(r"tests/probe/probe04[_.]", f))
    pl = trees.lines(final, probe)
    pn = next(i for i, x in enumerate(pl, 1) if len(strip(x).split()) >= 4)
    pw = " ".join(strip(pl[pn - 1]).split()[:3])
    rl = trees.lines(final, "meta/roadmap/0.1/README.md")
    rn = next(i for i, x in enumerate(rl, 1) if len(strip(x).split()) >= 4 and not x.startswith("#"))
    rw = " ".join(strip(rl[rn - 1]).split()[:3])
    # a list: two lines of the final decision log that each hold one word
    fl = trees.lines(final, "meta/DECISIONS.md")
    la, lb, lw = next((i, j, w) for i, x in enumerate(fl, 1) for w in strip(x).split()[:1] if len(w) >= 6
                      and w.isalpha() for j in range(i + 1, len(fl) + 1) if strip(fl[j - 1]).startswith(w + " "))
    plants = [
        ("path:N", 'the log at `meta/DECISIONS.md:%d` says "%s".' % (n, words)),
        ("path:N", 'a range, `meta/DECISIONS.md:%d–%d`, "%s".' % (n, n + 1, words)),
        ("line N of path", 'line %d of `meta/DECISIONS.md` reads "%s".' % (n, words)),
        ("path's line N", '`meta/DECISIONS.md`\'s line %d reads "%s".' % (n, words)),
        ("named line N", 'In `meta/DECISIONS.md`, its line %d reads "%s".' % (n, words)),
        ("named line N", 'probe 04\'s line %d reads "%s".' % (pn, pw)),
        ("named line N", 'the 0.1 roadmap\'s line %d reads "%s".' % (rn, rw)),
        ("line N of path", 'lines %d–%d of `meta/DECISIONS.md` read "%s".' % (n, n + 1, words)),
        ("path's line N", '`meta/DECISIONS.md` from line %d, "%s".' % (n, words)),
        ("`path` N", '`meta/DECISIONS.md` %d and %d, "%s".' % (la, lb, lw)),
        ("`path` N", '`meta/DECISIONS.md` %d, "%s".' % (n, words)),
        ("bare :N", 'The file `meta/DECISIONS.md` says it (:%d, "%s").' % (n, words)),
        ("path:N", 'the comment at `src/frontend/types.npk:%d` reads "cross a spawn".' % m),
    ]
    stales = [
        ("path:N", 'the log at `meta/DECISIONS.md:%d` says "%s".' % (stale, words)),
        ("line N of path", 'line %d of `meta/DECISIONS.md` reads "%s".' % (stale, words)),
        ("`path` N", '`meta/DECISIONS.md` %d, "%s".' % (stale, words)),
        ("bare :N", 'The file `meta/DECISIONS.md` says it (:%d, "%s").' % (stale, words)),
        ("path:N", 'and the comment still reads so, `src/frontend/types.npk:%d`, "cross a spawn".' % (m - 23)),
        ("named line N", 'probe 04\'s line %d reads "%s".' % (pn + 1 if strip(pl[pn]) and pw.lower() not in
                                                                   strip(pl[pn]).lower() else pn + 2, pw)),
        ("nothing", 'the comment at `src/frontend/types.npk:%d`, unquoted.' % m),
    ]
    ok = True
    scratch = os.path.join(repo, ".internal", "w00", "lines", "plants.md")
    with open(scratch, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(t for _, t in plants + stales) + "\n")
    print("planted: %d sound citation(s), one per form and the pin's O-N3 comment, and %d stale or empty ones, in "
          "a scratch file beside the trees" % (len(plants), len(stales)))
    for label, group, want in (("sound", plants, "OK"), ("stale", stales, "HIT")):
        for form, text in group:
            chk = Check(trees)
            scan(chk, trees, [("README.md", "md", text)], trees.plan)
            got = (chk.ok + chk.hits)
            forms = [f for f in FORM_NAMES if chk.by_form[f]]
            res = "OK" if chk.ok and not chk.hits else "HIT" if chk.hits else "NONE"
            good = res == want and (form == "nothing" or form in forms)
            ok = ok and good
            print("  %s %-15s found as %s -> %s%s" % (label, form, "/".join(forms) or "nothing", res,
                                                      "" if good else "   <- WRONG"))
            if not good:
                for g in got:
                    print("      " + g)
    os.remove(scratch)
    print("control: %s" % ("every planted form found; every sound citation holds and every stale or empty one is a "
                           "HIT" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("run", "control"):
        print(__doc__)
        sys.exit(2)
    sys.exit(run(sys.argv) if sys.argv[1] == "run" else control(sys.argv))
