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
    # exact key first: "time" must not resolve to "time step", nor
    # "internal energy" to "eroded internal energy" - the keys come out of
    # a set, so a substring-only match returns a different channel from
    # one run to the next
    for c in candidates:
        if c in curves:
            return curves[c]
    for c in candidates:
        for k in sorted(curves, key=len):
            if k.startswith(c):
                return curves[k]
    for c in candidates:
        for k in sorted(curves, key=len):
            if c in k:
                return curves[k]
    return None


# ----------------------------------------------------------------------
# ASCII readers for the l2a / ascii-output files. These are what the
# crash box results were actually extracted from, so they are tested
# against R16 output rather than written from the manual.
# ----------------------------------------------------------------------
_E = r"(-?\d+\.\d+E[+-]\d+)"


def read_rcforc(path, contact_id, side="SURFB"):
    """Resultant contact force history for one interface.

    Returns (time, fx, fy, fz). SURFB is the master/segment side of a
    two-surface contact; single-surface contacts have no resultants and
    are skipped by the solver itself ("resultants are undefined")."""
    pat = re.compile(rf"^\s*{side}\s+(\d+)\s+time\s+{_E}\s+x\s+{_E}\s+y\s+{_E}\s+z\s+{_E}")
    rows = []
    with open(path, errors="ignore") as fh:
        for line in fh:
            m = pat.match(line)
            if m and int(m.group(1)) == contact_id:
                rows.append([float(m.group(i)) for i in range(2, 6)])
    if not rows:
        raise KeyError(f"contact {contact_id} ({side}) not found in {path}")
    a = np.array(rows)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]


def read_nodout(path, node_id):
    """Translational history of one node from ASCII nodout.

    Returns dict of arrays: time, x/y/z_disp, x/y/z_vel, x/y/z_accl.
    Fixed-width 12-character fields, because negative numbers run into
    each other ("0.00000E+00-5.98449E-01") and a whitespace split fails."""
    names = ["x_disp", "y_disp", "z_disp", "x_vel", "y_vel", "z_vel",
             "x_accl", "y_accl", "z_accl"]
    out = {k: [] for k in ["time"] + names}
    t, trans = None, False
    tpat = re.compile(r"at time\s+(\S+)\s*\)")
    with open(path, errors="ignore") as fh:
        for line in fh:
            m = tpat.search(line)
            if m:
                t = float(m.group(1))
                continue
            if "x-disp" in line:
                trans = True
                continue
            if "x-rot" in line:
                trans = False
                continue
            if trans and line[:10].strip().isdigit() and int(line[:10]) == node_id:
                s = line[10:]
                vals = [float(s[i:i + 12]) for i in range(0, 108, 12)]
                out["time"].append(t)
                for k, v in zip(names, vals):
                    out[k].append(v)
                trans = False
    if not out["time"]:
        raise KeyError(f"node {node_id} not found in {path}")
    return {k: np.array(v) for k, v in out.items()}


def read_matsum(path, mid):
    """Internal, kinetic and hourglass energy of one part from ASCII matsum."""
    t, ie, ke, hg = [], [], [], []
    cur, want = None, False
    with open(path, errors="ignore") as fh:
        for line in fh:
            m = re.match(r"\s*time =\s+(\S+)", line)
            if m:
                cur = float(m.group(1))
                continue
            m = re.match(r"\s*mat\.#=\s+(\d+)\s+inten=\s+(\S+)\s+kinen=\s+(\S+)", line)
            if m:
                want = int(m.group(1)) == mid
                if want:
                    t.append(cur)
                    ie.append(float(m.group(2)))
                    ke.append(float(m.group(3)))
                continue
            m = re.search(r"hgeng=\s+(\S+)", line)
            if m and want:
                hg.append(float(m.group(1)))
                want = False
    return dict(time=np.array(t), internal=np.array(ie),
                kinetic=np.array(ke), hourglass=np.array(hg))


def sae_cfc_filter(t_ms, y, cfc):
    """SAE J211 channel frequency class filter, forward and backward pass
    (zero phase). Time in ms. CFC 600 for force, CFC 60 for acceleration
    pulses, as in the usual crash test evaluation."""
    t_ms = np.asarray(t_ms, float)
    y = np.asarray(y, float)
    if len(y) < 4:
        return t_ms, y
    T = float(np.median(np.diff(t_ms))) / 1000.0
    wd = 2.0 * np.pi * cfc * 2.0775
    wa = np.tan(wd * T / 2.0)
    den = 1.0 + np.sqrt(2.0) * wa + wa ** 2
    a0 = wa ** 2 / den
    a1, a2 = 2.0 * a0, a0
    b1 = -2.0 * (wa ** 2 - 1.0) / den
    b2 = (-1.0 + np.sqrt(2.0) * wa - wa ** 2) / den

    def one_pass(x):
        o = np.array(x, float)
        for i in range(2, len(x)):
            o[i] = (a0 * x[i] + a1 * x[i - 1] + a2 * x[i - 2]
                    + b1 * o[i - 1] + b2 * o[i - 2])
        return o

    return t_ms, one_pass(one_pass(y)[::-1])[::-1]


def rcforc_component(path, contact_id):
    """|F| of one contact from an ASCII rcforc - convenience wrapper."""
    t, fx, fy, fz = read_rcforc(path, contact_id)
    return t, np.sqrt(fx ** 2 + fy ** 2 + fz ** 2)


def read_binout_branch(path, branch):
    """Every channel of one binout branch, via lasso-python."""
    try:
        from lasso.dyna import Binout
    except ImportError as exc:
        raise ImportError("lasso-python is not installed; convert with l2a "
                          "and use the ASCII readers instead") from exc
    b = Binout(path)
    return {name: np.asarray(b.read(branch, name)) for name in b.read(branch)}
