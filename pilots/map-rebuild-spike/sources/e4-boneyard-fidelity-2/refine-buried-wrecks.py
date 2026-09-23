"""Rebuild three existing salvage bodies from frozen input, using original pixels.
Run with Blender from the game checkout. No new mounts or gameplay surfaces.
"""
from pathlib import Path
import bpy, json, hashlib, math
from mathutils import Vector

P=Path.cwd()/'assets/pilots/map-rebuild-spike'; S=Path(__file__).resolve().parent
PACK=P/'landmarks/boneyard'; sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text())
assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
parts=[]; body=None; material=None
# Soil uses the renderer's existing Motor-earth pigment, in linear RGB. It is
# non-emissive matte geometry; no new bitmap, shader, terrain height or mask.
earth=bpy.data.materials.new('BoneyardDriftEarth');earth.use_nodes=True
principled=earth.node_tree.nodes.get('Principled BSDF')
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
principled.inputs['Base Color'].default_value=(*[linear(v/255) for v in (159,133,100)],1)
principled.inputs['Roughness'].default_value=1
principled.inputs['Metallic'].default_value=0
def finish(o,role):
 o.data.materials.clear();o.data.materials.append(material)
 uv=o.data.uv_layers.active or o.data.uv_layers.new();uv.name='LandmarkAtlasUV'
 row,col=divmod(role,4)
 # Restrict each primitive to a quieter part of the original swatch. Geometry
 # carries seams/hoops, rather than enlarging the atlas's miniature buildings.
 for v in uv.data:
  v.uv=((col+.25+v.uv.x*.28)/4,(row+.62+v.uv.y*.28)/4) if role in (0,2,3,6) else ((col+.48+v.uv.x*.055)/4,(row+.48+v.uv.y*.055)/4)
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
 body['fidelity_recipe']='sources/e4-boneyard-fidelity-2/refine-buried-wrecks.py'
 bpy.ops.export_scene.gltf(filepath=str(PACK/(body.name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
 r=c['assets'][body.name];r['fidelityCorrection']={'recipe':body['fidelity_recipe'],'trianglesBefore':r['triangles'],'trianglesAfter':n,'features':features,'preserved':'exact bounds, atlas bytes, mount, collision footprint, inspection declarations'}
 r.update(triangles=n,meshCount=2,materialCount=2,sha256=sha(PACK/(body.name+'.glb')));print(body.name,n,bounds)

def torus(name,p,major,minor,role=1,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_segments=16,minor_segments=4,location=p,rotation=rotation,major_radius=major,minor_radius=minor);o=bpy.context.object;o.name=name;return finish(o,role)

def soil(name,hx,hy,height):
 # Three uneven closed rings: low outer perimeter, buried wheel line, soft crown.
 n=16;verts=[]
 for ring in range(3):
  for i in range(n):
   a=i*math.tau/n;rr=(1,.76,.32)[ring]*((1 if i%4==0 else .90+.06*math.sin(i*2.1)) if ring==0 else 1+.09*math.sin(i*2.1))
   z=0 if ring==0 else height*(.74 if ring==1 else 1)*(.85+.15*math.sin(i*1.7))
   verts.append((hx*math.cos(a)*rr,hy*math.sin(a)*rr,z))
 verts.append((0,0,height*.92));faces=[]
 for ring in range(2):
  for i in range(n):faces.append((ring*n+i,ring*n+(i+1)%n,(ring+1)*n+(i+1)%n,(ring+1)*n+i))
 for i in range(n):faces.append((2*n+i,2*n+(i+1)%n,3*n))
 faces.append(tuple(reversed(range(n))))
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 uv=me.uv_layers.new()
 for f in me.polygons:
  for li in f.loop_indices:
   co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co.x/(2*hx)+.5,co.y/(2*hy)+.5)
 for f in me.polygons:f.use_smooth=True
 finish(o,6);o.data.materials.clear();o.data.materials.append(earth);return o
def wheel(x,y,z,r,spokes=6):
 torus('Corroded wheel rim',(x,y,z),r*.88,r*.12,2,(math.pi/2,0,0))
 cyl('Iron wheel hub',(x,y-.11,z),(x,y+.11,z),r*.20,1,10)
 for i in range(spokes):
  a=i*math.tau/spokes;beam('Wheel spoke',(x,y,z),(x+r*.82*math.cos(a),y,z+r*.82*math.sin(a)),.075,2)
def bolted_ring(x,z,r):
 cyl('Raised boiler seam',(x-.045,0,z),(x+.045,0,z),r,1,16)
 for i in range(8):
  a=i*math.tau/8;cyl('Seam rivet',(x-.055,r*math.cos(a),z+r*math.sin(a)),(x+.055,r*math.cos(a),z+r*math.sin(a)),.035,2,5)

start('half-buried-sleeper')
# Sink the visible machinery into authored soil, without moving its mount/height.
soil('Continuous windblown burial',4.9011,2.7439,1.60)
box('Exposed broken chassis',(-.12,0,.93),(8.34,2.61,.22),1)
for x in (-2.65,-.38,1.89):
 for y in (-1.52,1.52):wheel(x,y,.89,.83)
cyl('Weathered pressure shell',(-3.52,0,1.96),(2.58,0,1.96),1.13,6,24)
for x in (-3.46,-1.44,.53,2.50):bolted_ring(x,1.96,1.15)
cyl('Circular smokebox face',(-3.65,0,1.96),(-3.53,0,1.96),1.05,1,24)
cyl('Inset access door',(-3.72,0,1.96),(-3.65,0,1.96),.61,2,16)
beam('Door cross handle',(-3.74,-.28,1.96),(-3.74,.28,1.96),.07,1)
# Stack kept inside the original maximum; no rear upright reaching the HUD.
cyl('Tapered-looking stack collar',(-2.18,0,2.96),(-2.18,0,3.18),.32,1,12)
cyl('Broken chimney',(-2.18,0,3.10),(-2.18,0,5.04),.22,2,12)
cyl('Chimney rim',(-2.18,0,5.03),(-2.18,0,5.1372),.30,1,12)
for y in (-1.30,1.30):
 cyl('Side pressure pipe',(-2.90,y,1.66),(1.62,y,1.66),.085,2,10)
 cyl('Pressure elbow',(1.62,y,1.66),(1.62,y,2.28),.085,2,10)
 beam('Dull drive linkage',(-2.65,y*1.22,.94),(1.89,y*1.22,.94),.10,2)
box('Collapsed cab floor',(3.47,0,1.05),(1.46,2.69,.14),0)
for y in (-1.15,1.15):
 beam('Broken cab upright',(2.89,y,1.12),(3.20,y,2.84),.13,1)
 beam('Collapsed roof spar',(3.20,y,2.84),(4.27,y*.76,1.36),.12,1)
# Rusted sheet fragments break up the barrel's uniform finish without a new atlas.
for x,y,z,ang in [(-2.38,-.90,2.55,.15),(.10,.92,2.50,-.14),(1.48,-.90,2.57,.12)]:
 o=box('Oxidized repair plate',(x,y,z),(.62,.065,.45),3);o.rotation_euler.x=ang
commit_body(['riveted weathered metal shell and inset front door','dull drive rods and pressure pipes','buried lower wheels in continuous uneven soil','collapsed cab frame and oxidized repair plates'])

for name,variant in [('flivver-row-west-b',0),('flivver-row-east-b',1)]:
 start(name);hx,hy,h=c['assets'][name]['bounds']['max']
 soil('Drifted salvage footing',hx,hy,.57)
 box('Salvage chassis',(0,0,.70),(hx*1.82,hy*1.40,.18),1)
 for x in (-hx*.68,hx*.68):
  for y in (-hy*.79,hy*.79):wheel(x,y,.60,.55,6)
 if variant==0:
  cyl('Stripped small boiler',(-1.89,0,1.18),(.67,0,1.18),.59,6,16)
  for x in (-1.81,-.59,.59):cyl('Boiler strap',(x-.04,0,1.18),(x+.04,0,1.18),.61,1,12)
  cyl('Short flivver stack',(-1.15,0,1.70),(-1.15,0,h),.13,2,10)
  for y in (-.92,.92):beam('Exposed cab frame',(.95,y,.80),(1.11,y,2.25),.11,1)
  beam('Broken canopy',(.98,-.92,2.21),(1.87,.57,1.48),.12,0)
 else:
  cyl('Toppled cylindrical reserve',(-1.42,-.15,1.23),(1.44,.33,1.64),.74,3,16)
  cyl('Exposed end hatch',(-1.52,-.17,1.22),(-1.43,-.15,1.23),.59,2,16)
  beam('Leaning exhaust',(.12,.15,1.83),(.65,.25,h-.09),.18,1)
  box('Broken cargo board',(-2.15,.18,1.04),(.73,1.93,.10),0)
 for y in (-1.02,1.02):cyl('Visible loose pipe',(-1.70,y,.82),(1.90,y,1.04),.065,2,8)
 commit_body(['two distinct stripped salvage silhouettes','spoked wheels partly covered by drift','weathered metal with exposed frames and pipes'])

bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'boneyard-landmarks.blend'))
c['blend']['sha256']=sha(PACK/'boneyard-landmarks.blend')
(PACK/'boneyard-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
