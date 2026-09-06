#!/usr/bin/env python3
"""
Springback evaluation for the U-channel.

Reads the blank geometry before and after release and reports the three
benchmark quantities:

  theta1   flange angle, between the flange and the punch face
  theta2   sidewall angle, between the sidewall and the punch face
  rho      sidewall curl radius, from a circle fit to the sidewall

theta1 and theta2 are what a die face compensation loop is driven by;
rho is the one that is hardest to predict and the one most sensitive to
the number of through-thickness integration points and to the hardening
model. Reporting all three, rather than just an opening angle, is what
makes a springback study comparable to published data.

Geometry comes straight from the dynain files, so no LS-PrePost session
and no manual node picking is involved.

    python3 postproc_springback.py --formed run/dynain_formed \\
                                   --released run/dynain_sprung
"""

from __future__ import annotations

import argparse
import math
import os

import numpy as np


def read_nodes(path):
    """Pull *NODE out of a keyword or dynain file."""
    nodes = {}
    kw = None
    for raw in open(path, errors="ignore"):
        line = raw.rstrip("\n")
        if not line.strip() or line.startswith("$"):
            continue
        if line.startswith("*"):
            kw = line.strip().upper()
            continue
        if kw == "*NODE":
            try:
                nid = int(line[0:8])
                nodes[nid] = (float(line[8:24]), float(line[24:40]),
                              float(line[40:56]))
            except ValueError:
                continue
    if not nodes:
        raise SystemExit(f"no *NODE data found in {path}")
    return nodes


def centreline(nodes, tol=1.5):
    """Nodes on the strip centreline, sorted along the section."""
    pts = [(x, z) for (x, y, z) in nodes.values() if abs(y) < tol]
    if len(pts) < 20:
        raise SystemExit("centreline extraction found too few nodes - "
                         "increase --tol or check the model width")
    pts.sort()
    return np.array(pts)


def fit_line_angle(seg, reference="horizontal"):
    """Angle of a least-squares line through seg, in degrees."""
    x, z = seg[:, 0], seg[:, 1]
    if np.ptp(x) >= np.ptp(z):
        m = np.polyfit(x, z, 1)[0]
        ang = math.degrees(math.atan(m))
    else:
        m = np.polyfit(z, x, 1)[0]
        ang = 90.0 - math.degrees(math.atan(m))
    return ang if reference == "horizontal" else 90.0 - ang


def fit_circle(seg):
    """Algebraic circle fit (Kasa). Returns centre and radius."""
    x, z = seg[:, 0], seg[:, 1]
    A = np.c_[2 * x, 2 * z, np.ones(len(x))]
    b = x ** 2 + z ** 2
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cz, c = sol
    r = math.sqrt(max(c + cx ** 2 + cz ** 2, 0.0))
    return cx, cz, r


def split_regions(pts, punch_half=25.0, die_r=5.0):
    """Split the half section into punch face, sidewall and flange by
    where the geometry actually turns, not by fixed node numbers - the
    node that sits on the sidewall changes as the blank draws in."""
    right = pts[pts[:, 0] > 0]
    right = right[np.argsort(right[:, 0])]
    if len(right) < 15:
        raise SystemExit("too few points on the right half of the section")

    z = right[:, 1]
    x = right[:, 0]
    z_span = np.ptp(z)
    # punch face: the flat low region near the centre
    face = right[(x < punch_half * 0.7)]
    # flange: the flat high region at the outer end
    flange = right[z > z.min() + 0.85 * z_span] if z_span > 5 else right[-10:]
    # sidewall: what is left in the middle third of the height
    lo, hi = z.min() + 0.25 * z_span, z.min() + 0.75 * z_span
    wall = right[(z > lo) & (z < hi)]
    if len(wall) < 6:
        wall = right[len(right) // 3: 2 * len(right) // 3]
    return face, wall, flange


def evaluate(path, punch_half, die_r, tol):
    nodes = read_nodes(path)
    pts = centreline(nodes, tol)
    face, wall, flange = split_regions(pts, punch_half, die_r)
    theta1 = fit_line_angle(flange)
    theta2 = fit_line_angle(wall, reference="vertical")
    cx, cz, rho = fit_circle(wall)
    return dict(theta1=theta1, theta2=theta2, rho=rho,
                n_wall=len(wall), n_flange=len(flange), pts=pts,
                wall=wall, flange=flange)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--formed", required=True,
                    help="dynain written at the end of the forming run")
    ap.add_argument("--released", required=True,
                    help="dynain written at the end of the springback run")
    ap.add_argument("--punch-half", type=float, default=25.0)
    ap.add_argument("--die-r", type=float, default=5.0)
    ap.add_argument("--tol", type=float, default=1.5)
    ap.add_argument("--plot", default="results/springback_section.png")
    a = ap.parse_args()

    f = evaluate(a.formed, a.punch_half, a.die_r, a.tol)
    s = evaluate(a.released, a.punch_half, a.die_r, a.tol)

    print("U-channel springback evaluation")
    print("=" * 54)
    print(f"{'quantity':<26}{'formed':>10}{'released':>11}{'change':>10}")
    for key, label, unit in (("theta1", "flange angle", "deg"),
                             ("theta2", "sidewall angle", "deg"),
                             ("rho", "sidewall curl radius", "mm")):
        print(f"{label+' ['+unit+']':<26}{f[key]:>10.2f}{s[key]:>11.2f}"
              f"{s[key]-f[key]:>10.2f}")
    print(f"\ncentreline nodes: {len(f['pts'])} formed, {len(s['pts'])} released")
    print(f"sidewall fit used {f['n_wall']} / {s['n_wall']} points")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        os.makedirs(os.path.dirname(a.plot) or ".", exist_ok=True)
        fig, ax = plt.subplots(figsize=(7.2, 4.6))
        ax.plot(f["pts"][:, 0], f["pts"][:, 1], ".", ms=3,
                label="after forming")
        ax.plot(s["pts"][:, 0], s["pts"][:, 1], ".", ms=3,
                label="after springback")
        ax.set_xlabel("x [mm]")
        ax.set_ylabel("z [mm]")
        ax.set_title("U-channel section, centreline")
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(a.plot, dpi=150)
        print(f"\nplot written to {a.plot}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
