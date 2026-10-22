"""Drop the leftover cloth scraps on the hip side of the shield."""
import bmesh
import bpy
from collections import defaultdict
from mathutils import Vector

low = bpy.data.objects["Valkur_low"]
mesh = low.data
names = {group.index: group.name for group in low.vertex_groups}


def dominant(vertex_index):
    best = (0.0, "")
    for group in mesh.vertices[vertex_index].groups:
        if group.weight > best[0]:
            best = (group.weight, names.get(group.group, ""))
    return best[1]


areas = defaultdict(float)
for poly in mesh.polygons:
    if poly.area < 0.5:
        continue
    if any(dominant(index) != "Character1_LeftHand" for index in poly.vertices):
        continue
    key = tuple(round(value, 1) for value in poly.normal)
    areas[key] += poly.area
normal = Vector(max(areas, key=areas.get)).normalized()
wood = []
for poly in mesh.polygons:
    if any(dominant(index) != "Character1_LeftHand" for index in poly.vertices):
        continue
    if poly.normal.dot(normal) < 0.82:
        continue
    wood.append(Vector(poly.center))
center = sum(wood, Vector()) / len(wood)
distances = sorted((point - center).length for point in wood)
radius = distances[int(len(distances) * 0.96)]
print("WOOD", tuple(round(v, 1) for v in center), "R", round(radius, 1), "N", tuple(round(v, 2) for v in normal), flush=True)

remove = []
for poly in mesh.polygons:
    if any(dominant(index) != "Character1_LeftHand" for index in poly.vertices):
        continue
    point = Vector(poly.center)
    distance = (point - center).length
    on_disc = distance < radius * 0.98 and abs((point - center).dot(normal)) < 3.5
    if on_disc:
        continue
    if point.x < center.x and 64 < point.z < 120 and -40 < point.y < 18:
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
print("SHOT", len(mesh.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(
    filepath=r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\valkur-gap-cut.blend",
    compress=True,
)
print("SAVED", flush=True)
