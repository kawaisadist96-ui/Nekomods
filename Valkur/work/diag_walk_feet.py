"""Print the walk's vertical motion and the lowest each foot gets."""
import bpy

arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
action = bpy.data.actions["VALKUR_TEST_walk"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
arm.data.pose_position = "POSE"
scene = bpy.context.scene

def wz(name):
    return (arm.matrix_world @ arm.pose.bones[name].head).z

rows = []
for frame in range(1, 82):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    root_z = arm.pose.bones["root"].location.z
    left = wz("Character1_LeftFoot")
    right = wz("Character1_RightFoot")
    lt = wz("Character1_LeftToeBase")
    rt = wz("Character1_RightToeBase")
    rows.append((frame, root_z, left, right, lt, rt))

print("FRAME rootZ leftFoot rightFoot leftToe rightToe")
for frame, root_z, left, right, lt, rt in rows:
    if frame % 2 == 1:
        print(f"{frame:3d} {root_z:7.2f} {left:7.2f} {right:7.2f} {lt:7.2f} {rt:7.2f}")

def col(index):
    return [row[index] for row in rows]

for label, index in (("root", 1), ("Lfoot", 2), ("Rfoot", 3), ("Ltoe", 4), ("Rtoe", 5)):
    values = col(index)
    jumps = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
    worst = max(range(len(jumps)), key=lambda i: jumps[i])
    print(label, "min", round(min(values), 2), "max", round(max(values), 2), "worst_step", round(jumps[worst], 2), "into", worst + 2)
