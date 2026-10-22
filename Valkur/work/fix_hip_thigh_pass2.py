"""Redo the front-left thigh skin with a long hip-to-leg falloff.

The 2.5 cm band left a steep gradient: a 1.6 cm edge still posed to 9 cm.
Native CK3 weights change across roughly the upper half of the thigh, so this
pass uses that length on this skin panel only. Source is the untouched work copy.
"""
import json
import bpy
import bmesh
from mathutils import Vector, kdtree

DST = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-rig-hip-thigh-pass2.blend"
OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\hip_thigh_pass2.json"
RENDER = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\hip-thigh-attack-95-pass2.png"
A, B = 809011, 809035
HIP = "Character1_Hips"
LEG = "Character1_LeftUpLeg"
ALLOWED = {HIP, LEG}
T0, T1 = 0.12, 0.62

mesh = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in mesh.modifiers if m.type == "ARMATURE" and m.object)
me = mesh.data
scene = bpy.context.scene
scale = 100.0 * scene.unit_settings.scale_length

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


seed = bm.verts[A]
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
island = {v.index for fi in seen for v in bm.faces[fi].verts}


def world(co):
    return mesh.matrix_world @ Vector(co)


def groups_of(index):
    return {
        mesh.vertex_groups[g.group].name: g.weight
        for g in me.vertices[index].groups
        if g.weight > 0.001
    }


hip_head = arm.matrix_world @ arm.data.bones[HIP].head_local
leg_head = arm.matrix_world @ arm.data.bones[LEG].head_local
knee = arm.matrix_world @ arm.data.bones["Character1_LeftLeg"].head_local
# Falloff follows the thigh, starting at the hip joint rather than the spine root.
origin = leg_head
axis = knee - origin
length = axis.length
axis_n = axis.normalized()


def along(index):
    co = world(me.vertices[index].co)
    return (co - origin).dot(axis_n) / length


kd = kdtree.KDTree(len(me.vertices))
for i, v in enumerate(me.vertices):
    kd.insert(world(v.co), i)
kd.balance()

island_normal = Vector((0, 0, 0))
for i in list(island)[::10]:
    island_normal += (mesh.matrix_world.to_3x3() @ me.vertices[i].normal).normalized()
island_normal.normalize()

affected = set(island)
for i in list(island):
    co = world(me.vertices[i].co)
    for _co, j, dist in kd.find_range(co, 3.0):
        if j in affected or dist < 1e-6:
            continue
        if not set(groups_of(j)).issubset(ALLOWED):
            continue
        normal = (mesh.matrix_world.to_3x3() @ me.vertices[j].normal).normalized()
        if normal.dot(island_normal) < 0.35:
            continue
        if along(j) < -0.05 or along(j) > 0.85:
            continue
        affected.add(j)


def hip_weight(t):
    if t <= T0:
        return 1.0
    if t >= T1:
        return 0.0
    x = (t - T0) / (T1 - T0)
    s = x * x * (3.0 - 2.0 * x)
    return 1.0 - s


vg_hip = mesh.vertex_groups[HIP]
vg_leg = mesh.vertex_groups[LEG]
ts = []
for i in affected:
    t = along(i)
    ts.append(t)
    w_hip = hip_weight(t)
    vg_hip.add([i], float(w_hip), "REPLACE")
    vg_leg.add([i], float(1.0 - w_hip), "REPLACE")

edges = []
seen_edges = set()
for i in affected:
    for edge in bm.verts[i].link_edges:
        other = edge.other_vert(bm.verts[i]).index
        if other not in affected:
            continue
        key = (i, other) if i < other else (other, i)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        rest = (world(me.vertices[key[0]].co) - world(me.vertices[key[1]].co)).length * scale
        edges.append((key[0], key[1], rest))


def pose(action_name, frame):
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
    target = (world(em.vertices[A].co) - world(em.vertices[B].co)).length * scale
    worst = None
    over = 0
    for i, j, rest in edges:
        posed = (world(em.vertices[i].co) - world(em.vertices[j].co)).length * scale
        ratio = posed / rest if rest > 1e-6 else 0
        if worst is None or posed > worst["posed_cm"]:
            worst = {"edge": [i, j], "rest_cm": round(rest, 4), "posed_cm": round(posed, 4), "ratio": round(ratio, 3)}
        if posed > rest + 1.0:
            over += 1
    ev.to_mesh_clear()
    return {
        "frame": frame,
        "target_edge_cm": round(target, 6),
        "worst": worst,
        "edges_stretched_more_than_1cm": over,
    }


arm.data.pose_position = "POSE"
after = {
    "attack": [pose("VALKUR_TEST_attack", 95), pose("VALKUR_TEST_attack", 185)],
    "idle": [pose("VALKUR_TEST_idle", 90)],
    "walk": [pose("VALKUR_TEST_walk", 21), pose("VALKUR_TEST_walk", 61)],
    "defense": [pose("VALKUR_TEST_defense", 95), pose("VALKUR_TEST_defense", 185)],
}

# Border check: affected vert vs close skin outside the mask.
border = []
outside_checked = 0
for i in list(affected)[::4]:
    co = world(me.vertices[i].co)
    wi = groups_of(i).get(HIP, 0.0)
    for _co, j, dist in kd.find_range(co, 0.45):
        if j in affected:
            continue
        outside_checked += 1
        wj = groups_of(j).get(HIP, 0.0)
        if abs(wi - wj) > 0.35 and set(groups_of(j)).issubset(ALLOWED):
            border.append({"inside": i, "outside": j, "gap_cm": round(dist, 3), "hip_delta": round(abs(wi - wj), 3)})
            break

report = {
    "source": "valkur-rig-work.blend",
    "panel": "front-left upper thigh skin",
    "falloff_t": [T0, T1],
    "origin_cm": [round(c, 3) for c in origin],
    "knee_cm": [round(c, 3) for c in knee],
    "thigh_length_cm": round(length, 3),
    "island_verts": len(island),
    "affected_verts": len(affected),
    "t_range": [round(min(ts), 3), round(max(ts), 3)],
    "border_cliffs": border[:20],
    "border_cliff_count": len(border),
    "after": after,
}
if min(ts) < -0.2 or max(ts) > 1.3:
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    raise SystemExit("t range outside thigh; file not saved")

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print("MEASURED", len(affected), "CLIFFS", len(border))

scene.frame_set(95)
attack = bpy.data.actions["VALKUR_TEST_attack"]
arm.animation_data.action = attack
arm.animation_data.action_slot = attack.slots[0]
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(deps)
em = ev.to_mesh()
center = sum((world(em.vertices[i].co) for i in island), Vector()) / len(island)
ev.to_mesh_clear()
cam_data = bpy.data.cameras.new("HipThighCam2")
cam = bpy.data.objects.new("HipThighCam2", cam_data)
scene.collection.objects.link(cam)
cam_data.lens = 50
cam_data.clip_start = 0.01
cam_data.clip_end = 10000
view = Vector((-0.35, -1.0, 0.05)).normalized()
cam.location = center + view * 28.0
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 960
scene.render.resolution_y = 960
scene.render.image_settings.file_format = "PNG"
try:
    scene.eevee.taa_render_samples = 16
except Exception:
    pass
scene.render.filepath = RENDER
bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(cam, do_unlink=True)
bpy.data.cameras.remove(cam_data)
bm.free()
bpy.ops.wm.save_as_mainfile(filepath=DST, copy=True)
print("SAVED", DST)
