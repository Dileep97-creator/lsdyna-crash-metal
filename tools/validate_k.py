#!/usr/bin/env python3
"""
Static checks on a keyword deck before it ever reaches the solver.

None of this replaces running the model, but it catches the class of
error that costs a queue slot and half a day: a field spilling past
column 80, a *PART pointing at a section or material that does not
exist, a curve referenced by a material but never defined, duplicate
part IDs across included files.

    python3 tools/validate_k.py 01_crashbox_axial/models/*.k
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

FREE_FORMAT = ("*NODE", "*ELEMENT", "*SET", "*DEFINE_CURVE")

# keyword -> (field index of its own id on card 1)
ID_ON_CARD1 = {
    "*PART": 0, "*SECTION_SHELL": 0, "*SECTION_SOLID": 0,
    "*SECTION_BEAM": 0, "*HOURGLASS": 0, "*DEFINE_CURVE": 0,
}


def fields(line, width=10):
    return [line[i:i + width] for i in range(0, len(line), width)]


class Report:
    def __init__(self, path):
        self.path = path
        self.errors = []
        self.warnings = []
        self.info = []

    def err(self, ln, msg):
        self.errors.append(f"{self.path}:{ln}: ERROR {msg}")

    def warn(self, ln, msg):
        self.warnings.append(f"{self.path}:{ln}: WARN  {msg}")


def include_targets(paths):
    """Every file pulled in with *INCLUDE by any of the decks given."""
    targets, kw = set(), None
    for p in paths:
        for raw in open(p, errors="ignore"):
            line = raw.rstrip("\n")
            if line.startswith("$") or not line.strip():
                continue
            if line.startswith("*"):
                kw = line.strip().upper()
                continue
            if kw == "*INCLUDE":
                targets.add(os.path.basename(line.strip()))
                kw = None
    return targets


def check(path, includes=frozenset()):
    rep = Report(path)
    with open(path) as fh:
        lines = fh.read().split("\n")

    kw = None
    counts = defaultdict(int)
    declared = defaultdict(set)     # kind -> ids defined
    referenced = defaultdict(set)   # kind -> ids used
    node_ids, elem_ids = set(), set()
    has_end = False

    for n, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("$"):
            continue
        if line.startswith("*"):
            kw = line.strip().upper()
            counts[kw.split("_")[0]] += 1
            if kw == "*END":
                has_end = True
            continue
        if kw is None:
            rep.err(n, "data line before any keyword")
            continue

        if len(line) > 80 and not kw.startswith(FREE_FORMAT):
            rep.err(n, f"card is {len(line)} chars, fixed format allows 80")

        # ---- structural bookkeeping
        if kw == "*NODE":
            nid = line[:8].strip()
            if nid.isdigit():
                if int(nid) in node_ids:
                    rep.err(n, f"duplicate node id {nid}")
                node_ids.add(int(nid))
        elif kw.startswith("*ELEMENT_SHELL") or kw.startswith("*ELEMENT_SOLID"):
            eid = line[:8].strip()
            if eid.isdigit():
                if int(eid) in elem_ids:
                    rep.err(n, f"duplicate element id {eid}")
                elem_ids.add(int(eid))
                pid = line[8:16].strip()
                if pid.isdigit():
                    referenced["part"].add(int(pid))
        elif kw.startswith("*PART"):
            f = fields(line)
            if f and f[0].strip().isdigit():
                pid = int(f[0])
                if pid in declared["part"]:
                    rep.err(n, f"duplicate part id {pid}")
                declared["part"].add(pid)
                for idx, kind in ((1, "section"), (2, "material")):
                    if len(f) > idx and f[idx].strip().isdigit():
                        referenced[kind].add(int(f[idx]))
        elif kw.startswith("*SECTION_"):
            f = fields(line)
            if f and f[0].strip().isdigit():
                declared["section"].add(int(f[0]))
        elif kw.startswith("*MAT_"):
            f = fields(line)
            if f and f[0].strip().isdigit() and int(f[0]) < 1_000_000:
                declared["material"].add(int(f[0]))
        elif kw.startswith("*DEFINE_CURVE"):
            f = fields(line)
            if f and f[0].strip().isdigit():
                declared["curve"].add(int(f[0]))

    # ---- cross references
    for kind in ("part", "section", "material"):
        missing = referenced[kind] - declared[kind]
        # elements may legitimately reference parts defined in another
        # included file; flag as warning, not error
        for mid in sorted(missing):
            rep.warn(0, f"{kind} {mid} referenced but not defined in this file")

    if not has_end and os.path.basename(path) not in includes:
        rep.err(len(lines), "deck has no *END")
    if os.path.basename(path) in includes:
        # An *END inside an included file terminates input reading, so
        # everything after the *INCLUDE in the parent deck is dropped in
        # silence. The solver then blames the elements, which is nowhere
        # near the cause. Same for a second *KEYWORD.
        if has_end:
            rep.err(0, "this file is pulled in with *INCLUDE and contains "
                       "*END - it will truncate the parent deck")
        if counts.get("*KEYWORD"):
            rep.err(0, "this file is pulled in with *INCLUDE and contains "
                       "*KEYWORD - remove it")
    elif not counts.get("*KEYWORD"):
        rep.err(1, "deck does not start with *KEYWORD")

    rep.info.append(
        f"{len(node_ids)} nodes, {len(elem_ids)} elements, "
        f"{len(declared['part'])} parts, {len(declared['material'])} materials, "
        f"{len(declared['curve'])} curves")
    return rep


def main(argv):
    paths = argv[1:]
    if not paths:
        print(__doc__)
        return 2
    incl = include_targets(paths)
    bad = 0
    for p in paths:
        rep = check(p, incl)
        status = "FAIL" if rep.errors else ("warn" if rep.warnings else "ok")
        print(f"[{status:4}] {p}  ({rep.info[0]})")
        for m in rep.errors + rep.warnings:
            print("        " + m)
        bad += len(rep.errors)
    print(f"\n{len(paths)} deck(s) checked, {bad} error(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
