from pathlib import Path
p=Path(__file__).parent/'io_pdx_mesh/pdx_blender/blender_import_export.py'
s=p.read_text();(p.parent/'blender_import_export.original.txt').write_text(s)
s=s.replace('export_verts = []\n    unique_verts = set()', 'export_verts = []\n    vertex_lookup = {}\n    unique_verts = set()')
s=s.replace('i = export_verts.index(new_vert)', 'i = vertex_lookup[new_vert]')
s=s.replace('unique_verts.add(new_vert)\n                export_verts.append(new_vert)', 'unique_verts.add(new_vert)\n                vertex_lookup.setdefault(new_vert, len(export_verts))\n                export_verts.append(new_vert)')
s=s.replace('vert_weights = {v: {} for v in vertex_ids}', 'vertex_id_set = set(vertex_ids)\n    vert_weights = {v: {} for v in vertex_ids}')
s=s.replace('if vert_id in vertex_ids:', 'if vert_id in vertex_id_set:')
p.write_text(s)
