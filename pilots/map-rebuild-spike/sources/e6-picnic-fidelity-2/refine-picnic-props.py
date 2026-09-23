"""Rebuild existing picnic props; preserve footprints and source bounds; keep original shared atlas untouched.
Run Blender from game root. Optional -- output-dir exports an isolated draft.
"""
from pathlib import Path
import bpy,math,json,hashlib,sys
from mathutils import Vector
P=Path.cwd()/'assets/pilots/map-rebuild-spike';S=Path(__file__).resolve().parent;PACK=P/'landmarks/picnic'
if '--' in sys.argv:PACK=Path(sys.argv[sys.argv.index('--')+1]);PACK.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text());assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
parts=[];material=None;body=None
cloth_material=bpy.data.materials.new('Picnic woven cloth and wicker');cloth_material.use_nodes=True
bsdf=cloth_material.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=1
texture=cloth_material.node_tree.nodes.new('ShaderNodeTexImage');texture.image=bpy.data.images.load(str(S/'cloth-wicker-atlas.png'));texture.image.scale(1024,1024);texture.image.pack()
cloth_material.node_tree.links.new(texture.outputs['Color'],bsdf.inputs['Base Color'])

def finish(o,role):
 o.data.materials.append(cloth_material if role>=16 else material);uv=o.data.uv_layers.active or o.data.uv_layers.new();uv.name='LandmarkAtlasUV'
 if role>=16:
  col,row={16:(0,1),17:(1,1),18:(0,0),19:(1,0)}[role]
  for v in uv.data:v.uv=((col+.03+v.uv.x*.94)/2,(row+.03+v.uv.y*.94)/2)
 else:
  row,col=divmod(role,4)
  for v in uv.data:v.uv=((col+.30+v.uv.x*.22)/4,(row+.42+v.uv.y*.22)/4)
 parts.append(o);return o

def box(name,p,size,role=0,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size
 if bevel:
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);m=o.modifiers.new('Soft handcrafted edge','BEVEL');m.width=bevel;m.segments=1;bpy.ops.object.modifier_apply(modifier=m.name)
 return finish(o,role)

def cyl(name,a,b,r,role=8,n=12):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return finish(o,role)

def ring(name,p,r,t,role=8,n=16,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=4,major_radius=r,minor_radius=t,location=p,rotation=rotation);o=bpy.context.object;o.name=name;return finish(o,role)

def custom(name,verts,faces,role):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);uv=mesh.uv_layers.new()
 for f in mesh.polygons:
  for li in f.loop_indices:
   v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(v.x*.1+.5,v.y*.1+.5)
 return finish(o,role)

def start(name):
 global body,material,parts,bounds
 body=bpy.data.objects[name];material=body.data.materials[0];parts=[];bounds=[(min(v.co[i] for v in body.data.vertices),max(v.co[i] for v in body.data.vertices)) for i in range(3)]

def complete(features):
 old=body.data;body.data=bpy.data.meshes.new(body.name+'Fidelity');bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join();bpy.data.meshes.remove(old)
 for i,(lo,hi) in enumerate(bounds):
  a=min(v.co[i] for v in body.data.vertices);b=max(v.co[i] for v in body.data.vertices)
  for v in body.data.vertices:v.co[i]=lo+(v.co[i]-a)*(hi-lo)/(b-a)
 bpy.context.view_layer.update();n=sum(len(f.vertices)-2 for f in body.data.polygons);assert n<=3000,(body.name,n)
 body['fidelity_recipe']='sources/e6-picnic-fidelity-2/refine-picnic-props.py'
 bpy.ops.export_scene.gltf(filepath=str(PACK/(body.name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
 r=c['assets'][body.name];r['fidelityCorrection']={'recipe':body['fidelity_recipe'],'trianglesBefore':r['triangles'],'trianglesAfter':n,'features':features,'preserved':'exact source envelope, atlas pixels, mounts, collision footprints, inspection stations'};r.update(triangles=n,meshCount=2,materialCount=2,sha256=sha(PACK/(body.name+'.glb')));print(body.name,n)

def cup(x,y):
 # Open vessel with a closed bottom and a visibly separate curved handle.
 n=12;v=[]
 for r,z in [(.24,.20),(.28,.73),(.22,.73),(.18,.25)]:
  for i in range(n):a=i*math.tau/n;v.append((x+r*math.cos(a),y+r*math.sin(a),z))
 f=[]
 for k in range(3):
  for i in range(n):f.append((k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i))
 f.append(tuple(reversed(range(n))));f.append(tuple(3*n+i for i in range(n)));custom('Open enamel cup',v,f,6)
 ring('Cup handle',(x+.30,y,.47),.17,.045,6,12,(math.pi/2,0,0))

def basket(x,y):
 box('Rounded wicker basket',(x,y,.62),(1.28,1.08,.85),17,.13)
 for z in (.28,.48,.69,.91):
  o=ring('Woven basket rib',(x,y,z),.53,.035,17,12);o.scale=(1.17,1,1)
 # Upright arched handle meets opposing sides of the basket.
 for i in range(8):
  a=i*math.pi/8;b=(i+1)*math.pi/8
  cyl('Basket handle',(x+.56*math.cos(a),y,1.00+.59*math.sin(a)),(x+.56*math.cos(b),y,1.00+.59*math.sin(b)),.055,8,6)
 box('Basket cloth',(x,y,1.055),(1.02,.78,.045),18,.04)

def saucer(x,y):
 cyl('Plate well',(x,y,.16),(x,y,.22),.46,10,16);ring('Raised plate rim',(x,y,.23),.42,.035,10,16)

for name,variant in [('west-picnic-blanket',0),('center-picnic-blanket',1),('east-picnic-blanket',2)]:
 start(name);hx,hy=bounds[0][1],bounds[1][1]
 # Hand-folded ground cloth, no new physical obstacle.
 nx,ny=8,6;v=[];f=[]
 for j in range(ny+1):
  for i in range(nx+1):
   x=-hx+2*hx*i/nx;y=-hy+2*hy*j/ny;z=.07+.03*math.sin(i*1.8+j*.9)+(.035 if i in (0,nx) else 0)
   v.append((x,y,z))
 for j in range(ny):
  for i in range(nx):a=j*(nx+1)+i;f.append((a,a+1,a+nx+2,a+nx+1))
 custom('Soft folded picnic cloth',v,f,18)
 for x,y in [(-1.40,-.65),(.15,-1.25),(1.56,-.45)]:saucer(x,y)
 cup(-2.22,-.36);cup(.88,-1.52)
 basket(2.32,1.49)
 box('Bread board',(-1.16,1.03,.20),(1.8,1.15,.10),0,.09)
 for i in range(3):
  o=box('Thick sandwich',(-1.65+i*.51,1.03,.39),(.47,.69,.27),10,.05);o.rotation_euler.z=(i-1)*.16
 if variant==1:
  cyl('Orrery pedestal',(0,.59,.15),(0,.59,.37),.40,8,16)
  cyl('Orrery stem',(0,.59,.34),(0,.59,1.27),.085,8,10)
  for angle in (0,math.pi/3,2*math.pi/3):
   ring('Atom orbital band',(0,.59,1.29),.80,.035,8,20,(math.pi/2,.5,angle))
  for x,y,z in [(.67,.65,1.71),(-.56,.45,.75),(0,.59,1.29)]:
   bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.15,location=(x,y,z));finish(bpy.context.object,8)
 else:
  box('Folded spare napkin',(.25,1.06,.23),(.74,.56,.17),10,.035)
 complete(['folded cloth and woven checks','open cups with handles and rimmed dishes','rounded wicker basket with arched handle','bread board and thick sandwiches']+(['small brass atom centerpiece'] if variant==1 else []))

start('mesa-civilian-shade');hx,hy,h=bounds[0][1],bounds[1][1],bounds[2][1]
# Retain the authored bench and atom meshes. Lower the pendant beneath the sagging membrane.
m=body.data;adj={v.index:set() for v in m.vertices}
for e in m.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
unseen=set(adj);keep=set()
while unseen:
 todo=[next(iter(unseen))];group=set()
 while todo:
  i=todo.pop()
  if i in group:continue
  group.add(i);todo.extend(adj[i]-group)
 unseen-=group
 lo=[min(m.vertices[i].co[k] for i in group) for k in range(3)];hi=[max(m.vertices[i].co[k] for i in group) for k in range(3)]
 if hi[2]<1 or (hi[0]-lo[0]<1.5 and lo[2]>2 and hi[2]<4):keep|=group
indices=sorted(keep);remap={v:i for i,v in enumerate(indices)};faces=[f for f in m.polygons if all(v in keep for v in f.vertices)]
mesh=bpy.data.meshes.new('Retained bench and atom pendant');mesh.from_pydata([(m.vertices[i].co.x,m.vertices[i].co.y,m.vertices[i].co.z-(.82 if m.vertices[i].co.z>2 else 0)) for i in indices],[],[[remap[v] for v in f.vertices] for f in faces]);mesh.update();uv=mesh.uv_layers.new(name='LandmarkAtlasUV')
for a,b in zip(faces,mesh.polygons):
 for old,new in zip(a.loop_indices,b.loop_indices):uv.data[new].uv=m.uv_layers.active.data[old].uv
furniture=bpy.data.objects.new('Retained bench and atom pendant',mesh);bpy.context.collection.objects.link(furniture);furniture.data.materials.append(material);parts.append(furniture)
for x in (-1.92,1.92):box('Bench trestle foot',(x,.8,.29),(.23,.76,.58),0,.035)

# Four posts retain the exact existing collision-backed canopy envelope.
for x in (-hx+.26,hx-.26):
 for y in (-hy+.30,hy-.30):
  cyl('Canopy upright',(x,y,0),(x,y,h-.11),.105,0,10)
  cyl('Post finial',(x,y,h-.21),(x,y,h),.16,8,10)
  box('Post footing',(x,y,.07),(.38,.38,.14),0,.035)
nx,ny=12,8;v=[];f=[]
for j in range(ny+1):
 for i in range(nx+1):
  x=-hx+2*hx*i/nx;y=-hy+2*hy*j/ny
  z=h-.35-.67*(1-(x/hx)**2)-.14*(1-(y/hy)**2)+.025*math.sin(j*math.pi/2)
  v.append((x,y,z))
for j in range(ny):
 for i in range(nx):a=j*(nx+1)+i;f.append((a,a+1,a+nx+2,a+nx+1))
cloth=custom('Sagging woven canopy',v,f,16)
for face in cloth.data.polygons:face.use_smooth=True
# Closed thin membrane supplies an underside without two-sided material flags.
mod=cloth.modifiers.new('Canvas thickness','SOLIDIFY');mod.thickness=.045;bpy.context.view_layer.objects.active=cloth;cloth.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name)
for y in (-hy,hy):
 for i in range(nx):
  a=v[(0 if y<0 else ny)*(nx+1)+i];b=v[(0 if y<0 else ny)*(nx+1)+i+1]
  cyl('Stitched canvas hem',a,b,.055,0,6)
for x in (-hx,hx):
 for i in range(ny):
  a=v[i*(nx+1)+(0 if x<0 else nx)];b=v[(i+1)*(nx+1)+(0 if x<0 else nx)]
  cyl('Canvas side hem',a,b,.045,0,6)
complete(['sagging closed canvas with soft folds','stitched continuous hems','four capped support posts with footings','retained authored bench and atom pendant with bench feet'])
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'picnic-landmarks.blend'));c['fidelityTextures']={'clothWicker':{'path':'../../sources/e6-picnic-fidelity-2/cloth-wicker-atlas.png','sha256':sha(S/'cloth-wicker-atlas.png'),'provenance':'../../sources/e6-picnic-fidelity-2/image-provenance.md'}};c['blend']['sha256']=sha(PACK/'picnic-landmarks.blend');(PACK/'picnic-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
