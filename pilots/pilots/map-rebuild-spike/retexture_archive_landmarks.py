"""Repack native Archive materials and repair collapsed planar UVs without changing geometry."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / 'assets/pilots/map-rebuild-spike/landmarks/archive-world'
RAW = ROOT / 'assets/raw/archive-world-landmark-material-atlas-v1.png'
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--source', type=Path, default=PACK)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
PACK = args.source.resolve()
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=True)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
contract = json.loads((PACK / 'archive-world-landmark-pack-contract.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(PACK / 'archive-world-landmarks.blend'))
objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
assert {obj.name for obj in objects} == set(contract['assets']) and len(objects) == 5
snapshot = lambda obj: ([tuple(v.co) for v in obj.data.vertices], [tuple(p.vertices) for p in obj.data.polygons])
before = {obj.name: snapshot(obj) for obj in objects}
for obj in objects:
    mesh = obj.data
    low = [min(v.co[axis] for v in mesh.vertices) for axis in range(3)]
    span = max(max(v.co[axis] for v in mesh.vertices) - low[axis] for axis in range(3))
    assert span > 0
    uv = mesh.uv_layers.active.data
    for face in mesh.polygons:
        # Preserve each face's material cell; project on its dominant plane at one isotropic scale.
        column = int(sum(uv[i].uv.x for i in face.loop_indices) / len(face.loop_indices) * 4)
        row = int(sum(uv[i].uv.y for i in face.loop_indices) / len(face.loop_indices) * 4)
        assert 0 <= column < 4 and 0 <= row < 4
        normal_axis = max(range(3), key=lambda axis: abs(face.normal[axis]))
        a, b = [axis for axis in range(3) if axis != normal_axis]
        for i in face.loop_indices:
            co = mesh.vertices[mesh.loops[i].vertex_index].co
            uv[i].uv = ((column + .08 + (co[a] - low[a]) / span * .84) / 4,
                        (row + .08 + (co[b] - low[b]) / span * .84) / 4)
image = bpy.data.images.load(str(RAW), check_existing=False)
image.colorspace_settings.name = 'sRGB'
assert min(image.size) > 0, 'native atlas must decode before resizing'
image.scale(1024, 1024)
image.filepath_raw = str(out / 'archive-world-landmarks-atlas.png')
image.file_format = 'PNG'
image.save()
image.pack()
materials = {mat for obj in objects for mat in obj.data.materials}
nodes = [node for mat in materials for node in mat.node_tree.nodes if node.type == 'TEX_IMAGE']
assert len(nodes) == 1
previous = nodes[0].image
nodes[0].image = image
if previous is not None and previous.users == 0:
    bpy.data.images.remove(previous)
image.name = 'ArchiveWorldLandmarkMaterialAtlas'
assert all(before[obj.name] == snapshot(obj) for obj in objects)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'archive-world-landmarks.blend'))
for obj in objects:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    target = out / (obj.name + '.glb')
    bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB', use_selection=True, export_apply=True, export_animations=False, export_extras=True)
    contract['assets'][obj.name]['sha256'] = sha(target)
contract['atlas'].update(sha256=sha(out / 'archive-world-landmarks-atlas.png'), source=str(RAW.relative_to(ROOT)), recipe=str(Path(__file__).resolve().relative_to(ROOT)))
contract['blend']['sha256'] = sha(out / 'archive-world-landmarks.blend')
(out / 'archive-world-landmark-pack-contract.json').write_text(json.dumps(contract, indent=2) + '\n')
print('PASS: five bodies exported with unchanged geometry and material cells; isotropic planar UVs')
