"""Native materials and wind-anchor fittings inside the frozen envelopes.
Run from game root with Blender --background --python this-file.
"""
from pathlib import Path
import bpy,math,json,hashlib
from mathutils import Vector
P=Path.cwd()/'assets/pilots/map-rebuild-spike'; S=Path(__file__).resolve().parent; PACK=P/'landmarks/devils-alley'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text());assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
atlas=bpy.data.images.load(str(P/'landmarks/devils-alley/devils-alley-landmarks-atlas.png'),check_existing=False);atlas.pack()
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
for stage,side in enumerate(['west','center','east']):
 rig=bpy.data.objects[side+'-wind-anchor'];mat=rig.data.materials[0];before=[tuple(v) for v in rig.bound_box];parts=[]
 oldtri=sum(len(f.vertices)-2 for f in rig.data.polygons);project(rig)
 # The pressure gauge is physically attached to the housing, not an emissive sign.
 cyl('Gauge housing',(0,-.65,1.61),(0,-.89,1.61),.25,1,12)
 cyl('Gauge face',(0,-.895,1.61),(0,-.91,1.61),.20,6,12)
 bpy.ops.mesh.primitive_torus_add(major_segments=16,minor_segments=4,major_radius=.223,minor_radius=.033,location=(0,-.92,1.61),rotation=(math.pi/2,0,0));finish(bpy.context.object,8)
 beam('Gauge pointer',(0,-.934,1.61),(.10,-.934,1.73),.026,1)
 for j in range(4):
  t=math.pi/4+j*math.tau/4;x,y=1.3*math.cos(t),.05+1.3*math.sin(t)
  cyl('Hex anchor bolt',(x,y,.40),(x,y,.48),.09,1,6)
 for z in (2.0,4.0+stage*.5):cyl('Spindle collar',(0,.05,z-.055),(0,.05,z+.055),.34,8,8)
 # Narrow bands read as real clamped metal at inspection scale.
 for z in (.51,1.36):cyl('Drive collar',(0,-1.10,z-.05),(0,-1.10,z+.05),.39,1,10)
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.join()
 for f in rig.data.polygons:f.material_index=0
 while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
 bpy.context.view_layer.update();assert [tuple(v) for v in rig.bound_box]==before,(rig.name,before,[tuple(v) for v in rig.bound_box])
 tri=sum(len(f.vertices)-2 for f in rig.data.polygons);assert tri<=3000,tri
 rig['fidelity_recipe']='sources/e9-devils-alley-fidelity-2/refine-wind-anchors.py';c['assets'][rig.name]['triangles']=tri
 c['assets'][rig.name]['artRevision']={'date':'2026-09-24','recipe':rig['fidelity_recipe'],'trianglesBefore':oldtri,'trianglesAfter':tri,'preserved':'source envelope, mounts, collision footprint and all original geometry','features':['physical UV proportions','native metal and stone surfaces','mounted pressure gauge','hex anchor bolts','spindle and drive collars']}
 print('WIND ANCHOR',rig.name,tri)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'devils-alley-landmarks.blend'))
for id in c['assets']:
 bpy.ops.object.select_all(action='DESELECT');o=bpy.data.objects[id];o.select_set(True);bpy.context.view_layer.objects.active=o
 target=PACK/(id+'.glb');bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True);c['assets'][id]['sha256']=sha(target)
c['blend']['sha256']=sha(PACK/'devils-alley-landmarks.blend');c['atlas']['sha256']=sha(P/'landmarks/devils-alley/devils-alley-landmarks-atlas.png');c['atlas']['provenance']='Native image_gen; sources/e9-devils-alley-fidelity-2/native-material-swatches-v2.png; sips resize 1024 square.'
(PACK/'devils-alley-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
