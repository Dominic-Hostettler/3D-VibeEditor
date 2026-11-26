import numpy as np
import trimesh
from skimage.measure import marching_cubes

# Implicitly modeled dragon head -> marching cubes -> watertight STL.
# Z is up, head faces +X. All units mm.

RES = 0.45                     # voxel size in mm
X0, X1 = -55, 65               # bounding box
Y0, Y1 = -38, 38
Z0, Z1 = -22, 62

x = np.arange(X0, X1, RES)
y = np.arange(Y0, Y1, RES)
z = np.arange(Z0, Z1, RES)
P = np.stack(np.meshgrid(x, y, z, indexing="ij"), axis=-1)  # (nx,ny,nz,3)


def smin(a, b, k):
    # polynomial smooth-min for organic blending
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def ellipsoid(c, r):
    q = (P - np.asarray(c)) / np.asarray(r)
    return (np.linalg.norm(q, axis=-1) - 1.0) * min(r)


def sphere(c, r):
    return np.linalg.norm(P - np.asarray(c), axis=-1) - r


def capsule_chain(pts, rads):
    # tapered tube along a polyline; rads has one radius per point
    pts = [np.asarray(p, float) for p in pts]
    d = np.full(P.shape[:3], 1e9)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        t = np.clip(np.sum((P - a) * ab, axis=-1) / np.dot(ab, ab), 0, 1)
        closest = a + t[..., None] * ab
        r = rads[i] * (1 - t) + rads[i + 1] * t
        d = np.minimum(d, np.linalg.norm(P - closest, axis=-1) - r)
    return d


def cone(base, tip, r):
    # pointed cone via tapered capsule
    a, b = np.asarray(base, float), np.asarray(tip, float)
    ab = b - a
    t = np.clip(np.sum((P - a) * ab, axis=-1) / np.dot(ab, ab), 0, 1)
    closest = a + t[..., None] * ab
    rad = r * (1 - t)
    return np.linalg.norm(P - closest, axis=-1) - rad


def sdiff(a, b, k):
    # smooth subtraction of shape b from field a -> rounded cut edges
    return -smin(-a, b, k)


K_BLEND = 6.0

# --- skull: cranium + snout + nose ---
field = ellipsoid((0, 0, 22), (27, 21, 24))                    # cranium
field = smin(field, ellipsoid((26, 0, 15), (26, 15, 12)), K_BLEND)   # snout
field = smin(field, sphere((47, 0, 18), 8), K_BLEND)           # nose tip
field = smin(field, ellipsoid((18, 0, 3), (27, 13, 9)), K_BLEND)     # lower jaw
field = smin(field, sphere((2, 0, 0), 7), K_BLEND)             # chin

# --- mouth: carve a slit between snout and jaw ---
mouth = ellipsoid((30, 0, 9), (30, 17, 2.0))
field = sdiff(field, mouth, 1.0)

# --- nostrils ---
for sy in (-1, 1):
    field = sdiff(field, sphere((44, sy * 5.5, 21), 3.2), 1.5)

# --- eye sockets + eyeballs ---
for sy in (-1, 1):
    field = sdiff(field, sphere((8, sy * 16, 28), 7.0), 2.5)           # socket
    field = smin(field, sphere((5, sy * 15, 28), 5.5), 4.0)            # eyeball

# --- horns: two big swept horns + smaller spikes behind them ---
for sy in (-1, 1):
    horn = capsule_chain(
        [(-6, sy * 9, 40), (-12, sy * 15, 47), (-24, sy * 19, 50),
         (-38, sy * 18, 46), (-48, sy * 12, 36)],
        [5.0, 4.2, 3.2, 2.0, 0.5])
    field = smin(field, horn, 4.0)
    spike = cone((-2, sy * 16, 42), (-16, sy * 26, 52), 2.2)
    field = smin(field, spike, 3.0)

# --- nose horn ---
field = smin(field, cone((45, 0, 24), (52, 0, 32), 2.2), 2.0)

# --- teeth: fangs + row along the mouth slit ---
for sy in (-1, 1):
    field = np.minimum(field, cone((36, sy * 6, 13), (36, sy * 6, 4), 1.8))   # fangs
for xt in np.arange(14, 47, 6.5):
    for sy in (-1, 1):
        yt = sy * (11 - 0.16 * (xt - 14))                      # follow jaw taper
        field = np.minimum(field, cone((xt, yt, 12), (xt, yt, 6), 1.3))
        if xt + 2 < 44:
            field = np.minimum(field, cone((xt + 2, yt * 0.9, 4), (xt + 2, yt * 0.9, 10.5), 1.2))

# --- dorsal crest: pointed scales along the spine ---
crest_pts = [(40, 0, 28), (30, 0, 27), (20, 0, 40),
             (8, 0, 45), (-6, 0, 44), (-18, 0, 40)]
for i, (cx, cy, cz) in enumerate(crest_pts):
    h = 7 - i * 0.4
    fin = capsule_chain([(cx, 0, cz - 1), (cx - 2.5, 0, cz + h)], [1.6, 0.3])
    field = np.minimum(field, fin)

# --- scales: subtle bumps on the snout top ---
for a in np.arange(0.0, 1.0, 0.12):
    for sy in (-1, 1):
        field = smin(field, sphere((44 - a * 14, sy * (3 + a * 5), 24 + a * 8), 1.4), 1.8)

print("field done", field.shape)
verts, faces, _, _ = marching_cubes(field, level=0.0, spacing=(RES, RES, RES))
verts += np.array([X0, Y0, Z0])
mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
mesh.update_faces(mesh.nondegenerate_faces())
print("raw watertight:", mesh.is_watertight, "| euler:", mesh.euler_number)
trimesh.smoothing.filter_laplacian(mesh, lamb=0.5, iterations=4)
mesh.fix_normals()
mesh.fill_holes()
print("watertight:", mesh.is_watertight, "| triangles:", len(mesh.faces))
mesh.export("model.stl")
print("wrote model.stl")
