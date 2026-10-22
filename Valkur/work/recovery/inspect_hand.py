import bpy,os
from mathutils import Vector
W=os.path.dirname(__file__);s=bpy.context.scene;o=bpy.data.objects['Valkur_low'];a=next(m.object for m in o.modifiers if m.type=='ARMATURE');a.data.pose_position='REST'
cam=s.camera;cam.data.ortho_scale=55;s.render.resolution_x=800;s.render.resolution_y=800
# World reference spheres, every 5 cm, in an unobstructed strip.
mat=bpy.data.materials.new('coordinate_reference');mat.diffuse_color=(0,1,0,1)
for z in range(85,141,5):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=.3,location=(15,-18,z));bpy.context.object.data.materials.append(mat)
for label,pos in [('front',(25,-200,112)),('back',(25,200,112)),('side',(-180,3,112))]:
 cam.location=pos;cam.rotation_euler=((Vector((25,3,112))-cam.location).to_track_quat('-Z','Y').to_euler());s.render.filepath=os.path.join(W,'hand-rest-'+label+'.png');bpy.ops.render.render(write_still=True)
