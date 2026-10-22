import bpy,sys,os,json,numpy as np
W=os.path.dirname(__file__);sys.path.insert(0,W)
from io_pdx_mesh.pdx_blender import blender_import_export as io
from io_pdx_mesh import pdx_data
out=os.path.join(W,'export','valkur.mesh')
o=bpy.data.objects['Valkur_low'];me=o.data;a=next(m.object for m in o.modifiers if m.type=='ARMATURE');a.data.pose_position='REST'
meshinfo,ids=io.get_mesh_info(o,0)
tree=pdx_data.read_meshfile(out);node=tree.find('object')[0];m=node.find('mesh');sk=node.find('skeleton')
report={'file':out,'source_faces':len(me.polygons),'export_vertices':len(m.attrib['p'])//3,'export_triangles':len(m.attrib['tri'])//3,'export_bones':len(sk)}
report['geometry_matches_export_input']=all(np.allclose(m.attrib[k],meshinfo[k],rtol=0,atol=1e-5) for k in ['p','n','ta','u0']) and m.attrib['tri']==meshinfo['tri']
old_path=os.path.join(W,'mod-before-restoration/gfx/models/units/infantry/valkur/valkur.mesh')
oldtree=pdx_data.read_meshfile(old_path);oldsk=oldtree.find('object')[0].find('skeleton')
report['skeleton_matches_previous_game_mesh']= [(b.tag,b.attrib) for b in sk]==[(b.tag,b.attrib) for b in oldsk]
skin=m.find('skin');ws=np.array(skin.attrib['w']).reshape(-1,4);report['max_weight_sum_error']=float(np.max(abs(ws.sum(axis=1)-1)))
expected_skin=io.get_mesh_skin_info(o,ids)
report['skin_matches_export_input']=skin.attrib['ix']==expected_skin['ix'] and np.allclose(skin.attrib['w'],expected_skin['w'],rtol=0,atol=1e-7)
expected=np.array([v.co[:] for v in me.vertices])
for obj in list(bpy.data.objects): bpy.data.objects.remove(obj,do_unlink=True)
old_objects=set(bpy.data.objects);io.import_meshfile(out,imp_mesh=True,imp_skel=True,imp_locs=False)
newobjects=set(bpy.data.objects)-old_objects;newmesh=next(x for x in newobjects if x.type=='MESH');newarm=next(x for x in newobjects if x.type=='ARMATURE')
report['reimport_vertices']=len(newmesh.data.vertices);report['reimport_faces']=len(newmesh.data.polygons);report['reimport_bones']=len(newarm.data.bones)
ix=np.array(skin.attrib['ix']).reshape(-1,4);bone_names=[bone.tag for bone in sk];mismatches=0
for i,v in enumerate(newmesh.data.vertices):
 want={bone_names[int(b)]:float(w) for b,w in zip(ix[i],ws[i]) if b>=0 and w>0}
 got={newmesh.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}
 if set(want)!=set(got) or any(abs(want[k]-got[k])>1e-6 for k in want):mismatches+=1
report['reimport_weight_mismatches']=mismatches
actual=np.array([v.co[:] for v in newmesh.data.vertices]);report['bounds_max_difference']=float(np.max(abs(np.array([expected.min(axis=0),expected.max(axis=0)])-np.array([actual.min(axis=0),actual.max(axis=0)]))))
assert report['geometry_matches_export_input'];assert report['skeleton_matches_previous_game_mesh'];assert report['bounds_max_difference']<1e-4
assert report['skin_matches_export_input'] and report['reimport_weight_mismatches']==0
open(os.path.join(W,'roundtrip.json'),'w').write(json.dumps(report,indent=2));print('ROUNDTRIP',report,flush=True)
