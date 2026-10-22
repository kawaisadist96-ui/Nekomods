"""Separate fused arm/body contact seams without removing any face or UV corner."""
import bpy,os,json
from mathutils import Vector,kdtree
W=os.path.dirname(__file__);o=bpy.data.objects['Valkur_low'];m=o.data;a=next(x.object for x in o.modifiers if x.type=='ARMATURE')
names={g.index:g.name for g in o.vertex_groups};idx={v:k for k,v in names.items()};orig=[{g.group:g.weight for g in v.groups if g.weight>1e-6} for v in m.vertices]
normal=Vector((.91381155,-.40613847,0))
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def segdist(p,u,v):d=v-u;t=max(0,min(1,(p-u).dot(d)/d.length_squared));return (p-u-d*t).length
def limb(g):return any(t in names[g] for t in ['Arm','Hand','hand_node','Shoulder'])
bones={side:{key:a.data.bones['Character1_'+side+key].head_local.copy() for key in ['Arm','ForeArm','ForeArmRoll','Hand','HandRing3']} for side in ['Left','Right']}
donors=[v.index for v,w in zip(m.vertices,orig) if 80<v.co.z<141 and not any(limb(g) for g in w)]
kd=kdtree.KDTree(len(donors))
for i in donors:kd.insert(m.vertices[i].co,i)
kd.balance()
def classify(c):
 x,y,z=c
 if not 85<z<140:return 0
 side='Left' if x>0 else 'Right';sgn=1 if x>0 else -1;b=bones[side]
 if z<106:
  # Closed fist lies outside the skirt, centered beyond the fitted finger bones.
  onarm=sgn*x>25 and segdist(c,b['Hand'],b['HandRing3']+Vector((sgn*4,3,0)))<12
 else:
  onarm=sgn*x>17 and min(segdist(c,b['Arm'],b['ForeArm']),segdist(c,b['ForeArm'],b['Hand']))<9
  if side=='Left' and normal.dot(c)>27.5:onarm=False
 if onarm:return 1 if side=='Left' else 2
 # Keep the rigid shield and the sword intact.
 if side=='Left' and normal.dot(c)>27.5:return 0
 if side=='Right' and x<-25 and z<106:return 0
 if abs(x)>14 and z<136:return 3
 return 0
def assigned(i,label):
 w=orig[i].copy();p=m.vertices[i].co;z=p.z
 if label in (1,2):
  side='Left' if label==1 else 'Right';prefix='Character1_'+side;b=bones[side]
  upper=smooth((z-b['ForeArm'].z+7)/14);h=smooth((b['Hand'].z+4-z)/8);roll=smooth((b['ForeArm'].z-3-z)/12)
  target={idx[prefix+'Arm']:(1-h)*upper,idx[prefix+'ForeArm']:(1-h)*(1-upper)*(1-roll),idx[prefix+'ForeArmRoll']:(1-h)*(1-upper)*roll,idx[prefix+'Hand']:h}
  blend=1-smooth((z-134)/6)
  w={g:v*(1-blend) for g,v in w.items()}
  for g,v in target.items():w[g]=w.get(g,0)+v*blend
 elif label==3:
  w={g:v for g,v in w.items() if not limb(g)}
  if sum(w.values())<.01:
   _,j,_=kd.find(p);w={g:v for g,v in orig[j].items() if not limb(g)}
 pairs=sorted([(g,v) for g,v in w.items() if v>1e-6],key=lambda x:-x[1])[:4];total=sum(v for g,v in pairs)
 return {g:v/total for g,v in pairs}
vs=[];fs=[];uvs=[];ws=[];mapping={};classes=[]
for p in m.polygons:
 label=classify(p.center);classes.append(label);face=[]
 for li in p.loop_indices:
  i=m.loops[li].vertex_index;key=(i,label)
  if key not in mapping:
   mapping[key]=len(vs);vs.append(m.vertices[i].co[:]);ws.append(assigned(i,label))
  face.append(mapping[key]);uvs.append(tuple(m.uv_layers.active.data[li].uv))
 fs.append(face)
new=bpy.data.meshes.new('valkurShapeContacts');new.from_pydata(vs,[],fs);new.update();uv=new.uv_layers.new(name='UVMap')
for i,co in enumerate(uvs):uv.data[i].uv=co
for mat in m.materials:new.materials.append(mat)
for p,old in zip(new.polygons,m.polygons):p.use_smooth=old.use_smooth;p.material_index=old.material_index
attr=new.attributes.new('repair_region','INT','FACE')
for cell,label in zip(attr.data,classes):cell.value=label
o.data=new
for name in names.values():o.vertex_groups.new(name=name)
for i,w in enumerate(ws):
 for g,v in w.items():o.vertex_groups[g].add([i],v,'REPLACE')
report={'source':bpy.data.filepath,'vertices':len(vs),'extra_seam_vertices':len(vs)-len(m.vertices),'faces':len(fs),'face_regions':{str(k):classes.count(k) for k in set(classes)},'deleted_faces':0}
open(os.path.join(W,'contact-repair.json'),'w').write(json.dumps(report,indent=2));print('CONTACT_REPAIR',report,flush=True)
s=bpy.context.scene
for label,frame in [('walk',20),('attack',95),('defense',53)]:
 ac=bpy.data.actions['VALKUR_TEST_'+label];a.animation_data.action=ac;a.animation_data.action_slot=ac.slots[0];a.data.pose_position='POSE';s.frame_set(frame);bpy.context.view_layer.update();s.render.filepath=os.path.join(W,'contacts-'+label+'.png');bpy.ops.render.render(write_still=True)
a.data.pose_position='REST';bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W,'valkur-restored-contacts.blend'),compress=True)
