#!/usr/bin/env python3
"""0.0.4 -- `src/core/` and what guards it, each broken alone in a copy of the tree, and what the runner says.

    python3 -B mutants.py <tree>

Every row of `mutants.tsv` beside this script, `name<TAB>file<TAB>old<TAB>new` (`\\n` a newline, `\\t` a tab in a
text), is one edit; the rows sharing a name are one mutant. An `old` of exactly `<new file>` PLANTS the file, `new`
its whole text, and the file must not exist in the copy. For the unchanged tree and then each mutant in the
table's order, the tree's COMMITTED `HEAD` is copied (`git archive`) into `$A/mut/<name>/`, each edit made
EXACTLY ONCE -- any other count is a STOP, printed, and that mutant is not run -- and `harness/run.py` is run in
the copy, under `python3 -B`, with `$NPKC` and `$NPKRT` from the environment. It prints one line per mutant:
`<name>: exit <n> --` and the run's first failing line, cut at 200 characters, or its summary when nothing failed:
the first `failed:` line that carries its finding -- a build step's or a tree check's, whose `FAIL` line can pass 200
characters before the finding begins -- else the first `FAIL` line (a unit's `failed:` line names only the unit),
else its `CANNOT PROCEED` line. Three run at a time; the copies are
removed at the end. Each mutant breaks ONE facet of `src/core/` or of what guards it -- an accessor's check, a free,
a guard before an addition, the digits' leading zeros, a bound's value, the unit that instantiates the generics --
so its line names what saw it first in the run's order: the self-check, build step 2, or a unit by its exit
(`0.0.4.md` §5). Cycle 0.0.3's `mutants.py`, but for this docstring and the choice of line above.
"""
import concurrent.futures
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def table():
    order, rows = [], {}
    with open(os.path.join(HERE, "mutants.tsv"), encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            name, f, old, new = line.rstrip("\n").split("\t")
            un = lambda t: t.replace("\\n", "\n").replace("\\t", "\t")
            if name not in rows:
                order.append(name)
                rows[name] = []
            rows[name].append((f, un(old), un(new)))
    return order, rows


def one(tree, base, name, edits):
    d = os.path.join(base, name)
    os.makedirs(d)
    arc = subprocess.run(["git", "-C", tree, "archive", "HEAD"], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", d], input=arc, check=True)
    for f, old, new in edits:
        p = os.path.join(d, f)
        if old == "<new file>":
            if os.path.exists(p):
                return f"{name}: STOP -- {f} exists already, and the row plants it"
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(new)
            continue
        s = open(p, encoding="utf-8").read()
        if s.count(old) != 1:
            return f"{name}: STOP -- the text to replace occurs {s.count(old)} times in {f}"
        open(p, "w", encoding="utf-8").write(s.replace(old, new))
    r = subprocess.run([sys.executable, "-B", os.path.join(d, "harness", "run.py")], cwd=d,
                       capture_output=True, text=True)
    lines = (r.stdout + r.stderr).splitlines()
    key = (next((x.strip() for x in lines if x.startswith("  failed: ") and ": " in x[len("  failed: "):]), None)
           or next((x for x in lines if x.startswith("FAIL")), None)
           or next((x for x in lines if "CANNOT PROCEED" in x), None)
           or (lines[-1] if lines else "no output"))
    return f"{name}: exit {r.returncode} -- {key[:200]}"


def main(argv):
    tree = os.path.realpath(argv[1])
    base = os.path.join(os.environ["A"], "mut")
    shutil.rmtree(base, ignore_errors=True)
    order, rows = table()
    jobs = [("unchanged", [])] + [(n, rows[n]) for n in order]
    with concurrent.futures.ThreadPoolExecutor(3) as ex:
        results = list(ex.map(lambda j: one(tree, base, *j), jobs))
    for line in results:
        print(line)
    shutil.rmtree(base, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
