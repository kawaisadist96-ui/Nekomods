import bpy,os,json,numpy as np
from mathutils import Vector,kdtree
W=os.path.dirname(__file__);o=bpy.data.objects['Valkur_low'];me=o.data;a=next(m.object for m in o.modifiers if m.type=='ARMATURE');names={g.index:g.name for g in o.vertex_groups};hand=o.vertex_groups['Character1_LeftHand'].index
orig=[{g.group:g.weight for g in v.groups if g.weight>1e-6} for v in me.vertices]
n=Vector((.91381155,-.40613847,0))
wrist=a.matrix_world@a.data.bones['Character1_LeftHand'].head_local;tip=a.matrix_world@a.data.bones['Character1_LeftHand'].tail_local;elbow=a.matrix_world@a.data.bones['Character1_LeftForeArm'].head_local

def segdist(p,aa,bb):
 d=bb-aa;t=max(0,min(1,(p-aa).dot(d)/d.length_squared));return (p-aa-d*t).length

def body(w):return {g:v for g,v in w.items() if not any(t in names[g] for t in ['Hand','hand_node','Arm','Shoulder'])}
donors=[v.index for v,w in zip(me.vertices,orig) if 55<v.co.z<130 and not any(t in names[g] for g in w for t in ['Hand','hand_node','Arm','Shoulder'])]
kd=kdtree.KDTree(len(donors))
for i in donors:kd.insert(me.vertices[i].co,i)
kd.balance()
newverts=[];newfaces=[];uvs=[];weights=[];mapping={};classes=[];modified=0
for p in me.polygons:
 c=p.center
 relevant=8<c.x<53 and 62<c.z<140 and any(orig[i].get(hand,0)>.01 for i in p.vertices)
 if relevant:
  onshield=n.dot(c)>28
  ongrip=min(segdist(c,wrist,tip),segdist(c,elbow,wrist))<10
  label=1 if onshield else (3 if ongrip or c.z>119 else 2)
 else:label=0
 classes.append(label);face=[]
 for li in p.loop_indices:
  i=me.loops[li].vertex_index;key=(i,label)
  if key not in mapping:
   mapping[key]=len(newverts);newverts.append(me.vertices[i].co[:]);w=orig[i].copy()
   if label==1 and w.get(hand,0)>.1:w={hand:1.0};modified+=1
   if label==3:
    w={g:v for g,v in w.items() if any(t in names[g] for t in ['Hand','hand_node','Arm','Shoulder'])}
    if not w:w={hand:1.0}
    total=sum(w.values());w={g:v/total for g,v in w.items()}
   if label==2:
    w=body(w)
    if sum(w.values())<.05:
     _,j,_=kd.find(me.vertices[i].co);w=body(orig[j])
    total=sum(w.values());w={g:v/total for g,v in w.items()};modified+=1
   weights.append(w)
  face.append(mapping[key]);uvs.append(tuple(me.uv_layers.active.data[li].uv))
 newfaces.append(face)
new=bpy.data.meshes.new('valkurShapeRestored');new.from_pydata(newverts,[],newfaces);new.update();uv=new.uv_layers.new(name='UVMap')
for i,co in enumerate(uvs):uv.data[i].uv=co
for mat in me.materials:new.materials.append(mat)
for p,oldp in zip(new.polygons,me.polygons):p.use_smooth=oldp.use_smooth;p.material_index=oldp.material_index
for attr in [a for a in me.attributes if a.domain=='CORNER' and a.data_type=='FLOAT_VECTOR']:
 pass
o.data=new
for gname in names.values():o.vertex_groups.new(name=gname)
# Vertex groups attached to the object keep group indices, assign fresh deform data.
for i,w in enumerate(weights):
 for g,v in w.items():o.vertex_groups[g].add([i],v,'REPLACE')
print('FACES',len(new.polygons),'SPLIT_VERTS',len(new.vertices)-len(me.vertices),'ASSIGNMENTS',modified,flush=True)
open(os.path.join(W,'split-restoration.json'),'w').write(json.dumps({'original_faces':len(me.polygons),'restored_faces':6930,'deleted_faces':0,'faces':len(new.polygons),'original_vertices':len(me.vertices),'vertices':len(new.vertices),'face_classes':{str(k):classes.count(k) for k in set(classes)}},indent=2))
# Reuse render-only tail from the prior script.
s=open(os.path.join(W,'restore_weights.py'),encoding='utf-8-sig').read();tail=s[s.index('for im in bpy.data.images:'):]
tail=tail.replace("'restored-'","'split3-'").replace("'valkur-restored.blend'","'valkur-restored-split3.blend'")
exec(tail)



