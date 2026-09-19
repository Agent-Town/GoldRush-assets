"""Repack native Baron materials into existing per-body sources; no geometry changes.

Blender --background --python-exit-code 1 --python this.py -- PACK_DIRECTORY RAW_ATLAS
The headframe legs use medium wood; seven banners use the full emblem.
Roof/rocket accents sample plain oxblood. Repeat runs preserve the same UVs.
"""
import bpy, hashlib, json, sys
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
pack,raw=map(lambda p:Path(p).resolve(),args)
contract_path=pack/'baron-landmark-pack-contract.json';contract=json.loads(contract_path.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def remap_emblems(obj,identifier):
 m=obj.data
 before=([tuple(v.co) for v in m.vertices],[tuple(f.vertices) for f in m.polygons]);parent=list(range(len(m.vertices)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for e in m.edges:
  a,b=map(find,e.vertices);parent[b]=a
 groups={}
 for face in m.polygons:groups.setdefault(find(face.vertices[0]),[]).append(face)
 components=[]
 for faces in groups.values():
  cells=set()
  for face in faces:
   uv=[m.uv_layers.active.data[i].uv for i in face.loop_indices];cells.add((int(sum(v.x for v in uv)/len(uv)*4),int((1-sum(v.y for v in uv)/len(uv))*4)))
  if cells!={(1,0)}:continue
  ids=set(v for f in faces for v in f.vertices)
  if len(ids)!=42:
   assert (identifier,len(ids)) in {('fortified_far_bank',18),('rocket_cart',20)}
   for face in faces:
    for i in face.loop_indices:
     uv=m.uv_layers.active.data[i].uv.copy()
     if not (.261999 <= uv.x <= .272001 and .761999 <= uv.y <= .772001):
      m.uv_layers.active.data[i].uv=(.262+.01*(uv.x-.26)/.23,.762+.01*(uv.y-.76)/.23)
   components.append({'kind':'plain-oxblood','faces':len(faces),'vertices':len(ids)})
   continue
  lowx=min(m.vertices[i].co.x for i in ids);highx=max(m.vertices[i].co.x for i in ids);lowz=min(m.vertices[i].co.z for i in ids);highz=max(m.vertices[i].co.z for i in ids)
  assert highx-lowx>1 and highz-lowz>1
  for face in faces:
   for i in face.loop_indices:
    co=m.vertices[m.loops[i].vertex_index].co;m.uv_layers.active.data[i].uv=(.26+.23*(co.x-lowx)/(highx-lowx),.76+.23*(co.z-lowz)/(highz-lowz))
  components.append({'kind':'emblem-cloth','faces':len(faces),'vertices':len(ids)})
 assert before==([tuple(v.co) for v in m.vertices],[tuple(f.vertices) for f in m.polygons])
 return components
records=[]
for identifier,record in contract['assets'].items():
 source=pack/Path(record['blend']['asset']).name
 bpy.ops.wm.open_mainfile(filepath=str(source))
 objects=[o for o in bpy.data.objects if o.type=='MESH'];assert len(objects)==1
 obj=objects[0];geometry=([tuple(v.co) for v in obj.data.vertices],[tuple(f.vertices) for f in obj.data.polygons])
 changed=0
 if identifier=='seized_headframe':
  medium=0
  for face in obj.data.polygons:
   loops=[obj.data.uv_layers.active.data[i] for i in face.loop_indices]
   u=sum(d.uv.x for d in loops)/len(loops);v=sum(d.uv.y for d in loops)/len(loops)
   if int((1-v)*4)==3:
    if int(u*4)==0:
     for d in loops:d.uv.x+=.25
     changed+=1
    elif int(u*4)==1:medium+=1
  assert (changed,medium) in {(104,78),(0,182)},(changed,medium)
 components=remap_emblems(obj,identifier)
 image=bpy.data.images.load(str(raw),check_existing=False);assert min(image.size)>0
 image.scale(1024,1024);image.filepath_raw=str(pack/'baron-landmarks-atlas.png');image.file_format='PNG';image.save();image.colorspace_settings.name='sRGB';image.pack()
 nodes=[n for m in obj.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE'];assert len(nodes)==1
 previous=nodes[0].image;nodes[0].image=image
 if previous is not None and previous.users==0:bpy.data.images.remove(previous)
 image.name='BaronLandmarkMaterialAtlas'
 assert geometry==([tuple(v.co) for v in obj.data.vertices],[tuple(f.vertices) for f in obj.data.polygons])
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(source))
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 target=pack/(identifier+'.glb');bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True)
 record['sha256']=sha(target);record['blend']['sha256']=sha(source);records.append({'id':identifier,'remappedFaces':changed,'emblemComponents':components,'sha256':sha(target)})
contract['atlas']['sha256']=sha(pack/'baron-landmarks-atlas.png')
contract_path.write_text(json.dumps(contract,indent=2)+'\n')
print(json.dumps(records))
