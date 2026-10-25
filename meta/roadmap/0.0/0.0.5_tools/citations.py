#!/usr/bin/env python3
"""Cycle 0.0.5 -- every place outside cycle 0.0's folder that names a file in it, or cites a place inside one of its
plans: what the archive (`0.0.5.md` step 7) moves away from under a reader. Blocks 0b and 2.

    python3 -B citations.py "$REPO"

A permanent file -- a specification, a tool's docstring, a probe's header -- cites a rule or a fact by a permanent
name, never by a cycle file's section, which the close archives (the scoped re-verification's F5). So this reads
every file `git ls-files` lists, the `.npk` sources AMONG them (a probe's header is such a file, and `tools/sweep.py`
leaves every `.npk` out), but four kinds: cycle 0.0's own folder, `meta/roadmap/0.0/` or `done/0.0/`; the decision
log, `meta/DECISIONS.md`, whose settled text is never rewritten and records where each decision was measured;
`LICENSE`; and the research digests, by their first line (`tools/sweep.py`'s `DIGEST`), each history as of its date.
Each file is read as `tools/sweep.py` reads one -- its lines' markers and emphasis stripped and the lines joined -- so
a citation a line break splits is one string, and each hit is printed at the line it starts on:

  * PATH  -- a path into the folder: `roadmap/0.0/`, `roadmap/done/0.0/`, `0.0/0.0.<n>`;
  * PLACE -- a place inside a cycle 0.0 plan: `0.0.<n>.md`; `0.0.<n>'s` plan, block, step, mutants, facts, record,
    request, table or §; `0.0.<n>, step <k>` and the like; a plan's `§<n>`; a subcycle's plan, record, block or step;
    a record's quotation.

A citation of a PROBE by its number is not a hit: `tests/probe/` is permanent. Each hit's verdict is the plan's
(`0.0.5.md` §1.5). The control runs first: one planted line per form, each found -- one of them split by a line
break -- a twin phrased without a subcycle's number, found by its subject, and a citation of probes, left alone.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import sweep  # noqa: E402 -- the one reading of joined text, sweep.py's

SUB = r"0\.0\.[0-5][a-z]?"
PATH = re.compile(r"roadmap/(?:done/)?0\.0(?:/|\b)|\b0\.0/0\.0\.\d")
PLACE = re.compile(
    r"\b" + SUB + r"\.md\b"
    r"|\b" + SUB + r"'s (?:plan|block|step|mutants?|facts|record|request|table|§)"
    r"|\b" + SUB + r",? (?:step|block|§) ?\d"
    r"|\bplan(?:'s|,) §\s?\d"
    r"|\bsubcycle's (?:plan|record|block|step)"
    r"|\brecord quotes\b|\bquoted in (?:the|its|that) (?:subcycle's )?record\b", re.I)
SKIP = re.compile(r"^meta/roadmap/(?:done/)?0\.0/|^meta/DECISIONS\.md$|^LICENSE$")

PLANTED = [
    ("a path into the folder", ["see meta/roadmap/0.0/0.0.0.md for it"], "PATH"),
    ("the archived path", ["now meta/roadmap/done/0.0/0.0.0.md"], "PATH"),
    ("a plan's file name", ["as `0.0.3.md` says"], "PLACE"),
    ("a subcycle's mutants", ["the shapes cycle 0.0.2's mutants measured"], "PLACE"),
    ("a step, across a line break", ["> written at the close (0.0.5, step", "> 4). That is"], "PLACE"),
    ("a plan's section", ["written out in full in cycle 0.0.0's plan, §13:"], "PLACE"),
    ("a record's quotation", ["by the first run, quoted in that subcycle's record"], "PLACE"),
    ("the record quotes", ["whose log prints it and the record quotes"], "PLACE"),
]
TWIN = ["as the probes' own subcycle's plan measured it"]
LEFT_ALONE = ["Measured at compiler `c9baa9e` by cycle 0.0.0's probes 13 and 13b"]


def hits(lines):
    text, where = sweep.joined(lines)
    out = []
    for cls, rx in (("PATH", PATH), ("PLACE", PLACE)):
        for m in rx.finditer(text):
            out.append((where[m.start()], cls, m.group(0)))
    return sorted(set(out))


def control():
    found = sum(1 for _, lines, cls in PLANTED if any(c == cls for _, c, _ in hits(lines)))
    twin = bool(hits(TWIN))
    alone = not hits(LEFT_ALONE)
    print("citations' control: %d of %d planted forms found; the twin %s; a citation of probes %s" % (
        found, len(PLANTED), "found" if twin else "NOT FOUND", "left alone" if alone else "FOUND"))
    return found == len(PLANTED) and twin and alone


def main(root):
    ok = control()
    files = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True).stdout.split("\n")
    read, npk, found = 0, 0, []
    for f in sorted(x for x in files if x and not SKIP.search(x)):
        p = os.path.join(root, f)
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                lines = fh.read().split("\n")
        except UnicodeDecodeError:
            continue
        if lines and sweep.DIGEST.match(lines[0].rstrip()):
            continue
        read += 1
        npk += f.endswith(".npk")
        for n, cls, what in hits(lines):
            found.append("  %-5s %s:%d -- %s" % (cls, f, n, what))
    print("citations: %d file(s) read, %d of them .npk -- every tracked file but cycle 0.0's folder, the decision log, "
          "LICENSE and the research digests" % (read, npk))
    print("citations found: %d" % len(found))
    print("\n".join(found)) if found else None
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
