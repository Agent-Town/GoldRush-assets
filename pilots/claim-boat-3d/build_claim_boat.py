"""Claim Boat body from its approved plate; Blender 5.1.2, existing E5 atlas/helpers."""
from pathlib import Path
import bpy, hashlib, importlib.util, json, math, sys
from mathutils import Vector
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
helper = REPO / 'assets/pilots/plaza-props-3d/build_era_props_e5.py'
spec = importlib.util.spec_from_file_location('claim_boat_e5', helper)
e5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(e5)
c = e5.common
out = Path(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else ROOT
out.mkdir(parents=True, exist_ok=True)
c.reset(); c.ATLAS = REPO / 'assets/raw/claim-boat-material-atlas.png'; mat = e5.material(); mat.name = 'ClaimBoatLedgerHarbor'
# Standard exported texture downsize; original atlas remains untouched and is pinned below.
image = next(n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE')
image.scale(512, 512); image.pack()
parts = []
def box(name, size, pos, ink=3, bevel=0):
    obj = c.box(name, size, pos, mat, ink, bevel); parts.append(obj); return obj
def cylinder(name, radius, height, pos, ink=10, vertices=12, rotation=(0,0,0)):
    obj = c.cylinder(name, radius, height, pos, mat, ink, vertices, rotation); parts.append(obj); return obj
def beam(name, a, b, radius=.05, ink=10):
    obj = e5.beam(name,a,b,radius,mat,ink,8); parts.append(obj); return obj
# Blender Y points toward the bow (game -Z). Waterline 0, deck +0.8 m.
outline=[(-4.2,-8.0),(4.2,-8.0),(4.8,-7.2),(4.8,6.8),(4.0,8.0),(-4.0,8.0),(-4.8,6.8),(-4.8,-7.2)]
verts=[(x*.93,y*.96,-.65) for x,y in outline]+[(x,y,.66) for x,y in outline]
faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
mesh=bpy.data.meshes.new('BroadWorkingHull');mesh.from_pydata(verts,[],faces);mesh.update()
hull=bpy.data.objects.new('BroadWorkingHull',mesh);bpy.context.collection.objects.link(hull);c.tag(hull,mat,2,.04);parts.append(hull)
box('Deck brass rim',(9.25,15.7,.16),(0,0,.7),10,.04)
box('Deck seam backing',(8.95,15.4,.08),(0,0,.76),1)
# Separate top faces keep the existing wood atlas at plank scale, without hidden box faces.
plank_width, plank_length = 8.9 / 17, 15.4 / 16
for column in range(17):
    x0 = -4.45 + column * plank_width
    for row in range(-1,17):
        y0 = max(-7.7, -7.7 + row * plank_length + (column % 2) * plank_length / 2)
        y1 = min(7.7, -7.7 + (row + 1) * plank_length + (column % 2) * plank_length / 2)
        if y1 - y0 < .02: continue
        mesh = bpy.data.meshes.new('Deck plank face')
        mesh.from_pydata([(x0+.006,y0+.006,.811),(x0+plank_width-.006,y0+.006,.811),
                          (x0+plank_width-.006,y1-.006,.811),(x0+.006,y1-.006,.811)], [], [(0,1,2,3)])
        mesh.update()
        plank = bpy.data.objects.new('Deck plank',mesh);bpy.context.collection.objects.link(plank)
        c.tag(plank,mat,3,0);plank['grain_along_y'] = True;parts.append(plank)
cabin_start = len(parts)
# Aft wheelhouse leaves three authored deck pads at (0,+3), (-3,-1), (+3,-1) clear.
box('Aft wheelhouse foot',(4.7,3.6,.35),(0,-5.4,.96),1,.05)
box('Wheelhouse',(4.1,3.15,2.25),(0,-5.4,2.22),3,.08)
box('Cabin roof rim',(4.65,3.65,.19),(0,-5.4,3.43),10,.05)
box('Cabin roof',(4.48,3.48,.10),(0,-5.4,3.55),1)
for x in [-1.4,0,1.4]:
    box('Forward brass window surround',(.95,.09,1.16),(x,-3.8,2.50),10,.03)
    box('Forward teal glass',(.75,.10,.95),(x,-3.74,2.50),6)
    box('Window center muntin',(.045,.12,.98),(x,-3.68,2.50),1)
for side in [-1,1]:
    for y in [-6.3,-5.35,-4.4]:
        box('Side window surround',(.08,.68,1.12),(side*2.08,y,2.48),10,.02)
        box('Side teal glass',(.09,.52,.92),(side*2.13,y,2.48),6)
    cylinder('Roof vent',.17,.8,(side*1.5,-5.8,4.0),10)
    cylinder('Vent cap',.26,.10,(side*1.5,-5.8,4.45),1)
e5.lantern(parts,'Wheelhouse roof lantern',(0,-5.4,4.18),mat,2)
for z in [1.2,1.45,3.1]:
    box('Cabin brass belt',(4.24,3.28,.075),(0,-5.4,z),10)
for x in [-1.95,1.95]:
    for y in [-6.75,-4.05]:
        cylinder('Cabin carved corner post',.085,2.1,(x,y,2.3),10,8)
for side in [-1,1]:
    for y in [-6.7,-5.4,-4.1]:
        cylinder('Roof rail post',.05,.35,(side*2.1,y,3.77),10,8)
    beam('Roof side rail',(side*2.1,-6.7,3.92),(side*2.1,-4.1,3.92),.035,10)
for y in [-6.7,-4.1]:beam('Roof end rail',(-2.1,y,3.92),(2.1,y,3.92),.035,10)
# Helm wheel and visible spokes on the wheelhouse crown.
parts.append(c.torus('Roof helm wheel',.35,.045,(.8,-4.7,4.22),mat,10,rotation=(math.pi/2,0,0),segments=(16,4)))
for i in range(8):
    a=i*math.pi/4
    beam('Helm spoke',(.8,-4.7,4.22),(.8+math.cos(a)*.39,-4.7,4.22+math.sin(a)*.39),.018,10)

# Raised wheelhouse over its machinery room, with an accessible balcony.
for part in parts[cabin_start:]:part.location.z += 1.3
box('Lower machinery room',(4.6,3.7,1.3),(0,-5.4,1.45),2,.04)
box('Wheelhouse balcony',(6.3,4.1,.14),(0,-5.4,2.13),10,.03)
for side in [-1,1]:
    for i in range(6):
        height=(i+1)*.22
        box('Balcony stair',(.95,.40,height),(side*2.8,-2.9-i*.36,.8+height*.5),10)
    for y in [-7.2,-5.4,-3.6]:cylinder('Balcony stanchion',.045,.65,(side*3.0,y,2.5),10,8)
    beam('Balcony rail',(side*3.0,-7.2,2.82),(side*3.0,-3.6,2.82),.035,10)
    for y in [-6.2,-4.6]:
        cylinder('Lower engine flywheel',.38,.15,(side*2.4,y,1.45),10,12,(0,math.pi/2,0))
        cylinder('Engine teal hub',.16,.17,(side*2.45,y,1.45),6,12,(0,math.pi/2,0))
beam('Balcony aft rail',(-3.0,-7.2,2.82),(3.0,-7.2,2.82),.035,10)
# Crane amidships: offset from the rider origin and all three build pads.
crane_start = len(parts)
cylinder('Crane revolving pedestal',.80,.45,(0,0,1.03),1,16)
cylinder('Crane brass ring',.85,.11,(0,0,1.28),10,16)
box('Crane gearbox',(1.35,1.25,.8),(0,0,1.7),10,.04)
for x in [-.48,.48]:
    beam('Crane mast',(x,0,1.8),(x,-.25,4.5),.11,10)
    beam('Crane boom',(x,-.25,4.5),(x,3.9,5.3),.09,10)
    beam('Crane diagonal',(x,0,2.2),(x,3.9,5.3),.10,10)
    beam('Crane truss',(x,1.2,2.9),(x,1.2,4.78),.07,10)
    beam('Crane truss',(x,2.5,3.85),(x,2.5,5.03),.07,10)
    beam('Crane rigging',(x,-.25,4.5),(x,3.9,5.3),.027,1)
beam('Crane boom end',(-.6,3.9,5.3),(.6,3.9,5.3),.12,10)
for y,z in [(0,4.5),(3.9,5.3),(1.2,4.78),(2.5,5.03)]:
    cylinder('Crane pulley wheel',.44 if y in [0,3.9] else .28,.22,(0,y,z),10,12,(0,math.pi/2,0))
    cylinder('Pulley axle',.065,1.2,(0,y,z),13,8,(0,math.pi/2,0))
    for side in [-1,1]:
        cylinder('Pulley teal hub',.14 if y in [0,3.9] else .10,.05,(side*.14,y,z),6,10,(0,math.pi/2,0))
beam('Crane hanging chain',(0,3.9,5.25),(0,3.9,2.0),.025,1)
cylinder('Claw bucket crown',.25,.20,(0,3.9,2.08),10,10)
for side in [-1,1]:
    section=[(.08,2.02),(.72,1.8),(.68,1.3),(.12,1.1),(.18,1.36),(.49,1.56),(.08,1.88)]
    vertices=[(side*x,y,z) for y in [3.48,4.32] for x,z in section]
    faces=[tuple(reversed(range(7))),tuple(range(7,14))]+[(i,(i+1)%7,(i+1)%7+7,i+7) for i in range(7)]
    if side<0:faces=[tuple(reversed(face)) for face in faces]
    mesh=bpy.data.meshes.new('Clamshell jaw');mesh.from_pydata(vertices,[],faces);mesh.update()
    jaw=bpy.data.objects.new('Clamshell bucket jaw',mesh);bpy.context.collection.objects.link(jaw);c.tag(jaw,mat,10,0);parts.append(jaw)
    beam('Clamshell jaw rib',(side*.70,3.9,1.78),(side*.65,3.9,1.3),.055,1)

for side in [-1,1]:
    cylinder('Crane winch hub',.28,.12,(side*.64,0,1.65),6,12,(0,math.pi/2,0))
crane_parts = set(parts[crane_start:])
for part in crane_parts:
    if part.get('palette_index') == 10: part['palette_index'] = 11
    part.location.x -= 2.0
    part.location.y += 1.0
# Bow pan-dredge: roller, comb teeth and two side linkages; no gun silhouette.
box('Dredge apron',(4.6,1.7,.16),(0,8.4,.4),1,.03)
cylinder('Dredge roller',.62,4.6,(0,8.7,.83),2,16,(0,math.pi/2,0))
for x in [-2.25,-1.5,-.75,0,.75,1.5,2.25]:
    parts.append(c.torus('Dredge brass roller band',.635,.065,(x,8.7,.83),mat,10,rotation=(0,math.pi/2,0),segments=(16,4)))

for x in [-2,-1.5,-1,-.5,0,.5,1,1.5,2]:
    tooth=box('Pan dredge tooth',(.18,2.5,.18),(x,10.2,.05),10)
    tooth.rotation_euler.x=-.4
for x in [-2.3,2.3]:
    beam('Dredge lift arm',(x,7,.9),(x,9.6,.7),.11,10)
for side in [-1,1]:
    cylinder('Dredge side drive wheel',.58,.20,(side*2.55,8.7,.85),11,16,(0,math.pi/2,0))
    cylinder('Dredge drive teal hub',.20,.23,(side*2.57,8.7,.85),6,12,(0,math.pi/2,0))
    for a,b in [((7,1.65),(8.5,2.1)),((8.5,2.1),(10,1.2)),((10,1.2),(11,-.1))]:
        beam('Dredge arched side frame',(side*2.4,*a),(side*2.4,*b),.16,11)
    beam('Dredge linkage brace',(side*2.4,7.0,.85),(side*2.4,7.0,1.65),.16,10)
    box('Bow gearbox',(.8,1.2,.65),(side*2.6,7.25,1.1),10,.025)
cylinder('Dredge lower return roller',.30,4.6,(0,9.3,.24),10,12,(0,math.pi/2,0))
beam('Dredge upper cross shaft',(-2.4,8.5,2.1),(2.4,8.5,2.1),.12,10)
for x in [-1.5,-.5,.5,1.5]:
    beam('Dredge feed linkage',(x,8.5,2.1),(x,9.3,.24),.06,10)
# Brass bulwark posts, restrained rails, rope fenders and running lamps.
for side in [-1,1]:
    for y in [-7,-5,-3,-1,1,3,5,7]:
        cylinder('Rail stanchion',.06,.56,(side*4.55,y,1.1),10,8)
        cylinder('Rail cap',.10,.06,(side*4.55,y,1.41),10,8)
    beam('Side top rail',(side*4.55,-7,1.36),(side*4.55,7,1.36),.045,10)
    for y in [-6,-2,2,6]:
        cylinder('Hull rope fender',.22,1.0,(side*4.66,y,.07),1,10)
    for y in [-4,0,4]:
        cylinder('Hull teal porthole',.22,.06,(side*4.63,y,.25),6,12,(0,math.pi/2,0))
        parts.append(c.torus('Hull brass porthole rim',.25,.05,(side*4.7,y,.25),mat,10,rotation=(0,math.pi/2,0),segments=(12,4)))
    for y in [-7,7]:
        e5.lantern(parts,'Teal running light',(side*4.4,y,1.55),mat,1.3)
beam('Stern rail',(-4.5,-7.3,1.36),(4.5,-7.3,1.36),.045,10)
# Segmented buoyant side floats form the rounded perimeter in the plate.
for side in [-1,1]:
    cylinder('Long side flotation',.58,14.5,(side*4.45,0,-.18),2,12,(math.pi/2,0,0))
    for y in [-7,-5,-3,-1,1,3,5,7]:
        parts.append(c.torus('Flotation brass strap',.585,.045,(side*4.45,y,-.18),mat,10,rotation=(math.pi/2,0,0),segments=(12,4)))
    for y in [-7.25,7.25]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.58,location=(side*4.45,y,-.18))
        obj=bpy.context.object;obj.name='Rounded float end';c.tag(obj,mat,2,0);parts.append(obj)
# The plate's long barge proportion: elongate along the hull, preserving beam and deck height.
# All solids are baked before export; runtime needs no model-specific transform.
bpy.context.view_layer.update()
for part in parts:
    matrix=part.matrix_world.copy()
    for vertex in part.data.vertices:
        world=matrix @ vertex.co;world.y *= 1.9
        if part in crane_parts:
            world.z=.8+(world.z-.8)*1.5
        vertex.co=matrix.inverted() @ world
# Deck pad locations remain the authored game coordinates, not stretched UV/model anchors.
# One material and mesh, as with the established E5 prop exports.
c.apply_palette_uv(parts,False)
# Deterministic box projection: Smart Project rotates tied islands between fresh Blender runs.
# Keep the same 4x4 atlas and helpers, but derive each face's UV from its dominant normal.
for obj in parts:
    vertices=obj.data.vertices; uv=obj.data.uv_layers.active
    low=[min(v.co[a] for v in vertices) for a in range(3)]
    high=[max(v.co[a] for v in vertices) for a in range(3)]
    index=int(obj['palette_index']); column,row=index%4,index//4
    for polygon in obj.data.polygons:
        dominant=max(range(3),key=lambda a:abs(polygon.normal[a]))
        axes=[a for a in range(3) if a!=dominant]
        if obj.get('grain_along_y') and dominant==2: axes.reverse()
        for loop_index in polygon.loop_indices:
            co=vertices[obj.data.loops[loop_index].vertex_index].co
            unit=[(co[a]-low[a])/max(high[a]-low[a],1e-6) for a in axes]
            uv.data[loop_index].uv=((column+.025+unit[0]*.95)/4,(row+.025+unit[1]*.95)/4)

bpy.ops.object.select_all(action='DESELECT')
for p in parts:p.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();model=bpy.context.object
model.name='ClaimBoat';model.data.name='ClaimBoatMesh'
# Bake a fixed triangulation so exporter tessellation cannot change index bytes per run.
triangulate=model.modifiers.new('Factory fixed triangulation','TRIANGULATE')
triangulate.quad_method='FIXED';triangulate.ngon_method='CLIP'
bpy.ops.object.modifier_apply(modifier=triangulate.name)
# Store triangles in canonical vertex/face order; BMesh may rotate equal triangle loops per run.
old=model.data; triangles=[]
for polygon in old.polygons:
    vertices=list(polygon.vertices); loops=list(polygon.loop_indices)
    first=vertices.index(min(vertices));vertices=vertices[first:]+vertices[:first];loops=loops[first:]+loops[:first]
    triangles.append((vertices,[tuple(old.uv_layers.active.data[i].uv) for i in loops]))
triangles.sort(key=lambda row:tuple(row[0]))
mesh=bpy.data.meshes.new('ClaimBoatMeshCanonical')
mesh.from_pydata([tuple(v.co) for v in old.vertices],[],[row[0] for row in triangles]);mesh.update()
uv=mesh.uv_layers.new(name='UVMap')
for polygon,(_,coords) in zip(mesh.polygons,triangles):
    for loop_index,coord in zip(polygon.loop_indices,coords):uv.data[loop_index].uv=coord
mesh.materials.append(mat);model.data=mesh;bpy.data.meshes.remove(old)

for p in model.data.polygons:p.material_index=0
while len(model.data.materials)>1:model.data.materials.pop(index=len(model.data.materials)-1)
bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
triangles=sum(len(p.vertices)-2 for p in model.data.polygons)
assert triangles<=22000, triangles
contract_source=next((REPO/'assets/contracts').glob('epoch-5*/contracts.json'))
contracts=json.loads(contract_source.read_text())['contracts']
pads=next(entry for entry in contracts if entry['id']=='e5-deepwater-claim')['tileParams']['deepwater']['claimBoat']['pads']
for entry in contracts:
    if entry['id']!='e5-flotilla':assert entry['tileParams']['deepwater']['claimBoat']['pads']==pads
clearance=[]
for pad in [{'id':'rider','x':0,'z':0},*pads]:
    for dx,dz in [(x*.25,z*.25) for x in range(-3,4) for z in range(-3,4)]:
        hit,point,normal,index=model.ray_cast(Vector((pad['x']+dx,-pad['z']-dz,100)),Vector((0,0,-1)))
        assert hit and .77<=point.z<=.85,(pad,dx,dz,tuple(point))
        clearance.append({'id':pad['id'],'x':pad['x']+dx,'z':pad['z']+dz,'topY':point.z})
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'claim-boat.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'claim-boat.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT')
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contract={'id':'claim-boat','status':'candidate; visual and runtime acceptance pending','concept':'assets/raw/plate-e5-bld-claimboat.png','sourceTier':'build-new with existing E5 geometry/material helpers','builder':'assets/pilots/claim-boat-3d/build_claim_boat.py','toolchain':'Blender 5.1.2 / glTF exporter 5.1.20','sha256':hashfile(out/'claim-boat.glb'),'triangles':triangles,'meshCount':1,'materialCount':1,'textureSize':[512,512],'deckY':.8,'waterlineY':0,'deckBounds':{'minX':-4.4,'maxX':4.4,'minZ':-14.25,'maxZ':14.25},'clearBuildPads':pads,'deckClearanceSamples':clearance,'sourceHashes':{str(p.relative_to(REPO)):hashfile(p) for p in [Path(__file__).resolve(),contract_source,helper,helper.with_name('build_era_props_e2.py'),REPO/'assets/raw/claim-boat-material-atlas.png',REPO/'assets/raw/plate-e5-bld-claimboat.png']}}
(out/'claim-boat-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
(out/'claim-boat.export.json').write_text(json.dumps({'profile':'static','extras':False,'animations':False,'applyTransforms':True,'selection':['ClaimBoat']},indent=2)+'\n')
print('CLAIM_BOAT',triangles,contract['sha256'])
