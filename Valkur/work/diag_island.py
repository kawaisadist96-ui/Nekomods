"""World-space identity of the failing skirt edge. Does not save the blend."""
import bpy
import json
import math
from collections import Counter
from mathutils import Vector, kdtree

OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\diag_island.json"
RENDER_DIR = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work"
A, B = 809011, 809035

mesh = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in mesh.modifiers if m.type == "ARMATURE" and m.object)
me = mesh.data
scene = bpy.context.scene

report = {
    "mesh": mesh.name,
    "armature": arm.name,
    "mesh_parent": mesh.parent.name if mesh.parent else None,
    "mesh_matrix_world": [[round(v, 8) for v in row] for row in mesh.matrix_world],
    "arm_matrix_world": [[round(v, 8) for v in row] for row in arm.matrix_world],
    "mesh_scale": [round(v, 8) for v in mesh.scale],
    "arm_scale": [round(v, 8) for v in arm.scale],
    "parents": [],
}

node = mesh.parent
while node:
    report["parents"].append({
        "name": node.name,
        "type": node.type,
        "scale": [round(v, 8) for v in node.scale],
        "location": [round(v, 6) for v in node.location],
        "matrix_world": [[round(v, 8) for v in row] for row in node.matrix_world],
    })
    node = node.parent


def world_cm(co):
    w = mesh.matrix_world @ Vector(co)
    return w * 100.0 * scene.unit_settings.scale_length


import bmesh
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
uv_layer = bm.loops.layers.uv.active
va = bm.verts[A]


def loop_uv(vert, face):
    for loop in face.loops:
        if loop.vert == vert:
            return loop[uv_layer].uv.copy()
    return None


stack = [f.index for f in va.link_faces]
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
report["island_faces"] = len(seen)
report["island_verts"] = len(island)

coords = [world_cm(me.vertices[i].co) for i in island]
xs = [c.x for c in coords]
ys = [c.y for c in coords]
zs = [c.z for c in coords]
report["bbox_cm"] = {
    "min": [round(min(xs), 3), round(min(ys), 3), round(min(zs), 3)],
    "max": [round(max(xs), 3), round(max(ys), 3), round(max(zs), 3)],
    "size": [round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3), round(max(zs) - min(zs), 3)],
}
centroid = Vector((sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)))
report["centroid_cm"] = [round(c, 3) for c in centroid]

normals = []
for fi in seen:
    n = (mesh.matrix_world.to_3x3() @ bm.faces[fi].normal).normalized()
    normals.append(n)
avg_n = Vector((0, 0, 0))
for n in normals:
    avg_n += n
avg_n.normalize()
report["average_normal_world"] = [round(c, 4) for c in avg_n]

# Open boundary: edges used by only one island face.
boundary = 0
internal = 0
for fi in seen:
    for edge in bm.faces[fi].edges:
        island_faces = [f.index for f in edge.link_faces if f.index in seen]
        if len(island_faces) == 1:
            boundary += 1
        else:
            internal += 1
report["boundary_edges"] = boundary // 1
report["internal_edge_visits"] = internal

groups = Counter()
for i in island:
    best = None
    for g in me.vertices[i].groups:
        if best is None or g.weight > best[1]:
            best = (mesh.vertex_groups[g.group].name, g.weight)
    if best and best[1] > 0.5:
        groups[best[0]] += 1
report["dominant_weight"] = groups.most_common()

# Texture sample. Prefer the largest packed image.
import array
images = sorted(bpy.data.images, key=lambda im: im.size[0] * im.size[1], reverse=True)
img = images[0]
report["albedo_image"] = {"name": img.name, "size": list(img.size)}
w, h = img.size
pixels = array.array("f", [0.0]) * (w * h * 4)
img.pixels.foreach_get(pixels)
samples = []
step = max(1, len(seen) // 80)
for n, fi in enumerate(sorted(seen)):
    if n % step:
        continue
    face = bm.faces[fi]
    uv = Vector((0, 0))
    for loop in face.loops:
        uv += loop[uv_layer].uv
    uv /= len(face.loops)
    x = min(w - 1, max(0, int(uv.x * w)))
    y = min(h - 1, max(0, int(uv.y * h)))
    i = (y * w + x) * 4
    samples.append(pixels[i:i + 3])
if samples:
    avg = [sum(s[k] for s in samples) / len(samples) for k in range(3)]
    report["albedo_sample_count"] = len(samples)
    report["albedo_average_rgb"] = [round(c, 4) for c in avg]
    # rough class
    r, g, b = avg
    if r > 0.35 and r > g * 1.25 and r > b * 1.25:
        kind = "red_cloth"
    elif abs(r - g) < 0.08 and abs(g - b) < 0.08 and r > 0.25:
        kind = "neutral_gray_or_metal"
    elif r > g and g > b and r < 0.75:
        kind = "skin_or_tan"
    else:
        kind = "unclassified"
    report["albedo_guess"] = kind

# Separation from the rest of the body.
kd = kdtree.KDTree(len(me.vertices))
for i, v in enumerate(me.vertices):
    kd.insert(v.co, i)
kd.balance()
shell = []
sample_ids = list(sorted(island))[:: max(1, len(island) // 40)]
for i in sample_ids:
    co = me.vertices[i].co
    hits = kd.find_n(co, 12)
    outside = None
    for hit_co, hit_i, dist in hits:
        if hit_i not in island and dist > 1e-8:
            outside = (hit_i, dist)
            break
    if not outside:
        continue
    gap_cm = (world_cm(co) - world_cm(me.vertices[outside[0]].co)).length
    n = me.vertices[i].normal
    delta = (me.vertices[outside[0]].co - co).normalized()
    shell.append({
        "vertex": i,
        "outside": outside[0],
        "gap_cm": round(gap_cm, 4),
        "normal_alignment": round(delta.dot(n), 4),
    })
report["outside_gaps"] = shell
if shell:
    gaps = sorted(s["gap_cm"] for s in shell)
    report["outside_gap_cm_median"] = gaps[len(gaps) // 2]
    report["outside_gap_cm_min"] = gaps[0]

wa = world_cm(me.vertices[A].co)
wb = world_cm(me.vertices[B].co)
report["rest_edge_cm"] = round((wa - wb).length, 6)
report["rest_a_cm"] = [round(c, 4) for c in wa]
report["rest_b_cm"] = [round(c, 4) for c in wb]

# Pose attack frame 95.
act = bpy.data.actions["VALKUR_TEST_attack"]
report["action_slots"] = []
for slot in getattr(act, "slots", []):
    report["action_slots"].append({
        "identifier": getattr(slot, "identifier", None),
        "display": getattr(slot, "name_display", None),
        "type": str(getattr(slot, "target_id_type", "")),
    })
report["action_layers"] = len(getattr(act, "layers", []))
ad = arm.animation_data_create()
ad.action = act
if getattr(act, "slots", None):
    target = act.slots[0] if act.slots else None
    for slot in act.slots:
        ident = str(getattr(slot, "identifier", "")) + " " + str(getattr(slot, "name_display", ""))
        slot_type = str(getattr(slot, "target_id_type", ""))
        if "ARMATURE" in ident.upper() or arm.name in ident or slot_type in {"OBJECT", "ARMATURE"}:
            target = slot
            break
    if target:
        ad.action_slot = target
        chosen = ad.action_slot
        report["assigned_slot"] = {
            "identifier": getattr(chosen, "identifier", None),
            "display": getattr(chosen, "name_display", None),
        }
scene.frame_end = max(scene.frame_end, 309)
scene.frame_set(95)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(deps)
em = ev.to_mesh()
pa = mesh.matrix_world @ em.vertices[A].co
pb = mesh.matrix_world @ em.vertices[B].co
# evaluated vertex coords are in the original object's local space
scale = 100.0 * scene.unit_settings.scale_length
report["posed_edge_cm"] = round((pa - pb).length * scale, 6)
report["posed_a_cm"] = [round(c * scale, 4) for c in pa]
report["posed_b_cm"] = [round(c * scale, 4) for c in pb]
ev.to_mesh_clear()

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print("WROTE", OUT)

# Mark the island and render rest + attack close-ups. Memory only; file is not saved.
mark = bpy.data.materials.new("VALKUR_ISLAND_MARK")
mark.use_nodes = True
bsdf = next(n for n in mark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Base Color"].default_value = (1.0, 0.15, 0.05, 1.0)
bsdf.inputs["Roughness"].default_value = 0.45
me.materials.append(mark)
mark_index = len(me.materials) - 1
for fi in seen:
    me.polygons[fi].material_index = mark_index

center = mesh.matrix_world @ (sum((me.vertices[i].co for i in island), Vector()) / len(island))
cam_data = bpy.data.cameras.new("IslandCam")
cam = bpy.data.objects.new("IslandCam", cam_data)
scene.collection.objects.link(cam)
cam_data.lens = 50
cam_data.clip_start = 0.01
cam_data.clip_end = 10000
# Look from the front (-Y) and slightly outside the average normal.
view = Vector((avg_n.x, avg_n.y, avg_n.z * 0.25))
if view.length < 0.2:
    view = Vector((0, -1, 0.15))
view.normalize()
distance = max(report["bbox_cm"]["size"]) * 2.2
if distance < 8:
    distance = 18
cam.location = center + view * (distance / (100.0 * scene.unit_settings.scale_length))
direction = center - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
    try:
        scene.render.engine = engine
        report["render_engine"] = engine
        break
    except Exception:
        continue
scene.render.resolution_x = 960
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
if scene.render.engine.startswith("BLENDER_EEVEE"):
    try:
        scene.eevee.taa_render_samples = 16
    except Exception as exc:
        report["eevee_samples_error"] = str(exc)

def shoot(path, frame):
    scene.frame_set(frame)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

arm.data.pose_position = "POSE"
shoot(RENDER_DIR + r"\island-rest.png", 1)
shoot(RENDER_DIR + r"\island-attack-95.png", 95)
print("RENDERS DONE")

bm.free()
