#!/usr/bin/env python3
"""
Collect every crash box run into one results table.

Walks models/ for run directories (any folder holding glstat + rcforc +
nodout next to a crashbox_*.k deck), and for each one:

  1. checks the run is trustworthy before reading a single performance
     number - normal termination, energy balance, hourglass, added mass,
     sliding energy, and "did the tube actually carry load"
  2. extracts peak force (raw and CFC 600), mean crush force, CFE,
     absorbed energy, stroke, SEA and peak deceleration
  3. writes results/crashbox_results.csv, results/force_crush.png and
     rewrites the table in README.md between the RESULTS markers

Thickness, density and element size are read from the deck in the run
directory, not assumed, so SEA is right for every variant.

    python3 collect_results.py            # everything under models/
    python3 collect_results.py --no-readme

ASCII output only (the solver default with binary=3 plus ascii files).
IDs match build.py: contact 2 is impactor-to-tube, node set 11 is the
single impactor node, material 1 is the tube.
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from postproc.read_curves import (  # noqa: E402
    get, read_glstat, read_matsum, read_nodout, read_rcforc, sae_cfc_filter,
)

CONTACT_IMPACTOR = 2
MID_TUBE = 1
IMPACT_MASS_KG = 100.0
FREE_LENGTH_MM = 300.0
PERIMETER_MM = 4 * (80.0 - 2 * 6.0) + 2 * np.pi * 6.0
LIMITS = dict(drift=1.0, hg=5.0, mass=5.0, slide=10.0)   # percent

ORDER = ["t1.5 h5 DP600", "t1.5 h7.5 DP600", "t1.5 h3.5 DP600",
         "t1.2 h5 DP600", "t1.8 h5 DP600", "t1.5 h5 HC340LA",
         "t2.5 h5 AA6060-T6", "t1.5 h5 DP600 + GISSMO"]


# ------------------------------------------------------------ deck info
def deck_info(run_dir):
    decks = [k for k in glob.glob(os.path.join(run_dir, "crashbox_*.k"))]
    if not decks:
        return None
    text = open(decks[0], errors="ignore").read()
    m = re.search(r"crashbox_t([\d.]+)_h([\d.]+)_([A-Za-z0-9\-]+?)(_gissmo)?\.k$",
                  os.path.basename(decks[0]))
    t, h, grade, gissmo = float(m.group(1)), m.group(2), m.group(3), bool(m.group(4))
    # tube material density = second field of the first MAT_024 data card
    mm = re.search(r"\*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE\n.*\n(?:\$.*\n)*(.{10})(.{10})",
                   text)
    rho = float(mm.group(2)) if mm else 7.85e-6
    name = f"t{t:g} h{h} {grade}" + (" + GISSMO" if gissmo else "")
    return dict(name=name, t=t, h=float(h), grade=grade, rho=rho,
                gissmo=gissmo, deck=os.path.basename(decks[0]))


def termination(run_dir):
    p = os.path.join(run_dir, "messag")
    if not os.path.exists(p):
        return "no messag", 0
    txt = open(p, errors="ignore").read()
    eroded = len(re.findall(r"failed at time", txt))
    for key, label in [("N o r m a l", "normal"),
                       ("termination due to mass increase", "mass increase"),
                       ("E r r o r   t e r m i n a t i o n", "error")]:
        if key in txt:
            return label, eroded
    return "unknown", eroded


# ------------------------------------------------------------- one run
def evaluate(run_dir):
    info = deck_info(run_dir)
    if info is None:
        return None
    r = dict(info, run=os.path.relpath(run_dir, HERE), status="", notes="")
    term, eroded = termination(run_dir)
    r["termination"] = term
    files_ok = all(os.path.exists(os.path.join(run_dir, f))
                   for f in ("glstat", "rcforc", "nodout", "matsum"))
    if not files_ok:
        r["status"] = "NOT RUN"
        r["notes"] = f"no result files (messag: {term})"
        return r

    g = read_glstat(os.path.join(run_dir, "glstat"))
    t_f, fx, fy, fz = read_rcforc(os.path.join(run_dir, "rcforc"), CONTACT_IMPACTOR)
    F = np.sqrt(fx ** 2 + fy ** 2 + fz ** 2)
    nsid = read_nodout_first_node(os.path.join(run_dir, "nodout"))
    nd = read_nodout(os.path.join(run_dir, "nodout"), nsid)
    ms = read_matsum(os.path.join(run_dir, "matsum"), MID_TUBE)

    # ---- validity: stop at the first output where the energy balance breaks
    ratio = get(g, "total energy / initial energy")
    tg = get(g, "time")
    bad = np.where(np.abs(ratio - 1.0) * 100 > LIMITS["drift"])[0]
    # A run that completes and then holds a constant offset has taken one
    # discrete energy injection (a contact event, a shooting node), not a
    # runaway. Those numbers are still worth reporting, flagged, over the
    # whole history. A drift that keeps growing is truncated at the break.
    runaway = True
    if len(bad):
        tail = np.abs(ratio[bad[0]:] - 1.0) * 100
        runaway = float(tail[-1]) > 10.0 or float(tail[-1]) > 2 * float(tail[0])
    t_valid = tg[bad[0] - 1] if (len(bad) and runaway) else tg[-1]
    keep = lambda tt: tt <= t_valid + 1e-9                       # noqa: E731

    ie_g = get(g, "internal energy")
    gk = keep(tg)
    ie_max = max(float(np.nanmax(ie_g[gk])), 1e-9)
    r["end_time_ms"] = float(tg[-1])
    r["valid_to_ms"] = float(t_valid)
    r["drift_pct"] = float(np.nanmax(np.abs(ratio - 1.0)) * 100)
    r["hg_pct"] = float(np.nanmax(np.abs(get(g, "hourglass energy")[gk])) / ie_max * 100)
    r["slide_pct"] = float(np.nanmax(np.abs(get(g, "sliding interface energy")[gk])) / ie_max * 100)
    added = get(g, "added mass")
    r["added_mass_pct_model"] = float(np.nanmax(get(g, "percentage increase")[gk]))
    tube_mass = PERIMETER_MM * FREE_LENGTH_MM * info["t"] * info["rho"]
    r["added_mass_pct_tube"] = float(np.nanmax(added[gk]) / tube_mass * 100)

    # ---- performance, on the valid part of the history only
    n = min(len(t_f), len(nd["time"]))
    m = keep(t_f[:n])
    t, Fm = t_f[:n][m], F[:n][m]
    disp = np.abs(nd["z_disp"][:n][m])
    if Fm.max() < 1e-3:
        r["status"] = "INVALID"
        r["notes"] = (f"tube carried no load; {eroded} elements eroded"
                      if eroded else "tube carried no load")
        return r

    _, Ff = sae_cfc_filter(t, Fm, 600)
    c0 = int(np.argmax(Fm > 1e-3))
    crush = np.clip(disp - disp[c0], 0, None)
    crush[:c0] = 0
    k = int(np.argmax(crush)) + 1              # loading branch only
    stroke = float(crush.max())
    e_fd = float(np.trapezoid(Fm[:k], disp[:k]) if hasattr(np, "trapezoid")
                 else np.trapz(Fm[:k], disp[:k]))
    ms_k = ms["time"] <= t_valid + 1e-9
    absorbed = float(ms["internal"][ms_k][-1])
    # Energy in deleted elements leaves the part's internal energy and
    # reappears in glstat as eroded internal energy. Leave it out and an
    # erosion run looks like it absorbed a third less than it did.
    er_ie = get(g, "eroded internal energy")
    r["eroded_J"] = float(np.nanmax(er_ie[gk])) if er_ie is not None else 0.0
    r["eroded_elements"] = eroded
    absorbed += r["eroded_J"]
    peak = float(Ff.max())
    mean = e_fd / stroke if stroke else float("nan")
    crushed_mass = PERIMETER_MM * info["t"] * stroke * info["rho"]

    r.update(peak_raw_kN=float(Fm.max()), peak_cfc600_kN=peak, mean_kN=mean,
             CFE=mean / peak if peak else float("nan"), absorbed_J=absorbed,
             stroke_mm=stroke, stroke_pct=stroke / FREE_LENGTH_MM * 100,
             SEA_kJ_kg=absorbed / crushed_mass / 1000 if crushed_mass else float("nan"),
             peak_decel_g=peak * 1000.0 / IMPACT_MASS_KG / 9.81,
             v_end_ms=float(nd["z_vel"][:n][m][-1]),
             curve=(crush[:k], Ff[:k]))

    fails = []
    if term != "normal":
        fails.append(f"terminated: {term}")
    if len(bad):
        fails.append(f"energy balance lost at {tg[bad[0]]:.2f} ms")
    if r["hg_pct"] > LIMITS["hg"]:
        fails.append("hourglass")
    if r["added_mass_pct_model"] > LIMITS["mass"]:
        fails.append("added mass")
    if r["slide_pct"] > LIMITS["slide"]:
        fails.append("sliding energy")
    if abs(e_fd / max(absorbed, 1e-9) - 1) > 0.05:
        fails.append("force-displacement and matsum energy disagree >5 %")
    if fails:
        if (term == "normal" and not len(bad)
                and fails == ["sliding energy"] + fails[1:] and "sliding energy" in fails
                and all(f in ("sliding energy",
                              "force-displacement and matsum energy disagree >5 %")
                        for f in fails)):
            r["status"] = "CHECK"
            r["notes"] = (f"energy balance clean ({r['drift_pct']:.2f} % drift) but "
                          f"sliding energy is {r['slide_pct']:.0f} % of internal"
                          + (f"; {eroded} elements eroded" if eroded else ""))
        elif len(bad) and not runaway and term == "normal":
            r["status"] = "CHECK"
            r["notes"] = (f"one energy step of {abs(ratio[bad[0]]-1)*100:.1f} % at "
                          f"{tg[bad[0]]:.2f} ms, flat afterwards; full history reported")
        else:
            r["status"] = "PARTIAL" if len(bad) and stroke > 0 else "INVALID"
            r["notes"] = "; ".join(fails)
            if r["status"] == "PARTIAL":
                r["notes"] += f" - values up to {t_valid:.2f} ms only"
    else:
        r["status"] = "valid"
    return r


def read_nodout_first_node(path):
    with open(path, errors="ignore") as fh:
        for line in fh:
            if "{END LEGEND}" in line:
                break
            m = re.match(r"^\s+(\d+)\s*$", line)
            if m:
                return int(m.group(1))
    return 3917


# ------------------------------------------------------------- output
COLS = [("peak_cfc600_kN", "peak CFC600 [kN]", "{:.1f}"),
        ("mean_kN", "mean [kN]", "{:.1f}"),
        ("CFE", "CFE", "{:.2f}"),
        ("absorbed_J", "absorbed [J]", "{:.0f}"),
        ("stroke_mm", "stroke [mm]", "{:.1f}"),
        ("SEA_kJ_kg", "SEA [kJ/kg]", "{:.1f}"),
        ("hg_pct", "HG [%]", "{:.2f}"),
        ("added_mass_pct_model", "added mass [% model]", "{:.2f}"),
        ("added_mass_pct_tube", "added mass [% tube]", "{:.1f}")]


def markdown_table(rows):
    head = "| variant | " + " | ".join(c[1] for c in COLS) + " | status |"
    sep = "|---" * (len(COLS) + 2) + "|"
    lines = [head, sep]
    for r in rows:
        cells = []
        for key, _, fmt in COLS:
            v = r.get(key)
            cells.append("-" if v is None or (isinstance(v, float) and np.isnan(v))
                         else fmt.format(v))
        st = r["status"] if r["status"] == "valid" else f"**{r['status']}** - {r['notes']}"
        lines.append(f"| {r['name']} | " + " | ".join(cells) + f" | {st} |")
    return "\n".join(lines)


def plot(rows, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed - no plot")
        return
    colours = {"t1.5 h5 DP600": "#2a78d6", "t1.2 h5 DP600": "#eb6834",
               "t1.8 h5 DP600": "#1baf7a", "t1.5 h7.5 DP600": "#eda100",
               "t1.5 h3.5 DP600": "#008300", "t1.5 h5 HC340LA": "#e87ba4",
               "t2.5 h5 AA6060-T6": "#4a3aa7", "t1.5 h5 DP600 + GISSMO": "#e34948"}
    panels = [("Wall thickness (DP600, 5 mm mesh)",
               ["t1.2 h5 DP600", "t1.5 h5 DP600", "t1.8 h5 DP600"]),
              ("Mesh, material and damage (t = 1.5 mm unless noted)",
               ["t1.5 h5 DP600", "t1.5 h7.5 DP600", "t1.5 h3.5 DP600",
                "t1.5 h5 HC340LA", "t2.5 h5 AA6060-T6", "t1.5 h5 DP600 + GISSMO"])]
    by = {r["name"]: r for r in rows if "curve" in r}
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, (title, names) in zip(axs, panels):
        for nm in names:
            if nm not in by:
                continue
            x, y = by[nm]["curve"]
            lab = nm if by[nm]["status"] == "valid" else f"{nm} ({by[nm]['status'].lower()})"
            ax.plot(x, y, lw=2, color=colours.get(nm, "#52514e"), label=lab)
        ax.set_title(title, loc="left", fontsize=10)
        ax.set_xlabel("crush [mm]")
        ax.grid(alpha=0.25, lw=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(frameon=False, fontsize=8)
        ax.set_xlim(0, None)
        ax.set_ylim(0, None)
    axs[0].set_ylabel("impactor contact force, CFC 600 [kN]")
    fig.suptitle(f"Crash box axial crush - force vs crush "
                 f"({IMPACT_MASS_KG:g} kg @ 12 m/s)", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", default=os.path.join(HERE, "models"))
    ap.add_argument("--no-readme", action="store_true")
    a = ap.parse_args()

    dirs = sorted({os.path.dirname(p) for p in
                   glob.glob(os.path.join(a.models, "**", "crashbox_*.k"), recursive=True)
                   if os.path.dirname(p) != os.path.abspath(a.models)})
    rows = [r for r in (evaluate(d) for d in dirs) if r]
    rows.sort(key=lambda r: ORDER.index(r["name"]) if r["name"] in ORDER else 99)

    out = os.path.join(HERE, "results")
    os.makedirs(out, exist_ok=True)
    keys = ["name", "run", "status", "notes", "termination", "end_time_ms",
            "valid_to_ms", "peak_raw_kN", "peak_cfc600_kN", "mean_kN", "CFE",
            "absorbed_J", "stroke_mm", "stroke_pct", "SEA_kJ_kg", "peak_decel_g",
            "v_end_ms", "drift_pct", "hg_pct", "slide_pct",
            "added_mass_pct_model", "added_mass_pct_tube", "eroded_J",
            "eroded_elements", "t", "rho"]
    with open(os.path.join(out, "crashbox_results.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(keys)
        for r in rows:
            w.writerow([f"{r[k]:.5g}" if isinstance(r.get(k), float) else r.get(k, "")
                        for k in keys])
    plot(rows, os.path.join(out, "force_crush.png"))

    table = markdown_table(rows)
    print(table)
    if not a.no_readme:
        p = os.path.join(HERE, "README.md")
        txt = open(p, encoding="utf-8").read()
        start, end = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"
        if start in txt and end in txt:
            txt = txt.split(start)[0] + start + "\n" + table + "\n" + end + txt.split(end)[1]
            open(p, "w", encoding="utf-8").write(txt)
            print("\nREADME.md results table updated")
    print(f"wrote {out}/crashbox_results.csv and force_crush.png")


if __name__ == "__main__":
    main()
