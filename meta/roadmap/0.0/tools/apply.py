#!/usr/bin/env python3
"""Cycle 0.0 -- apply one subcycle step's patch, all-or-nothing, and say which of three states the tree was in.

    python3 -B apply.py "$REPO" <subcycle> <step>        e.g.  apply.py "$REPO" 0.0.0 2
    python3 -B apply.py selftest                         the dated-line reading, planted in a temp dir

The patch is `meta/roadmap/0.0/<subcycle>_tools/step<step>.patch` BESIDE THIS SCRIPT -- the plan's own, whatever tree
it is applied to -- a `git diff` of the design chain the plan was cut from, and the review surface: a worker may tighten a text, never change what it says, and amends THE PATCH, never
the tree by hand (the workbench `PLAYBOOK.md` §12).

THE DECISION NUMBERS ARE WRITTEN HERE, NOT IN THE PLAN. Every `@@PD-nnn@@` in a patch becomes this repository's
number for that proposed decision: `decisions.txt` beside this tool lists the accepted PDs in order after a `base`,
and PD at rank k (1-based) is `SK-<base + k>`. A placeholder with no line there is a STOP: the review declined it,
and the hunks that carry it must be re-cut first. The same substitution runs over every patch of every subcycle, so
a later patch's context holds the numbers an earlier one wrote.

  * the patch applies IN REVERSE  -> ALREADY: the step is in the tree; nothing written
  * the patch applies             -> APPLY: written and staged (`git apply --index`), every file of it
  * neither                       -> STOP: the tree is not the one the patch was cut from; nothing was written

`git apply` checks every hunk before it writes any, so a STOP writes nothing.

THE LABELS ARE CHECKED BEFORE ANY HUNK IS (the plan verification of 2026-10-15, its findings 1 and 5). A patch whose
added lines hold any of these is a STOP, by name, and nothing is written:
  * a BARE label, `PD-<n>` outside `@@...@@`, in either case (`pd-161` too, and `@@pd-161@@`, which the
    substitution does not read as a placeholder: fix round 1, the plan verification's finding 11) -- the
    substitution never sees it, so it would land as a label no decision log defines, in a text the review makes
    immutable;
  * a number past the base written out, `SK-<n>` with n > base -- that number is the review's to give;
  * a placeholder CITED BEFORE THE STEP THAT DECLARES IT -- its `### @@PD-n@@` heading is added by a later patch,
    in plan order (every `<subcycle>_tools/step<k>.patch` beside this plan, subcycle by subcycle, step by step),
    so at this step's commit it would name a decision the log does not hold yet; or one that no step declares.

THE RUN'S DATE (the workbench `PLAYBOOK.md` §7: a dated line says when the tree began to say it, so it carries the day
it lands, not the day the plan drafted it; `nitpick-parse`'s mechanism, from its cycle 0.0.2). In an ADDED line, every
`@@DATE@@` becomes ONE date for the whole run of its subcycle: the day the run's first step that carries the placeholder
applied, which that step records in `.internal/w00/<subcycle>.date` of the tree it applies to. Every later step of the
run reads it there, so a run that crosses midnight, or spans days, writes one date everywhere. The file is the hand-off
from one step's worker to the next, kept between steps; the subcycle's record removes it. A re-run reports ALREADY on
any day while the file holds the run's date. In a CONTEXT or REMOVED line, `@@DATE@@` is the date the tree already holds
on that line -- the run's own, written by an earlier step, or an earlier subcycle's, written by its run on a day this plan
cannot know: each such line is found in the file it belongs to, the placeholder read as any date, and the one date the
tree holds there is written in. A line that cannot be read to one date is a STOP, by its own name: found `nowhere`; on
more than one line of the file, with different dates (`with more than one date`); or on one line that holds two
different dates, for a line with two placeholders (`with two different dates on the one line`). `selftest` plants each
in a temp dir (under TMPDIR), reads the date from a sound line, and exits 0 when each is as planted, 1 when one is not.
A file the patches touch must not hold `@@DATE@@` itself before they are applied, and no added line names a date the
run did not write.
"""
import datetime
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLACEHOLDER = re.compile(r"@@(PD-\d+)@@")
DECLARES = re.compile(r"^\+### @@(PD-\d+)@@")
DATE_PLACEHOLDER = "@@DATE@@"


def date_file(root, sub):
    """The run's one date for a subcycle whose patches carry `@@DATE@@`: the file its first applying step writes."""
    return os.path.join(root, ".internal", "w00", sub + ".date")


def run_date(root, sub):
    """(the run's date, whether a step has recorded it): the recorded day, or today's when none has yet."""
    p = date_file(root, sub)
    if not os.path.isfile(p):
        return datetime.date.today().isoformat(), False
    with open(p, encoding="utf-8") as fh:
        day = fh.read().strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise SystemExit("STOP %s: .internal/w00/%s.date holds %r, not a date" % (sub, sub, day))
    return day, True


def tree_dates(root, sub, step, text, strict=True):
    """The patch with every `@@DATE@@` of a context or removed line replaced by the date the tree holds there --
    or, not `strict` (the check whether the step is already in the tree, where a removed line is gone), left as it
    is where the tree holds no such line."""
    out, cur, cache = [], None, {}
    for line in text.split("\n"):
        if line.startswith("+++ "):
            cur = line[6:] if line.startswith("+++ b/") else None
        elif cur and DATE_PLACEHOLDER in line and line[:1] in (" ", "-") and not line.startswith("---"):
            if cur not in cache:
                path = os.path.join(root, cur)
                if os.path.isfile(path):
                    with open(path, encoding="utf-8", newline="") as fh:
                        cache[cur] = fh.read().split("\n")
                else:
                    cache[cur] = []
            parts = [re.escape(p) for p in line[1:].split(DATE_PLACEHOLDER)]
            rx = re.compile("^" + r"(\d{4}-\d{2}-\d{2})".join(parts) + "$")
            found = {m.groups() for m in (rx.match(t) for t in cache[cur]) if m}
            if not strict and len(found) != 1:
                out.append(line)
                continue
            if len(found) != 1 or len(set(next(iter(found)))) != 1:
                why = ("nowhere" if not found else "with more than one date" if len(found) > 1
                       else "with two different dates on the one line")
                raise SystemExit("STOP %s step%s: %s holds the dated context line %r %s" % (
                    sub, step, cur, line[1:80], why))
            day = next(iter(found))[0]
            line = line.replace(DATE_PLACEHOLDER, day)
        out.append(line)
    return "\n".join(out)


def numbers():
    base, order = None, []
    with open(os.path.join(HERE, "decisions.txt"), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("base "):
                m = re.fullmatch(r"base SK-(\d+)", line)
                if not m:
                    raise SystemExit("STOP: decisions.txt's base line is not `base SK-<n>`: %r" % line)
                base = int(m.group(1))
            elif re.fullmatch(r"PD-\d+", line):
                order.append(line)
            else:
                raise SystemExit("STOP: decisions.txt holds a line that is neither a PD nor the base: %r" % line)
    if base is None:
        raise SystemExit("STOP: decisions.txt has no base line")
    return {pd: "SK-%03d" % (base + k + 1) for k, pd in enumerate(order)}


def base_number():
    for line in open(os.path.join(HERE, "decisions.txt"), encoding="utf-8"):
        m = re.fullmatch(r"base SK-(\d+)", line.strip())
        if m:
            return int(m.group(1))
    raise SystemExit("STOP: decisions.txt has no base line")


def plan_order():
    """Every step patch of the cycle beside this plan, in plan order: [(subcycle, step, path)]."""
    out = []
    for d in sorted(glob.glob(os.path.join(HERE, "..", "0.0.*_tools"))):
        sub = os.path.basename(d)[:-len("_tools")]
        steps = []
        for p in glob.glob(os.path.join(d, "step*.patch")):
            m = re.search(r"step(\d+)\.patch$", p)
            if m:
                steps.append((int(m.group(1)), p))
        out += [(sub, str(n), p) for n, p in sorted(steps)]
    return out


def added(raw):
    return [line for line in raw.split("\n") if line.startswith("+") and not line.startswith("+++")]


def label_findings(sub, step, raw):
    """Each way this patch's added lines misuse a decision label (the module's docstring), or []."""
    bad, base = [], base_number()
    for line in added(raw):
        for m in re.finditer(r"\bPD-\d+\b", PLACEHOLDER.sub("", line), re.I):
            bad.append("a bare %s in an added line -- a label is written @@%s@@" % (m.group(0), m.group(0).upper()))
        for m in re.finditer(r"\bSK-(\d+)\b", line):
            if int(m.group(1)) > base:
                bad.append("%s written out in an added line -- a number past the base is the review's" % m.group(0))
    order = plan_order()
    steps = [(s, n) for s, n, _ in order]
    declared = {}
    for s, n, p in order:
        with open(p, encoding="utf-8", newline="") as fh:
            for line in added(fh.read()):
                m = DECLARES.match(line)
                if m:
                    declared.setdefault(m.group(1), (s, n))
    here = steps.index((sub, step)) if (sub, step) in steps else len(steps)
    for pd in sorted(set(PLACEHOLDER.findall("\n".join(added(raw))))):
        if pd not in declared:
            bad.append("%s is declared by no step of the cycle" % pd)
        elif steps.index(declared[pd]) > here:
            bad.append("%s is cited before the step that declares it, %s step%s" % ((pd,) + declared[pd]))
    return bad


def text_of(sub, step):
    # The patch is read from THIS PLAN's tools, beside this script, whatever tree it is applied to: a dry run in a
    # throwaway clone applies the plan's own text, not whatever the clone holds.
    path = os.path.normpath(os.path.join(HERE, "..", sub + "_tools", "step%s.patch" % step))
    if not os.path.isfile(path):
        raise SystemExit("STOP %s step%s: no %s_tools/step%s.patch beside this plan's tools" % (sub, step, sub, step))
    with open(path, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    bad = label_findings(sub, step, raw)
    if bad:
        raise SystemExit("STOP %s step%s: %s" % (sub, step, "; ".join(bad)))
    table = numbers()
    missing = sorted(set(PLACEHOLDER.findall(raw)) - set(table))
    if missing:
        raise SystemExit("STOP %s step%s: no decision number for %s in decisions.txt" % (sub, step, ", ".join(missing)))
    return PLACEHOLDER.sub(lambda m: table[m.group(1)], raw)


def selftest():
    """Plant a file of dated lines and a patch reading them; True when each case is read or stopped on as planted."""
    import tempfile
    files = ["dated 2026-10-18 line", "only 2026-10-18 and 2026-10-19 here", "same 2026-10-18 and 2026-10-18 here",
             "two 2026-10-18 lines", "two 2026-10-19 lines"]
    cases = [(" dated @@DATE@@ line", True, "dated 2026-10-18 line"),
             (" same @@DATE@@ and @@DATE@@ here", True, "same 2026-10-18 and 2026-10-18 here"),
             (" missing @@DATE@@ line", True, "nowhere"),
             (" two @@DATE@@ lines", True, "with more than one date"),
             (" only @@DATE@@ and @@DATE@@ here", True, "with two different dates on the one line"),
             (" missing @@DATE@@ line", False, " missing @@DATE@@ line")]
    good = 0
    with tempfile.TemporaryDirectory() as root:
        with open(os.path.join(root, "planted.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(files) + "\n")
        for line, strict, want in cases:
            patch = "--- a/planted.md\n+++ b/planted.md\n@@ -1,1 +1,1 @@\n%s" % line
            try:
                got = tree_dates(root, "planted", "1", patch, strict).split("\n")[-1].lstrip()
                good += got == want.lstrip()
            except SystemExit as e:
                good += str(e).endswith(want) and strict
    print("selftest: %d of %d dated context lines as planted -- a date read, the same date twice on one line read, "
          "`nowhere`, `with more than one date` and `with two different dates on the one line` each a STOP, and a missing "
          "line left as it is when not strict" % (good, len(cases)))
    return good == len(cases)


def main(argv):
    if argv[1:] == ["selftest"]:
        return 0 if selftest() else 1
    if len(argv) != 4:
        print(__doc__)
        return 2
    root, sub, step = os.path.realpath(argv[1]), argv[2], argv[3]
    raw = text_of(sub, step)
    day, recorded = None, False
    if DATE_PLACEHOLDER in "\n".join(added(raw)):
        day, recorded = run_date(root, sub)

    def dated(strict):
        t = tree_dates(root, sub, step, raw, strict) if DATE_PLACEHOLDER in raw else raw
        return t.replace(DATE_PLACEHOLDER, day) if day else t

    def git(text, *args):
        return subprocess.run(["git", "-C", root, "apply", "--index", *args, "-"],
                              input=text, text=True, capture_output=True)

    if git(dated(False), "--reverse", "--check").returncode == 0:
        print("ALREADY %s step%s" % (sub, step))
        return 0
    text = dated(True)
    r = git(text, "--check")
    if r.returncode == 0:
        r = git(text)
    if r.returncode != 0:
        print("STOP %s step%s: %s" % (sub, step, " | ".join(r.stderr.strip().splitlines()[:6])))
        return 1
    if day and not recorded:
        os.makedirs(os.path.dirname(date_file(root, sub)), exist_ok=True)
        with open(date_file(root, sub), "w", encoding="utf-8") as fh:
            fh.write(day + "\n")
    files = len(re.findall(r"^diff --git ", text, re.M))
    print("APPLY %s step%s: %d file(s)" % (sub, step, files))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
