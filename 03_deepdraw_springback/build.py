#!/usr/bin/env python3
"""
Study 03 - U-channel deep draw and implicit springback.

Geometry follows the classic 2D draw-bend benchmark: a long narrow strip
drawn into a U-channel over a radiused die, then released. The benchmark
exists because it is the cheapest experiment that produces all three
springback modes at once - sidewall curl, flange opening and the change
in punch-corner radius - and because those are what a forming model has
to get right before it is worth trusting on a real panel.

Two decks are produced per case:

  forming_*.k     explicit draw, MAT_036 Barlat with the Lankford values
                  of the grade, forming contacts, adaptive-free
                  structured blank. Ends by writing dynain through
                  *INTERFACE_SPRINGBACK_LSDYNA.

  springback_*.k  implicit static release. Reads the dynain from the
                  forming run, so it inherits the deformed shape, the
                  thinned thickness and the residual stress through the
                  thickness. Rigid body modes are removed with a
                  three-node minimal constraint rather than by clamping
                  an edge, which would suppress the very deformation
                  being measured.

The blankholder force is swept because springback is far more sensitive
to restraining force than to almost anything else in the model.

Usage:
    python3 build.py
"""

from __future__ import annotations

import glob
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from kfile import Deck, card, control_explicit_crash, database_standard  # noqa: E402
from mesh import Mesh, swept_profile, polyline_line, polyline_arc        # noqa: E402
import materials as mat                                                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "models")

# ------------------------------------------------------------------ geometry
BLANK_L = 350.0      # mm
BLANK_W = 35.0       # mm
THICK = 0.80         # mm
GRADE = "DC04"

PUNCH_HALF = 25.0    # mm, half width of the punch
PUNCH_R = 5.0        # mm, punch nose radius
DIE_R = 5.0          # mm, die shoulder radius
CLEARANCE = 0.05     # mm per side on top of the sheet thickness
DIE_HALF = PUNCH_HALF + THICK + CLEARANCE
DRAW_DEPTH = 70.0    # mm

ELEM = 2.0           # mm target element size on the blank
PUNCH_V = 5.0        # mm/ms, ramped - artificially fast, see README
BHF_CASES = [2.45, 10.0, 19.6]      # kN total blankholder force

# ------------------------------------------------------------------ ids
PID_BLANK, PID_DIE, PID_PUNCH, PID_HOLD = 1, 2, 3, 4
SID_BLANK, SID_TOOL = 1, 2
MID_BLANK, MID_DIE, MID_PUNCH, MID_HOLD = 1, 2, 3, 4
HGID = 1
LC_FLOW, LC_PUNCH, LC_BHF = 100, 200, 201
PSID_BLANK, PSID_DIE, PSID_PUNCH, PSID_HOLD = 10, 11, 12, 13


def tool_profiles():
    """Right half of each tool as an (x, z) polyline; the left half is
    mirrored. z = 0 is the blank mid-surface."""
    ds = 1.5
    half_t = THICK / 2.0
    x_out = BLANK_L / 2.0 + 10.0

    # --- die: flange flat, shoulder arc, then the vertical draw wall
    die = []
    die += polyline_line((x_out, -half_t), (DIE_HALF + DIE_R, -half_t), ds)
    die += polyline_arc(DIE_HALF + DIE_R, -half_t - DIE_R, DIE_R,
                        math.pi / 2, math.pi, ds)
    die += polyline_line((DIE_HALF, -half_t - DIE_R),
                         (DIE_HALF, -half_t - DIE_R - DRAW_DEPTH - 15.0), ds)
    die.append((DIE_HALF, -half_t - DIE_R - DRAW_DEPTH - 15.0))

    # --- punch: nose flat, corner arc, vertical flank
    pun = []
    pun += polyline_line((0.0, half_t), (PUNCH_HALF - PUNCH_R, half_t), ds)
    pun += polyline_arc(PUNCH_HALF - PUNCH_R, half_t + PUNCH_R, PUNCH_R,
                        -math.pi / 2, 0.0, ds)
    pun += polyline_line((PUNCH_HALF, half_t + PUNCH_R),
                         (PUNCH_HALF, half_t + PUNCH_R + DRAW_DEPTH + 20.0), ds)
    pun.append((PUNCH_HALF, half_t + PUNCH_R + DRAW_DEPTH + 20.0))

    # --- blankholder: flat pad over the flange only
    hold = polyline_line((DIE_HALF + DIE_R + 2.0, half_t), (x_out, half_t), ds)
    hold.append((x_out, half_t))
    return die, pun, hold


def mirror(profile):
    return [(-x, z) for x, z in reversed(profile)]


def build_mesh():
    m = Mesh()
    nx = int(round(BLANK_L / ELEM))
    ny = int(round(BLANK_W / ELEM))
    blank_ids = m.grid(nx + 1, ny + 1,
                       lambda i, j: (-BLANK_L / 2 + BLANK_L * i / nx,
                                     -BLANK_W / 2 + BLANK_W * j / ny, 0.0))
    m.quads_from_grid(blank_ids, PID_BLANK)

    die, pun, hold = tool_profiles()
    ty0, ty1, tny = -BLANK_W / 2 - 5.0, BLANK_W / 2 + 5.0, 12
    for prof, pid in ((die, PID_DIE), (pun, PID_PUNCH), (hold, PID_HOLD)):
        swept_profile(m, pid, prof, ty0, ty1, tny)
        swept_profile(m, pid, mirror(prof), ty0, ty1, tny)

    # three nodes on the blank centreline used to remove rigid body modes
    # in the springback run: centre, one along x, one along y
    mid_i, mid_j = nx // 2, ny // 2
    m.spring_nodes = (blank_ids[mid_i][mid_j],
                      blank_ids[mid_i + 5][mid_j],
                      blank_ids[mid_i][0])
    m.blank_ids = blank_ids
    m.nx, m.ny = nx, ny
    return m


def write_forming(m: Mesh, bhf: float) -> str:
    tag = f"forming_bhf{bhf:g}"
    path = os.path.join(MODELS, tag + ".k")
    end_time = DRAW_DEPTH / PUNCH_V + 3.0

    d = Deck(f"U-channel draw, {GRADE} t={THICK:g}mm, BHF={bhf:g} kN")
    d.note(
        "units: mm / ms / kg / kN / GPa\n"
        f"blank {BLANK_L:g} x {BLANK_W:g} x {THICK:g} mm, element {ELEM:g} mm\n"
        f"punch {2*PUNCH_HALF:g} mm wide, nose R{PUNCH_R:g}, die shoulder R{DIE_R:g}\n"
        f"draw depth {DRAW_DEPTH:g} mm, blankholder force {bhf:g} kN\n"
        "writes dynain at termination for the implicit springback run")

    d.raw(*control_explicit_crash(end_time, dt2ms=-3.0e-4, tssfac=0.9))
    d.kw("CONTROL_ADAPTIVE_CURVE") if False else None
    d.raw(*database_standard(dt_ascii=0.05, dt_d3plot=1.0))
    d.include("mesh.k")

    d.part(PID_BLANK, SID_BLANK, MID_BLANK, f"blank {GRADE}", hgid=HGID)
    d.part(PID_DIE, SID_TOOL, MID_DIE, "die")
    d.part(PID_PUNCH, SID_TOOL, MID_PUNCH, "punch")
    d.part(PID_HOLD, SID_TOOL, MID_HOLD, "blankholder")

    d.lines.append("*SECTION_SHELL_TITLE")
    d.lines.append("blank, type 16, 7 integration points through thickness")
    d.cards(
        (("secid", "elform", "shrf", "nip", "propt", "qr/irid", "icomp", "setyp"),
         (SID_BLANK, 16, 0.8333, 7, 1.0, 0.0, 0, 1)),
        (("t1", "t2", "t3", "t4"), (THICK,) * 4))
    d.lines.append("*SECTION_SHELL_TITLE")
    d.lines.append("rigid tool surfaces")
    d.cards(
        (("secid", "elform", "shrf", "nip", "propt", "qr/irid", "icomp", "setyp"),
         (SID_TOOL, 2, 0.8333, 2, 1.0, 0.0, 0, 1)),
        (("t1", "t2", "t3", "t4"), (1.0,) * 4))
    mat.add_hourglass(d, HGID)

    g = mat.GRADES[GRADE]
    d.define_curve(LC_FLOW, mat.swift_curve(g["K"], g["eps0"], g["n"], g["sy"]),
                   title=f"{GRADE} flow curve [GPa]")
    mat.add_mat36(d, MID_BLANK, GRADE, LC_FLOW)
    mat.add_mat_rigid(d, MID_DIE, "die", cmo=1.0, con1=7, con2=7)
    mat.add_mat_rigid(d, MID_PUNCH, "punch", cmo=1.0, con1=4, con2=7)
    mat.add_mat_rigid(d, MID_HOLD, "blankholder", cmo=1.0, con1=4, con2=7)

    # punch travel: smooth ramp, then constant, so no shock is injected
    d.define_curve(LC_PUNCH,
                   [(0.0, 0.0), (1.0, PUNCH_V), (end_time, PUNCH_V)],
                   title="punch velocity [mm/ms]")
    d.define_curve(LC_BHF,
                   [(0.0, 0.0), (0.5, bhf), (end_time, bhf)],
                   title="blankholder force [kN]")

    d.kw("BOUNDARY_PRESCRIBED_MOTION_RIGID",
         (("pid", "dof", "vad", "lcid", "sf", "vid", "death", "birth"),
          (PID_PUNCH, 3, 0, LC_PUNCH, -1.0, 0, 1.0e20, 0.0)))
    d.kw("LOAD_RIGID_BODY",
         (("pid", "dof", "lcid", "sf", "cid", "m1", "m2", "m3"),
          (PID_HOLD, 3, LC_BHF, -1.0, 0, 0, 0, 0)))

    for psid, pid in ((PSID_BLANK, PID_BLANK), (PSID_DIE, PID_DIE),
                      (PSID_PUNCH, PID_PUNCH), (PSID_HOLD, PID_HOLD)):
        d.kw("SET_PART_LIST", (psid, 0.0, 0.0, 0.0, 0.0), (pid,))

    # forming contacts: blank is always the slave side, one-way, with a
    # Coulomb coefficient typical of a lubricated mild steel / tool pair
    for cid, (name, msid) in enumerate(
            (("blank to die", PSID_DIE),
             ("blank to punch", PSID_PUNCH),
             ("blank to blankholder", PSID_HOLD)), start=1):
        d.lines.append("*CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE_ID")
        d.lines.append(card(cid) + name)
        d.cards(
            (("ssid", "msid", "sstyp", "mstyp", "sboxid", "mboxid", "spr", "mpr"),
             (PSID_BLANK, msid, 2, 2, 0, 0, 1, 1)),
            (("fs", "fd", "dc", "vc", "vdc", "penchk", "bt", "dt"),
             (0.125, 0.125, 0.0, 0.0, 10.0, 0, 0.0, 1.0e20)),
            (("sfs", "sfm", "sst", "mst", "sfst", "sfmt", "fsf", "vsf"),
             (1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0)),
            (("soft", "sofscl", "lcidab", "maxpar", "sbopt", "depth",
              "bsort", "frcfrq"),
             (1, 0.1, 0, 1.025, 2.0, 5, 0, 1)))

    # hand the deformed blank, its thickness field and its residual
    # stress over to the implicit springback run
    d.kw("INTERFACE_SPRINGBACK_LSDYNA",
         (("psid", "nshv", "ftype", "ftensr", "nthhsv", "rflag", "intstrn", "optc"),
          (PSID_BLANK, 0, 0, 0, 0, 0, 0, "")))

    d.write(path)
    return path


def write_springback(m: Mesh, bhf: float) -> str:
    tag = f"springback_bhf{bhf:g}"
    path = os.path.join(MODELS, tag + ".k")
    n0, nx_, ny_ = m.spring_nodes

    d = Deck(f"U-channel springback, {GRADE} t={THICK:g}mm, BHF={bhf:g} kN")
    d.note(
        "implicit static release of the drawn blank\n"
        f"run forming_bhf{bhf:g}.k first, then copy its dynain next to this deck\n"
        "rigid body modes are removed by a three-node minimal constraint,\n"
        "not by clamping an edge - clamping would suppress the sidewall\n"
        "curl this model exists to measure")

    d.kw("CONTROL_TERMINATION",
         (("endtim", "endcyc", "dtmin", "endeng", "endmas", "nosol"),
          (1.0, 0, 0.0, 0.0, 0.0, 0)))
    d.kw("CONTROL_IMPLICIT_GENERAL",
         (("imflag", "dt0", "imform", "nsbs", "igso", "cnstn", "form", "zero_v"),
          (1, 0.1, 2, 1, 0, 0, 0, 0)))
    d.kw("CONTROL_IMPLICIT_AUTO",
         (("iauto", "iteopt", "itewin", "dtmin", "dtmax", "dtexp", "kfail", "kcycle"),
          (1, 11, 5, 0.001, 0.1, 0.0, 0, 0)))
    d.kw("CONTROL_IMPLICIT_SOLUTION",
         (("nsolvr", "ilimit", "maxref", "dctol", "ectol", "rctol", "lstol", "abstol"),
          (12, 11, 55, 0.001, 0.01, 1.0e10, 0.9, 1.0e-10)),
         (("dnorm", "diverg", "istif", "nlprint", "nlnorm", "d3itctl", "cpchk"),
          (2, 1, 1, 2, 4, 0, 0)),
         (("arcctl", "arcdir", "arclen", "arcmth", "arcdmp", "arcpsi", "arcalf", "arctim"),
          (0, 0, 0.0, 1, 2, 0.0, 0.0, 0.0)))
    d.kw("CONTROL_IMPLICIT_SOLVER",
         (("lsolvr", "lprint", "negev", "order", "drcm", "drcprm", "autospc", "aspctol"),
          (2, 0, 2, 0, 4, 0.0, 1, 0.0)))
    d.kw("CONTROL_SHELL",
         (("wrpang", "esort", "irnxx", "istupd", "theory", "bwc", "miter", "proj"),
          (20.0, 1, -1, 1, 2, 2, 1, 0)))
    d.kw("DATABASE_BINARY_D3PLOT",
         (("dt", "lcdt", "beam", "npltc", "psetid"), (0.1, 0, 0, 0, 0)))
    d.kw("DATABASE_GLSTAT", (("dt", "binary"), (0.05, 3)))
    d.kw("DATABASE_NODOUT", (("dt", "binary"), (0.05, 3)))

    # deformed mesh, thickness and residual stress come in from the
    # forming run
    d.include("dynain")

    d.part(PID_BLANK, SID_BLANK, MID_BLANK, f"blank {GRADE}", hgid=HGID)
    d.lines.append("*SECTION_SHELL_TITLE")
    d.lines.append("blank, type 16, 7 integration points through thickness")
    d.cards(
        (("secid", "elform", "shrf", "nip", "propt", "qr/irid", "icomp", "setyp"),
         (SID_BLANK, 16, 0.8333, 7, 1.0, 0.0, 0, 1)),
        (("t1", "t2", "t3", "t4"), (THICK,) * 4))
    mat.add_hourglass(d, HGID)
    g = mat.GRADES[GRADE]
    d.define_curve(LC_FLOW, mat.swift_curve(g["K"], g["eps0"], g["n"], g["sy"]),
                   title=f"{GRADE} flow curve [GPa]")
    mat.add_mat36(d, MID_BLANK, GRADE, LC_FLOW)

    d.kw("BOUNDARY_SPC_NODE",
         (("nid", "cid", "dofx", "dofy", "dofz", "dofrx", "dofry", "dofrz"),
          (n0, 0, 1, 1, 1, 0, 0, 0)),
         (("nid", "cid", "dofx", "dofy", "dofz", "dofrx", "dofry", "dofrz"),
          (nx_, 0, 0, 1, 1, 0, 0, 0)),
         (("nid", "cid", "dofx", "dofy", "dofz", "dofrx", "dofry", "dofrz"),
          (ny_, 0, 0, 0, 1, 0, 0, 0)))
    d.kw("INTERFACE_SPRINGBACK_LSDYNA",
         (("psid", "nshv", "ftype", "ftensr", "nthhsv", "rflag", "intstrn", "optc"),
          (PSID_BLANK, 0, 0, 0, 0, 0, 0, "")))
    d.kw("SET_PART_LIST", (PSID_BLANK, 0.0, 0.0, 0.0, 0.0), (PID_BLANK,))

    d.write(path)
    return path


def main():
    os.makedirs(MODELS, exist_ok=True)
    for stale in glob.glob(os.path.join(MODELS, "*.k")):
        os.remove(stale)
    m = build_mesh()
    # one mesh include shared by every load case, the way a production
    # deck is organised: the geometry is identical across the sweep, so
    # committing three copies of it would be three chances to diverge
    md = Deck("U-channel draw: blank and tool mesh")
    md.note("generated by 03_deepdraw_springback/build.py - do not hand edit\n"
            + m.summary())
    m.emit(md)
    md.write(os.path.join(MODELS, "mesh.k"))
    print("mesh:", m.summary())
    print("springback constraint nodes:", m.spring_nodes)
    for bhf in BHF_CASES:
        print("wrote", os.path.relpath(write_forming(m, bhf), HERE))
        print("wrote", os.path.relpath(write_springback(m, bhf), HERE))


if __name__ == "__main__":
    main()
