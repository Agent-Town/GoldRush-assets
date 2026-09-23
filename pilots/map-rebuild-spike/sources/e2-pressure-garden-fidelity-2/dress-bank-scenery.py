"""Low render-only stones on the delivered bank, never a height/collision source.
Run Blender from the game checkout. The preserved source makes reruns idempotent.
"""
from pathlib import Path
import bpy, json, math, random, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

P = Path.cwd() / 'assets/pilots/map-rebuild-spike'
S = P / 'sources/e2-pressure-garden-fidelity-2'
bpy.ops.wm.open_mainfile(filepath=str(S / 'panorama-input.blend'))
panorama = next(o for o in bpy.data.objects if o.type == 'MESH')
original_vertices = len({tuple(v.co) for v in panorama.data.vertices})
bpy.ops.import_scene.gltf(filepath=str(P / 'pressure-garden-terrain.glb'))
terrain = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
world = [terrain.matrix_world @ v.co for v in terrain.data.vertices]
bvh = BVHTree.FromPolygons(world, [tuple(f.vertices) for f in terrain.data.polygons])
def height(x, y):
    hit = bvh.ray_cast(Vector((x, y, 30)), Vector((0, 0, -1)))[0]
    assert hit is not None
    return hit.z

stone = bpy.data.materials.new('GardenBankStone'); stone.use_nodes = True
bsdf = stone.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Roughness'].default_value = .93
tex = stone.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(str(S / 'engraved-river-gravel.png'))
# Preserve native source pixels on disk; resample only the embedded GLB atlas
# to the panorama's declared 2048-square texture contract.
tex.image.scale(2048, 2048); tex.image.pack()
stone.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
rng = random.Random(90223); parts = []; records = []
for side in (-1, 1):
    # The declared crossing is x +/-6. Keep its approach entirely bare.
    for i in range(32):
        x = -44 + i * 88 / 31 + rng.uniform(-.8, .8)
        if abs(x) < 9.0: continue
        for small in (False, True):
            px = x + (rng.uniform(.45, .85) if small else 0)
            py = side * (6.18 + rng.uniform(-.15, .48))
            sx = rng.uniform(.38, .64) if small else rng.uniform(.95, 1.62)
            sy = rng.uniform(.22, .32) if small else rng.uniform(.40, .72)
            sz = rng.uniform(.12, .18) if small else rng.uniform(.18, .28)
            floor = height(px, py)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=(px, py, floor + sz * .25))
            o = bpy.context.object; o.name = 'BankStone'; o.scale = (sx, sy, sz)
            o.rotation_euler.z = rng.uniform(-.55, .55)
            for v in o.data.vertices: v.co *= rng.uniform(.87, 1.13)
            o.data.materials.append(stone)
            uv = o.data.uv_layers.new(name='UVMap')
            for face in o.data.polygons:
                for loop in face.loop_indices:
                    v = o.data.vertices[o.data.loops[loop].vertex_index].co
                    uv.data[loop].uv = ((v.x + 1) * .32 + rng.uniform(0, .015), (v.y + 1) * .32)
            parts.append(o); records.append({'x':px, 'z':py, 'ground':floor, 'heightRadius':sz, 'maxRadiusXZ':max(sx,sy)})
# 104 low stones, 2080 triangles would exceed the 1888 remaining budget.
# Keep one small companion per alternating cluster, deterministically.
for i in range(len(parts)-1, -1, -1):
    if i % 4 == 3:
        bpy.data.objects.remove(parts.pop(i), do_unlink=True); records.pop(i)
bpy.ops.object.select_all(action='DESELECT')
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
rocks = bpy.context.object; rocks.name = 'PressureGardenBankStones'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
rocks['renderOnly'] = True; rocks['heightAuthority'] = False
bpy.data.objects.remove(terrain, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
panorama.select_set(True); rocks.select_set(True); bpy.context.view_layer.objects.active = panorama
triangles = sum(len(f.vertices)-2 for o in (panorama, rocks) for f in o.data.polygons)
assert triangles <= 4000
blend = P / 'pressure-garden-panorama.blend'; glb = P / 'pressure-garden-panorama.glb'
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_apply=True, export_cameras=False, export_lights=False, export_animations=False, export_materials='EXPORT', export_extras=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
c = json.loads((S / 'panorama-input-contract.json').read_text())
c.update(meshCount=2, primitiveCount=2, materialCount=2, triangles=triangles, vertices=original_vertices+len({tuple(v.co) for v in rocks.data.vertices}))
c['texture'].update(count=2, secondAtlas='sources/e2-pressure-garden-fidelity-2/engraved-river-gravel.png', secondAtlasSourceSize=[1254,1254], secondAtlasEncoding='Blender resamples the native source to the shared 2048-square panorama contract; original PNG remains unchanged')
c['sourceArt'].append('assets/pilots/map-rebuild-spike/sources/e2-pressure-garden-fidelity-2/engraved-river-gravel.png')
c['bankScenery'] = {'recipe':'sources/e2-pressure-garden-fidelity-2/dress-bank-scenery.py', 'count':len(records), 'triangles':triangles-2112, 'renderOnly':True, 'fordClearHalfWidth':6, 'heightSource':'raycast unchanged delivered terrain; scenery never enters height sampler'}
for kind,p in [('blend',blend),('glb',glb)]: c['files'][kind] = {'bytes':p.stat().st_size,'sha256':sha(p)}
(P / 'pressure-garden-panorama-contract.json').write_text(json.dumps(c,indent=2)+'\n')
(S / 'bank-grounding.json').write_text(json.dumps(records,indent=2)+'\n')
print('GARDEN_BANK', json.dumps(c['bankScenery']))
