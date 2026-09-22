"""Add low scattered gravel to the saved nonblocking River bodies only.
Run in Blender from the code checkout; height grid, terrain and masks are read-only.
"""
from pathlib import Path
import bpy, json, math, random, hashlib
OUT=Path.cwd()/'assets/pilots/map-rebuild-spike';PACK=OUT/'landmarks/river';SOURCE=OUT/'sources/river-fidelity-1'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'landmarks-input.blend'));bpy.context.preferences.filepaths.save_version=0
for image in bpy.data.images:
    if image.source=='FILE':image.filepath=str(PACK/'river-landmarks-atlas.png');image.pack()
grid=json.loads((OUT/'river-fallback-height-grid.json').read_text())['heights']
def height(x,z):
    x=max(0,min(127.99999,x+64));z=max(0,min(127.99999,z+64));ix=math.floor(x);iz=math.floor(z);u=x-ix;v=z-iz
    a,b=grid[iz*129+ix:iz*129+ix+2];c,d=grid[(iz+1)*129+ix:(iz+1)*129+ix+2]
    return a+(b-a)*u+(d-b)*v if u>=v else a+(d-c)*u+(c-a)*v
c=json.loads((SOURCE/'pack-input.json').read_text());records=[];rng=random.Random(20260922)
for mount in c['mounts']:
    identifier=mount['id'];body=bpy.data.objects[identifier];mx,_,mz=mount['position'];material=body.data.materials[0];parts=[]
    def mesh(label,verts,faces):
        data=bpy.data.meshes.new(label);data.from_pydata(verts,[],faces);data.update();obj=bpy.data.objects.new(label,data);bpy.context.collection.objects.link(obj);data.materials.append(material)
        uv=data.uv_layers.new(name=body.data.uv_layers.active.name)
        for face in data.polygons:
            axes=[k for k in range(3) if k!=max(range(3),key=lambda k:abs(face.normal[k]))]
            for li in face.loop_indices:
                co=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=((3+.1+.8*((co[axes[0]]*.22)%1))/4,(1+.1+.8*((co[axes[1]]*.22)%1))/4)
        parts.append(obj);return obj
    def pebble(x,z,index,shore=False):
        radius=rng.uniform(.25,.50) if shore else rng.uniform(.19,.40);rise=rng.uniform(.09,.22)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x-mx,mz-z,height(x,z)-height(mx,mz)+rise*.2));obj=bpy.context.object;obj.scale=(radius,radius*rng.uniform(.65,1.3),rise);obj.rotation_euler.z=rng.random()*math.tau
        for v in obj.data.vertices:v.co *= rng.uniform(.91,1.08)
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);verts=[tuple(v.co) for v in obj.data.vertices];faces=[tuple(f.vertices) for f in obj.data.polygons];bpy.data.objects.remove(obj,do_unlink=True);mesh(identifier+'.pebble'+str(index),verts,faces)
    if identifier!='ford-wet-stones':
        sign=1 if mz>0 else -1;start,end=(-62,-3.3) if mx<0 else (3.3,62)
        for i in range(38):
            x=start+(end-start)*(i+.5)/38;z=sign*(6.9+rng.uniform(-.85,.85)+math.sin(x*.63)*.3);pebble(x,z,i,True)
        expected=3000
    else:
        for i in range(20):pebble((-1 if i%2 else 1)*rng.uniform(1.65,2.3),rng.uniform(-4.8,4.8),i)
        expected=2000
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [body,*parts]:obj.select_set(True)
    bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
    for face in body.data.polygons:face.material_index=0
    while len(body.data.materials)>1:body.data.materials.pop(index=len(body.data.materials)-1)
    triangles=sum(len(face.vertices)-2 for face in body.data.polygons);assert triangles==expected,(identifier,triangles)
    verts=[tuple(v.co) for v in body.data.vertices];assert all(abs(x+mx)>1.1 for x,z,y in verts),identifier
    glb=PACK/(identifier+'.glb');bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
    a=c['assets'][identifier];a.update(triangles=triangles,bounds={'min':[min(v[i] for v in verts) for i in range(3)],'max':[max(v[i] for v in verts) for i in range(3)]},sha256=hashlib.sha256(glb.read_bytes()).hexdigest())
    a['sources']+=['assets/pilots/map-rebuild-spike/sources/river-fidelity-1/landmarks-input.blend'];records.append({'id':identifier,'triangles':triangles,'mountUnchanged':mount['position'],'gravelOnly':True})
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'river-landmarks.blend'))
c['blend']['sha256']=hashlib.sha256((PACK/'river-landmarks.blend').read_bytes()).hexdigest();c['recipe']='fidelity_river_shores.py';c['fidelity']='Low gravel follows the immutable height grid; existing stones retained; no sampled heights or collision added.'
(PACK/'river-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
p=OUT/'landmarks/landmark-source-ledger.json';ledger=json.loads(p.read_text());ledger['packs']['river']={k:{f:v[f] for f in ['sourceTier','sources','asset']} for k,v in c['assets'].items()};p.write_text(json.dumps(ledger,indent=2)+'\n')
(SOURCE/'geometry-proof.json').write_text(json.dumps(records,indent=2)+'\n');print('RIVER FIDELITY',records)
