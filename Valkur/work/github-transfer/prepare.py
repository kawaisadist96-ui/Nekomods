"""Prepare a complete Valkur project snapshot without modifying source assets."""
from pathlib import Path
import hashlib,json,shutil,os
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'.github-transfer'/'Valkur'
SKIP={'.git','.github-transfer','__pycache__','.pytest_cache'}
manifest=[]
for directory,dirs,files in os.walk(ROOT):
 dirs[:]=[d for d in dirs if d not in SKIP]
 for name in files:
  source=Path(directory)/name
  if source.suffix=='.pyc':continue
  relative=source.relative_to(ROOT)
  target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(source,target)
  digest=hashlib.file_digest(source.open('rb'),'sha256').hexdigest()
  assert digest==hashlib.file_digest(target.open('rb'),'sha256').hexdigest()
  manifest.append({'path':relative.as_posix(),'bytes':source.stat().st_size,'sha256':digest})
mod=Path(r'C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test')
for source in mod.rglob('*'):
 if not source.is_file():continue
 relative=Path('mod/valkur_units_test')/source.relative_to(mod);target=DEST/relative
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 manifest.append({'path':relative.as_posix(),'bytes':source.stat().st_size,'sha256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest()})
descriptor=mod.with_suffix('.mod').read_text(encoding='utf-8-sig')
descriptor='\n'.join('path="mod/valkur_units_test"' if line.startswith('path=') else line for line in descriptor.splitlines())+'\n'
(DEST/'mod/valkur_units_test.mod').write_text(descriptor,encoding='utf-8')
(DEST/'TRANSFER-MANIFEST.json').write_text(json.dumps({'files':manifest,'excluded':['Git metadata','Python bytecode/cache'],'source_files':len(manifest),'bytes':sum(f['bytes'] for f in manifest)},ensure_ascii=False,indent=2),encoding='utf-8')
print('PREPARED',len(manifest),'files',sum(f['bytes'] for f in manifest),'bytes',flush=True)
