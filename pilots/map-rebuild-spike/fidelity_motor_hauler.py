"""Authored shared Motor hauler, 2400-triangle budget; no raster generation."""
from pathlib import Path
import bpy,math,json,hashlib
OUT=Path.cwd()/'assets/pilots/map-rebuild-spike/landmarks/motor-hauler';OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.context.preferences.filepaths.save_version=0
parts=[]
def mat(name,color,rough,metal,emission=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Roughness'].default_value=rough;s.inputs['Metallic'].default_value=metal;s.inputs['Emission Color'].default_value=(*color,1);s.inputs['Emission Strength'].default_value=emission;return m
steel=mat('HaulerPaintedSteel',(.12,.25,.23),.58,.3);brass=mat('HaulerBrass',(.65,.37,.10),.5,.42);rubber=mat('HaulerRubber',(.035,.03,.025),.93,0);wood=mat('HaulerWood',(.25,.12,.045),.9,0);glass=mat('HaulerTealGlass',(.10,.38,.36),.28,.25,.18)
def finish(obj,name,material):obj.name=name;obj.data.materials.append(material);parts.append(obj);return obj
def box(name,loc,size,material,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('Authored softened edges','BEVEL');m.width=bevel;m.segments=1;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
    return finish(o,name,material)
def cylinder(name,loc,r,depth,material,axis='Z',vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);o=bpy.context.object
    if axis=='X':o.rotation_euler.y=math.pi/2
    if axis=='Y':o.rotation_euler.x=math.pi/2
    return finish(o,name,material)
box('Chassis',(0,0,.62),(1.78,3.02,.36),steel,.07)
box('Front bumper',(0,-1.49,.51),(1.8,.12,.18),brass,.025)
box('Cab roof',(0,-.72,1.52),(1.58,1.30,.12),steel,.035)
box('Cab sill',(0,-.72,.90),(1.54,1.22,.20),brass,.025)
for x in [-.70,.70]:
    for y in [-1.27,-.18]:box('Cab post',(x,y,1.18),(.11,.11,.62),brass,.015)
box('Windshield',(0,-1.28,1.22),(1.28,.035,.43),glass)
for x in [-.725,.725]:box('Side glass',(x,-.72,1.22),(.035,.91,.42),glass)
box('Cab rear',(0,-.15,1.18),(1.45,.10,.58),steel,.015)
box('Bonnet',(0,-1.38,.93),(1.42,.27,.23),steel,.045)
for x in [-.5,-.3,-.1,.1,.3,.5]:box('Grille slat',(x,-1.53,.82),(.055,.035,.18),brass)
for x in [-.62,.62]:
    cylinder('Lamp bezel',(x,-1.50,1.03),.12,.065,brass,'Y',10)
    cylinder('Lamp glass',(x,-1.538,1.03),.085,.012,glass,'Y',10)
for i in range(5):box('Bed floor plank',(0,.15+i*.27,.835),(1.48,.24,.065),wood)
for x in [-.78,.78]:
    box('Bed side rail',(x,.68,1.01),(.09,1.40,.12),brass)
    for y in [.05,.70,1.34]:box('Bed upright',(x,y,.94),(.08,.08,.38),steel)
box('Tail rail',(0,1.37,1.0),(1.6,.1,.16),wood)
for x in [-.99,.99]:
    for y in [-1,1]:
        # One faceted tire, bright hub and axle cap per wheel.
        cylinder('Tire',(x,y,.45),.42,.28,rubber,'X',16)
        cylinder('Wheel rim',(x+(1 if x>0 else -1)*.135,y,.45),.28,.012,brass,'X',12)
        cylinder('Hub',(x+(1 if x>0 else -1)*.135,y,.45),.10,.028,steel,'X',8)
# The ratified Motor bundle leaves the stake bed empty for composed cargo.
for x in [-.99,.99]:
    box('Running board',(x,0,.55),(.20,.80,.10),steel,.025)
box('Rear bumper',(0,1.49,.51),(1.8,.12,.18),brass,.025)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=bpy.context.object;body.name='MotorHauler';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
for key,value in {'render_only':True,'landmark':True,'mount_id':'motor-hauler','map_pack':'motor-hauler','era':4}.items():body[key]=value
tri=sum(len(f.vertices)-2 for f in body.data.polygons);assert tri<=2400,tri
blend=OUT/'motor-hauler.blend';glb=OUT/'motor-hauler.glb';bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
verts=[tuple(v.co) for v in body.data.vertices];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'asset':'landmarks/motor-hauler/motor-hauler.glb','sourceTier':'build-new','sources':['assets/pilots/map-rebuild-spike/fidelity_motor_hauler.py','assets/pilots/map-rebuild-spike/landmarks/motor-hauler/motor-hauler.blend','assets/raw/plate-contract-e4-boneyard.png'],'triangleBudget':2400,'triangles':tri,'meshCount':5,'materialCount':5,'bounds':{'min':[min(v[i] for v in verts) for i in range(3)],'max':[max(v[i] for v in verts) for i in range(3)]},'sha256':sha(glb),'blendSha256':sha(blend)}
c={'map':'motor-hauler','era':4,'renderOnly':True,'dynamicOwner':'src/entities/Vehicle.ts; no terrain landmark mount or collision registration','recipe':'fidelity_motor_hauler.py','simulation':'Existing Vehicle movement/fuel/path/reset behavior is the sole authority. Authored body only.','cargoBed':'Empty per specs/epoch-saga/e4-motor-bundle.md A3; no gameplay cargo invented.','rasterGenerated':False,'assets':{'motor-hauler':record}}
(OUT/'motor-hauler-landmark-pack-contract.json').write_text(json.dumps(c,indent=2)+'\n')
p=OUT.parent/'landmark-source-ledger.json';ledger=json.loads(p.read_text());ledger['packs']['motor-hauler']={'motor-hauler':{k:record[k] for k in ['sourceTier','sources','asset']}};p.write_text(json.dumps(ledger,indent=2)+'\n');print('MOTOR BODY',tri)
