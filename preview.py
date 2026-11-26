"""Render a quick preview PNG of model.stl (or a given STL) for self-checking.
Usage: python preview.py [file.stl] [elev azim]
"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

path = sys.argv[1] if len(sys.argv) > 1 else "model.stl"
elev = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
azim = float(sys.argv[3]) if len(sys.argv) > 3 else -60.0

m = trimesh.load(path)
if len(m.faces) > 20000:
    m = m.simplify_quadric_decimation(0.9)
b = m.bounds
span = (b[1] - b[0]).max()

fig = plt.figure(figsize=(9, 7), facecolor="#222")
ax = fig.add_subplot(111, projection="3d", facecolor="#222")
ax.add_collection3d(Poly3DCollection(m.triangles, facecolor="#7d9bd6",
                                     edgecolor="none"))
c = (b[0] + b[1]) / 2
ax.set_xlim(c[0] - span * 0.7, c[0] + span * 0.7)
ax.set_ylim(c[1] - span * 0.7, c[1] + span * 0.7)
ax.set_zlim(c[2] - span * 0.7, c[2] + span * 0.7)
ax.view_init(elev=elev, azim=azim)
ax.set_axis_off()
plt.savefig("_preview.png", dpi=110, bbox_inches="tight")
print("saved _preview.png")
