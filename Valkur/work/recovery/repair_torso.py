import bpy,os,json
W=os.path.dirname(__file__);o=bpy.data.objects['Valkur_low'];m=o.data;a=next(x.object for x in o.modifiers if x.type=='ARMATURE');names={g.index:g.name for g in o.vertex_groups};idx={v:k for k,v in names.items()}
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
spines=[('Character1_'+n,a.data.bones['Character1_'+n].head_local.z) for n in ['Hips','Spine','Spine1','Spine2']]
changed=[]
for v in m.vertices:
 x,y,z=v.co
 blend=(1-smooth((abs(x)-13)/5))*smooth((z-103)/7)*(1-smooth((z-141)/7))
 if blend<.001 or y>12 or y<-20:continue
 old={g.group:g.weight for g in v.groups}
 if sum(w for g,w in old.items() if any(t in names[g] for t in ['Head','Neck','Hand','hand_node']))>.1:continue
 target={idx[spines[-1][0]]:1.}
 for (n0,z0),(n1,z1) in zip(spines[:-1],spines[1:]):
  if z<=z1:
   t=smooth((z-z0)/(z1-z0));target={idx[n0]:1-t,idx[n1]:t};break
 mixed={g:w*(1-blend) for g,w in old.items()}
 for g,w in target.items():mixed[g]=mixed.get(g,0)+blend*w
 pairs=sorted([(g,w) for g,w in mixed.items() if w>1e-6],key=lambda x:-x[1])[:4];total=sum(w for g,w in pairs)
 for g in old:o.vertex_groups[g].remove([v.index])
 for g,w in pairs:o.vertex_groups[g].add([v.index],w/total,'REPLACE')
 changed.append(v.index)
open(os.path.join(W,'torso-repair.json'),'w').write(json.dumps({'changed_vertices':len(changed),'indices':changed,'spine_centers':spines},indent=2));print('TORSO',len(changed),flush=True)
s=bpy.context.scene
for label,frame in [('walk',20),('attack',218),('defense',71)]:
 ac=bpy.data.actions['VALKUR_TEST_'+label];a.animation_data.action=ac;a.animation_data.action_slot=ac.slots[0];a.data.pose_position='POSE';s.frame_set(frame);bpy.context.view_layer.update();s.render.filepath=os.path.join(W,'torso-'+label+'-'+str(frame)+'.png');bpy.ops.render.render(write_still=True)
a.data.pose_position='REST';bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W,'valkur-restored-torso.blend'),compress=True)
