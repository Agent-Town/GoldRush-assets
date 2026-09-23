"""Rebuild two existing service landmarks from frozen input, using original pixels.
Run with Blender from the game checkout. No new mounts or gameplay surfaces.
"""
from pathlib import Path
import bpy, json, hashlib, math
from mathutils import Vector

P=Path.cwd()/'assets/pilots/map-rebuild-spike'; S=Path(__file__).resolve().parent
PACK=P/'landmarks/dust-flats'; sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text())
assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
parts=[]; body=None; material=None
def finish(o,role):
 o.data.materials.clear();o.data.materials.append(material)
 uv=o.data.uv_layers.active or o.data.uv_layers.new();uv.name='LandmarkAtlasUV'
 row,col=divmod(role,4)
 # Restrict each primitive to a quieter part of the original swatch. Geometry
 # carries seams/hoops, rather than enlarging the atlas's miniature buildings.
 for v in uv.data:v.uv=((col+.28+v.uv.x*.30)/4,(row+.23+v.uv.y*.38)/4)
 parts.append(o);return o
def box(name,p,size,role=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;return finish(o,role)
def cyl(name,a,b,r,role=1,n=12):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=(b-a).length,location=(a+b)/2)
 o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return finish(o,role)
def beam(name,a,b,w,role=0):
 a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,w,(b-a).length),role);o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return o
def start(name):
 global body,material,parts
 body=bpy.data.objects[name];material=body.data.materials[0];parts=[]
def commit_body(features):
 old=body.data;body.data=bpy.data.meshes.new(body.name+'Fidelity')
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join();bpy.data.meshes.remove(old)
 bpy.context.view_layer.update()
 bounds={k:[round(fn(v.co[i] for v in body.data.vertices),4) for i in range(3)] for k,fn in [('min',min),('max',max)]}
 assert bounds==c['assets'][body.name]['bounds'],(body.name,bounds,c['assets'][body.name]['bounds'])
 n=sum(len(f.vertices)-2 for f in body.data.polygons);assert n<=c['assets'][body.name]['triangleBudget'],n
 body['fidelity_recipe']='sources/e4-dust-flats-fidelity-2/refine-service-chain.py'
 bpy.ops.export_scene.gltf(filepath=str(PACK/(body.name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
 r=c['assets'][body.name];r['fidelityCorrection']={'recipe':body['fidelity_recipe'],'trianglesBefore':r['triangles'],'trianglesAfter':n,'features':features,'preserved':'exact bounds, atlas bytes, mount, collision footprint, inspection declarations'}
 r.update(triangles=n,sha256=sha(PACK/(body.name+'.glb')));print(body.name,n,bounds)

start('east-horizon-fuel-reserve')
box('Low earth-stained footing',(0,0,.10),(7.4,4.8,.20),2)
for x in (-3.2,-1.6,0,1.6,3.2):box('Deck joist',(x,0,.28),(.22,4.42,.18),0)
for i in range(13):box('Walkable-looking boarded deck',(-3.24+i*.54,0,.42),(.52,4.35,.12),0)
# Three different-height storage vessels echo the plate without making new leases.
for j,(x,y,r,h) in enumerate([(-2.23,.57,.83,2.20),(0,.67,.98,2.48),(2.25,.62,.82,1.92)]):
 z=.49
 cyl('Tank stave barrel',(x,y,z),(x,y,z+h),r,0,16)
 for zz in (z+.20,z+h*.50,z+h-.15):cyl('Iron hoop',(x,y,zz-.055),(x,y,zz+.055),r+.035,1,16)
 for a in range(12):
  t=a*math.tau/12;cyl('Raised stave seam',(x+r*math.cos(t),y+r*math.sin(t),z+.12),(x+r*math.cos(t),y+r*math.sin(t),z+h-.08),.024,1,5)
 bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=r+.045,radius2=.15,depth=.30,location=(x,y,z+h+.15));finish(bpy.context.object,1)
 cyl('Vent neck',(x,y,z+h+.29),(x,y,z+h+.46),.12,8,8)
 cyl('Front tap',(x,y-r-.24,1.03),(x,y-r+.02,1.03),.09,8,8)
 cyl('Tap riser',(x,y-r-.24,.62),(x,y-r-.24,1.03),.09,8,8)
# Visible continuous offline manifold and supported pump, entirely on this deck.
cyl('Collection manifold',(-2.6,-.71,.63),(2.65,-.71,.63),.085,1,12)
for x in (-2.23,0,2.25):cyl('Vessel branch',(x,-.71,.63),(x,-.44,.63),.08,8,8)
box('Pump saddle',(2.87,-1.22,.57),(.76,.76,.18),2)
cyl('Pump body',(2.87,-1.53,.82),(2.87,-.95,.82),.26,1,12)
for x in (-3.35,3.35):
 for y in (-1.95,1.95):box('Rail upright',(x,y,.90),(.09,.09,.84),0)
 beam('Side rail',(x,-1.95,1.31),(x,1.95,1.31),.085,0)
beam('Rear rail',(-3.35,1.95,1.31),(3.35,1.95,1.31),.085,0)
# Center tank reaches the former roof's precise 3.43 m upper bound.
assert abs(.49+2.48+.46-3.43)<1e-9
commit_body(['three hooped storage vessels','ribbed staves and sloped iron lids','connected passive manifold and taps','boarded deck and rails'])

start('north-railhead-storm-tower')
box('Stone landing',(0,0,.13),(4.8,4,.26),2)
for x in (-1.77,1.77):
 for y in (-1.43,1.43):
  beam('Tapered tower leg',(x,y,.22),(x*.71,y*.71,6.24),.24,0)
  box('Iron foot shoe',(x,y,.34),(.37,.37,.40),1)
for z,scale in [(2.23,.91),(4.25,.81),(6.18,.71)]:
 for y in (-1.43*scale,1.43*scale):beam('Cross tie',(-1.77*scale,y,z),(1.77*scale,y,z),.14,0)
 for x in (-1.77*scale,1.77*scale):beam('Side tie',(x,-1.43*scale,z),(x,1.43*scale,z),.14,0)
for lo,hi,s0,s1 in [(.39,2.23,1,.91),(2.23,4.25,.91,.81),(4.25,6.18,.81,.71)]:
 for side in (-1,1):
  for a,b in [(-1,1),(1,-1)]:
   beam('Front lattice',(a*1.77*s0,side*1.43*s0,lo),(b*1.77*s1,side*1.43*s1,hi),.12,0)
   beam('Side lattice',(side*1.77*s0,a*1.43*s0,lo),(side*1.77*s1,b*1.43*s1,hi),.12,0)
box('Observation floor',(0,0,6.30),(3.76,3.16,.22),0)
for x in (-1.47,1.47):
 for y in (-1.17,1.17):box('Cabin corner',(x,y,7.17),(.16,.16,1.6),0)
box('Cabin lower wall',(0,0,6.78),(2.92,2.32,.77),0)
for x in (-1.70,1.70):
 for y in (-1.37,1.37):box('Balcony upright',(x,y,6.85),(.10,.10,1.0),0)
 beam('Balcony side rail',(x,-1.37,7.34),(x,1.37,7.34),.09,0)
for y in (-1.37,1.37):beam('Balcony rail',(-1.70,y,7.34),(1.70,y,7.34),.09,0)
# Open belfry windows and a hipped roof make this a watch tower rather than a shed.
for x in (-.7,0,.7):
 for y in (-1.18,1.18):box('Window mullion',(x,y,7.58),(.075,.075,.80),0)
bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=2.37,radius2=0,depth=1.14,rotation=(0,0,math.pi/4),location=(0,0,8.43));finish(bpy.context.object,1)
cyl('Weather mast',(0,0,8.95),(0,0,9.63),.045,8,8)
box('Teal weather vane',(.31,0,9.43),(.58,.055,.20),4)
commit_body(['tapered open lattice supports','observation cabin with open windows','railed balcony and hipped metal roof','passive teal weather vane'])

bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'dust-flats-landmarks.blend'))
c['blend']['sha256']=sha(PACK/'dust-flats-landmarks.blend')
(PACK/'dust-flats-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
