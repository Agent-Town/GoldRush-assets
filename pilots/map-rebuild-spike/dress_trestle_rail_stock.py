"""Reseat the duplicate spur track as stored rail, preserving its accepted body.

Run with Blender --background --python-exit-code 1 --python this.py.
The shared runtime rail path remains the sole active route. Every face and UV
survives; only the two rails, ten sleepers and switch tongue move. Other pack
bodies, atlas, mounts, overall bounds and gameplay data remain unchanged.
"""
from pathlib import Path
import bpy,hashlib,json,math,subprocess,time
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
PACK=OUT/'landmarks/trestle'
PIN='ddfb210f5e8dacdc3595a9370d8498a7934427a8'
REL='assets/pilots/map-rebuild-spike/landmarks/trestle/trestle-landmarks.blend'
RAW=ROOT/'artifacts/sol/map-art-campaign-2/_raw/run-3'/f'trestle-rail-stock-{time.time_ns()}'
RAW.mkdir(parents=True)
original=subprocess.check_output(['git','show',f'{PIN}:{REL}'],cwd=ROOT)
(RAW/'input.blend').write_bytes(original)
bpy.ops.wm.open_mainfile(filepath=str(RAW/'input.blend'))
body=bpy.data.objects['mine-spur-kit'];mesh=body.data
assert tuple(body.location)==(0,0,0) and tuple(body.scale)==(1,1,1)
before=[v.co.copy() for v in mesh.vertices]
faces=[tuple(p.vertices) for p in mesh.polygons]
uvs=[tuple(v.uv) for v in mesh.uv_layers.active.data]
bounds=lambda:[[min(v.co[a] for v in mesh.vertices) for a in range(3)],[max(v.co[a] for v in mesh.vertices) for a in range(3)]]
old_bounds=bounds()
adj={v.index:set() for v in mesh.vertices}
for edge in mesh.edges:
 a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
parts=[];left=set(adj)
while left:
 todo=[min(left)];ids=set()
 while todo:
  i=todo.pop()
  if i in ids:continue
  ids.add(i);todo.extend(adj[i]-ids)
 left-=ids;parts.append(sorted(ids))
assert len(parts)==272
moved=set()
for n,ids in enumerate(parts[:12]):
 assert len(ids)==8
 center=sum((before[i] for i in ids),Vector())/len(ids)
 if n<2:
  assert abs(max(before[i].y for i in ids)-min(before[i].y for i in ids)-16)<1e-5
  y0=min(before[i].y for i in ids)
  for i in ids:
   v=mesh.vertices[i].co;v.x+=(-3.45 if n==0 else -3.08)-center.x;v.y=y0+(v.y-y0)*.375
 else:
  layer=(n-2)//5;bay=(n-2)%5
  for i in ids:
   v=mesh.vertices[i].co;v.x+=-3.25-center.x;v.y+=(-7.8+1.2*bay)-center.y;v.z+=.26*layer
 moved.update(ids)
ids=parts[263];assert len(ids)==8
center=sum((before[i] for i in ids),Vector())/8
c,s=math.cos(.18),math.sin(.18)
for i in ids:
 v=mesh.vertices[i].co;d=before[i]-center
 v.x=-2.72+c*d.x-s*d.y;v.y=-5.5+(s*d.x+c*d.y)*.8
moved.update(ids);mesh.update()
assert len(moved)==104
assert all(tuple(v.co)==tuple(before[i]) for i,v in enumerate(mesh.vertices) if i not in moved)
assert [tuple(p.vertices) for p in mesh.polygons]==faces
assert [tuple(v.uv) for v in mesh.uv_layers.active.data]==uvs
assert bounds()==old_bounds,(bounds(),old_bounds)
triangles=sum(len(f)-2 for f in faces);assert triangles==660
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'trestle-landmarks.blend'))
bpy.ops.object.select_all(action='DESELECT');body.hide_set(False);body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(PACK/'mine-spur-kit.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=PACK/'trestle-landmark-pack-contract.json';pack=json.loads(p.read_text());pack['blend']['sha256']=sha(PACK/'trestle-landmarks.blend');pack['assets']['mine-spur-kit']['sha256']=sha(PACK/'mine-spur-kit.glb')
pack['assets']['mine-spur-kit']['railStockCorrection']={'date':'2026-09-20','recipe':str(Path(__file__).relative_to(ROOT)),'inputCommit':PIN,'inputBlendSha256':hashlib.sha256(original).hexdigest(),'movedVertices':104,'trianglesBeforeAfter':[660,660],'scope':'Duplicate visual rails and sleepers become stored rail beside the bins; live route, original other geometry, UVs, atlas, mounts, collision and overall bounds are unchanged.'}
p.write_text(json.dumps(pack,indent=2)+'\n')
(RAW/'result.json').write_text(json.dumps(pack['assets']['mine-spur-kit'],indent=2)+'\n')
print('TRESTLE_RAIL_STOCK',json.dumps({'movedVertices':len(moved),'triangles':triangles,'boundsUnchanged':True,'raw':str(RAW)}))
