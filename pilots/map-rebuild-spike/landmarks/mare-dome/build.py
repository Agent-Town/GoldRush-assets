import bpy,bmesh,math,json,hashlib
from pathlib import Path
from mathutils import Vector
root=Path.cwd();out=Path(__file__).resolve().parent
source=root/'assets/pilots/dome-commons-3d/dome-commons-plate.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
original=next(o for o in bpy.context.scene.objects if o.type=='MESH');material=original.data.materials[0]
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
atlas_path=root/'assets/raw/mare-dome-material-atlas-v1.png'
image=bpy.data.images.load(str(atlas_path));image.scale(1024,1024);image.filepath_raw=str(out/'mare-dome-landmarks-atlas.png');image.file_format='PNG';image.save();image.pack()
for node in material.node_tree.nodes:
 if node.type=='TEX_IMAGE':node.image=image
shader=next(node for node in material.node_tree.nodes if node.type=='BSDF_PRINCIPLED')
for link in list(shader.inputs['Alpha'].links):material.node_tree.links.remove(link)
shader.inputs['Alpha'].default_value=1
material.name='MareDomeFrame';material.surface_render_method='DITHERED'
glass_material=material.copy();glass_material.name='MareDomeGlass';glass_material.use_backface_culling=True
glass_shader=next(node for node in glass_material.node_tree.nodes if node.type=='BSDF_PRINCIPLED')
glass_shader.inputs['Roughness'].default_value=.18
glass_shader.inputs['Alpha'].default_value=.22;glass_material.surface_render_method='BLENDED'
parts=[]
def finish(obj,name,swatch=2):
 obj.name=name;obj.data.materials.clear();obj.data.materials.append(material)
 uv=obj.data.uv_layers.active or obj.data.uv_layers.new(name='UVMap')
 strip={2:0,6:3,1:1,3:2}.get(swatch,1)
 lo,hi=strip/4+.012,(strip+1)/4-.012
 for polygon in obj.data.polygons:
  for i,loop in enumerate(polygon.loop_indices):uv.data[loop].uv=[(lo,.03),(hi,.03),(hi,.97),(lo,.97)][i%4]
 parts.append(obj);return obj

def box(name,center,size,swatch=2):
 bpy.ops.mesh.primitive_cube_add(size=1,location=center);obj=bpy.context.object;obj.scale=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(obj,name,swatch)

def beam(name,a,b,r=.13,swatch=2,sides=4):
 a,b=Vector(a),Vector(b)
 if name in ('DomeRib','DomeBand'):
  def inside_airlock(p):
   roof=2.55+.68*math.sqrt(max(0,1-(p.x/1.42)**2))
   return abs(p.x)<1.42 and p.y<-4.7 and p.z<roof
  ai,bi=inside_airlock(a),inside_airlock(b)
  if ai and bi:return
  if ai!=bi:
   outside,inside=(b,a) if ai else (a,b)
   for _ in range(32):
    mid=(outside+inside)/2
    if inside_airlock(mid):inside=mid
    else:outside=mid
   if ai:a=outside
   else:b=outside
 bpy.ops.mesh.primitive_cylinder_add(vertices=sides,end_fill_type='NOTHING',radius=r,depth=(b-a).length,location=(a+b)/2)
 obj=bpy.context.object;obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return finish(obj,name,swatch)

def point(angle,t):
 x,y=math.cos(angle),math.sin(angle);factor=6
 return (x*factor*math.sin(t),y*factor*math.sin(t),1.25+3.8*math.cos(t))
# Atlas-backed flush bays add inhabited detail without extra materials or a larger footprint.
def drum_panel(name,angle,width,height,swatch,offset):
 radial=Vector((math.cos(angle),math.sin(angle),0));tangent=Vector((-math.sin(angle),math.cos(angle),0))
 center=radial*(6*math.cos(math.pi/24)+offset)+Vector((0,0,.73))
 vertices=[center+tangent*x+Vector((0,0,z)) for x,z in [(-width/2,-height/2),(width/2,-height/2),(width/2,height/2),(-width/2,height/2)]]
 mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(vertices,[],[(0,1,2,3)]);mesh.update()
 panel=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(panel);finish(panel,name,swatch)
# Circular drum, with a clear south opening into the projecting airlock.
for segment in range(24):
 angle=(segment+.5)/24*math.tau
 if abs(math.atan2(math.sin(angle+math.pi/2),math.cos(angle+math.pi/2)))<.27:continue
 p0=(6*math.cos(segment/24*math.tau),6*math.sin(segment/24*math.tau),.6)
 p1=(6*math.cos((segment+1)/24*math.tau),6*math.sin((segment+1)/24*math.tau),.6)
 # A vertical wall reads as an inhabited drum instead of a diamond-section rail.
 mesh=bpy.data.meshes.new('DrumWallMesh');mesh.from_pydata([(p0[0],p0[1],.08),(p1[0],p1[1],.08),(p1[0],p1[1],1.15),(p0[0],p0[1],1.15)],[],[(0,1,2,3)]);mesh.update()
 panel=bpy.data.objects.new('DrumWall',mesh);bpy.context.collection.objects.link(panel);finish(panel,'DrumWall',6)
 beam('DrumFoot',(p0[0],p0[1],.1),(p1[0],p1[1],.1),.12,2,4)
 if segment%2==0:
  beam('DrumUpright',(p0[0],p0[1],.1),(p0[0],p0[1],1.23),.1,2,4)
 if segment in [2,8,14,20]:
  box('DrumLight',(6.06*math.cos(angle),6.06*math.sin(angle),.8),(.16,.16,.24),3)
 beam('DrumSill',(p0[0],p0[1],1.15),(p1[0],p1[1],1.15),.12,2,4)
 # Five framed ports and six service panels use the last 32 triangles of the 3,000 budget.
 # The two south opening segments have already been skipped; the passage remains empty.
 if segment%2==0:
  if segment%4==2:
   drum_panel('DrumPortFrame',angle,.94,.54,2,.02)
   drum_panel('DrumPortGlass',angle,.72,.34,3,.03)
  else:drum_panel('DrumServicePanel',angle,.62,.76,1,.02)
# Thick, continuous meridians and latitude bands retain a dome silhouette at the game camera.
for meridian in range(24):
 angle=(meridian+.5)/24*math.tau
 pts=[point(angle,i/5*math.pi/2) for i in range(6)]
 for a,b in zip(pts,pts[1:]):
  beam('DomeRib',a,b,.065)
for theta in [.3,.6,.9,1.2,math.pi/2]:
 pts=[point(i/24*math.tau,theta) for i in range(25)]
 for a,b in zip(pts,pts[1:]):
  if theta==math.pi/2 and (abs((a[0]+b[0])/2)<1.6 or abs((a[1]+b[1])/2)<1.6):continue
  beam('DomeBand',a,b,.045,2)
# Each glass bay uses one existing atlas pane, avoiding the dense whole-atlas grid.
vertices=[];faces=[]
for ring in range(6):
 for segment in range(24):
  angles=[segment/24*math.tau,(segment+1)/24*math.tau]
  ts=[ring/6*math.pi/2,(ring+1)/6*math.pi/2]
  if ring>=4 and abs(math.atan2(math.sin(sum(angles)/2+math.pi/2),math.cos(sum(angles)/2+math.pi/2)))<.27:continue
  face=[point(angles[0],ts[0]),point(angles[1],ts[0]),point(angles[1],ts[1]),point(angles[0],ts[1])]
  faces.append(tuple(reversed(range(len(vertices),len(vertices)+4))));vertices.extend(face)
mesh=bpy.data.meshes.new('DomePaneMesh');mesh.from_pydata(vertices,[],faces);mesh.update()
assert all(face.normal.dot(face.center-Vector((0,0,1.25)))>0 for face in mesh.polygons if face.area>1e-8), 'Dome glass must face outward'
obj=bpy.data.objects.new('DomePanes',mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(glass_material)
uv=mesh.uv_layers.new(name='UVMap')
for polygon in mesh.polygons:
 for loop in polygon.loop_indices:
  co=mesh.vertices[mesh.loops[loop].vertex_index].co
  uv.data[loop].uv=(.625+co.x/12*.23,.5+co.y/20*.94)
parts.append(obj)
# Projecting barrel-roof airlock, with a 2.5-wide clear passage.
for y in [-4.7,-8.35]:
 for side in [-1,1]:beam('AirlockPost',(side*1.42,y,0),(side*1.42,y,2.55),.13,2,4)
 pts=[]
 for i in range(9):
  x=math.cos(i/8*math.pi)*1.42;z=2.55+math.sin(i/8*math.pi)*.68
  # Inner collar follows the dome/barrel intersection, supporting trimmed ribs.
  join_y=-6*math.sqrt(1-(x/6)**2-((z-1.25)/3.8)**2) if y==-4.7 else y
  pts.append((x,join_y,z))
 for a,b in zip(pts,pts[1:]):beam('AirlockArch',a,b,.13,2,4)
for side in [-1,1]:
 box('AirlockWall',(side*1.42,-6.525,.8),(.2,3.65,1.6),6)
 beam('AirlockRail',(side*1.42,-4.7,2.55),(side*1.42,-8.35,2.55),.1,2)
 box('PressureLamp',(side*1.42,-8.45,2.3),(.22,.22,.3),3)
# Glazed barrel closes the vestibule roof without blocking either end.
verts=[];faces=[]
for segment in range(8):
 a,b=segment/8*math.pi,(segment+1)/8*math.pi
 face=[(math.cos(a)*1.42,-4.7,2.55+math.sin(a)*.68),(math.cos(b)*1.42,-4.7,2.55+math.sin(b)*.68),(math.cos(b)*1.42,-8.35,2.55+math.sin(b)*.68),(math.cos(a)*1.42,-8.35,2.55+math.sin(a)*.68)]
 faces.append(tuple(range(len(verts),len(verts)+4)));verts.extend(face)
mesh=bpy.data.meshes.new('AirlockGlassMesh');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('AirlockGlass',mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(glass_material);uv=mesh.uv_layers.new(name='UVMap')
for polygon in mesh.polygons:
 for loop in polygon.loop_indices:
  co=mesh.vertices[mesh.loops[loop].vertex_index].co
  uv.data[loop].uv=(.625+co.x/12*.23,.5+co.y/20*.94)
parts.append(obj)
# Open ground passage: no opaque slab that reads as a shut door from the game camera.
# Brass crown establishes a built roof rather than a temporary cage.
bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=1,location=(0,0,5.04));obj=bpy.context.object;obj.scale=(.48,.48,.16);finish(obj,'Crown',2)
bpy.ops.object.select_all(action='DESELECT')
for obj in parts:obj.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();obj=bpy.context.object
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
obj.name='air-pad-dome';bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001);bm.to_mesh(obj.data);bm.free();obj.data.calc_loop_triangles();triangles=len(obj.data.loop_triangles);assert triangles<=3000,triangles
for key,value in {'render_only':True,'landmark':True,'mount_id':'air-pad-dome','map_pack':'mare-dome','era':8,'source_tier':'derive','simulation_authority':'none; mounted render-only scenery'}.items():obj[key]=value
bpy.ops.wm.save_as_mainfile(filepath=str(out/'mare-dome-landmarks.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'air-pad-dome.glb'),export_format='GLB',use_selection=True,export_yup=True,export_extras=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
lo=[min(v.co[i] for v in obj.data.vertices) for i in range(3)]
hi=[max(v.co[i] for v in obj.data.vertices) for i in range(3)]
asset='landmarks/mare-dome/'
pack={'map':'mare-dome','hostTerrainContract':'mare-claim-terrain-contract.json','era':8,'status':'integrated work in progress; final concept fidelity and objective proof open',
 'sourceLadder':['reuse','derive','build-new'],
 'atlas':{'asset':asset+'mare-dome-landmarks-atlas.png','width':1024,'height':1024,'sharedByEveryAsset':True,'sha256':sha(out/'mare-dome-landmarks-atlas.png')},
 'blend':{'asset':asset+'mare-dome-landmarks.blend','sha256':sha(out/'mare-dome-landmarks.blend')},
 'assets':{'air-pad-dome':{'asset':asset+'air-pad-dome.glb','sourceTier':'derive','sources':[str(source.relative_to(root)),str(atlas_path.relative_to(root)),'assets/raw/plate-contract-e8-mare-claim.png'],'terrainConformed':False,'triangles':triangles,'triangleBudget':3000,'meshCount':2,'gltfMeshCount':1,'primitiveCount':2,'materialCount':2,'bounds':{'min':lo,'max':hi},'sha256':sha(out/'air-pad-dome.glb')}},
 'mounts':[{'id':name+'-air-pad-dome','position':[x,.08,0],'rotation':[0,0,0],'scale':[1,1,1],'asset':asset+'air-pad-dome.glb','contractIds':['e8-mare-claim','e8-eclipse']} for name,x in [('west',-18),('central',0),('east',18)]]}
contract=out/'mare-dome-landmark-pack-contract.json'
contract.write_text(json.dumps(pack,indent=2)+'\n')
ledger_path=out.parent/'landmark-source-ledger.json'
ledger=json.loads(ledger_path.read_text())
ledger['packs']['mare-dome']={key:{field:body[field] for field in ['sourceTier','sources','asset']} for key,body in pack['assets'].items()}
ledger['packs']=dict(sorted(ledger['packs'].items()))
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps(pack))
