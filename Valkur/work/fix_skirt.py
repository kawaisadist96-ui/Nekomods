"""Skirt-only pass on top of pass 5. Does not touch hand or shoulder weights."""
import json
import bpy
from mathutils import Vector, kdtree

DST = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-rig-repair-pass7.blend"
OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\repair_pass7.json"
RENDER = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\attack-95-pass7.png"
mesh = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in mesh.modifiers if m.type == "ARMATURE" and m.object)
me = mesh.data
scene = bpy.context.scene
scale = 100.0 * scene.unit_settings.scale_length
SKIRT = [g.name for g in mesh.vertex_groups if "skirt" in g.name]

def world(co):
    return mesh.matrix_world @ Vector(co)

def groups_of(index):
    return {mesh.vertex_groups[g.group].name: g.weight for g in me.vertices[index].groups if g.weight > 0.001}

def bone_head(name):
    return arm.matrix_world @ arm.data.bones[name].head_local

def remove_group(index, name):
    group = mesh.vertex_groups.get(name)
    if group:
        try:
            group.remove([index])
        except RuntimeError:
            pass

def replace_weights(index, pairs):
    keep = {name for name, _w in pairs}
    for name in list(groups_of(index)):
        if name not in keep:
            remove_group(index, name)
    for name, weight in pairs:
        mesh.vertex_groups[name].add([index], float(weight), "REPLACE")

def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)

kd = kdtree.KDTree(len(me.vertices))
for i, vert in enumerate(me.vertices):
    kd.insert(world(vert.co), i)
kd.balance()
seeds = [i for i in range(len(me.vertices)) if any(n in SKIRT for n in groups_of(i))]
chosen = set(seeds)
blocked = ("Hand", "UpLeg", "Leg", "Arm", "Foot", "Head", "Toe")
for i in seeds:
    co = world(me.vertices[i].co)
    for _co, j, _dist in kd.find_range(co, 2.5):
        names = set(groups_of(j))
        if not names or any(any(token in n for token in blocked) for n in names):
            continue
        if names.issubset(set(SKIRT) | {"Character1_Hips", "Character1_Spine"}):
            chosen.add(j)

def skirt_pair(co):
    side = "Left" if co.x >= 0.0 else "Rright"
    facing = "front" if co.y <= 2.0 else "back"
    return [f"{side}_skirt_{facing}_{level}" for level in (1, 2, 3)]

for i in chosen:
    co = world(me.vertices[i].co)
    b1, b2, b3 = skirt_pair(co)
    z1, z2, z3 = bone_head(b1).z, bone_head(b2).z, bone_head(b3).z
    z = co.z
    if z >= z1:
        pairs = [("Character1_Hips", 0.75), (b1, 0.25)]
    elif z >= z2:
        s = smoothstep((z1 - z) / max(0.1, z1 - z2))
        pairs = [("Character1_Hips", 0.55 * (1.0 - s)), (b1, 0.45 * (1.0 - s) + 0.25 * s), (b2, 0.75 * s)]
    elif z >= z3:
        s = smoothstep((z2 - z) / max(0.1, z2 - z3))
        pairs = [(b1, 0.25 * (1.0 - s)), (b2, 0.75 * (1.0 - s) + 0.25 * s), (b3, 0.75 * s)]
    else:
        pairs = [(b2, 0.2), (b3, 0.8)]
    total = sum(w for _n, w in pairs) or 1.0
    replace_weights(i, [(n, w / total) for n, w in pairs])

PROBES = [(809011, 809035), (221522, 221525), (613288, 613296), (122507, 122508), (1258444, 1258445)]
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
probes = []
for a, b in PROBES:
    rest = (world(me.vertices[a].co) - world(me.vertices[b].co)).length * scale
    posed = (world(em.vertices[a].co) - world(em.vertices[b].co)).length * scale
    probes.append({"edge": [a, b], "rest_cm": round(rest, 3), "posed_cm": round(posed, 3)})
ev.to_mesh_clear()
report = {"skirt_verts": len(chosen), "attack_95": probes}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print(json.dumps(probes))
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
