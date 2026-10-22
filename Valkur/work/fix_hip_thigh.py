"""Local hip/thigh skin blend for the verified body panel around 809011-809035.

The panel is thigh skin, not skirt cloth. Only this panel and its immediate
same-surface seam are reweighted. The blend file is written to a new path.
"""
import array
import json
from collections import defaultdict

import bmesh
import bpy
from mathutils import Vector, kdtree

SRC = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-rig-work.blend"
DST = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-rig-hip-thigh-pass1.blend"
OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\hip_thigh_pass1.json"
RENDER_DIR = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work"
A, B = 809011, 809035
HIP = "Character1_Hips"
LEG = "Character1_LeftUpLeg"
ALLOWED = {HIP, LEG}
BAND_CM = 2.5
SEAM_CM = 0.2

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
    out = {}
    for g in me.vertices[index].groups:
        name = mesh.vertex_groups[g.group].name
        if g.weight > 0.001:
            out[name] = g.weight
    return out


def dominant(index):
    best_name, best_w = None, -1.0
    for name, weight in groups_of(index).items():
        if weight > best_w:
            best_name, best_w = name, weight
    return best_name


kd = kdtree.KDTree(len(me.vertices))
for i, v in enumerate(me.vertices):
    kd.insert(world(v.co), i)
kd.balance()

affected = set(island)
for i in island:
    co = world(me.vertices[i].co)
    normal = (mesh.matrix_world.to_3x3() @ me.vertices[i].normal).normalized()
    for _co, j, dist in kd.find_range(co, SEAM_CM):
        if j in affected:
            continue
        if not set(groups_of(j)).issubset(ALLOWED):
            continue
        other_n = (mesh.matrix_world.to_3x3() @ me.vertices[j].normal).normalized()
        if normal.dot(other_n) < 0.5:
            continue
        affected.add(j)

hip_set = {i for i in affected if dominant(i) == HIP}
leg_set = {i for i in affected if dominant(i) == LEG}
skipped = sorted(i for i in affected if dominant(i) not in ALLOWED)

hip_kd = kdtree.KDTree(max(1, len(hip_set)))
for i in hip_set:
    hip_kd.insert(world(me.vertices[i].co), i)
hip_kd.balance()
leg_kd = kdtree.KDTree(max(1, len(leg_set)))
for i in leg_set:
    leg_kd.insert(world(me.vertices[i].co), i)
leg_kd.balance()

vg_hip = mesh.vertex_groups[HIP]
vg_leg = mesh.vertex_groups[LEG]
changed = 0
for i in affected:
    if i in skipped:
        continue
    co = world(me.vertices[i].co)
    if i in hip_set:
        _co, _j, dist = leg_kd.find(co)
        if dist >= BAND_CM:
            continue
        w_hip = 0.5 + 0.5 * (dist / BAND_CM)
    elif i in leg_set:
        _co, _j, dist = hip_kd.find(co)
        if dist >= BAND_CM:
            continue
        w_leg = 0.5 + 0.5 * (dist / BAND_CM)
        w_hip = 1.0 - w_leg
    else:
        continue
    if i in hip_set:
        w_leg = 1.0 - w_hip
    vg_hip.add([i], float(w_hip), "REPLACE")
    vg_leg.add([i], float(w_leg), "REPLACE")
    changed += 1

# Edges inside the affected surface, for before/after stretch scans.
edges = []
seen_edges = set()
for i in affected:
    for edge in bm.verts[i].link_edges:
        other = edge.other_vert(bm.verts[i]).index
        if other not in affected:
            continue
        key = (min(i, other), max(i, other))
        if key in seen_edges:
            continue
        seen_edges.add(key)
        edges.append(key)


def posed_stats(frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(deps)
    em = ev.to_mesh()
    pa = world(em.vertices[A].co)
    pb = world(em.vertices[B].co)
    longest = 0.0
    longest_edge = None
    over_2 = 0
    over_5 = 0
    for i, j in edges:
        length = (world(em.vertices[i].co) - world(em.vertices[j].co)).length * scale
        if length > longest:
            longest = length
            longest_edge = [i, j, round(length, 4)]
        if length > 2.0:
            over_2 += 1
        if length > 5.0:
            over_5 += 1
    ev.to_mesh_clear()
    return {
        "frame": frame,
        "target_edge_cm": round((pa - pb).length * scale, 6),
        "longest_affected_edge_cm": longest_edge,
        "edges_over_2cm": over_2,
        "edges_over_5cm": over_5,
    }


act = bpy.data.actions["VALKUR_TEST_attack"]
ad = arm.animation_data_create()
ad.action = act
ad.action_slot = act.slots[0]
scene.frame_end = 309
arm.data.pose_position = "POSE"

# The weights above are already changed. Capture AFTER first, then we need BEFORE.
# BEFORE was measured in diag_island.json. Recompute AFTER here.
after = {}
for label, action_name, frames in (
    ("attack", "VALKUR_TEST_attack", [95, 185]),
    ("idle", "VALKUR_TEST_idle", [90]),
    ("walk", "VALKUR_TEST_walk", [21, 61]),
    ("defense", "VALKUR_TEST_defense", [95, 185]),
):
    action = bpy.data.actions[action_name]
    ad.action = action
    ad.action_slot = action.slots[0]
    after[label] = [posed_stats(frame) for frame in frames]

hip_z = [(world(me.vertices[i].co).z * scale) for i in hip_set]
leg_z = [(world(me.vertices[i].co).z * scale) for i in leg_set]
report = {
    "decision": "body skin on the front-left upper thigh, not skirt cloth or equipment",
    "bones": [HIP, LEG],
    "band_cm": BAND_CM,
    "seam_cm": SEAM_CM,
    "island_verts": len(island),
    "affected_verts": len(affected),
    "seam_added": len(affected) - len(island),
    "hip_verts_before": len(hip_set),
    "leg_verts_before": len(leg_set),
    "hip_z_cm": [round(min(hip_z), 3), round(max(hip_z), 3)] if hip_z else None,
    "leg_z_cm": [round(min(leg_z), 3), round(max(leg_z), 3)] if leg_z else None,
    "weights_changed": changed,
    "skipped_other_bones": skipped,
    "affected_edges": len(edges),
    "after": after,
    "rest_edge_cm": round((world(me.vertices[A].co) - world(me.vertices[B].co)).length * scale, 6),
}

# Close-up after the fix, textured, attack frame 95.
ad.action = act
ad.action_slot = act.slots[0]
scene.frame_set(95)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(deps)
em = ev.to_mesh()
center = Vector((0, 0, 0))
for i in island:
    center += world(em.vertices[i].co)
center /= len(island)
ev.to_mesh_clear()

cam_data = bpy.data.cameras.new("HipThighCam")
cam = bpy.data.objects.new("HipThighCam", cam_data)
scene.collection.objects.link(cam)
cam_data.lens = 50
cam_data.clip_start = 0.01
cam_data.clip_end = 10000
view = Vector((-0.35, -1.0, 0.05)).normalized()
cam.location = center + view * 28.0
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = engine
        break
    except Exception:
        continue
scene.render.resolution_x = 960
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
try:
    scene.eevee.taa_render_samples = 16
except Exception:
    pass
scene.render.filepath = RENDER_DIR + r"\hip-thigh-attack-95-after.png"
bpy.ops.render.render(write_still=True)

# Remove the diagnostic camera before saving the repair file.
bpy.data.objects.remove(cam, do_unlink=True)
bpy.data.cameras.remove(cam_data)

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
bpy.ops.wm.save_as_mainfile(filepath=DST, copy=True)
print("SAVED", DST)
print("CHANGED", changed)
