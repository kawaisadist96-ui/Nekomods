"""Close view of the shield-thigh gap in the raised-leg pose."""
import os

import bpy

WORK = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\walk_frames"
arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
action = bpy.data.actions["VALKUR_TEST_walk"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
arm.data.pose_position = "POSE"
low = bpy.data.objects["Valkur_low"]
scene = bpy.context.scene
for obj in scene.objects:
    obj.hide_render = obj is not low
light_data = bpy.data.lights.new("gap_sun", "SUN")
light_data.energy = 5
light = bpy.data.objects.new("gap_sun", light_data)
scene.collection.objects.link(light)
light.rotation_euler = (0.6, 0.2, -0.4)
target = bpy.data.objects.new("gap_target", None)
target.location = (18, -8, 78)
scene.collection.objects.link(target)
camera_data = bpy.data.cameras.new("gap_cam")
camera_data.lens = 70
camera = bpy.data.objects.new("gap_cam", camera_data)
scene.collection.objects.link(camera)
track = camera.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 800
scene.render.resolution_y = 900

shots = {
    "gap_a": (90, -160, 150),
    "gap_b": (40, -220, 200),
    "gap_c": (140, -40, 120),
}
for frame in (1, 49):
    scene.frame_set(frame)
    for name, location in shots.items():
        camera.location = location
        scene.render.filepath = os.path.join(WORK, f"{name}_{frame:02d}.png")
        bpy.ops.render.render(write_still=True)
        print("SHOT", name, frame, flush=True)
