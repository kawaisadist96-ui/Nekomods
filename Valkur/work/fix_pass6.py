"""Pass 6 from the arm/hand/right-thigh repair."""
import json
import bpy
from mathutils import Vector, kdtree

DST = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-rig-repair-pass6.blend"
OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\repair_pass6.json"
RENDER = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\attack-95-pass6.png"

mesh = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in mesh.modifiers if m.type == "ARMATURE" and m.object)
me = mesh.data
scene = bpy.context.scene
scale = 100.0 * scene.unit_settings.scale_length
SKIRT = [g.name for g in mesh.vertex_groups if "skirt" in g.name]


def is_hand(name):
    return "Hand" in name or "hand_node" in name


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


def set_group(index, name, weight):
    mesh.vertex_groups[name].add([index], float(max(0.0, min(1.0, weight))), "REPLACE")


def replace_weights(index, pairs):
    keep = {name for name, _weight in pairs}
    for name in list(groups_of(index)):
        if name not in keep:
            remove_group(index, name)
    for name, weight in pairs:
        set_group(index, name, weight)


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


snapped_hand = 0
snapped_body = 0
for i in range(len(me.vertices)):
    groups = groups_of(i)
    if not groups:
        continue
    hand = {n: w for n, w in groups.items() if is_hand(n)}
    body = {n: w for n, w in groups.items() if not is_hand(n)}
    if not hand or not body:
        continue
    if sum(hand.values()) >= sum(body.values()):
        target = max(hand, key=hand.get)
        replace_weights(i, [(target, 1.0)])
        snapped_hand += 1
    else:
        total = sum(body.values()) or 1.0
        replace_weights(i, [(n, w / total) for n, w in body.items()])
        snapped_body += 1

kd = kdtree.KDTree(len(me.vertices))
for i, vert in enumerate(me.vertices):
    kd.insert(world(vert.co), i)
kd.balance()
skirt_seeds = [i for i in range(len(me.vertices)) if any(n in SKIRT for n in groups_of(i))]
skirt_set = set(skirt_seeds)
blocked = ("Hand", "UpLeg", "Leg", "Arm", "Foot", "Head", "Toe")
for i in skirt_seeds:
    co = world(me.vertices[i].co)
    for _co, j, dist in kd.find_range(co, 2.5):
        names = set(groups_of(j))
        if not names or any(any(token in n for token in blocked) for n in names):
            continue
        if names.issubset(set(SKIRT) | {"Character1_Hips", "Character1_Spine"}):
            skirt_set.add(j)


def skirt_pair(co):
    side = "Left" if co.x >= 0.0 else "Rright"
    facing = "front" if co.y <= 2.0 else "back"
    return [f"{side}_skirt_{facing}_{level}" for level in (1, 2, 3)]


skirt_changed = 0
for i in skirt_set:
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
    skirt_changed += 1


def blend_side(side, sign):
    spine = bone_head("Character1_Spine2")
    upper = bone_head(f"Character1_{side}Arm")
    seg = upper - spine
    length = seg.length
    direction = seg.normalized()
    allowed = {
        "Character1_Spine", "Character1_Spine1", "Character1_Spine2",
        f"Character1_{side}Shoulder", f"Character1_{side}Arm",
        f"Character1_{side}ForeArm", f"Character1_{side}ForeArmRoll",
    }
    count = 0
    for i, vert in enumerate(me.vertices):
        names = set(groups_of(i))
        if not names or not names.issubset(allowed):
            continue
        dom = dominant(i) or ""
        if any(token in dom for token in ("ForeArm", "Hand", "Head", "Neck")):
            continue
        co = world(vert.co)
        if sign * co.x < -2.0:
            continue
        t_raw = (co - spine).dot(direction)
        t = t_raw / length
        closest = spine + direction * max(0.0, min(length, t_raw))
        if (co - closest).length > 14.0 or t < -0.05 or t > 1.05:
            continue
        if t <= 0.18:
            pairs = [("Character1_Spine2", 1.0)]
        elif t <= 0.48:
            s = smoothstep((t - 0.18) / 0.30)
            pairs = [("Character1_Spine2", 1.0 - s), (f"Character1_{side}Shoulder", s)]
        elif t <= 0.82:
            s = smoothstep((t - 0.48) / 0.34)
            pairs = [(f"Character1_{side}Shoulder", 1.0 - s), (f"Character1_{side}Arm", s)]
        else:
            pairs = [(f"Character1_{side}Arm", 1.0)]
        replace_weights(i, pairs)
        count += 1
    return count


shoulder_counts = {"left": blend_side("Left", 1.0), "right": blend_side("Right", -1.0)}

spine = bone_head("Character1_Spine2")
head = bone_head("Character1_Head")
seg = head - spine
length = seg.length
direction = seg.normalized()
neck_count = 0
neck_allowed = {"Character1_Spine2", "Character1_Neck", "Character1_Head", "Character1_Spine1"}
for i, vert in enumerate(me.vertices):
    names = set(groups_of(i))
    if not names or not names.issubset(neck_allowed):
        continue
    if "Character1_Head" not in names and "Character1_Neck" not in names:
        continue
    co = world(vert.co)
    t_raw = (co - spine).dot(direction)
    t = t_raw / length
    closest = spine + direction * max(0.0, min(length, t_raw))
    if (co - closest).length > 11.0 or not -0.05 <= t <= 1.15:
        continue
    if t <= 0.22:
        pairs = [("Character1_Spine2", 1.0)]
    elif t <= 0.5:
        s = smoothstep((t - 0.22) / 0.28)
        pairs = [("Character1_Spine2", 1.0 - s), ("Character1_Neck", s)]
    elif t <= 0.78:
        s = smoothstep((t - 0.5) / 0.28)
        pairs = [("Character1_Neck", 1.0 - s), ("Character1_Head", s)]
    else:
        pairs = [("Character1_Head", 1.0)]
    replace_weights(i, pairs)
    neck_count += 1

PROBES = [(809011, 809035), (221522, 221525), (613288, 613296), (122507, 122508), (1258444, 1258445)]


def measure():
    action = bpy.data.actions["VALKUR_TEST_attack"]
    ad = arm.animation_data_create()
    ad.action = action
    ad.action_slot = action.slots[0]
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
    over8 = 0
    worst = None
    for edge in me.edges:
        a, b = int(edge.vertices[0]), int(edge.vertices[1])
        rest = (world(me.vertices[a].co) - world(me.vertices[b].co)).length * scale
        if rest > 1.5 or rest < 1e-5:
            continue
        posed = (world(em.vertices[a].co) - world(em.vertices[b].co)).length * scale
        extra = posed - rest
        if extra > 8.0:
            over8 += 1
            if worst is None or extra > worst[0]:
                worst = (extra, a, b, rest, posed, dominant(a), dominant(b))
    ev.to_mesh_clear()
    return {
        "probes": probes,
        "edges_extra_over_8cm": over8,
        "worst": None if worst is None else {
            "edge": [worst[1], worst[2]],
            "rest_cm": round(worst[3], 3),
            "posed_cm": round(worst[4], 3),
            "bones": [worst[5], worst[6]],
        },
    }


arm.data.pose_position = "POSE"
attack = measure()
report = {
    "snapped_to_hand": snapped_hand,
    "snapped_to_body": snapped_body,
    "skirt_verts": skirt_changed,
    "shoulders": shoulder_counts,
    "neck_verts": neck_count,
    "attack_95": attack,
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print(json.dumps(attack))

action = bpy.data.actions["VALKUR_TEST_attack"]
arm.animation_data.action = action
arm.animation_data.action_slot = action.slots[0]
scene.frame_set(95)
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
