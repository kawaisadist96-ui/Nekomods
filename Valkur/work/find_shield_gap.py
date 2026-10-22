"""Find the sheet of faces stretched between the shield and the thigh."""
import bpy
from mathutils import Vector

low = bpy.data.objects["Valkur_low"]
mesh = low.data
uvs = mesh.uv_layers.active.data
worst = []
for poly in mesh.polygons:
    center = Vector(poly.center)
    if center.z < 40 or center.z > 120:
        continue
    area = poly.area
    if area < 0.2:
        continue
    loops = list(poly.loop_indices)
    uv_area = 0.0
    for i in range(len(loops)):
        a = uvs[loops[i]].uv
        b = uvs[loops[(i + 1) % len(loops)]].uv
        uv_area += a.x * b.y - b.x * a.y
    uv_area = abs(uv_area) * 0.5
    stretch = uv_area / area if area else 0
    worst.append((stretch, area, tuple(round(v, 1) for v in center), poly.index, round(uv_area, 5)))

worst.sort(reverse=True)
print("STRETCHED", len(worst))
for row in worst[:25]:
    print(row)

# Faces sitting in the lateral gap, away from the torso center.
gap = []
for poly in mesh.polygons:
    center = Vector(poly.center)
    if 55 < center.z < 110 and abs(center.x) > 14 and abs(center.x) < 32 and poly.area > 1.0:
        gap.append((round(poly.area, 2), tuple(round(v, 1) for v in center), poly.index))
gap.sort(reverse=True)
print("GAP", len(gap))
for row in gap[:30]:
    print(row)
