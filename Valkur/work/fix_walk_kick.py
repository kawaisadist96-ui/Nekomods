"""Lower the kicking foot in the walk cycle and render the result. Does not write game files."""
import os

import bpy
from mathutils import Quaternion

WORK = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work"
arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
action = bpy.data.actions["VALKUR_TEST_walk"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
arm.data.pose_position = "POSE"
scene = bpy.context.scene
identity = Quaternion((1.0, 0.0, 0.0, 0.0))

sides = {
    "L": ("Character1_LeftToeBase", ("Character1_LeftUpLeg", "Character1_LeftLeg", "Character1_LeftFoot")),
    "R": ("Character1_RightToeBase", ("Character1_RightUpLeg", "Character1_RightLeg", "Character1_RightFoot")),
}

def toe_z(name):
    return (arm.matrix_world @ arm.pose.bones[name].head).z

for frame in range(1, 82):
    scene.frame_set(frame)
    for _ in range(5):
        bpy.context.view_layer.update()
        for _side, (toe, bones) in sides.items():
            height = toe_z(toe)
            if height <= 11.0:
                continue
            factor = min(0.42, (height - 11.0) / 36.0)
            for index, bone_name in enumerate(bones):
                bone = arm.pose.bones[bone_name]
                amount = factor if index < 2 else factor * 0.45
                bone.rotation_quaternion = bone.rotation_quaternion.slerp(identity, amount)
                bone.keyframe_insert("rotation_quaternion", frame=frame)
    if frame in (1, 13, 49, 73, 81):
        bpy.context.view_layer.update()
        print(
            "F",
            frame,
            "L",
            round(toe_z("Character1_LeftToeBase"), 1),
            "R",
            round(toe_z("Character1_RightToeBase"), 1),
            flush=True,
        )

low = bpy.data.objects["Valkur_low"]
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
for frame in (1, 13, 49, 73):
    scene.frame_set(frame)
    scene.render.filepath = os.path.join(WORK, "walk_frames", f"fixed_{frame:02d}.png")
    bpy.ops.render.render(write_still=True)
    print("SHOT", frame, flush=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "valkur-walk-fix.blend"), compress=True)
print("SAVED", flush=True)
