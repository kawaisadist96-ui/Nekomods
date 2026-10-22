import bpy,numpy as np,json,os,hashlib
W=os.path.dirname(__file__); o=bpy.data.objects['Valkur_low'];m=o.data;a=next(x.object for x in o.modifiers if x.type=='ARMATURE')
with bpy.data.libraries.load(os.path.join(os.path.dirname(W),'valkur-export-ready.blend'),link=False) as (src,dst):dst.objects=['Valkur_low']
b=dst.objects[0]
def geo(mesh):
 h=hashlib.sha256()
 for p in mesh.polygons:
  for li in p.loop_indices:
   h.update(np.array(mesh.vertices[mesh.loops[li].vertex_index].co,dtype='<f4').tobytes())
   h.update(np.array(mesh.uv_layers.active.data[li].uv,dtype='<f4').tobytes())
 return h.hexdigest()
report={'geometry_uv_identical_to_uncut':geo(m)==geo(b.data),'vertices':len(m.vertices),'faces':len(m.polygons),'bones':len(a.data.bones)}
weights=lambda ob:[{ob.vertex_groups[g.group].name:round(g.weight,7) for g in v.groups if g.weight>1e-6} for v in ob.data.vertices]
w0=weights(b);w1=weights(o);changed=[i for i,(x,y) in enumerate(zip(w0,w1)) if x!=y]
report['changed_weights']=len(changed);report['max_influences']=max(map(len,w1));report['max_weight_sum_error']=max(abs(sum(w.values())-1) for w in w1);report['unweighted']=sum(not w for w in w1)
r=np.array([v.co[:] for v in m.vertices]);ed=np.array([e.vertices[:] for e in m.edges]);rs=np.linalg.norm(r[ed[:,0]]-r[ed[:,1]],axis=1)
region=(r[:,0]>8)&(r[:,0]<31)&(r[:,2]>65)&(r[:,2]<114)&((r@np.array([.91381155,-.40613847,0]))<27)
edge_mask=region[ed[:,0]]&region[ed[:,1]]
report['tests']=[]
for suffix in ['idle','walk','attack','defense']:
 ac=bpy.data.actions['VALKUR_TEST_'+suffix];a.animation_data.action=ac;a.animation_data.action_slot=ac.slots[0];a.data.pose_position='POSE'
 frames=range(int(ac.frame_range[0]),int(ac.frame_range[1])+1)
 worst=(0,0);count=0
 for f in frames:
  bpy.context.scene.frame_set(f);bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=np.empty(len(m.vertices)*3);em.vertices.foreach_get('co',co);co=co.reshape(-1,3)
  ps=np.linalg.norm(co[ed[:,0]]-co[ed[:,1]],axis=1);extra=(ps-rs)[edge_mask];value=float(extra.max());count+=int((extra>8).sum())
  if value>worst[0]:worst=(value,f)
  ev.to_mesh_clear()
 report['tests'].append({'action':suffix,'frames':len(frames),'max_side_edge_extra_cm':worst[0],'worst_frame':worst[1],'edge_frame_occurrences_over8cm':count})
 print('SCAN',report['tests'][-1],flush=True)
report['bone_rest_unchanged']=all(np.allclose(np.array(a.data.bones[bone.name].matrix_local),np.array(bone.matrix_local)) for bone in next(q.object for q in b.modifiers if q.type=='ARMATURE').data.bones)
open(os.path.join(W,'validation-backup.json'),'w').write(json.dumps(report,indent=2));print('VALIDATION',report,flush=True)



