#!/usr/bin/env python3
"""0.0.4 -- the planting sweep that every loop under `src/` is REACHED by the unit suite (the planning guide's G8).

    python3 -B loops.py <tree>

A loop no unit enters is a loop no test has run, however green the suite. So, for each `for` loop of each module
under `src/` -- read through the harness's own reader, `harness/lexical.py`, so a loop in a comment or a string is
none -- the tree's COMMITTED `HEAD` is copied (`git archive`) into `$A/loops/<n>/`, ONE statement is planted first in
that loop's body, on its own line,

    int64:g8_planted = (<binding> - <binding>) + 9223372036854775807i64 + 1i64;

an `int64` overflow, which traps `IntOverflow` and so exits 93 through every unit's `failsafe` (`PLAYBOOK.md` §3's
convention) at both legs; `exit 93i32` cannot be planted, since `exit` outside `main` and `failsafe` is
`NITPICK-TYPE-010`, and the binding keeps the sum from being a constant. Then every unit of `tests/unit/` that imports
that module -- its `use` lines read by `lexical.imports()` -- is built as the harness builds a program (`npkc`, `llc`,
`ld.lld -static` with `$NPKRT`, and again through `opt -O2`) in name order, and run, under its `mem-cap-mib:` cap if it
carries one, until one exits 93 at BOTH legs: the loop is REACHED, and the line names that unit. If none does, the loop
is NOT REACHED and the sweep fails.

Its CONTROL runs the other way, on every run: a function no unit calls, holding one loop, is appended to the first
module of `src/` that has a loop, and planted the same way; every unit importing it is built and run, and the control
passes only if none exits 93 -- a sweep that called every loop reached would fail it.

A `for` whose binding is not an integer cannot take this plant, and a `while` or `when` loop is not planted at all:
each is a STOP by name, for the cycle that writes the first one to extend this sweep. Exit 0 when every loop is reached
and the control is not; 1 otherwise.
"""
import os
import re
import resource
import shutil
import subprocess
import sys

INTS = {"int8", "int16", "int32", "int64", "int128", "uint8", "uint16", "uint32", "uint64", "uint128"}
FOR = re.compile(r"\bfor\s*\(\s*([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)\s+in\b")
OTHER = re.compile(r"\b(while|when)\b")
PLANT = "int64:g8_planted = ({b} - {b}) + 9223372036854775807i64 + 1i64;"
CONTROL = ("\n// g8 control: a loop no unit calls.\nfunc:g8_unreached = int64(int64:n) never fails {\n"
           "    int64:t = 0i64;\n    for (int64:c in 0i64...n) {\n        t = t + c;\n    }\n    pass t;\n};\n")


def copy(tree, dest):
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    arc = subprocess.run(["git", "-C", tree, "archive", "HEAD"], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", dest], input=arc, check=True)


def loops_in(root, lexical):
    """[(relpath, line, type, binding, offset of the body's `{` in the file's bytes)] and [(relpath, line, word)]."""
    found, other = [], []
    for d, dirs, fs in os.walk(os.path.join(root, "src")):
        dirs.sort()
        for f in sorted(x for x in fs if x.endswith(".npk")):
            path = os.path.join(d, f)
            rel = os.path.relpath(path, root)
            code = lexical.blank(lexical.read(path))
            for m in OTHER.finditer(code):
                other.append((rel, code.count("\n", 0, m.start()) + 1, m.group(1)))
            for m in FOR.finditer(code):
                depth, i = 0, code.index("(", m.start())
                while True:
                    depth += {"(": 1, ")": -1}.get(code[i], 0)
                    if depth == 0:
                        break
                    i += 1
                j = i + 1
                while code[j] in " \t":
                    j += 1
                if code[j] != "{":
                    raise SystemExit("STOP: %s:%d: a `for` whose body does not open on its header's line"
                                     % (rel, code.count("\n", 0, m.start()) + 1))
                found.append((rel, code.count("\n", 0, m.start()) + 1, m.group(1), m.group(2), j))
    return found, other


def plant(root, rel, brace, binding):
    path = os.path.join(root, rel)
    raw = open(path, "rb").read()
    line_start = raw.rfind(b"\n", 0, brace) + 1
    indent = re.match(rb"[ \t]*", raw[line_start:]).group(0).decode() + "    "
    text = "\n" + indent + PLANT.format(b=binding)
    open(path, "wb").write(raw[:brace + 1] + text.encode() + raw[brace + 1:])


def units_of(root, module_rel, lexical):
    out = []
    udir = os.path.join(root, "tests", "unit")
    for f in sorted(os.listdir(udir)):
        if not f.endswith(".npk"):
            continue
        path = os.path.join(udir, f)
        for _, target, _ in lexical.imports(lexical.read(path)):
            if os.path.realpath(os.path.join(udir, target)) == os.path.realpath(os.path.join(root, module_rel)):
                out.append(path)
                break
    return out


def run_unit(path, work):
    """(-O0 exit, -O2 exit), or a string saying where the build stopped."""
    os.makedirs(work, exist_ok=True)
    b = os.path.join(work, os.path.basename(path)[:-4])
    npkc, npkrt = os.environ["NPKC"], os.environ["NPKRT"]
    r = subprocess.run([npkc, os.path.basename(path), "-o", b + ".ll"], cwd=os.path.dirname(path),
                       capture_output=True, text=True)
    if r.returncode != 0:
        return "npkc %d -- %s" % (r.returncode, " ".join(re.findall(r"^NITPICK-[A-Z]+-\d+", r.stdout + r.stderr, re.M)))
    steps = [["llc", "-O0", "-filetype=obj", "-relocation-model=static", b + ".ll", "-o", b + ".o"],
             ["ld.lld", "-static", b + ".o", npkrt, "-o", b],
             ["opt", "-O2", "-S", b + ".ll", "-o", b + ".2.ll"],
             ["llc", "-O2", "-filetype=obj", "-relocation-model=static", b + ".2.ll", "-o", b + ".2.o"],
             ["ld.lld", "-static", b + ".2.o", npkrt, "-o", b + ".2"]]
    for s in steps:
        if subprocess.run(s, capture_output=True).returncode != 0:
            return "%s refused" % s[0]
    cap = re.search(r"^// mem-cap-mib: (\d+)$", open(path, encoding="utf-8").read(), re.M)
    limit = (lambda: resource.setrlimit(resource.RLIMIT_AS, (int(cap.group(1)) << 20,) * 2)) if cap else None
    exits = []
    for exe in (b, b + ".2"):
        try:
            exits.append(subprocess.run([exe], capture_output=True, preexec_fn=limit, timeout=120).returncode)
        except subprocess.TimeoutExpired:
            exits.append("timeout")
    return tuple(exits)


def reached(root, rel, lexical, work):
    """(the unit that exits 93 at both legs, or None; how many units were run; how many import the module)."""
    units = units_of(root, rel, lexical)
    for k, u in enumerate(units, 1):
        got = run_unit(u, work)
        if got == (93, 93):
            return os.path.relpath(u, root), k, len(units)
    return None, len(units), len(units)


def main(argv):
    tree = os.path.realpath(argv[1])
    base = os.path.join(os.environ["A"], "loops")
    shutil.rmtree(base, ignore_errors=True)
    probe = os.path.join(base, "read")
    copy(tree, probe)
    sys.path.insert(0, os.path.join(probe, "harness"))
    import lexical
    found, other = loops_in(probe, lexical)
    for rel, line, word in other:
        raise SystemExit("STOP: %s:%d: a `%s` loop, which this sweep does not plant -- extend it first" % (rel, line, word))
    for rel, line, typ, binding, _ in found:
        if typ not in INTS:
            raise SystemExit("STOP: %s:%d: a `for` over `%s:%s`, whose binding this plant cannot take -- extend it "
                             "first" % (rel, line, typ, binding))
    mods = sorted({rel for rel, *_ in found})
    print("loops under src/: %d `for` loop(s) in %d module file(s), 0 `while` or `when`; units importing each: %s"
          % (len(found), len(mods), ", ".join("%s %d" % (os.path.basename(m), len(units_of(probe, m, lexical)))
                                             for m in mods) or "none"))
    bad, hit, control = 0, 0, "absent, with no loop to append it beside"
    for n, (rel, line, typ, binding, brace) in enumerate(found, 1):
        root = os.path.join(base, str(n))
        copy(tree, root)
        plant(root, rel, brace, binding)
        unit, ran, of = reached(root, rel, lexical, os.path.join(root, ".g8"))
        if unit:
            hit += 1
            print("%s:%d for (%s:%s): REACHED -- %s exits 93 at -O0 and -O2" % (rel, line, typ, binding, unit))
        else:
            bad += 1
            print("%s:%d for (%s:%s): NOT REACHED -- none of %d unit(s) importing it exits 93" % (rel, line, typ,
                                                                                               binding, of))
        shutil.rmtree(root, ignore_errors=True)
    if mods:
        root = os.path.join(base, "control")
        copy(tree, root)
        path = os.path.join(root, mods[0])
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(CONTROL)
        got, _ = loops_in(root, lexical)
        rel, line, typ, binding, brace = [x for x in got if x[0] == mods[0]][-1]
        plant(root, rel, brace, binding)
        unit, ran, of = reached(root, rel, lexical, os.path.join(root, ".g8"))
        if unit:
            bad += 1
            control = "REACHED"
            print("control: a loop no unit calls, appended to %s: REACHED by %s -- the sweep cannot fail" % (rel, unit))
        else:
            control = "not reached"
            print("control: a loop no unit calls, appended to %s: NOT REACHED by any of %d unit(s) importing it, as it "
                  "must be" % (rel, of))
    shutil.rmtree(base, ignore_errors=True)
    print("loops: %d of %d reached by a unit; the control %s; the sweep %s" % (hit, len(found), control,
                                                                                "GREEN" if not bad else "RED"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
