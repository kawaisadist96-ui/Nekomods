import json
import bpy
from mathutils import Vector

OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\hip_thigh_residual.json"
mesh = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in mesh.modifiers if m.type == "ARMATURE" and m.object)
me = mesh.data
scene = bpy.context.scene
scale = 100.0 * scene.unit_settings.scale_length
PAIR = (758631, 758655)

def weights(i):
    return sorted(
        [(mesh.vertex_groups[g.group].name, round(g.weight, 4)) for g in me.vertices[i].groups if g.weight > 0.001],
        key=lambda x: -x[1],
    )

def world(co):
    return mesh.matrix_world @ Vector(co)

rest = (world(me.vertices[PAIR[0]].co) - world(me.vertices[PAIR[1]].co)).length * scale
act = bpy.data.actions["VALKUR_TEST_attack"]
ad = arm.animation_data_create()
ad.action = act
ad.action_slot = act.slots[0]
scene.frame_set(95)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(deps)
em = ev.to_mesh()
posed = (world(em.vertices[PAIR[0]].co) - world(em.vertices[PAIR[1]].co)).length * scale
report = {
    "rest_cm": round(rest, 4),
    "posed_cm": round(posed, 4),
    "a": {"index": PAIR[0], "rest_cm": [round(c * scale, 3) for c in world(me.vertices[PAIR[0]].co)], "weights": weights(PAIR[0])},
    "b": {"index": PAIR[1], "rest_cm": [round(c * scale, 3) for c in world(me.vertices[PAIR[1]].co)], "weights": weights(PAIR[1])},
}
# Neighbor weight jumps inside a small world radius of the pair.
from mathutils import kdtree
kd = kdtree.KDTree(len(me.vertices))
for i, v in enumerate(me.vertices):
    kd.insert(world(v.co), i)
kd.balance()
center = world(me.vertices[PAIR[0]].co)
nearby = []
for _co, i, dist in kd.find_range(center, 1.5):
    nearby.append(i)
jumps = []
for i in nearby:
    wi = {n: w for n, w in weights(i)}
    for j in nearby:
        if j <= i:
            continue
        d = (world(me.vertices[i].co) - world(me.vertices[j].co)).length * scale
        if d > 0.35:
            continue
        wj = {n: w for n, w in weights(j)}
        bones = set(wi) | set(wj)
        delta = max(abs(wi.get(b, 0) - wj.get(b, 0)) for b in bones) if bones else 0
        if delta > 0.35:
            pd = (world(em.vertices[i].co) - world(em.vertices[j].co)).length * scale
            jumps.append({
                "edge": [i, j],
                "rest_cm": round(d, 4),
                "posed_cm": round(pd, 4),
                "weight_delta": round(delta, 4),
                "a": weights(i),
                "b": weights(j),
            })
jumps.sort(key=lambda x: -x["posed_cm"])
report["nearby_count"] = len(nearby)
report["sharp_jumps"] = jumps[:12]
ev.to_mesh_clear()
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print("jumps", len(jumps), "rest", round(rest, 4), "posed", round(posed, 4))
