"""Derive three braced coil anchors inside their original envelopes and footprints.
Blender --background --python this.py -- --source <base blend> --out <dir>.
Gates, mount transforms, atlas and collisions remain unchanged. No raster is generated.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(a.source).resolve()));rows=[]
roles={'iron':1,'brass':8,'teal':4,'stone':2}
for stage,side in enumerate(['west','center','east']):
 rig=bpy.data.objects[side+'-wind-anchor'];material=rig.data.materials[0];parts=[rig]
 bounds=lambda:([min(v.co[i] for v in rig.data.vertices) for i in range(3)],[max(v.co[i] for v in rig.data.vertices) for i in range(3)])
 old=bounds();assert all(v.co.z<.36 for v in list(rig.data.vertices)[:8])
 bm=bmesh.new();bm.from_mesh(rig.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=list(bm.verts)[:8],context='VERTS');bm.to_mesh(rig.data);bm.free()
 def finish(o,name,role):
  o.name=side+'.'+name;bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
  o.data.materials.clear();o.data.materials.append(material)
  while o.data.uv_layers:o.data.uv_layers.remove(o.data.uv_layers[0])
  uv=o.data.uv_layers.new(name='LandmarkAtlasUV');row,col=divmod(roles[role],4)
  for poly in o.data.polygons:
   # Per-face planar UVs keep narrow braces from sampling unrelated atlas tiles.
   axis=max(range(3),key=lambda j:abs(poly.normal[j]));axes=[j for j in range(3) if j!=axis]
   for li in poly.loop_indices:
    co=o.data.vertices[o.data.loops[li].vertex_index].co
    u=(co[axes[0]]*.20)%1;v=(co[axes[1]]*.20)%1
    uv.data[li].uv=((col+.08+.84*u)/4,(row+.08+.84*v)/4)
  parts.append(o);o.select_set(False);return o
 def cylinder(name,loc,r,depth,role='iron',sides=12,scale=(1,1,1)):
  bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=r,depth=depth,location=loc);o=bpy.context.object;o.scale=scale;return finish(o,name,role)
 def beam(name,a,b,w,role='iron'):
  delta=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cube_add(size=1,location=(Vector(a)+Vector(b))*.5);o=bpy.context.object;o.dimensions=(w,w,delta.length);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return finish(o,name,role)
 cylinder('ChamferedFooting',(0,0,.12),1,.24,'stone',8,(2.8+stage*.2,2.3,1))
 cylinder('PressureHousing',(0,.05,1.05),.76,1.60,'iron')
 cylinder('HousingCrown',(0,.05,1.90),.88,.18,'brass')
 cylinder('CoilSpindle',(0,.05,3.0+stage*.25),.28,2.20+stage*.5,'teal')
 for i in range(3+stage):
  z=2.1+i*.66;r=1.18-i*.055
  bpy.ops.mesh.primitive_torus_add(major_segments=20,minor_segments=5,location=(0,.05,z),major_radius=r,minor_radius=.085);finish(bpy.context.object,f'Coil.{i}','brass')
  for j in range(4):
   t=j*math.tau/4;beam(f'CoilSpoke.{i}.{j}',(.24*math.cos(t),.05+.24*math.sin(t),z),(r*math.cos(t),.05+r*math.sin(t),z),.075,'iron')
 for j in range(4):
  t=math.pi/4+j*math.tau/4;x,y=1.3*math.cos(t),.05+1.3*math.sin(t)
  beam(f'Brace.{j}',(x,y,.25),(.42*math.cos(t),.05+.42*math.sin(t),2.1),.13,'iron')
  cylinder(f'AnchorShoe.{j}',(x,y,.32),.23,.17,'brass',8)
 cylinder('FrontDrive',(0,-1.10,.73),.35,.96,'brass',12)
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.join();rig.name=side+'-wind-anchor'
 for p in rig.data.polygons:p.material_index=0
 while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
 tri=sum(len(p.vertices)-2 for p in rig.data.polygons);assert tri<=3000,tri
 new=bounds();assert all(abs(x-y)<.0001 for aa,bb in zip(old,new) for x,y in zip(aa,bb)),(old,new)
 bpy.ops.export_scene.gltf(filepath=str((out/(rig.name+'.glb')).resolve()),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
 rows.append({'id':rig.name,'triangles':tri,'bounds':{'min':new[0],'max':new[1]},'sha256':hashlib.sha256((out/(rig.name+'.glb')).read_bytes()).hexdigest()})
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str((out/'devils-alley-landmarks.blend').resolve()))
(out/'derivation.json').write_text(json.dumps({'sourceSha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'rows':rows},indent=2)+'\n');print('DRESSING_RESULT',json.dumps(rows))
