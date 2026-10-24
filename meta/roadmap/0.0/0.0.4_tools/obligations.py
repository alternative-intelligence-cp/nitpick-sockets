#!/usr/bin/env python3
"""Each `// obligation:` comment of a module, made LIVE one at a time: the function's `never fails {` replaced by the
comment's clause and `{`, the copy compiled alone by the pinned npkc. Prints one line per obligation and a summary.

    python3 -B obligations.py <npkc> <scratch dir> <module.npk>...
"""
import os
import re
import shutil
import subprocess
import sys

npkc, scratch, mods = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(scratch, exist_ok=True)
total = ok = 0
for mod in mods:
    text = open(mod, encoding="utf-8").read()
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r"^// obligation: (.*)$", lines[i])
        if not m:
            i += 1
            continue
        clause = [m.group(1).strip()]
        j = i + 1
        while j < len(lines) and re.match(r"^//\s{10,}\S", lines[j]):
            clause.append(lines[j][2:].strip())
            j += 1
        k = j
        while k < len(lines) and not re.match(r"^(pub )?func:", lines[k]):
            k += 1
        head = lines[k]
        name = re.match(r"^(?:pub )?func:(\w+)", head).group(1)
        live = " ".join(clause)
        assert head.rstrip().endswith("never fails {"), (mod, name, head)
        variant = lines[:k] + [head.rstrip()[:-len("never fails {")] + live + " {"] + lines[k + 1:]
        d = os.path.join(scratch, os.path.basename(mod)[:-4] + "_" + name)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        path = os.path.join(d, os.path.basename(mod))
        open(path, "w", encoding="utf-8").write("\n".join(variant))
        r = subprocess.run([npkc, os.path.basename(path), "-o", "/dev/null"], cwd=d, capture_output=True, text=True)
        codes = " ".join(re.findall(r"^(NITPICK-[A-Z]+-\d+) \S+:(\d+:\d+)", r.stdout + r.stderr, re.M) and
                         ["%s %s" % c for c in re.findall(r"^(NITPICK-[A-Z]+-\d+) \S+:(\d+:\d+)", r.stdout + r.stderr, re.M)])
        total += 1
        ok += r.returncode == 0 and not codes
        print("%s %s: %s" % (os.path.basename(mod), name, "compiles live" if r.returncode == 0 and not codes
                             else "npkc %d -- %s" % (r.returncode, codes)))
        i = j
print("obligations made live one at a time: %d; compile: %d" % (total, ok))
