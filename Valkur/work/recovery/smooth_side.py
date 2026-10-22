from mathutils import Vector
import bpy,numpy as np,os,json
W=os.path.dirname(__file__);o=bpy.data.objects['Valkur_low'];me=o.data;a=next(m.object for m in o.modifiers if m.type=='ARMATURE');N=len(me.vertices);G=len(o.vertex_groups)
names={g.index:g.name for g in o.vertex_groups};r=np.array([v.co[:] for v in me.vertices]);weights=np.zeros((N,G),dtype=np.float64)
for v in me.vertices:
 for g in v.groups:weights[v.index,g.group]=g.weight
limb=[g for g,n in names.items() if any(t in n for t in ['Hand','hand_node','Arm','Shoulder'])]
allowed=(weights[:,limb].sum(axis=1)<1e-6)
mask=allowed&(r[:,0]>5)&(r[:,0]<33)&(r[:,2]>64)&(r[:,2]<119)
ed=np.array([e.vertices[:] for e in me.edges]);ed=ed[allowed[ed[:,0]]&allowed[ed[:,1]]]
i=np.concatenate([ed[:,0],ed[:,1]]);j=np.concatenate([ed[:,1],ed[:,0]])
length=np.linalg.norm(r[i]-r[j],axis=1);factor=1/np.maximum(length,.2)
sumf=np.bincount(i,weights=factor,minlength=N)
blend=np.minimum.reduce([(r[:,0]-5)/4,(33-r[:,0])/4,(r[:,2]-64)/6,(119-r[:,2])/6,np.ones(N)])
blend=np.clip(blend,0,1)*mask*.5
original=weights.copy()
for step in range(18):
 avg=np.zeros_like(weights)
 for g in np.where(weights[mask].sum(axis=0)>0)[0]:avg[:,g]=np.bincount(i,weights=factor*weights[j,g],minlength=N)/np.maximum(sumf,1e-9)
 weights=weights*(1-blend[:,None])+avg*blend[:,None]
modified=[]
for vi in np.where(mask)[0]:
 row=weights[vi];indices=np.argsort(row)[-4:];total=row[indices].sum()
 if total<1e-6:continue
 new=np.zeros(G);new[indices]=row[indices]/total
 if np.max(abs(new-original[vi]))<1e-5:continue
 for g in np.where(original[vi]>0)[0]:o.vertex_groups[int(g)].remove([int(vi)])
 for g in indices:
  if new[g]>1e-6:o.vertex_groups[int(g)].add([int(vi)],float(new[g]),'REPLACE')
 modified.append(int(vi))
print('LOCAL_SMOOTH',len(modified),flush=True)
open(os.path.join(W,'local-smooth.json'),'w').write(json.dumps({'vertices':len(modified),'iterations':18,'region':'left hip/thigh and skirt only, equipment excluded'},indent=2))
s=open(os.path.join(W,'restore_weights.py'),encoding='utf-8-sig').read();tail=s[s.index('for im in bpy.data.images:'):];tail=tail.replace("'restored-'","'final-'").replace("'valkur-restored.blend'","'valkur-restored-smoothed.blend'");exec(tail)

