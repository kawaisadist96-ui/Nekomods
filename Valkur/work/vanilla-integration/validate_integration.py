import bpy,sys,os,json,re,numpy as np,hashlib
from mathutils import Matrix,Vector,Quaternion
W=os.path.dirname(__file__);sys.path.insert(0,os.path.join(os.path.dirname(W),'recovery'))
from io_pdx_mesh import pdx_data
from io_pdx_mesh.pdx_blender import blender_import_export as io
OUT=os.path.join(W,'staged/gfx/models/units/infantry/valkur');a=next(m.object for m in bpy.data.objects['Valkur_body'].modifiers if m.type=='ARMATURE');a.data.pose_position='POSE'
manifest=json.load(open(os.path.join(W,'animation-manifest.json')));report={'clips':[],'meshes':[]}
for spec in manifest:
 tree=pdx_data.read_meshfile(spec['output']);inf=tree.find('info');sam=tree.find('samples');count=spec['frames'];bn=[b.tag for b in inf];q=np.array(sam.attrib['q']).reshape(count,len(bn),4);t=np.array(sam.attrib['t']).reshape(count,len(bn),3)
 assert np.isfinite(q).all() and np.isfinite(t).all();assert abs(np.linalg.norm(q,axis=2)-1).max()<1e-5
 assert inf.attrib['fps']==[spec['fps']] and inf.attrib['sa']==[count]
 action=bpy.data.actions['VANILLA_'+spec['id']];a.animation_data_create();a.animation_data.action=action;a.animation_data.action_slot=action.slots[0];worst=0
 for f in sorted(set([0,count//2,count-1])):
  bpy.context.scene.frame_set(f+1);bpy.context.view_layer.update();globalpose={}
  for j,n in enumerate(bn):
   qr=q[f,j];local=io.swap_coord_space(Matrix.LocRotScale(Vector(t[f,j]),Quaternion((qr[3],qr[0],qr[1],qr[2])),Vector((1,1,1))))
   parent=a.data.bones[n].parent;globalpose[n]=globalpose[parent.name]@local if parent else local
   worst=max(worst,float(np.abs(np.array(globalpose[n])-np.array(a.pose.bones[n].matrix)).max()))
 assert worst<.002,(spec['id'],worst)
 report['clips'].append({'id':spec['id'],'samples':count,'fps':spec['fps'],'matrix_max_error':worst,'quaternion_min_adjacent_dot':float(np.sum(q[1:]*q[:-1],axis=2).min())})
for fn in ['valkur.mesh','valkur_shield.mesh','valkur_shield_back.mesh','valkur_sword.mesh','valkur_sword_stowed.mesh']:
 tr=pdx_data.read_meshfile(os.path.join(OUT,fn));obj=tr.find('object')[0];mesh=obj.find('mesh');sk=obj.find('skeleton');p=np.array(mesh.attrib['p']);assert np.isfinite(p).all()
 report['meshes'].append({'file':fn,'shape':obj.tag,'vertices':len(p)//3,'triangles':len(mesh.attrib['tri'])//3,'bones':len(sk) if sk is not None else 0})
asset=open(os.path.join(OUT,'valkur.asset')).read();nodes=set(re.findall(r'\bnode\s*=\s*(\w+)',asset));bone_names=set(a.data.bones.keys());assert nodes<=bone_names,(nodes-bone_names)
report['attachment_nodes']=sorted(nodes);report['animation_count']=len(report['clips']);report['total_samples']=sum(c['samples'] for c in report['clips']);report['in_game_test']=False
open(os.path.join(W,'integration-validation.json'),'w').write(json.dumps(report,indent=2));print('VALIDATED',report['animation_count'],report['total_samples'],'MAX',max(c['matrix_max_error'] for c in report['clips']),report['meshes'],flush=True)
