import bpy,sys,os,json,inspect
W=os.path.dirname(__file__);sys.path.insert(0,W)
from io_pdx_mesh.pdx_blender import blender_import_export as io
# Compare accelerated lookup with unmodified source on a small UV mapped cube.
ns=dict(io.__dict__);exec(compile(open(os.path.join(W,'io_pdx_mesh/pdx_blender/blender_import_export.original.txt')).read(),'reference','exec'),ns)
bpy.ops.mesh.primitive_cube_add();test=bpy.context.object
fast=io.get_mesh_info(test,0);reference=ns['get_mesh_info'](test,0)
assert fast==reference,'Mesh exporter output mismatch'
bpy.data.objects.remove(test,do_unlink=True)
o=bpy.data.objects['Valkur_low'];a=next(m.object for m in o.modifiers if m.type=='ARMATURE');a.data.pose_position='REST'
o.data.name='valkurShape'
mat=o.data.materials[0];mat['shader']='standard';mat['diff']='valkur_diffuse.dds';mat['n']='valkur_normal.dds';mat['spec']='valkur_properties.dds'
for x in bpy.context.view_layer.objects:x.select_set(False)
o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
staging=os.path.join(W,'export');os.makedirs(staging,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W,'valkur-restored-final.blend'),compress=True)
io.export_meshfile(os.path.join(staging,'valkur.mesh'),exp_mesh=True,exp_skel=True,exp_locs=False,exp_selected=True)
print('EXPORT_OK',os.path.getsize(os.path.join(staging,'valkur.mesh')),flush=True)
