"""Repack native material art into the authoritative saved landmark source; preserve geometry."""
import hashlib
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / 'assets/pilots/map-rebuild-spike/landmarks/moth-season'
RAW = ROOT / 'assets/raw/moth-season-landmark-material-atlas-v1.png'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(PACK / 'moth-season-landmarks.blend'))
objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
assert len(objects) == 5
geometry = {obj.name: ([tuple(v.co) for v in obj.data.vertices], [tuple(p.vertices) for p in obj.data.polygons]) for obj in objects}
image = bpy.data.images.load(str(RAW), check_existing=False)
image.scale(1024, 1024)
image.filepath_raw = str(PACK / 'moth-season-landmarks-atlas.png')
image.file_format = 'PNG'
image.colorspace_settings.name = 'sRGB'
image.save()
image.pack()
materials = {material for obj in objects for material in obj.data.materials}
nodes = [node for material in materials for node in material.node_tree.nodes if node.type == 'TEX_IMAGE']
assert len(nodes) == 1
previous = nodes[0].image
nodes[0].image = image
if previous is not None and previous.users == 0:
    bpy.data.images.remove(previous)
image.name = 'MothSeasonLandmarkMaterialAtlas'
# Reuse the existing lighter zinc cell for the north frame, keeping its scale and geometry.
mesh = bpy.data.objects['north-migration-watch-gate'].data
changed = 0
zinc_faces = 0
for face in mesh.polygons:
    loops = [mesh.uv_layers.active.data[i] for i in face.loop_indices]
    u = sum(loop.uv.x for loop in loops) / len(loops)
    v = sum(loop.uv.y for loop in loops) / len(loops)
    if int((1 - v) * 4) == 3:
        if int(u * 4) == 1:
            for loop in loops:
                loop.uv.x += 0.25
            changed += 1
        elif int(u * 4) == 2:
            zinc_faces += 1
assert (changed, zinc_faces) in {(1150, 6), (0, 1156)}, (changed, zinc_faces)
for obj in objects:
    assert geometry[obj.name] == ([tuple(v.co) for v in obj.data.vertices], [tuple(p.vertices) for p in obj.data.polygons])
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK / 'moth-season-landmarks.blend'))
contract_path = PACK / 'moth-season-landmark-pack-contract.json'
contract = json.loads(contract_path.read_text())
assert set(contract['assets']) == {obj.name for obj in objects}
for obj in objects:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    target = PACK / (obj.name + '.glb')
    bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB', use_selection=True, export_apply=True, export_animations=False, export_extras=True)
    contract['assets'][obj.name]['sha256'] = sha(target)
contract['atlas'].update(sha256=sha(PACK / 'moth-season-landmarks-atlas.png'), source=str(RAW.relative_to(ROOT)), recipe=str(Path(__file__).resolve().relative_to(ROOT)))
contract['blend']['sha256'] = sha(PACK / 'moth-season-landmarks.blend')
contract_path.write_text(json.dumps(contract, indent=2) + '\n')
