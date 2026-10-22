"""Export the lowered walk. Leaves attack, defense, and idle untouched."""
import os

import bpy

OUT = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur\valkur_move.anim"
arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
action = bpy.data.actions["VALKUR_TEST_walk"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
arm.data.pose_position = "POSE"
scene = bpy.context.scene
scene.render.fps = 60
scene.frame_start = 1
scene.frame_end = 81
scene.io_pdx_export.custom_range = True
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
result = bpy.ops.io_pdx_mesh.export_anim(
    filepath=OUT,
    int_start=1,
    int_end=81,
    chk_uniform_scale=True,
)
print("ANIM", result, os.path.getsize(OUT), flush=True)
