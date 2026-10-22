"""Continue from the left-thigh repair.

1. Islands that mix a hand bone with the body are resolved as either a rigid
   weapon/shield or body skin. A consistent weapon island is not touched.
2. Right thigh skin gets the same hip-to-leg falloff as the left thigh.
3. Each shoulder cap blends spine, clavicle and upper arm along the bone.
"""
import json
import bpy
import bmesh
from mathutils import Vector, kdtree

SRC_NOTE = "valkur-rig-hip-thigh-pass4.blend"
DST = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-rig-repair-pass5.blend"
OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\repair_pass5.json"
RENDER = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\attack-95-pass5.png"

mesh = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in mesh.modifiers if m.type == "ARMATURE" and m.object)
me = mesh.data
scene = bpy.context.scene
scale = 100.0 * scene.unit_settings.scale_length

BODY = {
    "Character1_Hips", "Character1_Spine", "Character1_Spine1", "Character1_Spine2",
    "Character1_LeftUpLeg", "Character1_RightUpLeg",
    "Character1_LeftLeg", "Character1_RightLeg",
    "Left_skirt_front_1", "Left_skirt_front_2", "Left_skirt_front_3",
    "Left_skirt_back_1", "Left_skirt_back_2", "Left_skirt_back_3",
    "Rright_skirt_front_1", "Rright_skirt_front_2", "Rright_skirt_front_3",
    "Rright_skirt_back_1", "Rright_skirt_back_2", "Rright_skirt_back_3",
}
SHOULDER_NAMES = {
    "Character1_Spine1", "Character1_Spine2",
    "Character1_LeftShoulder", "Character1_LeftArm", "Character1_LeftForeArm",
    "Character1_RightShoulder", "Character1_RightArm", "Character1_RightForeArm",
}


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
    mesh.vertex_groups[name].add([index], float(weight), "REPLACE")


bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
uv_layer = bm.loops.layers.uv.active


def loop_uv(vert, face):
    for loop in face.loops:
        if loop.vert == vert:
            return loop[uv_layer].uv.copy()
    return None


def flood_island(start_index):
    seed = bm.verts[start_index]
    stack = [f.index for f in seed.link_faces]
    seen = set(stack)
    while stack:
        face = bm.faces[stack.pop()]
        for edge in face.edges:
            for other in edge.link_faces:
                if other.index in seen:
                    continue
                if all((loop_uv(v, face) - loop_uv(v, other)).length <= 1e-4 for v in edge.verts):
                    seen.add(other.index)
                    stack.append(other.index)
    return {v.index for fi in seen for v in bm.faces[fi].verts}


kd = kdtree.KDTree(len(me.vertices))
for i, vert in enumerate(me.vertices):
    kd.insert(world(vert.co), i)
kd.balance()

hand_verts = [i for i in range(len(me.vertices)) if any(is_hand(n) for n in groups_of(i))]
seeds = []
for i in hand_verts:
    co = world(me.vertices[i].co)
    for _co, j, dist in kd.find_range(co, 0.45):
        if j == i:
            continue
        other = dominant(j)
        if other and not is_hand(other):
            seeds.append(i)
            break

visited = set()
islands = []
for seed in seeds:
    if seed in visited:
        continue
    island = flood_island(seed)
    visited.update(island)
    islands.append(island)

hand_heads = {
    "Character1_LeftHand": bone_head("Character1_LeftHand"),
    "Character1_RightHand": bone_head("Character1_RightHand"),
}
decisions = []
rewritten_weapon = 0
rewritten_body = 0
for island in islands:
    hand_count = 0
    body_count = 0
    hand_votes = {}
    for i in island:
        name = dominant(i)
        if name and is_hand(name):
            hand_count += 1
            root = "Character1_LeftHand" if "Left" in name else "Character1_RightHand"
            hand_votes[root] = hand_votes.get(root, 0) + 1
        elif name in BODY or (name and name.startswith("Character1_")):
            body_count += 1
    total = max(1, hand_count + body_count)
    hand_frac = hand_count / total
    if hand_frac >= 0.65 and hand_votes:
        target = max(hand_votes, key=hand_votes.get)
        changed = 0
        for i in island:
            if dominant(i) != target:
                for name in list(groups_of(i)):
                    remove_group(i, name)
                set_group(i, target, 1.0)
                changed += 1
        rewritten_weapon += changed
        kind = "weapon"
    elif hand_frac <= 0.35:
        donors = [i for i in island if not any(is_hand(n) for n in groups_of(i))]
        changed = 0
        for i in island:
            if not any(is_hand(n) for n in groups_of(i)):
                continue
            co = world(me.vertices[i].co)
            donor = None
            best = 1e9
            for j in donors:
                dist = (co - world(me.vertices[j].co)).length
                if dist < best:
                    best = dist
                    donor = j
            for name in list(groups_of(i)):
                if is_hand(name):
                    remove_group(i, name)
            if donor is None:
                set_group(i, "Character1_Hips", 1.0)
            else:
                donor_groups = groups_of(donor)
                total_w = sum(donor_groups.values()) or 1.0
                for name, weight in donor_groups.items():
                    set_group(i, name, weight / total_w)
            changed += 1
        rewritten_body += changed
        kind = "body"
        target = "nearest-body"
    else:
        kind = "mixed-kept"
        target = None
        changed = 0
    decisions.append({
        "verts": len(island),
        "hand_frac": round(hand_frac, 3),
        "kind": kind,
        "target": target,
        "changed": changed,
    })

# Right thigh skin. Left thigh weights from pass 4 stay as they are.
HIP = "Character1_Hips"
LEG = "Character1_RightUpLeg"
ALLOWED = {HIP, LEG}
T0, T1 = 0.12, 0.62
origin = bone_head(LEG)
knee = bone_head("Character1_RightLeg")
left = bone_head("Character1_LeftUpLeg")
axis = knee - origin
thigh_len = axis.length
axis_n = axis.normalized()


def tube_distance(co):
    t = max(0.0, min(thigh_len, (co - origin).dot(axis_n)))
    return (co - (origin + axis_n * t)).length


def along(co):
    return (co - origin).dot(axis_n) / thigh_len


def hip_weight(t):
    if t <= T0:
        return 1.0
    if t >= T1:
        return 0.0
    x = (t - T0) / (T1 - T0)
    s = x * x * (3.0 - 2.0 * x)
    return 1.0 - s


right_thigh = []
for i, vert in enumerate(me.vertices):
    names = set(groups_of(i))
    if not names or not names.issubset(ALLOWED):
        continue
    co = world(vert.co)
    if co.x > 0.0:
        continue
    if tube_distance(co) > 18.0:
        continue
    if (co - left).length <= (co - origin).length:
        continue
    t = along(co)
    if t < 0.0 or t > 0.75:
        continue
    right_thigh.append(i)
for i in right_thigh:
    t = along(world(me.vertices[i].co))
    w = hip_weight(t)
    set_group(i, HIP, w)
    set_group(i, LEG, 1.0 - w)

# Shoulder caps.
def blend_shoulder(side):
    shoulder = bone_head(f"Character1_{side}Shoulder")
    upper = bone_head(f"Character1_{side}Arm")
    elbow = bone_head(f"Character1_{side}ForeArm")
    seg = upper - shoulder
    seg_len = seg.length
    seg_n = seg.normalized()
    names = {
        "Character1_Spine2",
        f"Character1_{side}Shoulder",
        f"Character1_{side}Arm",
        f"Character1_{side}ForeArm",
        f"Character1_{side}ForeArmRoll",
    }
    picked = []
    for i, vert in enumerate(me.vertices):
        owned = set(groups_of(i))
        if not owned or not owned.issubset(SHOULDER_NAMES | {f"Character1_{side}ForeArmRoll"}):
            continue
        co = world(vert.co)
        t_raw = (co - shoulder).dot(seg_n)
        t = t_raw / seg_len
        closest = shoulder + seg_n * max(-2.0, min(seg_len + 2.0, t_raw))
        if (co - closest).length > 8.0:
            continue
        if t < -0.15 or t > 1.15:
            continue
        picked.append(i)
        if t <= 0.05:
            weights = [("Character1_Spine2", 1.0)]
        elif t <= 0.45:
            x = (t - 0.05) / 0.40
            s = x * x * (3.0 - 2.0 * x)
            weights = [("Character1_Spine2", 1.0 - s), (f"Character1_{side}Shoulder", s)]
        elif t <= 0.85:
            x = (t - 0.45) / 0.40
            s = x * x * (3.0 - 2.0 * x)
            weights = [(f"Character1_{side}Shoulder", 1.0 - s), (f"Character1_{side}Arm", s)]
        else:
            weights = [(f"Character1_{side}Arm", 1.0)]
        for name in list(groups_of(i)):
            if name not in {item[0] for item in weights}:
                remove_group(i, name)
        for name, weight in weights:
            set_group(i, name, weight)
    return {"side": side, "verts": len(picked), "segment_cm": round(seg_len, 3), "elbow_cm": [round(c, 2) for c in elbow]}


shoulders = [blend_shoulder("Left"), blend_shoulder("Right")]

PROBES = [
    (809011, 809035),
    (672624, 672629),
    (221522, 221525),
    (1195206, 1295651),
    (122507, 122508),
    (1331753, 1331754),
    (1396755, 1396756),
]


def pose_probe(action_name, frame):
    action = bpy.data.actions[action_name]
    ad = arm.animation_data_create()
    ad.action = action
    ad.action_slot = action.slots[0]
    scene.frame_end = max(scene.frame_end, int(action.frame_range[1]))
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(deps)
    em = ev.to_mesh()
    rows = []
    for i, j in PROBES:
        rest = (world(me.vertices[i].co) - world(me.vertices[j].co)).length * scale
        posed = (world(em.vertices[i].co) - world(em.vertices[j].co)).length * scale
        rows.append({"edge": [i, j], "rest_cm": round(rest, 4), "posed_cm": round(posed, 4)})
    # Worst short edges. Skip edges already long at rest.
    worst = []
    for edge in me.edges:
        a, b = edge.vertices
        rest = (world(me.vertices[a].co) - world(me.vertices[b].co)).length * scale
        if rest > 1.5 or rest < 1e-5:
            continue
        posed = (world(em.vertices[a].co) - world(em.vertices[b].co)).length * scale
        extra = posed - rest
        if extra > 4.0:
            worst.append((extra, a, b, rest, posed))
    worst.sort(reverse=True)
    top = []
    for extra, a, b, rest, posed in worst[:12]:
        top.append({
            "edge": [int(a), int(b)],
            "rest_cm": round(rest, 3),
            "posed_cm": round(posed, 3),
            "a": groups_of(int(a)),
            "b": groups_of(int(b)),
        })
    ev.to_mesh_clear()
    return {"frame": frame, "probes": rows, "still_over_4cm": len(worst), "worst": top}


arm.data.pose_position = "POSE"
report = {
    "base": SRC_NOTE,
    "mixed_islands": len(islands),
    "hand_seed_verts": len(seeds),
    "weapon_verts_rewritten": rewritten_weapon,
    "body_leak_verts_rewritten": rewritten_body,
    "island_decisions_largest": sorted(decisions, key=lambda d: -d["verts"])[:15],
    "right_thigh_verts": len(right_thigh),
    "shoulders": shoulders,
    "attack_95": pose_probe("VALKUR_TEST_attack", 95),
    "walk_21": pose_probe("VALKUR_TEST_walk", 21),
    "defense_95": pose_probe("VALKUR_TEST_defense", 95),
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print("ISLANDS", len(islands), "RIGHT", len(right_thigh), "OVER", report["attack_95"]["still_over_4cm"])

attack = bpy.data.actions["VALKUR_TEST_attack"]
arm.animation_data.action = attack
arm.animation_data.action_slot = attack.slots[0]
scene.frame_set(95)
cam = bpy.data.objects.get("Rig review camera")
if cam:
    scene.camera = cam
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 960
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
try:
    scene.eevee.taa_render_samples = 16
except Exception:
    pass
scene.render.filepath = RENDER
bpy.ops.render.render(write_still=True)
bm.free()
bpy.ops.wm.save_as_mainfile(filepath=DST, copy=True)
print("SAVED", DST)
