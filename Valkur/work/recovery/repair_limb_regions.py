"""Local forearm and fixed-grip repair; preserve every mesh face and rest transform."""
import bpy,os,json,numpy as np
from mathutils import Vector
W=os.path.dirname(__file__);o=bpy.data.objects['Valkur_low'];m=o.data;a=next(x.object for x in o.modifiers if x.type=='ARMATURE')
names={g.index:g.name for g in o.vertex_groups};index={v:k for k,v in names.items()};orig=[{g.group:g.weight for g in v.groups if g.weight>1e-6} for v in m.vertices]
def smooth(x): x=max(0.,min(1.,x));return x*x*(3-2*x)
def segdist(p,u,v): d=v-u;t=max(0,min(1,(p-u).dot(d)/d.length_squared));return (p-u-d*t).length
normal=Vector((.91381155,-.40613847,0));counts={};selected={}
for side,sign in [('Left',1),('Right',-1)]:
 prefix='Character1_'+side
 shoulder=a.data.bones[prefix+'Arm'].head_local;elbow=a.data.bones[prefix+'ForeArm'].head_local;wrist=a.data.bones[prefix+'Hand'].head_local;tip=a.data.bones[prefix+'HandRing3'].head_local
 picked=[]
 for v,w in zip(m.vertices,orig):
  p=v.co;z=p.z;lw=sum(val for g,val in w.items() if side in names[g] and any(t in names[g] for t in ['Arm','Hand']))
  if lw<.015 or sign*p.x<19 or not 86<z<143:continue
  if side=='Left' and normal.dot(p)>27.5:continue
  if min(segdist(p,shoulder,elbow),segdist(p,elbow,wrist),segdist(p,wrist,tip))>9:continue
  upper=smooth((z-(elbow.z-7))/14);hand=smooth((wrist.z+4-z)/8);roll=smooth((elbow.z-3-z)/12)
  target={index[prefix+'Arm']:(1-hand)*upper,index[prefix+'ForeArm']:(1-hand)*(1-upper)*(1-roll),index[prefix+'ForeArmRoll']:(1-hand)*(1-upper)*roll,index[prefix+'Hand']:hand}
  # Feather the upper-arm endpoint into the established shoulder weights.
  blend=1-smooth((z-137)/6)
  mixed={g:val*(1-blend) for g,val in w.items()}
  for g,val in target.items():mixed[g]=mixed.get(g,0)+blend*val
  ranked=sorted([(g,val) for g,val in mixed.items() if val>1e-6],key=lambda x:-x[1])[:4];total=sum(val for g,val in ranked)
  for g in w:o.vertex_groups[g].remove([v.index])
  for g,val in ranked:o.vertex_groups[g].add([v.index],val/total,'REPLACE')
  picked.append(v.index)
 counts[side]=len(picked);selected[side]=picked
open(os.path.join(W,'limb-repair.json'),'w').write(json.dumps({'vertices_changed':counts,'selected_vertices':selected,'deleted_faces':0},indent=2));print('LIMB_REPAIR',counts,flush=True)
s=bpy.context.scene
for label,frame in [('walk',20),('attack',95),('defense',53)]:
 ac=bpy.data.actions['VALKUR_TEST_'+label];a.animation_data.action=ac;a.animation_data.action_slot=ac.slots[0];a.data.pose_position='POSE';s.frame_set(frame);bpy.context.view_layer.update();s.render.filepath=os.path.join(W,'limbs-'+label+'.png');bpy.ops.render.render(write_still=True)
a.data.pose_position='REST';bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W,'valkur-restored-limbs.blend'),compress=True)
