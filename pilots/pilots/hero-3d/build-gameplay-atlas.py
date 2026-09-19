"""Idempotent complete UV/material rebuild; preserves HeroMesh silhouette, weights and walk.
Blender --background hero-3d.blend --python build-gameplay-atlas.py
Atlas is native image_gen art; deterministic 1024 resample is done before this script.
"""
import bpy, bmesh, json, math
from pathlib import Path
root = Path(bpy.data.filepath).parent
obj = bpy.data.objects['HeroMesh']; mesh = obj.data
bpy.context.scene.frame_set(0)
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
bpy.context.view_layer.objects.active = obj
# Preserve the semantic identity of each disconnected authored part while welding only
# its own float-noise duplicates. Global welding would join touching clothing parts.
labels=mesh.attributes.get('hero_uv_part')
if not labels:
    adj=[set() for _ in mesh.vertices]
    for edge in mesh.edges:
        a,b=edge.vertices; adj[a].add(b); adj[b].add(a)
    seen=set(); components=[]
    for vertex in mesh.vertices:
        if vertex.index in seen: continue
        todo=[vertex.index]; ids=[]; seen.add(vertex.index)
        while todo:
            i=todo.pop(); ids.append(i)
            for j in adj[i]:
                if j not in seen: seen.add(j); todo.append(j)
        components.append(ids)
    assert len(components)==50, 'Review part assignment if topology changes'
    labels=mesh.attributes.new(name='hero_uv_part',type='INT',domain='POINT')
    for part,ids in enumerate(components):
        for i in ids: labels.data[i].value=part
obj['source_vertex_count']=obj.get('source_vertex_count',len(mesh.vertices))
bm=bmesh.new(); bm.from_mesh(mesh); layer=bm.verts.layers.int['hero_uv_part']
for part in range(50):
    verts=[v for v in bm.verts if v[layer]==part]
    bmesh.ops.remove_doubles(bm,verts=verts,dist=1e-7)
    edges=[edge for edge in bm.edges if all(v[layer]==part for v in edge.verts)]
    bmesh.ops.dissolve_degenerate(bm,edges=edges,dist=1e-7)
bm.to_mesh(mesh); bm.free(); mesh.update()
labels=mesh.attributes['hero_uv_part']
components=[[i for i,v in enumerate(labels.data) if v.value==part] for part in range(50)]
assert all(components), 'A semantic part disappeared during precision cleanup'
assert all(sum(g.weight for g in vertex.groups)>0 for vertex in mesh.vertices), 'Unweighted skin vertex'
# UV rectangles, bottom-left origin; 8-pixel safe inset from all painted tile boundaries.
rects = {
    'leather':(.5,.75,1,1), 'linen':(.5,.5,1,.75),
    'hair':(0,.25,.25,.5), 'coat':(.25,.25,.5,.5),
    'trousers':(.5,.25,.75,.5), 'boots':(.75,.25,1,.5),
    'skin':(0,0,.25,.25), 'brass':(.25,0,.5,.25),
    'teal':(.5,0,.75,.25), 'iron':(.75,0,1,.25),
}
parts = ['trousers','trousers','boots','leather','trousers','trousers','boots','leather',
 'trousers','coat','linen','coat','coat','leather','leather','leather','brass',
 'coat','linen','leather','skin','coat','linen','leather','skin','skin','hair','skin',
 'skin','iron','iron','leather', 'hair','hair','hair','hair','hair','hair',
 'leather','leather','boots','leather','leather','leather','iron','brass','iron','brass','teal','brass']
while mesh.uv_layers: mesh.uv_layers.remove(mesh.uv_layers[0])
mesh.uv_layers.new(name='Gameplay1024_Complete')
uv=mesh.uv_layers.active.data
part_report=[]
for component, (ids, slot) in enumerate(zip(components,parts)):
    members=set(ids)
    faces=[face for face in mesh.polygons if face.vertices[0] in members]
    bpy.context.tool_settings.mesh_select_mode=(False,False,True)
    for v in mesh.vertices: v.select=False
    for edge in mesh.edges: edge.select=False
    for face in mesh.polygons: face.select=face.vertices[0] in members
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.035, area_weight=.5, correct_aspect=True, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh=obj.data; uv=mesh.uv_layers.active.data
    faces=[face for face in mesh.polygons if face.vertices[0] in members]
    x0,y0,x1,y1=rects[slot]; pad=8/1024
    for face in faces:
        for loop in face.loop_indices:
            coord=uv[loop].uv.copy()
            uv[loop].uv=(x0+pad+coord.x*(x1-x0-2*pad), y0+pad+coord.y*(y1-y0-2*pad))
    part_report.append({'part':component,'slot':slot,'polygons':len(faces),'vertices':len(ids)})
# Deliberately keep face/side/back skin clean. The authored eyes, nose and mouth supply
# readable features; no portrait projection is stretched across head/arms/rear surfaces.
image=bpy.data.images.load(str(root/'hero-painted-atlas.png'),check_existing=False)
image.name='Hero_Gameplay_Diffuse_1024'; image.colorspace_settings.name='sRGB'; image.pack()
assert tuple(image.size)==(1024,1024)
mat=bpy.data.materials.get('Hero_Gameplay_Diffuse') or bpy.data.materials.new('Hero_Gameplay_Diffuse')
mat.use_nodes=True; nodes=mat.node_tree.nodes; nodes.clear()
output=nodes.new('ShaderNodeOutputMaterial'); bsdf=nodes.new('ShaderNodeBsdfPrincipled'); tex=nodes.new('ShaderNodeTexImage'); tex.image=image
bsdf.inputs['Base Color'].default_value=(1,1,1,1)
bsdf.inputs['Roughness'].default_value=.83; bsdf.inputs['Metallic'].default_value=0
bsdf.inputs['Emission Color'].default_value=(0,0,0,1); bsdf.inputs['Emission Strength'].default_value=0
mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']); mat.node_tree.links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
for obsolete in list(bpy.data.images):
    if obsolete!=image and obsolete.name.startswith('Hero_Gameplay_Diffuse_1024') and obsolete.users==0: bpy.data.images.remove(obsolete)
image.name='Hero_Gameplay_Diffuse_1024'
mat.diffuse_color=(1,1,1,1); mesh.materials.clear(); mesh.materials.append(mat)
for face in mesh.polygons: face.material_index=0
def uv_area(tri):
    a,b,c=[uv[i].uv for i in tri.loops]
    return abs((b-a).cross(c-a))*.5
mesh.calc_loop_triangles()
# Prove every nondegenerate geometric triangle has a nondegenerate UV triangle.
bad=[]; areas=[]
for tri in mesh.loop_triangles:
    if tri.area>1e-10:
        area=uv_area(tri); areas.append(area)
        if area<1e-12: bad.append(tri.index)
assert not bad, f'Collapsed UV triangles: {bad}'
# Catch selection leakage: a later unwrap must never overwrite another part's tile.
for part,ids in enumerate(components):
    members=set(ids); x0,y0,x1,y1=rects[parts[part]]
    values=[uv[loop].uv for face in mesh.polygons if face.vertices[0] in members for loop in face.loop_indices]
    bounds=[min(v.x for v in values),min(v.y for v in values),max(v.x for v in values),max(v.y for v in values)]
    assert all((x0+7/1024 <= v.x <= x1-7/1024 and y0+7/1024 <= v.y <= y1-7/1024) for v in values), f'UV tile leakage: part {part} {bounds}'
    part_report[part]['uv_bounds']=bounds
obj['uv_contract']='All 50 authored components unwrapped, including side/back/caps; safe material-tile reuse.'
obj['atlas_pixels']=1024; obj['pilot_only']=True
# Ground the existing walk without changing its horizontal stride or joint choreography.
# Its original soles floated up to 6.8 cm and penetrated 3 cm at the comparison scale.
# Retiming to eight subframes preserves the 0.5 s duration while glTF's integer-frame
# sampling keeps the contact correction between the eight authored poses.
rig=bpy.data.objects['HeroRig']; action=rig.animation_data.action
curves=lambda:[curve for layer in action.layers for strip in layer.strips for bag in strip.channelbags for curve in bag.fcurves]
if not rig.get('grounded_walk_v1'):
    assert tuple(action.frame_range)==(0.0,8.0) and bpy.context.scene.render.fps==16, 'Review changed walk timing before retiming'
    for curve in curves():
        for key in curve.keyframe_points:
            key.co.x*=8; key.handle_left.x*=8; key.handle_right.x*=8
    bpy.context.scene.render.fps*=8
    rig['grounded_walk_v1']=True
for layer in action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in list(bag.fcurves):
                if curve.data_path=='location' and curve.array_index==2: bag.fcurves.remove(curve)
rig.location.z=0
bpy.context.scene.frame_start=0; bpy.context.scene.frame_end=64
boots=[i for i,v in enumerate(mesh.attributes['hero_uv_part'].data) if v.value in (2,6)]
def lowest_boot():
    graph=bpy.context.evaluated_depsgraph_get(); graph.update()
    evaluated=obj.evaluated_get(graph); posed=evaluated.to_mesh()
    value=min((evaluated.matrix_world@posed.vertices[i].co).z for i in boots)
    evaluated.to_mesh_clear(); return value
bpy.context.scene.frame_set(0); floor=lowest_boot()
rig.location.z=.1; bpy.context.view_layer.update()
assert abs(lowest_boot()-floor-.1)<1e-5, 'Rig translation does not move the skinned soles'
rig.location.z=0
corrections=[]
for frame in range(65):
    bpy.context.scene.frame_set(frame); corrections.append(.003/ .83-lowest_boot())
for frame,value in enumerate(corrections):
    bpy.context.scene.frame_set(frame); rig.location.z=value
    rig.keyframe_insert(data_path='location',index=2,frame=frame,group='Ground contact')
for curve in curves():
    if curve.data_path=='location' and curve.array_index==2:
        for key in curve.keyframe_points: key.interpolation='LINEAR'
bpy.context.scene.frame_set(0)
# Drop only obsolete material/image datablocks that no scene object uses.
# Packed reference planes are retained for editable provenance, excluded by named export.
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'hero-3d.blend'))
bpy.ops.object.select_all(action='DESELECT')
for name in ['HeroMesh','HeroRig']: bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str(root/'hero-3d.glb'), export_format='GLB',use_selection=True,export_apply=False,export_extras=True,export_cameras=False,export_lights=False,export_animations=True,export_materials='EXPORT')
report={'source_vertices_blend':int(obj['source_vertex_count']),'vertices_blend':len(mesh.vertices),'weld_tolerance':1e-7,'polygons':len(mesh.polygons),'triangles':len(mesh.loop_triangles),'components':part_report,'collapsed_uv_triangles':bad,'minimum_uv_triangle_area':min(areas),'atlas':[1024,1024],'rgba8_mip_MiB':1024*1024*4*4/3/1024**2,'material':'Principled baseColor, roughness .83, metalness 0, emission 0','animation_frames':[0,64],'animation_fps':bpy.context.scene.render.fps,'ground_correction_range':[min(corrections),max(corrections)],'runtime':'pilot only'}
(root/'uv-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('HERO_AUDIT',json.dumps(report))
