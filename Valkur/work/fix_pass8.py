"""Pass 8. Blend the skirt across the center line and close hips borders.

Starts from pass 7. Thigh and shoulder weights stay unless a vertex is
hips-dominant cloth next to the skirt.
"""
import json
import bpy
from mathutils import Vector, kdtree

DST = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-rig-repair-pass8.blend"
OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\repair_pass8.json"
RENDER = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\attack-95-pass8.png"
mesh = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in mesh.modifiers if m.type == "ARMATURE" and m.object)
me = mesh.data
scene = bpy.context.scene
scale = 100.0 * scene.unit_settings.scale_length
SKIRT = [g.name for g in mesh.vertex_groups if "skirt" in g.name]


def world(co):
    return mesh.matrix_world @ Vector(co)


def groups_of(index):
    return {
        mesh.vertex_groups[g.group].name: g.weight
        for g in me.vertices[index].groups
        if g.weight > 0.001
    }


def dominant(index):
    best, weight = None, -1.0
    for name, value in groups_of(index).items():
        if value > weight:
            best, weight = name, value
    return best


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
    ranked = sorted(pairs, key=lambda item: -item[1])[:3]
    total = sum(weight for _name, weight in ranked) or 1.0
    keep = {name for name, _weight in ranked}
    for name in list(groups_of(index)):
        if name not in keep:
            remove_group(index, name)
    for name, weight in ranked:
        mesh.vertex_groups[name].add([index], float(weight / total), "REPLACE")


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def is_cloth_candidate(index):
    name = dominant(index) or ""
    if "UpLeg" in name or "Hand" in name or "Arm" in name or "Foot" in name or "Head" in name:
        return False
    return name == "Character1_Hips" or name in SKIRT or name == "Character1_Spine"


seeds = [i for i in range(len(me.vertices)) if any(name in SKIRT for name in groups_of(i))]
seed_tree = kdtree.KDTree(len(seeds))
for index in seeds:
    seed_tree.insert(world(me.vertices[index].co), index)
seed_tree.balance()
chosen = set(seeds)
for index in range(len(me.vertices)):
    if index in chosen or not is_cloth_candidate(index):
        continue
    _co, _seed, dist = seed_tree.find(world(me.vertices[index].co))
    if dist <= 3.0:
        chosen.add(index)
print("CLOTH", len(seeds), len(chosen), flush=True)

z1 = bone_head("Left_skirt_front_1").z
z2 = bone_head("Left_skirt_front_2").z
z3 = bone_head("Left_skirt_front_3").z


def cloth_weights(co):
    z = co.z
    if z >= z1:
        levels = [("Hips", 0.85), (1, 0.15)]
    elif z >= z2:
        span = smoothstep((z1 - z) / max(0.1, z1 - z2))
        levels = [("Hips", 0.7 * (1.0 - span)), (1, 0.3 * (1.0 - span) + 0.2 * span), (2, 0.8 * span)]
    elif z >= z3:
        span = smoothstep((z2 - z) / max(0.1, z2 - z3))
        levels = [(1, 0.2 * (1.0 - span)), (2, 0.8 * (1.0 - span) + 0.25 * span), (3, 0.75 * span)]
    else:
        levels = [(2, 0.15), (3, 0.85)]
    side = smoothstep((co.x + 6.0) / 12.0)
    facing = 1.0 - smoothstep((co.y + 2.0) / 8.0)
    combined = {}
    for level, weight in levels:
        if level == "Hips" or weight <= 0.0:
            if level == "Hips" and weight > 0.0:
                combined["Character1_Hips"] = combined.get("Character1_Hips", 0.0) + weight
            continue
        for side_name, side_weight in (("Left", side), ("Rright", 1.0 - side)):
            for face_name, face_weight in (("front", facing), ("back", 1.0 - facing)):
                amount = weight * side_weight * face_weight
                if amount < 0.02:
                    continue
                bone = f"{side_name}_skirt_{face_name}_{level}"
                combined[bone] = combined.get(bone, 0.0) + amount
    return list(combined.items())


for index in chosen:
    replace_weights(index, cloth_weights(world(me.vertices[index].co)))

# Partial hand weights next to a rigid hand vertex follow that hand.
kd = kdtree.KDTree(len(me.vertices))
for index, vert in enumerate(me.vertices):
    kd.insert(world(vert.co), index)
kd.balance()
harmonized = 0
partial = []
for index in range(len(me.vertices)):
    groups = groups_of(index)
    hand = {name: weight for name, weight in groups.items() if "Hand" in name}
    hand_sum = sum(hand.values())
    if 0.35 <= hand_sum <= 0.98:
        partial.append(index)
for index in partial:
    co = world(me.vertices[index].co)
    target = None
    for _co, other, dist in kd.find_range(co, 0.4):
        if other == index:
            continue
        other_groups = groups_of(other)
        other_hand = {name: weight for name, weight in other_groups.items() if "Hand" in name}
        if sum(other_hand.values()) > 0.98:
            target = max(other_hand, key=other_hand.get)
            break
    if target:
        replace_weights(index, [(target, 1.0)])
        harmonized += 1

PROBES = [(809011, 809035), (221522, 221525), (613288, 613296), (519568, 519579), (1258444, 1258445)]
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
pairs = {}
over = 0
for edge in me.edges:
    a, b = int(edge.vertices[0]), int(edge.vertices[1])
    rest = (world(me.vertices[a].co) - world(me.vertices[b].co)).length * scale
    if rest > 1.5 or rest < 1e-5:
        continue
    posed = (world(em.vertices[a].co) - world(em.vertices[b].co)).length * scale
    if posed - rest > 8.0:
        over += 1
        key = " / ".join(sorted((dominant(a) or "?", dominant(b) or "?")))
        pairs[key] = pairs.get(key, 0) + 1
ev.to_mesh_clear()
report = {
    "cloth_verts": len(chosen),
    "hand_harmonized": harmonized,
    "probes": probes,
    "edges_over_8cm": over,
    "pairs": sorted(pairs.items(), key=lambda item: -item[1])[:12],
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print(json.dumps({"cloth": len(chosen), "hands": harmonized, "over": over, "probes": probes}))
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
