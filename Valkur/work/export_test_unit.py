"""Export a test-resolution Valkyr mesh and two animations. Does not save the blend."""
import array
import os
import struct

import bpy

OUT_DIR = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur"
os.makedirs(OUT_DIR, exist_ok=True)


def write_dds(image, path):
    width, height = image.size
    pixels = array.array("f", [0.0]) * (width * height * 4)
    image.pixels.foreach_get(pixels)
    # Blender stores rows bottom-up. DDS rows are top-down, BGRA.
    body = bytearray(width * height * 4)
    for y in range(height):
        src_y = height - 1 - y
        for x in range(width):
            i = (src_y * width + x) * 4
            o = (y * width + x) * 4
            body[o] = int(max(0.0, min(1.0, pixels[i + 2])) * 255)
            body[o + 1] = int(max(0.0, min(1.0, pixels[i + 1])) * 255)
            body[o + 2] = int(max(0.0, min(1.0, pixels[i])) * 255)
            body[o + 3] = int(max(0.0, min(1.0, pixels[i + 3])) * 255)
    header = struct.pack(
        "<4sI",
        b"DDS ",
        124,
    )
    header += struct.pack(
        "<7I",
        0x100F,
        height,
        width,
        width * 4,
        0,
        0,
        0,
    )
    header += struct.pack("<10I", *([0] * 10))
    header += struct.pack(
        "<8I",
        32,
        0x41,
        0,
        32,
        0x00FF0000,
        0x0000FF00,
        0x000000FF,
        0xFF000000,
    )
    header += struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    with open(path, "wb") as handle:
        handle.write(header)
        handle.write(body)
    print("DDS", path, os.path.getsize(path), flush=True)

try:
    bpy.ops.preferences.addon_enable(module="io_pdx_mesh")
except Exception as exc:
    print("ADDON", exc)

src = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
arm = next(m.object for m in src.modifiers if m.type == "ARMATURE" and m.object)
print("SRC", src.name, len(src.data.vertices), "ARM", arm.name, flush=True)

bpy.ops.object.select_all(action="DESELECT")
src.select_set(True)
bpy.context.view_layer.objects.active = src
mesh = src.copy()
mesh.data = src.data.copy()
mesh.name = "Valkur_test_export"
bpy.context.collection.objects.link(mesh)
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
world = mesh.matrix_world.copy()
mesh.parent = None
mesh.matrix_world = world
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
print("APPLIED", [round(v, 4) for v in mesh.scale], "verts", len(mesh.data.vertices), flush=True)

try:
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.mode_set(mode="OBJECT")
except Exception as exc:
    print("NORMALS", exc)
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

arm.data.pose_position = "REST"
dec = mesh.modifiers.new("test_decimate", "DECIMATE")
dec.decimate_type = "COLLAPSE"
dec.ratio = 0.003
bpy.ops.object.modifier_move_to_index(modifier=dec.name, index=0)
bpy.ops.object.modifier_apply(modifier=dec.name)
print("DECIMATED", len(mesh.data.vertices), len(mesh.data.polygons), flush=True)
mesh.data.name = "valkurShape"

zs = [v.co.z for v in mesh.data.vertices]
print("HEIGHT", round(min(zs), 2), round(max(zs), 2), flush=True)

image = bpy.data.images.get("Image_0")
if image:
    image.scale(1024, 1024)
    write_dds(image, os.path.join(OUT_DIR, "valkur_diffuse.dds"))

mat = bpy.data.materials.new("PDXmat_valkur")
mat["shader"] = "standard"
mat["diff"] = "valkur_diffuse.dds"
mat["n"] = "valkur_normal.dds"
mat["spec"] = "valkur_properties.dds"
mesh.data.materials.clear()
mesh.data.materials.append(mat)

bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
mesh_path = os.path.join(OUT_DIR, "valkur.mesh")
result = bpy.ops.io_pdx_mesh.export_mesh(
    filepath=mesh_path,
    chk_mesh=True,
    chk_skel=True,
    chk_locs=False,
    chk_selected=True,
    chk_asset=False,
    chk_gfx=False,
)
print("MESH_EXPORT", result, os.path.exists(mesh_path), flush=True)

def export_action(action_name, filename, start, end):
    action = bpy.data.actions[action_name]
    ad = arm.animation_data_create()
    ad.action = action
    if action.slots:
        ad.action_slot = action.slots[0]
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    scene.io_pdx_export.custom_range = True
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(OUT_DIR, filename)
    result = bpy.ops.io_pdx_mesh.export_anim(
        filepath=path,
        int_start=start,
        int_end=end,
        chk_uniform_scale=True,
    )
    print("ANIM", action_name, result, os.path.exists(path), os.path.getsize(path) if os.path.exists(path) else 0, flush=True)

export_action("VALKUR_TEST_idle", "valkur_idle.anim", 1, 60)
export_action("VALKUR_TEST_walk", "valkur_move.anim", 1, 40)
print("DONE", flush=True)
