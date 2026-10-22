"""Higher-resolution bake of the original paint, gap fill, normal map, then export."""
import array
import os
import struct
from collections import deque

import bpy

OUT_DIR = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur"
PREVIEW = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-preview.png"


def write_dds(image, path, flip_green=False):
    width, height = image.size
    raw = array.array("f", [0.0]) * (width * height * 4)
    image.pixels.foreach_get(raw)
    body = bytearray(width * height * 4)
    for y in range(height):
        src_y = height - 1 - y
        for x in range(width):
            i = ((src_y * width) + x) * 4
            o = ((y * width) + x) * 4
            red = raw[i]
            green = 1.0 - raw[i + 1] if flip_green else raw[i + 1]
            blue = raw[i + 2]
            body[o] = int(max(0.0, min(1.0, blue)) * 255)
            body[o + 1] = int(max(0.0, min(1.0, green)) * 255)
            body[o + 2] = int(max(0.0, min(1.0, red)) * 255)
            body[o + 3] = 255
    header = struct.pack("<4sI", b"DDS ", 124)
    header += struct.pack("<7I", 0x100F, height, width, width * 4, 0, 0, 0)
    header += struct.pack("<10I", *([0] * 10))
    header += struct.pack("<8I", 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    header += struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    with open(path, "wb") as handle:
        handle.write(header)
        handle.write(body)
    print("DDS", os.path.basename(path), os.path.getsize(path), flush=True)


def fill_gaps(image, radius=28):
    width, height = image.size
    pixels = array.array("f", [0.0]) * (width * height * 4)
    image.pixels.foreach_get(pixels)
    empty = bytearray(width * height)
    dist = bytearray(width * height)
    queue = deque()
    for index in range(width * height):
        offset = index * 4
        if pixels[offset] > 0.025 or pixels[offset + 1] > 0.025 or pixels[offset + 2] > 0.025:
            queue.append(index)
        else:
            empty[index] = 1
            dist[index] = 255
    filled = 0
    while queue:
        index = queue.popleft()
        if dist[index] >= radius:
            continue
        x = index % width
        y = index // width
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x + dx
            ny = y + dy
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            neighbor = ny * width + nx
            if empty[neighbor] and dist[neighbor] == 255:
                src = index * 4
                dst = neighbor * 4
                pixels[dst] = pixels[src]
                pixels[dst + 1] = pixels[src + 1]
                pixels[dst + 2] = pixels[src + 2]
                pixels[dst + 3] = 1.0
                empty[neighbor] = 0
                dist[neighbor] = dist[index] + 1
                queue.append(neighbor)
                filled += 1
    image.pixels.foreach_set(pixels)
    image.update()
    print("FILLED", filled, flush=True)


for name in ("Image_0", "Image_1", "Image_2"):
    image = bpy.data.images[name]
    image.filepath = os.path.join(OUT_DIR, "src_" + name + ".png")
    image.source = "FILE"
    image.reload()

src = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(mod.object for mod in src.modifiers if mod.type == "ARMATURE")
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
dec.ratio = 0.028
bpy.ops.object.modifier_apply(modifier=dec.name)
print("LOW", len(low.data.vertices), len(low.data.polygons), flush=True)
bpy.ops.object.shade_smooth()

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
normal_img = bpy.data.images.new("valkur_normal_bake", 2048, 2048, alpha=False)
normal_img.colorspace_settings.name = "Non-Color"
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


def select_pair():
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low


select_pair()
print("BAKE_COLOR", flush=True)
bpy.ops.object.bake(
    type="DIFFUSE",
    pass_filter={"COLOR"},
    use_selected_to_active=True,
    cage_extrusion=0.45,
    max_ray_distance=2.5,
)
fill_gaps(bake_img, 28)
print("BAKE_NORMAL", flush=True)
tex_node.image = normal_img
bake_mat.node_tree.nodes.active = tex_node
select_pair()
bpy.ops.object.bake(
    type="NORMAL",
    use_selected_to_active=True,
    cage_extrusion=0.45,
    max_ray_distance=2.5,
    normal_space="TANGENT",
)
print("BAKE_DONE", flush=True)

preview = bpy.data.materials.new("preview")
preview.use_nodes = True
nodes = preview.node_tree.nodes
links = preview.node_tree.links
bsdf = nodes.get("Principled BSDF")
color_node = nodes.new("ShaderNodeTexImage")
color_node.image = bake_img
links.new(color_node.outputs["Color"], bsdf.inputs["Base Color"])
normal_node = nodes.new("ShaderNodeTexImage")
normal_node.image = normal_img
normal_node.image.colorspace_settings.name = "Non-Color"
normal_map = nodes.new("ShaderNodeNormalMap")
links.new(normal_node.outputs["Color"], normal_map.inputs["Color"])
links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
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

write_dds(bake_img, os.path.join(OUT_DIR, "valkur_diffuse.dds"))
write_dds(normal_img, os.path.join(OUT_DIR, "valkur_normal.dds"), flip_green=True)
header = struct.pack("<4sI", b"DDS ", 124)
header += struct.pack("<7I", 0x100F, 4, 4, 16, 0, 0, 0)
header += struct.pack("<10I", *([0] * 10))
header += struct.pack("<8I", 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
header += struct.pack("<5I", 0x1000, 0, 0, 0, 0)
with open(os.path.join(OUT_DIR, "valkur_properties.dds"), "wb") as handle:
    handle.write(header + bytes((180, 0, 40, 255)) * 16)

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
