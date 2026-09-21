"""Rebuild the Seed Run center vault roof inside its exact original envelope.
Blender --background --python this.py -- --source <base blend> --out <dir>.
Four peers, shared atlas, collision footprint and all mount transforms are retained.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(a.source).resolve()))
rig=bpy.data.objects['center-seed-vault'];material=rig.data.materials[0]
assert len(rig.data.vertices)==1226
original_bounds=([min(v.co[i] for v in rig.data.vertices) for i in range(3)],[max(v.co[i] for v in rig.data.vertices) for i in range(3)])
roof=[rig.data.vertices[i].co.copy() for i in range(1218,1226)];roof_x=max(v.x for v in roof);front=min(v.y for v in roof);back=max(v.y for v in roof);base_z=min(v.z for v in roof)
assert all(3.21<v.z<3.45 for v in roof)
# The existing front emblem ring uses brass for separation against the teal roof.
uv=rig.data.uv_layers.active
for poly in rig.data.polygons:
 if min(poly.vertices)>=1046 and max(poly.vertices)<1094:
  for li in poly.loop_indices:
   old=uv.data[li].uv.copy();uv.data[li].uv=(((old.x*4)%1)/4,(2+(old.y*4)%1)/4)
bm=bmesh.new();bm.from_mesh(rig.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in [*range(8),*range(1218,1226)]],context='VERTS');bm.to_mesh(rig.data);bm.free()
parts=[rig];roles={'iron':1,'stone':2,'brass':8,'teal':4,'soot':9}
def finish(obj,name,role):
 obj.name=name;bpy.context.view_layer.objects.active=obj
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 obj.data.materials.clear();obj.data.materials.append(material)
 while obj.data.uv_layers:obj.data.uv_layers.remove(obj.data.uv_layers[0])
 uv=obj.data.uv_layers.new(name='LandmarkAtlasUV');row,col=divmod(roles[role],4)
 for poly in obj.data.polygons:
  for li in poly.loop_indices:
   co=obj.data.vertices[obj.data.loops[li].vertex_index].co
   u=(co.x*.13+co.z*.07)%1;v=(co.y*.13+co.z*.11)%1
   uv.data[li].uv=((col+.08+.84*u)/4,(row+.08+.84*v)/4)
 parts.append(obj);obj.select_set(False);return obj
def beam(name,a,b,width,role='iron'):
 delta=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cube_add(size=1,location=(Vector(a)+Vector(b))*.5)
 o=bpy.context.object;o.dimensions=(width,width,delta.length);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return finish(o,name,role)
def cylinder(name,loc,radius,depth,role='iron',sides=12,scale=(1,1,1)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=radius,depth=depth,location=loc)
 o=bpy.context.object;o.scale=scale;return finish(o,name,role)
def panel(name,loc,size,role='iron'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;return finish(o,name,role)
# Eight-sided footing retains exact outer extrema, with less dark slab area.
cylinder('SeedVault.ChamferedFooting',(0,-.045,.11),1,.22,'stone',8,(2.85,2.10,1))
# A closed curved roof shell replaces the flat red card; the seed emblem stays.
verts=[];faces=[];segments=12
for y in [front,back]:
 for inner in [False,True]:
  for i in range(segments+1):
   t=i*math.pi/segments;verts.append((-roof_x*math.cos(t),y,base_z+1.1*math.sin(t)-(.12 if inner else 0)))
n=segments+1
for i in range(segments):
 j=i+1
 faces.extend([(i,j,2*n+j,2*n+i),(n+i,3*n+i,3*n+j,n+j),(i,n+i,n+j,j),(2*n+i,2*n+j,3*n+j,3*n+i)])
faces.extend([(0,2*n,3*n,n),(segments,n+segments,3*n+segments,2*n+segments)])
mesh=bpy.data.meshes.new('SeedVault.CurvedRoof');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('SeedVault.CurvedRoof',mesh);bpy.context.collection.objects.link(o);o.select_set(True);finish(o,'SeedVault.CurvedRoof','teal')
uv=o.data.uv_layers.active
for poly in o.data.polygons:
 for li in poly.loop_indices:
  co=o.data.vertices[o.data.loops[li].vertex_index].co
  uv.data[li].uv=((.08+.84*(co.x+roof_x)/(2*roof_x))/4,(1+.08+.84*(co.y-front)/(back-front))/4)
for r in range(5):
 y=front+.08+(back-front-.16)*r/4
 for i in range(segments):
  t=i*math.pi/segments;u=(i+1)*math.pi/segments
  beam(f'SeedVault.RoofRib.{r}.{i}',(-roof_x*math.cos(t),y,base_z+1.1*math.sin(t)+.04),(-roof_x*math.cos(u),y,base_z+1.1*math.sin(u)+.04),.085,'brass')
# Roof stanchions seat the curved shell on the existing footing.
for side,x in enumerate([-2.3,2.3]):
 for end,y in enumerate([-1.7,1.78]):
  top=base_z+1.1*math.sqrt(1-(x/roof_x)**2)-.08
  beam(f'SeedVault.Stanchion.{side}.{end}',(x,y,.22),(x,y,top),.16,'iron')
  beam(f'SeedVault.StanchionShoe.{side}.{end}',(x,y,.22),(x,y,.43),.32,'brass')
# Enclosure and a framed entrance sit inside the already-blocked vault footprint.
for side,x in enumerate([-1.93,1.93]):
 panel(f'SeedVault.SideWall.{side}',(x,0,1.52),(.16,2.90,2.60))
 panel(f'SeedVault.WallCornice.{side}',(x,0,2.88),(.24,3.02,.16),'brass')
panel('SeedVault.BackWall',(0,1.37,1.52),(3.86,.16,2.60))
for side,x in enumerate([-1.3,1.3]):
 panel(f'SeedVault.FrontWall.{side}',(x,-1.37,1.52),(1.25,.16,2.60))
panel('SeedVault.VaultDoor',(0,-1.46,1.48),(1.24,.12,2.50),'stone')
for x in [-.69,.69]:beam('SeedVault.DoorJamb',(x,-1.54,.25),(x,-1.54,2.85),.10,'brass')
beam('SeedVault.DoorLintel',(-.74,-1.54,2.82),(.74,-1.54,2.82),.13,'brass')
for side,x in enumerate([-2.3,2.3]):
 top=base_z+1.1*math.sqrt(1-(x/roof_x)**2)-.08
 beam(f'SeedVault.RoofHeader.{side}',(x,-1.75,top),(x,1.83,top),.18,'iron')
 for end,y in enumerate([-1.7,1.78]):
  beam(f'SeedVault.RoofBracket.{side}.{end}',(x,y,top-.65),(x*.78,y,top+.25),.13,'brass')
for i,x in enumerate([-1.7,-.57,.57,1.7]):
 cylinder(f'SeedVault.FrontCanister.{i}',(x,-1.86,1.35),.18,1.8,'brass',8)
 cylinder(f'SeedVault.CanisterLid.{i}',(x,-1.86,2.27),.21,.10,'iron',8)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.join();rig.name='center-seed-vault'
for p in rig.data.polygons:p.material_index=0
while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
tri=sum(len(p.vertices)-2 for p in rig.data.polygons);assert tri<=3000,tri
bounds=([min(v.co[i] for v in rig.data.vertices) for i in range(3)],[max(v.co[i] for v in rig.data.vertices) for i in range(3)])
assert all(abs(a-b)<.0001 for aa,bb in zip(original_bounds,bounds) for a,b in zip(aa,bb)),(original_bounds,bounds)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str((out/'seed-run-landmarks.blend').resolve()))
bpy.ops.export_scene.gltf(filepath=str((out/'center-seed-vault.glb').resolve()),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
print('DRESSING_RESULT',json.dumps({'triangles':tri,'bounds':{'min':bounds[0],'max':bounds[1]},'sourceSha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'glbSha256':hashlib.sha256((out/'center-seed-vault.glb').read_bytes()).hexdigest()}))
