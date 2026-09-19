"""Derive furnished, open Showroom displays with the existing landmark factory."""
import argparse,bpy,hashlib,importlib.util,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--source',type=Path)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
source=args.source.resolve() if args.source else ROOT/'assets/pilots/map-rebuild-spike/landmarks/showroom'
spec=importlib.util.spec_from_file_location('factory',ROOT/'assets/pilots/map-rebuild-spike/build_landmark_packs.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
f.PACKS['showroom']={'era':6}
f.ROLE_INDEX['pewter']=12
f.ROLE_INDEX['slate']=14
f.ROLE_INDEX['plaster']=13
f.ROLE_INDEX['walnut']=15
contract=json.loads((source/'showroom-landmark-pack-contract.json').read_text())
terrain_path=source/'showroom-terrain-contract.json' if args.source else ROOT/'assets/pilots/map-rebuild-spike/showroom-terrain-contract.json'
terrain=json.loads(terrain_path.read_text())
bpy.ops.wm.open_mainfile(filepath=str(source/'showroom-landmarks.blend'))
# Rebuilding from the saved result replaces the authored homes instead of appending duplicates.
house_ids={house['id'] for house in terrain['maskTruth']['showroomHouses']}
for obj in list(bpy.data.objects):
 if obj.name in house_ids:bpy.data.objects.remove(obj,do_unlink=True)
for mesh in list(bpy.data.meshes):
 if mesh.users==0:bpy.data.meshes.remove(mesh)
for identifier in house_ids:contract['assets'].pop(identifier,None)
terrain['landmarkMounts']=[m for m in terrain['landmarkMounts'] if m['id'] not in house_ids]
def geometry(obj):
 return ([tuple(v.co) for v in obj.data.vertices],[tuple(p.vertices) for p in obj.data.polygons],[tuple(u.uv) for u in obj.data.uv_layers.active.data])
original={o.name:geometry(o) for o in bpy.data.objects if o.type=='MESH'}
raw=ROOT/'assets/raw/showroom-landmark-material-atlas-v2.png'
image=bpy.data.images.load(str(raw),check_existing=False);image.scale(1024,1024);image.name='ShowroomSharedMaterialAtlas'
atlas=out/'showroom-landmarks-atlas.png';image.filepath_raw=str(atlas);image.file_format='PNG';image.save();image.pack()
material=f.make_material('Showroom',image)
# Existing role slots, with face-local mapping so a plank never crosses an atlas seam.
def component_uv(obj,role):
 mesh=obj.data
 while mesh.uv_layers:mesh.uv_layers.remove(mesh.uv_layers[0])
 layer=mesh.uv_layers.new(name='LandmarkAtlasUV').data
 uwidth=.12 if role=='slate' else .84
 vwidth=.16 if role=='slate' else .84
 low=[min(v.co[i] for v in mesh.vertices) for i in range(3)]
 span=[max(v.co[i] for v in mesh.vertices)-low[i] for i in range(3)]
 row,col=divmod(f.ROLE_INDEX[role],4)
 for face in mesh.polygons:
  axis=max(range(3),key=lambda i:abs(face.normal[i]));a,b=[i for i in range(3) if i!=axis]
  for i in face.loop_indices:
   v=mesh.vertices[mesh.loops[i].vertex_index].co
   if obj.name.startswith('floor-plank'):
    u=.08+((obj['floor_column']*7)%16)/16*.60+(v.x-low[0])/span[0]*.22
    vv=.08+(v.y-low[1])/(10.4/3)*.84
    layer[i].uv=((col+u)/4,(row+vv)/4)
    continue
   layer[i].uv=((col+.08+(v[a]-low[a])/max(span[a],.001)*uwidth)/4,(row+.08+(v[b]-low[b])/max(span[b],.001)*vwidth)/4)
f.map_uv=component_uv
parts=[];solids=[]
def box(name,location,size,role='timber',solid=False):
 obj=f.add_box(name,location,size,role);parts.append(obj)
 if solid:solids.append({'x':location[0],'z':-location[1],'w':size[0],'d':size[1]})
 return obj
def cyl(name,start,end,radius,role='iron',vertices=8):
 obj=f.add_cylinder(name,start,end,radius,role,vertices);parts.append(obj);return obj
def beam(name,start,end,width=.12,role='timber'):
 obj=f.add_beam(name,start,end,width,role);parts.append(obj);return obj
def roof():
 # Hipped rear roof: retain an open front while giving the cabin a readable roof volume.
 verts=[(-6.25,1.4,4.02),(6.25,1.4,4.02),(-3.8,3.4,5.95),(3.8,3.4,5.95),(-6.25,4.9,4.02),(6.25,4.9,4.02)]
 mesh=bpy.data.meshes.new('DisplayRoof.mesh');mesh.from_pydata(verts,[],[(0,1,3,2),(2,3,5,4),(0,2,4),(1,5,3),(0,4,5,1)]);mesh.update()
 obj=bpy.data.objects.new('rear-hipped-roof',mesh);bpy.context.collection.objects.link(obj);f.role_object(obj,'slate');parts.append(obj)
 # Small overlapping faces carry material at shingle scale instead of stretching one atlas cell across the roof.
 for side,quad in [('front',[verts[i] for i in [0,1,3,2]]),('rear',[verts[i] for i in [4,5,3,2]])]:
  def point(u,v):return tuple((quad[0][k]*(1-u)+quad[1][k]*u)*(1-v)+(quad[3][k]*(1-u)+quad[2][k]*u)*v+(0.035 if k==2 else 0) for k in range(3))
  for row in range(6):
   for col in range(14):
    u0=(col+.025)/14;u1=(col+.975)/14;v0=(row+.025)/6;v1=(row+.975)/6
    points=[point(u0,v0),point(u1,v0),point(u1,v1),point(u0,v1)]
    mesh=bpy.data.meshes.new('Shingle.mesh');mesh.from_pydata(points,[],[(0,1,2,3) if side=='front' else (3,2,1,0)]);mesh.update()
    obj=bpy.data.objects.new('roof-shingle',mesh);bpy.context.collection.objects.link(obj);f.role_object(obj,'slate');parts.append(obj)
 for a,b in [(0,2),(2,4),(1,3),(3,5)]:beam('roof-hip',verts[a],verts[b],.12,'iron')
 beam('roof-front-eave',verts[0],verts[1],.13,'timber')
 beam('roof-ridge',(-3.84,3.4,5.99),(3.84,3.4,5.99),.16,'iron')
def window(x):
 box('window-glass',(x,3.78,1.56),(1.70,.045,1.25),'water')
 for dx in [-.90,0,.90]:box('window-mullion',(x+dx,3.72,1.50),(.08,.08,1.40),'bone')
 for z in [1.50,2.18,2.82]:box('window-rail',(x,3.72,z),(1.88,.08,.08),'bone')
def shell():
 # Plank faces meet: the visible floor and its walk surface share one uninterrupted top.
 for i in range(16):
  # Stagger real plank joins and vary the sampled grain; every edge still meets exactly.
  edges=[-5.2];edge=-5.2+10.4/3-(i%4)*.82
  while edge<5.2-1e-8:edges.append(edge);edge+=10.4/3
  edges.append(5.2)
  for y,end in zip(edges,edges[1:]):
   x=-6.4+i*12.8/16
   mesh=bpy.data.meshes.new('FloorPlank.mesh');mesh.from_pydata([(x,y,.02),(x+.8,y,.02),(x+.8,end,.02),(x,end,.02)],[],[(0,1,2,3)]);mesh.update()
   obj=bpy.data.objects.new('floor-plank',mesh);bpy.context.collection.objects.link(obj);f.role_object(obj,'timber');obj['floor_column']=i;parts.append(obj)
 for i in range(16):box('back-wall-plank',(-6+(i+.5)*.75,4,.02),(.738,.22,4.0),'plaster')
 solids.append({'x':0,'z':-4,'w':12,'d':.22})
 window(-3.8);window(.1)
 for x in [-5.9,5.9]:
  box('rear-side-wall',(x,2.55,.02),(.22,2.70,4.0),'plaster',True)
  box('cutaway-side-wall',(x,-1.70,.02),(.22,5.8,4.0),'plaster',True)
  for y in [-4.55,1.25,3.95]:box('wall-upright',(x,y,.02),(.25,.25,4.02),'walnut')
 for x in [-5.8,-3.85,-1.93,0,1.93,3.85,5.8]:box('back-batten',(x,3.855,.02),(.10,.07,4.0),'iron')
 for z in [.10,1.0,3.92]:box('back-rail',(0,3.835,z),(11.9,.12,.11),'walnut')
 box('back-wainscot',(0,3.865,.02),(11.65,.08,.86),'walnut')
 for x in [-5.74,5.74]:
  box('side-wainscot',(x,-.35,.02),(.08,8.45,.86),'walnut')
  box('side-chair-rail',(x,-.35,.88),(.12,8.45,.09),'timber')
 box('front-floor-edge',(0,-5.13,0),(12.8,.13,.06),'iron')
 roof()
def refrigerator(x,y):
 box('refrigerator-feet',(x,y,.02),(1.6,1.6,.12),'iron')
 box('refrigerator-body',(x,y,.14),(1.8,1.72,2.70),'bone',True)
 for z,h in [(.21,1.69),(1.97,.77)]:
  box('refrigerator-door',(x,y-.91,z),(1.62,.11,h),'parchment')
  cyl('refrigerator-handle',(x+.55,y-1.02,z+.18),(x+.55,y-1.02,z+h-.16),.045,'brass',8)
 box('refrigerator-vent',(x,y-.93,.10),(1.32,.07,.16),'soot')
def stove(x,y):
 box('range-body',(x,y,.02),(2.3,1.72,1.38),'bone',True)
 box('oven-door',(x,y-.88,.23),(1.88,.08,.88),'iron')
 box('oven-glass',(x,y-.94,.39),(1.30,.05,.47),'soot')
 cyl('oven-handle',(x-.64,y-1.0,1.02),(x+.64,y-1.0,1.02),.055,'brass',8)
 box('stove-top',(x,y,1.40),(2.38,1.78,.08),'iron')
 for xx in [-.59,.59]:
  for yy in [-.43,.43]:
   cyl('burner',(x+xx,y+yy,1.48),(x+xx,y+yy,1.53),.25,'soot',10)
 for xx in [-.75,-.25,.25,.75]:cyl('range-control',(x+xx,y-.90,1.22),(x+xx,y-.98,1.22),.085,'brass',8)
def table(x,y):
 # A continuous top, dark apron and stocky legs separate the furniture from the floor at game zoom.
 box('tabletop',(x,y,1.32),(2.45,1.75,.18),'timber')
 for xx in [-1.225,1.225]:box('tabletop-end',(x+xx,y,1.32),(.07,1.82,.18),'walnut')
 for yy in [-.875,.875]:box('tabletop-edge',(x,y+yy,1.32),(2.45,.07,.18),'walnut')
 for xx in [-1.05,1.05]:box('table-apron-end',(x+xx,y,1.10),(.14,1.40,.22),'walnut')
 for yy in [-.68,.68]:box('table-apron-side',(x,y+yy,1.10),(2.10,.14,.22),'walnut')
 solids.append({'x':x,'z':-y,'w':2.45,'d':1.75})
 for xx in [-.97,.97]:
  for yy in [-.62,.62]:box('table-leg',(x+xx,y+yy,.02),(.22,.22,1.30),'walnut')
 cyl('table-bowl',(x-.4,y,1.50),(x-.4,y,1.66),.25,'bone',10)
 cyl('table-cup',(x+.60,y+.27,1.50),(x+.60,y+.27,1.76),.12,'bone',8)
 for xx in [-.90,.90]:
  yy=y-1.18
  box('chair-seat',(x+xx,yy,.69),(.72,.70,.12),'timber')
  box('chair-back',(x+xx,yy-.28,.81),(.72,.12,.82),'walnut')
  for dx in [-.25,.25]:
   for dy in [-.24,.24]:box('chair-leg',(x+xx+dx,yy+dy,.02),(.12,.12,.69),'walnut')
  solids.append({'x':x+xx,'z':-yy,'w':.8,'d':.8})
def sink(x,y):
 box('sink-cabinet',(x,y,.02),(2.25,1.70,1.31),'timber',True)
 box('sink-worktop',(x,y,1.33),(2.40,1.81,.12),'bone')
 box('sink-basin',(x,y,1.45),(1.43,1.08,.025),'soot')
 for dx in [-.8,.8]:box('sink-rim',(x+dx,y,1.45),(.12,1.25,.055),'pewter')
 cyl('tap-upright',(x,y+.61,1.45),(x,y+.61,2.00),.055,'brass',8)
 cyl('tap-spout',(x,y+.61,2.00),(x,y+.22,2.00),.055,'brass',8)
def bed(x,y):
 box('bed-frame',(x,y,.30),(2.9,4.0,.27),'timber',True)
 box('bed-mattress',(x,y,.57),(2.70,3.72,.43),'bone')
 box('bed-blanket',(x,y-.48,1.00),(2.76,2.55,.10),'cloth')
 for dx in [-.67,.67]:box('pillow',(x+dx,y+1.23,1.0),(1.08,.71,.20),'parchment')
 box('headboard',(x,y+2.03,.30),(3.07,.18,1.62),'timber')
 for dx in [-1.4,1.4]:
  for dy in [-1.91,1.91]:cyl('bedpost',(x+dx,y+dy,.02),(x+dx,y+dy,1.10 if dy<0 else 2.02),.08,'brass',8)
 box('bedside-table',(x+2.0,y+1.38,.02),(.90,.82,.85),'timber',True)
 cyl('lamp-stem',(x+2.0,y+1.38,.87),(x+2.0,y+1.38,1.56),.045,'brass',8)
 cyl('lamp-shade',(x+2.0,y+1.38,1.34),(x+2.0,y+1.38,1.70),.29,'parchment',10)
def sofa(x,y):
 box('sofa-feet',(x,y,.02),(3.4,1.48,.20),'timber')
 box('sofa-seat',(x,y,.22),(3.4,1.48,.45),'cloth',True)
 box('sofa-back',(x,y+.57,.67),(3.4,.32,.92),'cloth')
 for xx in [-1.55,1.55]:box('sofa-arm',(x+xx,y,.64),(.32,1.45,.48),'cloth')
 for xx in [-1.0,0,1.0]:box('sofa-cushion',(x+xx,y-.09,.68),(.88,1.06,.17),'cactus')

def wall_shelf(x):
 # Recessed shelving stays over the existing range/dresser footprints.
 for z in [2.25,3.15]:box('wall-shelf',(x,3.38,z),(1.9,.65,.10),'walnut')
 for xx in [-.95,.95]:box('shelf-upright',(x+xx,3.38,2.25),(.10,.65,1.00),'walnut')
 for xx in [x-.60,x,x+.60]:
  cyl('shelf-canister',(xx,3.35,2.35),(xx,3.35,2.80),.20,'bone',8)
  cyl('canister-lid',(xx,3.35,2.80),(xx,3.35,2.86),.22,'brass',8)

styles=['kitchen','kitchen','living','bedroom','bedroom'];new_mounts=[]
for house,style in zip(terrain['maskTruth']['showroomHouses'],styles):
 parts.clear();solids.clear();shell();wall_shelf(2.32 if style=='bedroom' else 1.65)
 if style=='kitchen':
  refrigerator(4.65,2.25);stove(1.60,2.85);sink(-1.45,2.85);table(-2.9,-.8)
  box('side-counter',(4.45,-.55,.02),(1.85,2.15,1.33),'parchment',True)
  box('countertop',(4.45,-.55,1.35),(1.95,2.23,.12),'timber')
  box('breadbox',(4.45,-.15,1.47),(1.1,.72,.55),'bone')
  for z in [.32,.78]:cyl('counter-handle',(4.14,-1.7,z),(4.76,-1.7,z),.045,'brass',8)
 elif style=='bedroom':
  bed(-3.55,1.12);refrigerator(4.65,2.25)
  box('bench-seat',(4.30,-1.50,.60),(2.0,1.25,.18),'cloth',True)
  box('bench-back',(4.30,-.98,.78),(2.0,.18,1.05),'timber')
  for x in [3.50,5.10]:
   for y in [-1.95,-1.05]:box('bench-leg',(x,y,.02),(.14,.14,.58),'timber')
  box('dresser',(2.32,2.95,.02),(2.35,1.5,1.5),'timber',True)
  for z in [.28,.77,1.26]:
   box('dresser-drawer',(2.32,2.16,z),(2.08,.08,.32),'parchment')
   cyl('drawer-handle',(2.00,2.03,z+.16),(2.64,2.03,z+.16),.045,'brass',8)
 else:
  box('living-rug',(-3.55,-.90,.024),(4.22,4.52,.008),'cactus')
  sofa(-3.70,1.10);table(-3.70,-1.70);stove(1.60,2.85);refrigerator(4.65,2.25)
  cyl('standing-lamp-base',(-1.6,1.5,.025),(-1.6,1.5,.10),.36,'iron',10)
  cyl('standing-lamp-stem',(-1.6,1.5,.10),(-1.6,1.5,2.15),.065,'brass',8)
  cyl('standing-lamp-shade',(-1.6,1.5,1.8),(-1.6,1.5,2.35),.43,'parchment',10)
  solids.append({'x':-1.6,'z':-1.5,'w':.72,'d':.72})
 # A real raised floor and three steps; surface metadata is authored from these same dimensions.
 for obj in parts:obj.location.z+=.60
 box('foundation',(0,0,0),(12.8,10.4,.60),'walnut')
 for z in [.06,.42]:box('foundation-front-course',(0,-5.205,z),(12.8,.015,.07),'iron')
 surfaces=[{'minX':-6.4,'maxX':6.4,'minZ':-5.2,'maxZ':5.2,'height':.62}]
 for i in range(3):
  top=.60-i*.20;near=5.2+i*.9;far=near+.9
  box('entry-step',(0,-(near+far)/2,0),(3.8,.9,top-.055),'walnut')
  # Top and lip end exactly at the documented walk height; no floating decoration above it.
  box('step-tread',(0,-(near+far-.07)/2,top-.055),(3.8,.83,.055),'timber')
  box('step-nosing',(0,-far+.035,top-.065),(3.8,.07,.065),'walnut')
  surfaces.append({'minX':-1.9,'maxX':1.9,'minZ':near,'maxZ':far,'height':top})
 # Low front rails keep side approaches from walking into the raised foundation.
 for x in [-4.12,4.12]:
  box('front-rail',(x,-4.65,.60),(3.56,.18,.92),'walnut',True)
 bpy.context.view_layer.update()
 points=[obj.matrix_world @ v.co for obj in parts for v in obj.data.vertices]
 center=[(min(p[i] for p in points)+max(p[i] for p in points))/2 for i in [0,1]]
 for solid in solids:solid['x']-=center[0];solid['z']+=center[1]
 for surface in surfaces:
  surface['minX']-=center[0];surface['maxX']-=center[0];surface['minZ']+=center[1];surface['maxZ']+=center[1]
 identifier=house['id'];asset=f.finish_asset(parts,identifier,material,'showroom',{'tier':'derive'})
 cx=(house['minX']+house['maxX'])/2;cz=(house['minZ']+house['maxZ'])/2
 new_mounts.append({'id':identifier,'position':[cx+center[0],0,cz-center[1]],'rotation':[0,0,0],'scale':[1,1,1],'asset':f'landmarks/showroom/{identifier}.glb','role':'display-home','walkSurfaces':surfaces})
 bounds=f.glb_bounds(asset);tris=sum(len(p.vertices)-2 for p in asset.data.polygons)
 assert tris<=3000,(identifier,tris)
 assert bounds['max'][0]-bounds['min'][0]<=18 and bounds['max'][1]-bounds['min'][1]<=18
 contract['assets'][identifier]={'asset':f'landmarks/showroom/{identifier}.glb','sourceTier':'derive','terrainConformed':False,'sources':['assets/raw/plate-contract-e6-showroom.png',str(raw.relative_to(ROOT))],'triangles':tris,'triangleBudget':3000,'bounds':bounds,'style':style,'collisionParts':list(solids),'walkSurfaces':surfaces}
 print(identifier,style,tris,bounds)

objects=[o for o in bpy.data.objects if o.type=='MESH'];assert len(objects)==10
for obj in objects:
 if obj.name in original:assert geometry(obj)==original[obj.name]
 obj.data.materials.clear();obj.data.materials.append(material)
 for face in obj.data.polygons:face.material_index=0
for old in list(bpy.data.materials):
 if old!=material and old.users==0:bpy.data.materials.remove(old)
for old in list(bpy.data.images):
 if old!=image and old.users==0:bpy.data.images.remove(old)
# Blender may suffix names while the old shared resources still exist. Pin after removing unused predecessors.
material.name='ShowroomLandmarkPackMaterial';image.name='ShowroomSharedMaterialAtlas'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bpy.context.preferences.filepaths.save_version=0
blend=out/'showroom-landmarks.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
for obj in objects:
 path=out/(obj.name+'.glb');f.export_asset(obj,path);contract['assets'][obj.name]['sha256']=sha(path)
 sources=contract['assets'][obj.name]['sources']
 if str(raw.relative_to(ROOT)) not in sources:sources.append(str(raw.relative_to(ROOT)))
contract['recipe']=str(Path(__file__).resolve().relative_to(ROOT));contract['atlas'].update(sha256=sha(atlas),source=str(raw.relative_to(ROOT)));contract['blend']['sha256']=sha(blend)
terrain['landmarkMounts'].extend(new_mounts);contract['mounts']=terrain['landmarkMounts'];terrain.pop('candidateNote',None);terrain['landmarkNotes']='Five furnished display homes with three entry steps. collisionParts feed the existing planar registry; walkSurfaces supply rendered floor and pointer heights.';contract['simulation']='Planar collision uses landmark-collision-contract.json. Rendered floor and pointer heights use the existing Terrain visual owner. No economy, combat, objective or ground-heightfield changes.'
(out/'showroom-landmark-pack-contract.json').write_text(json.dumps(contract,indent=2)+'\n');(out/'showroom-terrain-contract.json').write_text(json.dumps(terrain,indent=2)+'\n')
print('PASS: ten one-material bodies, five original meshes/UVs unchanged, five concept-derived interiors; proposed collision parts retained')
