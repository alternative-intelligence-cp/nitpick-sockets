#!/usr/bin/env python3
"""0.0.2 -- the harness's own checks, each broken alone in a copy of the tree, and what the runner says.

    python3 -B mutants.py <tree>

Every row of `mutants.tsv` beside this script, `name<TAB>file<TAB>old<TAB>new` (`\\n` a newline, `\\t` a tab in a
text), is one edit; the rows sharing a name are one mutant. For the unchanged tree and then each mutant in the
table's order, the tree's COMMITTED `HEAD` is copied (`git archive`) into `$A/mut/<name>/`, each edit made
EXACTLY ONCE -- any other count is a STOP, printed, and that mutant is not run -- and `harness/run.py` is run in
the copy, under `python3 -B`, with `$NPKC` and `$NPKRT` from the environment. It prints one line per mutant:
`<name>: exit <n> --` and the run's first failing line (a `FAIL` line, else a `failed:` line, else its `CANNOT
PROCEED` line), cut at 200 characters, or its summary when nothing failed. Three run at a time; the copies are
removed at the end. Each mutant breaks ONE facet of one check, so the line names the check that saw it, and the
two controls the other way end GREEN or red by the one check they lean on (`0.0.2.md` §5). After
`nitpick-parse`'s `0.0.2_tools/mutants.py`.

    python3 -B mutants.py selftest      the statuses `main` gives, each planted through `verdict`

Exit 0 when every row ends its way: the unchanged tree and each control the other way GREEN (`GREEN` below, which
the table's header names), and every other mutant red, a non-zero exit; 3 when one does not -- a mutant that must be
red exits 0 (it survives), or a GREEN row does not; 1 on a STOP, a mutant not run, which outranks a 3, or on an error
the tool does not catch. A later pass reads the status, never the lines alone. `selftest` exits 0 when each planted
set of outcomes gives its status, and 1 when one does not.
"""
import concurrent.futures
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# The rows that must end GREEN beside the unchanged tree: this table's controls the other way, its header names each.
GREEN = ("library-shapes-allowed",)


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
        s = open(p, encoding="utf-8").read()
        if s.count(old) != 1:
            return f"{name}: STOP -- the text to replace occurs {s.count(old)} times in {f}", None
        open(p, "w", encoding="utf-8").write(s.replace(old, new))
    r = subprocess.run([sys.executable, "-B", os.path.join(d, "harness", "run.py")], cwd=d,
                       capture_output=True, text=True)
    lines = (r.stdout + r.stderr).splitlines()
    key = (next((x for x in lines if x.startswith("FAIL")), None)
           or next((x.strip() for x in lines if x.startswith("  failed:")), None)
           or next((x for x in lines if "CANNOT PROCEED" in x), None)
           or (lines[-1] if lines else "no output"))
    return f"{name}: exit {r.returncode} -- {key[:200]}", r.returncode


def verdict(results):
    """The status `main` exits with, from each row's (name, exit), an exit of None being a STOP: the mutant not run."""
    if any(code is None for _, code in results):
        return 1
    if any((code == 0) != (name == "unchanged" or name in GREEN) for name, code in results):
        return 3
    return 0


def selftest():
    """Each planted set of outcomes through `verdict`; 0 when each gives the status planted, 1 when one does not."""
    cases = [("every row its way", [("unchanged", 0), ("a-mutant", 1)], 0),
             ("a mutant that survives", [("unchanged", 0), ("a-mutant", 0)], 3),
             ("the unchanged tree red", [("unchanged", 1), ("a-mutant", 1)], 3)]
    cases += [("a control the other way red", [("unchanged", 0), (g, 1), ("a-mutant", 1)], 3) for g in GREEN]
    cases += [("a STOP", [("unchanged", 0), ("a-mutant", None)], 1),
              ("a STOP beside a survivor", [("unchanged", 0), ("b-mutant", 0), ("a-mutant", None)], 1)]
    ok = sum(verdict(rows) == want for _, rows, want in cases)
    print("selftest: %d of %d planted outcome sets as planted -- %s" % (
        ok, len(cases), "; ".join("%s %d" % (what, want) for what, _, want in cases)))
    return 0 if ok == len(cases) else 1


def main(argv):
    if argv[1:] == ["selftest"]:
        return selftest()
    tree = os.path.realpath(argv[1])
    base = os.path.join(os.environ["A"], "mut")
    shutil.rmtree(base, ignore_errors=True)
    order, rows = table()
    jobs = [("unchanged", [])] + [(n, rows[n]) for n in order]
    with concurrent.futures.ThreadPoolExecutor(3) as ex:
        results = list(ex.map(lambda j: one(tree, base, *j), jobs))
    for line, _ in results:
        print(line)
    shutil.rmtree(base, ignore_errors=True)
    return verdict([(name, code) for (name, _), (_, code) in zip(jobs, results)])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
