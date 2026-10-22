import bpy,os
from mathutils import Vector
W=os.path.dirname(__file__);s=bpy.context.scene;o=bpy.data.objects['Valkur_low'];a=next(m.object for m in o.modifiers if m.type=='ARMATURE');a.data.pose_position='REST';s.render.resolution_x=650;s.render.resolution_y=850
cam=s.camera;cam.data.ortho_scale=210
for label,loc in [('back',(100,250,160)),('side',(-240,-80,150)),('front',(0,-280,140))]:
 cam.location=loc;cam.rotation_euler=((Vector((0,0,95))-cam.location).to_track_quat('-Z','Y').to_euler());s.render.filepath=os.path.join(W,'review-'+label+'.png');bpy.ops.render.render(write_still=True)
