"""Replace competing hoops with a joined salvage housing; exact original envelope.

Run with Blender from the game root. Frozen peer meshes and new native surface
swatches; no gameplay or mount authority is changed.
"""
from pathlib import Path
import bpy,math,json,hashlib
from mathutils import Vector
P=Path.cwd()/'assets/pilots/map-rebuild-spike';S=Path(__file__).resolve().parent;PACK=P/'landmarks/low-orbit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text());assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
body=bpy.data.objects['claw-carcass-rig'];mat=body.data.materials[0]
atlas=bpy.data.images.load(str(P/'landmarks/low-orbit/low-orbit-landmarks-atlas.png'),check_existing=False);atlas.pack()
for m in bpy.data.materials:
 if m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE':n.image=atlas
parts=[]
def finish(o,role):
 o.data.materials.append(mat);uv=o.data.uv_layers.active or o.data.uv_layers.new();uv.name='LandmarkAtlasUV';row,col=divmod(role,4)
 for v in uv.data:v.uv=((col+.15+v.uv.x*.70)/4,(row+.15+v.uv.y*.70)/4)
 parts.append(o);return o
def box(name,p,size,role=1):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;return finish(o,role)
def beam(name,a,b,w,role=1):
 a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,w,(b-a).length),role);o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return o
def cyl(name,a,b,r,role=8,n=12,r2=None):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r,radius2=r if r2 is None else r2,depth=(b-a).length,location=(a+b)/2)
 o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return finish(o,role)
def ring(name,p,r,t,role=8,n=24,vertical=False):
 bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=4,major_radius=r,minor_radius=t,location=p,rotation=(math.pi/2 if vertical else 0,0,0));o=bpy.context.object;o.name=name;return finish(o,role)
def housing():
 # Closed cross-section with a deep inner bore, bolted lip and tapering outer wall.
 profile=[(2.2,1.05),(2.4,1.42),(2.12,3.12),(1.91,3.30),(1.25,3.30),(1.25,1.11)]
 n=24;verts=[(r*math.cos(i*math.tau/n),.22+r*.78*math.sin(i*math.tau/n),z) for r,z in profile for i in range(n)]
 faces=[]
 for j in range(len(profile)):
  for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,((j+1)%len(profile))*n+(i+1)%n,((j+1)%len(profile))*n+i))
 mesh=bpy.data.meshes.new('SalvageHousing');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('SalvageHousing',mesh);bpy.context.collection.objects.link(o)
 uv=mesh.uv_layers.new(name='LandmarkAtlasUV')
 for f in mesh.polygons:
  j=f.index//n;role=9 if j==4 else (8 if j in (0,2,3) else 1);row,col=divmod(role,4)
  corners=[mesh.vertices[i].co for i in f.vertices];u=(corners[1]-corners[0]).length/2.8;v=(corners[3]-corners[0]).length/2.8
  for k,li in enumerate(f.loop_indices):uv.data[li].uv=((col+.15+(0,u,u,0)[k]*.70)/4,(row+.15+(0,0,v,v)[k]*.70)/4)
 o.data.materials.append(mat);parts.append(o)
housing()
base=cyl('Chamfered work deck',(0,0,0),(0,0,.22),1,10,8);base.scale.x=4.2;base.scale.y=3.2
# A quiet atlas sample keeps the broad deck from magnifying brushed-metal grain
# into apparent timber planks. Detail belongs to the housing and locking rim.
for v in base.data.uv_layers.active.data:v.uv=((2+.48)/4,(2+.48)/4)
cyl('Bore floor',(0,.22,1.03),(0,.22,1.10),1.24,9,24)
# The service rim is attached to the housing, no floating vertical hoop.
for z,r in [(1.42,2.42),(3.30,1.91)]:
 o=ring('Joined pressure collar',(0,.22,z),r,.065,8);o.scale.y=.78
for i in range(12):
 t=i*math.tau/12
 beam('Housing armor seam',(2.39*math.cos(t),.22+1.86*math.sin(t),1.43),(2.12*math.cos(t),.22+1.65*math.sin(t),3.10),.07,10)
for i in range(16):
 t=i*math.tau/16;x=1.66*math.cos(t);y=.22+1.30*math.sin(t)
 cyl('Rim locking bolt',(x,y,3.29),(x,y,3.39),.06,10,6)
# Four explicit foot/pier/turret assemblies make contact and support readable.
for x in (-2.72,2.72):
 for y in (-1.64,1.64):
  box('Socket shoe',(x,y,.35),(.96,.91,.26),9)
  cyl('Pier base',(x,y,.46),(x,y,.73),.43,8,10)
  cyl('Fluted pressure pier',(x,y,.73),(x,y,3.36),.32,1,12)
  for z in (1.02,2.31,3.20):cyl('Pier binding collar',(x,y,z),(x,y,z+.10),.37,8,8)
  cyl('Turret conical cap',(x,y,3.41),(x,y,4.60),.48,8,8,r2=.10)
  for t in (math.pi*1.25,math.pi*1.75):
   beam('Turret panel seam',(x+.47*math.cos(t),y+.47*math.sin(t),3.44),(x+.11*math.cos(t),y+.11*math.sin(t),4.57),.035,1)
  cyl('Turret insulator',(x,y,4.60),(x,y,4.77),.14,4,8)
  beam('Radial housing saddle',(x,y,2.82),(x*.69,y*.76,2.82),.24,1)
  beam('Foot knee',(x,y,.64),(x*.73,y*.76,1.56),.16,8)
# Articulated jaws use solid plate profiles and visible pivot/hydraulic parts.
for side in (-1,1):
 x=side*2.52
 cyl('Jaw axle',(x,-.78,2.42),(x,-1.20,2.42),.42,8,12)
 beam('Jaw shoulder',(x,-.98,2.44),(side*3.65,-1.50,1.92),.50,1)
 beam('Jaw outer knuckle',(side*3.65,-1.50,1.92),(side*4.04,-2.05,.85),.42,8)
 beam('Inturned salvage finger',(side*4.04,-2.05,.85),(side*3.42,-2.50,.46),.26,1)
 cyl('Hydraulic cylinder',(side*2.67,-1.36,2.85),(side*3.41,-1.74,1.93),.16,10,10)
 cyl('Hydraulic piston',(side*3.41,-1.74,1.93),(side*3.82,-2.04,1.15),.095,8,8)
# A narrow rear hoist defines the highest point and ties into the rear piers.
for x in (-1.80,1.80):
 beam('Hoist stanchion',(x,1.30,1.38),(x,1.30,5.72),.20,1)
 beam('Hoist knee',(x,1.30,4.94),(x*.48,1.30,5.72),.14,8)
beam('Hoist header',(-1.90,1.30,5.77),(1.90,1.30,5.77),.24,1)
ring('Hoist pulley',(0,1.22,5.80),.35,.065,8,n=12,vertical=True)
beam('Hoist cable',(0,1.17,5.49),(0,1.17,3.73),.042,9)
cyl('Hoist hook collar',(0,1.17,3.66),(0,1.17,3.82),.15,8,8)
beam('Beacon stalk',(1.80,1.30,5.83),(1.80,1.30,6.46),.085,1)
cyl('Beacon ceramic',(1.80,1.30,6.40),(1.80,1.30,6.63),.17,6,8)
# Face panel/pressure glass sits flush; avoids another competing decorative ring.
box('Front control panel',(0,-1.64,2.03),(1.30,.26,.90),1)
box('Teal inset controls',(0,-1.79,2.08),(.98,.055,.59),4)
for x in (-.34,.34):cyl('Panel fixing',(x,-1.81,1.82),(x,-1.88,1.82),.065,8,6)
old=body.data;bounds=[(min(v.co[i] for v in old.vertices),max(v.co[i] for v in old.vertices)) for i in range(3)]
body.data=bpy.data.meshes.new('SalvageRigFidelity');body.data.materials.append(mat);bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();bpy.data.meshes.remove(old)
for i,(lo,hi) in enumerate(bounds):
 a=min(v.co[i] for v in body.data.vertices);b=max(v.co[i] for v in body.data.vertices)
 for v in body.data.vertices:v.co[i]=lo+(v.co[i]-a)*(hi-lo)/(b-a)
for f in body.data.polygons:f.material_index=0
while len(body.data.materials)>1:body.data.materials.pop(index=len(body.data.materials)-1)
tri=sum(len(f.vertices)-2 for f in body.data.polygons);assert tri<=3000,tri
body['fidelity_recipe']='sources/e8-low-orbit-fidelity-2/refine-salvage-rig.py'
c['assets'][body.name]['triangles']=tri
c['assets'][body.name]['fidelityCorrection']={'recipe':body['fidelity_recipe'],'trianglesBefore':2972,'trianglesAfter':tri,'preserved':'exact full-body bounds, chamfered deck height, mount, station, collision footprint','features':['deep annular recovery housing','integrated rim and locking bolts','four socket-foot pressure turrets','articulated jaws with hydraulics','braced hoist and pulley','physically scaled housing UVs and native material swatches']}
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'low-orbit-landmarks.blend'))
for id in c['assets']:
 bpy.ops.object.select_all(action='DESELECT');o=bpy.data.objects[id];o.select_set(True);bpy.context.view_layer.objects.active=o
 target=PACK/(id+'.glb');bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
 c['assets'][id]['sha256']=sha(target)
c['blend']['sha256']=sha(PACK/'low-orbit-landmarks.blend');c['atlas']['sha256']=sha(P/'landmarks/low-orbit/low-orbit-landmarks-atlas.png');c['atlas']['provenance']='Native image_gen swatches reused from the completed Far Side material pass; local original in sources/e8-low-orbit-fidelity-2/native-metal-swatches.png.'
(PACK/'low-orbit-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n');print('SALVAGE RIG',tri)
