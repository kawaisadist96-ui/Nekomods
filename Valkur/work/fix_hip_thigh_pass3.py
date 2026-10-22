"""Left-thigh skin only: hips to upper-leg falloff along the fitted thigh bone.

Pass 2 smoothed the original panel and then stopped mid-gradient, which moved
the tear to the mask border. This pass covers the left thigh skin whose weights
are only Hips and LeftUpLeg, and it stops where the falloff is already pure.
Skirt, hands, and the right leg are left unchanged. Source is the work copy.
"""
import json
import bpy
import bmesh
from mathutils import Vector

DST = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-rig-hip-thigh-pass4.blend"
OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\hip_thigh_pass4.json"
RENDER = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\hip-thigh-attack-95-pass4.png"
A, B = 809011, 809035
HIP = "Character1_Hips"
LEG = "Character1_LeftUpLeg"
ALLOWED = {HIP, LEG}
T0, T1 = 0.12, 0.62
TUBE_CM = 18.0
PROBES = [
    (809011, 809035),
    (831717, 831722),
    (674425, 674449),
    (672624, 672629),
    (698656, 698658),
    (730716, 730718),
    (731048, 731049),
    (758631, 758655),
]

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


origin = arm.matrix_world @ arm.data.bones[LEG].head_local
knee = arm.matrix_world @ arm.data.bones["Character1_LeftLeg"].head_local
right = arm.matrix_world @ arm.data.bones["Character1_RightUpLeg"].head_local
axis = knee - origin
length = axis.length
axis_n = axis.normalized()


def tube_distance(co):
    t = max(0.0, min(length, (co - origin).dot(axis_n)))
    return (co - (origin + axis_n * t)).length


def along(co):
    return (co - origin).dot(axis_n) / length


def hip_weight(t):
    if t <= T0:
        return 1.0
    if t >= T1:
        return 0.0
    x = (t - T0) / (T1 - T0)
    s = x * x * (3.0 - 2.0 * x)
    return 1.0 - s


affected = set()
for i, vert in enumerate(me.vertices):
    names = groups_of(i)
    if not names or not set(names).issubset(ALLOWED):
        continue
    co = world(vert.co)
    if co.x < 0.0:
        continue
    if tube_distance(co) > TUBE_CM:
        continue
    if (co - right).length <= (co - origin).length:
        continue
    t = along(co)
    if t < 0.0 or t > 0.75:
        continue
    affected.add(i)

if A not in affected or B not in affected:
    raise SystemExit(f"target verts missing A={A in affected} B={B in affected}")

vg_hip = mesh.vertex_groups[HIP]
vg_leg = mesh.vertex_groups[LEG]
ts = []
for i in affected:
    t = along(world(me.vertices[i].co))
    ts.append(t)
    w_hip = hip_weight(t)
    vg_hip.add([i], float(w_hip), "REPLACE")
    vg_leg.add([i], float(1.0 - w_hip), "REPLACE")

bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
edges = []
seen = set()
for i in affected:
    for edge in bm.verts[i].link_edges:
        j = edge.other_vert(bm.verts[i]).index
        if j not in affected:
            continue
        key = (i, j) if i < j else (j, i)
        if key in seen:
            continue
        seen.add(key)
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
    probes = []
    for i, j in PROBES:
        if i >= len(em.vertices) or j >= len(em.vertices):
            continue
        rest = (world(me.vertices[i].co) - world(me.vertices[j].co)).length * scale
        posed = (world(em.vertices[i].co) - world(em.vertices[j].co)).length * scale
        probes.append({
            "edge": [i, j],
            "in_mask": i in affected and j in affected,
            "rest_cm": round(rest, 4),
            "posed_cm": round(posed, 4),
        })
    worst = None
    extra = 0
    for i, j, rest in edges:
        posed = (world(em.vertices[i].co) - world(em.vertices[j].co)).length * scale
        if worst is None or posed - rest > worst["extra_cm"]:
            worst = {"edge": [i, j], "rest_cm": round(rest, 4), "posed_cm": round(posed, 4), "extra_cm": round(posed - rest, 4)}
        if posed > rest + 1.0:
            extra += 1
    ev.to_mesh_clear()
    return {"frame": frame, "probes": probes, "worst": worst, "edges_extra_over_1cm": extra}


arm.data.pose_position = "POSE"
after = {
    "attack": [pose("VALKUR_TEST_attack", 95), pose("VALKUR_TEST_attack", 185)],
    "idle": [pose("VALKUR_TEST_idle", 90)],
    "walk": [pose("VALKUR_TEST_walk", 21), pose("VALKUR_TEST_walk", 61)],
    "defense": [pose("VALKUR_TEST_defense", 95)],
}

from mathutils import kdtree
kd = kdtree.KDTree(len(me.vertices))
for i, vert in enumerate(me.vertices):
    kd.insert(world(vert.co), i)
kd.balance()
cliffs = 0
for n, i in enumerate(affected):
    if n % 5:
        continue
    wi = groups_of(i).get(HIP, 0.0)
    co = world(me.vertices[i].co)
    for _co, j, dist in kd.find_n(co, 8):
        if j in affected or dist > 0.4:
            continue
        outside = groups_of(j)
        if not outside or not set(outside).issubset(ALLOWED):
            continue
        if abs(wi - outside.get(HIP, 0.0)) > 0.25:
            cliffs += 1
            break

report = {
    "affected_verts": len(affected),
    "target_pair_included": A in affected and B in affected,
    "t_range": [round(min(ts), 3), round(max(ts), 3)],
    "thigh_length_cm": round(length, 3),
    "tube_cm": TUBE_CM,
    "sampled_border_cliffs": cliffs,
    "after": after,
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print("MEASURED", len(affected), "CLIFFS", cliffs)

attack = bpy.data.actions["VALKUR_TEST_attack"]
arm.animation_data.action = attack
arm.animation_data.action_slot = attack.slots[0]
scene.frame_set(95)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(deps)
em = ev.to_mesh()
center = (world(em.vertices[A].co) + world(em.vertices[B].co)) * 0.5
ev.to_mesh_clear()
cam_data = bpy.data.cameras.new("HipThighCam3")
cam = bpy.data.objects.new("HipThighCam3", cam_data)
scene.collection.objects.link(cam)
cam_data.lens = 50
cam_data.clip_start = 0.01
cam_data.clip_end = 10000
view = Vector((-0.35, -1.0, 0.05)).normalized()
cam.location = center + view * 32.0
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
