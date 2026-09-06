#!/usr/bin/env python3
"""
Crash box performance metrics.

Reduces a run to the four numbers a package engineer actually asks for:

  peak force        sets the load into the structure behind the box, and
                    therefore the pulse the occupant sees
  mean crush force  what the box is worth as an energy absorber
  CFE               mean / peak; a value near 1 means the box crushes at
                    a steady load instead of spiking and then collapsing
  SEA               absorbed energy per kilogram of crushed material,
                    the metric that decides between two designs at equal
                    mass

Input, in order of preference:
  --run DIR         a directory holding glstat and, if present, an
                    exported force-displacement CSV
  --fd file.csv     force vs displacement, two columns
  --glstat file     energy history only; SEA and absorbed energy still
                    work, peak force does not

    python3 postproc.py --run runs/crashbox_t1.5_h5_DP600
    python3 postproc.py --run runs/*  --compare
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from postproc.read_curves import read_glstat, read_csv_curve, get  # noqa: E402

RHO_STEEL = 7.85e-6      # kg/mm^3


def crushed_mass(perimeter, thickness, crush, rho=RHO_STEEL):
    """Mass of the length of tube that actually folded. SEA quoted
    against total part mass instead of crushed mass flatters a design
    that barely crushed, so it is computed against the crushed length."""
    return perimeter * thickness * crush * rho


def metrics(disp=None, force=None, energy=None, perimeter=None,
            thickness=None):
    out = {}
    if disp is not None and force is not None:
        f = np.abs(force)
        out["peak_force_kN"] = float(np.max(f))
        # ignore the contact spike in the first millimetre of travel
        m = disp > max(disp) * 0.02
        out["peak_force_after_spike_kN"] = float(np.max(f[m])) if m.any() else None
        out["crush_mm"] = float(np.max(disp))
        e = float(np.trapezoid(f, disp)) if hasattr(np, "trapezoid") \
            else float(np.trapz(f, disp))
        out["absorbed_J"] = e
        out["mean_force_kN"] = e / max(np.max(disp), 1e-9)
        out["CFE"] = out["mean_force_kN"] / out["peak_force_kN"]
    if energy is not None:
        out["absorbed_J"] = float(energy[-1] - energy[0])
    if (perimeter and thickness and out.get("absorbed_J")
            and out.get("crush_mm")):
        mkg = crushed_mass(perimeter, thickness, out["crush_mm"])
        out["crushed_mass_kg"] = mkg
        out["SEA_J_per_kg"] = out["absorbed_J"] / mkg
    return out


def load_run(d):
    """Pick up whatever the run directory happens to contain."""
    res = dict(name=os.path.basename(d.rstrip("/")))
    fd = (glob.glob(os.path.join(d, "*force*disp*.csv"))
          + glob.glob(os.path.join(d, "fd.csv")))
    if fd:
        x, y = read_csv_curve(fd[0])
        res["disp"], res["force"] = x, y
    g = os.path.join(d, "glstat")
    if os.path.exists(g):
        c = read_glstat(g)
        res["energy"] = get(c, "internal energy")
        res["time"] = get(c, "time")
        res["ke"] = get(c, "kinetic energy")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", nargs="*", default=[])
    ap.add_argument("--fd")
    ap.add_argument("--glstat")
    ap.add_argument("--perimeter", type=float, default=310.0,
                    help="tube section perimeter [mm], default matches build.py")
    ap.add_argument("--thickness", type=float, default=1.5)
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--plot", default="results/crush_comparison.png")
    a = ap.parse_args()

    runs = []
    for d in a.run:
        runs.append(load_run(d))
    if a.fd or a.glstat:
        r = dict(name="single")
        if a.fd:
            r["disp"], r["force"] = read_csv_curve(a.fd)
        if a.glstat:
            c = read_glstat(a.glstat)
            r["energy"], r["time"] = get(c, "internal energy"), get(c, "time")
        runs.append(r)
    if not runs:
        ap.error("give --run, --fd or --glstat")

    rows = []
    for r in runs:
        m = metrics(r.get("disp"), r.get("force"), r.get("energy"),
                    a.perimeter, a.thickness)
        rows.append((r["name"], m))
        print(f"\n{r['name']}")
        for k, v in m.items():
            if v is None:
                continue
            print(f"  {k:<28} {v:12.4g}")

    if a.compare and len(rows) > 1:
        keys = ["peak_force_kN", "mean_force_kN", "CFE", "absorbed_J",
                "SEA_J_per_kg"]
        print("\n" + "-" * 96)
        print(f"{'run':<38}" + "".join(f"{k:>14}" for k in keys))
        print("-" * 96)
        for name, m in rows:
            print(f"{name:<38}" + "".join(
                f"{m.get(k):>14.4g}" if isinstance(m.get(k), float)
                else f"{'-':>14}" for k in keys))

    plotted = [r for r in runs if "disp" in r]
    if plotted:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            os.makedirs(os.path.dirname(a.plot) or ".", exist_ok=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
            for r in plotted:
                ax1.plot(r["disp"], np.abs(r["force"]), lw=1.4, label=r["name"])
                e = np.cumsum(np.abs(r["force"])[:-1] * np.diff(r["disp"]))
                ax2.plot(r["disp"][1:], e, lw=1.4, label=r["name"])
            ax1.set_xlabel("crush [mm]")
            ax1.set_ylabel("contact force [kN]")
            ax1.set_title("Crush response")
            ax2.set_xlabel("crush [mm]")
            ax2.set_ylabel("absorbed energy [J]")
            ax2.set_title("Energy absorption")
            for ax in (ax1, ax2):
                ax.grid(alpha=0.3)
                ax.legend(fontsize=8)
            fig.tight_layout()
            fig.savefig(a.plot, dpi=150)
            print(f"\nplot written to {a.plot}")
        except ImportError:
            pass


if __name__ == "__main__":
    main()
