#!/usr/bin/env python3
"""
Study 04 - resistance spot weld failure envelope.

A body-in-white crash model lives or dies on its spot welds. There are
several thousand of them, they are represented by a single beam or solid
element each, and their failure is what decides whether a joint tears
open or a section stays closed and keeps absorbing energy.

This study builds one specimen geometry loaded at a sweep of angles, the
way a KS-II style test is run: at 0 degrees the weld sees pure shear, at
90 degrees pure normal load, and the intermediate angles fill in the
envelope between them. Each run gives one point of peak resultant force,
and calibrate.py fits the *MAT_SPOTWELD failure surface

    (|N_rr| / NRR)^NF + (|N_rs| / NRS)^NF  =  1

through those points and writes the material card.

The weld itself is a beam element tied to both sheets with
*CONTACT_SPOTWELD, with its nodes deliberately placed at an element
centroid rather than on a shell node - a tied contact wants to project
onto a segment interior, and coincident nodes are a common source of
initial penetration warnings.

Usage:
    python3 build.py
"""

from __future__ import annotations

import glob
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from kfile import Deck, card, fmt, control_explicit_crash, database_standard  # noqa: E402
from mesh import Mesh                                                          # noqa: E402
import materials as mat                                                        # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "models")

GRADE = "DP600"
THICK = 1.5          # mm, both sheets
SHEET_L = 60.0       # mm free length of each sheet
SHEET_W = 40.0       # mm
OVERLAP = 40.0       # mm
NUGGET_D = 5.0       # mm weld nugget diameter
ELEM = 2.0           # mm
PULL_V = 0.5         # mm/ms
END_TIME = 6.0       # ms
ANGLES = [0, 30, 45, 60, 90]     # degrees from pure shear to pure normal

PID_S1, PID_S2, PID_WELD = 1, 2, 3
SID_SHEET, SID_WELD = 1, 3
MID_SHEET, MID_WELD = 1, 3
HGID = 1
LC_FLOW, LC_PULL = 100, 200
NS_FIX, NS_PULL, NS_WELD = 10, 11, 12
PSID_SHEETS, PSID_S1, PSID_S2 = 20, 21, 22


def build_mesh():
    """Two overlapping strips, upper sheet offset by one thickness so the
    shell mid-surfaces sit one sheet thickness apart."""
    m = Mesh()
    nx = int(round(SHEET_L / ELEM))
    ny = int(round(SHEET_W / ELEM))
    gap = THICK

    # lower sheet spans x in [-SHEET_L, 0] ... overlap is x in [-OVERLAP, 0]
    lo = m.grid(nx + 1, ny + 1,
                lambda i, j: (-SHEET_L + SHEET_L * i / nx,
                              -SHEET_W / 2 + SHEET_W * j / ny, 0.0))
    m.quads_from_grid(lo, PID_S1)
    up = m.grid(nx + 1, ny + 1,
                lambda i, j: (-OVERLAP + SHEET_L * i / nx,
                              -SHEET_W / 2 + SHEET_W * j / ny, gap))
    m.quads_from_grid(up, PID_S2)

    # weld at the centre of the overlap, positioned at an element
    # centroid so the tied contact projects into a segment interior
    xw = -OVERLAP / 2.0 + ELEM / 2.0
    yw = ELEM / 2.0
    n1 = m.node(xw, yw, 0.0)
    n2 = m.node(xw, yw, gap)
    n3 = m.node(xw, yw + 10.0, gap / 2.0)     # beam orientation node

    m.add_node_set(NS_FIX, [n for n in m.pick(
        lambda x, y, z: z < gap / 2 and x < -SHEET_L + 6.0)])
    m.add_node_set(NS_PULL, [n for n in m.pick(
        lambda x, y, z: z > gap / 2 and x > -OVERLAP + SHEET_L - 6.0)])
    m.add_node_set(NS_WELD, [n1, n2])
    m.weld = (n1, n2, n3)
    return m


def write_case(m: Mesh, angle_deg: float) -> str:
    tag = f"spotweld_{int(angle_deg):02d}deg"
    path = os.path.join(MODELS, tag + ".k")
    th = math.radians(angle_deg)
    vx, vz = math.cos(th), math.sin(th)
    n1, n2, n3 = m.weld

    d = Deck(f"spot weld coupon, load angle {angle_deg:g} deg, {GRADE} "
             f"t={THICK:g} mm, nugget {NUGGET_D:g} mm")
    d.note(
        "units: mm / ms / kg / kN / GPa\n"
        f"pull direction ({vx:.3f}, 0, {vz:.3f}) - "
        f"{angle_deg:g} deg from pure shear\n"
        "take the peak resultant from the swforc file; that is one point\n"
        "on the weld failure envelope fitted by calibrate.py\n"
        "failure is left OFF in these decks (NRR/NRS blank) so the peak\n"
        "load is governed by the sheet, not by an assumed weld strength")

    d.raw(*control_explicit_crash(END_TIME, dt2ms=-3.0e-4))
    d.raw(*database_standard(dt_ascii=0.01, dt_d3plot=0.25))
    d.kw("DATABASE_SWFORC", (("dt", "binary", "lcur", "ioopt"), (0.01, 3, 0, 1)))
    d.kw("DATABASE_HISTORY_NODE_SET", (NS_PULL,))

    m.emit(d)

    # weld beam
    d.kw("ELEMENT_BEAM",
         "".join(fmt(v, 8) for v in (m._eid + 1, PID_WELD, n1, n2, n3)))

    d.part(PID_S1, SID_SHEET, MID_SHEET, "lower sheet", hgid=HGID)
    d.part(PID_S2, SID_SHEET, MID_SHEET, "upper sheet", hgid=HGID)
    d.part(PID_WELD, SID_WELD, MID_WELD, "spot weld nugget")

    d.lines.append("*SECTION_SHELL_TITLE")
    d.lines.append("sheet, type 16")
    d.cards(
        (("secid", "elform", "shrf", "nip", "propt", "qr/irid", "icomp", "setyp"),
         (SID_SHEET, 16, 0.8333, 5, 1.0, 0.0, 0, 1)),
        (("t1", "t2", "t3", "t4"), (THICK,) * 4))
    d.lines.append("*SECTION_BEAM_TITLE")
    d.lines.append("spot weld beam, elform 9")
    d.cards(
        (("secid", "elform", "shrf", "qr/irid", "cst", "scoor", "nsm"),
         (SID_WELD, 9, 1.0, 2.0, 0.0, 0.0, 0.0)),
        (("ts1", "ts2", "tt1", "tt2"),
         (NUGGET_D, NUGGET_D, NUGGET_D, NUGGET_D)))
    mat.add_hourglass(d, HGID)

    g = mat.GRADES[GRADE]
    d.define_curve(LC_FLOW, mat.swift_curve(g["K"], g["eps0"], g["n"], g["sy"]),
                   title=f"{GRADE} flow curve [GPa]")
    mat.add_mat24(d, MID_SHEET, GRADE, LC_FLOW, rate=False)

    # *MAT_SPOTWELD. Yield is raised relative to the sheet because the
    # nugget is a cast, hardened microstructure; the resultant failure
    # limits are left at zero here and filled in by calibrate.py.
    d.lines.append("*MAT_SPOTWELD_TITLE")
    d.lines.append("spot weld nugget, resultant failure to be calibrated")
    d.cards(
        (("mid", "ro", "e", "pr", "sigy", "et", "dt", "tfail"),
         (MID_WELD, mat.RHO_STEEL, mat.E_STEEL, mat.NU_STEEL, 0.80, 0.0,
          0.0, 0.0)),
        (("efail", "nrr", "nrs", "nrt", "mrr", "mss", "mtt", "nf"),
         (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)))

    d.define_curve(LC_PULL, [(0.0, 0.0), (0.5, PULL_V), (END_TIME, PULL_V)],
                   title="pull velocity [mm/ms]")

    d.kw("BOUNDARY_SPC_SET",
         (("nsid", "cid", "dofx", "dofy", "dofz", "dofrx", "dofry", "dofrz"),
          (NS_FIX, 0, 1, 1, 1, 1, 1, 1)))
    # a vector-defined prescribed motion is what lets one geometry sweep
    # the whole envelope from shear to normal
    d.kw("DEFINE_VECTOR",
         (("vid", "xt", "yt", "zt", "xh", "yh", "zh", "cid"),
          (1, 0.0, 0.0, 0.0, vx, 0.0, vz, 0)))
    d.kw("BOUNDARY_PRESCRIBED_MOTION_SET",
         (("id", "dof", "vad", "lcid", "sf", "vid", "death", "birth"),
          (NS_PULL, 4, 0, LC_PULL, 1.0, 1, 1.0e20, 0.0)))

    for psid, pids in ((PSID_S1, [PID_S1]), (PSID_S2, [PID_S2]),
                       (PSID_SHEETS, [PID_S1, PID_S2])):
        d.kw("SET_PART_LIST", (psid, 0.0, 0.0, 0.0, 0.0), tuple(pids))

    d.lines.append("*CONTACT_SPOTWELD_ID")
    d.lines.append(card(1) + "weld beam tied to both sheets")
    d.cards(
        (("ssid", "msid", "sstyp", "mstyp", "sboxid", "mboxid", "spr", "mpr"),
         (NS_WELD, PSID_SHEETS, 4, 2, 0, 0, 1, 1)),
        (("fs", "fd", "dc", "vc", "vdc", "penchk", "bt", "dt"),
         (0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 1.0e20)),
        (("sfs", "sfm", "sst", "mst", "sfst", "sfmt", "fsf", "vsf"),
         (1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0)))

    d.lines.append("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID")
    d.lines.append(card(2) + "sheet to sheet in the overlap")
    d.cards(
        (("ssid", "msid", "sstyp", "mstyp", "sboxid", "mboxid", "spr", "mpr"),
         (PSID_S1, PSID_S2, 2, 2, 0, 0, 1, 1)),
        (("fs", "fd", "dc", "vc", "vdc", "penchk", "bt", "dt"),
         (0.15, 0.10, 0.0, 0.0, 20.0, 0, 0.0, 1.0e20)),
        (("sfs", "sfm", "sst", "mst", "sfst", "sfmt", "fsf", "vsf"),
         (1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0)),
        (("soft", "sofscl", "lcidab", "maxpar", "sbopt", "depth", "bsort", "frcfrq"),
         (1, 0.1, 0, 1.025, 2.0, 2, 0, 1)))

    d.write(path)
    return path


def main():
    os.makedirs(MODELS, exist_ok=True)
    for stale in glob.glob(os.path.join(MODELS, "*.k")):
        os.remove(stale)
    m = build_mesh()
    print("mesh:", m.summary())
    for a in ANGLES:
        print("wrote", os.path.relpath(write_case(m, a), HERE))


if __name__ == "__main__":
    main()
