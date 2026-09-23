"""Rebuild the landing-frame visual inside its unchanged envelope; no gameplay edits.

Blender --background --python this-file, from the game root. The frozen input
preserves peer geometry. Native imagegen swatches replace the stretched pictures.
"""
from pathlib import Path
import bpy, math, json, hashlib
from mathutils import Vector
P=Path.cwd()/'assets/pilots/map-rebuild-spike'; S=Path(__file__).resolve().parent; PACK=P/'landmarks/far-side'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text())
assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
body=bpy.data.objects['far-side-landing-frame'];mat=body.data.materials[0]
atlas=bpy.data.images.load(str(P/'landmarks/far-side/far-side-landmarks-atlas.png'),check_existing=False);atlas.pack()
for m in bpy.data.materials:
 if m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE':n.image=atlas
parts=[]
def finish(o,role):
 o.data.materials.append(mat);uv=o.data.uv_layers.active or o.data.uv_layers.new();uv.name='LandmarkAtlasUV'
 row,col=divmod(role,4)
 for v in uv.data:v.uv=((col+.12+v.uv.x*.76)/4,(row+.12+v.uv.y*.76)/4)
 parts.append(o);return o
def box(name,p,size,role=1):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;return finish(o,role)
def beam(name,a,b,w,role=1):
 a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,w,(b-a).length),role);o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return o
def cyl(name,a,b,r,role=8,n=12,r2=None):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r,radius2=r if r2 is None else r2,depth=(b-a).length,location=(a+b)/2)
 o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return finish(o,role)
def ring(name,y,z,r,t,role=8,n=24):
 bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=4,major_radius=r,minor_radius=t,location=(0,y,z),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name=name;return finish(o,role)
def shell():
 # Five longitudinal bays form a pressure vessel, with faceted domed end caps.
 profile=[(-1.95,.67),(-1.80,1.48),(-1.23,2.03),(1.14,2.03),(1.63,1.64),(1.84,.76)]
 verts=[(r*math.cos(i*math.tau/24),y,3.23+r*math.sin(i*math.tau/24)) for y,r in profile for i in range(24)]
 faces=[(j*24+i,(j+1)*24+i,(j+1)*24+(i+1)%24,j*24+(i+1)%24) for j in range(5) for i in range(24)]
 mesh=bpy.data.meshes.new('Riveted pressure shell');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Riveted pressure shell',mesh);bpy.context.collection.objects.link(o)
 uv=mesh.uv_layers.new()
 for f in mesh.polygons:
  corners=[mesh.vertices[i].co for i in f.vertices]
  length=(corners[1]-corners[0]).length/3;arc=(corners[3]-corners[0]).length/3
  for k,li in enumerate(f.loop_indices):uv.data[li].uv=((0,length,length,0)[k],(0,0,arc,arc)[k])
 finish(o,8)
shell()
# A tiered plinth and four splayed shoes replace the featureless black rectangle.
box('Recessed iron bed',(0,0,.21),(5.62,4.26,.42),9)
for x in (-2.77,2.77):
 for y in (-1.87,1.87):
  box('Stone socket',(x,y,.15),(.8262,.96,.30),2)
  box('Brass foot plate',(x,y,.36),(.70,.74,.12),8)
  beam('Splayed cradle',(x,y,.43),(x*.83,y*.82,2.85),.25,1)
  cyl('Cradle pivot',(x*.83,-abs(y)*.82-.12,2.85),(x*.83,-abs(y)*.82-.32,2.85),.24,8,10)
for y in (-1.84,1.84):
 beam('Cradle sill',(-2.75,y,.62),(2.75,y,.62),.23,1)
 for side in (-1,1):beam('Cradle knee',(side*2.70,y,.69),(side*1.70,y,1.78),.19,8)
for y,r in [(-1.76,1.54),(-1.23,2.07),(.06,2.07),(1.13,2.07),(1.62,1.68)]:ring('Pressure seam collar',y,3.23,r,.062,1)
for i in range(8):
 t=(i+.5)*math.tau/8;x=2.046*math.cos(t);z=3.23+2.046*math.sin(t)
 beam('Longitudinal pressure rib',(x,-1.19,z),(x,1.10,z),.055,1)
 for y in (-1.23,1.13):
  cyl('Collar fastener',(x*.996,y,z),(x*1.035,y,3.23+(z-3.23)*1.035),.072,8,6)
cyl('Dark hatch recess',(0,-1.98,3.23),(0,-2.05,3.23),.64,9,24)
ring('Hatch flange',-2.10,3.23,.62,.10,8,n=20)
cyl('Pressure glass',(0,-2.12,3.23),(0,-2.16,3.23),.43,5,20)
ring('Pressure glass seal',-2.17,3.23,.44,.035,1,n=20)
cyl('Front pressure spindle',(0,-2.17,3.23),(0,-2.34,3.23),.20,1,8)
cyl('Spindle brass cap',(0,-2.30,3.23),(0,-2.35,3.23),.26,8,8)
for i in range(8):
 t=i*math.tau/8;x=.61*math.cos(t);z=3.23+.61*math.sin(t)
 cyl('Hatch bolt',(x,-2.15,z),(x,-2.22,z),.055,10,6)
# Closed service tubes, a wheel, and a narrow rear telemetry mast stay in bounds.
for x in (-2.60,2.60):
 cyl('Service riser',(x,.35,.56),(x,.35,3.80),.11,8,10)
 cyl('Service elbow',(x,.35,3.80),(x*.78,.35,3.80),.11,8,10)
 box('Riser saddle',(x,.35,1.38),(.31,.30,.17),1)
beam('Rear instrument mast',(2.42,1.70,.65),(2.42,1.70,6.58),.14,1)
beam('Visible mast knee',(2.42,1.70,5.58),(1.58,1.13,4.54),.12,8)
cyl('Telemetry ceramic',(2.42,1.70,6.48),(2.42,1.70,6.78),.21,6,12)
cyl('Telemetry cap',(2.42,1.70,6.78),(2.42,1.70,6.99),.14,8,8,r2=0)
box('Pressure readout',(-2.38,-.36,4.20),(.64,.36,.84),1)
box('Readout inset',(-2.38,-.55,4.20),(.45,.045,.52),5)
old=body.data;bounds=[(min(v.co[i] for v in old.vertices),max(v.co[i] for v in old.vertices)) for i in range(3)]
body.data=bpy.data.meshes.new('PressureVesselFidelity');body.data.materials.append(mat);bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();bpy.data.meshes.remove(old)
for i,(lo,hi) in enumerate(bounds):
 a=min(v.co[i] for v in body.data.vertices);b=max(v.co[i] for v in body.data.vertices)
 for v in body.data.vertices:v.co[i]=lo+(v.co[i]-a)*(hi-lo)/(b-a)
for f in body.data.polygons:f.material_index=0
while len(body.data.materials)>1:body.data.materials.pop(index=len(body.data.materials)-1)
tri=sum(len(f.vertices)-2 for f in body.data.polygons);assert tri<=3000,tri
body['fidelity_recipe']='sources/e8-far-side-fidelity-2/refine-pressure-vessel.py'
c['assets'][body.name]['triangles']=tri
c['assets'][body.name]['fidelityCorrection']={'recipe':body['fidelity_recipe'],'trianglesBefore':600,'trianglesAfter':tri,'preserved':'exact bounds, mount, station, nonblocking identity','features':['domed pressure shell','five seam collars and longitudinal ribs','recessed pressure hatch and fasteners','splayed cradle and socket shoes','service tubes and telemetry mast']}
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'far-side-landmarks.blend'))
for id in c['assets']:
 bpy.ops.object.select_all(action='DESELECT');o=bpy.data.objects[id];o.select_set(True);bpy.context.view_layer.objects.active=o
 target=PACK/(id+'.glb');bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
 c['assets'][id]['sha256']=sha(target)
c['blend']['sha256']=sha(PACK/'far-side-landmarks.blend');c['atlas']['sha256']=sha(P/'landmarks/far-side/far-side-landmarks-atlas.png')
c['atlas']['provenance']='Native image_gen; sources/e8-far-side-fidelity-2/native-metal-swatches.png, resized to 1024 square with sips. No painted object imagery.'
(PACK/'far-side-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n');print('PRESSURE VESSEL',tri)
