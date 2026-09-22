"""Build a dedicated Last Claim render pack without changing gameplay geometry.
Blender --background --python this.py. Native image_gen sources are copied byte-for-byte; generation receipts accompany them.
The terrain reuses sampled fallback visual heights; the square playable floor is retained.
"""
import hashlib,json,math,shutil
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path.cwd();OUT=ROOT/'assets/pilots/map-rebuild-spike';PACK=OUT/'landmarks/last-claim';PACK.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=OUT/'sources/last-claim-fidelity-1/engraved-bronze-deck.png';shutil.copy2(source,OUT/'last-claim-terrain-atlas.png')
shutil.copy2(OUT/'sources/last-claim-fidelity-1/engraved-star-vista-square.png',OUT/'last-claim-panorama-atlas.png')
shutil.copy2(OUT/'landmarks/archive-world/archive-world-landmarks-atlas.png',PACK/'last-claim-landmarks-atlas.png')
grid=json.loads((OUT/'last-claim-fallback-height-grid.json').read_text());heights=grid['heights'];truth=json.loads((ROOT/'assets/contracts/epoch-10-deepsky/mask-tables/e10-last-claim.json').read_text())
assert len(heights)==129*129
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version=0

def material(name,path):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.84
 tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True);tex.image.pack();tex.extension='REPEAT';m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);return m,tex.image

def mesh(name,verts,faces,mat,uvfun,smooth=False):
 data=bpy.data.meshes.new(name+'Mesh');data.from_pydata(verts,[],faces);data.update();o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);data.materials.append(mat);uv=data.uv_layers.new(name='PaintUV')
 for poly in data.polygons:
  poly.use_smooth=smooth
  for li in poly.loop_indices:uv.data[li].uv=uvfun(data.vertices[data.loops[li].vertex_index].co)
 return o

def export(o,path):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)

def facts(o,path,budget):
 verts={tuple(v.co) for v in o.data.vertices};tri=sum(len(p.vertices)-2 for p in o.data.polygons);assert tri<=budget,(o.name,tri)
 return {'meshCount':len(o.data.materials),'primitiveCount':len(o.data.materials),'materialCount':len(o.data.materials),'vertices':len(verts),'triangles':tri,'triangleBudget':budget,'boundsMeters':{'min':[min(v[i] for v in verts) for i in range(3)],'max':[max(v[i] for v in verts) for i in range(3)]},'sha256':sha(path)}

terrainMat,terrainImage=material('LastClaimStoneFloor',OUT/'last-claim-terrain-atlas.png')
verts=[(x,-z,heights[(z+64)*129+x+64]) for z in range(-64,65) for x in range(-64,65)];faces=[]
for z in range(128):
 for x in range(128):
  i=z*129+x;faces.extend([(i,i+130,i+1),(i,i+129,i+130)])
terrain=mesh('LastClaimTerrain',verts,faces,terrainMat,lambda co:((co.x+64)/22,(co.y+64)/22),True)
terrain['render_only']=True;terrain['height_socket']='Terrain.visualY';terrain['tile_id']='ark-plaza-e10';terrain['grid_segments']=128
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'last-claim-terrain.blend'));export(terrain,OUT/'last-claim-terrain.glb');terrainFacts=facts(terrain,OUT/'last-claim-terrain.glb',60000)
bpy.data.objects.remove(terrain,do_unlink=True)

# A separate skirt and star wall begins beyond every playable edge. No mountain
# or barrier is inserted into the corridor or the three preserve sites.
panoMat,panoImage=material('LastClaimStarHorizon',OUT/'last-claim-panorama-atlas.png');v=[];f=[];segments=128
for ring in range(5):
 for i in range(segments):
  a=math.tau*i/segments;dx,dz=math.cos(a),math.sin(a)
  if ring==0:
   r=64.05/max(abs(dx),abs(dz));x,z=r*dx,r*dz;ix=round(max(-64,min(64,x)))+64;iz=round(max(-64,min(64,z)))+64;h=heights[iz*129+ix]
  else:
   r,h=[(0,0),(100,-1.5),(150,-5),(190,-5),(190,115)][ring];x,z=r*dx,r*dz
  v.append((x,-z,h))
for ring in range(4):
 for i in range(segments):
  a=ring*segments+i;b=ring*segments+(i+1)%segments;c=(ring+1)*segments+(i+1)%segments;d=(ring+1)*segments+i;f.append((a,d,c,b))
panorama=mesh('LastClaimPanorama',v,f,panoMat,lambda co:(0,0),True)
uv=panorama.data.uv_layers.active
for poly in panorama.data.polygons:
 ring=poly.index//segments;i=poly.index%segments
 for corner,li in enumerate(poly.loop_indices):
  rr=ring+(1 if corner in [1,2] else 0);u=(i+(1 if corner in [2,3] else 0))/segments
  co=panorama.data.vertices[panorama.data.loops[li].vertex_index].co
  uv.data[li].uv=(u,(rr-3)) if ring==3 else (co.x/55,co.y/55)
# Decorative rim lives wholly OUTSIDE the unchanged 128 m square. It neither
# removes corners nor creates a visible wall through the walkable arena.
# One merged material primitive keeps the perimeter cheap on mobile.
rimMat,_=material('LastClaimEngravedRim',OUT/'last-claim-terrain-atlas.png')
rimMat.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(.15,.09,.035,1)
rimMat.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.35
rim=[]
def rim_part(a,b,width,name):
 delta=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cube_add(size=1,location=(Vector(a)+Vector(b))*.5);o=bpy.context.object;o.name=name;o.dimensions=(width,width,delta.length);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(rimMat);rim.append(o)
points=[]
for i in range(32):
 a=math.tau*i/32;dx,dy=math.cos(a),math.sin(a);r=64.6/max(abs(dx),abs(dy));points.append((r*dx,r*dy))
for i,(x,y) in enumerate(points):
 nx,ny=points[(i+1)%len(points)]
 h=heights[round(max(-64,min(64,-y))+64)*129+round(max(-64,min(64,x))+64)]
 nh=heights[round(max(-64,min(64,-ny))+64)*129+round(max(-64,min(64,nx))+64)]
 rim_part((x,y,h-.12),(x,y,h+1.7),.20,'Perimeter.Post')
 for z in [.45,1.3]:rim_part((x,y,h+z),(nx,ny,nh+z),.11,'Perimeter.Rail')
 # Vertical fascia and a narrow top lip are outside the grid, never walk surfaces.
 fascia=mesh('Perimeter.Fascia',[(x,y,h+.06),(nx,ny,nh+.06),(nx,ny,nh-2.5),(x,y,h-2.5)],[(0,1,2,3)],rimMat,lambda co:(co.x/4,co.z/4));rim.append(fascia)
 ratio=64.01/64.6
 lip=mesh('Perimeter.Lip',[(x*ratio,y*ratio,h+.035),(nx*ratio,ny*ratio,nh+.035),(nx,ny,nh+.035),(x,y,h+.035)],[(0,1,2,3)],rimMat,lambda co:(co.x/4,co.y/4));rim.append(lip)
 # Broad pointed caps and inset cross-bracing establish the engraved brass grammar.
 bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=.35,radius2=.03,depth=.48,location=(x,y,h+1.75));o=bpy.context.object;o.data.materials.append(rimMat);rim.append(o)
 if i%2==0:
  rim_part((x,y,h+.45),(nx,ny,nh+1.3),.055,'Perimeter.Filigree')
  rim_part((x,y,h+1.3),(nx,ny,nh+.45),.055,'Perimeter.Filigree')
bpy.ops.object.select_all(action='DESELECT');panorama.select_set(True)
for o in rim:o.select_set(True)
bpy.context.view_layer.objects.active=panorama;bpy.ops.object.join()
# Join may leave duplicate slots even when every rim piece shares one material.
for poly in panorama.data.polygons:
 if poly.material_index>0:poly.material_index=1
while len(panorama.data.materials)>2:panorama.data.materials.pop(index=len(panorama.data.materials)-1)
panorama['render_only']=True;panorama['panorama']=True;panorama['panorama_law']='v2';panorama['affects_playfield']=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'last-claim-panorama.blend'));export(panorama,OUT/'last-claim-panorama.glb');panoFacts=facts(panorama,OUT/'last-claim-panorama.glb',4000)
bpy.data.objects.remove(panorama,do_unlink=True)

mat,atlas=material('LastClaimMonumentAtlas',PACK/'last-claim-landmarks-atlas.png');roles={'stone':2,'iron':1,'brass':8,'teal':4,'parchment':10,'dark':13};parts=[]
def finish(o,name,role):
 o.name=name;bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.clear();o.data.materials.append(mat)
 while o.data.uv_layers:o.data.uv_layers.remove(o.data.uv_layers[0])
 uv=o.data.uv_layers.new(name='MonumentAtlasUV');row,col=divmod(roles[role],4)
 for poly in o.data.polygons:
  axis=max(range(3),key=lambda k:abs(poly.normal[k]));axes=[k for k in range(3) if k!=axis]
  for li in poly.loop_indices:
   co=o.data.vertices[o.data.loops[li].vertex_index].co;u=(co[axes[0]]*.21)%1;w=(co[axes[1]]*.21)%1;uv.data[li].uv=((col+.07+.86*u)/4,(row+.07+.86*w)/4)
 parts.append(o);o.select_set(False);return o

def box(name,p,s,role='iron'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=s;return finish(o,name,role)
def beam(name,a,b,w,role='iron'):
 d=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cube_add(size=1,location=(Vector(a)+Vector(b))*.5);o=bpy.context.object;o.dimensions=(w,w,d.length);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return finish(o,name,role)
def cyl(name,p,r,h,role='brass',n=16,scale=(1,1,1)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=h,location=p);o=bpy.context.object;o.scale=scale;return finish(o,name,role)
def cone(name,p,r1,r2,h,role='brass',n=16):
 bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r1,radius2=r2,depth=h,location=p);return finish(bpy.context.object,name,role)
def torus(name,p,r,t,role='brass',rot=(0,0,0),major=24,minor=5):
 bpy.ops.mesh.primitive_torus_add(major_segments=major,minor_segments=minor,location=p,major_radius=r,minor_radius=t,rotation=rot);return finish(bpy.context.object,name,role)
def orb(name,p,scale,role='brass',sub=1):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=p);o=bpy.context.object;o.scale=scale;return finish(o,name,role)

assets={};mounts=[]
def complete(identifier,x,z):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 root=parts[0];bpy.context.view_layer.objects.active=root;bpy.ops.object.join();root.name=identifier
 for poly in root.data.polygons:poly.material_index=0
 while len(root.data.materials)>1:root.data.materials.pop(index=len(root.data.materials)-1)
 root['render_only']=True;root['landmark']=True;root['mount_id']=identifier;root['map_pack']='last-claim';root['era']=10
 path=PACK/(identifier+'.glb');export(root,path);info=facts(root,path,3000)
 assets[identifier]={'asset':'landmarks/last-claim/'+identifier+'.glb','sourceTier':'build-new','sources':['assets/raw/plate-contract-e10-last-claim.png','assets/pilots/map-rebuild-spike/landmarks/archive-world/archive-world-landmarks-atlas.png'],'terrainConformed':False,'triangles':info['triangles'],'triangleBudget':3000,'bounds':info['boundsMeters'],'sha256':info['sha256'],'blocking':'none; decorative monument, no new collision footprint'}
 mounts.append({'id':identifier,'asset':assets[identifier]['asset'],'position':[x,0,z],'rotation':[0,0,0],'scale':[1,1,1]});parts.clear();root.select_set(False)

def plinth():
 cyl('Plinth.Lower',(0,0,.09),1.45,.18,'stone',16)
 cyl('Plinth.Brass',(0,0,.23),1.25,.10,'brass',16)
 cyl('Plinth.Upper',(0,0,.36),1.1,.16,'iron',16)
 for i in range(8):
  t=i*math.tau/8;box('Plinth.Inlay',(1.30*math.cos(t),1.30*math.sin(t),.2),(.13,.13,.22),'brass')
plinth();cyl('Lantern.Pedestal',(0,0,.83),.7,.80,'iron');cyl('Lantern.LowerCrown',(0,0,1.28),.86,.16)
cyl('Lantern.Glass',(0,0,2.52),.63,2.30,'parchment',12)
for i in range(8):
 t=i*math.tau/8;beam('Lantern.Cage',( .70*math.cos(t),.70*math.sin(t),1.35),(.70*math.cos(t),.70*math.sin(t),3.7),.075,'brass')
cyl('Lantern.TopCrown',(0,0,3.72),.86,.16);cone('Lantern.Roof',(0,0,4.04),.95,.23,.54);orb('Lantern.Finial',(0,0,4.45),(.20,.20,.32));torus('Lantern.Hanger',(0,0,4.82),.26,.065,rot=(math.pi/2,0,0))
complete('preserve-last-lantern',-10,47)
plinth();cyl('Resonator.Stem',(0,0,1.08),.31,1.32,'iron')
for i,(r,rot) in enumerate([(1.3,(math.pi/2,0,0)),(1.04,(math.pi/2,.55,.25)),(.74,(math.pi/2,-.42,-.3))]):torus('Resonator.Harmonic.'+str(i),(0,0,2.95),r,.09,'brass' if i!=1 else 'teal',rot)
orb('Resonator.Core',(0,0,2.95),(.42,.3,.42),'teal',2)
for x in [-1.4,1.4]:beam('Resonator.Frame',(x,0,.4),(x,0,2.95),.14);beam('Resonator.Bearing',(x,0,2.95),(x*.64,0,2.95),.19,'brass')
beam('Resonator.Pin',(0,0,4.24),(0,0,4.70),.10,'brass');orb('Resonator.Finial',(0,0,4.8),(.16,.16,.16))
complete('preserve-pan-theme-song',0,47)
plinth();box('Portrait.Tablet',(0,.09,2.56),(2.02,.20,3.22),'dark')
for x in [-1.14,1.14]:box('Portrait.Jamb',(x,0,2.55),(.21,.36,3.52),'brass');box('Portrait.Foot',(x,0,.74),(.40,.55,.66),'iron')
for h in [.84,4.25]:box('Portrait.Rail',(0,0,h),(2.45,.36,.22),'brass')
# A simple memorial relief is part of the monument, not a new character/sprite asset.
orb('Portrait.ReliefHead',(0,-.105,3.07),(.42,.15,.57),'parchment',2);cone('Portrait.ReliefShoulders',(0,-.06,2.2),.70,.20,.74,'parchment',12)
for x in [-1,1]:beam('Portrait.Crown',(x,0,4.35),(0,0,4.92),.12,'brass')
orb('Portrait.Finial',(0,0,5.08),(.16,.16,.18));complete('preserve-last-portrait',10,47)
plinth();cyl('Orrery.Column',(0,0,1.16),.45,1.6,'iron');cone('Orrery.Capital',(0,0,2.02),.68,.40,.26)
orb('Orrery.Sun',(0,0,2.90),(.53,.53,.53),'brass',2)
for i,rot in enumerate([(0,0,0),(.6,.3,0),(-.45,.5,.35)]):torus('Orrery.Orbit.'+str(i),(0,0,2.9),1.5+i*.25,.07,'brass',rot)
for i in range(5):
 t=i*math.tau/5;orb('Orrery.World.'+str(i),(1.5*math.cos(t),1.5*math.sin(t),2.9),(.15,.15,.15),'teal')
beam('Orrery.Axis',(0,0,1.7),(0,0,4.55),.095,'brass');orb('Orrery.Pole',(0,0,4.66),(.18,.18,.18));complete('central-orrery',0,0)
# Open ceremonial arch at the opposite end; no sealed door or blocking wall.
for x in [-3.2,3.2]:
 box('MemoryArch.Foot',(x,0,.16),(1.12,1.18,.32),'stone');cyl('MemoryArch.Column',(x,0,2.55),.38,4.6,'iron',12)
 for z in [.5,1.0,4.3,4.65]:cyl('MemoryArch.Collar',(x,0,z),.46,.13,'brass',12)
 cone('MemoryArch.Crown',(x,0,5.1),.63,.08,.84);orb('MemoryArch.Finial',(x,0,5.67),(.14,.14,.23))
for i in range(24):
 t=math.pi*i/24;u=math.pi*(i+1)/24;beam('MemoryArch.Curve',(-3.2*math.cos(t),0,3.25+2.0*math.sin(t)),(-3.2*math.cos(u),0,3.25+2.0*math.sin(u)),.25,'brass')
for i in range(9):
 t=math.pi*(i+1)/10;orb('MemoryArch.Inlay',(-3.2*math.cos(t),-.18,3.25+2*math.sin(t)),(.12,.09,.15),'teal')
complete('stern-memory-arch',0,-51)
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'last-claim-landmarks.blend'))

panoMount={'id':'last-claim-panorama','asset':'last-claim-panorama.glb','position':[0,0,0],'rotation':[0,0,0],'scale':[1,1,1],'renderOnly':True,'ownership':'separate star horizon outside the full rectangular gameplay bounds'}
stations=[{'id':m['id'],'heroPositionXZ':[m['position'][0],m['position'][2]+5],'offsetFromMountXZ':[0,5],'backMeters':5,'purpose':'Render-only monument inspection; ordinary entry measured separately.'} for m in mounts]
texture=lambda im:{'count':1,'width':im.size[0],'height':im.size[1],'embedded':True}
files=lambda stem:{k:{'bytes':(OUT/(stem+suffix)).stat().st_size,'sha256':sha(OUT/(stem+suffix))} for k,suffix in [('blend','.blend'),('glb','.glb'),('atlas','-atlas.png')]}
terrainContract={'asset':'last-claim-terrain.glb','contractId':'e10-last-claim','tileId':'ark-plaza-e10','renderOnly':True,'simulation':'Planar and unchanged; no collision, deck-loss, preserve, spawn or build rule is altered.','heightSocket':'Terrain.visualY','theme':'Circular brass-inlaid memorial deck across the full original square floor; no walkable corner is removed.',**terrainFacts,'texture':texture(terrainImage),'maskTable':'assets/contracts/epoch-10-deepsky/mask-tables/e10-last-claim.json',**truth,'panoramaMount':panoMount,'landmarkMounts':mounts,'landmarkAcceptanceStations':stations,'sourceArt':['assets/raw/plate-contract-e10-last-claim.png','assets/pilots/map-rebuild-spike/sources/last-claim-fidelity-1/engraved-bronze-deck.png'],'heightDerivation':{'grid':'last-claim-fallback-height-grid.json','sha256':sha(OUT/'last-claim-fallback-height-grid.json'),'method':'16641 fallback visual samples; unchanged sampler code and planar gameplay.'},'files':files('last-claim-terrain')}
# Contract bounds use Blender x/y/z; symmetric XZ extents preserve the established convention.
panoContract={'asset':'last-claim-panorama.glb','map':'last-claim','renderOnly':True,'style':'Native engraved star vista and 32-bay brass perimeter outside the unchanged square; Panorama Law v2 budget.',**panoFacts,'texture':{**texture(panoImage),'count':2,'secondAtlas':'last-claim-terrain-atlas.png'},'mount':panoMount,'projection':{'skyRingRadiusMeters':190,'skyBottomMeters':-5,'skyTopMeters':115,'groundSkirtInnerBoundaryMeters':{'shape':'expanded-playfield-rectangle','halfExtents':[64,64],'margin':.05}},'sourceArt':['assets/pilots/map-rebuild-spike/sources/last-claim-fidelity-1/engraved-star-vista-square.png','assets/pilots/map-rebuild-spike/sources/last-claim-fidelity-1/engraved-bronze-deck.png'],'files':files('last-claim-panorama')}
packContract={'map':'last-claim','era':10,'sourceLadder':['reuse-existing-raster','build-new-geometry'],'recipe':'build_last_claim_pack.py','atlas':{'asset':'landmarks/last-claim/last-claim-landmarks-atlas.png','width':atlas.size[0],'height':atlas.size[1],'sharedByEveryAsset':True,'sha256':sha(PACK/'last-claim-landmarks-atlas.png')},'blend':{'asset':'landmarks/last-claim/last-claim-landmarks.blend','sha256':sha(PACK/'last-claim-landmarks.blend')},'assets':assets,'mounts':mounts,'landmarkAcceptanceStations':stations,'simulation':'none; no new footprint, blocker, walk surface or gameplay owner','preservePlacement':'Monuments stand 3 m behind their published preserve sites, at the edge of the existing radius; all sites and markers remain unchanged.'}
for path,data in [(OUT/'last-claim-terrain-contract.json',terrainContract),(OUT/'last-claim-panorama-contract.json',panoContract),(PACK/'last-claim-landmark-pack-contract.json',packContract)]:path.write_text(json.dumps(data,indent=2)+'\n')
print('LAST_CLAIM_PACK',json.dumps({'terrain':terrainFacts,'panorama':panoFacts,'landmarks':{k:v['triangles'] for k,v in assets.items()}}))

sidecar={'profile':'terrain','why':'Dedicated regular terrain grid retains render-only and height socket metadata when re-exported; no decimation or animation is permitted.','extras':True,'animations':False,'applyTransforms':True,'selection':'meshes+anchors','asset':'last-claim-terrain.glb','blend':'last-claim-terrain.blend','contract':'last-claim-terrain-contract.json'}
(OUT/'last-claim-terrain.export.json').write_text(json.dumps(sidecar,indent=2)+'\n')
ledgerPath=OUT/'landmarks/landmark-source-ledger.json';ledger=json.loads(ledgerPath.read_text());ledger['packs']['last-claim']={k:{field:v[field] for field in ['sourceTier','sources','asset']} for k,v in assets.items()};ledgerPath.write_text(json.dumps(ledger,indent=2)+'\n')
