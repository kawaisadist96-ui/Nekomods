import bpy,os,sys,json,math,xml.etree.ElementTree as ET,numpy as np
from mathutils import Matrix,Vector,Quaternion
W=os.path.dirname(__file__);sys.path.insert(0,os.path.join(os.path.dirname(W),'recovery'))
from io_pdx_mesh import pdx_data
from io_pdx_mesh.pdx_blender import blender_import_export as io
o=bpy.data.objects['Valkur_low'];a=next(m.object for m in o.modifiers if m.type=='ARMATURE');a.animation_data_clear();a.data.pose_position='POSE'
audit=json.load(open(os.path.join(W,'audit.json')));native=json.load(open(os.path.join(os.path.dirname(os.path.dirname(W)),'reports/native-bones.json')))
N={x['name']:Matrix(x['matrix_local']) for x in native};F={b.name:b.matrix_local.copy() for b in a.data.bones};P={b.name:b.parent.name if b.parent else None for b in a.data.bones};order=[b.name for b in io.get_skeleton_hierarchy(a)]
NL={n:(N[P[n]].inverted()@N[n] if P[n] else N[n]) for n in order};FL={n:(F[P[n]].inverted()@F[n] if P[n] else F[n]) for n in order}
children={}
for side in ['Left','Right']:
 for first,second in [('Shoulder','Arm'),('Arm','ForeArm'),('ForeArm','Hand'),('UpLeg','Leg'),('Leg','Foot'),('Foot','ToeBase')]:children['Character1_'+side+first]='Character1_'+side+second
C={n:Quaternion() for n in order}
for n,ch in children.items():C[n]=(F[ch].translation-F[n].translation).rotation_difference(N[ch].translation-N[n].translation)
for side in ['Left','Right']:
 for n in order:
  if n.startswith('Character1_'+side+'Hand') or n=='Character1_'+side+'ForeArmRoll' or n==side+'_hand_node_1':C[n]=C['Character1_'+side+'ForeArm'].copy()
scale=F['Character1_Hips'].translation.z/N['Character1_Hips'].translation.z
outdir=os.path.join(W,'staged','gfx/models/units/infantry/valkur');os.makedirs(outdir,exist_ok=True)
summary=[]
for spec in audit['animations']:
 src=pdx_data.read_meshfile(spec['source']);info=src.find('info');samples=src.find('samples');count=int(spec['samples']);fps=spec['fps'];bn=[io.clean_imported_name(x.tag) for x in info];assert set(bn)==set(order)
 tracks={n:{} for n in bn};ptr={k:0 for k in 'tqs'}
 for f in range(count):
  for bone,n in zip(info,bn):
   for k,size in [('t',3),('q',4),('s',len(bone.attrib['s']))]:
    if k in bone.attrib['sa'][0]:v=samples.attrib[k][ptr[k]:ptr[k]+size];ptr[k]+=size
    else:v=bone.attrib[k]
    tracks[n].setdefault(k,[]).append(v)
 poses=[];localdata={n:[] for n in order};basisdata={n:[] for n in order}
 for f in range(count):
  nativepose={};target={}
  for n in order:
   tr=tracks[n];q=tr['q'][f];s=tr['s'][f];s=s*3 if len(s)==1 else s
   mat=io.swap_coord_space(Matrix.LocRotScale(Vector(tr['t'][f]),Quaternion((q[3],q[0],q[1],q[2])),Vector(s)))
   nativepose[n]=(nativepose[P[n]]@mat if P[n] else mat)
   rot=nativepose[n].to_quaternion()@N[n].to_quaternion().inverted()@C[n]@F[n].to_quaternion()
   if not P[n]:pos=nativepose[n].translation*scale
   else:
    parent=P[n];offset=F[n].translation-F[parent].translation
    delta=mat.translation-NL[n].translation
    # Preserve root/pelvis motion; child segment lengths stay fitted to the model.
    if n=='Character1_Hips':offset+=N[parent].to_3x3()@delta*scale
    pos=target[parent].translation+target[parent].to_quaternion()@F[parent].to_quaternion().inverted()@offset
   if '_node_' in n and P[n]:
    pos=target[P[n]].translation+(nativepose[n].translation-nativepose[P[n]].translation)
    rot=nativepose[n].to_quaternion()
   target[n]=Matrix.LocRotScale(pos,rot,Vector((1,1,1)))
  for n in order:
   local=target[P[n]].inverted()@target[n] if P[n] else target[n]
   localdata[n].append(io.swap_coord_space(local).decompose());basisdata[n].append((FL[n].inverted()@local).decompose())
  poses.append(target)
 for n in order:
  prev=None
  for t,q,s in localdata[n]:
   if prev is not None and prev.dot(q)<0:q.negate()
   prev=q.copy()
 root=ET.Element('File',{'pdxasset':[1,0]});inf=ET.SubElement(root,'info',{'fps':[fps],'sa':[count],'j':[len(order)]});sam=ET.SubElement(root,'samples',{'t':[],'q':[]})
 for n in order:
  t,q,s=localdata[n][0];ET.SubElement(inf,n,{'sa':['tq'],'t':list(t),'q':[q.x,q.y,q.z,q.w],'s':[1.]})
 for f in range(count):
  for n in order:
   t,q,s=localdata[n][f];sam.attrib['t'].extend(t);sam.attrib['q'].extend([q.x,q.y,q.z,q.w])
 path=os.path.join(outdir,'vanilla_'+spec['id']+'.anim');pdx_data.write_animfile(path,root)
 check=pdx_data.read_meshfile(path);assert check.find('info').attrib['fps']==[fps] and check.find('info').attrib['sa']==[count]
 action=bpy.data.actions.new('VANILLA_'+spec['id']);slot=action.slots.new('OBJECT',a.name);bag=action.layers.new('Retarget').strips.new(type='KEYFRAME').channelbag(slot,ensure=True);action.use_fake_user=True;action['source']=spec['source'];action['source_fps']=fps
 for n in order:
  data=basisdata[n];prev=None
  for t,q,s in data:
   if prev is not None and prev.dot(q)<0:q.negate()
   prev=q.copy()
  for prop,col,dim in [('location',0,3),('rotation_quaternion',1,4),('scale',2,3)]:
   for j in range(dim):
    fc=bag.fcurves.new(data_path='pose.bones["'+n+'"].'+prop,index=j);fc.keyframe_points.add(count);fc.keyframe_points.foreach_set('co',[v for f,d in enumerate(data) for v in (float(f+1),float(d[col][j]))])
    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
    fc.update()
  a.pose.bones[n].rotation_mode='QUATERNION'
 summary.append({'id':spec['id'],'fps':fps,'frames':count,'output':path,'duration':(count-1)/fps})
 print('RETARGET',spec['id'],count,flush=True)
 if spec['id'] in ['spawn_animation','despawn_animation','gathering_army_viking_animation','moving_standard_animation']:
  a.animation_data_create();a.animation_data.action=action;a.animation_data.action_slot=slot
  s=bpy.context.scene;s.render.fps=round(fps);s.render.fps_base=round(fps)/fps
  for frame in ([1,count//2,count] if 'spawn' in spec['id'] else [min(count,max(1,round(fps*2)))]):
   s.frame_set(frame);s.render.filepath=os.path.join(W,spec['id']+'-'+str(frame)+'.png');bpy.ops.render.render(write_still=True)
 a.animation_data_clear()
a.data.pose_position='REST';bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W,'valkur-vanilla-actions.blend'),compress=True)
open(os.path.join(W,'animation-manifest.json'),'w').write(json.dumps(summary,indent=2));print('DONE',len(summary),flush=True)
