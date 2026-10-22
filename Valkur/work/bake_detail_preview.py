"""Bake a tangent normal onto the solid shell and save a ready-to-export blend."""
import os

import bpy

OUT_DIR = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur"
WORK = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work"

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
voxel.voxel_size = 0.55
voxel.adaptivity = 0.0
bpy.ops.object.modifier_apply(modifier=voxel.name)
print("VOXEL_FACES", len(low.data.polygons), flush=True)
if len(low.data.polygons) > 90000:
    dec = low.modifiers.new("trim", "DECIMATE")
    dec.ratio = 90000 / len(low.data.polygons)
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
bpy.ops.uv.smart_project(angle_limit=1.05, island_margin=0.003)
bpy.ops.object.mode_set(mode="OBJECT")

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

bake_img = bpy.data.images.new("valkur_bake", 2048, 2048, alpha=False)
bake_img.colorspace_settings.name = "sRGB"
normal_img = bpy.data.images.new("valkur_normal_bake", 2048, 2048, alpha=True)
normal_img.colorspace_settings.name = "Non-Color"
flat = [0.5, 0.5, 1.0, 1.0] * (2048 * 2048)
normal_img.pixels.foreach_set(flat)
normal_img.update()

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
scene.render.bake.margin = 24
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
    cage_extrusion=1.2,
    max_ray_distance=6.0,
)
tex_node.image = normal_img
bake_mat.node_tree.nodes.active = tex_node
select_pair()
print("BAKE_NORMAL", flush=True)
bpy.ops.object.bake(
    type="NORMAL",
    use_selected_to_active=True,
    cage_extrusion=1.2,
    max_ray_distance=6.0,
    normal_space="TANGENT",
)
print("BAKE_DONE", flush=True)
bake_img.filepath_raw = os.path.join(WORK, "valkur-bake.png")
bake_img.file_format = "PNG"
bake_img.save()
normal_img.filepath_raw = os.path.join(WORK, "valkur-normal-bake.png")
normal_img.file_format = "PNG"
normal_img.save()

preview = bpy.data.materials.new("preview")
preview.use_nodes = True
nodes = preview.node_tree.nodes
links = preview.node_tree.links
bsdf = nodes.get("Principled BSDF")
bsdf.inputs["Roughness"].default_value = 0.72
color_node = nodes.new("ShaderNodeTexImage")
color_node.image = bake_img
links.new(color_node.outputs["Color"], bsdf.inputs["Base Color"])
normal_node = nodes.new("ShaderNodeTexImage")
normal_node.image = normal_img
normal_map = nodes.new("ShaderNodeNormalMap")
normal_map.space = "TANGENT"
links.new(normal_node.outputs["Color"], normal_map.inputs["Color"])
links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
low.data.materials.clear()
low.data.materials.append(preview)

for obj in list(scene.objects):
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

low.data.name = "valkurShape"
skin = low.modifiers.new("CK3 skin", "ARMATURE")
skin.object = arm
skin.use_vertex_groups = True

for obj in list(bpy.data.objects):
    if obj.type == "MESH" and obj is not low:
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
for image in list(bpy.data.images):
    if image not in (bake_img, normal_img):
        bpy.data.images.remove(image)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "valkur-export-ready.blend"), compress=True)
print("SAVED", flush=True)
