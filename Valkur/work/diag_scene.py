"""Read-only scene and skirt-edge audit. Does not save the blend."""
import bpy
import json
import os
from collections import Counter, defaultdict
from mathutils import Vector

OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\diag_scene.json"
A, B = 809011, 809035
SHOULDER = (221522, 221525)

report = {"file": bpy.data.filepath, "objects": [], "actions": []}

for obj in bpy.data.objects:
    item = {
        "name": obj.name,
        "type": obj.type,
        "hide": obj.hide_get(),
        "parent": obj.parent.name if obj.parent else None,
    }
    if obj.type == "MESH":
        item["verts"] = len(obj.data.vertices)
        item["polys"] = len(obj.data.polygons)
        item["materials"] = [s.name for s in obj.material_slots]
        item["modifiers"] = []
        for mod in obj.modifiers:
            md = {"name": mod.name, "type": mod.type}
            if mod.type == "ARMATURE":
                md["object"] = mod.object.name if mod.object else None
                md["use_vertex_groups"] = mod.use_vertex_groups
                md["show_viewport"] = mod.show_viewport
            item["modifiers"].append(md)
    if obj.type == "ARMATURE":
        item["bones"] = len(obj.data.bones)
        item["bone_names"] = [b.name for b in obj.data.bones]
    report["objects"].append(item)

for act in bpy.data.actions:
    report["actions"].append({
        "name": act.name,
        "frame_range": [float(act.frame_range[0]), float(act.frame_range[1])],
        "fcurves": len(act.fcurves) if hasattr(act, "fcurves") else None,
    })

mesh_obj = None
for obj in bpy.data.objects:
    if obj.type == "MESH" and len(obj.data.vertices) > 100000:
        mesh_obj = obj
        break

arm = None
for mod in mesh_obj.modifiers:
    if mod.type == "ARMATURE" and mod.object:
        arm = mod.object
        break

scene = bpy.context.scene
report["scene"] = {
    "fps": scene.render.fps,
    "frame_current": scene.frame_current,
    "frame_start": scene.frame_start,
    "frame_end": scene.frame_end,
    "unit": scene.unit_settings.system,
    "scale_length": scene.unit_settings.scale_length,
}
report["mesh"] = mesh_obj.name
report["armature"] = arm.name if arm else None
if arm and arm.animation_data:
    ad = arm.animation_data
    report["armature_action"] = ad.action.name if ad.action else None
    report["nla"] = [t.name for t in ad.nla_tracks]
else:
    report["armature_action"] = None

me = mesh_obj.data
report["mesh_counts"] = {"verts": len(me.vertices), "polys": len(me.polygons), "edges": len(me.edges)}


def vert_info(index):
    v = me.vertices[index]
    groups = []
    for g in v.groups:
        groups.append([mesh_obj.vertex_groups[g.group].name, round(g.weight, 6)])
    groups.sort(key=lambda x: -x[1])
    return {
        "index": index,
        "co_m": [round(c, 6) for c in v.co],
        "co_cm": [round(c * 100.0, 6) for c in v.co],
        "weights": groups[:8],
    }


report["pair"] = [vert_info(A), vert_info(B)]
report["shoulder_pair"] = [vert_info(SHOULDER[0]), vert_info(SHOULDER[1])]
report["index_ok"] = A < len(me.vertices) and B < len(me.vertices)

# Confirm the two verts share an edge.
linked = False
for e in me.edges:
    vs = tuple(e.vertices)
    if vs == (A, B) or vs == (B, A):
        linked = True
        break
if not linked:
    # fallback: polygon adjacency
    polys_a = set()
    for p in me.polygons:
        if A in p.vertices and B in p.vertices:
            linked = True
            break
report["pair_shares_polygon_or_edge_scan"] = "deferred"

# Edge existence without scanning all edges: use loop adjacency via a dict built only if needed.
# Build vertex->polygons is heavy; use bmesh for the two verts.
import bmesh
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()
va = bm.verts[A]
vb = bm.verts[B]
report["pair_linked"] = any(e.other_vert(va) == vb for e in va.link_edges)
if report["pair_linked"]:
    rest = (va.co - vb.co).length * 100.0
    report["rest_edge_cm"] = rest

# UV island flood from A, limited by UV continuity across shared edges.
uv_layer = bm.loops.layers.uv.active
report["uv_layer"] = uv_layer.name if uv_layer else None


def loop_uv(vert, face):
    for loop in face.loops:
        if loop.vert == vert:
            return loop[uv_layer].uv.copy()
    return None


island = set()
stack = [f.index for f in va.link_faces]
seen_faces = set(stack)
truncated = False
while stack and len(seen_faces) < 80000:
    fi = stack.pop()
    face = bm.faces[fi]
    island.update(v.index for v in face.verts)
    for edge in face.edges:
        for of in edge.link_faces:
            if of.index in seen_faces or of == face:
                continue
            ok = True
            for vert in edge.verts:
                u0 = loop_uv(vert, face)
                u1 = loop_uv(vert, of)
                if u0 is None or u1 is None or (u0 - u1).length > 1e-4:
                    ok = False
                    break
            if ok:
                seen_faces.add(of.index)
                stack.append(of.index)
if stack and len(seen_faces) >= 80000:
    truncated = True

island_list = sorted(island)
report["island_truncated"] = truncated
report["island_faces"] = len(seen_faces)
report["island_verts"] = len(island_list)
xs, ys, zs = [], [], []
group_counts = Counter()
hard = Counter()
for i in island_list:
    co = me.vertices[i].co
    xs.append(co.x)
    ys.append(co.y)
    zs.append(co.z)
    groups = [(mesh_obj.vertex_groups[g.group].name, g.weight) for g in me.vertices[i].groups if g.weight > 0.001]
    groups.sort(key=lambda x: -x[1])
    if groups:
        group_counts[groups[0][0]] += 1
        if groups[0][1] > 0.95:
            hard[groups[0][0]] += 1
report["island_bbox_cm"] = {
    "min": [round(min(xs) * 100, 3), round(min(ys) * 100, 3), round(min(zs) * 100, 3)],
    "max": [round(max(xs) * 100, 3), round(max(ys) * 100, 3), round(max(zs) * 100, 3)],
}
report["island_dominant_groups"] = group_counts.most_common(12)
report["island_hard_groups"] = hard.most_common(12)

# Bone heads in armature local / world for skirt and leg.
bones_of_interest = [
    "Character1_Hips",
    "Character1_LeftUpLeg",
    "Character1_RightUpLeg",
    "Left_skirt_front_1",
    "Left_skirt_front_2",
    "Left_skirt_front_3",
    "Left_skirt_back_1",
    "Rright_skirt_front_1",
    "Rright_skirt_front_2",
    "Rright_skirt_front_3",
]
bone_pos = {}
if arm:
    for name in bones_of_interest:
        bone = arm.data.bones.get(name)
        if not bone:
            continue
        head_w = arm.matrix_world @ bone.head_local
        bone_pos[name] = [round(c * 100, 3) for c in head_w]
report["bone_heads_cm"] = bone_pos

# Pose the attack clip at frame 95 and measure the edge on the evaluated mesh.
if arm and arm.animation_data:
    act = bpy.data.actions.get("VALKUR_TEST_attack")
    if act:
        arm.animation_data.action = act
        scene.frame_set(95)
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
        ev = mesh_obj.evaluated_get(deps)
        em = ev.to_mesh()
        pa = em.vertices[A].co
        pb = em.vertices[B].co
        # evaluated coords are in object space of evaluated object
        report["posed_frame"] = 95
        report["posed_action"] = act.name
        report["posed_edge_cm"] = (pa - pb).length * 100.0
        report["posed_a_cm"] = [round(c * 100, 4) for c in pa]
        report["posed_b_cm"] = [round(c * 100, 4) for c in pb]
        ev.to_mesh_clear()

# Sample a few island verts' distance to left thigh bone vs nearest skirt bone, rest pose.
scene.frame_set(1)
if arm:
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()

bm.free()

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print("WROTE", OUT)
