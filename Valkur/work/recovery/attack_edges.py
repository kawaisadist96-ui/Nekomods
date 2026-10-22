import bpy,numpy as np,json,os
m=bpy.data.objects['Valkur_low'];a=next(q.object for q in m.modifiers if q.type=='ARMATURE');a.data.pose_position='POSE';act=bpy.data.actions['VALKUR_TEST_attack'];a.animation_data.action=act;a.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(217);bpy.context.view_layer.update()
e=m.evaluated_get(bpy.context.evaluated_depsgraph_get());em=e.to_mesh()
r=np.array([v.co[:] for v in m.data.vertices]);p=np.array([v.co[:] for v in em.vertices]);ed=np.array([edge.vertices[:] for edge in m.data.edges]);rs=np.linalg.norm(r[ed[:,0]]-r[ed[:,1]],axis=1);ps=np.linalg.norm(p[ed[:,0]]-p[ed[:,1]],axis=1)
names={g.index:g.name for g in m.vertex_groups}
indices=np.where((ps-rs>7)&(r[ed[:,0],0]>5)&(r[ed[:,0],2]<120))[0];indices=indices[np.argsort(-(ps-rs)[indices])]
for i in indices[:18]:
 print('EDGE',ed[i].tolist(),float(rs[i]),float(ps[i]))
 for vi in ed[i]:print(' V',r[vi].round(2).tolist(),[(names[g.group],round(g.weight,3)) for g in m.data.vertices[int(vi)].groups if g.weight>.01])
print('TOTAL',len(indices))

