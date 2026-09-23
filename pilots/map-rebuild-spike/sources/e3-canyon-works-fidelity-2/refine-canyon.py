"""Canyon render fidelity from frozen source; no gameplay or raster-image writes.
Run Blender from the game checkout. Existing atlas pixels are reused exactly.
"""
from pathlib import Path
import bpy,bmesh,hashlib,json,math,random,struct
from mathutils import Vector
P=Path.cwd()/'assets/pilots/map-rebuild-spike';S=Path(__file__).resolve().parent
PACK=P/'landmarks/canyon-works'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contract=json.loads((S/'landmark-input-contract.json').read_text())
assert sha(S/'landmarks-input.blend')==contract['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
body=bpy.data.objects['sub-hall-dynamo-house'];material=body.data.materials[0];parts=[]
# Keep the exact original object owner and custom properties, replacing its mesh.
original_bounds=contract['assets'][body.name]['bounds']
def finish(o,role):
 o.data.materials.clear();o.data.materials.append(material)
 uv=o.data.uv_layers.active or o.data.uv_layers.new();uv.name='LandmarkAtlasUV'
 row,col=divmod(role,4)
 for v in uv.data:v.uv=((col+.08+v.uv.x*.84)/4,(row+.08+v.uv.y*.84)/4)
 parts.append(o);return o
def box(name,p,size,role=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;return finish(o,role)
def cylinder(name,a,b,r,role=1,n=12):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=(b-a).length,location=(a+b)/2)
 o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return finish(o,role)
def beam(name,a,b,w,role=0,depth=None):
 a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,depth or w,(b-a).length),role);o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return o
def ring(name,p,r,t,role=8,n=16):
 bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=t,major_segments=n,minor_segments=4,location=p,rotation=(math.pi/2,0,0));o=bpy.context.object;o.name=name;return finish(o,role)
# Low masonry plinth carries the original exact 7.8 x 5 m footprint and z=0.
box('Foundation',(0,0,.12),(7.8,5,.24),2)
for x in (-3.6,-2.4,-1.2,0,1.2,2.4,3.6):box('Front dressed stone',(x,-2.32,.29),(.59 if abs(x)>3 else 1.16,.34,.20),2)
for x in (-3.66,3.66):box('Side plinth',(x,.06,.28),(.34,4.39,.22),2)
for i in range(11):box('Boarded machine deck',(-2.56+i*.512,.28,.41),(.49,3.95,.14),0)
# Timber machine hall: roof and corner framing make depth visible at run scale.
box('Hall',(0,.91,1.99),(4.92,2.43,3.04),0)
for x in (-2.48,2.48):
 for y in (-.34,2.15):box('Corner post',(x,y,2.03),(.22,.22,3.25),0)
for side in (-1,1):
 y0=.89;y1=.89+side*1.47;z0=4.29;z1=3.47
 o=box('Pitched iron roof',(0,(y0+y1)/2,(z0+z1)/2),(5.35,math.hypot(y1-y0,z1-z0),.13),1);o.rotation_euler.x=math.atan((z1-z0)/(y1-y0))
 # Small existing iron swatch plus actual raised seams reads as sheet metal,
 # without baking or editing any new texture.
 for loop in o.data.uv_layers.active.data:loop.uv=(.375+(loop.uv.x-.375)*.08,.125+(loop.uv.y-.125)*.08)
 for x in (-2.18,-1.46,-.73,0,.73,1.46,2.18):beam('Standing roof seam',(x,y0,z0+.075),(x,y1,z1+.075),.045,1)
 beam('Copper eave',(-2.70,y1,z1),(2.70,y1,z1),.12,8)
 for x in (-2.65,2.65):beam('Gable fascia',(x,y0,z0),(x,y1,z1),.15,0)
beam('Copper ridge',(-2.67,.89,4.36),(2.67,.89,4.36),.13,8)
# Recesses and louvers create a readable facade rather than the former teal square.
for x in (-1.80,1.80):
 box('Louver recess',(x,-.337,2.67),(.72,.075,.98),9)
 for i in range(4):box('Louver slat',(x,-.40,2.28+i*.24),(.75,.15,.10),1)
 for xx in (x-.43,x+.43):box('Window stile',(xx,-.40,2.67),(.11,.13,1.10),8)
box('Upper service hatch',(0,-.38,3.16),(.62,.10,.42),1)
cylinder('Enamel service dial surround',(0,-.465,3.16),(0,-.425,3.16),.16,8,12)
cylinder('Passive teal enamel dial',(0,-.485,3.16),(0,-.465,3.16),.115,4,12)
# One deep, supported dynamo replaces the two thin wheel motifs and shared shaft.
cylinder('Generator barrel',(0,-1.79,1.75),(0,-.23,1.75),1.19,1,20)
for y in (-1.81,-.27):ring('Copper casing band',(0,y,1.75),1.17,.12,8,20)
# Front rotor is a hub, six spokes and a rim, with black recess visible between.
cylinder('Rotor face recess',(0,-1.86,1.75),(0,-1.80,1.75),.98,9,20)
ring('Rotor rim',(0,-1.96,1.75),.84,.09,8,16)
for i in range(6):
 a=i*math.tau/6;beam('Rotor spoke',(.16*math.sin(a),-1.99,1.75+.16*math.cos(a)),(.80*math.sin(a),-1.99,1.75+.80*math.cos(a)),.12,8)
cylinder('Rotor axle',(0,-2.25,1.75),(0,-1.69,1.75),.21,1)
cylinder('Hub cap',(0,-2.30,1.75),(0,-2.24,1.75),.30,8)
for i in range(10):
 a=i*math.tau/10;x=1.20*math.sin(a);z=1.75+1.20*math.cos(a)
 beam('Longitudinal casing rib',(x,-1.65,z),(x,-.40,z),.075,8)
for x in (-.94,.94):
 box('Generator stone saddle',(x,-1.08,.64),(.53,1.88,.39),2)
 beam('Bearing support',(x,-2.08,.48),(x,-2.08,1.73),.23,1)
beam('Front bearing bridge',(-1.10,-2.08,1.56),(1.10,-2.08,1.56),.17,1)
# Two individually supported ceramic/copper terminals, with no active grid links.
for x in (-2.82,2.82):
 cylinder('Terminal pedestal',(x,.80,.38),(x,.80,.79),.43,2,10)
 cylinder('Terminal column',(x,.80,.77),(x,.80,5.78),.16,1,10)
 for z in (1.05,4.60,5.08,5.52):cylinder('Ceramic collar',(x,.80,z-.08),(x,.80,z+.08),.28,2,10)
 cylinder('Copper terminal',(x,.80,5.74),(x,.80,6.55),.105,8,10)
 for z in (5.88,6.12,6.35):cylinder('Terminal disk',(x,.80,z-.055),(x,.80,z+.055),.27,2,10)
 beam('Column brace',(x,.80,3.10),(x*.72,1.92,.52),.12,1)
beam('Offline copper bus',(-2.82,.80,5.78),(2.82,.80,5.78),.09,8)
# Join with the original owner and preserve all its custom metadata.
old=body.data;body.data=bpy.data.meshes.new('CanyonDynamoFidelity')
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();bpy.data.meshes.remove(old)
body['fidelity_recipe']='sources/e3-canyon-works-fidelity-2/refine-canyon.py'
bpy.context.view_layer.update()
bounds={'min':[round(min(v.co[i] for v in body.data.vertices),4) for i in range(3)],'max':[round(max(v.co[i] for v in body.data.vertices),4) for i in range(3)]}
assert bounds==original_bounds,(bounds,original_bounds)
triangles=sum(len(f.vertices)-2 for f in body.data.polygons);assert triangles<=3000,triangles
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'canyon-works-landmarks.blend'))
bpy.ops.export_scene.gltf(filepath=str(PACK/'sub-hall-dynamo-house.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
contract['blend']['sha256']=sha(PACK/'canyon-works-landmarks.blend')
contract['assets'][body.name].update(triangles=triangles,sha256=sha(PACK/'sub-hall-dynamo-house.glb'),fidelityCorrection={'recipe':body['fidelity_recipe'],'trianglesBefore':1768,'trianglesAfter':triangles,'preserved':'bounds, mount, collision footprint, inspection station, four sibling bodies and shared atlas bytes','features':['deep ribbed dynamo barrel','six-spoke rotor, hub and bearing supports','pitched metal roof and timber hall','recessed louver windows','ceramic terminals and offline copper bus','masonry plinth and recessed footing']})
(PACK/'canyon-works-landmark-pack-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
print('CANYON_DYNAMO',triangles,bounds)
