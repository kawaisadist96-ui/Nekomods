"""Write the RRxG normal, diffuse, and mesh from the checked preview blend."""
import array
import os
import struct

import bpy

OUT_DIR = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur"


def dds_header(height, width):
    header = struct.pack("<4sI", b"DDS ", 124)
    header += struct.pack("<7I", 0x100F, height, width, width * 4, 0, 0, 0)
    header += struct.pack("<10I", *([0] * 10))
    header += struct.pack("<8I", 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    header += struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    return header


def write_diffuse(image, path):
    width, height = image.size
    raw = array.array("f", [0.0]) * (width * height * 4)
    image.pixels.foreach_get(raw)
    body = bytearray(width * height * 4)
    for y in range(height):
        src_y = height - 1 - y
        row = src_y * width
        dst = y * width
        for x in range(width):
            i = (row + x) * 4
            o = (dst + x) * 4
            body[o] = int(max(0.0, min(1.0, raw[i + 2])) * 255)
            body[o + 1] = int(max(0.0, min(1.0, raw[i + 1])) * 255)
            body[o + 2] = int(max(0.0, min(1.0, raw[i])) * 255)
            body[o + 3] = 255
    with open(path, "wb") as handle:
        handle.write(dds_header(height, width))
        handle.write(body)
    print("DIFFUSE", os.path.getsize(path), flush=True)


def write_rrxg(image, path):
    """CK3 UnpackRRxGNormal: X in R and A, Y in G, B is a color mask and stays 0."""
    width, height = image.size
    raw = array.array("f", [0.0]) * (width * height * 4)
    image.pixels.foreach_get(raw)
    body = bytearray(width * height * 4)
    for y in range(height):
        src_y = height - 1 - y
        row = src_y * width
        dst = y * width
        for x in range(width):
            i = (row + x) * 4
            o = (dst + x) * 4
            nx = int(max(0.0, min(1.0, raw[i])) * 255)
            ny = int(max(0.0, min(1.0, raw[i + 1])) * 255)
            body[o] = 0
            body[o + 1] = ny
            body[o + 2] = nx
            body[o + 3] = nx
    with open(path, "wb") as handle:
        handle.write(dds_header(height, width))
        handle.write(body)
    print("NORMAL", os.path.getsize(path), flush=True)


low = bpy.data.objects["Valkur_low"]
arm = next(mod.object for mod in low.modifiers if mod.type == "ARMATURE")
arm.data.pose_position = "REST"
pdx = bpy.data.materials.new("PDXmat_valkur")
pdx["shader"] = "standard"
pdx["diff"] = "valkur_diffuse.dds"
pdx["n"] = "valkur_normal.dds"
pdx["spec"] = "valkur_properties.dds"
low.data.materials.clear()
low.data.materials.append(pdx)

write_diffuse(bpy.data.images["valkur_bake"], os.path.join(OUT_DIR, "valkur_diffuse.dds"))
write_rrxg(bpy.data.images["valkur_normal_bake"], os.path.join(OUT_DIR, "valkur_normal.dds"))
header = dds_header(4, 4)
with open(os.path.join(OUT_DIR, "valkur_properties.dds"), "wb") as handle:
    handle.write(header + bytes((0, 0, 0, 220)) * 16)

for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
low.select_set(True)
bpy.context.view_layer.objects.active = low
result = bpy.ops.io_pdx_mesh.export_mesh(
    filepath=os.path.join(OUT_DIR, "valkur.mesh"),
    chk_mesh=True,
    chk_skel=True,
    chk_locs=False,
    chk_selected=True,
    chk_asset=False,
    chk_gfx=False,
)
print("MESH", result, len(low.data.polygons), flush=True)
