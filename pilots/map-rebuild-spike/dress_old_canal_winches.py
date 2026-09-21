"""Derive open hand-winches at the three Old Canal decision markers.
Blender --background --python this.py -- --source <base blend> --out <dir>.
All original geometry, exact bounds, atlas and mount/collision truth are retained.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(a.source).resolve()));rows=[]
for letter in ['a','b','c']:
 rig=bpy.data.objects['canal-segment-'+letter+'-marker'];material=rig.data.materials[0]
 original_bounds=([min(v.co[i] for v in rig.data.vertices) for i in range(3)],[max(v.co[i] for v in rig.data.vertices) for i in range(3)])
 parts=[rig];roles={'iron':1,'stone':2,'brass':8,'teal':4,'soot':9}
 def finish(obj,name,role):
  obj.name=name;bpy.context.view_layer.objects.active=obj
  bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
  obj.data.materials.clear();obj.data.materials.append(material)
  while obj.data.uv_layers:obj.data.uv_layers.remove(obj.data.uv_layers[0])
  uv=obj.data.uv_layers.new(name='LandmarkAtlasUV');row,col=divmod(roles[role],4)
  for poly in obj.data.polygons:
   for li in poly.loop_indices:
    co=obj.data.vertices[obj.data.loops[li].vertex_index].co
    u=(co.x*.13+co.z*.07)%1;v=(co.y*.13+co.z*.11)%1
    uv.data[li].uv=((col+.08+.84*u)/4,(row+.08+.84*v)/4)
  parts.append(obj);obj.select_set(False);return obj
 def beam(name,a,b,width,role='iron'):
  delta=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cube_add(size=1,location=(Vector(a)+Vector(b))*.5)
  o=bpy.context.object;o.dimensions=(width,width,delta.length);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return finish(o,name,role)
 def cylinder(name,loc,radius,depth,role='iron',sides=12,scale=(1,1,1)):
  bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=radius,depth=depth,location=loc)
  o=bpy.context.object;o.scale=scale;return finish(o,name,role)
 # Two hand wheels and supported spindle flank the retained open marker.
 for side,cx in enumerate([-2.4,2.4]):
  cz=2.8
  bpy.ops.mesh.primitive_torus_add(major_segments=20,minor_segments=5,location=(cx,-.55,cz),major_radius=.64,minor_radius=.075,rotation=(math.pi/2,0,0));finish(bpy.context.object,'CanalWinch.Wheel.'+str(side),'brass')
  for i in range(6):
   t=i*math.tau/6;beam(f'CanalWinch.Spoke.{side}.{i}',(cx,-.55,cz),(cx+.61*math.cos(t),-.55,cz+.61*math.sin(t)),.06,'iron')
  beam('CanalWinch.Axle.'+str(side),(cx,-.80,cz),(cx,.58,cz),.18,'iron')
  for y in [-.30,.45]:
   beam('CanalWinch.Pedestal.'+str(side),(cx,y,.1),(cx,y,cz),.23,'iron')
   beam('CanalWinch.Shoe.'+str(side),(cx-.4,y,.15),(cx+.4,y,.15),.21,'stone')
  beam('CanalWinch.Crank.'+str(side),(cx+.48,-.58,cz),(cx+.48,-.90,cz),.11,'brass')
 beam('CanalWinch.Drive',(-2.4,.48,2.8),(2.4,.48,2.8),.12,'iron')
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.join();rig.name='canal-segment-'+letter+'-marker'
 for p in rig.data.polygons:p.material_index=0
 while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
 tri=sum(len(p.vertices)-2 for p in rig.data.polygons);assert tri<=3000,tri
 bounds=([min(v.co[i] for v in rig.data.vertices) for i in range(3)],[max(v.co[i] for v in rig.data.vertices) for i in range(3)])
 assert all(abs(a-b)<.0001 for aa,bb in zip(original_bounds,bounds) for a,b in zip(aa,bb)),(original_bounds,bounds)
 bpy.ops.export_scene.gltf(filepath=str((out/(rig.name+'.glb')).resolve()),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
 rows.append({'id':rig.name,'triangles':tri,'sha256':hashlib.sha256((out/(rig.name+'.glb')).read_bytes()).hexdigest(),'bounds':{'min':bounds[0],'max':bounds[1]}})
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str((out/'old-canal-landmarks.blend').resolve()))
(out/'derivation.json').write_text(json.dumps({'sourceSha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'rows':rows},indent=2)+'\n');print('DRESSING_RESULT',json.dumps(rows))
