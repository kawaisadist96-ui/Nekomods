import bpy,sys,os,json,numpy as np
from mathutils import Matrix,Vector
W=os.path.dirname(__file__);sys.path.insert(0,os.path.join(os.path.dirname(W),'recovery'))
from io_pdx_mesh.pdx_blender import blender_import_export as io
from io_pdx_mesh import pdx_data
OUT=os.path.join(W,'staged/gfx/models/units/infantry/valkur');o=bpy.data.objects['Valkur_low'];m=o.data;a=next(x.object for x in o.modifiers if x.type=='ARMATURE');a.data.pose_position='REST'
names={g.index:g.name for g in o.vertex_groups};weights=[{names[g.group]:g.weight for g in v.groups} for v in m.vertices];uv=m.uv_layers.active
m.name='preserved_original_shape'
im=bpy.data.images['valkur_bake'];iw,ih=im.size;pixels=np.array(im.pixels[:],dtype=np.float32).reshape(ih,iw,4)
normal=Vector((.91381155,-.40613847,0));classes=[]
for p in m.polygons:
 c=p.center;x,y,z=c;d=normal.dot(c);lh=sum(weights[i].get('Character1_LeftHand',0) for i in p.vertices)/len(p.vertices);rh=sum(weights[i].get('Character1_RightHand',0) for i in p.vertices)/len(p.vertices)
 uvco=np.mean([uv.data[i].uv[:] for i in p.loop_indices],axis=0);rgb=pixels[int(uvco[1]*ih)%ih,int(uvco[0]*iw)%iw,:3];skin=rgb[0]>.43 and .58<rgb[1]/max(rgb[0],1e-6)<.88 and rgb[2]>.6*rgb[1]
 label='body'
 if x>16 and 64<z<136 and d>27.8 and lh>.8:
  if not (skin and 86<z<105 and -8<y<8 and x<37):label='shield'
 if x<-25 and rh>.8 and (z<88 or (z<101 and ((x+34)**2+(y-1)**2)<2.3**2 and not skin)):label='sword'
 classes.append(label)
def make(name,label,transform=Matrix.Identity(4),skinned=False):
 verts=[];faces=[];uvs=[];mapping={};ws=[];oldpolys=[]
 for p,cl in zip(m.polygons,classes):
  if cl!=label:continue
  face=[]
  for li in p.loop_indices:
   vi=m.loops[li].vertex_index
   if vi not in mapping:mapping[vi]=len(verts);verts.append(transform@m.vertices[vi].co);ws.append(weights[vi])
   face.append(mapping[vi]);uvs.append(tuple(uv.data[li].uv))
  faces.append(face);oldpolys.append(p)
 mesh=bpy.data.meshes.new(name+'Shape');mesh.from_pydata(verts,[],faces);mesh.update();uvnew=mesh.uv_layers.new(name='UVMap')
 for li,co in enumerate(uvs):uvnew.data[li].uv=co
 for mat in m.materials:mesh.materials.append(mat)
 for p,old in zip(mesh.polygons,oldpolys):p.use_smooth=old.use_smooth;p.material_index=old.material_index
 obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj)
 if skinned:
  for n in names.values():obj.vertex_groups.new(name=n)
  for vi,w in enumerate(ws):
   for n,v in w.items():obj.vertex_groups[n].add([vi],v,'REPLACE')
  mod=obj.modifiers.new('Armature','ARMATURE');mod.object=a
 return obj
body=make('Valkur_body','body',skinned=True);body.data.name='valkurShape'
from mathutils import Quaternion
native=json.load(open(os.path.join(os.path.dirname(os.path.dirname(W)),'reports/native-bones.json')));N={q['name']:Matrix(q['matrix_local']) for q in native};F={b.name:b.matrix_local.copy() for b in a.data.bones};P={b.name:b.parent.name if b.parent else None for b in a.data.bones};C={n:Quaternion() for n in F}
for side in ['Left','Right']:
 for first,second in [('Shoulder','Arm'),('Arm','ForeArm'),('ForeArm','Hand'),('UpLeg','Leg'),('Leg','Foot'),('Foot','ToeBase')]:
  n='Character1_'+side+first;ch='Character1_'+side+second;C[n]=(F[ch].translation-F[n].translation).rotation_difference(N[ch].translation-N[n].translation)
 for n in F:
  if n.startswith('Character1_'+side+'Hand') or n=='Character1_'+side+'ForeArmRoll':C[n]=C['Character1_'+side+'ForeArm'].copy()
R={}
for b in io.get_skeleton_hierarchy(a):
 n=b.name;p=P[n];rot=C[n]@F[n].to_quaternion();pos=F[n].translation if not p else R[p].translation+R[p].to_quaternion()@F[p].to_quaternion().inverted()@(F[n].translation-F[p].translation)
 if '_node_' in n and p:pos=R[p].translation+N[n].translation-N[p].translation;rot=N[n].to_quaternion()
 R[n]=Matrix.LocRotScale(pos,rot,Vector((1,1,1)))
def prop_transform(node,hand):return R[node].inverted()@Matrix.Translation(R[hand].translation)@C[hand].to_matrix().to_4x4()@Matrix.Translation(-F[hand].translation)
left=R['Left_hand_node_1'];right=R['Right_hand_node_1'];back=R['back_node_1'];hip=R['Left_hip_node_1']
shield=make('Valkur_shield','shield',prop_transform('Left_hand_node_1','Character1_LeftHand'));sword=make('Valkur_sword','sword',prop_transform('Right_hand_node_1','Character1_RightHand'))
sc=[p.center for p,cl in zip(m.polygons,classes) if cl=='shield'];center=sum(sc,Vector())/len(sc)
back_transform=Matrix.Translation(Vector((0,18,126)))@normal.rotation_difference(Vector((0,-1,0))).to_matrix().to_4x4()@Matrix.Translation(-center)
shieldback=make('Valkur_shield_back','shield',back.inverted()@back_transform)
stow_transform=Matrix.Translation(Vector((-18,4,105)))@Matrix.Rotation(.15,4,'Y')@Matrix.Translation(Vector((34,-1,-94)))
swordhip=make('Valkur_sword_stowed','sword',hip.inverted()@stow_transform)
assert len(body.data.polygons)+len(shield.data.polygons)+len(sword.data.polygons)==len(m.polygons)
o.hide_render=True;o.hide_set(True)
for mat in body.data.materials:mat['shader']='standard';mat['diff']='valkur_diffuse.dds';mat['n']='valkur_normal.dds';mat['spec']='valkur_properties.dds'
for obj,fn,skel in [(body,'valkur.mesh',True),(shield,'valkur_shield.mesh',False),(shieldback,'valkur_shield_back.mesh',False),(sword,'valkur_sword.mesh',False),(swordhip,'valkur_sword_stowed.mesh',False)]:
 for q in bpy.context.view_layer.objects:q.select_set(False)
 obj.select_set(True);bpy.context.view_layer.objects.active=obj
 io.export_meshfile(os.path.join(OUT,fn),exp_mesh=True,exp_skel=skel,exp_locs=False,exp_selected=True)
for obj,node in [(shield,'Left_hand_node_1'),(shieldback,'back_node_1'),(sword,'Right_hand_node_1'),(swordhip,'Left_hip_node_1')]:
 obj.parent=a;obj.parent_type='BONE';obj.parent_bone=node;obj.matrix_parent_inverse=Matrix.Translation((0,-a.data.bones[node].length,0));obj.matrix_basis=Matrix.Identity(4)
shieldback.hide_render=True;swordhip.hide_render=True
report={'source_faces':len(m.polygons),'body_faces':len(body.data.polygons),'shield_faces':len(shield.data.polygons),'sword_faces':len(sword.data.polygons),'deleted_faces':0,'node_names':[b.name for b in a.data.bones if 'node' in b.name]}
open(os.path.join(W,'equipment-report.json'),'w').write(json.dumps(report,indent=2));print('EQUIPMENT',report,flush=True)
s=bpy.context.scene
shield.hide_render=True;sword.hide_render=True;s.render.filepath=os.path.join(W,'body-without-equipment.png');bpy.ops.render.render(write_still=True)
ac=bpy.data.actions['VANILLA_idle_base_animation'];a.animation_data_create();a.animation_data.action=ac;a.animation_data.action_slot=ac.slots[0];a.data.pose_position='POSE';s.frame_set(1);shield.hide_render=False;swordhip.hide_render=False
s.render.filepath=os.path.join(W,'equipment-idle.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W,'valkur-vanilla-equipment.blend'),compress=True)
