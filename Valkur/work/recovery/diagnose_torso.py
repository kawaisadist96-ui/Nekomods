import bpy,os,json,numpy as np
W=os.path.dirname(__file__);o=bpy.data.objects['Valkur_low'];m=o.data;a=next(x.object for x in o.modifiers if x.type=='ARMATURE')
r=np.array([v.co[:] for v in m.vertices]);ed=np.array([e.vertices[:] for e in m.edges]);rs=np.linalg.norm(r[ed[:,0]]-r[ed[:,1]],axis=1)
names={g.index:g.name for g in o.vertex_groups}
weights=[{names[g.group]:round(g.weight,4) for g in v.groups if g.weight>1e-5} for v in m.vertices]
report={'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in a.data.bones if any(t in b.name for t in ['Arm','Hand','Shoulder','hand_node'])},'tests':[]}
for label,f in [('walk',20),('attack',95),('attack',218),('defense',53)]:
 ac=bpy.data.actions['VALKUR_TEST_'+label];a.animation_data.action=ac;a.animation_data.action_slot=ac.slots[0];a.data.pose_position='POSE';bpy.context.scene.frame_set(f);bpy.context.view_layer.update()
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=np.array([v.co[:] for v in em.vertices]);extra=np.linalg.norm(co[ed[:,0]]-co[ed[:,1]],axis=1)-rs
 mask=(r[ed[:,0],2]>108)&(r[ed[:,1],2]>108)&(r[ed[:,0],2]<149)&(r[ed[:,1],2]<149)&(np.abs(r[ed[:,0],0])<20)&(np.abs(r[ed[:,1],0])<20)
 inds=np.flatnonzero(mask);order=inds[np.argsort(extra[inds])[-12:][::-1]]
 report['tests'].append({'action':label,'frame':f,'worst':[{'edge':ed[i].tolist(),'rest':r[ed[i]].tolist(),'extra':float(extra[i]),'weights':[weights[j] for j in ed[i]]} for i in order]})
 ev.to_mesh_clear()
open(os.path.join(W,'torso-diagnosis.json'),'w').write(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
