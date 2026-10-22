"""Compare the left hand bone to the shield in rest and in the walk."""
import bpy
from mathutils import Vector

arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
low = bpy.data.objects["Valkur_low"]
mesh = low.data
names = {group.index: group.name for group in low.vertex_groups}


def dominant(vertex_index):
    best = (0.0, "")
    for group in mesh.vertices[vertex_index].groups:
        if group.weight > best[0]:
            best = (group.weight, names.get(group.group, ""))
    return best[1]


hand_verts = [vertex for vertex in mesh.vertices if dominant(vertex.index) == "Character1_LeftHand"]
xs = [vertex.co.x for vertex in hand_verts]
ys = [vertex.co.y for vertex in hand_verts]
zs = [vertex.co.z for vertex in hand_verts]
print("HAND_VERTS", len(hand_verts))
print("BBOX", round(min(xs), 1), round(max(xs), 1), round(min(ys), 1), round(max(ys), 1), round(min(zs), 1), round(max(zs), 1))

arm.data.pose_position = "REST"
bpy.context.view_layer.update()
for name in ("Character1_LeftHand", "Character1_LeftForeArm", "Left_hand_node_1", "Character1_LeftArm"):
    bone = arm.pose.bones.get(name)
    if bone is None:
        print("MISSING", name)
        continue
    head = arm.matrix_world @ bone.head
    tail = arm.matrix_world @ bone.tail
    print("REST", name, "head", tuple(round(v, 1) for v in head), "tail", tuple(round(v, 1) for v in tail))

action = bpy.data.actions["VALKUR_TEST_idle"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
arm.data.pose_position = "POSE"
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
for name in ("Character1_LeftHand", "Character1_LeftForeArm", "Left_hand_node_1"):
    bone = arm.pose.bones[name]
    head = arm.matrix_world @ bone.head
    print("IDLE", name, tuple(round(v, 1) for v in head))
