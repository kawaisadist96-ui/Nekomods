"""Bake the original material onto a fresh UV, fill gaps, preview, and export."""
import array
import os
import struct

import bpy

OUT_DIR = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur"
PREVIEW = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-preview.png"

for name in ("Image_0", "Image_1", "Image_2"):
    image = bpy.data.images[name]
    image.filepath = os.path.join(OUT_DIR, "src_" + name + ".png")
    image.source = "FILE"
    image.reload()
    print("RELOAD", name, image.size[0], os.path.exists(image.filepath), flush=True)

src = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
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
dec = low.modifiers.new("decimate", "DECIMATE")
dec.ratio = 0.012
bpy.ops.object.modifier_apply(modifier=dec.name)
print("LOW", len(low.data.polygons), flush=True)
bpy.ops.object.shade_smooth()

while low.data.uv_layers:
    low.data.uv_layers.remove(low.data.uv_layers[0])
low.data.uv_layers.new(name="UVMap")
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
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
scene.render.bake.margin = 32
try:
    scene.render.bake.margin_type = "EXTEND"
except AttributeError:
    pass
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
high.select_set(True)
low.select_set(True)
bpy.context.view_layer.objects.active = low
print("BAKE", flush=True)
bpy.ops.object.bake(
    type="DIFFUSE",
    pass_filter={"COLOR"},
    use_selected_to_active=True,
    cage_extrusion=0.6,
    max_ray_distance=3.0,
)
print("BAKE_DONE", flush=True)
width, height = bake_img.size
pixels = array.array("f", [0.0]) * (width * height * 4)
bake_img.pixels.foreach_get(pixels)
for _pass in range(8):
    previous = pixels[:]
    for y in range(height):
        row = y * width
        for x in range(width):
            i = (row + x) * 4
            if previous[i] > 0.03 or previous[i + 1] > 0.03 or previous[i + 2] > 0.03:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = x + dx
                ny = y + dy
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                j = ((ny * width) + nx) * 4
                if previous[j] > 0.03 or previous[j + 1] > 0.03 or previous[j + 2] > 0.03:
                    pixels[i] = previous[j]
                    pixels[i + 1] = previous[j + 1]
                    pixels[i + 2] = previous[j + 2]
                    pixels[i + 3] = 1.0
                    break
bake_img.pixels.foreach_set(pixels)
bake_img.update()
print("DILATE", flush=True)

preview = bpy.data.materials.new("preview")
preview.use_nodes = True
bsdf = preview.node_tree.nodes.get("Principled BSDF")
tex = preview.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = bake_img
preview.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
low.data.materials.clear()
low.data.materials.append(preview)
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
scene.render.filepath = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-preview.png"
bpy.ops.render.render(write_still=True)
print("PREVIEW", flush=True)

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
        handle.write(header + body)

write_dds(bake_img, os.path.join(OUT_DIR, "valkur_diffuse.dds"))
flat = bytes((255, 128, 128, 255)) * 16
header = struct.pack("<4sI", b"DDS ", 124)
header += struct.pack("<7I", 0x100F, 4, 4, 16, 0, 0, 0)
header += struct.pack("<10I", *([0] * 10))
header += struct.pack("<8I", 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
header += struct.pack("<5I", 0x1000, 0, 0, 0, 0)
for name, color in (("valkur_normal.dds", (255, 128, 128, 255)), ("valkur_properties.dds", (180, 0, 40, 255))):
    with open(os.path.join(OUT_DIR, name), "wb") as handle:
        handle.write(header + bytes(color) * 16)

arm = next(mod.object for mod in src.modifiers if mod.type == "ARMATURE")
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
