"""
Lightweight structured mesh generation.

Everything in this repository is meshed from script - there is no CAD
file, no proprietary pre-processor session and no binary blob in the
repo. Re-running build.py reproduces the exact model, which is the
whole point: a reviewer can regenerate and re-run it themselves.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from kfile import Deck, fmt, comment, card


@dataclass
class Mesh:
    nodes: dict = field(default_factory=dict)          # nid -> (x, y, z)
    shells: list = field(default_factory=list)         # (eid, pid, n1..n4)
    solids: list = field(default_factory=list)         # (eid, pid, n1..n8)
    node_sets: dict = field(default_factory=dict)      # sid -> [nid]
    part_sets: dict = field(default_factory=dict)
    _nid: int = 0
    _eid: int = 0

    # -- creation --------------------------------------------------------
    def node(self, x, y, z, tc=0, rc=0) -> int:
        self._nid += 1
        self.nodes[self._nid] = (float(x), float(y), float(z), tc, rc)
        return self._nid

    def quad(self, pid, n1, n2, n3, n4) -> int:
        self._eid += 1
        self.shells.append((self._eid, pid, n1, n2, n3, n4))
        return self._eid

    def hex8(self, pid, n) -> int:
        self._eid += 1
        self.solids.append((self._eid, pid, *n))
        return self._eid

    # -- structured grids ------------------------------------------------
    def grid(self, ni, nj, f, wrap_i=False):
        """Create an (ni x nj) node grid from f(i, j) -> (x, y, z).

        wrap_i=True reuses column 0 as column ni, which is how the closed
        cross-section of a tube is built without duplicate nodes on the
        seam.
        """
        ids = [[0] * nj for _ in range(ni)]
        for i in range(ni):
            for j in range(nj):
                ids[i][j] = self.node(*f(i, j))
        if wrap_i:
            ids.append(ids[0])
        return ids

    def quads_from_grid(self, ids, pid):
        ni, nj = len(ids), len(ids[0])
        out = []
        for i in range(ni - 1):
            for j in range(nj - 1):
                out.append(self.quad(pid, ids[i][j], ids[i + 1][j],
                                     ids[i + 1][j + 1], ids[i][j + 1]))
        return out

    # -- selection -------------------------------------------------------
    def pick(self, test) -> list:
        return [nid for nid, p in self.nodes.items() if test(p[0], p[1], p[2])]

    def add_node_set(self, sid, nids):
        self.node_sets[sid] = list(nids)
        return sid

    def bbox(self):
        xs = [p[0] for p in self.nodes.values()]
        ys = [p[1] for p in self.nodes.values()]
        zs = [p[2] for p in self.nodes.values()]
        return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

    # -- output ----------------------------------------------------------
    def emit(self, deck: Deck) -> Deck:
        deck.lines.append("*NODE")
        deck.lines.append("$#   nid               x               y               z      tc      rc")
        for nid, (x, y, z, tc, rc) in self.nodes.items():
            deck.lines.append(
                fmt(nid, 8) + fmt(x, 16) + fmt(y, 16) + fmt(z, 16)
                + fmt(tc, 8) + fmt(rc, 8))
        if self.shells:
            deck.lines.append("*ELEMENT_SHELL")
            deck.lines.append("$#   eid     pid      n1      n2      n3      n4")
            for eid, pid, a, b, c, d in self.shells:
                deck.lines.append("".join(fmt(v, 8) for v in (eid, pid, a, b, c, d)))
        if self.solids:
            deck.lines.append("*ELEMENT_SOLID")
            for eid, pid, *n in self.solids:
                deck.lines.append("".join(fmt(v, 8) for v in (eid, pid)))
                deck.lines.append("".join(fmt(v, 8) for v in n))
        for sid, nids in self.node_sets.items():
            deck.lines.append("*SET_NODE_LIST")
            deck.lines.append(card(sid, 0.0, 0.0, 0.0, 0.0))
            for k in range(0, len(nids), 8):
                deck.lines.append(card(*nids[k:k + 8]))
        return deck

    def summary(self) -> str:
        (x0, x1), (y0, y1), (z0, z1) = self.bbox()
        return (f"{len(self.nodes)} nodes, {len(self.shells)} shells, "
                f"{len(self.solids)} solids | bbox "
                f"x[{x0:.1f},{x1:.1f}] y[{y0:.1f},{y1:.1f}] z[{z0:.1f},{z1:.1f}]")


# ---------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------

def rounded_rect_path(width, height, radius, n_per_side, n_per_corner):
    """Closed polyline around a rectangle with filleted corners.

    Sharp corners in a thin-walled crush tube concentrate hourglass energy
    and bias the fold pattern, so the corners are filleted properly.
    Returns a list of (x, y) with no duplicate closing point.
    """
    a, b, r = width / 2.0, height / 2.0, radius
    pts = []
    corners = [(a - r, b - r, 0.0), (-(a - r), b - r, math.pi / 2),
               (-(a - r), -(b - r), math.pi), (a - r, -(b - r), 1.5 * math.pi)]
    straights = [
        ((a, b - r), (a, -(b - r))),      # right edge, downward - built later
    ]
    # walk: right edge up, top-right corner, top edge, ... counter-clockwise
    def arc(cx, cy, t0):
        for k in range(n_per_corner + 1):
            t = t0 + (math.pi / 2) * k / n_per_corner
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))

    def line(p0, p1, n):
        for k in range(n):
            s = k / n
            pts.append((p0[0] + (p1[0] - p0[0]) * s,
                        p0[1] + (p1[1] - p0[1]) * s))

    line((a, -(b - r)), (a, b - r), n_per_side)
    arc(a - r, b - r, 0.0)
    pts.pop()
    line((a - r, b), (-(a - r), b), n_per_side)
    arc(-(a - r), b - r, math.pi / 2)
    pts.pop()
    line((-a, b - r), (-a, -(b - r)), n_per_side)
    arc(-(a - r), -(b - r), math.pi)
    pts.pop()
    line((-(a - r), -b), (a - r, -b), n_per_side)
    arc(a - r, -(b - r), 1.5 * math.pi)
    pts.pop()
    # remove duplicate of the very first point if the walk closed onto it
    if abs(pts[-1][0] - pts[0][0]) < 1e-9 and abs(pts[-1][1] - pts[0][1]) < 1e-9:
        pts.pop()
    return pts


def dogbone_halfwidth(x, w_grip, w_gauge, l_gauge, r_fillet):
    """Half-width of a flat tensile coupon at station x (x = 0 at the
    specimen centre). The shoulder is a true circular fillet of radius
    r_fillet, which must exceed the shoulder depth so that the arc meets
    the grip edge at a finite slope - otherwise no mesh grading can save
    the elements there."""
    dep = (w_grip - w_gauge) / 2.0
    if r_fillet <= dep:
        raise ValueError("fillet radius must exceed the shoulder depth")
    a = math.sqrt(r_fillet ** 2 - (r_fillet - dep) ** 2)
    d = abs(x) - l_gauge / 2.0
    if d <= 0.0:
        return w_gauge / 2.0
    if d >= a:
        return w_grip / 2.0
    return w_gauge / 2.0 + r_fillet - math.sqrt(r_fillet ** 2 - d ** 2)


def notched_halfwidth(x, w_grip, w_min, r_notch):
    """Half-width of a coupon with one circular notch machined into each
    edge. Notch depth is set by w_grip - w_min and must be smaller than
    the notch radius."""
    dep = (w_grip - w_min) / 2.0
    if r_notch <= dep:
        raise ValueError("notch radius must exceed the notch depth")
    a = math.sqrt(r_notch ** 2 - (r_notch - dep) ** 2)
    if abs(x) >= a:
        return w_grip / 2.0
    return w_grip / 2.0 - dep + r_notch - math.sqrt(r_notch ** 2 - x ** 2)


def profiled_strip(m: Mesh, pid: int, length: float, halfwidth,
                   h: float, ny: int):
    """Structured shell mesh of a flat coupon whose half-width is given by
    the callable halfwidth(x), x running from -length/2 to +length/2.

    Node columns are spaced by arc length along the free edge rather than
    by equal x, so columns cluster where the profile actually turns. The
    edge slope is capped before it enters the metric: pure arc-length
    grading collapses dx towards zero at a steep shoulder, which trades a
    skewed element for a slivered one. Capping bounds the clustering at
    sqrt(1 + SMAX^2) relative to uniform spacing.
    """
    SMAX = 2.0
    ns = 4000
    xs = [-length / 2.0 + length * k / ns for k in range(ns + 1)]
    hw = [halfwidth(x) for x in xs]
    s = [0.0]
    for k in range(ns):
        dx = xs[k + 1] - xs[k]
        slope = min(abs(hw[k + 1] - hw[k]) / dx, SMAX)
        s.append(s[-1] + dx * math.sqrt(1.0 + slope * slope))
    total = s[-1]
    nx = max(4, int(round(total / h)))

    stations, k = [], 0
    for i in range(nx + 1):
        target = total * i / nx
        while k < ns and s[k + 1] < target:
            k += 1
        if k >= ns:
            stations.append(xs[-1])
            continue
        seg = s[k + 1] - s[k]
        f = 0.0 if seg <= 0 else (target - s[k]) / seg
        stations.append(xs[k] + f * (xs[k + 1] - xs[k]))

    def f(i, j):
        x = stations[i]
        w = halfwidth(x)
        return (x, -w + 2.0 * w * j / ny, 0.0)

    ids = m.grid(nx + 1, ny + 1, f)
    m.quads_from_grid(ids, pid)
    return ids


def drop_elements(m: Mesh, pred) -> int:
    """Delete shells whose centroid satisfies pred(x, y, z). Used to cut
    the slots of the in-plane shear coupon out of a plain grid."""
    keep, removed = [], 0
    for e in m.shells:
        eid, pid, *conn = e
        pts = [m.nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / 4.0
        cy = sum(p[1] for p in pts) / 4.0
        cz = sum(p[2] for p in pts) / 4.0
        if pred(cx, cy, cz):
            removed += 1
        else:
            keep.append(e)
    m.shells = keep
    return removed


def prune_unused_nodes(m: Mesh) -> int:
    used = set()
    for _, _, *conn in m.shells:
        used.update(conn)
    for _, _, *conn in m.solids:
        used.update(conn)
    for nids in m.node_sets.values():
        used.update(nids)
    drop = [n for n in m.nodes if n not in used]
    for n in drop:
        del m.nodes[n]
    return len(drop)


def swept_profile(m: Mesh, pid: int, profile_xz, y0: float, y1: float,
                  ny: int):
    """Sweep a 2D (x, z) polyline along y to build a tool surface.

    Forming tools in a 2D draw-bend are prismatic, so the whole die,
    punch and blankholder set can be described by three polylines and
    extruded. Keeps the tools exactly consistent with the nominal
    geometry instead of depending on an imported CAD surface.
    """
    def f(i, j):
        x, z = profile_xz[i]
        return (x, y0 + (y1 - y0) * j / ny, z)
    ids = m.grid(len(profile_xz), ny + 1, f)
    m.quads_from_grid(ids, pid)
    return ids


def polyline_line(p0, p1, ds):
    """Points along a straight segment at spacing ~ds, excluding the end."""
    import math as _m
    n = max(1, int(round(_m.dist(p0, p1) / ds)))
    return [(p0[0] + (p1[0] - p0[0]) * k / n,
             p0[1] + (p1[1] - p0[1]) * k / n) for k in range(n)]


def polyline_arc(cx, cz, r, a0, a1, ds):
    """Points along a circular arc at spacing ~ds, excluding the end.
    Angles in radians, measured in the x-z plane."""
    import math as _m
    n = max(1, int(round(abs(a1 - a0) * r / ds)))
    return [(cx + r * _m.cos(a0 + (a1 - a0) * k / n),
             cz + r * _m.sin(a0 + (a1 - a0) * k / n)) for k in range(n)]
