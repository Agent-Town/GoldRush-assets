"""Authored library scenery outside the preserved Archive floor. Run from code checkout."""
from pathlib import Path
import bpy, hashlib, json, math, random
OUT=Path.cwd()/'assets/pilots/map-rebuild-spike';SOURCE=OUT/'sources/archive-world-fidelity-1'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'panorama-input.blend'))
bpy.context.preferences.filepaths.save_version=0
panorama=next(o for o in bpy.data.objects if o.type=='MESH')
for image in bpy.data.images:
    if image.source=='FILE':image.filepath=str(OUT/'archive-world-panorama-atlas.png');image.pack()
stone=bpy.data.materials.new('ArchiveLibraryScenery');stone.use_nodes=True
bsdf=stone.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.86
texture=stone.node_tree.nodes.new('ShaderNodeTexImage');texture.image=bpy.data.images.load(str(OUT/'archive-world-terrain-atlas.png'),check_existing=True);texture.image.pack();texture.extension='REPEAT'
stone.node_tree.links.new(texture.outputs['Color'],bsdf.inputs['Base Color'])
# Four colonnaded library ruins: two real arched facade openings per ruin.
# 216 triangles each: six columns, two four-segment arches and six masonry boxes.
recess=stone.copy();recess.name='ArchiveLibraryRecess'
pieces=[];records=[]
for group in range(4):
    angle=math.tau*group/4;radius=72
    cx=math.cos(angle)*radius;cy=math.sin(angle)*radius;z0=-.65
    def build(label,verts,faces,mat=stone):
        verts=[(cx-x*math.sin(angle)+y*math.cos(angle),cy+x*math.cos(angle)+y*math.sin(angle),z) for x,y,z in verts]
        assert all(max(abs(x),abs(y))>64.01 for x,y,z in verts)
        mesh=bpy.data.meshes.new(f'Library{group}.{label}');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(mat)
        uv=mesh.uv_layers.new(name=panorama.data.uv_layers.active.name)
        for face in mesh.polygons:
            for li in face.loop_indices:
                co=mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv=(co.x/12,co.z/12) if abs(face.normal.z)<.5 else (co.x/12,co.y/12)
        pieces.append(obj)
    def box(label,x,y,z,sx,sy,sz,mat=stone):
        verts=[(x+vx*sx/2,y+vy*sy/2,z+vz*sz) for vx,vy,vz in [(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        build(label,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    box('plinth',0,0,z0,14.8,4.6,.65)
    box('back-wall',0,1.4,0,14,.6,5.2,recess)
    box('cornice',0,0,5.2,14.8,4.6,.5)
    box('frieze',0,-1.75,4.85,14.2,.6,.35)
    for sign in [-1,1]:box('end-wall'+str(sign),sign*6.85,0,0,.3,4,5.2)
    for n,x in enumerate([-6.6,-5.9,-.9,.9,5.9,6.6]):box('pier'+str(n),x,-1.8,0,.5,.65,3.0)
    for n,center in enumerate([-3.4,3.4]):
        verts=[]
        for y in [-2.15,-1.6]:
            for radius in [2.0,2.5]:
                for k in range(5):
                    theta=math.pi*k/4;verts.append((center+math.cos(theta)*radius,y,2.4+math.sin(theta)*radius))
        faces=[]
        for k in range(4):
            faces += [(k,k+1,k+6,k+5),(k+10,k+15,k+16,k+11),(k,k+10,k+11,k+1),(k+5,k+6,k+16,k+15)]
        faces += [(0,5,15,10),(4,14,19,9)]
        build('arch'+str(n),verts,faces)
    records.append({'group':group,'centerBlenderXY':[cx,cy],'triangles':216,'arches':2,'columns':6})
bpy.ops.object.select_all(action='DESELECT')
for obj in [panorama,*pieces]:obj.select_set(True)
bpy.context.view_layer.objects.active=panorama;bpy.ops.object.join();panorama['render_only']=True;panorama['fidelity_revision']='run8-library-halls'
triangles=sum(len(f.vertices)-2 for f in panorama.data.polygons);assert triangles==3936
blend=OUT/'archive-world-panorama.blend';glb=OUT/'archive-world-panorama.glb';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((SOURCE/'panorama-input-contract.json').read_text());c.update(meshCount=3,primitiveCount=3,materialCount=3,vertices=len({tuple(v.co) for v in panorama.data.vertices}),triangles=triangles)
c['texture'].update(count=2,secondAtlas='archive-world-terrain-atlas.png');c['style']='Existing sky and ridges with four authored colonnaded library ruins outside the playable square'
c['namedCorrections']['libraryHalls']='Four library ruins, eight arched openings and 24 columns; 864 added triangles; near scenery uses ordinary depth'
c['sourceArt']+=['assets/raw/plate-contract-e10-archive-world.png','assets/pilots/map-rebuild-spike/sources/archive-world-fidelity-1/engraved-masonry.png']
c['runtimeDetailTexture']={'asset':'sources/archive-world-fidelity-1/engraved-masonry.png','width':1254,'height':1254,'scope':'floor and scenery material only, no sampled height or restoration authority'}
for key,path in [('blend',blend),('glb',glb)]:c['files'][key]={'bytes':path.stat().st_size,'sha256':sha(path)}
(OUT/'archive-world-panorama-contract.json').write_text(json.dumps(c,indent=2)+'\n');(SOURCE/'library-layout.json').write_text(json.dumps(records,indent=2)+'\n')
print('ARCHIVE LIBRARY',triangles,c['vertices'])
