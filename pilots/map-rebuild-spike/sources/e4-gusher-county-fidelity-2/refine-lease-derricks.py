"""Rebuild eight existing lease derricks from frozen input, using original pixels.
Run with Blender from the game checkout. No new mounts or gameplay surfaces.
"""
from pathlib import Path
import bpy, json, hashlib, math
from mathutils import Vector

P=Path.cwd()/'assets/pilots/map-rebuild-spike'; S=Path(__file__).resolve().parent
PACK=P/'landmarks/gusher-county'; sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
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
 body['fidelity_recipe']='sources/e4-gusher-county-fidelity-2/refine-lease-derricks.py'
 bpy.ops.export_scene.gltf(filepath=str(PACK/(body.name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
 r=c['assets'][body.name];r['fidelityCorrection']={'recipe':body['fidelity_recipe'],'trianglesBefore':r['triangles'],'trianglesAfter':n,'features':features,'preserved':'exact bounds, atlas bytes, mount, collision footprint, inspection declarations'}
 r.update(triangles=n,sha256=sha(PACK/(body.name+'.glb')));print(body.name,n,bounds)

def torus(name,p,major,minor,role=1,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_segments=16,minor_segments=4,location=p,rotation=rotation,major_radius=major,minor_radius=minor);o=bpy.context.object;o.name=name;return finish(o,role)

# Each loop rebuilds one already mounted lease body. Pipes join only within that
# body's unchanged envelope: no inter-site network, channels or new colliders.
for j in range(1,9):
 name=f'derrick-{j:02d}';start(name)
 hx,hy,h=[c['assets'][name]['bounds']['max'][i] for i in range(3)]
 deck=h*.79;top=h-.12
 # Separated footing skids replace the continuous slab silhouette.
 for x in (-1.52,1.52):box('Stone skid',(x,0,.12),(.55,hy*2,.24),2)
 for y in (-1.62,1.62):box('Timber sill',(0,y,.32),(hx*2,.30,.25),0)
 for x in (-1.48,1.48):
  for y in (-1.39,1.39):
   beam('Tapered derrick leg',(x,y,.38),(x*.43,y*.43,deck),.20,0)
   box('Iron foot shoe',(x,y,.52),(.28,.28,.35),1)
 levels=3 if h>6 else 2
 for k in range(levels):
  z0=.49+(deck-.55)*k/levels;z1=.49+(deck-.55)*(k+1)/levels
  s0=1-.57*k/levels;s1=1-.57*(k+1)/levels
  for side in (-1,1):
   for a,b in [(-1,1),(1,-1)]:
    beam('Front cross brace',(a*1.48*s0,side*1.39*s0,z0),(b*1.48*s1,side*1.39*s1,z1),.105,0)
    beam('Side cross brace',(side*1.48*s0,a*1.39*s0,z0),(side*1.48*s1,b*1.39*s1,z1),.105,0)
  for side in (-1,1):
   beam('Front tie',(-1.48*s1,side*1.39*s1,z1),(1.48*s1,side*1.39*s1,z1),.12,0)
   beam('Side tie',(side*1.48*s1,-1.39*s1,z1),(side*1.48*s1,1.39*s1,z1),.12,0)
 box('Upper service landing',(0,0,deck),(1.78,1.70,.16),0)
 for x in (-.78,.78):
  for y in (-.74,.74):box('Top rail upright',(x,y,deck+.39),(.08,.08,.76),1)
  beam('Top side rail',(x,-.74,deck+.77),(x,.74,deck+.77),.08,1)
 for y in (-.74,.74):beam('Top front rail',(-.78,y,deck+.77),(.78,y,deck+.77),.08,1)
 cyl('Central drill pipe',(0,0,.70),(0,0,h),.11,1,10)
 # A side winch and visible feed riser provide legible mechanical use.
 winch_x=(-1 if j%2 else 1)*1.10
 cyl('Winch drum',(winch_x,-.48,1.03),(winch_x,.48,1.03),.38,1,12)
 for y in (-.52,.52):cyl('Winch flange',(winch_x,y-.045,1.03),(winch_x,y+.045,1.03),.44,8,12)
 cyl('Hanging cable',(winch_x,0,1.12),(0,0,deck-.20),.022,1,6)
 # Closed manifold: left return -> front header -> right riser -> central well.
 points=[(-2.06,.25,.62),(-2.06,-1.74,.62),(2.08,-1.74,.62),(2.08,.16,.62),(2.08,.16,1.68),(.35,.16,1.68),(.35,.16,.74),(0,.16,.74)]
 for a,b in zip(points,points[1:]):cyl('Connected passive feed pipe',a,b,.19,2,12)
 for x in (-1.10,.10,1.26):
  cyl('Header coupling',(x-.07,-1.74,.62),(x+.07,-1.74,.62),.25,8,12)
  box('Pipe support',(x,-1.74,.30),(.25,.28,.53),2)
  for a in (0,math.pi/2,math.pi,3*math.pi/2):
   yy=-1.74+.20*math.cos(a);zz=.62+.20*math.sin(a)
   cyl('Flange bolt',(x-.09,yy,zz),(x+.09,yy,zz),.035,1,5)
 cyl('Valve stem',(1.22,-1.74,.64),(1.22,-1.74,1.23),.075,8,8)
 torus('Valve handwheel',(1.22,-1.74,1.26),.29,.045,4)
 for a in (0,math.pi/2):beam('Valve spoke',(1.22-.25*math.cos(a),-1.74-.25*math.sin(a),1.26),(1.22+.25*math.cos(a),-1.74+.25*math.sin(a),1.26),.045,1)
 cyl('Gauge neck',(-1.62,-1.74,.64),(-1.62,-1.74,1.69),.065,8,8)
 cyl('Gauge rim',(-1.62,-1.86,1.88),(-1.62,-1.68,1.88),.26,1,12)
 cyl('Gauge pale face',(-1.62,-1.865,1.88),(-1.62,-1.86,1.88),.21,6,12)
 beam('Gauge hand',(-1.62,-1.87,1.88),(-1.74,-1.87,2.01),.025,1)
 # One small hooped service vessel, alternated between the lease variants.
 x=(-1 if j%2 else 1)*2.04;y=.94
 cyl('Service vessel',(x,y,.40),(x,y,1.46),.38,0,12)
 for z in (.54,1.30):cyl('Vessel hoop',(x,y,z-.04),(x,y,z+.04),.41,1,12)
 wheel_x=2.04 if j%2 else -2.04
 torus('Exposed drive flywheel',(wheel_x,-.72,1.18),.42,.065,2,(math.pi/2,0,0))
 cyl('Drive hub',(wheel_x,-.90,1.18),(wheel_x,-.53,1.18),.13,8,10)
 for k in range(6):
  a=k*math.tau/6;beam('Drive spoke',(wheel_x,-.72,1.18),(wheel_x+.39*math.cos(a),-.72,1.18+.39*math.sin(a)),.065,2)
 cyl('Winch drive feed',(wheel_x,-.54,1.18),(wheel_x,.26,1.18),.10,1,10)
 commit_body(['tapered timber lattice with upper safety rail','connected local header and return pipes','couplings, supports, passive valve and gauge','exposed spoked flywheel, bolted flanges and alternating side winch/service vessel'])

bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'gusher-county-landmarks.blend'))
c['blend']['sha256']=sha(PACK/'gusher-county-landmarks.blend')
(PACK/'gusher-county-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
