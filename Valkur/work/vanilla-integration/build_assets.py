import os,re,json
W=os.path.dirname(__file__);OUT=os.path.join(W,'staged/gfx/models/units/infantry/valkur')
src=open(r'C:\Game\Crusader Kings 3\game\gfx\models\units\infantry\unit_fp1_infantry_02\unit_fp1_infantry_02.asset',encoding='utf-8-sig').read()
def block(text,start):
 first=text.index('{',start);depth=0;quote=False;comment=False
 for i in range(first,len(text)):
  c=text[i]
  if c=='\n':comment=False
  if comment:continue
  if c=='"':quote=not quote
  if not quote and c=='#':comment=True;continue
  if quote:continue
  if c=='{':depth+=1
  if c=='}':
   depth-=1
   if depth==0:return text[start:i+1],i+1
 raise ValueError('Unclosed block')
start=re.search(r'entity\s*=\s*\{\s*name\s*=\s*"unit_fp1_infantry_02_entity"',src).start();entity,_=block(src,start)
entity=entity.replace('unit_fp1_infantry_02_entity','valkur_entity').replace('unit_fp1_infantry_02_mesh','valkur_mesh').replace('unit_northern_pagan_infantry_02_weapon_entity','valkur_sword_entity').replace('unit_fp1_infantry_02_shield_entity','valkur_shield_entity')
states=[];replacements=[]
for match in re.finditer(r'\bstate\s*=\s*\{',entity):
 st,end=block(entity,match.start());name=re.search(r'\bname\s*=\s*"([^"]+)"',st).group(1)
 st=re.sub(r'node\s*=\s*back_node_1\s+entity\s*=\s*"valkur_shield_entity"','node = back_node_1 entity = "valkur_shield_back_entity"',st)
 st=re.sub(r'remove_attachment\s*=\s*weapon','node = Left_hip_node_1 entity = "valkur_sword_stowed_entity" attachment_id = weapon',st)
 # Named attachment lets the timed draw event replace the stowed weapon.
 st=re.sub(r'entity\s*=\s*"valkur_sword_entity"(?!\s+attachment_id)', 'entity = "valkur_sword_entity" attachment_id = weapon',st)
 if not re.search(r'start_event\s*=\s*\{[^}]*valkur_sword',st):
  st=st[:-1]+'\n\t\tstart_event = { node = Left_hip_node_1 entity = "valkur_sword_stowed_entity" attachment_id = weapon }\n\t}'
 if name.startswith('gather'):
  st=st[:-1]+'\n\t\tstart_event = { node = back_node_1 entity = "valkur_shield_back_entity" attachment_id = shield }\n\t}'
 # Shield impact particle sub-states are not body animation states.
 st=re.sub(r'(entity\s*=\s*"valkur_shield(?:_back)?_entity")\s+state\s*=\s*\w+',r'\1',st)
 replacements.append((match.start(),end,st));states.append(name)
for start,end,st in reversed(replacements):entity=entity[:start]+st+entity[end:]
specs=json.load(open(os.path.join(W,'animation-manifest.json')))
def settings(shape):return '\n\tmeshsettings = {\n\t\tname = "'+shape+'"\n\t\tindex = 0\n\t\ttexture_diffuse = "valkur_diffuse.dds"\n\t\ttexture_normal = "valkur_normal.dds"\n\t\ttexture_specular = "valkur_properties.dds"\n\t\tshader = "standard"\n\t\tshader_file = "gfx/FX/pdxmesh.shader"\n\t}\n'
text='pdxmesh = {\n\tname = "valkur_mesh"\n\tfile = "valkur.mesh"\n\tscale = 0.06\n'
for a in specs:text+='\tanimation = { id = "'+a['id']+'" type = "vanilla_'+a['id']+'.anim" }\n'
text+=settings('valkurShape')+'}\n\n'+entity+'\n'
for name,shape in [('shield','Valkur_shieldShape'),('shield_back','Valkur_shield_backShape'),('sword','Valkur_swordShape'),('sword_stowed','Valkur_sword_stowedShape')]:
 text+='\npdxmesh = {\n\tname = "valkur_'+name+'_mesh"\n\tfile = "valkur_'+name+'.mesh"\n'+settings(shape)+'}\n'
 text+='entity = { name = "valkur_'+name+'_entity" pdxmesh = "valkur_'+name+'_mesh" scale = 0.06 }\n'
ids={x['id'] for x in specs};used=set(re.findall(r'\banimation\s*=\s*"([^"]+)"',entity));assert used<=ids
nexts=set(re.findall(r'next_state\s*=\s*(\w+)',entity));assert nexts<=set(states),(nexts-set(states))
open(os.path.join(OUT,'valkur.asset'),'w',encoding='utf-8').write(text)
report={'vanilla_body_states':states,'state_count':len(states),'animation_count':len(specs),'animation_ids_resolved':True,'next_states_resolved':True,'equipment_entities':['valkur_shield_entity','valkur_shield_back_entity','valkur_sword_entity','valkur_sword_stowed_entity','unit_fp1_horn_entity'],'source_entity':'unit_fp1_infantry_02_entity'}
open(os.path.join(W,'asset-validation.json'),'w').write(json.dumps(report,indent=2));print(json.dumps(report))
