"""Add closed reed clumps to the saved Twin Banks body; preserve terrain and mount truth.

Run with Blender --background --python <this file>. The pinned, accepted per-body
blend is the input, so repeated runs do not accumulate geometry. No image pixels
are generated: new faces reuse the pack atlas's existing green pigment cell.
"""
from pathlib import Path
import hashlib, json, math, subprocess, time
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PACK = OUT / 'landmarks/twin-banks'
PIN = '6b7f2e49a2cf37379525825f4b605482ee825562'
BODY = 'floodplain_dressing_pack'
REL = f'assets/pilots/map-rebuild-spike/landmarks/twin-banks/{BODY}.blend'
RAW = ROOT / 'artifacts/sol/map-art-campaign-2/_raw/run-3' / f'twin-reeds-{time.time_ns()}'
RAW.mkdir(parents=True)
original = subprocess.check_output(['git', 'show', f'{PIN}:{REL}'], cwd=ROOT)
(RAW / 'input.blend').write_bytes(original)
bpy.ops.wm.open_mainfile(filepath=str(RAW / 'input.blend'))
body = bpy.data.objects[BODY]
assert tuple(body.location) == (0, 0, 0) and tuple(body.scale) == (1, 1, 1)
assert sum(len(p.vertices) - 2 for p in body.data.polygons) == 944
material = body.data.materials[0]
existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(OUT / 'twin-banks-terrain.glb'))
imported = [o for o in bpy.data.objects if o not in existing]
terrain, = [o for o in imported if o.type == 'MESH']
inverse = terrain.matrix_world.inverted()
def height(x, z):
    hit, point, _, _ = terrain.ray_cast(inverse @ Vector((x, -z, 100)), inverse.to_3x3() @ Vector((0, 0, -1)))
    assert hit, (x, z)
    return (terrain.matrix_world @ point).z
base_y = height(0, 0)
contract = json.loads((OUT / 'twin-banks-terrain-contract.json').read_text())
regions = contract['maskTruth']['waterMask']['regions']
channels = [r for r in regions if r['kind'] == 'polyline_band']
fords = [r for r in regions if r['zone'] == 'ford']
vertices, faces, sites = [], [], []
def blade(x, z, y, angle, length, radius):
    start = len(vertices)
    # Closed triangular section; two rings and a leaning tip give a reed silhouette.
    for level, r, lean in [(0, radius, 0), (length * .6, radius * .55, .14)]:
        for corner in range(3):
            a = angle + corner * math.tau / 3
            vertices.append((x + math.cos(a) * r + math.cos(angle) * lean, -z + math.sin(a) * r + math.sin(angle) * lean, y + level))
    vertices.append((x + math.cos(angle) * .32, -z + math.sin(angle) * .32, y + length))
    faces.append(tuple(start + i for i in (2, 1, 0)))
    for i in range(3):
        j = (i + 1) % 3
        faces.extend([(start+i, start+j, start+j+3), (start+i, start+j+3, start+i+3), (start+i+3, start+j+3, start+6)])
for channel in channels:
    side = 1 if channel['id'] == 'north-channel' else -1
    for x in [-25, -22, -11, -8, -5, -2, 2, 5, 8, 11, 22, 25]:
        for a, b in zip(channel['points'], channel['points'][1:]):
            if a['x'] <= x <= b['x']:
                z = a['z'] + (b['z'] - a['z']) * (x - a['x']) / (b['x'] - a['x'])
                break
        # Outer dry bank, never a ford or the central gravel plait.
        z += side * (channel['halfWidth'] + 1.05)
        assert not any(f['minX']-.5 <= x <= f['maxX']+.5 and f['minZ']-.5 <= z <= f['maxZ']+.5 for f in fords)
        for offset in [-.4, .4]:
            px, pz = x + offset, z + side * abs(offset) * .4
            ground = height(px, pz)
            assert ground > .025
            sites.append({'x': px, 'z': pz, 'groundY': ground})
            for leaf in range(3):
                angle = (len(sites) * 1.37 + leaf * 2.1) % math.tau
                blade(px + .11*math.cos(angle), pz + .11*math.sin(angle), ground-base_y-.035,
                      angle, .75 + ((len(sites)+leaf*3) % 7)*.11, .07)
mesh = bpy.data.meshes.new('TwinBanksClosedReeds')
mesh.from_pydata(vertices, [], faces)
mesh.materials.append(material)
uv = mesh.uv_layers.new(name='UVMap')
for face in mesh.polygons:
    for j, loop in enumerate(face.loop_indices):
        uv.data[loop].uv = (.545 + (j % 2)*.12, .555 + (j // 2)*.12)
reeds = bpy.data.objects.new('TwinBanksClosedReeds', mesh)
bpy.context.collection.objects.link(reeds)
for obj in imported: bpy.data.objects.remove(obj, do_unlink=True)
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True); reeds.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body['riparian_clumps'] = len(sites)
body['riparian_recipe'] = str(Path(__file__).relative_to(ROOT))
body['source_tier'] = 'derive'
triangles = sum(len(p.vertices)-2 for p in body.data.polygons)
assert triangles == 944 + len(faces) <= 3000
# Keep only the authoritative body in its saved source; imported terrain is read-only input.
assert [o.name for o in bpy.data.objects if o.type == 'MESH'] == [BODY]
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK / f'{BODY}.blend'))
bpy.ops.export_scene.gltf(filepath=str(PACK/f'{BODY}.glb'), export_format='GLB', use_selection=True,
    export_apply=True, export_cameras=False, export_lights=False, export_animations=False,
    export_materials='EXPORT', export_extras=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
path = PACK / 'twin-banks-landmark-pack-contract.json'
pack = json.loads(path.read_text()); record = pack['assets'][BODY]
record.update(triangles=triangles, sha256=sha(PACK/f'{BODY}.glb'), sourceTier='derive')
record['blend']['sha256'] = sha(PACK/f'{BODY}.blend')
record['sources'] = ['assets/pilots/run3d/sluice.glb', 'assets/pilots/run3d/stockpile.glb', 'assets/raw/plate-contract-twin-banks.png']
bounds = [body.matrix_world @ Vector(c) for c in body.bound_box]
record['bounds'] = {key: [round(fn(p[i] for p in bounds),4) for i in range(3)] for key,fn in [('min',min),('max',max)]}
record['riparianCorrection'] = {'date':'2026-09-20','inputCommit':PIN,'inputBlendSha256':hashlib.sha256(original).hexdigest(),
    'recipe':str(Path(__file__).relative_to(ROOT)),'clumps':len(sites),'addedTriangles':len(faces),
    'atlas':'unchanged; existing green pigment cell','terrain':'unchanged; bases ray-cast onto delivered triangles',
    'sites':sites}
path.write_text(json.dumps(pack,indent=2)+'\n')
path = OUT/'landmarks/landmark-source-ledger.json'; ledger=json.loads(path.read_text())
ledger['packs']['twin-banks'][BODY].update({k:record[k] for k in ['sourceTier','sources']})
path.write_text(json.dumps(ledger,indent=2)+'\n')
(RAW/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print('TWIN_REEDS',json.dumps({'clumps':len(sites),'triangles':triangles,'raw':str(RAW)}))
