import bpy,os,json,math
from mathutils import Vector,kdtree
W=os.path.dirname(__file__)
o=bpy.data.objects['Valkur_low'];me=o.data;a=next(m.object for m in o.modifiers if m.type=='ARMATURE')
names={g.index:g.name for g in o.vertex_groups}; hand=o.vertex_groups['Character1_LeftHand'].index
n=Vector((.91381155,-.40613847,0)); d=34.3415
wrist=a.matrix_world@a.data.bones['Character1_LeftHand'].head_local
orig=[{g.group:g.weight for g in v.groups if g.weight>1e-6} for v in me.vertices]
def limb(g):return any(t in names[g] for t in ['Hand','hand_node','Arm','Shoulder'])
donors=[]
for v,w in zip(me.vertices,orig):
 if 55<v.co.z<123 and not any(limb(g) for g in w):donors.append(v.index)
kd=kdtree.KDTree(len(donors))
for i in donors:kd.insert(me.vertices[i].co,i)
kd.balance()
changes=[]
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
for v,w in zip(me.vertices,orig):
 if not (8<v.co.x<42 and 62<v.co.z<119):continue
 if hand not in w or w[hand]<.01:continue
 distance=d-n.dot(v.co)
 # Preserve shield slab and the grip around the wrist. Blend only skin behind shield.
 tip=a.matrix_world@a.data.bones['Character1_LeftHand'].tail_local
 arm_start=a.matrix_world@a.data.bones['Character1_LeftForeArm'].head_local
 def segdist(p,aa,bb):
  delta=bb-aa;t=max(0,min(1,(p-aa).dot(delta)/delta.length_squared));return (p-(aa+delta*t)).length
 grip_distance=min(segdist(v.co,wrist,tip),segdist(v.co,arm_start,wrist))
 cloth=smooth((distance-3)/2)*smooth((grip_distance-3)/2)
 if cloth<.001:continue
 _,j,dist=kd.find(v.co)
 target=orig[j]
 mixed={g:val*(1-cloth) for g,val in w.items()}
 for g,val in target.items():mixed[g]=mixed.get(g,0)+val*cloth
 ranked=sorted(mixed.items(),key=lambda p:-p[1])[:4];total=sum(val for g,val in ranked)
 for g in w:o.vertex_groups[g].remove([v.index])
 for g,val in ranked:
  if val>1e-6:o.vertex_groups[g].add([v.index],val/total,'REPLACE')
 changes.append([v.index,cloth,dist])
report={'source':'valkur-walk-fix.blend','faces':len(me.polygons),'vertices':len(me.vertices),'deleted_faces':0,'modified_weights':len(changes),'restored_faces':6930}
open(os.path.join(W,'restoration.json'),'w').write(json.dumps(report,indent=2))
print('CHANGED',len(changes),flush=True)
for im in bpy.data.images:
 if im.name=='valkur_bake':im.filepath=os.path.join(os.path.dirname(W),'valkur-bake.png');im.reload();im.pack()
 if im.name=='valkur_normal_bake':im.filepath=os.path.join(os.path.dirname(W),'valkur-normal-bake.png');im.reload();im.pack()
s=bpy.context.scene
for x in s.objects:x.hide_render=x!=o
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=700;s.render.resolution_y=850;s.render.resolution_percentage=100
s.world.color=(.35,.35,.35)
ld=bpy.data.lights.new('restore-key','AREA');ld.energy=350000;ld.shape='DISK';ld.size=140
l=bpy.data.objects.new('restore-key',ld);s.collection.objects.link(l);l.location=(70,-150,250);l.rotation_euler=((Vector((0,0,95))-l.location).to_track_quat('-Z','Y').to_euler())
ld2=bpy.data.lights.new('restore-fill','AREA');ld2.energy=180000;ld2.size=120
l2=bpy.data.objects.new('restore-fill',ld2);s.collection.objects.link(l2);l2.location=(-150,100,170);l2.rotation_euler=((Vector((0,0,95))-l2.location).to_track_quat('-Z','Y').to_euler())
cam=bpy.data.objects.new('restore-camera',bpy.data.cameras.new('restore-camera'));s.collection.objects.link(cam);s.camera=cam
cam.location=(130,-250,160);cam.rotation_euler=((Vector((0,0,95))-cam.location).to_track_quat('-Z','Y').to_euler());cam.data.type='ORTHO';cam.data.ortho_scale=215
for label,act,f in [('rest',None,1),('idle','VALKUR_TEST_idle',40),('walk','VALKUR_TEST_walk',20),('attack','VALKUR_TEST_attack',95),('defense','VALKUR_TEST_defense',95)]:
 a.data.pose_position='REST' if act is None else 'POSE'
 if act:
  ac=bpy.data.actions[act];a.animation_data.action=ac;a.animation_data.action_slot=ac.slots[0]
 s.frame_set(f);bpy.context.view_layer.update();s.render.filepath=os.path.join(W,'candidate2-'+label+'.png');bpy.ops.render.render(write_still=True)
a.data.pose_position='REST'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W,'valkur-restored-v2.blend'),compress=True)
print('SAVED_RESTORED',flush=True)

