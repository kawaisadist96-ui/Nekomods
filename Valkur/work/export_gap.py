"""Export the plate-cut mesh. Leaves textures and animations as they are."""
import os

import bpy

OUT = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur\valkur.mesh"
low = bpy.data.objects["Valkur_low"]
low.data.name = "valkurShape"
arm = next(mod.object for mod in low.modifiers if mod.type == "ARMATURE")
arm.data.pose_position = "REST"
pdx = bpy.data.materials.new("PDXmat_valkur")
pdx["shader"] = "standard"
pdx["diff"] = "valkur_diffuse.dds"
pdx["n"] = "valkur_normal.dds"
pdx["spec"] = "valkur_properties.dds"
low.data.materials.clear()
low.data.materials.append(pdx)
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
low.select_set(True)
bpy.context.view_layer.objects.active = low
result = bpy.ops.io_pdx_mesh.export_mesh(
    filepath=OUT,
    chk_mesh=True,
    chk_skel=True,
    chk_locs=False,
    chk_selected=True,
    chk_asset=False,
    chk_gfx=False,
)
print("MESH", result, len(low.data.polygons), os.path.getsize(OUT), flush=True)
