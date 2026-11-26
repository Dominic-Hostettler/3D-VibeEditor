"""Parametric open-top case -> model.stl (binary, millimeters).

Sized for a Raspberry Pi 4 (85 x 56 mm board) incl. header + jumper
cable headroom. Edit parameters below, then: python model.py
The viewer auto-reloads (~3 s) and keeps the camera.
"""
import cadquery as cq

# --- parameters (all in mm) ---
L, W, H = 145.0, 65.0, 37.5  # outer size: Pi 4 (85x56) + 50mm extension along X
WALL = 2.5                    # wall / floor thickness
R_VERT = 10.0                 # fillet: 4 outer vertical corners
R_BOT = 5.0                   # fillet: bottom perimeter loop
# inner radii derived so wall thickness stays constant: inner = outer - WALL
R_INNER_VERT = R_VERT - WALL  # 4 inner vertical corners of the cavity
R_INNER_BOT = R_BOT - WALL    # floor/wall junction inside the cavity
BOSS_R = 3.0                  # corner screw boss radius
BOSS_D = 1.6                  # pilot hole for self-tapping M2 screw
BOSS_HOLE_DEPTH = 12.0        # pilot hole depth from the top
VENT_W = 1.5                  # vent slot width
VENT_H = 24.0                 # vent slot length
VENT_N = 7                    # slots per long side
VENT_GAP = 6.0                # slot center spacing
VENT_ANGLE = 45.0             # slot tilt
VENT_X = -40.0                # slot block center along the case (head end)

# --- geometry ---
outer = cq.Workplane("XY").box(L, W, H, centered=(True, True, True))
if R_VERT:
    outer = outer.edges("|Z").fillet(R_VERT)
if R_BOT:
    outer = outer.edges("<Z").fillet(R_BOT)

# cut cavity (not shell) so inner corners stay independent of outer fillets;
# the cutter itself carries the inner-corner fillet
inner = cq.Workplane("XY").box(L - 2 * WALL, W - 2 * WALL, H,
                               centered=(True, True, True))
if R_INNER_VERT:
    inner = inner.edges("|Z").fillet(R_INNER_VERT)
if R_INNER_BOT:
    inner = inner.edges("<Z").fillet(R_INNER_BOT)
inner = inner.translate((0, 0, WALL))
case = outer.cut(inner)

# --- corner screw bosses for the lid ---
# one cylinder per inner corner, full cavity height, with a pilot hole on top
# boss centers sit on the 45-degree diagonal inside the inner corner arc:
# close enough to fuse with the wall, far enough to never reach the outer skin
boss_off = (R_VERT - 0.5 - BOSS_R) / 2 ** 0.5
bcx = (L - 2 * WALL) / 2 - R_INNER_VERT + boss_off
bcy = (W - 2 * WALL) / 2 - R_INNER_VERT + boss_off
for sx in (-1, 1):
    for sy in (-1, 1):
        boss = cq.Workplane("XY").circle(BOSS_R).extrude(H - WALL)
        boss = boss.translate((sx * bcx, sy * bcy, -H / 2 + WALL))
        case = case.union(boss)
        hole = cq.Workplane("XY").circle(BOSS_D / 2).extrude(BOSS_HOLE_DEPTH + 1)
        hole = hole.translate((sx * bcx, sy * bcy, H / 2 - BOSS_HOLE_DEPTH))
        case = case.cut(hole)

# --- ventilation slots in both long side walls ---
x0 = VENT_X - (VENT_N - 1) * VENT_GAP / 2
for i in range(VENT_N):
    for sy in (-1, 1):
        # capsule profile (rounded ends) extruded through the wall
        slot = cq.Workplane("XZ").slot2D(VENT_H, VENT_W, VENT_ANGLE).extrude(WALL + 4, both=True)
        slot = slot.translate((x0 + i * VENT_GAP, sy * (W / 2 - WALL / 2),
                               -H / 2 + WALL + (H - WALL) / 2))
        case = case.cut(slot)

cq.exporters.export(case, "model.stl")

import trimesh
import numpy as np
m = trimesh.load("model.stl")
v = m.vertices[m.faces]
area2 = np.linalg.norm(np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]), axis=1)
m.update_faces(area2 > 1e-9)  # cadquery emits degenerate tris at corner junctions
m.merge_vertices()
m.export("model.stl")
m = trimesh.load("model.stl")
assert m.is_watertight, "result is not watertight"
print(f"wrote model.stl ({len(m.faces)} triangles)")
