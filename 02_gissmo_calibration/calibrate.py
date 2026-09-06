#!/usr/bin/env python3
"""
Fit a GISSMO failure locus from coupon results and emit the material
card that goes into the crash model.

Inputs  : data/coupon_results.csv
Outputs : results/gissmo_<grade>.k        include-ready material card
          results/failure_locus.png       fit vs. data
          results/regularisation.png      element size dependence
          results/fit_report.txt

The workflow this automates:

  1. Each coupon is pulled in the simulation until the extensometer
     displacement matches the displacement at fracture measured on the
     test rig.
  2. At that instant, read the effective plastic strain and the stress
     triaxiality of the critical element. That is one point on the
     failure locus.
  3. Repeat for every stress state - the five coupons in build.py span
     shear through plane strain.
  4. Fit a smooth locus through the points and tabulate it as LCSDG.
  5. Repeat the whole thing at several element sizes. Failure strain in
     a shell model is mesh dependent, so a locus fitted on a 0.5 mm
     coupon mesh will predict fracture far too late on a 5 mm crash
     mesh. The ratio of failure strain at size h to failure strain at
     the reference size becomes the LCREGD regularisation curve.

Step 5 is the one that is usually skipped, and it is the reason a
"calibrated" damage card so often fails to transfer to the full vehicle
model.

    python3 calibrate.py
    python3 calibrate.py --refsize 2.0 --target-size 5.0
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from kfile import Deck   # noqa: E402
import materials as mat  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "coupon_results.csv")
OUT = os.path.join(HERE, "results")

LCSDG, LCREGD = 900, 901
MID = 1


# ------------------------------------------------------------------ model
def jc_locus(eta, d1, d2, d3):
    """Johnson-Cook style failure locus. Monotonically decreasing with
    triaxiality, which is the right behaviour on the tensile branch."""
    return d1 + d2 * np.exp(-d3 * eta)


def fit_locus(eta, epsf):
    """Least squares fit of the three-parameter locus.

    scipy is used when available; the fallback is a coarse grid on the
    one non-linear parameter with a closed-form linear solve for the
    other two, which is robust and needs no dependencies.
    """
    try:
        from scipy.optimize import curve_fit
        p0 = [min(epsf) * 0.5, max(epsf), 1.5]
        # d1 is bounded away from zero so the locus stays positive when
        # LS-DYNA samples triaxialities beyond the calibrated range
        popt, _ = curve_fit(jc_locus, eta, epsf, p0=p0, maxfev=20000,
                            bounds=([0.02, 0.0, 0.1], [2.0, 20.0, 10.0]))
        return tuple(popt), "scipy.curve_fit"
    except Exception:
        best, bestp = np.inf, None
        for d3 in np.linspace(0.2, 6.0, 300):
            A = np.vstack([np.ones_like(eta), np.exp(-d3 * eta)]).T
            sol, *_ = np.linalg.lstsq(A, epsf, rcond=None)
            sol = np.array([max(sol[0], 0.02), max(sol[1], 0.0)])
            r = float(np.sum((A @ sol - epsf) ** 2))
            if r < best:
                best, bestp = r, (sol[0], sol[1], d3)
        return bestp, "grid + linear least squares"


def regularisation(sizes, epsf, refsize):
    """Failure strain normalised by its value at the reference element
    size, fitted as a power law so it can be evaluated at any mesh size."""
    sizes = np.asarray(sizes, float)
    epsf = np.asarray(epsf, float)
    ref = np.interp(refsize, sizes, epsf)
    ratio = epsf / ref
    # log-log linear fit -> ratio = (h/href)^-m
    m, c = np.polyfit(np.log(sizes / refsize), np.log(ratio), 1)
    return ref, float(m), float(np.exp(c))


# ------------------------------------------------------------------ io
def load(path):
    rows = []
    with open(path) as fh:
        # tolerate a leading comment block so the file can document itself
        body = [ln for ln in fh if not ln.lstrip().startswith("#")]
        for r in csv.DictReader(body):
            if not r.get("specimen") or r["specimen"].startswith("#"):
                continue
            rows.append(dict(specimen=r["specimen"].strip(),
                             h=float(r["element_size_mm"]),
                             eta=float(r["triaxiality"]),
                             epsf=float(r["failure_plastic_strain"]),
                             src=r.get("source", "").strip()))
    if not rows:
        raise SystemExit(f"no usable rows in {path}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=DATA)
    ap.add_argument("--grade", default="DP600")
    ap.add_argument("--refsize", type=float, default=1.0,
                    help="element size the locus is fitted at [mm]")
    ap.add_argument("--target-size", type=float, default=5.0,
                    help="crash model element size to report the scaling for")
    ap.add_argument("--dcrit", type=float, default=0.35)
    ap.add_argument("--dmgexp", type=float, default=2.0)
    ap.add_argument("--fadexp", type=float, default=1.0)
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    rows = load(args.csv)

    # ---- locus at the reference element size
    ref_rows = [r for r in rows if abs(r["h"] - args.refsize) < 1e-9]
    if len(ref_rows) < 3:
        raise SystemExit(f"need at least 3 coupons at h={args.refsize} mm")
    eta = np.array([r["eta"] for r in ref_rows])
    epsf = np.array([r["epsf"] for r in ref_rows])
    order = np.argsort(eta)
    eta, epsf = eta[order], epsf[order]
    (d1, d2, d3), method = fit_locus(eta, epsf)

    pred = jc_locus(eta, d1, d2, d3)
    rms = float(np.sqrt(np.mean((pred - epsf) ** 2)))
    worst = float(np.max(np.abs(pred - epsf) / epsf) * 100.0)

    # tabulate the locus over the range LS-DYNA will actually sample
    eta_tab = np.concatenate([
        np.linspace(-0.6667, 0.0, 5, endpoint=False),
        np.linspace(0.0, 0.6667, 12, endpoint=False),
        np.linspace(0.6667, 1.5, 5)])
    epsf_tab = np.clip(jc_locus(eta_tab, d1, d2, d3), 0.02, 5.0)

    # ---- mesh regularisation from the element size sweep
    reg = {}
    by_spec = {}
    for r in rows:
        by_spec.setdefault(r["specimen"], []).append(r)
    sizes = sorted({r["h"] for r in rows})
    if len(sizes) >= 2:
        # average the normalised trend over all specimens that were run
        # at every size, so the curve is not biased by one stress state
        ratios = []
        for spec, rs in by_spec.items():
            hs = sorted(rs, key=lambda r: r["h"])
            if len(hs) != len(sizes):
                continue
            e = np.array([r["epsf"] for r in hs])
            h = np.array([r["h"] for r in hs])
            ratios.append(e / np.interp(args.refsize, h, e))
        if ratios:
            mean_ratio = np.mean(np.vstack(ratios), axis=0)
            m, c = np.polyfit(np.log(np.array(sizes) / args.refsize),
                              np.log(mean_ratio), 1)
            reg = dict(sizes=sizes, ratio=mean_ratio.tolist(),
                       exponent=float(m), scale=float(np.exp(c)))

    # ---- write the material card
    grade = args.grade
    d = Deck(f"GISSMO damage card for {grade}, fitted at h={args.refsize:g} mm")
    d.note(
        f"generated by 02_gissmo_calibration/calibrate.py from {os.path.basename(args.csv)}\n"
        f"locus  eps_f(eta) = {d1:.4f} + {d2:.4f} * exp(-{d3:.4f} * eta)\n"
        f"fit    RMS {rms:.4f} strain, worst point {worst:.1f}%  [{method}]\n"
        f"include this file next to the *MAT_ card for material {MID}")
    d.define_curve(LCSDG, list(zip(eta_tab, epsf_tab)),
                   title="LCSDG failure plastic strain vs triaxiality")
    if reg:
        hs = np.linspace(min(reg["sizes"]) * 0.5, 10.0, 20)
        rr = reg["scale"] * (hs / args.refsize) ** reg["exponent"]
        d.define_curve(LCREGD, list(zip(hs, rr)),
                       title="LCREGD mesh regularisation factor vs element size")
    mat.add_gissmo(d, MID, LCSDG, dmgexp=args.dmgexp, dcrit=args.dcrit,
                   fadexp=args.fadexp, lcregd=LCREGD if reg else 0)
    kpath = os.path.join(OUT, f"gissmo_{grade.lower()}.k")
    d.write(kpath)

    # ---- report
    lines = [
        f"GISSMO calibration report - {grade}",
        "=" * 52,
        f"input                {os.path.relpath(args.csv, HERE)}",
        f"coupons at h={args.refsize:g} mm  " +
        ", ".join(r["specimen"] for r in ref_rows),
        f"fit method           {method}",
        f"locus                eps_f = {d1:.4f} + {d2:.4f}*exp(-{d3:.4f}*eta)",
        f"RMS error            {rms:.4f} plastic strain",
        f"worst point error    {worst:.1f} %",
        "",
        "failure strain at the standard stress states",
    ]
    for label, e in (("pure shear", 0.0), ("uniaxial tension", 1 / 3),
                     ("plane strain", 0.5774), ("equibiaxial", 2 / 3)):
        lines.append(f"  {label:<20s} eta={e:6.3f}   eps_f={jc_locus(e, d1, d2, d3):.3f}")
    if reg:
        f_target = reg["scale"] * (args.target_size / args.refsize) ** reg["exponent"]
        lines += [
            "",
            f"mesh regularisation  ratio = {reg['scale']:.3f} * (h/{args.refsize:g})^{reg['exponent']:.3f}",
            f"  at h={args.target_size:g} mm the failure strain scales by {f_target:.3f}",
            "  -> a locus fitted on the coupon mesh and used unscaled on the",
            f"     crash mesh would over-predict ductility by {(1/f_target - 1)*100:.0f} %",
        ]
    else:
        lines += ["", "mesh regularisation  not enough element sizes in the data"]
    lines += ["", f"material card written to {os.path.relpath(kpath, HERE)}"]
    report = "\n".join(lines)
    with open(os.path.join(OUT, "fit_report.txt"), "w") as fh:
        fh.write(report + "\n")
    print(report)

    # ---- plots
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6.4, 4.2))
        xs = np.linspace(-0.6, 1.2, 300)
        ax.plot(xs, jc_locus(xs, d1, d2, d3), "-", lw=2, label="fitted locus")
        ax.plot(eta, epsf, "o", ms=7, label=f"coupons, h={args.refsize:g} mm")
        for r in ref_rows:
            ax.annotate(r["specimen"], (r["eta"], r["epsf"]),
                        textcoords="offset points", xytext=(6, 6), fontsize=8)
        for e, lab in ((0.0, "shear"), (1 / 3, "uniaxial"), (0.5774, "plane strain")):
            ax.axvline(e, color="0.85", lw=1, zorder=0)
        ax.set_xlabel("stress triaxiality  $\\eta = \\sigma_m/\\sigma_{vm}$")
        ax.set_ylabel("failure plastic strain")
        ax.set_title(f"GISSMO failure locus - {grade}")
        ax.grid(alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, "failure_locus.png"), dpi=150)

        if reg:
            fig, ax = plt.subplots(figsize=(6.0, 4.0))
            ax.plot(reg["sizes"], reg["ratio"], "o", label="coupon sweep")
            hs = np.linspace(min(reg["sizes"]) * 0.5, 8.0, 100)
            ax.plot(hs, reg["scale"] * (hs / args.refsize) ** reg["exponent"],
                    "-", label="power law fit")
            ax.axhline(1.0, color="0.7", lw=1)
            ax.set_xlabel("element size [mm]")
            ax.set_ylabel(f"failure strain / value at {args.refsize:g} mm")
            ax.set_title("GISSMO mesh regularisation")
            ax.grid(alpha=0.3)
            ax.legend()
            fig.tight_layout()
            fig.savefig(os.path.join(OUT, "regularisation.png"), dpi=150)
        print(f"\nplots written to {os.path.relpath(OUT, HERE)}/")
    except ImportError:
        print("\nmatplotlib not installed - skipped plots")


if __name__ == "__main__":
    main()
