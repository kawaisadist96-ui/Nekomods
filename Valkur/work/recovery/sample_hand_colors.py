import bpy,os,json,numpy as np
W=os.path.dirname(__file__);o=bpy.data.objects['Valkur_low'];m=o.data;im=bpy.data.images['valkur_bake'];w,h=im.size;pix=np.array(im.pixels[:],dtype=np.float32).reshape(h,w,4);uv=m.uv_layers.active
def col(p):
 u=np.mean([uv.data[i].uv[:] for i in p.loop_indices],axis=0);return pix[int(u[1]*h)%h,int(u[0]*w)%w,:3].tolist()
rows=[]
for p in m.polygons:
 x,y,z=p.center
 if 25<x<29 and 87<z<103 and -.5*x+.9*y<10:rows.append({'face':p.index,'pos':list(p.center),'rgb':col(p)})
open(os.path.join(W,'hand-color-samples.json'),'w').write(json.dumps(rows,indent=2))
print('IMAGE',im.name,im.colorspace_settings.name,'SAMPLES',len(rows),flush=True)
for label,cond in [('inner',lambda r:r['pos'][0]<27),('outer',lambda r:r['pos'][0]>=27)]:
 a=np.array([r['rgb'] for r in rows if cond(r)]);print(label,np.quantile(a,[0,.25,.5,.75,1],axis=0).tolist(),flush=True)
