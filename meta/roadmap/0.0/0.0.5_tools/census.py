#!/usr/bin/env python3
"""Cycle 0.0.5 -- the shapes the compiler's landings 141 ... 161 judge anew, and the nine safety rules of the
workbench `PLAYBOOK.md` §2 bind, counted over EVERY program cycle 0.0 compiles: each tracked `.npk` of the tree, and
every fixture the self-check wrote under `build/harness/selfcheck/` at the full run before it. Block 3, after that run.

    python3 -B census.py "$REPO" <keywords.npk>

None of those landings is at the pin, so no program here can be compiled by one; this is the reading the cycle
README's landing table rests on for every file: where a program writes one of these shapes, an adoption that carries
the landing compiles that program first. Each program is read with its comments and its string literals blanked, as
the compiler reads code (`tools/shapes.py`'s reading). Every hit is printed, for reading, one per line, but a member
dot's, which is counted; the census judges nothing.

  func-in-body  a `func:` declared inside a brace that is no `impl`'s or `trait`'s, over every `func:` within braces
                (landing 141)
  member-dot    a `.` before a member, after a name, a `)` or a `]`: counted, and each one before a keyword of the
                pin's table or before no name printed (landing 143); a number's `.` is no member's
  macro         `macro` (landing 144)
  atomic        `atomic` or `Atomic<` (landing 146)
  comptime      `comptime` (landing 147)
  pick-list     a `pick` arm naming several values, over every `pick` (landing 151)
  pick-repeat   a value named by two arms of one `pick` (landings 151 and 153)
  give          `give` (landing 152)
  for           a `for (...)` header: its binding (rules 1, 2 and 4; landing 155)
  slice-param   a slice parameter other than `main`'s `cstring[]`, `fixed` or plain (landing 157; rule 7, F99)
  range         a range `[lo...hi]` (landing 158; rule 7)
  slice-local   a slice local not declared `fixed` (landing 159)
  view          `string_bytes(`, `string_from_bytes(` or `#wild_slice` (landings 154 and 156; rules 5 and 6)
  view-stored   a view assigned into a field or an element (rule 5)
  ptr-write     a write through `<-` (landing 160; rule 6)
  ptr-return    a function whose result is a pointer (landing 161)
  spawn         a `drop` of a call to a function the same file declares `async` (rule 9)
  shared        `shared_arena`, `List<` or `channel` (rules 8 and 9)

A statement is read where a line, a `{` or a `;` starts it, so a write inside a one-line body is counted. The control
runs first: one planted line per class, counted in code -- the three statement classes each inside a one-line body --
and the same text in a comment and in a string, each left out; then a member dot after a name of each character class
-- a letter, a name ending in a digit (`a1.if`), an underscore inside one and leading one, a capital -- each counted
and flagged before the keyword, and a number's dots, a decimal's and a range's, left out.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from names import keywords  # noqa: E402 -- the one reading of the pin's keyword table, names.py's


def blank(text):
    """Comments and string literals replaced by spaces, newlines kept, so a hit's line is the file's."""
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", text[i:j]))
            i = j
        elif text[i] == '"':
            j = i + 1
            while j < n and text[j] != '"' and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
            out.append('"' + re.sub(r"[^\n]", " ", text[i + 1:j - 1]) + '"')
            i = j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


CLASSES = [
    ("func-in-body", None),
    ("member-dot", None),
    ("macro", re.compile(r"\bmacro\b")),
    ("atomic", re.compile(r"\batomic\b|\bAtomic<")),
    ("comptime", re.compile(r"\bcomptime\b")),
    ("pick-list", None),
    ("pick-repeat", None),
    ("give", re.compile(r"\bgive\b")),
    ("for", re.compile(r"\bfor\s*\(")),
    ("slice-param", re.compile(r"(?:^|[(,])\s*(?:fixed\s+)?(?!cstring\b)\w+(?:<[^>]*>)?\[\]:\w+(?=\s*[,)])", re.M)),
    ("range", re.compile(r"\[[^\]\n]*\.\.\.[^\]\n]*\]")),
    ("slice-local", re.compile(r"(?:^|(?<=[{;]))[ \t]*(?!fixed\b)\w+(?:<[^>]*>)?\[\]:\w+\s*=", re.M)),
    ("view", re.compile(r"\bstring_bytes\s*\(|\bstring_from_bytes\s*\(|#wild_slice\b")),
    ("view-stored", re.compile(r"(?:^|(?<=[{;]))[ \t]*[\w.]+(?:\[[^\]\n]*\])*\.\w+\s*=\s*(?:string_bytes|string_from_bytes|#wild_slice)"
                               r"|\]\s*=\s*(?:string_bytes|string_from_bytes|#wild_slice)", re.M)),
    ("ptr-write", re.compile(r"(?:^|(?<=[{;]))[ \t]*\(?<-[^=;\n]*?\)?\s*(?:\.\w+|\[[^\]\n]*\])*\s*=(?!=)", re.M)),
    ("ptr-return", re.compile(r"\bfunc:\w+\s*=\s*(?:wild\s+)?[\w<>]+->\??\s*\(")),
    ("spawn", None),
    ("shared", re.compile(r"\bshared_arena\b|\bList<|\bchannel\b")),
]
ASYNC = re.compile(r"\basync\s+func:(\w+)")
FUNC = re.compile(r"\bfunc:\w+")
DOT = re.compile(r"(?<!\.)\.(?![.\d])\s*(\w*)")
TOKEN = re.compile(r"\w+$")
PICK = re.compile(r"\bpick\s*\(")
ARM = re.compile(r"\(([^()]*)\)\s*\{")


def match_brace(b, i):
    """The index just past the `}` that closes the `{` at i."""
    depth = 0
    for j in range(i, len(b)):
        if b[j] == "{":
            depth += 1
        elif b[j] == "}":
            depth -= 1
            if depth == 0:
                return j + 1
    return len(b)


def openers(b):
    """For each `{`, whether its header -- the text back to the last `;`, `{` or `}` -- opens an `impl` or a `trait`."""
    out = {}
    for m in re.finditer(r"\{", b):
        k = max(b.rfind(";", 0, m.start()), b.rfind("{", 0, m.start()), b.rfind("}", 0, m.start()))
        head = b[k + 1:m.start()].strip()
        out[m.start()] = bool(re.match(r"(?:pub\s+)?(?:impl|trait)\b", head))
    return out


def scan(text, kw):
    b = blank(text)
    lines = text.split("\n")
    out = {k: [] for k, _ in CLASSES}
    dots = picks = braced = 0

    def hit(k, pos):
        ln = b.count("\n", 0, pos) + 1
        out[k].append((ln, lines[ln - 1].strip()))

    ops = openers(b)
    for m in FUNC.finditer(b):
        stack = []
        for j, c in enumerate(b[:m.start()]):
            if c == "{":
                stack.append(j)
            elif c == "}" and stack:
                stack.pop()
        braced += bool(stack)
        if stack and not ops.get(stack[-1], False):
            hit("func-in-body", m.start())
    for m in DOT.finditer(b):
        if m.start() == 0 or not re.match(r"[\w)\]]", b[m.start() - 1]):
            continue
        tok = TOKEN.search(b, max(0, m.start() - 120), m.start())
        if tok and tok.group(0)[0].isdigit():
            continue  # a number's `.`, never a member's: a name never starts with a digit
        dots += 1
        if not m.group(1) or not re.match(r"[A-Za-z_]", m.group(1)) or m.group(1) in kw:
            hit("member-dot", m.start())
    for m in PICK.finditer(b):
        o = b.find("{", m.end())
        if o < 0:
            continue
        picks += 1
        end = match_brace(b, o)
        body, depth, seen, i = b[o + 1:end - 1], 0, set(), 0
        while i < len(body):
            c = body[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == "(" and depth == 0:
                a = ARM.match(body, i)
                if a:
                    vals = [v.strip() for v in a.group(1).split(",")]
                    if len(vals) > 1:
                        hit("pick-list", o + 1 + i)
                    for v in vals:
                        if v in seen:
                            hit("pick-repeat", o + 1 + i)
                        seen.add(v)
                    i = a.end() - 1
                    continue
            i += 1
    for k, rx in CLASSES:
        if k == "spawn":
            names = set(ASYNC.findall(b))
            rx = re.compile(r"\bdrop\s+(?:%s)\s*\(" % "|".join(map(re.escape, sorted(names)))) if names else None
        if rx is None:
            continue
        for m in rx.finditer(b):
            hit(k, m.start())
    return out, (dots, picks, braced)


PLANT = {
    "func-in-body": "func:f = NIL() {\n    func:g = NIL() { pass NIL; };\n    pass NIL;\n};",
    "member-dot": "int64:n = a.if;",
    "macro": "macro m = { };",
    "atomic": "Atomic<int64>:a = x;",
    "comptime": "comptime int64:c = 1i64;",
    "pick-list": "pick (e) {\n    (A, B) { pass 1i64; },\n    (*) { pass 0i64; }\n}",
    "pick-repeat": "pick (e) {\n    (A) { pass 1i64; },\n    (A) { pass 2i64; }\n}",
    "give": "give 1i64;",
    "for": "for (int64:k in 0i64...3i64) { }",
    "slice-param": "func:f = int64(fixed uint8[]:src) never fails { pass 0i64; };",
    "range": "fixed uint8[]:r = a[0i64...2i64];",
    "slice-local": "if (c) { uint8[]:p = a; }",
    "view": "fixed uint8[]:v = string_bytes(s);",
    "view-stored": "if (c) { h.v = string_bytes(s); }",
    "ptr-write": "if (c) { <-one = 1i8; }",
    "ptr-return": "func:g = Node->(Node->:p) never fails { pass p; };",
    "spawn": "async func:h = NIL() { pass NIL; };\ndrop h();",
    "shared": "shared_arena<int64>:s = x;",
}


# A name of each character class before a member dot, and a number's dots (a decimal's and a range's), which are none.
DOT_NAMES = ["a", "a1", "a_b", "_a", "A"]
DOT_NUMBERS = ["1.5", "0i64...3i64"]


def control(kw):
    code = comment = string = 0
    for k, line in PLANT.items():
        code += bool(scan(line, kw)[0][k])
        comment += not any(scan("\n".join("// " + x for x in line.split("\n")), kw)[0].values())
        string += not any(scan("\n".join('string:t = "%s";' % x.replace('"', "") for x in line.split("\n")),
                               kw)[0].values())
    n = len(PLANT)
    print("census controls: %d of %d classes counted in code; %d of %d left out of a comment; %d of %d left out of a "
          "string" % (code, n, comment, n, string, n))
    names = sum(scan("int64:n = %s.if;" % x, kw)[1][0] == 1 and len(scan("int64:n = %s.if;" % x, kw)[0]["member-dot"])
                == 1 for x in DOT_NAMES)
    nums = sum(scan("int64:n = %s;" % x, kw)[1][0] == 0 for x in DOT_NUMBERS)
    print("census member-dot controls: %d of %d names' dots counted and flagged before a keyword (%s); %d of %d numbers' "
          "dots left out (%s)" % (names, len(DOT_NAMES), ", ".join(x + ".if" for x in DOT_NAMES), nums,
                                   len(DOT_NUMBERS), ", ".join(DOT_NUMBERS)))
    return code == comment == string == n and names == len(DOT_NAMES) and nums == len(DOT_NUMBERS)


def main(root, kwfile):
    kw = keywords(kwfile)
    ok = len(kw) > 0 and control(kw)
    tracked = subprocess.run(["git", "-C", root, "ls-files", "*.npk"], capture_output=True, text=True).stdout.split()
    fixtures = []
    for d, _, fs in os.walk(os.path.join(root, "build", "harness", "selfcheck")):
        fixtures += [os.path.relpath(os.path.join(d, f), root) for f in fs if f.endswith(".npk")]
    progs = sorted(tracked) + sorted(fixtures)
    print("census: %d program(s) -- %d tracked .npk, %d self-check fixture(s) under build/harness/selfcheck/; %d "
          "keywords in the pin's table" % (len(progs), len(tracked), len(fixtures), len(kw)))
    total = {k: [] for k, _ in CLASSES}
    dots = picks = braced = 0
    for rel in progs:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
            got, (nd, np, nb) = scan(fh.read(), kw)
        dots, picks, braced = dots + nd, picks + np, braced + nb
        for k, hs in got.items():
            total[k] += ["%s:%d: %s" % (rel, ln, t[:110]) for ln, t in hs]
    for k, _ in CLASSES:
        if k == "member-dot":
            print("census member-dot: %d, %d of them before a keyword or no name" % (dots, len(total[k])))
        elif k == "func-in-body":
            print("census func-in-body: %d, of %d `func:` within braces" % (len(total[k]), braced))
        elif k in ("pick-list", "pick-repeat"):
            print("census %s: %d, over %d pick(s)" % (k, len(total[k]), picks))
        else:
            print("census %s: %d" % (k, len(total[k])))
        for h in total[k]:
            print("  " + h)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
