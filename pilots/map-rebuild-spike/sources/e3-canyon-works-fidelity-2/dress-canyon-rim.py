"""Layered rock buttresses outside the playable rectangle, in one scenery mesh.
Reuse the plate-derived rock atlas without any raster repaint. The original
sky geometry/UVs and every apron position stay exact, including the seam ring.
"""
from pathlib import Path
import bpy,bmesh,hashlib,json,math,random
P=Path.cwd()/'assets/pilots/map-rebuild-spike';S=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(S/'panorama-input.blend'))
panorama=next(o for o in bpy.data.objects if o.type=='MESH')
# Split the original 192-triangle apron into its own material owner. Every
# position, including the 97 corrected inner-ring vertices, stays exact.
source=panorama.data; apron_faces=list(source.polygons)[2304:]; assert len(apron_faces)==192
indices=sorted({i for f in apron_faces for i in f.vertices}); remap={v:i for i,v in enumerate(indices)}
apron_mesh=bpy.data.meshes.new('CanyonApronEarth');apron_mesh.from_pydata([tuple(source.vertices[i].co) for i in indices],[],[tuple(remap[i] for i in f.vertices) for f in apron_faces]);apron_mesh.update()
apron=bpy.data.objects.new('CanyonApronEarth',apron_mesh);bpy.context.collection.objects.link(apron)
uv=apron_mesh.uv_layers.new(name='UVMap')
for loop in apron_mesh.loops:
 v=apron_mesh.vertices[loop.vertex_index].co
 uv.data[loop.index].uv=((v.x+48)/96,(v.y+56)/112)
bm=bmesh.new();bm.from_mesh(source);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=list(bm.faces)[2304:],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(source);bm.free()
earth=bpy.data.materials.new('CanyonApronEarth');earth.use_nodes=True
shader=earth.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.94
paint=earth.node_tree.nodes.new('ShaderNodeTexImage');paint.image=bpy.data.images.load(str(P/'canyon-works-terrain-atlas.png'));paint.image.pack();paint.extension='REPEAT'
earth.node_tree.links.new(paint.outputs['Color'],shader.inputs['Base Color']);apron_mesh.materials.append(earth)
apron['render_only']=True;apron['panorama']=True;apron['panorama_law']='v2';apron['heightAuthority']=False
material=bpy.data.materials.new('CanyonCliffStone');material.use_nodes=True
bsdf=material.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.96
tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P.parents[1]/'raw/ter-canyon-atlas.png'))
tex.image.scale(2048,2048);tex.image.pack();material.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
color_node=material.node_tree.nodes.new('ShaderNodeVertexColor');color_node.layer_name='CanyonStrataTint'
mix=material.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
material.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);material.node_tree.links.new(color_node.outputs['Color'],mix.inputs[2]);material.node_tree.links.new(mix.outputs[0],bsdf.inputs['Base Color'])
material.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=.25
verts=[];faces=[];uvs=[];tints=[];records=[];rng=random.Random(90323)
def buttress(x,y,rx,ry,h,tone,phase):
 start=len(verts);n=8;radii=[rng.uniform(.85,1.12) for _ in range(n)]
 # Five broken strata, a talus skirt and a sloped shoulder. Rings are staggered
 # rather than flat extrusions; rear and side pieces overlap into a distant rim.
 for level,(frac,scale) in enumerate([(0,1),(.17,.94),(.43,.68),(.65,.74),(.94,.43),(1,.36)]):
  for i in range(n):
   a=i*math.tau/n+phase; wobble=math.sin(a*3+phase)*.045 if level else 0
   verts.append((x+math.cos(a)*rx*radii[i]*scale,y+math.sin(a)*ry*radii[i]*scale,-.30+h*(frac+wobble)))
 for level in range(5):
  for i in range(n):
   j=(i+1)%n;faces.append((start+level*n+i,start+level*n+j,start+(level+1)*n+j,start+(level+1)*n+i))
   u=.52+(i%3)*.135;v=.54+(level%2)*.19
   uvs.append([(u,v),(u+.13,v),(u+.12,v+.18),(u+.01,v+.18)])
   # Tone each stratum and aspect without changing atlas pixels.
   k=tone*(.81 if level in (1,3) else 1.0)*(1+.08*math.cos(i*math.tau/n))
   tints.append((k,k*.93,k*.84,1))
 faces.append(tuple(start+5*n+i for i in range(n)));uvs.append([(.75+.18*math.cos(i*math.tau/n),.75+.18*math.sin(i*math.tau/n)) for i in range(n)]);tints.append((tone,tone*.96,tone*.90,1))
 points=verts[start:]
 # Explicit spatial authority: no rock vertex is inside the playfield rectangle.
 assert all(abs(v[0])>48 or abs(v[1])>56 for v in points)
 records.append({'center':[x,y],'radii':[rx,ry],'height':h,'vertices':len(points),'outsidePlayfield':True})
# The south rim is visible at plain entry; leave an asymmetric low saddle behind
# the works, with taller shoulders at each side and a separate distant layer.
for row in [(-44,67,12,10,16,.84),(-24,72,12,13,14,.89),(-5,82,14,16,10,.91),(19,77,14,14,13,.86),(41,69,13,11,18,.82),(-34,106,23,17,29,.62),(16,113,24,18,25,.65)]:buttress(*row,rng.uniform(-.2,.2))
# Side silhouettes extend the visual canyon along the route, all beyond x=48.
for row in [(-63,33,11,22,21,.74),(65,30,12,21,24,.76),(-66,-23,12,22,24,.70),(64,-25,12,24,21,.74),(-40,-72,17,13,17,.70),(7,-82,23,16,20,.67),(40,-72,16,13,23,.71)]:buttress(*row,rng.uniform(-.2,.2))
# Low broken talus sits just outside the protected edge and interrupts the
# ruler-straight material transition. Fourteen 20-triangle stones use the final
# 280 triangles of the panorama allowance, without touching the terrain mesh.
for i,(x,y) in enumerate([(-44,60),(-40,58.3),(-34,62),(-26,61),(-23,58),(-8,64),(-3,59),(14,58),(18,63),(29,60),(32,59),(36,64),(41,58.4),(45,62)]):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,.45))
 o=bpy.context.object;o.scale=(rng.uniform(.8,3.1),rng.uniform(.6,1.4),rng.uniform(.35,1.4));bpy.context.view_layer.update()
 start=len(verts);points=[o.matrix_world@v.co for v in o.data.vertices]
 assert all(abs(v.x)>48 or abs(v.y)>56 for v in points)
 verts.extend(tuple(v) for v in points)
 for f in o.data.polygons:
  faces.append(tuple(start+i for i in f.vertices));uvs.append([(.53+(o.data.vertices[j].co.x+1)*.21,.54+(o.data.vertices[j].co.y+1)*.21) for j in f.vertices]);tints.append((.83,.79,.72,1))
 records.append({'center':[x,y],'height':o.scale.z*2,'outsidePlayfield':True,'kind':'talus'})
 bpy.data.objects.remove(o,do_unlink=True)
mesh=bpy.data.meshes.new('CanyonRimStrata');mesh.from_pydata(verts,[],faces);mesh.update();rock=bpy.data.objects.new('CanyonRimStrata',mesh);bpy.context.collection.objects.link(rock);mesh.materials.append(material)
uv=mesh.uv_layers.new(name='UVMap');color=mesh.color_attributes.new(name='CanyonStrataTint',type='FLOAT_COLOR',domain='CORNER')
for f,coords,tint in zip(mesh.polygons,uvs,tints):
 for i,coord in zip(f.loop_indices,coords):uv.data[i].uv=coord;color.data[i].color=tint
rock['render_only']=True;rock['panorama']=True;rock['panorama_law']='v2';rock['heightAuthority']=False
bpy.ops.object.select_all(action='DESELECT');panorama.select_set(True);rock.select_set(True);apron.select_set(True);bpy.context.view_layer.objects.active=panorama
triangles=sum(len(f.vertices)-2 for o in (panorama,rock,apron) for f in o.data.polygons);assert triangles<=4000,triangles
bpy.context.preferences.filepaths.save_version=0;blend=P/'canyon-works-panorama.blend';glb=P/'canyon-works-panorama.glb'
bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True,export_vertex_color='ACTIVE')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=json.loads((S/'panorama-input-contract.json').read_text())
c.update(meshCount=3,primitiveCount=3,materialCount=3,triangles=triangles,vertices=sum(len({tuple(v.co) for v in o.data.vertices}) for o in (panorama,rock,apron)))
c['texture'].update(count=3,thirdAtlas='canyon-works-terrain-atlas.png',secondAtlas='assets/raw/ter-canyon-atlas.png',secondAtlasEncoding='existing native plate resampled to 2048 square only in embedded GLB; source pixels remain unchanged; UVs restricted to rocky upper-right quadrant')
c['sourceArt'].append('assets/raw/ter-canyon-atlas.png') if 'assets/raw/ter-canyon-atlas.png' not in c['sourceArt'] else None
c['rimScenery']={'recipe':'sources/e3-canyon-works-fidelity-2/dress-canyon-rim.py','count':len(records),'triangles':triangles-2496,'renderOnly':True,'allVerticesOutsidePlayfield':True,'heightAuthority':False,'preserved':'original sky geometry/UVs/tint and atlas; all original apron positions and seam-closing ring; apron uses unchanged terrain atlas'}
for kind,p in [('blend',blend),('glb',glb)]:c['files'][kind]={'bytes':p.stat().st_size,'sha256':sha(p)}
(P/'canyon-works-panorama-contract.json').write_text(json.dumps(c,indent=2)+'\n');(S/'rim-layout.json').write_text(json.dumps(records,indent=2)+'\n')
print('CANYON_RIM',triangles,c['vertices'],len(records))
