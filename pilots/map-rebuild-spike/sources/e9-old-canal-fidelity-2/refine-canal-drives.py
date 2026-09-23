"""Native materials and supported canal drives inside the frozen envelopes.
Run from game root with Blender --background --python this-file.
"""
from pathlib import Path
import bpy,math,json,hashlib
from mathutils import Vector
P=Path.cwd()/'assets/pilots/map-rebuild-spike'; S=Path(__file__).resolve().parent; PACK=P/'landmarks/old-canal'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text());assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
atlas=bpy.data.images.load(str(P/'landmarks/old-canal/old-canal-landmarks-atlas.png'),check_existing=False);atlas.pack()
for m in bpy.data.materials:
 if m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE':n.image=atlas
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

def finish(o,role):
 bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(mat);o.data.update();project(o,role);parts.append(o);return o
def box(name,p,size,role=2):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;return finish(o,role)
def beam(name,a,b,w,role=1):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cube_add(size=1,location=(a+b)/2);o=bpy.context.object;o.name=name;o.scale=(w,w,(b-a).length);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return finish(o,role)
def cyl(name,a,b,r,role=8,n=12):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return finish(o,role)
for letter in ['a','b','c']:
 rig=bpy.data.objects['canal-segment-'+letter+'-marker'];mat=rig.data.materials[0];before=[tuple(v) for v in rig.bound_box];parts=[]
 oldtri=sum(len(f.vertices)-2 for f in rig.data.polygons)
 # Locate the two authored colored wheels in the frozen mesh. Their centers,
 # radii and all original geometry stay exact; connected hardware explains them.
 parent=list(range(len(rig.data.vertices)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for f in rig.data.polygons:
  for i in f.vertices:parent[root(i)]=root(f.vertices[0])
 groups={}
 for v in rig.data.vertices:groups.setdefault(root(v.index),[]).append(v.co.copy())
 wheels=[]
 for vs in groups.values():
  lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
  if len(vs)==48 and lo[2]>3 and hi[0]-lo[0]>1:wheels.append([(a+b)/2 for a,b in zip(lo,hi)])
 assert len(wheels)==2,(rig.name,wheels)
 project(rig)
 level=sum(v[2] for v in wheels)/2
 cyl('Central drive column',(0,.20,.29),(0,.20,level+.44),.19,1,12)
 box('Column foot',(0,.20,.33),(.74,.70,.26),2)
 box('Column bearing seat',(0,.20,.60),(.43,.43,.22),8)
 beam('Upper cross shaft',(wheels[0][0],.20,level),(wheels[1][0],.20,level),.16,1)
 for cx,cy,cz in wheels:
  cyl('Wheel spindle',(cx,cy-.15,cz),(cx,.43,cz),.12,1,12)
  cyl('Wheel bearing',(cx,.05,cz),(cx,.33,cz),.24,8,12)
  for j in range(6):
   t=j*math.tau/6;beam('Wheel spoke',(cx,cy,cz),(cx+.57*math.cos(t),cy,cz+.57*math.sin(t)),.055,8)
  # A return bracket joins the upper assembly to the already grounded handwinch.
  lower=-2.4 if cx<0 else 2.4
  beam('Return bracket',(lower,.45,2.8),(cx,.20,cz),.14,1)
  for z in (2.78,cz):
   box('Bearing mount',(lower if z==2.78 else cx,.30,z),(.36,.30,.22),8)
  for y in (-.30,.45):
   box('Pedestal course',(lower,y,.33),(.68,.44,.18),2)
   box('Pedestal cap',(lower,y,.46),(.55,.39,.08),8)
 # Fine collars articulate the central vertical shaft and upper cross-drive.
 for z in (1.10,2.72,level-.20,level+.30):cyl('Shaft collar',(0,.20,z-.07),(0,.20,z+.07),.26,8,10)
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.join()
 for f in rig.data.polygons:f.material_index=0
 while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
 bpy.context.view_layer.update();assert [tuple(v) for v in rig.bound_box]==before,(rig.name,before,[tuple(v) for v in rig.bound_box])
 tri=sum(len(f.vertices)-2 for f in rig.data.polygons);assert tri<=3000,tri
 rig['fidelity_recipe']='sources/e9-old-canal-fidelity-2/refine-canal-drives.py';c['assets'][rig.name]['triangles']=tri
 c['assets'][rig.name]['artRevision']={'date':'2026-09-24','recipe':rig['fidelity_recipe'],'trianglesBefore':oldtri,'trianglesAfter':tri,'preserved':'source envelope, wheel centers, mounts, collision footprint and all original geometry','features':['physical UV proportions','native metal and masonry surfaces','grounded central drive and bearing seat','upper wheel spokes and bearing housings','return brackets join the handwinches','stepped pedestal feet and shaft collars']}
 print('CANAL DRIVE',rig.name,tri)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'old-canal-landmarks.blend'))
for id in c['assets']:
 bpy.ops.object.select_all(action='DESELECT');o=bpy.data.objects[id];o.select_set(True);bpy.context.view_layer.objects.active=o
 target=PACK/(id+'.glb');bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True);c['assets'][id]['sha256']=sha(target)
c['blend']['sha256']=sha(PACK/'old-canal-landmarks.blend');c['atlas']['sha256']=sha(P/'landmarks/old-canal/old-canal-landmarks-atlas.png');c['atlas']['provenance']='Native image_gen; sources/e9-old-canal-fidelity-2/native-material-swatches-v2.png; sips resize 1024 square.'
(PACK/'old-canal-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
