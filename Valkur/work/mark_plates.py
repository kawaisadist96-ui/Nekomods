"""Highlight the skirt stack and leave the shield disc alone."""
import bpy
from mathutils import Vector

low = bpy.data.objects["Valkur_low"]
mesh = low.data
names = {group.index: group.name for group in low.vertex_groups}
keep_out = {
    "Character1_LeftUpLeg",
    "Character1_LeftLeg",
    "Character1_LeftFoot",
    "Character1_LeftToeBase",
}


def dominant(vertex_index):
    best = (0.0, -1)
    for group in mesh.vertices[vertex_index].groups:
        if group.weight > best[0]:
            best = (group.weight, group.group)
    return names.get(best[1], "")


shield_points = []
for poly in mesh.polygons:
    center = Vector(poly.center)
    if center.x < 34:
        continue
    owners = {dominant(index) for index in poly.vertices}
    if owners == {"Character1_LeftHand"}:
        shield_points.append(center)
shield_center = sum(shield_points, Vector()) / len(shield_points)
print("SHIELD", tuple(round(v, 1) for v in shield_center), "n", len(shield_points), flush=True)

selected = []
for poly in mesh.polygons:
    center = Vector(poly.center)
    if not (10 < center.x < 48 and -42 < center.y < 14 and 64 < center.z < 118):
        continue
    if (center - shield_center).length < 15.0:
        continue
    owners = {dominant(index) for index in poly.vertices}
    if owners <= keep_out:
        continue
    selected.append(poly.index)
print("PLATES", len(selected), flush=True)

red = bpy.data.materials.new("plate_red")
red.use_nodes = True
red.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1, 0.05, 0.05, 1)
mesh.materials.append(red)
red_index = len(mesh.materials) - 1
for index in selected:
    mesh.polygons[index].material_index = red_index

arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
action = bpy.data.actions["VALKUR_TEST_walk"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
arm.data.pose_position = "POSE"
scene = bpy.context.scene
scene.frame_set(1)
for obj in scene.objects:
    obj.hide_render = obj is not low
light_data = bpy.data.lights.new("gap_sun", "SUN")
light_data.energy = 6
light = bpy.data.objects.new("gap_sun", light_data)
scene.collection.objects.link(light)
light.rotation_euler = (0.8, 0.1, 0.2)
target = bpy.data.objects.new("gap_target", None)
target.location = (20, -8, 84)
scene.collection.objects.link(target)
camera_data = bpy.data.cameras.new("gap_cam")
camera_data.lens = 60
camera = bpy.data.objects.new("gap_cam", camera_data)
scene.collection.objects.link(camera)
camera.location = (55, -170, 140)
track = camera.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 800
scene.render.resolution_y = 900
scene.render.filepath = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\walk_frames\plates.png"
bpy.ops.render.render(write_still=True)
print("SHOT", flush=True)
