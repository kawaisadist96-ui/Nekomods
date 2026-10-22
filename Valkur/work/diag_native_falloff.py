import json
import bpy
from mathutils import Vector

OUT = r"C:\Users\Administrator\Documents\ChatGPT\Neko\Valkur-Cursor-Devir\work\native_thigh_falloff.json"
native = bpy.data.objects["unit_fp1_infantry_01_LOD_0"]
arm = bpy.data.objects["io_pdx_rig"]
me = native.data
HIP = "Character1_Hips"
LEG = "Character1_LeftUpLeg"
hip = arm.matrix_world @ arm.data.bones[HIP].head_local
knee = arm.matrix_world @ arm.data.bones["Character1_LeftLeg"].head_local
axis = knee - hip
length = axis.length
axis_n = axis.normalized()

rows = []
for v in me.vertices:
    w = {native.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0.001}
    if HIP not in w and LEG not in w:
        continue
    co = native.matrix_world @ v.co
    t = (co - hip).dot(axis_n) / length
    if t < -0.15 or t > 1.15:
        continue
    # keep the left thigh, not the whole body: close to the bone segment
    closest = hip + axis_n * max(0.0, min(length, (co - hip).dot(axis_n)))
    if (co - closest).length > 0.18 * length and (co - closest).length > 8:
        continue
    rows.append({
        "t": round(t, 3),
        "hip": round(w.get(HIP, 0.0), 3),
        "leg": round(w.get(LEG, 0.0), 3),
        "other": sorted([k for k in w if k not in {HIP, LEG}])[:4],
    })

buckets = {}
for row in rows:
    key = round(row["t"] * 10) / 10
    buckets.setdefault(key, []).append(row)
summary = []
for key in sorted(buckets):
    items = buckets[key]
    summary.append({
        "t": key,
        "count": len(items),
        "hip_avg": round(sum(i["hip"] for i in items) / len(items), 3),
        "leg_avg": round(sum(i["leg"] for i in items) / len(items), 3),
    })
report = {
    "hip_cm": [round(c, 3) for c in hip],
    "knee_cm": [round(c, 3) for c in knee],
    "bone_length": round(length, 3),
    "samples": len(rows),
    "by_t": summary,
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print("samples", len(rows), "buckets", len(summary))
