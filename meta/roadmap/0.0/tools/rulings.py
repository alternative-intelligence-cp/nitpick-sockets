#!/usr/bin/env python3
"""Cycle 0.0 -- the shapes the compiler's rulings in landing 112's commit (D-353 … D-359) and its landing 114
(DEF-250) refuse or reserve, counted over `.npk` files the way `shapes.py` counts (comments and strings blanked),
so a plan can say which it writes. Added by `nitpick-parse`'s cycle 0.0.2 plan, and taken from it by this cycle's 0.0.0.

    python3 -B rulings.py [--sites] <file>...
    python3 -B rulings.py --selftest

  a module-level binding, by kind    landing 114 (DEF-250): one with NO initialiser is `NITPICK-TYPE-055` at its
                                     declaration, as a plain one with an initialiser already is at the pin
                                     (D-211); a `fixed` one with an initialiser is the kind that stays. A binding's
                                     kind is the qualifier its line leads with -- `fixed`, `const`, `wild`, `wildx` or
                                     `stack` (the pin's tests/grammar/whole_grammar.npk spells `pub fixed`,
                                     `wild int8->:global_buffer;` and `stack int32:scoped = 1i32;` at module level)
                                     -- or none, "plain"
  `NULL`                             D-355: legal only for a `wild` pointer, by a landing of its own
  `comptime`                         D-353: a value parameter is RESERVED (landing 117); a `comptime func:` is
                                     compile-time only
  an impl declared away from both    the orphan rule (S-37): an `impl:<Type>:<Trait>` lives in the module of its
  its trait and its type             trait or its type; one whose file declares neither is the shape to read

THE STOP. A line at brace depth 0 that has a binding's shape, `<type>:<name>` and then `=` or `;`, but whose leading
words are not `pub` and one qualifier above -- an attribute, `limit<…>`, a second qualifier, `nodrop`, `move`, `sealed`,
a type this reader does not spell, such as `Map<int64, int64>` or `int32[#three()]` -- is a form it does not read, and
counting it as nothing would leave a count short without saying so. Each is printed last as `STOP <file>:<line>` with
the word it stops at, and the run exits 1. A file it cannot read is a STOP too. Exit 0: every such line was read. A line
that declares (`comptime func:f`, `async func:f`) is no binding and no STOP.

`--selftest` plants, in memory, each qualifier with and without an initialiser and with `pub`, each form above that is a
STOP, the places a STOP must not fire (a comment, a string, a body, a declaration with a modifier), and a file that
cannot be read, through `main` itself: exit 0 when each is as planted, 1 when one is not.
"""
import contextlib
import io
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import blank  # noqa: E402

QUALIFIERS = ("fixed", "const", "wild", "wildx", "stack")
_KEYWORDS = "func|struct|enum|trait|impl|mod|error|use|extern|macro|unit|rule"
_DECL = re.compile(r"\s*(pub\s+)?(%s)\b" % _KEYWORDS)
_TYPE = r"[\w<>\[\]\-?]+(?:->)?"
_BINDING = re.compile(r"\s*(?:pub\s+)?(?:(%s)\s+)?(%s)\s*:\s*\w+\s*(=|;)" % ("|".join(QUALIFIERS), _TYPE))
_SHAPE = re.compile(r"(%s)\s*:\s*\w+\s*(=|;)" % _TYPE)
_DECLARING = re.compile(r"\b(%s)\s*:" % _KEYWORDS)  # `async func:f`, `comptime func:f`, `opaque struct:S`


def scan_text(text, path):
    """({kind: [site]}, [(site, why)]): the shapes in one file's text, and each depth-0 line shaped like a binding
    that this reader does not read, with the first word it cannot place."""
    text = blank(text)
    found, stops = {}, []

    def hit(kind, n):
        found.setdefault(kind, []).append("%s:%d" % (path, n))

    depth = 0
    for n, line in enumerate(text.split("\n"), 1):
        if depth == 0 and not _DECL.match(line):
            m = _BINDING.match(line)
            if m:
                if m.group(3) == ";":
                    hit("a module-level binding with no initialiser", n)
                else:
                    hit("a module-level binding, %s, initialised" % (m.group(1) or "plain"), n)
            else:
                s = _SHAPE.search(line)
                if s and not _DECLARING.search(line):
                    words = line[:s.start()].split()
                    words = words[1:] if words[:1] == ["pub"] else words
                    words = words[1:] if words[:1] and words[0] in QUALIFIERS else words
                    stops.append(("%s:%d" % (path, n),
                                  "leads with `%s`, which is no form this reader reads (a `pub` and one of %s, then "
                                  "`<type>:<name>`)" % ((words or line.split())[0], ", ".join(QUALIFIERS))))
        depth += line.count("{") - line.count("}")
        for _ in re.finditer(r"\bNULL\b", line):
            hit("`NULL`", n)
        for _ in re.finditer(r"\bcomptime\b", line):
            hit("`comptime`", n)
    declared = set(re.findall(r"\b(?:struct|enum|trait):(\w+)", text))
    for m in re.finditer(r"\bimpl:(\w+):(\w+)", text):
        if m.group(1) not in declared and m.group(2) not in declared:
            hit("an impl whose file declares neither its type nor its trait", text[:m.start()].count("\n") + 1)
    return found, stops


def status(stops):
    """The exit status: 1 when any line was a form not read, 0 when every one was read."""
    return 1 if stops else 0


def main(argv):
    sites = "--sites" in argv
    files = [a for a in argv[1:] if a != "--sites"]
    total, stops, read = {}, [], 0
    for f in files:
        try:
            with open(f, "rb") as fh:
                text = fh.read().decode("utf-8", errors="replace")
        except OSError as e:
            stops.append((f, "cannot be read: %s" % e.strerror))
            continue
        read += 1
        found, st = scan_text(text, f)
        for kind, where in found.items():
            total.setdefault(kind, []).extend(where)
        stops += st
    print("%d file(s) read" % read)
    for kind in sorted(total):
        print("  %s: %d%s" % (kind, len(total[kind]), ("  " + " ".join(total[kind])) if sites else ""))
    for site, why in stops:
        print("STOP %s: %s" % (site, why))
    return status(stops)


def selftest():
    """Plant every form in memory and read it with `scan_text`; True when each is as planted."""
    read = [("int64:a = 1i64;", "a module-level binding, plain, initialised"),
            ("int64:a;", "a module-level binding with no initialiser")]
    for q in QUALIFIERS:
        read += [("%s int8->:a = 0i64;" % q, "a module-level binding, %s, initialised" % q),
                 ("%s int8->:a;" % q, "a module-level binding with no initialiser"),
                 ("pub %s int8->:a;" % q, "a module-level binding with no initialiser")]
    got = []
    for text, kind in read:
        found, stops = scan_text(text + "\n", "planted")
        got.append(list(found) == [kind] and not stops)
    stop = [("limit<r_positive> int32:a = 1i32;", "limit<r_positive>"),
            ("#[cfg(debug)] int32:a = 1i32;", "#[cfg(debug)]"), ("nodrop int8->:a;", "nodrop"),
            ("wild nodrop int8->:a;", "nodrop"), ("pub move int8->:a;", "move"),
            ("fixed wild int8->:a = 0i64;", "wild"), ("Map<int64, int64>:a;", "Map<int64,")]
    stopped = []
    for text, word in stop:
        found, stops = scan_text(text + "\n", "planted")
        stopped.append(not found and ["`%s`" % word in why for _, why in stops] == [True] and status(stops) == 1)
    # none of them is a STOP in a comment, a string, a struct's body or a function's
    quiet = ["// limit<r_positive> int32:a = 1i32;", "string:s = \"nodrop int8->:a;\";",
             "struct:S = {\n    wild int8->:a;\n};", "func:f = NIL() {\n    wild int8->:a = NULL;\n};",
             "async func:f<F: Work> = int32(F->:f) { int32:a = await Work.run(f) ?! E9; pass a; };"]
    silent = [not scan_text(t + "\n", "planted")[1] for t in quiet]
    # a file it cannot read, through `main` itself: a STOP printed, exit 1
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main(["rulings.py", "/nonexistent/planted.npk"])
    unreadable = code == 1 and "STOP /nonexistent/planted.npk" in out.getvalue()
    print("selftest: %d of %d bindings read as planted, %d of %d unread forms a STOP at the word planted, %d of %d "
          "places where none fires, an unreadable file a STOP and `main`'s status %d" % (
              sum(got), len(got), sum(stopped), len(stopped), sum(silent), len(silent), code))
    return all(got) and all(stopped) and all(silent) and unreadable


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    sys.exit(main(sys.argv))
