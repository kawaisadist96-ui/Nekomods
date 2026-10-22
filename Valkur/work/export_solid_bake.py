"""Fuse the character into one surface, bake the original paint onto it, preview, then export."""
import array
import os
import struct

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


for image in bpy.data.images:
    if image.packed_file and image.size[0] > 0:
        image.filepath_raw = os.path.join(OUT_DIR, "src_" + image.name + ".png")
        image.file_format = "PNG"
        if not os.path.exists(image.filepath_raw):
            image.save()
        print("IMAGE", image.name, image.size[0], flush=True)

src = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in src.modifiers if m.type == "ARMATURE" and m.object)
arm.data.pose_position = "REST"

bpy.ops.object.select_all(action="DESELECT")
src.select_set(True)
bpy.context.view_layer.objects.active = src
high = src.copy()
high.data = src.data.copy()
high.name = "Valkur_bake_high"
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
low.name = "Valkur_test_export"
bpy.context.collection.objects.link(low)
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
low.select_set(True)
bpy.context.view_layer.objects.active = low
for mod in list(low.modifiers):
    low.modifiers.remove(mod)

voxel = low.modifiers.new("voxel", "REMESH")
voxel.mode = "VOXEL"
voxel.voxel_size = 1.15
voxel.adaptivity = 0.0
print("VOXEL", flush=True)
bpy.ops.object.modifier_apply(modifier=voxel.name)
print("VOXEL_FACES", len(low.data.polygons), flush=True)
if len(low.data.polygons) > 35000:
    dec = low.modifiers.new("trim", "DECIMATE")
    dec.ratio = 35000 / len(low.data.polygons)
    bpy.ops.object.modifier_apply(modifier=dec.name)
    print("TRIMMED", len(low.data.polygons), flush=True)

low.data.name = "valkurShape"
bpy.ops.object.shade_smooth()

transfer = low.modifiers.new("weights", "DATA_TRANSFER")
transfer.object = high
transfer.use_vert_data = True
transfer.data_types_verts = {"VGROUP_WEIGHTS"}
transfer.vert_mapping = "POLYINTERP_NEAREST"
bpy.ops.object.datalayout_transfer(modifier=transfer.name)
bpy.ops.object.modifier_apply(modifier=transfer.name)
print("GROUPS", len(low.vertex_groups), flush=True)

for vertex in low.data.vertices:
    weights = []
    for group in low.vertex_groups:
        try:
            weights.append((group.index, group.weight(vertex.index)))
        except RuntimeError:
            pass
    weights.sort(key=lambda item: item[1], reverse=True)
    for index, _weight in weights[4:]:
        low.vertex_groups[index].remove([vertex.index])
    keep = weights[:4]
    total = sum(weight for _index, weight in keep)
    if total > 0:
        for index, weight in keep:
            low.vertex_groups[index].add([vertex.index], weight / total, "REPLACE")

arm_mod = low.modifiers.new("CK3 skin", "ARMATURE")
arm_mod.object = arm
arm_mod.use_vertex_groups = True

while low.data.uv_layers:
    low.data.uv_layers.remove(low.data.uv_layers[0])
low.data.uv_layers.new(name="UVMap")
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
print("UNWRAP", bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.03), flush=True)
bpy.ops.object.mode_set(mode="OBJECT")

albedo = bpy.data.images["Image_0"]
simple = bpy.data.materials.new("albedo_only")
simple.use_nodes = True
nodes = simple.node_tree.nodes
nodes.clear()
output = nodes.new("ShaderNodeOutputMaterial")
emission = nodes.new("ShaderNodeEmission")
source_tex = nodes.new("ShaderNodeTexImage")
source_tex.image = albedo
simple.node_tree.links.new(source_tex.outputs["Color"], emission.inputs["Color"])
simple.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
high.data.materials.clear()
high.data.materials.append(simple)

bake_img = bpy.data.images.new("valkur_bake", 2048, 2048, alpha=False)
bake_img.colorspace_settings.name = "sRGB"
bake_mat = bpy.data.materials.new("valkur_bake_target")
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
scene.render.bake.margin = 8
scene.render.bake.use_clear = True
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
high.select_set(True)
low.select_set(True)
bpy.context.view_layer.objects.active = low
print("BAKE", flush=True)
bpy.ops.object.bake(
    type="EMIT",
    use_selected_to_active=True,
    cage_extrusion=1.5,
    max_ray_distance=6.0,
)
print("BAKE_DONE", flush=True)

preview_mat = bpy.data.materials.new("valkur_preview")
preview_mat.use_nodes = True
preview_bsdf = preview_mat.node_tree.nodes.get("Principled BSDF")
preview_tex = preview_mat.node_tree.nodes.new("ShaderNodeTexImage")
preview_tex.image = bake_img
preview_mat.node_tree.links.new(preview_tex.outputs["Color"], preview_bsdf.inputs["Base Color"])
low.data.materials.clear()
low.data.materials.append(preview_mat)
for obj in scene.objects:
    obj.hide_render = obj is not low
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
print("PREVIEW", PREVIEW, flush=True)

write_dds(bake_img, os.path.join(OUT_DIR, "valkur_diffuse.dds"))
solid_dds(os.path.join(OUT_DIR, "valkur_normal.dds"), 4, 4, (255, 128, 128, 255))
solid_dds(os.path.join(OUT_DIR, "valkur_properties.dds"), 4, 4, (180, 0, 40, 255))

pdx = bpy.data.materials.new("PDXmat_valkur")
pdx["shader"] = "standard"
pdx["diff"] = "valkur_diffuse.dds"
pdx["n"] = "valkur_normal.dds"
pdx["spec"] = "valkur_properties.dds"
low.data.materials.clear()
low.data.materials.append(pdx)
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
