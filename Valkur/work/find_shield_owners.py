"""See which bones own the faces between the shield and the thigh."""
import bpy
from mathutils import Vector

low = bpy.data.objects["Valkur_low"]
mesh = low.data
names = {group.index: group.name for group in low.vertex_groups}

def dominant(vertex_index):
    best = (0.0, -1)
    for group in mesh.vertices[vertex_index].groups:
        if group.weight > best[0]:
            best = (group.weight, group.group)
    return names.get(best[1], "?"), round(best[0], 2)

counts = {}
samples = []
for poly in mesh.polygons:
    center = Vector(poly.center)
    if not (60 < center.z < 115 and 12 < center.x < 40 and -40 < center.y < 20):
        continue
    owners = []
    for vertex_index in poly.vertices:
        owners.append(dominant(vertex_index)[0])
    key = tuple(sorted(set(owners)))
    counts[key] = counts.get(key, 0) + 1
    if len(samples) < 40 and ("Hand" in "".join(owners) or "Arm" in "".join(owners) or "shield" in "".join(owners).lower() or "node" in "".join(owners)):
        samples.append((tuple(round(v, 1) for v in center), owners, round(poly.area, 2)))

print("MIXES")
for key, count in sorted(counts.items(), key=lambda item: -item[1])[:30]:
    print(count, key)
print("SAMPLES")
for row in samples:
    print(row)
