import bpy,os,json
W=os.path.dirname(__file__);o=bpy.data.objects['Valkur_low'];m=o.data;a=next(x.object for x in o.modifiers if x.type=='ARMATURE');names={g.index:g.name for g in o.vertex_groups};idx={v:k for k,v in names.items()}
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
changed=[]
for v in m.vertices:
 x,y,z=v.co;blend=smooth((abs(x)-19)/4)*smooth((z-144)/6)*(1-smooth((z-161)/5))
 if blend<.001 or abs(x)>36 or y<-15 or y>17:continue
 side='Left' if x>0 else 'Right';prefix='Character1_'+side
 # Outer fur is part of the shoulder mantle, not the animated neck or head.
 outer=smooth((abs(x)-18)/10);upper=1-smooth((z-149)/8)
 target={idx['Character1_Spine2']:.65-.35*upper,idx[prefix+'Shoulder']:.35+.15*upper,idx[prefix+'Arm']:.2*upper}
 old={g.group:g.weight for g in v.groups};mixed={g:w*(1-blend) for g,w in old.items()}
 for g,w in target.items():mixed[g]=mixed.get(g,0)+blend*w
 pairs=sorted([(g,w) for g,w in mixed.items() if w>1e-6],key=lambda x:-x[1])[:4];total=sum(w for g,w in pairs)
 for g in old:o.vertex_groups[g].remove([v.index])
 for g,w in pairs:o.vertex_groups[g].add([v.index],w/total,'REPLACE')
 changed.append(v.index)
open(os.path.join(W,'collar-repair.json'),'w').write(json.dumps({'changed_vertices':len(changed),'indices':changed},indent=2));print('COLLAR',len(changed),flush=True)
s=bpy.context.scene
for label,frame in [('walk',20),('attack',95),('attack',218)]:
 ac=bpy.data.actions['VALKUR_TEST_'+label];a.animation_data.action=ac;a.animation_data.action_slot=ac.slots[0];a.data.pose_position='POSE';s.frame_set(frame);bpy.context.view_layer.update();s.render.filepath=os.path.join(W,'collar-'+label+'-'+str(frame)+'.png');bpy.ops.render.render(write_still=True)
a.data.pose_position='REST';bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W,'valkur-restored-collar.blend'),compress=True)
