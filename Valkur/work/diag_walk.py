"""Sample the walk cycle for pops, foot height, and a bad loop."""
import bpy
from mathutils import Vector

arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
action = bpy.data.actions["VALKUR_TEST_walk"]
print("RANGE", tuple(round(v, 2) for v in action.frame_range), "FPS", bpy.context.scene.render.fps)
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
arm.data.pose_position = "POSE"
scene = bpy.context.scene
start = int(action.frame_range[0])
end = int(action.frame_range[1])

curves = []
for layer in action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            curves.extend(bag.fcurves)
interesting = [c for c in curves if "root" in c.data_path or "Hips" in c.data_path or "Foot" in c.data_path or "Toe" in c.data_path]
for curve in interesting:
    keys = [(round(k.co[0], 1), round(k.co[1], 4)) for k in curve.keyframe_points]
    if len(keys) > 12:
        keys = keys[:6] + ["..."] + keys[-4:]
    print("CURVE", curve.data_path, curve.array_index, "n", len(curve.keyframe_points), keys)

names = [
    "root",
    "Character1_Hips",
    "Character1_LeftFoot",
    "Character1_RightFoot",
    "Character1_LeftToeBase",
    "Character1_RightToeBase",
]
present = [name for name in names if name in arm.pose.bones]
print("BONES", present)

def world(name):
    return arm.matrix_world @ arm.pose.bones[name].head

prev = None
worst = (0, None, None)
for frame in range(start, end + 1):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    root = arm.pose.bones["root"]
    loc = tuple(round(v, 3) for v in root.location)
    hips = world("Character1_Hips")
    left = world("Character1_LeftFoot") if "Character1_LeftFoot" in arm.pose.bones else Vector()
    right = world("Character1_RightFoot") if "Character1_RightFoot" in arm.pose.bones else Vector()
    sample = (loc, tuple(round(v, 2) for v in hips), tuple(round(v, 2) for v in left), tuple(round(v, 2) for v in right))
    if frame in (start, 10, 20, 30, 40, 50, 60, 70, end) or frame % 20 == 0:
        print("F", frame, "root", loc, "hips", sample[1], "L", sample[2], "R", sample[3])
    if prev is not None:
        jump = (Vector(sample[1]) - Vector(prev[1])).length
        if jump > worst[0]:
            worst = (jump, frame, prev[0])
    prev = sample

scene.frame_set(start)
bpy.context.view_layer.update()
a = {name: world(name).copy() for name in present}
scene.frame_set(end)
bpy.context.view_layer.update()
b = {name: world(name).copy() for name in present}
print("LOOP")
for name in present:
    delta = b[name] - a[name]
    print(" ", name, tuple(round(v, 2) for v in delta), "len", round(delta.length, 2))
print("WORST_HIP_STEP", round(worst[0], 2), "at", worst[1])
