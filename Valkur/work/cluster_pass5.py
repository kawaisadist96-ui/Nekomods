import json
import bpy
from mathutils import Vector

OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\pass5_clusters.json"
mesh = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in mesh.modifiers if m.type == "ARMATURE" and m.object)
me = mesh.data
scene = bpy.context.scene
scale = 100.0 * scene.unit_settings.scale_length

def is_hand(name):
    return "Hand" in name or "hand_node" in name

def world(co):
    return mesh.matrix_world @ Vector(co)

def dominant(index):
    best, weight = None, -1.0
    for g in me.vertices[index].groups:
        if g.weight > weight:
            best, weight = mesh.vertex_groups[g.group].name, g.weight
    return best

action = bpy.data.actions["VALKUR_TEST_attack"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
scene.frame_set(95)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(deps)
em = ev.to_mesh()

pairs = {}
samples = []
count = 0
for edge in me.edges:
    a, b = int(edge.vertices[0]), int(edge.vertices[1])
    rest = (world(me.vertices[a].co) - world(me.vertices[b].co)).length * scale
    if rest > 1.5 or rest < 1e-5:
        continue
    posed = (world(em.vertices[a].co) - world(em.vertices[b].co)).length * scale
    extra = posed - rest
    if extra < 4.0:
        continue
    count += 1
    da, db = dominant(a), dominant(b)
    key = " / ".join(sorted((da or "?", db or "?")))
    pairs[key] = pairs.get(key, 0) + 1
    if len(samples) < 8 and extra > 15:
        samples.append({
            "edge": [a, b],
            "rest": round(rest, 3),
            "posed": round(posed, 3),
            "a_cm": [round(c, 2) for c in world(me.vertices[a].co)],
            "b_cm": [round(c, 2) for c in world(me.vertices[b].co)],
            "da": da,
            "db": db,
        })
ev.to_mesh_clear()
report = {
    "edges_over_4cm": count,
    "pairs": sorted(pairs.items(), key=lambda kv: -kv[1])[:25],
    "samples": samples,
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print("COUNT", count)
print(report["pairs"][:8])
