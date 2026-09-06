#!/usr/bin/env python3
"""
Shell mesh quality report straight off a keyword file.

Checks the four things that actually decide whether an explicit crash
run behaves: degenerate/duplicate connectivity, aspect ratio, internal
angle, and the critical timestep of the worst element (which is what
sets the cost of the run and how much mass scaling you are about to
add).

    python3 tools/mesh_quality.py 01_crashbox_axial/models/mesh_h5.k
"""

from __future__ import annotations

import math
import sys

C_STEEL = 5172.0   # mm/ms, elastic wave speed of steel in this unit set


def read_mesh(path):
    nodes, shells = {}, []
    kw = None
    for raw in open(path):
        line = raw.rstrip("\n")
        if not line.strip() or line.startswith("$"):
            continue
        if line.startswith("*"):
            kw = line.strip().upper()
            continue
        if kw == "*NODE":
            nid = int(line[0:8])
            nodes[nid] = (float(line[8:24]), float(line[24:40]), float(line[40:56]))
        elif kw and kw.startswith("*ELEMENT_SHELL"):
            v = [line[i:i + 8].strip() for i in range(0, 48, 8)]
            if v[0].isdigit():
                shells.append(tuple(int(x) for x in v[:6]))
    return nodes, shells


def edge_lengths(p):
    return [math.dist(p[i], p[(i + 1) % 4]) for i in range(4)]


def angles(p):
    out = []
    for i in range(4):
        a, b, c = p[(i - 1) % 4], p[i], p[(i + 1) % 4]
        u = [a[k] - b[k] for k in range(3)]
        v = [c[k] - b[k] for k in range(3)]
        nu = math.dist(a, b) or 1e-12
        nv = math.dist(c, b) or 1e-12
        cos = sum(u[k] * v[k] for k in range(3)) / (nu * nv)
        out.append(math.degrees(math.acos(max(-1.0, min(1.0, cos)))))
    return out


def area(p):
    def tri(a, b, c):
        u = [b[k] - a[k] for k in range(3)]
        v = [c[k] - a[k] for k in range(3)]
        cr = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
              u[0] * v[1] - u[1] * v[0])
        return 0.5 * math.sqrt(sum(x * x for x in cr))
    return tri(p[0], p[1], p[2]) + tri(p[0], p[2], p[3])


def warpage(p):
    """Deviation of the 4th node from the plane of the first three,
    normalised by the average edge length."""
    u = [p[1][k] - p[0][k] for k in range(3)]
    v = [p[2][k] - p[0][k] for k in range(3)]
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
         u[0] * v[1] - u[1] * v[0])
    ln = math.sqrt(sum(x * x for x in n)) or 1e-12
    w = [p[3][k] - p[0][k] for k in range(3)]
    d = abs(sum(w[k] * n[k] for k in range(3))) / ln
    return d / (sum(edge_lengths(p)) / 4.0)


def report(path, c=C_STEEL):
    nodes, shells = read_mesh(path)
    if not shells:
        print(f"{path}: no shell elements found")
        return
    worst = {"aspect": (0, None), "angle": (90.0, None),
             "warp": (0.0, None), "dt": (1e30, None), "area": (1e30, None)}
    degenerate, tri = [], 0
    for eid, pid, *conn in shells:
        if len(set(conn)) < 4:
            tri += 1
            if len(set(conn)) < 3:
                degenerate.append(eid)
            continue
        p = [nodes[n] for n in conn]
        el = edge_lengths(p)
        ar = max(el) / max(min(el), 1e-12)
        an = angles(p)
        wp = warpage(p)
        a = area(p)
        # LS-DYNA shell timestep: characteristic length / wave speed
        dt = (a / max(el)) / c
        if ar > worst["aspect"][0]:
            worst["aspect"] = (ar, eid)
        mn = min(min(an), 180.0 - max(an))
        if mn < worst["angle"][0]:
            worst["angle"] = (mn, eid)
        if wp > worst["warp"][0]:
            worst["warp"] = (wp, eid)
        if dt < worst["dt"][0]:
            worst["dt"] = (dt, eid)
        if a < worst["area"][0]:
            worst["area"] = (a, eid)

    print(f"\n{path}")
    print(f"  elements            {len(shells)} ({tri} triangles)")
    print(f"  worst aspect ratio  {worst['aspect'][0]:.2f}   (elem {worst['aspect'][1]})")
    print(f"  worst corner angle  {worst['angle'][0]:.1f} deg (elem {worst['angle'][1]})")
    print(f"  worst warpage       {worst['warp'][0]:.4f}  (elem {worst['warp'][1]})")
    print(f"  smallest area       {worst['area'][0]:.3f} mm2")
    print(f"  critical timestep   {worst['dt'][0]*1e3:.4f} us (elem {worst['dt'][1]})")
    flags = []
    if degenerate:
        flags.append(f"{len(degenerate)} degenerate elements")
    if worst["aspect"][0] > 5.0:
        flags.append("aspect ratio > 5")
    if worst["angle"][0] < 30.0:
        flags.append("corner angle < 30 deg")
    if worst["warp"][0] > 0.05:
        flags.append("warpage > 5%")
    print("  status              " + ("OK" if not flags else "; ".join(flags)))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    for p in sys.argv[1:]:
        report(p)
