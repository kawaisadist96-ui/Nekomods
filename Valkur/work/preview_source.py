import os

import bpy

src = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
print("UVS", [layer.name for layer in src.data.uv_layers], flush=True)
print("MATS", [slot.name for slot in src.material_slots], flush=True)
mat = src.material_slots[0].material
for node in mat.node_tree.nodes:
    if node.type == "TEX_IMAGE" and node.image:
        print("TEX", node.name, node.image.name, node.image.size[0], flush=True)

bpy.ops.object.select_all(action="DESELECT")
src.select_set(True)
bpy.context.view_layer.objects.active = src
mesh = src.copy()
mesh.data = src.data.copy()
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
scene.render.filepath = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-source-preview.png"
bpy.ops.render.render(write_still=True)
print("PREVIEW", flush=True)
