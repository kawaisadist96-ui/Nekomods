"""Delete only the torn scraps hanging under the shield grip."""
import bmesh
import bpy
from mathutils import Vector

low = bpy.data.objects["Valkur_low"]
mesh = low.data
names = {group.index: group.name for group in low.vertex_groups}
keep = {
    "Character1_LeftUpLeg",
    "Character1_LeftLeg",
    "Character1_LeftArm",
    "Character1_LeftForeArm",
    "Character1_LeftForeArmRoll",
    "Character1_LeftShoulder",
}


def dominant(vertex_index):
    best = (0.0, "")
    for group in mesh.vertices[vertex_index].groups:
        if group.weight > best[0]:
            best = (group.weight, names.get(group.group, ""))
    return best[1]


remove = []
for poly in mesh.polygons:
    point = Vector(poly.center)
    if not (30 < point.x < 46 and -30 < point.y < 0 and 66 < point.z < 90):
        continue
    owners = {dominant(index) for index in poly.vertices}
    if owners & keep:
        continue
    remove.append(poly.index)
print("SCRAPS", len(remove), flush=True)
bm = bmesh.new()
bm.from_mesh(mesh)
dead = [face for face in bm.faces if face.index in set(remove)]
bmesh.ops.delete(bm, geom=dead, context="FACES")
bm.to_mesh(mesh)
bm.free()
mesh.update()

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
target.location = (22, -4, 100)
scene.collection.objects.link(target)
camera_data = bpy.data.cameras.new("gap_cam")
camera_data.lens = 48
camera = bpy.data.objects.new("gap_cam", camera_data)
scene.collection.objects.link(camera)
camera.location = (70, -150, 145)
track = camera.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 800
scene.render.resolution_y = 900
scene.render.filepath = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\walk_frames\grip_clean.png"
bpy.ops.render.render(write_still=True)
print("SHOT", len(mesh.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(
    filepath=r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-gap-cut.blend",
    compress=True,
)
print("SAVED", flush=True)
