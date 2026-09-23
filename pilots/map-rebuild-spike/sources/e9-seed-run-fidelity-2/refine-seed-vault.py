"""Native materials and recessed seed-vault hardware inside the frozen envelope.
Run from game root with Blender --background --python this-file.
"""
from pathlib import Path
import bpy,math,json,hashlib
from mathutils import Vector
P=Path.cwd()/'assets/pilots/map-rebuild-spike'; S=Path(__file__).resolve().parent; PACK=P/'landmarks/seed-run'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text());assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
rig=bpy.data.objects['center-seed-vault'];mat=rig.data.materials[0];before=[tuple(v) for v in rig.bound_box]
atlas=bpy.data.images.load(str(P/'landmarks/seed-run/seed-run-landmarks-atlas.png'),check_existing=False);atlas.pack()
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
  cell=(8 if cell==10 else 1 if cell>=12 else cell) if role is None else cell
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
# A working door and layered face give the vault depth without moving its walls.
box('Vault steel door face',(0,-1.535,1.49),(1.08,.045,2.31),1)
for x in (-.70,.70):
 box('Brass door reveal',(x,-1.60,1.50),(.11,.17,2.61),8)
 for z in (.66,2.24):
  box('Door hinge leaf',(x*.84,-1.645,z),(.23,.065,.14),1)
  cyl('Hinge pin',(x*.84,-1.685,z-.09),(x*.84,-1.685,z+.09),.055,8,8)
box('Lintel drip cap',(0,-1.63,2.84),(1.57,.26,.14),8)
box('Threshold',(0,-1.65,.29),(1.53,.38,.14),2)
cyl('Door wheel axle',(0,-1.57,1.64),(0,-1.80,1.64),.13,1,12)
bpy.ops.mesh.primitive_torus_add(major_segments=16,minor_segments=4,major_radius=.33,minor_radius=.055,location=(0,-1.80,1.64),rotation=(math.pi/2,0,0));finish(bpy.context.object,8)
for i in range(4):
 t=i*math.tau/4
 beam('Door wheel spoke',(0,-1.80,1.64),(.33*math.cos(t),-1.80,1.64+.33*math.sin(t)),.055,8)
# Fluted sill panels and dark gasket slots stay behind the front canisters.
for side in (-1,1):
 for z in (.53,1.36,2.38):box('Facade raised panel',(side*1.30,-1.465,z),(1.08,.07,.055),8)
 for y in (-1.7,1.78):
  box('Post footing',(side*2.30,y,.30),(.45,.42,.16),2)
  box('Foot bearing',(side*2.30,y,.43),(.28,.28,.10),1)
# Paired glass sight windows distinguish storage contents from plain dark boards.
for x in (-1.28,1.28):
 box('Sight window frame',(x,-1.47,1.84),(.63,.095,.56),8)
 box('Sight window',(x,-1.525,1.84),(.45,.035,.39),4)
 beam('Window mullion',(x,-1.55,1.64),(x,-1.55,2.03),.035,1)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.join()
for f in rig.data.polygons:f.material_index=0
while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
bpy.context.view_layer.update();assert [tuple(v) for v in rig.bound_box]==before,(before,[tuple(v) for v in rig.bound_box])
tri=sum(len(f.vertices)-2 for f in rig.data.polygons);assert tri<=3000,tri
rig['fidelity_recipe']='sources/e9-seed-run-fidelity-2/refine-seed-vault.py';c['assets'][rig.name]['triangles']=tri
c['assets'][rig.name]['artRevision']={'date':'2026-09-24','recipe':rig['fidelity_recipe'],'trianglesBefore':2148,'trianglesAfter':tri,'preserved':'source envelope, mounts, collision footprint and all original geometry','features':['physical UV proportions','native surfaces','recessed door reveal and four-spoke handwheel','hinges and threshold','framed sight windows and post bearings']}
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'seed-run-landmarks.blend'))
for id in c['assets']:
 bpy.ops.object.select_all(action='DESELECT');o=bpy.data.objects[id];o.select_set(True);bpy.context.view_layer.objects.active=o
 target=PACK/(id+'.glb');bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True);c['assets'][id]['sha256']=sha(target)
c['blend']['sha256']=sha(PACK/'seed-run-landmarks.blend');c['atlas']['sha256']=sha(P/'landmarks/seed-run/seed-run-landmarks-atlas.png');c['atlas']['provenance']='Native image_gen; sources/e9-seed-run-fidelity-2/native-material-swatches-v2.png; sips resize 1024 square.'
(PACK/'seed-run-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n');print('SEED VAULT',tri)
