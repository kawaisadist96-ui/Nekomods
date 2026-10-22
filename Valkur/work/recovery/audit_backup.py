import bpy,json,os
from collections import Counter
from mathutils import Vector
W=os.path.join(os.path.dirname(bpy.data.filepath),'recovery')
o=bpy.data.objects['Valkur_low']; a=next(m.object for m in o.modifiers if m.type=='ARMATURE')
report={'file':bpy.data.filepath,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'groups':[g.name for g in o.vertex_groups],'matrix':[list(r) for r in o.matrix_world],'images':[(i.name,list(i.size),i.filepath,bool(i.packed_file)) for i in bpy.data.images]}
libpath=os.path.join(os.path.dirname(bpy.data.filepath),'valkur-gap-cut.blend')
with bpy.data.libraries.load(libpath,link=False) as (src,dst): dst.meshes=['valkurShape'] if 'valkurShape' in src.meshes else [src.meshes[0]]
cut=dst.meshes[0]
def key(p,me): return tuple(sorted(tuple(round(v,4) for v in me.vertices[i].co) for i in p.vertices))
keys={key(p,cut) for p in cut.polygons}
missing=[p for p in o.data.polygons if key(p,o.data) not in keys]
report['cut_faces']=len(cut.polygons);report['missing_faces']=len(missing)
report['missing_bounds']=[ [min(o.data.vertices[i].co[j] for p in missing for i in p.vertices),max(o.data.vertices[i].co[j] for p in missing for i in p.vertices)] for j in range(3)]
report['missing_dominant']=Counter(o.vertex_groups[max(o.data.vertices[i].groups,key=lambda g:g.weight).group].name for p in missing for i in p.vertices if o.data.vertices[i].groups)
print(json.dumps(report,indent=2),flush=True)
open(os.path.join(W,'initial-audit.json'),'w').write(json.dumps(report,indent=2))
# shared preview
for im in bpy.data.images:
 if im.name=='valkur_bake': im.filepath=os.path.join(os.path.dirname(bpy.data.filepath),'valkur-bake.png'); im.reload()
 if im.name=='valkur_normal_bake': im.filepath=os.path.join(os.path.dirname(bpy.data.filepath),'valkur-normal-bake.png'); im.reload()
for x in bpy.context.scene.objects: x.hide_render=x!=o
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=700;s.render.resolution_y=850;s.render.resolution_percentage=100
s.world.color=(0.25,0.25,0.25)
ld=bpy.data.lights.new('audit-key','AREA');ld.energy=150000;ld.shape='DISK';ld.size=140
l=bpy.data.objects.new('audit-key',ld);s.collection.objects.link(l);l.location=(70,-150,250);l.rotation_euler=((Vector((0,0,95))-l.location).to_track_quat('-Z','Y').to_euler())
cam=bpy.data.objects.new('audit-camera',bpy.data.cameras.new('audit-camera'));s.collection.objects.link(cam);s.camera=cam
cam.location=(130,-250,160);cam.rotation_euler=((Vector((0,0,95))-cam.location).to_track_quat('-Z','Y').to_euler());cam.data.type='ORTHO';cam.data.ortho_scale=215
for label,action,frame in [('rest',None,1),('idle','VALKUR_TEST_idle',40),('walk','VALKUR_TEST_walk',20)]:
 a.data.pose_position='REST' if action is None else 'POSE'
 if action:
  ac=bpy.data.actions[action];a.animation_data.action=ac;a.animation_data.action_slot=ac.slots[0]
 s.frame_set(frame);bpy.context.view_layer.update();s.render.filepath=os.path.join(W,'backup-'+label+'.png');bpy.ops.render.render(write_still=True)
