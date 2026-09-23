"""Native masonry and supported wheel hardware inside the frozen lock envelope.
Run from game root with Blender --background --python this-file.
"""
from pathlib import Path
import bpy,math,json,hashlib
from mathutils import Vector
P=Path.cwd()/'assets/pilots/map-rebuild-spike'; S=Path(__file__).resolve().parent; PACK=P/'landmarks/dome-basin'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text());assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
rig=bpy.data.objects['canal-gate-works'];mat=rig.data.materials[0];before=[tuple(v) for v in rig.bound_box]
atlas=bpy.data.images.load(str(P/'landmarks/dome-basin/dome-basin-landmarks-atlas.png'),check_existing=False);atlas.pack()
for m in bpy.data.materials:
 if m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE':n.image=atlas
# Physical surface projection preserves aspect ratio; long faces use proportionally
# less tile height instead of stretching a square over a narrow pier or apron.
def project(o,role=None):
 uv=o.data.uv_layers.active or o.data.uv_layers.new(name='LandmarkAtlasUV');uv.name='LandmarkAtlasUV'
 for f in o.data.polygons:
  old=uv.data[f.loop_start].uv;cell=role if role is not None else min(15,int(old.y*4)*4+int(old.x*4))
  row,col=divmod(cell,4);axes=[i for i in range(3) if i!=max(range(3),key=lambda i:abs(f.normal[i]))]
  vs=[o.data.vertices[i].co for i in f.vertices];mid=[(min(v[a] for v in vs)+max(v[a] for v in vs))/2 for a in axes]
  scale=max(3.0,*[max(v[a] for v in vs)-min(v[a] for v in vs) for a in axes])
  for li in f.loop_indices:
   v=o.data.vertices[o.data.loops[li].vertex_index].co
   uv.data[li].uv=((col+.5+(v[axes[0]]-mid[0])*.80/scale)/4,(row+.5+(v[axes[1]]-mid[1])*.80/scale)/4)
project(rig);parts=[]
def finish(o,role):
 bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(mat);o.data.update();project(o,role);parts.append(o);return o
def box(name,p,size,role=2):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;return finish(o,role)
def beam(name,a,b,w,role=1):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cube_add(size=1,location=(a+b)/2);o=bpy.context.object;o.name=name;o.scale=(w,w,(b-a).length);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return finish(o,role)
def cyl(name,a,b,r,role=8,n=12):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return finish(o,role)
# Wheel pedestals step into their existing shoes, with dark bearing joints.
for y in (-.65,.85):
 box('Wheel plinth',(-3.7,y,.26),(1.22,.57,.30),2)
 box('Wheel pedestal',(-3.7,y,1.04),(.58,.45,1.42),2)
 box('Pedestal bearing seat',(-3.7,y,1.76),(.79,.65,.22),1)
 cyl('Axle bearing flange',(-3.7,y-.18,1.83),(-3.7,y-.30,1.83),.35,8,16)
 cyl('Axle bearing collar',(-3.7,y-.30,1.83),(-3.7,y-.38,1.83),.23,1,12)
 for x in (-3.96,-3.44):
  cyl('Bearing seat bolt',(x,y-.21,1.84),(x,y-.21,1.94),.065,8,6)
 beam('Pedestal brace',(-4.19,y,.35),(-3.70,y,1.50),.12,1)
# Narrow architectural pier shoes/cornices and connected railwork; the center
# remains an open nonblocking crossing, never an invented closed gate chamber.
for x in (-1.5,2.25):
 box('Pier contact plinth',(x,.25,.21),(1.06,1.15,.22),2)
 box('Pier lower band',(x,.25,.47),(.80,.86,.15),1)
 for z in (.64,1.13,1.62,2.11):box('Pier course seam',(x,.25,z),(.76,.82,.055),2)
 box('Pier capital',(x,.25,2.72),(.90,1.02,.18),8)
for x in (-5.25,-1.95,3.2,5.2):
 box('Apron socket',(x,.78,.19),(.38,.34,.17),2)
 beam('Low guard post',(x,.78,.20),(x,.78,.85),.08,1)
for a,b in [(-5.25,-1.95),(3.2,5.2)]:beam('Joined low guard rail',(a,.78,.79),(b,.78,.79),.07,8)
# Exposed drive housing joins the original spindle at x=-1.8.
box('Drive bearing housing',(-1.84,1.05,1.83),(.36,.41,.48),1)
cyl('Drive housing cap',(-2.07,1.05,1.83),(-2.12,1.05,1.83),.20,8,12)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.join()
for f in rig.data.polygons:f.material_index=0
while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
bpy.context.view_layer.update();assert [tuple(v) for v in rig.bound_box]==before,(before,[tuple(v) for v in rig.bound_box])
tri=sum(len(f.vertices)-2 for f in rig.data.polygons);assert tri<=3000,tri
rig['fidelity_recipe']='sources/e9-dome-basin-fidelity-2/refine-lock-works.py';c['assets'][rig.name]['triangles']=tri
c['assets'][rig.name]['artRevision']={'date':'2026-09-24','recipe':rig['fidelity_recipe'],'trianglesBefore':1580,'trianglesAfter':tri,'preserved':'source envelope, mounts, nonblocking crossing and all original geometry','features':['physical surface UV scale','native masonry and metals','stepped wheel pedestals and bearing flanges','pier courses and contact plinths','connected apron railwork']}
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'dome-basin-landmarks.blend'))
for id in c['assets']:
 bpy.ops.object.select_all(action='DESELECT');o=bpy.data.objects[id];o.select_set(True);bpy.context.view_layer.objects.active=o
 target=PACK/(id+'.glb');bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True);c['assets'][id]['sha256']=sha(target)
c['blend']['sha256']=sha(PACK/'dome-basin-landmarks.blend');c['atlas']['sha256']=sha(P/'landmarks/dome-basin/dome-basin-landmarks-atlas.png');c['atlas']['provenance']='Native image_gen; sources/e9-dome-basin-fidelity-2/native-material-swatches-v2.png; sips resize 1024 square.'
(PACK/'dome-basin-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n');print('LOCK WORKS',tri)
