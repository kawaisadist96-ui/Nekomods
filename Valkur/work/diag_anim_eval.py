import bpy

arm = bpy.data.objects["VALKUR_CK3_FITTED_61"]
print("FPS", bpy.context.scene.render.fps)
for name in ("VALKUR_TEST_idle", "VALKUR_TEST_walk"):
    action = bpy.data.actions[name]
    print("ACTION", name, "range", action.frame_range[:], "slots", len(action.slots))
    for slot in action.slots:
        print(" SLOT", slot.identifier, slot.target_id_type, getattr(slot, "name_display", ""))
    layers = list(action.layers)
    print(" LAYERS", len(layers))
    for layer in layers:
        for strip in layer.strips:
            print(" STRIP", strip.type, getattr(strip, "frame_start", None), getattr(strip, "frame_end", None))
            bags = list(strip.channelbags) if hasattr(strip, "channelbags") else []
            print("  BAGS", len(bags))
            for bag in bags:
                curves = list(bag.fcurves)
                print("  CURVES", len(curves), "slot", getattr(bag, "slot", None))
                if curves:
                    print("   FIRST", curves[0].data_path, "keys", len(curves[0].keyframe_points))

    print(" BONES0", arm.data.bones[0].name, "COUNT", len(arm.data.bones))
    bone_names = {b.name for b in arm.data.bones}
    mesh = next(o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) > 100000)
    groups = [g.name for g in mesh.vertex_groups]
    missing = [g for g in groups if g not in bone_names]
    print(" GROUPS", len(groups), "UNMATCHED", missing[:30], "count", len(missing))
    ad = arm.animation_data_create()
    ad.action = action
    if action.slots:
        ad.action_slot = action.slots[0]
    bone = arm.pose.bones["root"]
    for frame in (1, 20, 40, 60):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        q = tuple(round(v, 4) for v in bone.rotation_quaternion)
        loc = tuple(round(v, 3) for v in bone.location)
        print(" FRAME", frame, "q", q, "loc", loc)

from io_pdx_mesh.pdx_blender.blender_import_export import get_scene_animdata, get_skeleton_hierarchy

action = bpy.data.actions["VALKUR_TEST_walk"]
ad = arm.animation_data_create()
ad.action = action
ad.action_slot = action.slots[0]
bones = get_skeleton_hierarchy(arm)
print("EXPORT_BONES", len(bones), bones[0].name, bones[-1].name)
keys = get_scene_animdata(arm, bones, 1, 40)
moving = {name: list(data.keys()) for name, data in keys.items() if data}
print("MOVING", len(moving))
print("SAMPLE", list(moving.items())[:12])
