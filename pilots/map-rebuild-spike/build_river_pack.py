"""F-CORR4-18: build the raw 128 m River, preserving its sampled visual heights.

From the game checkout: Blender --background --python assets/pilots/map-rebuild-spike/build_river_pack.py
No raster generation. All three atlases are byte-for-byte copies of existing art.
The five low stone groups are decorative, with no collision or walk surfaces.
"""
import hashlib
import json
import math
import random
import shutil
from pathlib import Path
import bpy

ROOT = Path.cwd()
OUT = ROOT / 'assets/pilots/map-rebuild-spike'
PACK = OUT / 'landmarks/river'
PACK.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources = {
    'river-terrain-atlas.png': 'assets/processed/terrain-bank-tile.png',
    'river-panorama-atlas.png': 'assets/raw/plate-contract-e10-river.png',
    'landmarks/river/river-landmarks-atlas.png': 'assets/pilots/map-rebuild-spike/landmarks/twin-banks/twin-banks-landmarks-atlas.png',
}
for target, source in sources.items():
    shutil.copy2(ROOT / source, OUT / target)
grid = json.loads((OUT / 'river-fallback-height-grid.json').read_text())
heights = grid['heights']
truth = json.loads((ROOT / 'assets/contracts/epoch-10-deepsky/mask-tables/e10-river.json').read_text())
assert len(heights) == 129 * 129
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version = 0


def material(name, path):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = .86
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(path), check_existing=True)
    tex.image.pack()
    tex.extension = 'REPEAT'
    mat.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    return mat, tex.image


def mesh(name, verts, faces, mat, uvfun, smooth=False):
    data = bpy.data.meshes.new(name + 'Mesh')
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(mat)
    uv = data.uv_layers.new(name='RiverPaintUV')
    for poly in data.polygons:
        poly.use_smooth = smooth
        for li in poly.loop_indices:
            uv.data[li].uv = uvfun(data.vertices[data.loops[li].vertex_index].co)
    return obj


def export(obj, path):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
        export_apply=True, export_cameras=False, export_lights=False,
        export_animations=False, export_materials='EXPORT', export_extras=True)


def facts(obj, path, budget):
    verts = {tuple(v.co) for v in obj.data.vertices}
    tri = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    assert tri <= budget, (obj.name, tri)
    return dict(meshCount=1, primitiveCount=1, materialCount=1, vertices=len(verts),
        triangles=tri, triangleBudget=budget,
        boundsMeters={'min': [min(v[i] for v in verts) for i in range(3)],
                      'max': [max(v[i] for v in verts) for i in range(3)]}, sha256=sha(path))


def height(x, z):
    x = max(0, min(127.99999, x + 64))
    z = max(0, min(127.99999, z + 64))
    ix, iz = math.floor(x), math.floor(z)
    u, v = x - ix, z - iz
    a, b = heights[iz * 129 + ix: iz * 129 + ix + 2]
    c, d = heights[(iz + 1) * 129 + ix: (iz + 1) * 129 + ix + 2]
    return a + (b-a)*u + (d-b)*v if u >= v else a + (d-c)*u + (c-a)*v


terrain_mat, terrain_image = material('RiverBankPaint', OUT / 'river-terrain-atlas.png')
verts = [(x, -z, heights[(z+64)*129+x+64]) for z in range(-64,65) for x in range(-64,65)]
faces = []
for z in range(128):
    for x in range(128):
        i = z * 129 + x
        faces.extend([(i, i+130, i+1), (i, i+129, i+130)])
terrain = mesh('RiverTerrain', verts, faces, terrain_mat, lambda co: ((co.x+64)/12, (co.y+64)/12), True)
terrain['render_only'] = True
terrain['height_socket'] = 'Terrain.visualY'
terrain['tile_id'] = 'frontier-river-claim'
terrain['grid_segments'] = 128
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'river-terrain.blend'))
export(terrain, OUT / 'river-terrain.glb')
terrain_facts = facts(terrain, OUT / 'river-terrain.glb', 60000)
bpy.data.objects.remove(terrain, do_unlink=True)

# Separate distant ridge and dawn sky wall, outside the full square. The renderer
# supplies its existing textured continuation to the 120 m ridge foot; projecting
# the concept photograph directly onto that near apron would magnify its grain.
pano_mat, pano_image = material('RiverDawnHorizon', OUT / 'river-panorama-atlas.png')
verts, faces, segments = [], [], 128
for ring in range(5):
    for i in range(segments):
        a = math.tau * i / segments
        dx, dz = math.cos(a), math.sin(a)
        if ring == 0:
            r, h = 120, -.2
        else:
            r = [0, 150, 170, 190, 190][ring]
            h = [0, 4, 20 + 6*math.sin(a*3+.4) + 4*math.cos(a*7), -8, 115][ring]
        verts.append((r*dx, -r*dz, h))
for ring in reversed(range(4)):
    for i in range(segments):
        a = ring*segments+i
        faces.append((a, a+segments, (ring+1)*segments+(i+1)%segments, ring*segments+(i+1)%segments))
pano = mesh('RiverPanorama', verts, faces, pano_mat, lambda co: (0,0), True)
uv = pano.data.uv_layers.active
for poly in pano.data.polygons:
    strip, i = divmod(poly.index, segments)
    ring = 3-strip  # Backdrop first, nearer silhouettes last at the far-plane depth.
    for corner, li in enumerate(poly.loop_indices):
        rr = ring + (corner in [1,2])
        u = (i + (corner in [2,3])) / segments
        uv.data[li].uv = (u, [.50, .59, .80, .64, 1.0][rr])
for key, value in {'render_only':True, 'panorama':True, 'panorama_law':'v2', 'affects_playfield':False}.items():
    pano[key] = value
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'river-panorama.blend'))
export(pano, OUT / 'river-panorama.glb')
pano_facts = facts(pano, OUT / 'river-panorama.glb', 4000)
bpy.data.objects.remove(pano, do_unlink=True)

rock_mat, rock_image = material('RiverWetStoneAtlas', PACK / 'river-landmarks-atlas.png')
assets, mounts = {}, []
rng = random.Random(418)


def stone(name, x, z, rx, rz, rise, mx, mz, wet):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1,
        location=(x, -z, height(mx+x,mz+z)-height(mx,mz)+rise*.32))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (rx, rz, rise)
    obj.rotation_euler.z = rng.uniform(-.5,.5)
    # Small asymmetric facets keep the stones from reading as repeated spheres.
    for v in obj.data.vertices:
        v.co *= rng.uniform(.91,1.08)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.data.materials.clear()
    obj.data.materials.append(rock_mat)
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    uv = obj.data.uv_layers.new(name='WetStoneUV')
    # Existing neutral stone swatches only; teal is reserved for agent technology.
    row, col = divmod(11 if wet else (5 if rng.random()<.45 else 11), 4)
    for poly in obj.data.polygons:
        axes = [k for k in range(3) if k != max(range(3), key=lambda k: abs(poly.normal[k]))]
        for li in poly.loop_indices:
            co = obj.data.vertices[obj.data.loops[li].vertex_index].co
            uv.data[li].uv = ((col+.1+.8*((co[axes[0]]*.22)%1))/4, (3-row+.1+.8*((co[axes[1]]*.22)%1))/4)
    obj.select_set(False)
    return obj


def complete(identifier, mx, mz, parts, budget=3000):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:
        obj.select_set(True)
    obj = parts[0]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    obj.name = identifier
    for poly in obj.data.polygons:
        poly.material_index = 0
    while len(obj.data.materials)>1:
        obj.data.materials.pop(index=len(obj.data.materials)-1)
    for key, value in {'render_only':True, 'landmark':True, 'mount_id':identifier, 'map_pack':'river', 'era':10, 'blocking':False}.items():
        obj[key] = value
    path = PACK / (identifier+'.glb')
    export(obj, path)
    info = facts(obj, path, budget)
    assets[identifier] = dict(asset='landmarks/river/'+identifier+'.glb', sourceTier='build-new',
        sources=['assets/raw/plate-contract-e10-river.png', sources['landmarks/river/river-landmarks-atlas.png']],
        terrainConformed=True, triangles=info['triangles'], triangleBudget=budget,
        bounds=info['boundsMeters'], sha256=info['sha256'], blocking='none; low decorative stones, no collision or walk surface')
    mounts.append(dict(id=identifier,asset=assets[identifier]['asset'],position=[mx,0,mz],rotation=[0,0,0],scale=[1,1,1]))
    obj.select_set(False)


for name, mx, mz in [('south-west-shore',-18,7.3),('south-east-shore',18,7.3),('north-west-shore',-18,-7.3),('north-east-shore',18,-7.3)]:
    parts = []
    for i in range(28):
        x = [-10.5,-3.5,3.5,10.5][i//7] + rng.uniform(-2.5,2.5)
        z = rng.uniform(-1.4,1.6)
        rx = rng.uniform(.35,1.2)
        parts.append(stone(name+'.'+str(i),x,z,rx,rng.uniform(.34,.88),rng.uniform(.15,.56),mx,mz,abs(mz+z)<7))
    complete(name,mx,mz,parts)
parts=[]
for i in range(20):
    z = rng.uniform(-5.4,5.4)
    x = (-1 if i%2 else 1)*rng.uniform(1.6,2.4)
    parts.append(stone('FordWetStone.'+str(i),x,z,rng.uniform(.19,.40),rng.uniform(.22,.46),rng.uniform(.11,.21),0,0,True))
complete('ford-wet-stones',0,0,parts,2000)
bpy.ops.wm.save_as_mainfile(filepath=str(PACK / 'river-landmarks.blend'))

pano_mount = dict(id='river-panorama',asset='river-panorama.glb',position=[0,0,0],rotation=[0,0,0],scale=[1,1,1],renderOnly=True,
    ownership='Separate dawn panorama beyond the original 128 m square; no playable extension.')
stations = [dict(id=m['id'],heroPositionXZ=[m['position'][0],m['position'][2]+8],offsetFromMountXZ=[0,8],backMeters=8,
    purpose='Labelled shoreline inspection, separate from ordinary entry.') for m in mounts]
texture = lambda im: dict(count=1,width=im.size[0],height=im.size[1],embedded=True)
files = lambda stem: {k:dict(bytes=(OUT/(stem+s)).stat().st_size,sha256=sha(OUT/(stem+s))) for k,s in [('blend','.blend'),('glb','.glb'),('atlas','-atlas.png')]}
terrain_contract = dict(asset='river-terrain.glb',contractId='e10-river',tileId='frontier-river-claim',renderOnly=True,
    simulation='Planar and unchanged. Zero collision mounts; river, ford, water, credits zone, spawn and build rules preserved.',
    heightSocket='Terrain.visualY',theme='Quiet dawn river, irregular low wet-stone shores, open center ford.',
    **terrain_facts,texture=texture(terrain_image),maskTable='assets/contracts/epoch-10-deepsky/mask-tables/e10-river.json',**truth,
    panoramaMount=pano_mount,landmarkMounts=mounts,landmarkAcceptanceStations=stations,
    sourceArt=['assets/raw/plate-contract-e10-river.png', sources['river-terrain-atlas.png']],
    heightDerivation=dict(grid='river-fallback-height-grid.json',sha256=sha(OUT/'river-fallback-height-grid.json'),method='16641 captured fallback visual samples; original planar simulation and sampler source unchanged.'),files=files('river-terrain'))
pano_contract = dict(asset='river-panorama.glb',map='river',renderOnly=True,style='Low irregular distant ridges and warm dawn sky, sampled from the existing River plate.',
    **pano_facts,texture=texture(pano_image),mount=pano_mount,projection=dict(skyRingRadiusMeters=190,skyBottomMeters=-8,skyTopMeters=115,
    groundSkirtInnerBoundaryMeters=dict(shape='circle',radius=120),continuation='Existing renderer edge continuation, with the River bank pigment.'),
    sourceArt=[sources['river-panorama-atlas.png']],files=files('river-panorama'))
pack_contract = dict(map='river',era=10,sourceLadder=['reuse-existing-raster','build-new-geometry'],recipe='build_river_pack.py',
    atlas=dict(asset='landmarks/river/river-landmarks-atlas.png',width=rock_image.size[0],height=rock_image.size[1],sharedByEveryAsset=True,sha256=sha(PACK/'river-landmarks-atlas.png')),
    blend=dict(asset='landmarks/river/river-landmarks.blend',sha256=sha(PACK/'river-landmarks.blend')),assets=assets,mounts=mounts,
    landmarkAcceptanceStations=stations,simulation='none; every body NONBLOCKING, no collider or walk-surface registration',
    fordClearance='Central strip |x| <= 1.1 m remains free of stones across the complete ford; bank groups begin outside |x|=3 m.')
for path, data in [(OUT/'river-terrain-contract.json',terrain_contract),(OUT/'river-panorama-contract.json',pano_contract),(PACK/'river-landmark-pack-contract.json',pack_contract)]:
    path.write_text(json.dumps(data,indent=2)+'\n')
(OUT/'river-terrain.export.json').write_text(json.dumps(dict(profile='terrain',why='Preserve the sampled regular grid and render-only metadata; never decimate.',
    extras=True,animations=False,applyTransforms=True,selection='meshes+anchors',asset='river-terrain.glb',blend='river-terrain.blend',contract='river-terrain-contract.json'),indent=2)+'\n')
(OUT/'river-source-provenance.json').write_text(json.dumps(dict(recipe='build_river_pack.py',rasterGenerated=False,
    copies=[dict(target=k,source=v,sha256=sha(ROOT/v),bytes=(ROOT/v).stat().st_size) for k,v in sources.items()]),indent=2)+'\n')
ledger_path=OUT/'landmarks/landmark-source-ledger.json'
ledger=json.loads(ledger_path.read_text())
ledger['packs']['river']={k:{f:v[f] for f in ['sourceTier','sources','asset']} for k,v in assets.items()}
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
print('RIVER_PACK',json.dumps(dict(terrain=terrain_facts,panorama=pano_facts,bodies={k:v['triangles'] for k,v in assets.items()})))
