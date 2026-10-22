"""Pass 9. Average weights across the remaining hard bone borders.

Only the two vertices of a stretching edge are pulled together, then the
pass repeats so the blend spreads a few rings instead of jumping in one edge.
"""
import json
import bpy
from mathutils import Vector

DST = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-rig-repair-pass10.blend"
OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\repair_pass10.json"
RENDER = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\attack-95-pass10.png"
mesh = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in mesh.modifiers if m.type == "ARMATURE" and m.object)
me = mesh.data
scene = bpy.context.scene
scale = 100.0 * scene.unit_settings.scale_length


def world(co):
    return mesh.matrix_world @ Vector(co)


def groups_of(index):
    return {
        mesh.vertex_groups[g.group].name: g.weight
        for g in me.vertices[index].groups
        if g.weight > 0.001
    }


def dominant(groups):
    best, weight = None, -1.0
    for name, value in groups.items():
        if value > weight:
            best, weight = name, value
    return best


def family(name):
    if not name:
        return ""
    if "skirt" in name:
        return "skirt"
    if "UpLeg" in name:
        return "upleg"
    if name.endswith("Arm") or "Shoulder" in name:
        return "arm"
    if name in {"Character1_Hips", "Character1_Spine", "Character1_Spine1", "Character1_Spine2"}:
        return "torso"
    return name


def replace_weights(index, pairs):
    ranked = [(name, weight) for name, weight in pairs.items() if weight > 0.02]
    ranked.sort(key=lambda item: -item[1])
    ranked = ranked[:3]
    total = sum(weight for _name, weight in ranked) or 1.0
    keep = {name for name, _weight in ranked}
    for group in list(me.vertices[index].groups):
        name = mesh.vertex_groups[group.group].name
        if name not in keep:
            try:
                mesh.vertex_groups[name].remove([index])
            except RuntimeError:
                pass
    for name, weight in ranked:
        mesh.vertex_groups[name].add([index], float(weight / total), "REPLACE")


def mix(left, right):
    keys = set(left) | set(right)
    return {key: left.get(key, 0.0) * 0.5 + right.get(key, 0.0) * 0.5 for key in keys}


ALLOWED = {
    frozenset(("torso", "skirt")),
    frozenset(("torso", "upleg")),
    frozenset(("torso", "arm")),
    frozenset(("skirt", "upleg")),
}
for step in range(4):
    updates = {}
    touched = 0
    for edge in me.edges:
        a, b = int(edge.vertices[0]), int(edge.vertices[1])
        rest = (world(me.vertices[a].co) - world(me.vertices[b].co)).length * scale
        if rest > 1.5 or rest < 1e-5:
            continue
        ga = updates.get(a) or groups_of(a)
        gb = updates.get(b) or groups_of(b)
        pair = frozenset((family(dominant(ga)), family(dominant(gb))))
        if pair not in ALLOWED:
            continue
        blended = mix(ga, gb)
        updates[a] = blended
        updates[b] = blended
        touched += 1
    for index, weights in updates.items():
        replace_weights(index, weights)
    print("STEP", step, "edges", touched, "verts", len(updates), flush=True)

action = bpy.data.actions["VALKUR_TEST_attack"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
arm.data.pose_position = "POSE"
scene.frame_set(95)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(deps)
em = ev.to_mesh()
PROBES = [(809011, 809035), (221522, 221525), (613288, 613296), (519568, 519579), (1258444, 1258445)]
probes = []
for a, b in PROBES:
    rest = (world(me.vertices[a].co) - world(me.vertices[b].co)).length * scale
    posed = (world(em.vertices[a].co) - world(em.vertices[b].co)).length * scale
    probes.append({"edge": [a, b], "rest_cm": round(rest, 3), "posed_cm": round(posed, 3)})
pairs = {}
over = 0
for edge in me.edges:
    a, b = int(edge.vertices[0]), int(edge.vertices[1])
    rest = (world(me.vertices[a].co) - world(me.vertices[b].co)).length * scale
    if rest > 1.5 or rest < 1e-5:
        continue
    posed = (world(em.vertices[a].co) - world(em.vertices[b].co)).length * scale
    if posed - rest <= 8.0:
        continue
    over += 1
    ga, gb = groups_of(a), groups_of(b)
    key = " / ".join(sorted((dominant(ga) or "?", dominant(gb) or "?")))
    pairs[key] = pairs.get(key, 0) + 1
ev.to_mesh_clear()
report = {"probes": probes, "edges_over_8cm": over, "pairs": sorted(pairs.items(), key=lambda item: -item[1])[:12]}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print(json.dumps(report), flush=True)
cam = bpy.data.objects.get("Rig review camera")
if cam:
    scene.camera = cam
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 960
scene.render.resolution_y = 1280
scene.render.image_settings.file_format = "PNG"
try:
    scene.eevee.taa_render_samples = 16
except Exception:
    pass
scene.render.filepath = RENDER
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=DST, copy=True)
print("SAVED", DST)
