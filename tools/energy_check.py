#!/usr/bin/env python3
"""
Energy balance acceptance check for an explicit run.

A crash result is not trustworthy because the animation looks plausible.
It is trustworthy when the energy bookkeeping closes. These are the
checks every OEM deck guideline asks for, in one place, with a pass/fail
exit code so they can run in CI rather than being remembered by hand:

  total energy drift      |E_total/E_initial - 1| < 1 %
  hourglass energy        HG / internal energy  < 5 %
  added mass              added mass / model mass < 5 %
  sliding energy          |E_sliding| / internal energy < 10 %
                          and not strongly negative
  eroded energy           reported, so silent element deletion is visible

Thresholds are the usual defaults and can be overridden.

    python3 tools/energy_check.py run/glstat
    python3 tools/energy_check.py run/binout --hg-limit 0.03
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from postproc.read_curves import read_glstat, read_binout, get  # noqa: E402


def load(path):
    if os.path.basename(path).startswith("binout"):
        return read_binout(path, "glstat")
    return read_glstat(path)


def check(path, drift=0.01, hg=0.05, mass=0.05, slide=0.10):
    c = load(path)
    t = get(c, "time")
    ie = get(c, "internal energy")
    ke = get(c, "kinetic energy")
    te = get(c, "total energy")
    ratio = get(c, "energy ratio")
    hgE = get(c, "hourglass energy")
    slE = get(c, "sliding interface energy", "sliding energy")
    erE = get(c, "eroded internal energy", "eroded kinetic energy")
    dm = get(c, "percent increase", "added mass")

    results, fails = [], 0

    def line(name, value, limit, ok, unit=""):
        nonlocal fails
        if value is None:
            results.append(f"  {name:<26} not in file")
            return
        status = "PASS" if ok else "FAIL"
        if not ok:
            fails += 1
        lim = f"limit {limit}" if limit is not None else ""
        results.append(f"  {name:<26} {value:>10.4g}{unit:<4} {status:>6}   {lim}")

    if ratio is not None:
        d = float(np.max(np.abs(ratio - 1.0)))
    elif te is not None and len(te):
        d = float(np.max(np.abs(te / te[0] - 1.0))) if te[0] else None
    else:
        d = None
    line("total energy drift", None if d is None else d * 100,
         f"{drift*100:g} %", d is not None and d < drift, " %")

    if hgE is not None and ie is not None:
        den = float(np.max(np.abs(ie))) or 1.0
        r = float(np.max(np.abs(hgE))) / den
        line("hourglass / internal", r * 100, f"{hg*100:g} %", r < hg, " %")
    else:
        line("hourglass / internal", None, None, True)

    if dm is not None:
        r = float(np.max(dm))
        # glstat reports it already as a percentage
        line("added mass", r, f"{mass*100:g} %", r < mass * 100, " %")
    else:
        line("added mass", None, None, True)

    if slE is not None and ie is not None:
        den = float(np.max(np.abs(ie))) or 1.0
        r = float(np.max(np.abs(slE))) / den
        neg = float(np.min(slE)) / den
        ok = r < slide and neg > -slide
        line("|sliding| / internal", r * 100, f"{slide*100:g} %", ok, " %")
        if neg < -0.01:
            results.append(f"  {'most negative sliding':<26} {neg*100:>10.3g} %"
                           "          negative sliding energy means contact is"
                           " doing work on the model")
    else:
        line("|sliding| / internal", None, None, True)

    if erE is not None:
        results.append(f"  {'eroded energy':<26} {float(np.max(np.abs(erE))):>10.4g}"
                       "        informational")

    head = [f"Energy balance check: {path}"]
    if t is not None:
        head.append(f"  {len(t)} output states, t = 0 .. {t[-1]:g}")
    if ke is not None and ie is not None and len(ke):
        head.append(f"  KE {ke[0]:.4g} -> {ke[-1]:.4g}, "
                    f"IE {ie[0]:.4g} -> {ie[-1]:.4g}")
        if ke[0]:
            head.append(f"  energy absorbed: {ie[-1] - ie[0]:.4g} "
                        f"({(ie[-1]-ie[0])/ke[0]*100:.1f} % of initial KE)")
    print("\n".join(head))
    print("\n".join(results))
    print(f"\n  {'FAILED ' + str(fails) + ' check(s)' if fails else 'all checks passed'}")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--drift-limit", type=float, default=0.01)
    ap.add_argument("--hg-limit", type=float, default=0.05)
    ap.add_argument("--mass-limit", type=float, default=0.05)
    ap.add_argument("--slide-limit", type=float, default=0.10)
    a = ap.parse_args()
    bad = 0
    for f in a.files:
        bad += check(f, a.drift_limit, a.hg_limit, a.mass_limit, a.slide_limit)
        print()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
