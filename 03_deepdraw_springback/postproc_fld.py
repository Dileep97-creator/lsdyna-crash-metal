#!/usr/bin/env python3
"""
Forming limit evaluation.

Takes major/minor principal surface strains exported from LS-PrePost
(Fringe > strain > in-plane principal, then export element data to CSV)
and classifies every element against a forming limit curve.

The FLC is built from the Keeler-Brazier relation, which puts FLC0 - the
limit strain in plane strain - as a function of sheet thickness and
strain hardening exponent n, and then uses the standard left and right
branch shapes. It is a design-stage estimate, not a substitute for a
measured Nakajima curve, and the script says so in its output.

Elements are binned the way a forming report bins them:

  crack       above the FLC
  risk        within the safety margin below the FLC
  safe        below that
  thinning    thinning beyond the allowable, checked separately because
              a panel can pass the FLC and still be rejected on thinning
  wrinkle     strongly negative minor strain, compression risk

    python3 postproc_fld.py --strains run/strains.csv --t 0.8 --n 0.23
"""

from __future__ import annotations

import argparse
import os

import numpy as np


def flc0_keeler(t_mm, n, n_ref=0.21):
    """FLC0 in true strain. Keeler-Brazier, with the usual cap that the
    thickness term stops helping above about 3 mm."""
    t = min(t_mm, 3.0)
    fl0_eng = (23.3 + 14.13 * t) * (n / n_ref) / 100.0
    return np.log(1.0 + fl0_eng)


def flc_curve(flc0, minor):
    """Left and right branches around plane strain, in true strain."""
    minor = np.asarray(minor, float)
    left = flc0 + (-minor) * 0.78          # drawing side, slope ~0.78
    right = flc0 + minor * 0.55            # stretching side, slope ~0.55
    return np.where(minor < 0, left, right)


def classify(minor, major, flc0, margin=0.10, thin_limit=0.20,
             wrinkle_limit=-0.02):
    lim = flc_curve(flc0, minor)
    thinning = -(minor + major)            # volume constancy, true strains
    out = np.full(len(minor), "safe", dtype=object)
    out[(minor < wrinkle_limit) & (major < 0.02)] = "wrinkle"
    out[thinning > thin_limit] = "thinning"
    out[major > lim * (1.0 - margin)] = "risk"
    out[major > lim] = "crack"
    return out, lim, thinning


def read_strains(path):
    rows = []
    for line in open(path, errors="ignore"):
        s = line.strip()
        if not s or s[0] in "#$" or not (s[0].isdigit() or s[0] == "-"):
            continue
        parts = [p for p in s.replace(",", " ").split() if p]
        try:
            vals = [float(p) for p in parts]
        except ValueError:
            continue
        if len(vals) >= 2:
            rows.append(vals[-2:])       # last two columns: minor, major
    if not rows:
        raise SystemExit(f"no numeric strain rows found in {path}")
    a = np.array(rows)
    return a[:, 0], a[:, 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strains", required=True,
                    help="CSV with minor and major true strain in the last "
                         "two columns")
    ap.add_argument("--t", type=float, default=0.8, help="thickness [mm]")
    ap.add_argument("--n", type=float, default=0.23, help="hardening exponent")
    ap.add_argument("--margin", type=float, default=0.10)
    ap.add_argument("--thin-limit", type=float, default=0.20)
    ap.add_argument("--plot", default="results/fld.png")
    a = ap.parse_args()

    minor, major = read_strains(a.strains)
    flc0 = flc0_keeler(a.t, a.n)
    cls, lim, thinning = classify(minor, major, flc0, a.margin, a.thin_limit)

    print("Forming limit evaluation")
    print("=" * 46)
    print(f"  thickness            {a.t:g} mm")
    print(f"  hardening exponent   {a.n:g}")
    print(f"  FLC0 (true strain)   {flc0:.3f}")
    print(f"  safety margin        {a.margin*100:g} %")
    print(f"  elements evaluated   {len(minor)}")
    print()
    for k in ("crack", "risk", "thinning", "wrinkle", "safe"):
        n = int(np.sum(cls == k))
        print(f"  {k:<10} {n:>7}   {n/len(cls)*100:6.2f} %")
    print(f"\n  max thinning         {np.max(thinning)*100:.1f} %")
    print(f"  worst utilisation    {np.max(major/np.maximum(lim,1e-6)):.3f}"
          "   (>1 means past the FLC)")
    print("\n  The FLC here is a Keeler-Brazier estimate. For a release")
    print("  decision, replace it with the measured curve for the coil.")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        os.makedirs(os.path.dirname(a.plot) or ".", exist_ok=True)
        colors = dict(safe="#2a9d4a", risk="#e8a33d", crack="#c9433a",
                      thinning="#7b52c9", wrinkle="#3d7ec9")
        fig, ax = plt.subplots(figsize=(6.4, 5.4))
        xs = np.linspace(-0.5, 0.5, 400)
        ax.plot(xs, flc_curve(flc0, xs), "k-", lw=2, label="FLC")
        ax.plot(xs, flc_curve(flc0, xs) * (1 - a.margin), "k--", lw=1,
                label=f"FLC - {a.margin*100:g}%")
        for k in ("safe", "risk", "wrinkle", "thinning", "crack"):
            m = cls == k
            if m.any():
                ax.plot(minor[m], major[m], ".", ms=3, color=colors[k],
                        label=f"{k} ({int(m.sum())})")
        ax.set_xlabel("minor true strain")
        ax.set_ylabel("major true strain")
        ax.set_title("Forming limit diagram")
        ax.set_xlim(-0.5, 0.5)
        ax.set_ylim(0, max(0.8, float(np.max(major)) * 1.1))
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(a.plot, dpi=150)
        print(f"\nplot written to {a.plot}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
