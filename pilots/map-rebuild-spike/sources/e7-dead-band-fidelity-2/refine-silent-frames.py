"""Layer the two silent antenna frames inside their original source envelopes.

Run with Blender from the game root. Frozen input, original packed atlas only;
all mounts, gameplay data, sibling meshes and inspection stations are retained.
"""
from pathlib import Path
import bpy, math, json, hashlib
from mathutils import Vector

P=Path.cwd()/'assets/pilots/map-rebuild-spike'; S=Path(__file__).resolve().parent; PACK=P/'landmarks/dead-band'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'landmark-input-contract.json').read_text())
assert sha(S/'landmarks-input.blend')==c['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(S/'landmarks-input.blend'))
material=bpy.data.objects['iron-shadow-warning-frame'].data.materials[0]
parts=[]

def finish(o,role):
    o.data.materials.append(material)
    uv=o.data.uv_layers.active or o.data.uv_layers.new(); uv.name='LandmarkAtlasUV'
    row,col=divmod(role,4)
    for v in uv.data:v.uv=((col+.24+v.uv.x*.30)/4,(row+.31+v.uv.y*.27)/4)
    parts.append(o);return o

def box(name,p,size,role=1):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p)
    o=bpy.context.object;o.name=name;o.scale=size;return finish(o,role)

def beam(name,a,b,w,role=1):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,w,(b-a).length),role)
    o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return o

def cyl(name,a,b,r,role=10,n=8,r2=None):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r,radius2=r if r2 is None else r2,depth=(b-a).length,location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return finish(o,role)

def ring(name,p,r,t,role=10,n=20):
    bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=4,major_radius=r,minor_radius=t,location=p,rotation=(math.pi/2,0,0))
    o=bpy.context.object;o.name=name;return finish(o,role)

for id in ['iron-shadow-warning-frame','north-silence-gate']:
    body=bpy.data.objects[id];parts=[]
    bounds=[(min(v.co[i] for v in body.data.vertices),max(v.co[i] for v in body.data.vertices)) for i in range(3)]
    wide=id=='north-silence-gate'
    # Work in normalized frame coordinates; restore the exact envelope afterward.
    # Back/front trusses, caps and keyed footings create layered antenna craft.
    for side in (-1,1):
        x=side*3.23
        box('Stone socket',(x,0,.14),(.95,.64,.28),6)
        box('Iron foot plate',(x,0,.34),(.79,.58,.12),1)
        for dx in (-.22,.22):
            for y in (-.17,.17):
                beam('Antenna lattice upright',(x+dx,y,.40),(x+dx*.70,y*.65,4.24),.10,1)
        for z in (.57,1.42,2.27,3.12,3.97):
            box('Riveted collar',(x,0,z),(.61,.47,.11),10)
        for y in (-.19,.19):
            for i in range(4):
                z=.64+i*.85
                beam('Lattice diagonal',(x-.19,y,z),(x+.19,y,z+.67),.055,8)
                beam('Lattice diagonal',(x+.19,y,z),(x-.19,y,z+.67),.055,8)
        box('Crown saddle',(x,0,4.25),(.77,.59,.17),1)
        cyl('Antenna ceramic collar',(x,0,4.34),(x,0,4.62),.17,6)
        cyl('Inactive tapered aerial',(x,0,4.62),(x,0,5.02),.19,10,r2=0)
        for z in (.66,2.31,4.05):
            cyl('Front fastener',(x,-.24,z),(x,-.30,z),.064,10)
        # Narrow knee bracing supports the header without filling the opening.
        for y in (-.10,.10):
            beam('Header knee',(x,y,3.39),(x-side*.78,y,4.21),.105,1)
    for z in (4.06,4.38):box('Open header chord',(0,0,z),(6.48,.29,.105),1)
    for i in range(8):
        x=-3.20+i*.80
        beam('Header lattice web',(x,0,4.09),(x+.80,0,4.35),.053,10)
    for x in (-2.4,-1.2,1.2,2.4):
        box('Header clamp',(x,0,4.23),(.10,.38,.44),8)
    # Retain the crossed warning language and unlit null symbol. No active glow.
    for side in (-1,1):
        beam('Crossed silent-field stay',(-2.82,-.03,1.15 if side<0 else 3.63),(2.82,-.03,3.63 if side<0 else 1.15),.085,11)
    beam('Null-symbol hanger',(0,0,4.06),(0,0,3.91),.065,1)
    ring('Empty null bezel',(0,-.10,3.58),.37,.063,10)
    ring('Dark inset bezel',(0,-.08,3.58),.27,.025,1,n=16)
    if wide:
        box('Recessed warning tablet',(0,.03,2.53),(1.34,.22,.52),1)
        for x in (-.68,.68):box('Tablet edge',(x,-.10,2.53),(.07,.10,.57),10)
        for z in (2.25,2.81):box('Tablet rail',(0,-.10,z),(1.43,.10,.07),10)
        for side in (-1,1):beam('Blank tablet diagonal',(-.46,-.18,2.36 if side<0 else 2.70),(.46,-.18,2.70 if side<0 else 2.36),.055,11)
    old=body.data;body.data=bpy.data.meshes.new(id+'Fidelity')
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=body;bpy.ops.object.join();bpy.data.meshes.remove(old)
    for i,(lo,hi) in enumerate(bounds):
        a=min(v.co[i] for v in body.data.vertices);b=max(v.co[i] for v in body.data.vertices)
        for v in body.data.vertices:v.co[i]=lo+(v.co[i]-a)*(hi-lo)/(b-a)
    n=sum(len(f.vertices)-2 for f in body.data.polygons);assert n<=3000,(id,n)
    body['fidelity_recipe']='sources/e7-dead-band-fidelity-2/refine-silent-frames.py'
    r=c['assets'][id];before=r['triangles'];r['triangles']=n
    r['fidelityCorrection']={'recipe':body['fidelity_recipe'],'trianglesBefore':before,'trianglesAfter':n,'features':['twin layered lattice pylons','socket feet and riveted collars','open truss header and knees','unlit ceramic aerials and double null bezel'],'preserved':'exact source envelope, original atlas pixels, mount, inspection station, collision and sibling bodies'}
    print('SILENT FRAME',id,n)

bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'dead-band-landmarks.blend'))
for id in ['iron-shadow-warning-frame','north-silence-gate']:
    bpy.ops.object.select_all(action='DESELECT');body=bpy.data.objects[id];body.select_set(True);bpy.context.view_layer.objects.active=body
    target=PACK/(id+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
    c['assets'][id]['sha256']=sha(target)
c['blend']['sha256']=sha(PACK/'dead-band-landmarks.blend')
(PACK/'dead-band-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
