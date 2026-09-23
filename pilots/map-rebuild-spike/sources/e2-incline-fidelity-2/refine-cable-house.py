"""Complete the existing cable-house mechanisms and structural deck in one atlas.
Run Blender from the game checkout; -- <output directory> makes an isolated draft.
"""
from pathlib import Path
import bpy, bmesh, hashlib, json, math, sys
from mathutils import Vector

P = Path.cwd() / 'assets/pilots/map-rebuild-spike'
S = Path(__file__).resolve().parent
PACK = Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else P / 'landmarks/incline'
PACK.mkdir(parents=True, exist_ok=True)
assert hashlib.sha256((S / 'landmarks-input.blend').read_bytes()).hexdigest() == json.loads((S / 'landmark-input-contract.json').read_text())['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S / 'landmarks-input.blend'))
body = bpy.data.objects['upper-ore-cable-house']; mesh = body.data
material = mesh.materials[0]; uv_name = mesh.uv_layers.active.name
original_bounds = [tuple(v) for v in body.bound_box]
assert sum(len(f.vertices)-2 for f in mesh.polygons) == 2028

# The prior cable/wheel additions have the right coordinates in UVMap but zeros
# in the material's active LandmarkAtlasUV. Consolidate into the material owner.
fixed_loops = 0
for face in mesh.polygons:
    if face.index in range(1552,1568): continue # old vertical returns are replaced below
    if all(mesh.uv_layers[uv_name].data[i].uv.length == 0 for i in face.loop_indices):
        for i in face.loop_indices:
            mesh.uv_layers[uv_name].data[i].uv = mesh.uv_layers['UVMap'].data[i].uv
            fixed_loops += 1

# Frozen input: faces 0:788 are the reused low winch buried inside the house;
# 1480:1486 are its thin roof; 1552:1568 are the old cable returns. Remove whole
# authored components, not clipped fragments, before fitting the clear mechanism.
removed_faces=set(range(788)) | set(range(1480,1486)) | set(range(1552,1568))
assert sum(len(mesh.polygons[i].vertices)-2 for i in removed_faces)==840
bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[bm.faces[i] for i in removed_faces],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bm.to_mesh(mesh);bm.free()
parts=[]
def finish(o, role):
    o.data.materials.append(material)
    uv=o.data.uv_layers.active or o.data.uv_layers.new()
    uv.name=uv_name
    row,col=divmod(role,4)
    for loop in uv.data: loop.uv=((col+.08+loop.uv.x*.84)/4,(row+.08+loop.uv.y*.84)/4)
    parts.append(o)
def box(name,center,size,role=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name;o.scale=size;finish(o,role);return o
def beam(name,a,b,width,depth,role=0):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(width,depth,(b-a).length),role)
    o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return o
def cylinder(name,a,b,radius,role=1,segments=12):
    a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=radius,depth=(b-a).length,location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');finish(o,role);return o

# Closed sloping roof panels, with small overhang and visible supporting fascia.
for side in (-1,1):
    y0=.89; y1=.89+side*(max(v[1] for v in original_bounds)-.09-.89); z0=3.76;z1=3.38
    o=box('Timber roof slope',(0,(y0+y1)/2,(z0+z1)/2),(6.2,math.hypot(y1-y0,z1-z0),.16),0)
    # Local cube X spans the building, Y follows the slope, Z is panel thickness.
    o.rotation_euler.x=math.atan((z1-z0)/(y1-y0))
    for x in (-3.08,3.08):beam('Roof end fascia',(x,y0,z0-.08),(x,y1,z1-.08),.16,.18,0)
    box('Roof eave',(0,y1,z1-.1),(6.2,.18,.22),0)
box('Roof ridge',(0,.89,3.81),(6.24,.20,.18),0)

# A visible exhaust neck meets the existing world-space cable-house vent.
# Inverse yaw converts its (-.6,-1.4) world X/Z offset into Blender X/Y.
sx=math.cos(.1)*(-.6)+math.sin(.1)*(-1.4)
sy=-(math.cos(.1)*(-1.4)-math.sin(.1)*(-.6))
cylinder('Roof exhaust neck',(sx,sy,3.50),(sx,sy,5.02),.21,1,10)
cylinder('Exhaust collar',(sx,sy,4.94),(sx,sy,5.12),.28,8,10)

# The existing ring becomes a supported sheave rather than an empty hoop.
for i in range(8):
    a=i*math.tau/8
    beam('Sheave spoke',(math.sin(a)*.14,-1.55,4.65+math.cos(a)*.14),(math.sin(a)*.67,-1.55,4.65+math.cos(a)*.67),.085,.11,8)
cylinder('Sheave hub',(0,-1.77,4.65),(0,-1.29,4.65),.18,8)
cylinder('Sheave axle',(0,-1.91,4.65),(0,-.97,4.65),.085,1)
for y in (-1.82,-1.04):box('Axle bearing',(0,y,4.63),(.42,.16,.39),1)
beam('Bearing crosshead',(-1.48,-1.1,4.52),(1.48,-1.1,4.52),.17,.21,0)

# Explicit drum and cheek discs make the lower cable return legible.
cylinder('Winch drum',(-.79,-2.26,1.22),(.79,-2.26,1.22),.35,1,16)
for x in (-.84,.84):
    cylinder('Drum cheek',(x-.045,-2.26,1.22),(x+.045,-2.26,1.22),.47,8,12)
    box('Drum bearing',(x,-2.26,.67),(.25,.54,.64),0)

for x in (-.68,.68):beam('Cable return to drum',(x,-1.55,4.65),(x,-2.26,1.57),.045,.045,1)
for x in (-.48,-.16,.16,.48):cylinder('Drum winding',(x-.018,-2.26,1.22),(x+.018,-2.26,1.22),.364,8,8)

# Deck boards and rim sit over the retained slab, inside the original extent.
for i in range(8):box('Deck board',(0,-2.66+i*.23,.295),(8.96,.215,.11),0)
box('Front deck fascia',(0,-2.65,.265),(8.98,.27,.48),0)
for x in (-4.33,4.33):box('Side deck fascia',(x,-.12,.245),(.28,5.25,.44),0)

# Small readable facade apertures and trim use existing iron/wood atlas cells.
box('Door recess',(1.62,-.66,1.48),(.91,.065,2.14),1)
for x in (1.1,2.14):box('Door jamb',(x,-.72,1.48),(.13,.13,2.3),0)
box('Door lintel',(1.62,-.72,2.64),(1.17,.13,.16),0)
box('Window recess',(-1.68,-.66,2.18),(.82,.065,.65),1)
for x in (-2.14,-1.22):box('Window jamb',(x,-.72,2.18),(.12,.13,.85),0)
for z in (1.77,2.59):box('Window rail',(-1.68,-.72,z),(1.04,.13,.12),0)

bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
triangles=sum(len(f.vertices)-2 for f in body.data.polygons)
assert triangles<=3000,triangles
assert all(min(v[i] for v in original_bounds)-.001<=v.co[i]<=max(v[i] for v in original_bounds)+.001 for v in body.data.vertices for i in range(3)), [tuple(v) for v in body.bound_box]
body['fidelity_recipe']='sources/e2-incline-fidelity-2/refine-cable-house.py'
bpy.context.preferences.filepaths.save_version=0
blend=PACK/'incline-landmarks.blend';glb=PACK/'upper-ore-cable-house.glb'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text());c['blend']['sha256']=sha(blend)
c['assets']['upper-ore-cable-house'].update(triangles=triangles,sha256=sha(glb))
c['assets']['upper-ore-cable-house']['bounds']={'min':[round(min(v.co[i] for v in body.data.vertices),4) for i in range(3)],'max':[round(max(v.co[i] for v in body.data.vertices),4) for i in range(3)]}
c['assets']['upper-ore-cable-house']['fidelityCorrection']={'recipe':'sources/e2-incline-fidelity-2/refine-cable-house.py','trianglesBefore':2028,'trianglesAfter':triangles,'uvLoopsRestoredToMaterialLayer':fixed_loops,'preserved':'mount, collision, within original bounds, stations, atlas pixels, source siblings','features':['eight spokes and hub with bearings','lower drum and cheeks','thicker boarded deck and fascia','pitched timber roof','framed facade apertures','exhaust neck at the existing steam vent','replaced buried reused winch and crossed struts with direct cable returns and wound drum']}
(PACK/'incline-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
print('CABLE_HOUSE_FIDELITY',json.dumps(c['assets']['upper-ore-cable-house']['fidelityCorrection']))
