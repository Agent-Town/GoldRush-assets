"""Read-only skin/loop/foot-contact audit of the editable pilot's actual walk."""
import bpy,json,math
from pathlib import Path
obj=bpy.data.objects['HeroMesh']; labels=obj.data.attributes['hero_uv_part']
left=[i for i,v in enumerate(labels.data) if v.value==2]
right=[i for i,v in enumerate(labels.data) if v.value==6]
rows=[]; poses=[]
for frame in range(65):
    bpy.context.scene.frame_set(frame)
    graph=bpy.context.evaluated_depsgraph_get(); graph.update()
    evaluated=obj.evaluated_get(graph); mesh=evaluated.to_mesh()
    points=[evaluated.matrix_world@v.co for v in mesh.vertices]
    assert len(points)==len(obj.data.vertices)
    poses.append(points)
    bounds=lambda ids:{'ground_min':min(points[i].z for i in ids)*.83,'forward_center':sum(points[i].y for i in ids)/len(ids)*.83}
    rows.append({'phase':frame/64,'left':bounds(left),'right':bounds(right)})
    evaluated.to_mesh_clear()
loop=max((a-b).length*.83 for a,b in zip(poses[0],poses[-1]))
forward=[r['left']['forward_center']-r['right']['forward_center'] for r in rows[:-1]]
report={'frames':rows,'loop_max_vertex_distance':loop,'left_right_forward_range':[min(forward),max(forward)],'ground_min':min(min(r['left']['ground_min'],r['right']['ground_min']) for r in rows),'highest_lowest_foot':max(min(r['left']['ground_min'],r['right']['ground_min']) for r in rows),'scale':.83,'method':'Evaluated skinned mesh at resampled walk frames 0..64; labeled boot vertices; Blender Z is exported Three Y.'}
assert loop<1e-4, f'Walk loop seam: {loop}'
assert report['ground_min']>=-.001 and report['highest_lowest_foot']<.006, 'Sole grounding failed'
assert min(forward)<-.05 and max(forward)>.05, 'Feet do not alternate forward/back'
root=Path(bpy.data.filepath).parents[3]
(root/'artifacts/sol/open-findings/hero-foot-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('WALK_AUDIT',json.dumps(report))
