import bpy,os,sys,json
from mathutils import Matrix,Vector
W=os.path.dirname(__file__);sys.path.insert(0,os.path.join(os.path.dirname(W),'recovery'))
from io_pdx_mesh.pdx_blender import blender_import_export as io
a=next(x.object for x in bpy.data.objects['Valkur_body'].modifiers if x.type=='ARMATURE');s=bpy.context.scene
old=set(bpy.data.objects);io.import_meshfile(r'C:\Game\Crusader Kings 3\game\gfx\models\units\infantry\attachment_fp1_horn\unit_fp1_horn.mesh',imp_mesh=True,imp_skel=False,imp_locs=False)
horn=next(x for x in set(bpy.data.objects)-old if x.type=='MESH');horn.name='Valkur_vanilla_horn';node='Right_hand_node_1';horn.parent=a;horn.parent_type='BONE';horn.parent_bone=node;horn.matrix_parent_inverse=Matrix.Translation((0,-a.data.bones[node].length,0));horn.matrix_basis=Matrix.Identity(4);horn.scale=(4/3,)*3
# Resolve vanilla horn's texture reference explicitly for the Blender preview.
for im in bpy.data.images:
 if im.name.startswith('unit_fp1_infantry_03_') and not im.has_data:
  p=os.path.join(r'C:\Game\Crusader Kings 3\game\gfx\models\units\infantry\unit_fp1_infantry_03',im.name)
  if os.path.exists(p):im.filepath=p;im.reload()
props={k:bpy.data.objects['Valkur_'+k] for k in ['shield','shield_back','sword','sword_stowed']}
def preview(aid,time,shown):
 ac=bpy.data.actions['VANILLA_'+aid];fps=ac['source_fps'];a.animation_data_create();a.animation_data.action=ac;a.animation_data.action_slot=ac.slots[0];a.data.pose_position='POSE';s.render.fps=round(fps);s.render.fps_base=round(fps)/fps;s.frame_set(round(time*fps)+1)
 for k,obj in props.items():obj.hide_render=k not in shown
 horn.hide_render='horn' not in shown
 bpy.context.view_layer.update();s.render.filepath=os.path.join(W,'event-'+aid+'-'+str(time)+'.png');bpy.ops.render.render(write_still=True)
for time in [.73,1.5,3.,6.]:preview('gathering_army_viking_animation',time,['horn','shield_back','sword_stowed'])
preview('spawn_animation',0.,['shield_back'])
preview('despawn_animation',2.,['shield_back','sword_stowed'])
a.data.pose_position='REST';horn.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W,'valkur-vanilla-preview.blend'),compress=True)
