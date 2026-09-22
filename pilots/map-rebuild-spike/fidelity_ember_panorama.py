"""Rebuild Ember's scenery from the preserved source, without touching terrain.
Run Blender --background --python this.py from the code checkout.
Native basalt detail and original heat paint; no terrain or mask geometry changes.
"""
from pathlib import Path
import bpy, hashlib, json, math, random

OUT=Path.cwd()/'assets/pilots/map-rebuild-spike'
SOURCE=OUT/'sources/ember-shore-fidelity-1'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'panorama-input.blend'))
bpy.context.preferences.filepaths.save_version=0
panorama=next(o for o in bpy.data.objects if o.type=='MESH')
for image in bpy.data.images:
    if image.source=='FILE' and 'panorama' in image.name.lower():
        image.filepath=str(OUT/'ember-shore-panorama-atlas.png')
        image.pack()

stone=bpy.data.materials.new('EmberShoreBasaltScenery');stone.use_nodes=True
bsdf=stone.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.93
texture=stone.node_tree.nodes.new('ShaderNodeTexImage')
texture.image=bpy.data.images.load(str(OUT/'ember-shore-terrain-atlas.png'),check_existing=True)
texture.image.pack();texture.extension='REPEAT'
stone.node_tree.links.new(texture.outputs['Color'],bsdf.inputs['Base Color'])
panorama.data.materials.append(stone);stone_index=len(panorama.data.materials)-1
ground_faces=0
for face in panorama.data.polygons:
    # Sky vertices start at radius 190; apron and two rock ridges are inside 187.
    if max(math.hypot(panorama.data.vertices[i].co.x,panorama.data.vertices[i].co.y) for i in face.vertices)<187:
        face.material_index=stone_index;ground_faces+=1
        for loop in face.loop_indices:
            co=panorama.data.vertices[panorama.data.loops[loop].vertex_index].co
            panorama.data.uv_layers.active.data[loop].uv=(co.x/24,co.y/24)
            for color in panorama.data.color_attributes:
                if color.domain=='CORNER':color.data[loop].color=(1,1,1,1)

# Keep the authored scenery surfaces; rejected new rocks read as isolated props.
bpy.ops.object.select_all(action='DESELECT')
panorama.select_set(True);bpy.context.view_layer.objects.active=panorama
panorama['fidelity_revision']='run8-continuous-basalt';panorama['render_only']=True
triangles=sum(len(f.vertices)-2 for f in panorama.data.polygons);assert triangles==3072
blend=OUT/'ember-shore-panorama.blend';glb=OUT/'ember-shore-panorama.glb'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contract=json.loads((SOURCE/'panorama-input-contract.json').read_text())
contract.update(meshCount=2,primitiveCount=2,materialCount=2,vertices=len({tuple(v.co) for v in panorama.data.vertices}),triangles=triangles)
contract['texture'].update(count=2,secondAtlas='ember-shore-terrain-atlas.png')
contract['runtimeDetailTexture']={'asset':'sources/ember-shore-fidelity-1/engraved-basalt.png','width':1254,'height':1254,'scope':'render-side continuous pigment; no height or heat authority'}
contract['style']='Existing engraved sky; separate continuous basalt apron/ridges with continuous native basalt pigment'
contract['namedCorrections'].update(ground='World-space basalt shares the terrain treatment; sky retains its original atlas and material',shelves='Existing ridge geometry preserved; larger fractured shelf silhouettes remain held for art')
contract['sourceArt']+=['assets/pilots/map-rebuild-spike/sources/ember-shore-fidelity-1/engraved-basalt.png','assets/raw/plate-contract-e10-ember-shore.png']
contract['files']['blend']={'bytes':blend.stat().st_size,'sha256':sha(blend)}
contract['files']['glb']={'bytes':glb.stat().st_size,'sha256':sha(glb)}
(OUT/'ember-shore-panorama-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
print('EMBER_SCENERY',json.dumps({'groundFaces':ground_faces,'outcrops':0,'triangles':triangles,'vertices':contract['vertices']}))

