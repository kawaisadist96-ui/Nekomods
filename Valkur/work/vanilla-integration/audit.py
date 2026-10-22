import bpy,sys,os,json,re
from mathutils import Matrix
W=os.path.dirname(__file__);sys.path.insert(0,os.path.join(os.path.dirname(W),'recovery'))
from io_pdx_mesh import pdx_data
from io_pdx_mesh.pdx_blender import blender_import_export as io
G=r'C:\Game\Crusader Kings 3\game\gfx\models\units\infantry'
asset=open(os.path.join(G,'unit_fp1_infantry_02/unit_fp1_infantry_02.asset')).read()
native=json.load(open(os.path.join(os.path.dirname(os.path.dirname(W)),'reports/native-bones.json')))
a=next(m.object for m in bpy.data.objects['Valkur_low'].modifiers if m.type=='ARMATURE')
comparison=[]
for n in native:
 b=a.data.bones[n['name']];nr=Matrix(n['matrix_local']);fr=b.matrix_local
 comparison.append({'name':b.name,'native':n['head'],'fitted':list(fr.translation),'rotation_delta_degrees':nr.to_quaternion().rotation_difference(fr.to_quaternion()).angle*57.2957795})
tree=pdx_data.read_meshfile(os.path.join(G,'unit_fp1_infantry_02/unit_fp1_infantry_02.mesh'))
locs=tree.find('locator')
anims=[]
for aid,path in re.findall(r'animation\s*=\s*\{\s*id\s*=\s*"([^"]+)"\s*type\s*=\s*"([^"]+)"',asset):
 p=os.path.normpath(os.path.join(G,'unit_fp1_infantry_02',path));t=pdx_data.read_meshfile(p);info=t.find('info')
 anims.append({'id':aid,'source':p,'fps':info.attrib['fps'][0],'samples':info.attrib['sa'][0],'bones':len(info),'missing':[b.tag for b in info if io.clean_imported_name(b.tag) not in a.data.bones]})
report={'bones':comparison,'locators':[(x.tag,x.attrib) for x in locs] if locs is not None else [],'animations':anims,'mesh_objects':[(x.tag,len(x.findall('mesh'))) for x in tree.find('object')]}
report['root_nodes']=[x.tag for x in tree]
open(os.path.join(W,'audit.json'),'w').write(json.dumps(report,indent=2));print('ANIMS',len(anims),'ROOT',report['root_nodes'],'MISSING',sum(len(x['missing']) for x in anims),flush=True)
