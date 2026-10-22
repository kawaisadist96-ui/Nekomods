"""Show the shield grip from the arm side, rest and mid-walk."""
import os

import bpy

low = bpy.data.objects["Valkur_low"]
arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
action = bpy.data.actions["VALKUR_TEST_walk"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
arm.data.pose_position = "POSE"
scene = bpy.context.scene
for obj in scene.objects:
    obj.hide_render = obj is not low
light_data = bpy.data.lights.new("grip_sun", "SUN")
light_data.energy = 6
light = bpy.data.objects.new("grip_sun", light_data)
scene.collection.objects.link(light)
light.rotation_euler = (0.9, -0.4, 0.6)
target = bpy.data.objects.new("grip_target", None)
target.location = (36, -6, 96)
scene.collection.objects.link(target)
camera_data = bpy.data.cameras.new("grip_cam")
camera_data.lens = 70
camera = bpy.data.objects.new("grip_cam", camera_data)
scene.collection.objects.link(camera)
camera.location = (10, 40, 110)
track = camera.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 800
scene.render.resolution_y = 800
work = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\walk_frames"
for frame in (1, 30, 60):
    scene.frame_set(frame)
    scene.render.filepath = os.path.join(work, f"grip_{frame:02d}.png")
    bpy.ops.render.render(write_still=True)
    hand = arm.matrix_world @ arm.pose.bones["Character1_LeftHand"].head
    print("F", frame, "HAND", tuple(round(v, 1) for v in hand), flush=True)
