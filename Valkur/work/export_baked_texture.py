"""Decimate, rebake albedo onto a new UV, and re-export the test mesh."""
import array
import os
import struct

import bpy

OUT_DIR = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur"
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
    print("DDS", path, os.path.getsize(path), flush=True)


def write_dds(image, path):
    width, height = image.size
    pixels = array.array("f", [0.0]) * (width * height * 4)
    image.pixels.foreach_get(pixels)
    body = bytearray(width * height * 4)
    for y in range(height):
        src_y = height - 1 - y
        row_in = src_y * width
        row_out = y * width
        for x in range(width):
            i = (row_in + x) * 4
            o = (row_out + x) * 4
            body[o] = int(max(0.0, min(1.0, pixels[i + 2])) * 255)
            body[o + 1] = int(max(0.0, min(1.0, pixels[i + 1])) * 255)
            body[o + 2] = int(max(0.0, min(1.0, pixels[i])) * 255)
            body[o + 3] = 255
    write_dds_bytes(path, width, height, body)


def solid_dds(path, width, height, bgra):
    pixel = bytes(bgra)
    write_dds_bytes(path, width, height, pixel * (width * height))


for image in bpy.data.images:
    if image.packed_file and image.size[0] > 0:
        image.filepath_raw = os.path.join(OUT_DIR, "src_" + image.name + ".png")
        image.file_format = "PNG"
        image.save()
        print("UNPACKED", image.name, image.size[0], image.size[1], flush=True)

src = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in src.modifiers if m.type == "ARMATURE" and m.object)
arm.data.pose_position = "REST"
print("SRC", src.name, len(src.data.vertices), flush=True)

bpy.ops.object.select_all(action="DESELECT")
src.select_set(True)
bpy.context.view_layer.objects.active = src
high = src.copy()
high.data = src.data.copy()
high.name = "Valkur_bake_high"
bpy.context.collection.objects.link(high)
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
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
dec = low.modifiers.new("test_decimate", "DECIMATE")
dec.decimate_type = "COLLAPSE"
dec.ratio = 0.01
bpy.ops.object.modifier_apply(modifier=dec.name)
print("DECIMATED", len(low.data.vertices), len(low.data.polygons), flush=True)
low.data.name = "valkurShape"
arm_mod = low.modifiers.new("CK3 skin", "ARMATURE")
arm_mod.object = arm
arm_mod.use_vertex_groups = True

while low.data.uv_layers:
    low.data.uv_layers.remove(low.data.uv_layers[0])
low.data.uv_layers.new(name="UVMap")
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
unwrap = bpy.ops.uv.smart_project(angle_limit=1.151917, island_margin=0.02)
print("UNWRAP", unwrap, flush=True)
bpy.ops.object.mode_set(mode="OBJECT")
uvs = low.data.uv_layers.active.data
umin = min(loop.uv.x for loop in uvs)
umax = max(loop.uv.x for loop in uvs)
vmin = min(loop.uv.y for loop in uvs)
vmax = max(loop.uv.y for loop in uvs)
bpy.context.view_layer.update()
print("UV", round(umin, 3), round(umax, 3), round(vmin, 3), round(vmax, 3), flush=True)
print("BBOX_LOW", [round(v, 1) for v in low.bound_box[0]], [round(v, 1) for v in low.bound_box[6]], flush=True)
print("BBOX_HIGH", [round(v, 1) for v in high.bound_box[0]], [round(v, 1) for v in high.bound_box[6]], flush=True)

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
scene.render.bake.margin = 16
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
    cage_extrusion=0.4,
    max_ray_distance=3.0,
)
print("BAKE_DONE", flush=True)

preview_mat = bpy.data.materials.new("valkur_preview")
preview_mat.use_nodes = True
preview_nodes = preview_mat.node_tree.nodes
preview_bsdf = preview_nodes.get("Principled BSDF")
preview_tex = preview_nodes.new("ShaderNodeTexImage")
preview_tex.image = bake_img
preview_mat.node_tree.links.new(preview_tex.outputs["Color"], preview_bsdf.inputs["Base Color"])
low.data.materials.clear()
low.data.materials.append(preview_mat)
for obj in bpy.context.scene.objects:
    obj.hide_render = obj is not low
light_data = bpy.data.lights.new("preview_sun", "SUN")
light_data.energy = 4
light = bpy.data.objects.new("preview_sun", light_data)
bpy.context.scene.collection.objects.link(light)
light.rotation_euler = (0.9, 0.2, 0.6)
light.hide_render = False
target = bpy.data.objects.new("preview_target", None)
target.location = (0, 0, 95)
bpy.context.scene.collection.objects.link(target)
camera_data = bpy.data.cameras.new("preview_cam")
camera_data.lens = 50
camera = bpy.data.objects.new("preview_cam", camera_data)
bpy.context.scene.collection.objects.link(camera)
camera.location = (90, -280, 140)
track = camera.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
bpy.context.scene.camera = camera
bpy.context.scene.render.engine = "BLENDER_EEVEE"
bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 1200
bpy.context.scene.render.filepath = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-preview.png"
bpy.ops.render.render(write_still=True)
print("PREVIEW", bpy.context.scene.render.filepath, flush=True)

bake_img.filepath_raw = os.path.join(OUT_DIR, "valkur_diffuse_baked.png")
bake_img.file_format = "PNG"
bake_img.save()
write_dds(bake_img, os.path.join(OUT_DIR, "valkur_diffuse.dds"))
solid_dds(os.path.join(OUT_DIR, "valkur_normal.dds"), 4, 4, (255, 128, 128, 255))
solid_dds(os.path.join(OUT_DIR, "valkur_properties.dds"), 4, 4, (180, 0, 40, 255))

mat = bpy.data.materials.new("PDXmat_valkur")
mat["shader"] = "standard"
mat["diff"] = "valkur_diffuse.dds"
mat["n"] = "valkur_normal.dds"
mat["spec"] = "valkur_properties.dds"
low.data.materials.clear()
low.data.materials.append(mat)
arm_mod.show_render = True
arm_mod.show_viewport = True

for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
low.select_set(True)
bpy.context.view_layer.objects.active = low
mesh_path = os.path.join(OUT_DIR, "valkur.mesh")
result = bpy.ops.io_pdx_mesh.export_mesh(
    filepath=mesh_path,
    chk_mesh=True,
    chk_skel=True,
    chk_locs=False,
    chk_selected=True,
    chk_asset=False,
    chk_gfx=False,
)
print("MESH_EXPORT", result, os.path.getsize(mesh_path), flush=True)
print("DONE", flush=True)
