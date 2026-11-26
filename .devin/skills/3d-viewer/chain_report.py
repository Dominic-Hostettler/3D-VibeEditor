"""Print edge-chain report for model.stl, matching the viewer's topology.

Usage (from the 3d-viewer directory):
    python chain_report.py          # all chains
    python chain_report.py 14 17    # only those chain ids

Chain IDs match index.html exactly: weld tol 1e-3, smooth-union dot>0.94,
chain merge turn angle <30 deg.
"""
import math
import struct
import sys
from collections import defaultdict

import numpy as np


def load_stl(path):
    data = open(path, "rb").read()
    n = struct.unpack("<I", data[80:84])[0]
    return np.frombuffer(
        data[84:],
        dtype=np.dtype([("n", "<f4", (3,)), ("v", "<f4", (3, 3)), ("a", "<u2")]),
    )


def main():
    stl = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith(".stl") else "model.stl"
    want = {int(a) for a in sys.argv[1:] if a.isdigit()}
    tris = load_stl(stl)
    pts = tris["v"].reshape(-1, 3)
    T = len(tris)

    _, inv = np.unique(np.round(pts, 3), axis=0, return_inverse=True)
    tv = inv.reshape(-1, 3)

    edge_tris = defaultdict(list)
    edges = {}
    edge_kv = {}
    for t in range(T):
        c = tv[t]
        for e in range(3):
            a, b = sorted((int(c[e]), int(c[(e + 1) % 3])))
            if (a, b) not in edges:
                edges[(a, b)] = len(edges)
                edge_kv[len(edges) - 1] = (a, b)
            edge_tris[(a, b)].append(t)

    v0, v1, v2 = pts[0::3], pts[1::3], pts[2::3]
    nrm = np.cross(v1 - v0, v2 - v0)
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    ln[ln == 0] = 1
    N = nrm / ln

    parent = list(range(T))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for ts in edge_tris.values():
        if len(ts) == 2 and float(N[ts[0]] @ N[ts[1]]) > 0.94:
            parent[find(ts[0])] = find(ts[1])

    comp = defaultdict(list)
    for t in range(T):
        comp[find(t)].append(t)
    face_of = {}
    for i, ts in enumerate(comp.values()):
        for t in ts:
            face_of[t] = i

    hard = {}
    for k, ts in edge_tris.items():
        eid = edges[k]
        hard[eid] = not (len(ts) == 2 and face_of[ts[0]] == face_of[ts[1]])

    vedges = defaultdict(list)
    for (a, b), eid in edges.items():
        if hard[eid]:
            vedges[a].append(eid)
            vedges[b].append(eid)

    corner_vid = inv.reshape(-1)
    vp = {}
    for ci, v in enumerate(corner_vid):
        if v not in vp:
            vp[v] = pts[ci]

    def unit(eid, frm):
        a, b = edge_kv[eid]
        p, q = (a, b) if a == frm else (b, a)
        d = vp[q] - vp[p]
        return d / np.linalg.norm(d)

    COS = math.cos(math.radians(30))
    visited = set()
    chains = []
    for s in range(len(edges)):
        if not hard[s] or s in visited:
            continue
        a, b = edge_kv[s]
        members = [s]
        visited.add(s)
        cverts = {a, b}
        closed = False
        for end in (a, b):
            if closed:
                break
            other = b if end == a else a
            cur, ind = end, unit(s, other)
            while True:
                best, bc = None, -2
                for e2 in vedges.get(cur, []):
                    if e2 in visited:
                        continue
                    od = unit(e2, cur)
                    c = float(od @ ind)
                    if c > bc:
                        bc, best = c, e2
                if best is None or bc < COS:
                    break
                visited.add(best)
                members.append(best)
                ea, eb = edge_kv[best]
                nxt = eb if ea == cur else ea
                ind = unit(best, cur)
                cur = nxt
                if cur in cverts:
                    closed = True
                    break
                cverts.add(cur)
        vcount = defaultdict(int)
        for m in members:
            for v in edge_kv[m]:
                vcount[v] += 1
        ends = [v for v, c in vcount.items() if c == 1]
        length = sum(
            float(np.linalg.norm(vp[edge_kv[m][1]] - vp[edge_kv[m][0]]))
            for m in members
        )
        chains.append({
            "id": len(chains), "n": len(members), "length": length,
            "closed": closed, "ends": ends,
        })

    print(f"faces: {len(comp)}  chains: {len(chains)}")
    if not want:
        for i, ts in enumerate(comp.values()):
            ts = np.array(ts)
            tri_area = np.linalg.norm(
                np.cross(v1[ts] - v0[ts], v2[ts] - v0[ts]), axis=1) / 2
            mn = N[ts].mean(axis=0)
            mn /= np.linalg.norm(mn)
            center = tris["v"].reshape(T, 9)[ts].mean(axis=0)
            print(
                f"F{i}: tris={len(ts)} area={tri_area.sum():.1f}mm2 "
                f"normal=({mn[0]:.2f},{mn[1]:.2f},{mn[2]:.2f}) "
                f"center=({center[0]:.1f},{center[1]:.1f},{center[2]:.1f})"
            )
    for ch in chains:
        if want and ch["id"] not in want:
            continue
        pts_s = [tuple(np.round(vp[v], 2)) for v in ch["ends"]]
        print(
            f"E{ch['id']}: len={ch['length']:.2f}mm segs={ch['n']} "
            f"closed={ch['closed']} ends={pts_s}"
        )


if __name__ == "__main__":
    main()
