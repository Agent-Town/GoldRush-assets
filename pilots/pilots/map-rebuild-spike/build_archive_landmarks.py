"""Rebuild Archive library bodies using the existing pack for unchanged entry/marker assets."""
import argparse, bpy, importlib.util, json, runpy, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('factory', ROOT / 'assets/pilots/map-rebuild-spike/build_landmark_packs.py')
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
source = ROOT / 'assets/pilots/map-rebuild-spike/landmarks/archive-world'
contract = json.loads((source/'archive-world-landmark-pack-contract.json').read_text())
contract['recipe'] = str(Path(__file__).resolve().relative_to(ROOT))
bpy.ops.wm.open_mainfile(filepath=str(source/'archive-world-landmarks.blend'))
material = bpy.data.objects['west-stack-ruin'].data.materials[0]
for identifier, variant in [('west-stack-ruin','west'),('east-stack-ruin','east'),('warning-shelf-ruin',None)]:
    previous = bpy.data.objects[identifier]
    previous_mesh = previous.data
    bpy.data.objects.remove(previous, do_unlink=True)
    if previous_mesh.users == 0:
        bpy.data.meshes.remove(previous_mesh)
    parts = f.archive_stack_ruin_parts(variant) if variant else f.archive_warning_shelf_parts()
    asset = f.finish_asset(parts, identifier, material, 'archive-world', {'tier':'derive'})
    r = contract['assets'][identifier]
    r.update(sourceTier='derive', sources=['assets/raw/plate-contract-e10-archive-world.png'], triangles=sum(len(p.vertices)-2 for p in asset.data.polygons), bounds=f.glb_bounds(asset))
    assert r['triangles'] <= r['triangleBudget']
    assert r['bounds']['max'][0]-r['bounds']['min'][0] <= (8.4 if variant is None else 7.4)+.001
    assert r['bounds']['max'][1]-r['bounds']['min'][1] <= (5.4 if variant is None else 5.2)+.001
    print(identifier, r['triangles'],r['bounds'])
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'archive-world-landmarks.blend'))
(out/'archive-world-landmark-pack-contract.json').write_text(json.dumps(contract,indent=2)+'\n')

# Reuse the material/UV export recipe after replacing only the three library bodies.
sys.argv = [sys.argv[0], '--', '--source', str(out), '--out', str(out)]
runpy.run_path(str(ROOT / 'assets/pilots/map-rebuild-spike/retexture_archive_landmarks.py'), run_name='__main__')
