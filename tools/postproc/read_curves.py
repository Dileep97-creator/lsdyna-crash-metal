"""
Readers for LS-DYNA results.

Three routes are supported, in order of preference:

  1. binout, through lasso-python if it is installed. Best option -
     everything is in one place and nothing is lost to text rounding.
  2. the ASCII files produced by l2a (glstat, matsum, rcforc, ...).
     glstat is parsed properly here because it is what the energy
     balance check needs and its layout is stable across releases.
  3. two-column CSV exported from LS-PrePost. Always available, and the
     format everyone can produce without extra packages.

Nothing here assumes a particular solver version: if a key is missing
the caller gets None rather than an exception, so a QA script degrades
to a partial report instead of failing outright.
"""

from __future__ import annotations

import csv
import re

import numpy as np

# "  kinetic energy...............  5.6250E+04"
_KV = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /%().\-']*?)\s*\.{2,}\s*"
                 r"(-?\d+\.?\d*(?:[EeDd][+-]?\d+)?)\s*$")
# "  total energy         =  5.6373E+04"
_KV_EQ = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /%().\-']*?)\s*=\s*"
                    r"(-?\d+\.?\d*(?:[EeDd][+-]?\d+)?)\s*$")


def _num(s):
    return float(s.replace("D", "E").replace("d", "e"))


def read_glstat(path):
    """Parse an ASCII glstat into {label: np.array}.

    A new time record is detected by the reappearance of the time key,
    which is how the file is actually structured - blocks of key/value
    lines, one block per output interval.
    """
    records, cur = [], {}
    with open(path, errors="ignore") as fh:
        for line in fh:
            m = _KV.match(line) or _KV_EQ.match(line)
            if not m:
                continue
            key = " ".join(m.group(1).split()).lower()
            val = _num(m.group(2))
            if key.startswith("time") and key in cur:
                records.append(cur)
                cur = {}
            cur[key] = val
    if cur:
        records.append(cur)
    if not records:
        raise ValueError(f"no key/value records found in {path}")

    keys = set()
    for r in records:
        keys |= set(r)
    out = {}
    for k in keys:
        out[k] = np.array([r.get(k, np.nan) for r in records], float)
    return out


def read_binout(path, branch="glstat"):
    """Read a branch of binout using lasso-python, if available."""
    try:
        from lasso.dyna import Binout
    except ImportError as exc:
        raise ImportError(
            "lasso-python is not installed; run `pip install lasso-python` "
            "or convert with l2a and use read_glstat instead") from exc
    b = Binout(path)
    return {name: np.asarray(b.read(branch, name))
            for name in b.read(branch)
            if not isinstance(b.read(branch, name), (str, bytes))}


def read_csv_curve(path, xcol=0, ycol=1):
    """Two-column curve exported from LS-PrePost. Comment lines starting
    with # or $ and any non-numeric header are skipped."""
    xs, ys = [], []
    with open(path, errors="ignore") as fh:
        for row in csv.reader(fh):
            if not row or row[0].lstrip().startswith(("#", "$")):
                continue
            try:
                xs.append(float(row[xcol]))
                ys.append(float(row[ycol]))
            except (ValueError, IndexError):
                continue
    if not xs:
        raise ValueError(f"no numeric rows in {path}")
    return np.array(xs), np.array(ys)


def get(curves, *candidates):
    """First matching key, tolerating wording differences between
    solver releases. Returns None when nothing matches."""
    for c in candidates:
        for k in curves:
            if c in k:
                return curves[k]
    return None
