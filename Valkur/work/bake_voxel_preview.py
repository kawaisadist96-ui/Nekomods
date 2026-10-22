"""Fuse the card mesh into a solid shell and preview a color bake. Does not write game files."""
import os

import bpy

OUT_DIR = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur"
WORK = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work"

for name in ("Image_0", "Image_1", "Image_2"):
    image = bpy.data.images[name]
    image.filepath = os.path.join(OUT_DIR, "src_" + name + ".png")
    image.source = "FILE"
    image.reload()
    print("RELOAD", name, image.size[:], image.has_data, flush=True)

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

voxel = low.modifiers.new("voxel", "REMESH")
voxel.mode = "VOXEL"
voxel.voxel_size = 0.72
voxel.adaptivity = 0.0
print("VOXEL", flush=True)
bpy.ops.object.modifier_apply(modifier=voxel.name)
print("VOXEL_FACES", len(low.data.polygons), flush=True)
if len(low.data.polygons) > 70000:
    dec = low.modifiers.new("trim", "DECIMATE")
    dec.ratio = 70000 / len(low.data.polygons)
    bpy.ops.object.modifier_apply(modifier=dec.name)
    print("TRIMMED", len(low.data.polygons), flush=True)
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
bake_img.filepath_raw = os.path.join(WORK, "valkur-bake.png")
bake_img.file_format = "PNG"
bake_img.save()
print("BAKE_SAVED", flush=True)

preview = bpy.data.materials.new("preview")
preview.use_nodes = True
bsdf = preview.node_tree.nodes.get("Principled BSDF")
color_node = preview.node_tree.nodes.new("ShaderNodeTexImage")
color_node.image = bake_img
preview.node_tree.links.new(color_node.outputs["Color"], bsdf.inputs["Base Color"])
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
scene.render.filepath = os.path.join(WORK, "valkur-preview.png")
bpy.ops.render.render(write_still=True)
print("PREVIEW", len(low.data.polygons), flush=True)
