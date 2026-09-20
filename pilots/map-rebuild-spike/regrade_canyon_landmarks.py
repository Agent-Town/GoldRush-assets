"""Repaint the saved Canyon pack from its tracked atlas recipe; never rebuild geometry.

Run Blender from the game checkout. The original geometry/UVs are asserted
unchanged, and every body receives the same packed atlas.
"""
from pathlib import Path
import hashlib, importlib.util, json, shutil, sys, time
import bpy

ROOT = Path.cwd()
assert (ROOT / 'src/world/Terrain3dClaimPilot.ts').is_file(), 'Run from the game checkout'
OUT = Path(__file__).resolve().parent
PACK = OUT / 'landmarks/canyon-works'
RAW = ROOT / 'artifacts/sol/map-art-campaign-2/_raw/run-4' / f'canyon-grade-{time.time_ns()}'
RAW.mkdir(parents=True)
def geometry():
    return {o.name: {'vertices': [tuple(v.co) for v in o.data.vertices],
        'faces': [tuple(p.vertices) for p in o.data.polygons],
        'uv': [tuple(v.uv) for v in o.data.uv_layers.active.data],
        'bounds': [tuple(v) for v in o.bound_box]} for o in bpy.data.objects if o.type == 'MESH'}

bpy.ops.wm.open_mainfile(filepath=str(PACK / 'canyon-works-landmarks.blend'))
before = geometry()
sys.argv.append('--atlas-only')  # Select the builder's game-checkout input root.
spec = importlib.util.spec_from_file_location('canyon_atlas_recipe', OUT / 'build_landmark_packs.py')
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)
atlas, generated = recipe.make_atlas('canyon-works', recipe.E3_ATLAS_RECIPES['canyon-works'], output_root=RAW)
destination = PACK / generated.name
shutil.copy2(generated, destination)
atlas.filepath_raw = '//' + destination.name
atlas.pack()
for material in bpy.data.materials:
    if material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE': node.image = atlas
assert geometry() == before
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK / 'canyon-works-landmarks.blend'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p = PACK / 'canyon-works-landmark-pack-contract.json'
pack = json.loads(p.read_text())
for name, record in pack['assets'].items():
    bpy.ops.object.select_all(action='DESELECT')
    body = bpy.data.objects[name]; body.select_set(True); bpy.context.view_layer.objects.active = body
    path = OUT / record['asset']
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials='EXPORT', export_extras=True)
    assert sum(len(f.vertices)-2 for f in body.data.polygons) == record['triangles']
    record['sha256'] = sha(path)
pack['atlas']['sha256'] = sha(destination)
pack['atlas']['recipe'] = 'build_landmark_packs.py:E3_CANYON_ROLE_COLORS'
pack['blend']['sha256'] = sha(PACK / 'canyon-works-landmarks.blend')
p.write_text(json.dumps(pack, indent=2) + '\n')
(RAW / 'verification.json').write_text(json.dumps({'originalGeometryAndUVsPreserved': True,
    'bodies': list(before), 'atlasSha256': sha(destination)}, indent=2) + '\n')
print('CANYON_REGRADED', sha(destination))
