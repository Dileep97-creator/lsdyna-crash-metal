"""
Material library - unit system mm / ms / kg / kN / GPa.

  length   mm
  time     ms
  mass     kg
  force    kN
  stress   GPa
  density  kg/mm^3   (steel = 7.85e-6)
  energy   kN-mm = J
  velocity mm/ms = m/s

This is the standard automotive crash unit set. Using it consistently is
half the battle: most "the model exploded" tickets are a units mistake.

IMPORTANT: the flow curves below are representative published-range
values for the grades named. They are here so the models run and so the
workflow is demonstrable end to end. Replace them with your own tensile
data before quoting any number as a material result.
"""

from __future__ import annotations

import math

from kfile import Deck

RHO_STEEL = 7.85e-6      # kg/mm^3
E_STEEL = 210.0          # GPa
NU_STEEL = 0.30
RHO_AL = 2.70e-6
E_AL = 70.0
NU_AL = 0.33


def swift_curve(K, eps0, n, sig_y, eps_max=1.2, npts=40):
    """Swift/Krupkowski hardening, returned as (eff. plastic strain, yield
    stress) pairs suitable for *DEFINE_CURVE fed to MAT_024 LCSS."""
    pts = []
    for i in range(npts + 1):
        ep = eps_max * (i / npts) ** 1.5
        s = K * (eps0 + ep) ** n
        pts.append((ep, max(s, sig_y)))
    return pts


def voce_curve(sig0, Q, b, eps_max=1.2, npts=40):
    pts = []
    for i in range(npts + 1):
        ep = eps_max * (i / npts) ** 1.5
        pts.append((ep, sig0 + Q * (1.0 - math.exp(-b * ep))))
    return pts


# grade -> (K [GPa], eps0, n, sigma_y [GPa], R00, R45, R90)
GRADES = {
    # dual-phase steel, typical crash-box / longitudinal member material
    "DP600": dict(K=1.030, eps0=0.0035, n=0.165, sy=0.360,
                  r=(0.90, 0.95, 1.00), C=0.0, p=0.0),
    # micro-alloyed HSLA, common in cross members
    "HC340LA": dict(K=0.740, eps0=0.0045, n=0.170, sy=0.355,
                    r=(0.95, 0.90, 1.10), C=0.0, p=0.0),
    # mild deep-drawing steel, forming study
    "DC04": dict(K=0.530, eps0=0.0070, n=0.230, sy=0.180,
                 r=(1.80, 1.45, 2.10), C=0.0, p=0.0),
    # 6xxx extrusion alloy, aluminium crash box variant
    "AA6060-T6": dict(K=0.250, eps0=0.0020, n=0.120, sy=0.180,
                      r=(0.65, 0.75, 0.70), C=0.0, p=0.0),
}


def cowper_symonds(grade):
    """Strain-rate parameters for MAT_024 (C, p). Rate sensitivity of
    aluminium is negligible, DP/HSLA steels are not."""
    return {"DP600": (1.0e4, 5.0),        # 1/s converted below
            "HC340LA": (8.0e3, 5.0),
            "DC04": (4.0e3, 5.0),
            "AA6060-T6": (0.0, 0.0)}[grade]


def add_mat24(deck: Deck, mid: int, grade: str, lcss: int,
              rate: bool = True, fail: float = 0.0) -> Deck:
    """*MAT_PIECEWISE_LINEAR_PLASTICITY with a tabulated flow curve."""
    g = GRADES[grade]
    rho = RHO_AL if grade.startswith("AA") else RHO_STEEL
    E = E_AL if grade.startswith("AA") else E_STEEL
    nu = NU_AL if grade.startswith("AA") else NU_STEEL
    C, p = cowper_symonds(grade) if rate else (0.0, 0.0)
    # C is quoted in 1/s in the literature; time unit here is ms
    C_ms = C / 1000.0 if C else 0.0
    deck.lines.append("*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE")
    deck.lines.append(f"{grade} (representative flow curve)")
    deck.cards((("mid", "ro", "e", "pr", "sigy", "etan", "fail", "tdel"),
                 (mid, rho, E, nu, g["sy"], 0.0, fail, 0.0)),
            (("c", "p", "lcss", "lcsr", "vp"),
             (C_ms, p, lcss, 0, 1.0)),
            (("eps1", "eps2", "eps3", "eps4", "eps5", "eps6", "eps7", "eps8"),
             (0.0,) * 8),
            (("es1", "es2", "es3", "es4", "es5", "es6", "es7", "es8"),
             (0.0,) * 8))
    # kw() emitted a stray "*" line for the empty name - drop it
    return deck


def add_mat36(deck: Deck, mid: int, grade: str, lcid: int) -> Deck:
    """*MAT_3-PARAMETER_BARLAT - planar anisotropy via Lankford values.
    This is the standard sheet-forming material model; using MAT_024 for
    a deep-drawing study is a common and visible mistake."""
    g = GRADES[grade]
    r00, r45, r90 = g["r"]
    deck.lines.append("*MAT_3-PARAMETER_BARLAT_TITLE")
    deck.lines.append(f"{grade} Barlat89 (representative)")
    deck.cards((("mid", "ro", "e", "pr", "hr", "p1", "p2", "iter"),
                 (mid, RHO_STEEL, E_STEEL, NU_STEEL, 3.0, 0.0, 0.0, 1.0)),
            (("m", "r00", "r45", "r90", "lcid", "e0", "spi", "p3"),
             (6.0, r00, r45, r90, lcid, 0.0, 0.0, 0.0)),
            (("aopt", "c", "p", "vlcid", "", "", "", ""),
             (0.0, 0.0, 0.0, 0)),
            (("xp", "yp", "zp", "a1", "a2", "a3"),
             (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
            (("v1", "v2", "v3", "d1", "d2", "d3", "beta"),
             (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)))
    return deck


def add_mat_rigid(deck: Deck, mid: int, title: str, rho=RHO_STEEL,
                  E=E_STEEL, nu=NU_STEEL,
                  cmo=0.0, con1=0, con2=0) -> Deck:
    """*MAT_RIGID. E and nu are still required - they set the contact
    stiffness of the rigid body, so they must be physical."""
    deck.lines.append("*MAT_RIGID_TITLE")
    deck.lines.append(title[:80])
    deck.cards((("mid", "ro", "e", "pr", "n", "couple", "m", "alias"),
                 (mid, rho, E, nu, 0.0, 0.0, 0.0, 0.0)),
            (("cmo", "con1", "con2"), (cmo, con1, con2)),
            (("lco/a1", "a2", "a3", "v1", "v2", "v3"),
             (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)))
    return deck


def add_gissmo(deck: Deck, mid: int, lcsdg: int, dmgexp=2.0, dcrit=0.4,
               fadexp=1.0, lcregd=0, numfip=1) -> Deck:
    """*MAT_ADD_EROSION in GISSMO mode.

    Damage accumulates non-linearly with plastic strain against a
    triaxiality-dependent failure strain curve (LCSDG), and element
    stress is faded once the critical damage DCRIT is passed. This is
    what industrial crash decks use instead of a single FAIL value on
    MAT_024, because a constant failure strain is wrong for anything
    other than the one stress state it was fitted to.
    """
    # EXCL is the "switched off" marker. Once EXCL is set, a criterion is
    # disabled ONLY if its field holds the EXCL value - a 0.0 is a live
    # criterion. Writing 0.0 here makes MNPRES = 0 active, every element
    # satisfies "pressure <= 0" on the first cycle and the whole part is
    # deleted before it touches anything (warning SOL+487 in messag).
    X = -999.0
    deck.lines.append("*MAT_ADD_EROSION_TITLE")
    deck.lines.append(f"GISSMO damage for material {mid}")
    deck.cards((("mid", "excl", "mxpres", "mneps", "effeps", "voleps",
                  "numfip", "ncs"),
                 (mid, X, X, X, X, X, float(numfip), 1.0)),
            (("mnpres", "sigp1", "sigvm", "mxeps", "epssh", "sigth",
              "impulse", "failtm"),
             (X,) * 8),
            (("idam", "dmgtyp", "lcsdg", "ecrit", "dmgexp", "dcrit",
              "fadexp", "lcregd"),
             (1, 1.0, lcsdg, 0.0, dmgexp, dcrit, fadexp, lcregd)),
            (("sizflg", "refsz", "nahsv", "lcsrs", "shrf", "biaxf",
              "lcdlim", "midfail"),
             (0.0, 0.0, 3, 0, 0.0, 0.0, 0, 0.0)))
    return deck


def add_hourglass(deck: Deck, hgid: int, ihq=4, qm=0.05) -> Deck:
    """*HOURGLASS. IHQ=4 (Flanagan-Belytschko stiffness) for shells under
    large bending; the coefficient is deliberately small so hourglass
    energy stays below the 5 % of internal energy acceptance limit rather
    than being stiffened away."""
    deck.kw("HOURGLASS",
            (("hgid", "ihq", "qm", "ibq", "q1", "q2", "qb/vdc", "qw"),
             (hgid, ihq, qm, 0, 1.5, 0.06, 0.0, 0.0)))
    return deck
