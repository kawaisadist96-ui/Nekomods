import bpy,json,os
from collections import Counter
from mathutils import Vector
m=bpy.data.objects['Valkur_low'];a=next(q.object for q in m.modifiers if q.type=='ARMATURE')
names={g.index:g.name for g in m.vertex_groups}
for z0 in range(60,120,10):
 rows=[]
 for x0 in range(0,50,5):
  verts=[v for v in m.data.vertices if x0<=v.co.x<x0+5 and z0<=v.co.z<z0+10]
  c=Counter(names[max(v.groups,key=lambda g:g.weight).group] for v in verts if v.groups)
  h=[v for v in verts if any(names[g.group]=='Character1_LeftHand' and g.weight>.5 for g in v.groups)]
  if h:rows.append([x0,len(h),[round(min(v.co.y for v in h),1),round(max(v.co.y for v in h),1)],c.most_common(2)])
 print(z0,rows,flush=True)
for b in a.data.bones:
 if 'Left' in b.name and any(n in b.name for n in ['Hand','Arm','Leg']):print(b.name,list(a.matrix_world@b.head_local))
