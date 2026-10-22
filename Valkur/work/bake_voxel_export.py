"""Solid-shell color bake, then write the game mesh and diffuse. Flat normal stays."""
import array
import os
import struct

import bpy

OUT_DIR = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur"
WORK = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work"


def write_dds(image, path):
    width, height = image.size
    raw = array.array("f", [0.0]) * (width * height * 4)
    image.pixels.foreach_get(raw)
    body = bytearray(width * height * 4)
    for y in range(height):
        src_y = height - 1 - y
        for x in range(width):
            i = ((src_y * width) + x) * 4
            o = ((y * width) + x) * 4
            body[o] = int(max(0.0, min(1.0, raw[i + 2])) * 255)
            body[o + 1] = int(max(0.0, min(1.0, raw[i + 1])) * 255)
            body[o + 2] = int(max(0.0, min(1.0, raw[i])) * 255)
            body[o + 3] = 255
    header = struct.pack("<4sI", b"DDS ", 124)
    header += struct.pack("<7I", 0x100F, height, width, width * 4, 0, 0, 0)
    header += struct.pack("<10I", *([0] * 10))
    header += struct.pack("<8I", 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    header += struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    with open(path, "wb") as handle:
        handle.write(header)
        handle.write(body)
    print("DDS", os.path.getsize(path), flush=True)


def flat_dds(path, size, pixel):
    header = struct.pack("<4sI", b"DDS ", 124)
    header += struct.pack("<7I", 0x100F, size, size, size * 4, 0, 0, 0)
    header += struct.pack("<10I", *([0] * 10))
    header += struct.pack("<8I", 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    header += struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    with open(path, "wb") as handle:
        handle.write(header + bytes(pixel) * (size * size))


for name in ("Image_0", "Image_1", "Image_2"):
    image = bpy.data.images[name]
    image.filepath = os.path.join(OUT_DIR, "src_" + name + ".png")
    image.source = "FILE"
    image.reload()

src = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(mod.object for mod in src.modifiers if mod.type == "ARMATURE")
arm.data.pose_position = "REST"
bpy.ops.object.select_all(action="DESELECT")
src.select_set(True)
bpy.context.view_layer.objects.active = src
high = src.copy()
high.data = src.data.copy()
high.name = "Valkur_high"
bpy.context.collection.objects.link(high)
high.select_set(True)
bpy.context.view_layer.objects.active = high
world = high.matrix_world.copy()
high.parent = None
high.matrix_world = world
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for mod in list(high.modifiers):
    high.modifiers.remove(mod)

low = high.copy()
low.data = high.data.copy()
low.name = "Valkur_low"
bpy.context.collection.objects.link(low)
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
low.select_set(True)
bpy.context.view_layer.objects.active = low
for mod in list(low.modifiers):
    low.modifiers.remove(mod)

voxel = low.modifiers.new("voxel", "REMESH")
voxel.mode = "VOXEL"
voxel.voxel_size = 0.72
voxel.adaptivity = 0.0
bpy.ops.object.modifier_apply(modifier=voxel.name)
print("VOXEL_FACES", len(low.data.polygons), flush=True)
if len(low.data.polygons) > 70000:
    dec = low.modifiers.new("trim", "DECIMATE")
    dec.ratio = 70000 / len(low.data.polygons)
    bpy.ops.object.modifier_apply(modifier=dec.name)
    print("TRIMMED", len(low.data.polygons), flush=True)
bpy.ops.object.shade_smooth()

transfer = low.modifiers.new("weights", "DATA_TRANSFER")
transfer.object = high
transfer.use_vert_data = True
transfer.data_types_verts = {"VGROUP_WEIGHTS"}
transfer.vert_mapping = "POLYINTERP_NEAREST"
bpy.ops.object.datalayout_transfer(modifier=transfer.name)
bpy.ops.object.modifier_apply(modifier=transfer.name)
print("GROUPS", len(low.vertex_groups), flush=True)

while low.data.uv_layers:
    low.data.uv_layers.remove(low.data.uv_layers[0])
low.data.uv_layers.new(name="UVMap")
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=1.05, island_margin=0.004)
bpy.ops.object.mode_set(mode="OBJECT")

bake_img = bpy.data.images.new("valkur_bake", 2048, 2048, alpha=False)
bake_img.colorspace_settings.name = "sRGB"
bake_mat = bpy.data.materials.new("bake_target")
bake_mat.use_nodes = True
tex_node = bake_mat.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = bake_img
bake_mat.node_tree.nodes.active = tex_node
low.data.materials.clear()
low.data.materials.append(bake_mat)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 1
scene.render.bake.margin = 16
try:
    scene.render.bake.margin_type = "EXTEND"
except AttributeError:
    pass

for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
high.select_set(True)
low.select_set(True)
bpy.context.view_layer.objects.active = low
print("BAKE_COLOR", flush=True)
bpy.ops.object.bake(
    type="DIFFUSE",
    pass_filter={"COLOR"},
    use_selected_to_active=True,
    cage_extrusion=1.4,
    max_ray_distance=8.0,
)
print("BAKE_DONE", flush=True)

for vertex in low.data.vertices:
    weights = []
    for group in low.vertex_groups:
        try:
            weights.append((group.index, group.weight(vertex.index)))
        except RuntimeError:
            pass
    weights.sort(key=lambda item: item[1], reverse=True)
    keep = [(index, weight) for index, weight in weights[:4] if weight > 0]
    for index, _weight in weights[4:]:
        low.vertex_groups[index].remove([vertex.index])
    total = sum(weight for _index, weight in keep)
    if total > 0:
        for index, weight in keep:
            low.vertex_groups[index].add([vertex.index], weight / total, "REPLACE")
print("WEIGHTS", flush=True)

low.data.name = "valkurShape"
skin = low.modifiers.new("CK3 skin", "ARMATURE")
skin.object = arm
skin.use_vertex_groups = True
pdx = bpy.data.materials.new("PDXmat_valkur")
pdx["shader"] = "standard"
pdx["diff"] = "valkur_diffuse.dds"
pdx["n"] = "valkur_normal.dds"
pdx["spec"] = "valkur_properties.dds"
low.data.materials.clear()
low.data.materials.append(pdx)

write_dds(bake_img, os.path.join(OUT_DIR, "valkur_diffuse.dds"))
flat_dds(os.path.join(OUT_DIR, "valkur_normal.dds"), 4, (255, 128, 128, 255))
flat_dds(os.path.join(OUT_DIR, "valkur_properties.dds"), 4, (180, 0, 40, 255))

for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
low.select_set(True)
bpy.context.view_layer.objects.active = low
result = bpy.ops.io_pdx_mesh.export_mesh(
    filepath=os.path.join(OUT_DIR, "valkur.mesh"),
    chk_mesh=True,
    chk_skel=True,
    chk_locs=False,
    chk_selected=True,
    chk_asset=False,
    chk_gfx=False,
)
print("MESH", result, len(low.data.polygons), flush=True)
