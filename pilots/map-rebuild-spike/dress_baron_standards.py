"""Bring the existing company standards into the approach; no new image pixels.

Blender --background --python-exit-code 1 --python this.py
Uses the accepted, pinned per-body source, retains every original vertex/UV,
and grounds three smaller standards on the delivered terrain. Re-running never
accumulates geometry. Mounts, collision and the fort remain unchanged.
"""
from pathlib import Path
import hashlib, json, subprocess, time
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PACK = OUT / 'landmarks/baron'
PIN = '6b7f2e49a2cf37379525825f4b605482ee825562'
BODY = 'oxblood_banners'
REL = f'assets/pilots/map-rebuild-spike/landmarks/baron/{BODY}.blend'
RAW = ROOT/'artifacts/sol/map-art-campaign-2/_raw/run-3'/f'baron-standards-{time.time_ns()}'
RAW.mkdir(parents=True)
original = subprocess.check_output(['git', 'show', f'{PIN}:{REL}'], cwd=ROOT)
(RAW/'input.blend').write_bytes(original)
bpy.ops.wm.open_mainfile(filepath=str(RAW/'input.blend'))
body = bpy.data.objects[BODY]
assert tuple(body.location) == (0,0,0) and tuple(body.scale) == (1,1,1)
mesh = body.data
assert sum(len(p.vertices)-2 for p in mesh.polygons) == 1500
# The six disconnected pieces around the central standard form its complete
# closed base, pole, crossbar, embroidered cloth and two brass bands.
faces = [p for p in mesh.polygons if all(-.31 <= mesh.vertices[i].co.x <= 2.16 and 7.70 <= mesh.vertices[i].co.y <= 8.30 for i in p.vertices)]
assert sum(len(p.vertices)-2 for p in faces) == 300
ids = sorted({i for p in faces for i in p.vertices})
source = {i:mesh.vertices[i].co.copy() for i in ids}
source_base = min(co.z for co in source.values())
existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(OUT/'baron-terrain.glb'))
imported = [o for o in bpy.data.objects if o not in existing]
terrain, = [o for o in imported if o.type == 'MESH']
inverse = terrain.matrix_world.inverted()
def height(x,z):
    hit, point, _, _ = terrain.ray_cast(inverse@Vector((x,-z,100)), inverse.to_3x3()@Vector((0,0,-1)))
    assert hit, (x,z)
    return (terrain.matrix_world@point).z
mount_height = height(0,0)
vertices, polygons, uvs, sites = [], [], [], []
for x,z,scale in [(-3.6,10.0,.80),(2.7,7.8,.60),(-8.0,7.2,.65)]:
    ground = height(x,z)
    assert ground > .025 and abs(x)>2.5
    sites.append({'x':x,'z':z,'scale':scale,'groundY':ground})
    mapping = {i:len(vertices)+j for j,i in enumerate(ids)}
    for i in ids:
        co=source[i]
        vertices.append((x+co.x*scale, -z+(co.y-8.0)*scale, ground-mount_height-.025+(co.z-source_base)*scale))
    for face in faces:
        polygons.append(tuple(mapping[i] for i in face.vertices))
        uvs.extend(tuple(mesh.uv_layers.active.data[i].uv) for i in face.loop_indices)
for obj in imported:bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.outliner.orphans_purge(do_recursive=True)
addition = bpy.data.meshes.new('BaronApproachStandards')
addition.from_pydata(vertices,[],polygons)
addition.materials.append(mesh.materials[0])
uv = addition.uv_layers.new(name='UVMap')
assert len(uv.data)==len(uvs)
for i,value in enumerate(uvs):uv.data[i].uv=value
obj = bpy.data.objects.new('BaronApproachStandards',addition)
bpy.context.collection.objects.link(obj)
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True);obj.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
body['approach_standards']=len(sites)
body['approach_recipe']=str(Path(__file__).relative_to(ROOT))
body['source_tier']='derive'
triangles=sum(len(p.vertices)-2 for p in body.data.polygons)
assert triangles==2400 and triangles<=3000
assert [o.name for o in bpy.data.objects if o.type=='MESH']==[BODY]
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/f'{BODY}.blend'))
bpy.ops.export_scene.gltf(filepath=str(PACK/f'{BODY}.glb'),export_format='GLB',use_selection=True,
    export_apply=True,export_cameras=False,export_lights=False,export_animations=False,
    export_materials='EXPORT',export_extras=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
path=PACK/'baron-landmark-pack-contract.json';pack=json.loads(path.read_text());record=pack['assets'][BODY]
record.update(triangles=triangles,sha256=sha(PACK/f'{BODY}.glb'),sourceTier='derive')
record['blend']['sha256']=sha(PACK/f'{BODY}.blend')
bounds=[body.matrix_world@Vector(c) for c in body.bound_box]
record['bounds']={key:[round(fn(p[i] for p in bounds),4) for i in range(3)] for key,fn in [('min',min),('max',max)]}
record['approachCorrection']={'date':'2026-09-20','inputCommit':PIN,'inputBlendSha256':hashlib.sha256(original).hexdigest(),
    'recipe':str(Path(__file__).relative_to(ROOT)),'standards':len(sites),'addedTriangles':900,
    'atlas':'unchanged; exact embroidered-cloth and pole UVs reused',
    'terrain':'unchanged; bases ray-cast onto delivered triangles','sites':sites}
path.write_text(json.dumps(pack,indent=2)+'\n')
path=OUT/'landmarks/landmark-source-ledger.json';ledger=json.loads(path.read_text())
ledger['packs']['baron'][BODY].update({k:record[k] for k in ['sourceTier','sources']})
path.write_text(json.dumps(ledger,indent=2)+'\n')
(RAW/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print('BARON_STANDARDS',json.dumps({'standards':len(sites),'triangles':triangles,'raw':str(RAW)}))
