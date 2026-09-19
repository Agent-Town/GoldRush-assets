"""Rebuild Ember's concept-derived vent and repack its shared native material atlas."""
from pathlib import Path
import argparse,bpy,importlib.util,json,math,sys,hashlib
ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=args.out.resolve();OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'assets/pilots/map-rebuild-spike/landmarks/ember-shore'
RAW=ROOT/'assets/raw/ember-shore-landmark-material-atlas-v1.png'
spec=importlib.util.spec_from_file_location('factory',ROOT/'assets/pilots/map-rebuild-spike/build_landmark_packs.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
f.PACKS.setdefault('ember-shore',{'era':10})
f.ROLE_INDEX['edge_brass']=13
contract=json.loads((SOURCE/'ember-shore-landmark-pack-contract.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'ember-shore-landmarks.blend'))
snapshot=lambda o:([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[tuple(u.uv) for u in o.data.uv_layers.active.data])
before={o.name:snapshot(o) for o in bpy.data.objects if o.type=='MESH' and o.name=='cooled-titan-shelf'}
for identifier in ['last-warm-vent-altar','west-vein-cooling-marker','center-vein-bridge-school','shore-preserve-rack']:
 old=bpy.data.objects[identifier];oldmesh=old.data;bpy.data.objects.remove(old,do_unlink=True)
 if oldmesh.users==0:bpy.data.meshes.remove(oldmesh)
image=bpy.data.images.load(str(RAW),check_existing=False);image.scale(1024,1024)
atlas=OUT/'ember-shore-landmarks-atlas.png';image.filepath_raw=str(atlas);image.file_format='PNG';image.save();image.pack()
material=f.make_material('EmberShore',image)
p=[]
def box(n,loc,size,role='brass',rotation=0):
 o=f.add_box(n,loc,size,role,rotation);p.append(o);return o
def cyl(n,a,b,r,role='brass',v=10):
 o=f.add_cylinder(n,a,b,r,role,v);p.append(o);return o
def rock(n,loc,size,role='stone'):
 o=f.add_rock(n,loc,size,role);p.append(o);return o
# Enclosed brass lantern, from the contract plate's preserve fixture.
box('stone-footing',(0,0,0),(2.8,2.8,.22),'stone')
box('brass-base',(0,0,.22),(2.45,2.45,.18),'brass')
cyl('vent-body',(0,0,.4),(0,0,1.5),.76,'iron',16)
for z in [.43,.75,1.35]:cyl('brass-body-band',(0,0,z),(0,0,z+.13),.80,'brass',16)
cyl('amber-window',(0,0,1.50),(0,0,2.48),.68,'water',16)
for j in range(8):
 angle=2*math.pi*j/8;x=.70*math.cos(angle);y=.70*math.sin(angle)
 cyl('window-cage-post',(x,y,1.48),(x,y,2.53),.055,'brass',6)
for z in [1.48,2.45]:cyl('window-rim',(0,0,z),(0,0,z+.13),.80,'brass',16)
cyl('vent-lid',(0,0,2.58),(0,0,2.72),.76,'brass',16)
cyl('lid-boss',(0,0,2.72),(0,0,2.91),.20,'iron',10)
for side in [-1,1]:
 cyl('return-pipe',(side*.95,0,.35),(side*.95,0,1.05),.095,'brass',8)
 cyl('pipe-elbow',(side*.95,0,1.05),(side*.70,0,1.05),.095,'brass',8)
def component_uv(obj,role):
 mesh=obj.data
 while mesh.uv_layers:mesh.uv_layers.remove(mesh.uv_layers[0])
 uv=mesh.uv_layers.new(name='LandmarkAtlasUV').data
 low=[min(v.co[a] for v in mesh.vertices) for a in range(3)]
 span=max(max(v.co[a] for v in mesh.vertices)-low[a] for a in range(3))
 row,col=divmod(f.ROLE_INDEX[role],4)
 for face in mesh.polygons:
  face.material_index=0
  axis=max(range(3),key=lambda a:abs(face.normal[a]));a,b=[a for a in range(3) if a!=axis]
  for i in face.loop_indices:
   co=mesh.vertices[mesh.loops[i].vertex_index].co
   uv[i].uv=((col+.08+(co[a]-low[a])/span*.84)/4,(row+.08+(co[b]-low[b])/span*.84)/4)
f.map_uv=component_uv
def finish(identifier):
 asset=f.finish_asset(p,identifier,material,'ember-shore',{'tier':'derive'})
 record=contract['assets'][identifier]
 bounds=f.glb_bounds(asset)
 assert all(bounds['max'][i]-bounds['min'][i] <= record['bounds']['max'][i]-record['bounds']['min'][i]+.001 for i in range(3)), identifier
 record.update(sourceTier='derive',sources=['assets/raw/plate-contract-e10-ember-shore.png'],triangles=sum(len(poly.vertices)-2 for poly in asset.data.polygons),bounds=f.glb_bounds(asset))
 assert record['triangles']<=record['triangleBudget']
 p.clear()
 return asset
finish('last-warm-vent-altar')
# West cabinet: a low enclosed salvage console, not a marker tower.
box('cabinet-foot',(0,0,0),(2.9,2.1,.18),'stone')
for x in [-1.05,1.05]:box('cabinet-foot-rail',(x,0,.18),(.22,1.8,.22),'iron')
box('cabinet-housing',(0,0,.4),(2.6,1.5,1.25),'iron')
box('cabinet-lid',(0,0,1.65),(2.8,1.65,.15),'brass')
box('cabinet-recess',(0,-.77,.68),(2.13,.08,.61),'soot')
for x in [-.70,0,.70]:
 box('cabinet-front-panel',(x,-.83,.73),(.62,.06,.30),'brass')
 cyl('cabinet-dial',(x,-.88,1.02),(x,-.99,1.02),.15,'iron',10)
box('cabinet-window-recess',(0,-.84,1.08),(1.98,.08,.26),'soot')
for side in [-1,1]:
 cyl('cabinet-side-pipe',(side*1.30,-.55,.3),(side*1.30,-.55,1.38),.12,'edge_brass',8)
 cyl('cabinet-side-elbow',(side*1.30,-.55,1.38),(side*1.08,-.55,1.38),.12,'edge_brass',8)
finish('west-vein-cooling-marker')
# Central station: handwheel, gauge, two service blocks on an iron base.
box('valve-station-base',(0,0,0),(3.5,2.5,.2),'iron')
box('valve-pedestal',(0,0,.2),(.55,.60,1.20),'iron')
cyl('valve-shaft',(0,-.30,1.55),(0,-.94,1.55),.11,'iron',8)
p.append(f.add_torus('valve-handwheel',(0,-.96,1.55),.62,.075,'edge_brass'))
for j in range(6):
 angle=2*math.pi*j/6
 p.append(f.add_beam('wheel-spoke',(0,-.96,1.55),(.59*math.cos(angle),-.96,1.55+.59*math.sin(angle)),.075,'edge_brass'))
for x in [-1.15,1.15]:
 box('service-block',(x,.20,.20),(.68,.74,.82),'iron')
 box('service-cap',(x,.20,1.02),(.77,.81,.09),'brass')
cyl('gauge-neck',(.9,.3,1.1),(.9,.3,1.65),.09,'brass',8)
cyl('gauge-case',(.9,.3,1.65),(.9,.1,1.65),.26,'brass',12)
cyl('gauge-face',(.9,.09,1.65),(.9,.07,1.65),.21,'parchment',12)
finish('center-vein-bridge-school')
# Preserve rack: six individual pressure bottles and a low connected manifold.
box('bottle-platform',(0,0,0),(5.4,2.7,.19),'iron')
cyl('manifold',(-2.3,.73,.52),(2.3,.73,.52),.12,'brass',10)
for j in range(6):
 x=-1.45+j*.72;height=1.45+(j%3)*.23
 cyl('bottle',(x,0,.24),(x,0,height),.28,'iron',12)
 for z in [.31,height-.18]:cyl('bottle-band',(x,0,z),(x,0,z+.10),.30,'edge_brass',12)
 cyl('bottle-neck',(x,0,height),(x,0,height+.21),.11,'brass',8)
 cyl('bottle-valve',(x-.15,0,height+.20),(x+.15,0,height+.20),.055,'edge_brass',8)
 cyl('bottle-return',(x,0,.55),(x,.73,.55),.075,'brass',8)
for x in [-2.5,-1.6]:cyl('hanging-frame-post',(x,-.65,.19),(x,-.65,2.8),.07,'edge_brass',8)
cyl('hanging-frame-crossbar',(-2.5,-.65,2.8),(-1.6,-.65,2.8),.07,'edge_brass',8)
cyl('hanging-chain',(-2.05,-.65,2.8),(-2.05,-.65,1.6),.03,'iron',6)
cyl('hanging-vessel',(-2.05,-.65,1.20),(-2.05,-.65,1.65),.21,'brass',10)
finish('shore-preserve-rack')

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
objects=[o for o in bpy.data.objects if o.type=='MESH']
assert {o.name for o in objects}==set(contract['assets']) and len(objects)==5
for obj in objects:
 if obj.name in before:assert snapshot(obj)==before[obj.name]
 obj.data.materials.clear();obj.data.materials.append(material)
 for face in obj.data.polygons:face.material_index=0
for oldmat in list(bpy.data.materials):
 if oldmat!=material and oldmat.users==0:bpy.data.materials.remove(oldmat)
for oldimage in list(bpy.data.images):
 if oldimage!=image and oldimage.users==0:bpy.data.images.remove(oldimage)
material.name='EmberShoreLandmarkPackMaterial';image.name='EmberShoreLandmarkMaterialAtlas'
contract['recipe']=str(Path(__file__).resolve().relative_to(ROOT))
contract['atlas'].update(source=str(RAW.relative_to(ROOT)),sha256=sha(atlas),recipe=contract['recipe'])
bpy.context.preferences.filepaths.save_version=0
blend=OUT/'ember-shore-landmarks.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend));contract['blend']['sha256']=sha(blend)
for obj in objects:
 target=OUT/(obj.name+'.glb');f.export_asset(obj,target);contract['assets'][obj.name]['sha256']=sha(target)
(OUT/'ember-shore-landmark-pack-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
print('PASS: five exported bodies; one unchanged mesh/UVs; four concept fixtures within budget; shared native atlas')
