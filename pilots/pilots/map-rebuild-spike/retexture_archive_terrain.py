"""Rebuild Archive floor material while retaining the authored terrain and mount contract."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import bpy

SOURCE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('archive_floor', SOURCE / 'build_e10_archive_terrain.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
contract = json.loads((SOURCE / 'archive-world-terrain-contract.json').read_text())
_, table = builder.documents()
assert contract['maskTruth'] == table['maskTruth']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE / 'archive-world-terrain.blend'))
meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH']
assert len(meshes) == 1
terrain = meshes[0]
snapshot = lambda: ([tuple(v.co) for v in terrain.data.vertices], [tuple(p.vertices) for p in terrain.data.polygons], [tuple(v.uv) for v in terrain.data.uv_layers.active.data])
before = snapshot()
builder.OUT = out
image, atlas = builder.make_atlas(table)
nodes = [node for mat in terrain.data.materials for node in mat.node_tree.nodes if node.type == 'TEX_IMAGE']
assert len(nodes) == 1
previous = nodes[0].image
nodes[0].image = image
if previous is not None and previous.users == 0:
    bpy.data.images.remove(previous)
image.name = builder.PROFILE['atlas']
assert before == snapshot()
bpy.context.preferences.filepaths.save_version = 0
blend = out / 'archive-world-terrain.blend'
glb = out / 'archive-world-terrain.glb'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.object.select_all(action='DESELECT')
terrain.select_set(True)
bpy.context.view_layer.objects.active = terrain
bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_apply=True, export_cameras=False, export_lights=False, export_animations=False, export_extras=True)
contract['sourceArt'] = [str(p.relative_to(builder.ROOT)) for p in (builder.FLOOR, builder.claim.BANK_A)]
contract['materialRecipe'] = str(Path(__file__).resolve().relative_to(builder.ROOT))
for key, path in [('blend', blend), ('glb', glb), ('atlas', atlas)]:
    contract['files'][key] = {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
(out / 'archive-world-terrain-contract.json').write_text(json.dumps(contract, indent=2) + '\n')
print('PASS: native floor atlas exported; terrain geometry, UVs, masks and mounts preserved')
