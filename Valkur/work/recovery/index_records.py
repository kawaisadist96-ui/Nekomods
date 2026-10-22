from pathlib import Path
import json,hashlib,ast
root=Path(__file__).resolve().parents[2];rows=[]
for p in sorted(root.rglob('*')):
 if not p.is_file() or 'recovery' in p.parts:continue
 if p.suffix.lower() not in {'.json','.py','.md','.html','.csv'}:continue
 s=p.read_text(encoding='utf-8-sig',errors='replace');row={'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
 if p.suffix=='.py':
  try:row['description']=ast.get_docstring(ast.parse(s))
  except Exception as exc:row['parse_error']=str(exc)
 if p.suffix=='.json':
  try:
   d=json.loads(s);row['keys']=list(d) if isinstance(d,dict) else 'list'
  except Exception as exc:row['parse_error']=str(exc)
 rows.append(row)
(root/'work/recovery/records-index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('Indexed',len(rows),'records')
print('Source GLB SHA256',hashlib.sha256((root/'source/valkur.glb').read_bytes()).hexdigest())
