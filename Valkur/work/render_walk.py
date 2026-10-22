"""Side-view frames of the walk, plus stance-foot drift."""
import os

import bpy
from mathutils import Vector

WORK = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\walk_frames"
os.makedirs(WORK, exist_ok=True)

arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
action = bpy.data.actions["VALKUR_TEST_walk"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
arm.data.pose_position = "POSE"

low = bpy.data.objects.get("Valkur_low")
if low is None:
    low = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.polygons) < 200000)
print("MESH", low.name, len(low.data.polygons))

scene = bpy.context.scene
for frame in range(1, 82):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    if frame % 5 == 1:
        def p(name):
            v = arm.matrix_world @ arm.pose.bones[name].head
            return tuple(round(x, 1) for x in v)
        print("F", frame, "Ltoe", p("Character1_LeftToeBase"), "Rtoe", p("Character1_RightToeBase"))

for obj in scene.objects:
    obj.hide_render = obj is not low
light_data = bpy.data.lights.new("walk_sun", "SUN")
light_data.energy = 5
light = bpy.data.objects.new("walk_sun", light_data)
scene.collection.objects.link(light)
light.rotation_euler = (1.1, 0.1, 0.4)
target = bpy.data.objects.new("walk_target", None)
target.location = (0, 0, 95)
scene.collection.objects.link(target)
camera_data = bpy.data.cameras.new("walk_cam")
camera_data.lens = 55
camera = bpy.data.objects.new("walk_cam", camera_data)
scene.collection.objects.link(camera)
camera.location = (260, 20, 110)
track = camera.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 480
scene.render.resolution_y = 720

for frame in (1, 13, 25, 37, 49, 61, 73):
    scene.frame_set(frame)
    scene.render.filepath = os.path.join(WORK, f"walk_{frame:02d}.png")
    bpy.ops.render.render(write_still=True)
    print("SHOT", frame, flush=True)
