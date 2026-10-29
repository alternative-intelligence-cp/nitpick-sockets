#!/usr/bin/env python3
"""Each `// obligation:` comment of a module, made LIVE one at a time: the function's `never fails {` replaced by the
comment's clause and `{`, the copy compiled alone by the pinned npkc. Prints one line per obligation and a summary.

    python3 -B obligations.py <npkc> <scratch dir> <module.npk>...

THE FORM IT READS: `// obligation: <clause>`, then each continuation of the clause as a comment line indented ten columns
or more (under the clause), then a bare `//` or the function's head -- `func:` or `pub func:`, ending `never fails {` --
with only comment lines between.

THE STOPS. A line the reader cannot place would cut a clause short, and a count over it would read "12; compile: 12"
with a part of a clause never compiled. So each of these is a STOP by name, before anything is compiled:
  1. a line that follows a clause and is none of a continuation, a bare `//` or the function's head -- among them a
     continuation indented under ten columns;
  2. an obligation comment spelt otherwise than `// obligation: <clause>` (`//obligation:`, `// Obligation:`, a clause
     left empty);
  3. a comment run that ends, or meets another obligation comment, before a function's head, or whose head does not
     end `never fails {`.
Its CONTROLS run first, on every run: planted text for the reader -- a sound clause with its continuation read, and each
STOP's forms, each of which must stop -- and two planted modules compiled as the real ones are: a sound obligation
compiles live, and one naming a name its function has not (`resultz`) is refused by npkc.

Exit 0 when every obligation compiles live; 1 otherwise -- an obligation npkc refuses, a STOP, or a control that fails;
2 on a usage error.
"""
import os
import re
import shutil
import subprocess
import sys

STRICT = re.compile(r"^// obligation: (\S.*)$")
SPELT = re.compile(r"^\s*//\s*obligation\s*:", re.I)
CONT = re.compile(r"^//\s{10,}\S")
BARE = re.compile(r"^//\s*$")
HEAD = re.compile(r"^(?:pub )?func:(\w+)")
CODES = re.compile(r"^(NITPICK-[A-Z]+-\d+) \S+:(\d+:\d+)", re.M)


def read(lines, where):
    """([(name, clause, head index)], [stop]): each obligation of a module's lines, read or stopped on."""
    items, stops = [], []
    i = 0
    while i < len(lines):
        m = STRICT.match(lines[i])
        if not m:
            if SPELT.match(lines[i]):
                stops.append("%s:%d is an obligation comment spelt otherwise than `// obligation: <clause>`: %r" % (
                    where, i + 1, lines[i][:60]))
            i += 1
            continue
        clause = [m.group(1).strip()]
        j = i + 1
        while j < len(lines) and CONT.match(lines[j]):
            clause.append(lines[j][2:].strip())
            j += 1
        nxt = lines[j] if j < len(lines) else ""
        if not (BARE.match(nxt) or HEAD.match(nxt)):
            stops.append("%s:%d follows an obligation's clause and is no continuation indented ten columns or more, no "
                         "bare `//` and no function head: %r" % (where, j + 1, nxt[:60]))
            i = j + 1
            continue
        k = j
        while k < len(lines) and lines[k].startswith("//") and not (STRICT.match(lines[k]) or SPELT.match(lines[k])):
            k += 1
        if k >= len(lines) or not HEAD.match(lines[k]):
            stops.append("%s:%d ends an obligation's comment run, which names no function beneath it: %r" % (
                where, k + 1, lines[k][:60] if k < len(lines) else "(end of file)"))
            i = k          # the line that ended the run is read in its turn: it may be an obligation of its own
            continue
        if not lines[k].rstrip().endswith("never fails {"):
            stops.append("%s:%d is the head of an obligation's function and does not end `never fails {`: %r" % (
                where, k + 1, lines[k][:60]))
            i = k + 1
            continue
        items.append((HEAD.match(lines[k]).group(1), " ".join(clause), k))
        i = j
    return items, stops


def compile_live(npkc, scratch, mod, lines, name, live, k):
    """(compiles live, the codes npkc printed): the module with function `name`'s `never fails {` made `live {`."""
    head = lines[k].rstrip()
    variant = lines[:k] + [head[:-len("never fails {")] + live + " {"] + lines[k + 1:]
    d = os.path.join(scratch, os.path.basename(mod)[:-4] + "_" + name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    path = os.path.join(d, os.path.basename(mod))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(variant))
    r = subprocess.run([npkc, os.path.basename(path), "-o", "/dev/null"], cwd=d, capture_output=True, text=True)
    codes = " ".join("%s %s" % c for c in CODES.findall(r.stdout + r.stderr))
    return r.returncode == 0 and not codes, "npkc %d -- %s" % (r.returncode, codes)


SOUND = ["// obligation: never fails requires n >= 0i64", "//             ensures result >= 0i64", "//",
         "// A planted obligation, with a continuation.", "func:planted = int64(int64:n) never fails {", "    pass n;", "};"]


def reader_controls():
    """(cases as planted, cases): the planted text, each as it must be read or stopped on."""
    def swap(i, line):
        return SOUND[:i] + [line] + SOUND[i + 1:]
    cases = [("a sound clause with its continuation", SOUND, 1, 0),
             ("a continuation indented 9 columns", swap(1, "//         ensures result >= 0i64"), 0, 1),
             ("a continuation at the comment's own margin", swap(1, "// ensures result >= 0i64"), 0, 1),
             ("a prose line straight after the clause", swap(1, "// A prose line."), 0, 1),
             ("an obligation spelt `//obligation:`", swap(0, "//obligation: never fails requires n >= 0i64"), 0, 1),
             ("an obligation spelt `// Obligation:`", swap(0, "// Obligation: never fails requires n >= 0i64"), 0, 1),
             ("an obligation with no clause", swap(0, "// obligation: "), 0, 1),
             ("a comment run with no function beneath it", SOUND[:4], 0, 1),
             ("a comment run that meets a second obligation comment first", SOUND[:4] + SOUND, 1, 1),
             ("a head that does not end `never fails {`", swap(4, "func:planted = int64(int64:n) {"), 0, 1)]
    ok = 0
    for _, lines, n_items, n_stops in cases:
        items, stops = read(lines, "planted")
        ok += (len(items), len(stops)) == (n_items, n_stops)
    return ok, len(cases)


def compile_controls(npkc, scratch):
    """(cases as planted, cases): a sound planted obligation compiles live, one naming a name it has not is refused."""
    ok = 0
    for tag, clause, want in (("sound", "n >= 0i64", True), ("refused", "n >= 0i64 ensures resultz >= 0i64", False)):
        lines = ["mod:control_%s;" % tag, "// obligation: never fails requires " + clause, "//", "// A planted obligation.",
                 "func:planted = int64(int64:n) never fails {", "    pass n;", "};"]
        items, stops = read(lines, "planted")
        live, text = compile_live(npkc, scratch, "control_%s.npk" % tag, lines, items[0][0], items[0][1], items[0][2])
        ok += (not stops) and live == want and (want or "NITPICK-RESOLVE-002" in text)
    return ok, 2


def main(argv):
    if len(argv) < 4:
        print(__doc__.split("\n\n")[1])
        return 2
    npkc, scratch, mods = argv[1], argv[2], argv[3:]
    os.makedirs(scratch, exist_ok=True)
    rk, rn = reader_controls()
    ck, cn = compile_controls(npkc, scratch)
    print("controls: reader %d of %d as planted (a sound clause read; each of %d planted forms it does not read a STOP); "
          "compile %d of %d (a sound planted obligation compiles live, one naming `resultz` is refused)" % (
              rk, rn, rn - 1, ck, cn))
    if (rk, ck) != (rn, cn):
        print("STOP: a control failed")
        return 1
    total = ok = 0
    reads, stops = [], []
    for mod in mods:
        with open(mod, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        items, st = read(lines, os.path.basename(mod))
        reads.append((mod, lines, items))
        stops += st
    if stops:
        for s in stops:
            print("STOP %s" % s)
        print("obligations not compiled: %d line(s) the reader does not read" % len(stops))
        return 1
    for mod, lines, items in reads:
        for name, live, k in items:
            good, text = compile_live(npkc, scratch, mod, lines, name, live, k)
            total += 1
            ok += good
            print("%s %s: %s" % (os.path.basename(mod), name, "compiles live" if good else text))
    print("obligations made live one at a time: %d; compile: %d" % (total, ok))
    return 0 if total == ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
