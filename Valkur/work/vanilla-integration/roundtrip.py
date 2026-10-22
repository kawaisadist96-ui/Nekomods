import bpy,sys,os,json,numpy as np
from mathutils import Matrix
W=os.path.dirname(__file__);sys.path.insert(0,os.path.join(os.path.dirname(W),'recovery'))
from io_pdx_mesh.pdx_blender import blender_import_export as io
from io_pdx_mesh import pdx_data
OUT=os.path.join(W,'staged/gfx/models/units/infantry/valkur')
report=[];expected={}
pairs=[('Valkur_body','valkur'),('Valkur_shield','valkur_shield'),('Valkur_shield_back','valkur_shield_back'),('Valkur_sword','valkur_sword'),('Valkur_sword_stowed','valkur_sword_stowed')]
for arm in bpy.data.objects:
 if arm.type=='ARMATURE':arm.data.pose_position='REST'
for name,fn in pairs:
 o=bpy.data.objects[name];o.parent=None;o.matrix_world=Matrix.Identity(4);bpy.context.view_layer.update()
 info,ids=io.get_mesh_info(o,0);tree=pdx_data.read_meshfile(os.path.join(OUT,fn+'.mesh'));node=tree.find('object')[0];me=node.find('mesh')
 assert node.tag==('valkurShape' if fn=='valkur' else name+'Shape'),node.tag
 for k in ['p','n','ta','u0']:assert np.allclose(me.attrib[k],info[k],rtol=0,atol=1e-5),(fn,k)
 assert me.attrib['tri']==info['tri']
 coords=np.array([v.co[:] for v in o.data.vertices]);expected[fn]=(coords.min(axis=0),coords.max(axis=0))
 skin=me.find('skin')
 if skin is not None:
  want=io.get_mesh_skin_info(o,ids);assert skin.attrib['ix']==want['ix'];assert np.allclose(skin.attrib['w'],want['w'],rtol=0,atol=1e-7)
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
for name,fn in pairs:
 path=os.path.join(OUT,fn+'.mesh');old=set(bpy.data.objects);io.import_meshfile(path,imp_mesh=True,imp_skel=fn=='valkur',imp_locs=False)
 new=set(bpy.data.objects)-old;o=next(x for x in new if x.type=='MESH');co=np.array([v.co[:] for v in o.data.vertices]);err=float(abs(np.array([co.min(axis=0),co.max(axis=0)])-np.array(expected[fn])).max());assert err<1e-4,(fn,err)
 tree=pdx_data.read_meshfile(path);node=tree.find('object')[0];me=node.find('mesh');skin=me.find('skin');mismatches=0
 if skin is not None:
  bn=[b.tag for b in node.find('skeleton')];ix=np.array(skin.attrib['ix']).reshape(-1,4);ws=np.array(skin.attrib['w']).reshape(-1,4)
  for i,v in enumerate(o.data.vertices):
   want={bn[int(b)]:float(w) for b,w in zip(ix[i],ws[i]) if b>=0 and w>0};got={o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}
   if set(want)!=set(got) or any(abs(want[k]-got[k])>1e-6 for k in want):mismatches+=1
  assert mismatches==0
 assert len(o.data.polygons)==len(me.attrib['tri'])//3
 report.append({'file':fn+'.mesh','geometry_uv_normals_match':True,'bounds_max_error':err,'weight_mismatches':mismatches,'reimport_triangles':len(o.data.polygons)})
open(os.path.join(W,'roundtrip.json'),'w').write(json.dumps(report,indent=2));print('ROUNDTRIP_OK',len(report),flush=True)
