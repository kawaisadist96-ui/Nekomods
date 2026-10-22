"""Reduce the mesh inside each original UV island so the painted texture still lines up."""
import array
import os
import struct

import bmesh
import bpy

OUT_DIR = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur"
PREVIEW = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-preview.png"
os.makedirs(OUT_DIR, exist_ok=True)


def write_dds_bytes(path, width, height, body):
    header = struct.pack("<4sI", b"DDS ", 124)
    header += struct.pack("<7I", 0x100F, height, width, width * 4, 0, 0, 0)
    header += struct.pack("<10I", *([0] * 10))
    header += struct.pack("<8I", 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    header += struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    with open(path, "wb") as handle:
        handle.write(header)
        handle.write(body)


def write_dds(image, path):
    width, height = image.size
    pixels = array.array("f", [0.0]) * (width * height * 4)
    image.pixels.foreach_get(pixels)
    body = bytearray(width * height * 4)
    for y in range(height):
        src_y = height - 1 - y
        for x in range(width):
            i = ((src_y * width) + x) * 4
            o = ((y * width) + x) * 4
            body[o] = int(max(0.0, min(1.0, pixels[i + 2])) * 255)
            body[o + 1] = int(max(0.0, min(1.0, pixels[i + 1])) * 255)
            body[o + 2] = int(max(0.0, min(1.0, pixels[i])) * 255)
            body[o + 3] = 255
    write_dds_bytes(path, width, height, body)
    print("DDS", os.path.basename(path), os.path.getsize(path), flush=True)


def solid_dds(path, width, height, bgra):
    write_dds_bytes(path, width, height, bytes(bgra) * (width * height))


def clamp_weights(mesh, limit=4):
    for vertex in mesh.data.vertices:
        weights = []
        for group in mesh.vertex_groups:
            try:
                weights.append((group.index, group.weight(vertex.index)))
            except RuntimeError:
                pass
        weights.sort(key=lambda item: item[1], reverse=True)
        for index, _weight in weights[limit:]:
            mesh.vertex_groups[index].remove([vertex.index])
        keep = [(index, weight) for index, weight in weights[:limit] if weight > 0]
        total = sum(weight for _index, weight in keep)
        if total > 0:
            for index, weight in keep:
                mesh.vertex_groups[index].add([vertex.index], weight / total, "REPLACE")


albedo = bpy.data.images["Image_0"]
if albedo.packed_file:
    albedo.filepath_raw = os.path.join(OUT_DIR, "src_Image_0.png")
    albedo.file_format = "PNG"
    if not os.path.exists(albedo.filepath_raw):
        albedo.save()

src = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in src.modifiers if m.type == "ARMATURE" and m.object)
arm.data.pose_position = "REST"

bpy.ops.object.select_all(action="DESELECT")
src.select_set(True)
bpy.context.view_layer.objects.active = src
mesh = src.copy()
mesh.data = src.data.copy()
mesh.name = "Valkur_test_export"
bpy.context.collection.objects.link(mesh)
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
world = mesh.matrix_world.copy()
mesh.parent = None
mesh.matrix_world = world
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for mod in list(mesh.modifiers):
    mesh.modifiers.remove(mod)

print("SEAMS", flush=True)
bm = bmesh.new()
bm.from_mesh(mesh.data)
bm.edges.ensure_lookup_table()
uv_layer = bm.loops.layers.uv.active
before = len(bm.verts)
seams = []
for edge in bm.edges:
    if len(edge.link_faces) != 2:
        continue
    uv_at = []
    for face in edge.link_faces:
        found = {}
        for loop in face.loops:
            if loop.vert in edge.verts:
                found[loop.vert.index] = loop[uv_layer].uv
        uv_at.append(found)
    verts = [vert.index for vert in edge.verts]
    if any((uv_at[0][index] - uv_at[1][index]).length > 0.0001 for index in verts):
        seams.append(edge)
print("UV_BREAKS", len(seams), "VERTS_BEFORE", before, flush=True)
if seams:
    bmesh.ops.split_edges(bm, edges=seams)
print("VERTS_AFTER", len(bm.verts), flush=True)
bm.to_mesh(mesh.data)
bm.free()
print("SPLIT", len(mesh.data.vertices), len(mesh.data.polygons), flush=True)

dec = mesh.modifiers.new("island_decimate", "DECIMATE")
dec.decimate_type = "COLLAPSE"
dec.ratio = 0.08
print("DECIMATE", flush=True)
bpy.ops.object.modifier_apply(modifier=dec.name)
print("LOW", len(mesh.data.vertices), len(mesh.data.polygons), flush=True)
bm = bmesh.new()
bm.from_mesh(mesh.data)
loose = [vert for vert in bm.verts if not vert.link_faces]
if loose:
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(mesh.data)
bm.free()
print("CLEAN", len(mesh.data.vertices), len(mesh.data.polygons), flush=True)
if len(mesh.data.vertices) > 200000:
    raise RuntimeError("Decimate left too many vertices.")
mesh.data.name = "valkurShape"
bpy.ops.object.shade_smooth()
clamp_weights(mesh)

arm_mod = mesh.modifiers.new("CK3 skin", "ARMATURE")
arm_mod.object = arm
arm_mod.use_vertex_groups = True

preview = bpy.data.materials.new("valkur_preview")
preview.use_nodes = True
bsdf = preview.node_tree.nodes.get("Principled BSDF")
tex = preview.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = albedo
preview.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
mesh.data.materials.clear()
mesh.data.materials.append(preview)

scene = bpy.context.scene
for obj in scene.objects:
    obj.hide_render = obj is not mesh
light_data = bpy.data.lights.new("preview_sun", "SUN")
light_data.energy = 4
light = bpy.data.objects.new("preview_sun", light_data)
scene.collection.objects.link(light)
light.rotation_euler = (0.9, 0.2, 0.6)
light.hide_render = False
target = bpy.data.objects.new("preview_target", None)
target.location = (0, 0, 95)
scene.collection.objects.link(target)
camera_data = bpy.data.cameras.new("preview_cam")
camera_data.lens = 50
camera = bpy.data.objects.new("preview_cam", camera_data)
scene.collection.objects.link(camera)
camera.location = (90, -280, 140)
track = camera.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.filepath = PREVIEW
bpy.ops.render.render(write_still=True)
print("PREVIEW", flush=True)
raise SystemExit(0)

albedo.scale(2048, 2048)
write_dds(albedo, os.path.join(OUT_DIR, "valkur_diffuse.dds"))
solid_dds(os.path.join(OUT_DIR, "valkur_normal.dds"), 4, 4, (255, 128, 128, 255))
solid_dds(os.path.join(OUT_DIR, "valkur_properties.dds"), 4, 4, (180, 0, 40, 255))

pdx = bpy.data.materials.new("PDXmat_valkur")
pdx["shader"] = "standard"
pdx["diff"] = "valkur_diffuse.dds"
pdx["n"] = "valkur_normal.dds"
pdx["spec"] = "valkur_properties.dds"
mesh.data.materials.clear()
mesh.data.materials.append(pdx)
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
result = bpy.ops.io_pdx_mesh.export_mesh(
    filepath=os.path.join(OUT_DIR, "valkur.mesh"),
    chk_mesh=True,
    chk_skel=True,
    chk_locs=False,
    chk_selected=True,
    chk_asset=False,
    chk_gfx=False,
)
print("MESH", result, len(mesh.data.polygons), flush=True)
