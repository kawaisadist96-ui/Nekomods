"""Remove the hip-to-shield plates without cutting the shield disc."""
import bmesh
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
    "Character1_LeftShoulder",
    "Character1_LeftArm",
    "Character1_LeftForeArm",
    "Character1_LeftForeArmRoll",
    "Character1_LeftHandThumb1",
    "Character1_LeftHandThumb2",
    "Character1_LeftHandThumb3",
    "Character1_LeftHandIndex1",
    "Character1_LeftHandIndex2",
    "Character1_LeftHandIndex3",
    "Character1_LeftHandRing1",
    "Character1_LeftHandRing2",
    "Character1_LeftHandRing3",
}


def dominant_set(vertex_indices):
    found = set()
    for vertex_index in vertex_indices:
        best = (0.0, "")
        for group in mesh.vertices[vertex_index].groups:
            if group.weight > best[0]:
                best = (group.weight, names.get(group.group, ""))
        found.add(best[1])
    return found


owners = [dominant_set(poly.vertices) for poly in mesh.polygons]
bm = bmesh.new()
bm.from_mesh(mesh)
bm.faces.ensure_lookup_table()
hand_faces = [face for face in bm.faces if owners[face.index] == {"Character1_LeftHand"}]
seed = max(hand_faces, key=lambda face: face.calc_center_median().x)
shield = set()
stack = [seed]
while stack:
    face = stack.pop()
    if face in shield:
        continue
    shield.add(face)
    for edge in face.edges:
        for other in edge.link_faces:
            if other in shield or owners[other.index] != {"Character1_LeftHand"}:
                continue
            if face.normal.dot(other.normal) < 0.45:
                continue
            stack.append(other)
shield_ids = {face.index for face in shield}
print("SHIELD_FACES", len(shield_ids), flush=True)

remove = []
for poly in mesh.polygons:
    if poly.index in shield_ids:
        continue
    point = Vector(poly.center)
    if not (8 < point.x < 52 and -44 < point.y < 18 and 62 < point.z < 120):
        continue
    if owners[poly.index] <= keep_out:
        continue
    remove.append(poly.index)
print("REMOVE", len(remove), flush=True)

dead = [face for face in bm.faces if face.index in set(remove)]
bmesh.ops.delete(bm, geom=dead, context="FACES")
bm.to_mesh(mesh)
bm.free()
mesh.update()

bm = bmesh.new()
bm.from_mesh(mesh)
seen = set()
remove_islands = []
for face in bm.faces:
    if face in seen:
        continue
    stack = [face]
    island = []
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        island.append(current)
        for edge in current.edges:
            stack.extend(other for other in edge.link_faces if other not in seen)
    if len(island) > 350:
        continue
    center = sum((item.calc_center_median() for item in island), Vector()) / len(island)
    if 20 < center.x < 48 and -36 < center.y < 12 and 66 < center.z < 112:
        remove_islands.extend(island)
        print("ISLAND", len(island), tuple(round(v, 1) for v in center), flush=True)
if remove_islands:
    bmesh.ops.delete(bm, geom=remove_islands, context="FACES")
bm.to_mesh(mesh)
bm.free()
mesh.update()
print("LEFT", len(mesh.polygons), flush=True)

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
target.location = (18, -8, 82)
scene.collection.objects.link(target)
camera_data = bpy.data.cameras.new("gap_cam")
camera_data.lens = 58
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
scene.render.filepath = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\walk_frames\gap_cut.png"
bpy.ops.render.render(write_still=True)
print("SHOT", flush=True)
bpy.ops.wm.save_as_mainfile(
    filepath=r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-gap-cut.blend",
    compress=True,
)
print("SAVED", flush=True)
