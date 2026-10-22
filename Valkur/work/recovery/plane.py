import bpy,numpy as np,json
from collections import defaultdict
m=bpy.data.objects['Valkur_low']; me=m.data
h=m.vertex_groups['Character1_LeftHand'].index
hand={v.index for v in me.vertices if any(g.group==h and g.weight>.95 for g in v.groups)}
areas=defaultdict(float)
for p in me.polygons:
 if all(i in hand for i in p.vertices):areas[tuple(round(v,1) for v in p.normal)]+=p.area
for k,v in sorted(areas.items(),key=lambda x:-x[1])[:12]:print('NORMAL',k,v)
n=np.array(max(areas,key=areas.get));n=n/np.linalg.norm(n)
cs=np.array([tuple(p.center) for p in me.polygons if all(i in hand for i in p.vertices) and np.dot(p.normal,n)>.94])
d=np.median(cs@n)
print('PLANE',n.tolist(),float(d),'center',cs.mean(axis=0).tolist(),'bounds',cs.min(axis=0).tolist(),cs.max(axis=0).tolist())
