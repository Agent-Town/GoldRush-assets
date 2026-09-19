"""Verify the current E5 export, saved scene, damage groups and flag/lid clearances."""
from pathlib import Path
import importlib.util,sys,json,hashlib,math
import bpy
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
MODEL=HERE
OUT=HERE/'renders-fidelity-e5'
OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('queen_verifier',ROOT/'assets/pilots/dredge-queen-3d/verify_dredge_queen.py')
parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
path=MODEL/'dredge-queen-detail-opus5.glb'
asset_sha=hashlib.sha256(path.read_bytes()).hexdigest()
(OUT/'contract.json').write_text(json.dumps({'passed':False,'assetSha256':asset_sha,'status':'Verification started; a failed assertion leaves this export unverified.'},indent=2)+'\n')
checked=parser.contract(path)
expected=['claw','paddle_port','paddle_starboard','hold']
morphs=['Damage_SlackClaw','Damage_BrokenPortPaddle','Damage_BrokenStarboardPaddle','Damage_CrackedLootHold']
assert checked['nodes']==expected and checked['nodeCount']==4
assert checked['meshes']==checked['primitives']==4
assert checked['primitiveMaterials']==[0,0,0,0]
assert checked['materials']==checked['images']==checked['embeddedImages']==1
assert checked['imageDimensions']==[[1024,1024]]
assert checked['triangles']<=45000
assert checked['cameras']==checked['lights']==checked['animations']==0
assert checked['morphTargets']=={node+'Mesh':[morph] for node,morph in zip(expected,morphs)}
assert all(count==1 for count in checked['targetCounts'].values())
identity={'translation':[0.,0.,0.],'rotation':[0.,0.,0.,1.],'scale':[1.,1.,1.],'matrix':None}
assert all(transform==identity for transform in checked['nodeTransforms'].values())
assert abs(checked['bounds']['size'][0]-8)<.001
assert 4.3<checked['bounds']['size'][2]<5.3,'Candidate beam outside the inspected envelope; runtime target fit remains required'
assert abs(checked['bounds']['min'][1])<.001
bpy.ops.wm.open_mainfile(filepath=str(MODEL/'dredge-queen-detail-opus5.blend'))
objects=[obj for obj in bpy.data.objects if obj.type=='MESH']
assert sorted(obj.name for obj in objects)==sorted(expected)
assert not any(obj.type in ('CAMERA','LIGHT') for obj in bpy.data.objects)
assert not bpy.data.actions
for obj in objects:
 assert len(obj.data.shape_keys.key_blocks)==2
 assert all(math.isfinite(value) for key in obj.data.shape_keys.key_blocks for point in key.data for value in point.co)
 assert all(key.value==0 for key in obj.data.shape_keys.key_blocks)
 bpy.context.view_layer.objects.active=obj
 obj.select_set(True)
hold=bpy.data.objects['hold']
basis,damaged=hold.data.shape_keys.key_blocks
flag_vertices=[]
for name in ('DamageMainFlag','DamageAftFlag'):
 group=hold.vertex_groups[name]
 indices={v.index for v in hold.data.vertices if any(g.group==group.index for g in v.groups)}
 assert indices,f'Missing authored sail vertices: {name}'
 fold=.30 if name=='DamageMainFlag' else .40
 offsets=[damaged.data[i].co.x-fold*basis.data[i].co.x for i in indices]
 assert max(offsets)-min(offsets)<1e-5,f'Sail folds around inconsistent pivots: {name}'
 flag_vertices.append(indices)
assert not flag_vertices[0]&flag_vertices[1],'Main and aft sail groups overlap'
wheel_groups={}
for name,label in (('paddle_port','Port'),('paddle_starboard','Starboard')):
 obj=bpy.data.objects[name]
 basis_key,damage_key=obj.data.shape_keys.key_blocks
 stations=[]
 for station in ('Fore','Aft'):
  group=obj.vertex_groups[f'Damage{label}{station}Paddle']
  indices={v.index for v in obj.data.vertices if any(g.group==group.index for g in v.groups)}
  broken_group=obj.vertex_groups[f'Damage{label}{station}Break']
  broken_indices={v.index for v in obj.data.vertices if any(g.group==broken_group.index for g in v.groups)}
  assert indices and broken_indices and broken_indices<=indices
  assert all((damage_key.data[i].co-basis_key.data[i].co).length>.1 for i in broken_indices)
  stations.append(indices)
 assert not stations[0]&stations[1]
 fore_max=max(basis_key.data[i].co.x for i in stations[0])
 aft_min=min(basis_key.data[i].co.x for i in stations[1])
 assert aft_min-fore_max>.25,'Fore/aft wheel silhouettes must remain separated'
 wheel_groups[name]={'gap':aft_min-fore_max,'verticesPerStation':[len(v) for v in stations]}
claw=bpy.data.objects['claw']
assert min(p.co.z for p in claw.data.shape_keys.key_blocks[1].data)>-.01,'Damaged claw blades fall below the model datum'
basis_claw,damaged_claw=claw.data.shape_keys.key_blocks
for name in ('DamageGrab','DamageGrabChain'):
 group=claw.vertex_groups[name]
 indices={v.index for v in claw.data.vertices if any(g.group==group.index for g in v.groups)}
 assert indices,f'Missing slack grab group: {name}'
 drops=[damaged_claw.data[i].co.z-basis_claw.data[i].co.z for i in indices]
 if name=='DamageGrab':
  assert sum(drops)/len(drops)<-.4,'Grab does not visibly lower in its damaged shape'
 else:
  assert max(drops)-min(drops)>.3,'Hoist chain must lengthen instead of translating rigidly'
group=claw.vertex_groups['DamageTalons']
indices={v.index for v in claw.data.vertices if any(g.group==group.index for g in v.groups)}
assert indices,'Missing damaged talon group'
assert max(abs(damaged_claw.data[i].co.y) for i in indices)>max(abs(basis_claw.data[i].co.y) for i in indices)+.15,'Failed grab must visibly splay open'

for name in ('DamageHoldPortLid','DamageHoldStarboardLid'):
 group=hold.vertex_groups[name]
 indices={v.index for v in hold.data.vertices if any(g.group==group.index for g in v.groups)}
 assert indices
 assert all(abs(damaged.data[i].co.y-basis.data[i].co.y)<1e-5 for i in indices),'Rear hinge moves vertices sideways'
 assert max(damaged.data[i].co.z for i in indices)>max(basis.data[i].co.z for i in indices)+.5
hold.data.calc_loop_triangles()
clearance_groups=('DamageMainFlag','DamageAftFlag','DamageHoldPortLid','DamageHoldStarboardLid')
clearance_indices={name:{v.index for v in hold.data.vertices if any(g.group==hold.vertex_groups[name].index for g in v.groups)} for name in clearance_groups}
clearance_faces={name:[tuple(t.vertices) for t in hold.data.loop_triangles if set(t.vertices)<=clearance_indices[name]] for name in clearance_groups}
clearance=[]
for key in hold.data.shape_keys.key_blocks:
 vertices=[tuple(p.co) for p in key.data]
 trees={name:BVHTree.FromPolygons(vertices,clearance_faces[name],all_triangles=True) for name in clearance_groups}
 for flag in clearance_groups[:2]:
  for lid in clearance_groups[2:]:
   intersections=len(trees[flag].overlap(trees[lid]))
   clearance.append({'shape':key.name,'flag':flag,'lid':lid,'triangleIntersections':intersections})
   assert intersections==0,f'{key.name}: {flag} intersects {lid}'
reexport=OUT/'reexport.glb'
bpy.ops.export_scene.gltf(filepath=str(reexport.with_suffix('')),export_format='GLB',use_selection=True,export_apply=True,
 export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_morph=True)
assert path.read_bytes()==reexport.read_bytes(),'Saved blend differs on re-export'
reexport.unlink()
(OUT/'contract.json').write_text(json.dumps({'passed':True,'assetSha256':asset_sha,'checked':checked,'byteIdenticalReexport':True,'wheelGroups':wheel_groups,'flagLidClearance':clearance,
 'scope':'Asset structure and normalized shape keys only; actual visual, gameplay and browser checks remain required.'},indent=2)+'\n')
print('Candidate asset contract and saved blend re-export passed.')
