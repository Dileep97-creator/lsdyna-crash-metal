#!/usr/bin/env python3
"""
Study 02 - GISSMO damage model calibration coupons.

A single FAIL value on *MAT_024 is only correct for the one stress state
it was fitted to. Real crash decks use a failure strain that depends on
stress triaxiality, calibrated on a set of coupons that each sit at a
different point on the failure locus. This study builds that set:

  specimen        nominal triaxiality   what it loads
  --------------------------------------------------
  shear                    0.00         pure in-plane shear ligament
  tensile (dogbone)        0.33         uniaxial tension
  notched R20              0.40         mild notch constraint
  notched R5               0.48         sharp notch constraint
  plane strain             0.58         wide grooved specimen

Each coupon is pulled quasi-statically in explicit with mass scaling,
with a virtual extensometer defined so the simulated force-displacement
curve can be overlaid on the tensile machine trace directly.

The same coupons are also emitted at three element sizes, which is what
you need to build the GISSMO mesh regularisation curve (LCREGD) - the
single most common reason a calibrated damage model does not transfer
from the coupon mesh to the 5 mm crash mesh.

Usage:
    python3 build.py
"""

from __future__ import annotations

import glob
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from kfile import Deck, card, control_explicit_crash, database_standard   # noqa: E402
from mesh import (Mesh, profiled_strip, drop_elements, prune_unused_nodes,  # noqa: E402
                  dogbone_halfwidth, notched_halfwidth)
import materials as mat                                                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "models")

GRADE = "DP600"
THICK = 1.5          # mm sheet thickness
PULL_V = 1.0         # mm/ms pull rate, ramped - quasi-static in practice
END_TIME = 8.0       # ms
ELEMENT_SIZES = [0.5, 1.0, 2.0]     # mm, for the regularisation curve

PID, SID, MID, HGID = 1, 1, 1, 1
LC_FLOW, LC_PULL = 100, 200
NS_FIX, NS_PULL, NS_EXT_A, NS_EXT_B = 10, 11, 12, 13


# ------------------------------------------------------------------ coupons
def coupon_shear(m: Mesh, h: float):
    """Rectangular strip with two offset slots leaving a shear ligament.
    Loading the ligament in-plane gives triaxiality near zero."""
    L, W = 60.0, 40.0
    nx, ny = int(L / h), int(W / h)
    ids = m.grid(nx + 1, ny + 1,
                 lambda i, j: (-L / 2 + L * i / nx, -W / 2 + W * j / ny, 0.0))
    m.quads_from_grid(ids, PID)
    slot_l, slot_w, lig = 18.0, 4.0, 6.0

    def in_slot(x, y, z):
        # upper slot runs in from the left, lower slot in from the right
        if abs(y - lig / 2 - slot_w / 2) < slot_w / 2 and x < -L / 2 + slot_l:
            return True
        if abs(y + lig / 2 + slot_w / 2) < slot_w / 2 and x > L / 2 - slot_l:
            return True
        return False

    drop_elements(m, in_slot)
    prune_unused_nodes(m)
    return dict(length=L, width=W, eta=0.0)


def coupon_tensile(m: Mesh, h: float):
    L, wg, wgauge, lg, r = 120.0, 20.0, 12.5, 50.0, 20.0
    profiled_strip(m, PID, L,
                   lambda x: dogbone_halfwidth(x, wg, wgauge, lg, r),
                   h=h, ny=max(4, int(wgauge / h)))
    return dict(length=L, width=wg, eta=1 / 3)


def coupon_notch(m: Mesh, h: float, r_notch: float, eta: float):
    L, wg, wmin = 100.0, 20.0, 10.0
    profiled_strip(m, PID, L,
                   lambda x: notched_halfwidth(x, wg, wmin, r_notch),
                   h=h, ny=max(4, int(wmin / h)))
    return dict(length=L, width=wg, eta=eta)


def coupon_plane_strain(m: Mesh, h: float):
    """Wide specimen with a shallow groove - lateral contraction is
    suppressed by the surrounding material, so the ligament sits close to
    the plane strain triaxiality of 1/sqrt(3)."""
    L, wg, wmin, r = 90.0, 40.0, 32.0, 20.0
    profiled_strip(m, PID, L,
                   lambda x: notched_halfwidth(x, wg, wmin, r),
                   h=h, ny=max(8, int(wmin / h)))
    return dict(length=L, width=wg, eta=0.577)


COUPONS = {
    "shear": (coupon_shear, {}),
    "tensile": (coupon_tensile, {}),
    "notchR20": (coupon_notch, dict(r_notch=20.0, eta=0.40)),
    "notchR10": (coupon_notch, dict(r_notch=10.0, eta=0.48)),
    "planestrain": (coupon_plane_strain, {}),
}


def write_coupon(name: str, h: float) -> str:
    fn, kwargs = COUPONS[name]
    m = Mesh()
    info = fn(m, h, **kwargs)
    L = info["length"]

    grip = 0.06 * L
    m.add_node_set(NS_FIX, m.pick(lambda x, y, z: x < -L / 2 + grip))
    m.add_node_set(NS_PULL, m.pick(lambda x, y, z: x > L / 2 - grip))
    # virtual extensometer, 25 mm gauge, mirrors the clip gauge on the rig
    m.add_node_set(NS_EXT_A, m.pick(lambda x, y, z: abs(x + 12.5) < h / 2 and abs(y) < h))
    m.add_node_set(NS_EXT_B, m.pick(lambda x, y, z: abs(x - 12.5) < h / 2 and abs(y) < h))

    tag = f"{name}_h{h:g}"
    path = os.path.join(MODELS, tag + ".k")
    d = Deck(f"{name} coupon, {GRADE}, t={THICK:g} mm, element {h:g} mm")
    d.note(
        "units: mm / ms / kg / kN / GPa\n"
        f"nominal stress triaxiality of the ligament: {info['eta']:.3f}\n"
        f"{m.summary()}\n"
        "pull one end at a ramped rate; take force from bndout/spcforc and\n"
        "extensometer displacement from the two nodout node sets.")

    d.raw(*control_explicit_crash(END_TIME, dt2ms=-2.0e-4, tssfac=0.9))
    d.raw(*database_standard(dt_ascii=0.01, dt_d3plot=0.2))
    d.kw("DATABASE_HISTORY_NODE_SET", (NS_EXT_A, NS_EXT_B, NS_PULL))

    m.emit(d)

    d.part(PID, SID, MID, f"{name} coupon", hgid=HGID)
    d.lines.append("*SECTION_SHELL_TITLE")
    d.lines.append("coupon, fully integrated, 7 through-thickness points")
    d.cards(
        (("secid", "elform", "shrf", "nip", "propt", "qr/irid", "icomp", "setyp"),
         (SID, 16, 0.8333, 7, 1.0, 0.0, 0, 1)),
        (("t1", "t2", "t3", "t4"), (THICK,) * 4))
    mat.add_hourglass(d, HGID)

    g = mat.GRADES[GRADE]
    d.define_curve(LC_FLOW, mat.swift_curve(g["K"], g["eps0"], g["n"], g["sy"]),
                   title=f"{GRADE} flow curve [GPa]")
    mat.add_mat24(d, MID, GRADE, LC_FLOW, rate=False)

    # smooth ramp to the pull rate so no stress wave is launched
    d.define_curve(LC_PULL, [(0.0, 0.0), (0.5, 0.5 * PULL_V),
                             (1.0, PULL_V), (END_TIME, PULL_V)],
                   title="pull velocity ramp [mm/ms]")

    d.kw("BOUNDARY_SPC_SET",
         (("nsid", "cid", "dofx", "dofy", "dofz", "dofrx", "dofry", "dofrz"),
          (NS_FIX, 0, 1, 1, 1, 1, 1, 1)))
    d.kw("BOUNDARY_PRESCRIBED_MOTION_SET",
         (("id", "dof", "vad", "lcid", "sf", "vid", "death", "birth"),
          (NS_PULL, 1, 0, LC_PULL, 1.0, 0, 1.0e20, 0.0)))
    # keep the pulled end from rotating or moving out of plane
    d.kw("BOUNDARY_SPC_SET",
         (("nsid", "cid", "dofx", "dofy", "dofz", "dofrx", "dofry", "dofrz"),
          (NS_PULL, 0, 0, 1, 1, 1, 1, 1)))

    d.write(path)
    return path


def main():
    os.makedirs(MODELS, exist_ok=True)
    for stale in glob.glob(os.path.join(MODELS, "*.k")):
        os.remove(stale)   # regenerate from scratch, never leave orphans
    for name in COUPONS:
        for h in ELEMENT_SIZES:
            p = write_coupon(name, h)
            print("wrote", os.path.relpath(p, HERE))


if __name__ == "__main__":
    main()
