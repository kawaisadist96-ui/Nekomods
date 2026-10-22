"""Re-export idle and walk with the armature in pose mode. Does not save the blend."""
import os

import bpy

OUT_DIR = r"C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test\gfx\models\units\infantry\valkur"
arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
arm.data.pose_position = "POSE"
bpy.context.scene.render.fps = 60


def export_action(action_name, filename, start, end):
    action = bpy.data.actions[action_name]
    ad = arm.animation_data_create()
    ad.action = action
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
    print("ANIM", action_name, result, os.path.getsize(path), flush=True)


export_action("VALKUR_TEST_attack", "valkur_attack.anim", 1, 309)
export_action("VALKUR_TEST_defense", "valkur_defense.anim", 1, 309)
print("DONE", flush=True)
