"""Architectural clock gate, same mount/envelope and unobstructed passage.
Blender from game root. Frozen source input; original atlas pixels only.
"""
from pathlib import Path
import bpy,math,json,hashlib
from mathutils import Vector
P=Path.cwd()/'assets/pilots/map-rebuild-spike';S=Path(__file__).resolve().parent;PACK=P/'landmarks/half-life-hollow'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text());assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
body=bpy.data.objects['south-countdown-gate'];material=body.data.materials[0];parts=[]
old_bounds=[(min(v.co[i] for v in body.data.vertices),max(v.co[i] for v in body.data.vertices)) for i in range(3)]
def finish(o,role):
 o.data.materials.append(material);uv=o.data.uv_layers.active or o.data.uv_layers.new();uv.name='LandmarkAtlasUV'
 row,col=divmod(role,4)
 # Sample a small engraved patch rather than stretching an entire prop portrait.
 for v in uv.data:v.uv=((col+.32+v.uv.x*.17)/4,(row+.40+v.uv.y*.17)/4)
 parts.append(o);return o
def box(name,p,size,role=8):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;return finish(o,role)
def cyl(name,a,b,r,role=8,n=16):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return finish(o,role)
def beam(name,a,b,w,role=8):
 a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,w,(b-a).length),role);o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return o
def ring(name,p,r,t,role=8,n=32):
 bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=4,major_radius=r,minor_radius=t,location=p,rotation=(math.pi/2,0,0));o=bpy.context.object;o.name=name;return finish(o,role)
# Source Z-up. Side piers stay at the old feet, and the center remains open.
for x in (-4.0,4.0):
 box('Dressed stone footing',(x,0,.28),(1.70,2.49,.56),10)
 box('Stepped pier plinth',(x,0,.67),(1.46,1.90,.24),8)
 box('Recessed pier core',(x,0,3.73),(1.13,1.43,5.88),6)
 for z in (1.0,2.40,3.80,5.20,6.58):box('Pier course',(x,0,z),(1.31,1.62,.16),8)
 for dx in (-.46,.46):box('Raised pilaster',(x+dx,-.78,3.76),(.14,.14,5.74),8)
 box('Pier capital',(x,0,6.94),(1.58,1.85,.42),8)
 cyl('Capped pier lantern',(x,0,7.17),(x,0,7.90),.29,5,12)
 cyl('Lantern foot',(x,0,7.14),(x,0,7.29),.43,8,12)
 cyl('Lantern crown',(x,0,7.90),(x,0,8.04),.43,8,12)
 for dx,dy in [(-.23,-.23),(.23,-.23),(-.23,.23),(.23,.23)]:beam('Lantern cage',(x+dx,dy,7.25),(x+dx,dy,7.94),.045,8)
# Layered arch ribs meet the capitals; no detached hoop or crossing-state cue.
for y in (-.48,.48):
 for i in range(12):
  x0=-3.9+7.8*i/12;x1=-3.9+7.8*(i+1)/12
  z0=6.98+1.93*(1-(x0/3.9)**2);z1=6.98+1.93*(1-(x1/3.9)**2)
  beam('Segmented arch rib',(x0,y,z0),(x1,y,z1),.19,8)
box('Clock housing',(0,0,6.66),(4.74,.68,4.32),0)
for x in (-2.34,2.34):box('Dial housing stile',(x,-.43,6.68),(.18,.23,4.35),8)
for z in (4.50,8.84):box('Dial housing cornice',(0,-.43,z),(4.90,.23,.17),8)
# Complete face with concentric brass bezel, engraved tick marks and fixed hands.
cyl('Dark recessed dial',(0,-.38,6.68),(0,-.57,6.68),1.92,10,32)
ring('Outer clock bezel',(0,-.61,6.68),1.95,.13,8)
ring('Inner clock bezel',(0,-.68,6.68),1.60,.045,8)
for i in range(12):
 a=i*math.tau/12;r0=1.43 if i%3==0 else 1.51;r1=1.73
 beam('Engraved hour mark',(r0*math.sin(a),-.70,6.68+r0*math.cos(a)),(r1*math.sin(a),-.70,6.68+r1*math.cos(a)),.065,8)
beam('Minute hand',(0,-.78,6.68),(.72,-.78,7.74),.08,9)
beam('Hour hand',(0,-.81,6.68),(-.79,-.81,6.31),.10,9)
cyl('Clock pin',(0,-.76,6.68),(0,-.87,6.68),.16,8,12)
for x in (-2.12,2.12):
 for z in (4.75,8.61):cyl('Housing bolt',(x,-.55,z),(x,-.68,z),.10,8,8)
# Knees carry the housing without closing the old clear center passage.
for s in (-1,1):beam('Arch support knee',(s*3.40,0,5.07),(s*2.45,0,6.24),.22,8)
old=body.data;body.data=bpy.data.meshes.new('CountdownGateFidelity');bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();bpy.data.meshes.remove(old)
for i,(lo,hi) in enumerate(old_bounds):
 a=min(v.co[i] for v in body.data.vertices);b=max(v.co[i] for v in body.data.vertices)
 for v in body.data.vertices:v.co[i]=lo+(v.co[i]-a)*(hi-lo)/(b-a)
bpy.context.view_layer.update();n=sum(len(f.vertices)-2 for f in body.data.polygons);assert n<=3000,n
body['fidelity_recipe']='sources/e6-half-life-hollow-fidelity-2/refine-countdown-gate.py'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'half-life-hollow-landmarks.blend'))
bpy.ops.export_scene.gltf(filepath=str(PACK/'south-countdown-gate.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
c['blend']['sha256']=sha(PACK/'half-life-hollow-landmarks.blend');r=c['assets']['south-countdown-gate'];r.update(triangles=n,sha256=sha(PACK/'south-countdown-gate.glb'))
r['fidelityCorrection']={'recipe':body['fidelity_recipe'],'trianglesBefore':508,'trianglesAfter':n,'features':['stepped masonry piers and pilasters','double arch ribs and support knees','recessed framed dial with layered bezel','caged lanterns and engraved hour marks'],'preserved':'exact source envelope, atlas pixels, mount, clear passage, inspection station, collision and all sibling bodies'}
(PACK/'half-life-hollow-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n');print('COUNTDOWN',n)
