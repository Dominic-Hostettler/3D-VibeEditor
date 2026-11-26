"""Starter model -> model.stl (binary, millimeters).

Edit parameters below, then: python model.py
The viewer auto-reloads (~3 s) and keeps the camera.

Examples to grow from:
  examples/case.py    - cadquery open-top case (fillets, bosses, vents)
  examples/dragon.py  - implicit SDF modeling (organic shapes)
"""
import trimesh

# --- parameters (all in mm) ---
L, W, H = 40.0, 40.0, 20.0    # outer size

box = trimesh.creation.box(extents=(L, W, H))
assert box.is_watertight
box.export("model.stl")
print(f"wrote model.stl ({len(box.faces)} triangles)")
