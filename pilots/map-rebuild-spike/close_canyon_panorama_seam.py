"""Join the render-only apron to the unchanged terrain; preserve its topology/UVs.

The pinned source leaves a one-metre gap outside the playfield. Its inner ring
now overlaps the terrain by 8 cm and samples that existing surface's height.
Run Blender from the game checkout. No gameplay height source is altered.
"""
from pathlib import Path
import hashlib, json, struct, subprocess, time
import bpy

ROOT=Path.cwd(); OUT=Path(__file__).resolve().parent; STORE=OUT.parents[1]
assert (ROOT/'src/world/Terrain3dClaimPilot.ts').is_file()
RAW=ROOT/'artifacts/sol/map-art-campaign-2/_raw/run-4'/f'canyon-seam-{time.time_ns()}'
RAW.mkdir(parents=True)
pin='213e677'; source='pilots/map-rebuild-spike/canyon-works-panorama.blend'
(RAW/'input.blend').write_bytes(subprocess.check_output(['git','show',pin+':'+source],cwd=STORE))
bpy.ops.wm.open_mainfile(filepath=str(RAW/'input.blend'))
body=next(o for o in bpy.data.objects if o.type=='MESH' and 'Panorama' in o.name)
# Read the existing baked grid; only panorama vertices are written.
data=(OUT/'canyon-works-terrain.glb').read_bytes(); n=struct.unpack_from('<I',data,12)[0]
g=json.loads(data[20:20+n]); a=g['accessors'][g['meshes'][0]['primitives'][0]['attributes']['POSITION']]; v=g['bufferViews'][a['bufferView']]
offset=28+n+v.get('byteOffset',0)+a.get('byteOffset',0)
grid={}
for i in range(a['count']):
    x,y,z=struct.unpack_from('<fff',data,offset+i*12)
    grid[round((x+48)/.75),round((z+56)/.875)]=y
def height(x,z):
    gx=max(0,min(127.999999,(x+48)/.75)); gz=max(0,min(127.999999,(z+56)/.875))
    ix,iz=int(gx),int(gz); tx,tz=gx-ix,gz-iz
    return (grid[ix,iz]*(1-tx)+grid[ix+1,iz]*tx)*(1-tz)+(grid[ix,iz+1]*(1-tx)+grid[ix+1,iz+1]*tx)*tz
changed=[]
for v in body.data.vertices:
    x,y,z=v.co
    if abs(max(abs(x)/49,abs(y)/57)-1)<1e-5:
        nx,ny=x*47.92/49,y*55.92/57
        changed.append({'vertex':v.index,'before':list(v.co),'after':[nx,ny,height(nx,-ny)-.025]})
        v.co=(nx,ny,height(nx,-ny)-.025)
assert len(changed)==97, len(changed)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'canyon-works-panorama.blend'))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(OUT/'canyon-works-panorama.glb'),export_format='GLB',use_selection=True,
    export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
p=OUT/'canyon-works-panorama-contract.json';c=json.loads(p.read_text())
c['projection']['groundSkirtInnerBoundaryMeters'].update(shape='overlapping-playfield-rectangle',margin=-.08,
    height='existing terrain grid minus 0.025 m; render-only, no height-source change')
c['namedCorrections']['terrainSeam']='close_canyon_panorama_seam.py; 97 inner-ring vertices (96 segments plus UV seam) close the one-metre gap'
for key,extension in [('blend','blend'),('glb','glb')]:
    b=(OUT/f'canyon-works-panorama.{extension}').read_bytes();c['files'][key]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
p.write_text(json.dumps(c,indent=2)+'\n')
(RAW/'vertices.json').write_text(json.dumps(changed,indent=2)+'\n')
print('CANYON_SEAM_VERTICES',len(changed))
