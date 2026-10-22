"""High angle of the whole figure so the shield arm can be judged."""
import bpy

low = bpy.data.objects["Valkur_low"]
arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
scene = bpy.context.scene
for obj in scene.objects:
    obj.hide_render = obj is not low
if bpy.data.objects.get("grip_sun") is None:
    light_data = bpy.data.lights.new("grip_sun", "SUN")
    light_data.energy = 5
    light = bpy.data.objects.new("grip_sun", light_data)
    scene.collection.objects.link(light)
    light.rotation_euler = (0.4, 0.2, 0.8)
target = bpy.data.objects.new("top_target", None)
target.location = (0, 0, 90)
scene.collection.objects.link(target)
camera_data = bpy.data.cameras.new("top_cam")
camera_data.lens = 42
camera = bpy.data.objects.new("top_cam", camera_data)
scene.collection.objects.link(camera)
camera.location = (40, -180, 260)
track = camera.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 700
scene.render.resolution_y = 900

def shoot(action_name, frame, filename):
    action = bpy.data.actions[action_name]
    ad = arm.animation_data_create()
    ad.action = action
    ad.action_slot = action.slots[0]
    arm.data.pose_position = "POSE"
    scene.frame_set(frame)
    scene.render.filepath = filename
    bpy.ops.render.render(write_still=True)
    print("SHOT", filename, flush=True)

base = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\walk_frames"
shoot("VALKUR_TEST_idle", 40, base + r"\arm_idle.png")
shoot("VALKUR_TEST_walk", 20, base + r"\arm_walk.png")
