"""Banana-shaped cookie cutter -> model.stl (binary, millimeters).

Pure geometry, no voxels: the banana outline is traced from
examples/banana_silhouette.png and simplified. The cutter wall is a
teardrop cross-section (pointed bottom edge, rounded top) swept along
the outline -> crisp knife edge, smooth faces.

Run from the project root:  python examples/banana_cutter.py
"""
import numpy as np
import trimesh
import shapely
from shapely.geometry import Polygon
from skimage import io, measure

# --- parameters ---
SIZE = 95.0         # longest dimension of the cutter, mm
WT = 1.6            # cutter wall thickness
H = 14.0            # cutter height
TAPER_H = 4.0       # height of the pointed blade part
N_PATH = 720        # samples along the outline

t = WT / 2

# --- trace the silhouette ---
img = io.imread("examples/banana_silhouette.png", as_gray=True)
mask = img < 0.5
contour = max(measure.find_contours(mask.astype(float), 0.5), key=len)
xy = np.stack([contour[:, 1], -contour[:, 0]], axis=1)   # x right, y up

banana = Polygon(xy).buffer(0).simplify(1.0)
if banana.geom_type != "Polygon":
    banana = max(banana.geoms, key=lambda p: p.area)

# scale to SIZE and center on the origin
b = banana.bounds
s = SIZE / max(b[2] - b[0], b[3] - b[1])
cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
banana = shapely.affinity.scale(banana, s, s, origin=(0, 0))
ring = shapely.affinity.translate(banana, -cx * s, -cy * s).exterior

# resample outline to N_PATH evenly spaced points
seg = np.linspace(0, ring.length, N_PATH, endpoint=False)
pts = np.array([ring.interpolate(s2).coords[0] for s2 in seg])

# smooth resampled curve (closes tiny polygonization kinks)
for _ in range(8):
    pts = (np.roll(pts, 2, axis=0) + np.roll(pts, 1, axis=0) * 4 + pts * 6
           + np.roll(pts, -1, axis=0) * 4 + np.roll(pts, -2, axis=0)) / 16

# --- teardrop profile (u across the wall, z up): point -> blade -> round top ---
arc = [(t * np.cos(a), H - t + t * np.sin(a))
       for a in np.linspace(0, np.pi, 25)[1:-1]]   # endpoints already in profile
prof = np.array([(0.0, 0.0), (t, TAPER_H), (t, H - t), *arc,
                 (-t, H - t), (-t, TAPER_H)])
M = len(prof)

# --- sweep the profile along the outline ---
tan = np.roll(pts, -1, axis=0) - np.roll(pts, 1, axis=0)
tan /= np.linalg.norm(tan, axis=1, keepdims=True)
nrm = np.stack([-tan[:, 1], tan[:, 0]], axis=1)

verts = np.empty((N_PATH * M, 3))
verts[:, 0] = (pts[:, None, 0] + nrm[:, None, 0] * prof[None, :, 0]).ravel()
verts[:, 1] = (pts[:, None, 1] + nrm[:, None, 1] * prof[None, :, 0]).ravel()
verts[:, 2] = np.tile(prof[:, 1], N_PATH)

i = np.arange(N_PATH)
j = np.arange(M)
a = (i[:, None] * M + j[None, :])
b = ((i[:, None] + 1) % N_PATH) * M + j[None, :]
c = ((i[:, None] + 1) % N_PATH) * M + (j[None, :] + 1) % M
d = i[:, None] * M + (j[None, :] + 1) % M
faces = np.concatenate([np.stack([a, b, c], -1).reshape(-1, 3),
                        np.stack([a, c, d], -1).reshape(-1, 3)])

mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
mesh.fix_normals()
print("watertight:", mesh.is_watertight, "| triangles:", len(mesh.faces))
mesh.export("model.stl")
print("wrote model.stl")
