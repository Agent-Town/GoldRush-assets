"""Rebuild two existing service landmarks from frozen input, using original pixels.
Run with Blender from the game checkout. No new mounts or gameplay surfaces.
"""
from pathlib import Path
import bpy, json, hashlib, math
from mathutils import Vector

P=Path.cwd()/'assets/pilots/map-rebuild-spike'; S=Path(__file__).resolve().parent
PACK=P/'landmarks/long-road'; sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
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
 for v in uv.data:
  v.uv=((col+.46+v.uv.x*.035)/4,(row+.46+v.uv.y*.035)/4) if role==4 else ((col+.28+v.uv.x*.30)/4,(row+.23+v.uv.y*.38)/4)
 parts.append(o);return o
def box(name,p,size,role=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;return finish(o,role)
def cyl(name,a,b,r,role=1,n=12):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=(b-a).length,location=(a+b)/2)
 o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return finish(o,role)
def beam(name,a,b,w,role=0):
 a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,w,(b-a).length),role);o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return o
def start(name):
 global body,material,parts,original_bounds
 body=bpy.data.objects[name];material=body.data.materials[0];parts=[]
 original_bounds=[(min(v.co[i] for v in body.data.vertices),max(v.co[i] for v in body.data.vertices)) for i in range(3)]
def commit_body(features):
 old=body.data;body.data=bpy.data.meshes.new(body.name+'Fidelity')
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join();bpy.data.meshes.remove(old)
 # Fit the final envelope to the exact float32 source bounds, not rounded JSON.
 for i,(lo,hi) in enumerate(original_bounds):
  a=min(v.co[i] for v in body.data.vertices);b=max(v.co[i] for v in body.data.vertices)
  for v in body.data.vertices:v.co[i]=lo+(v.co[i]-a)*(hi-lo)/(b-a)
 bpy.context.view_layer.update()
 bounds={k:[round(fn(v.co[i] for v in body.data.vertices),4) for i in range(3)] for k,fn in [('min',min),('max',max)]}
 assert bounds==c['assets'][body.name]['bounds'],(body.name,bounds,c['assets'][body.name]['bounds'])
 n=sum(len(f.vertices)-2 for f in body.data.polygons);assert n<=c['assets'][body.name]['triangleBudget'],n
 body['fidelity_recipe']='sources/e4-long-road-fidelity-2/refine-roadside-service.py'
 bpy.ops.export_scene.gltf(filepath=str(PACK/(body.name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
 r=c['assets'][body.name];r['fidelityCorrection']={'recipe':body['fidelity_recipe'],'trianglesBefore':r['triangles'],'trianglesAfter':n,'features':features,'preserved':'exact bounds, atlas bytes, mount, collision footprint, inspection declarations'}
 r.update(triangles=n,sha256=sha(PACK/(body.name+'.glb')));print(body.name,n,bounds)

def torus(name,p,major,minor,role=1,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_segments=16,minor_segments=4,location=p,rotation=rotation,major_radius=major,minor_radius=minor);o=bpy.context.object;o.name=name;return finish(o,role)

start('west-way-station')
box('Low weathered footing',(0,0,.10),(8.6,5.9728,.20),2)
for i in range(17):box('Deck board',(-4.08+i*.51,0,.28),(.49,5.56,.16),0)
# Elevated water reserve beside an open front service canopy.
for x in (-3.60,-1.24):
 for y in (-.98,1.38):box('Tank trestle leg',(x,y,1.85),(.23,.23,3.14),0)
for y in (-.98,1.38):
 beam('Trestle diagonal',(-3.60,y,.36),(-1.24,y,3.38),.14,0)
 beam('Trestle opposing diagonal',(-1.24,y,.36),(-3.60,y,3.38),.14,0)
box('Tank landing',(-2.42,.20,3.40),(2.85,2.85,.20),0)
cyl('Timber water tank',(-2.42,.20,3.51),(-2.42,.20,5.62),1.26,0,16)
for z in (3.70,4.53,5.43):cyl('Tank hoop',(-2.42,.20,z-.065),(-2.42,.20,z+.065),1.29,1,16)
bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=1.32,radius2=.12,depth=.44,location=(-2.42,.20,5.84));finish(bpy.context.object,1)
cyl('Tank cap',(-2.42,.20,6.05),(-2.42,.20,6.32),.12,8,8)
cyl('Water downpipe',(-1.18,.20,.72),(-1.18,.20,4.27),.11,1,10)
cyl('Faucet branch',(-1.18,.20,1.35),(-.70,.20,1.35),.10,8,8)
for x in (-.58,3.81):
 for y in (-2.18,2.18):box('Canopy post',(x,y,1.97),(.13,.13,3.38),0)
for y in (-2.18,2.18):beam('Canopy header',(-.65,y,3.60),(3.88,y,3.60),.16,0)
# Two cloth planes carry a low ridge and a scalloped visual valance.
for side in (-1,1):
 o=box('Teal canvas roof',(1.61,side*1.13,3.73),(4.64,2.33,.065),4);o.rotation_euler.x=side*-.12
 for i in range(8):box('Canvas hanging hem',(-.38+i*.57,side*2.28,3.48),(.54,.065,.22),4)
box('Service counter',(1.20,.88,1.02),(2.40,.74,1.30),0)
box('Counter iron top',(1.20,.88,1.71),(2.55,.83,.12),1)
for x,y,z in [(2.96,1.27,.68),(3.12,.15,.64),(2.96,1.27,1.32)]:
 box('Freight crate',(x,y,z),(.64,.70,.63),0)
 for zz in (-.20,.20):box('Crate strapping',(x,y,z+zz),(.67,.73,.05),1)
cyl('Rain barrel',(-.02,1.84,.37),(-.02,1.84,1.33),.41,0,12)
for z in (.49,1.17):cyl('Barrel hoop',(-.02,1.84,z-.04),(-.02,1.84,z+.04),.43,1,12)
commit_body(['open teal canvas service canopy','elevated hooped water tank and connected faucet','braced timber trestle','counter, freight crates and rain barrel'])

start('convoy-lead-hauler-start')
# This is the static registered convoy landmark. Shared Motor actors are untouched.
box('Iron chassis',(0,0,1.17),(8.10,2.58,.28),1)
for i in range(15):box('Wagon deck board',(-3.98+i*.567,0,1.39),(.54,3.24,.16),0)
for x in (-2.83,2.82):
 cyl('Exposed axle',(x,-1.965,.77),(x,1.965,.77),.13,1,10)
 for y in (-1.65,1.65):
  torus('Iron wheel rim',(x,y,.77),.665,.105,1,(math.pi/2,0,0))
  cyl('Wheel hub',(x,y-.18,.77),(x,y+.18,.77),.18,8,10)
  for i in range(8):
   a=i*math.tau/8;beam('Wheel spoke',(x,y,.77),(x+.65*math.cos(a),y,.77+.65*math.sin(a)),.075,0)
# Broken-up bed boards leave the mechanical frame legible.
for y in (-1.58,1.58):
 for z in (1.69,2.05):box('Side board',(-1.43,y,z),(5.44,.13,.23),0)
 for x in (-4.00,-2.65,-1.30,.05,1.29):box('Stake', (x,y,1.91),(.12,.17,1.10),1)
for z in (1.69,2.05):box('Rear gate',(-4.18,0,z),(.20,3.30,.23),0)
# Short open cab canopy; broad dark covered-wagon shell is removed.
for x in (-.16,1.54):
 for y in (-1.37,1.37):box('Cab upright',(x,y,2.31),(.12,.12,1.68),0)
box('Cab canvas roof',(.69,0,3.20),(2.08,3.13,.13),4)
box('Bench seat',(.07,0,1.91),(.62,2.30,.24),0)
box('Bench back',(-.20,0,2.16),(.14,2.30,.53),0)
cyl('Hauler boiler',(1.75,0,2.15),(3.71,0,2.15),.57,1,16)
for x in (1.87,2.72,3.60):cyl('Boiler band',(x-.055,0,2.15),(x+.055,0,2.15),.60,8,16)
cyl('Exhaust stack',(2.91,0,2.63),(2.91,0,6.27),.15,1,12)
cyl('Stack flared cap',(2.91,0,6.25),(2.91,0,6.40),.25,1,12)
for y in (-.81,.81):
 cyl('Side feed pipe',(1.83,y,1.78),(3.52,y,1.78),.09,8,8)
 cyl('Feed elbow',(3.52,y,1.78),(3.52,y,2.10),.09,8,8)
box('Front bumper',(4.18,0,1.10),(.2555,3.55,.18),1)
for x,y in [(-3.16,-.63),(-2.02,.65),(-3.09,.65)]:
 box('Freight case',(x,y,1.98),(.92,1.02,1.02),0)
 for xx in (-.31,.31):box('Case iron strap',(x+xx,y,1.98),(.06,1.05,1.05),1)
commit_body(['open freight bed and cab canopy','spoked iron wheels and exposed axles','banded boiler and pipe feeds','separated cargo with iron straps'])

bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'long-road-landmarks.blend'))
c['blend']['sha256']=sha(PACK/'long-road-landmarks.blend')
(PACK/'long-road-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
