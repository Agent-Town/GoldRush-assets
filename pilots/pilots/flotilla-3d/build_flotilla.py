"""Three authored Flotilla hulls; existing E5 helpers and native Claim Boat atlas."""
from pathlib import Path
import bpy, hashlib, importlib.util, json, math, sys
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
helper = REPO / 'assets/pilots/plaza-props-3d/build_era_props_e5.py'
spec = importlib.util.spec_from_file_location('flotilla_e5', helper)
e5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(e5)
c = e5.common
out = Path(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else ROOT
out.mkdir(parents=True, exist_ok=True)
atlas = REPO / 'assets/raw/flotilla-material-atlas.png'
contracts_path = REPO / 'assets/contracts/epoch-5-deepwater/contracts.json'
contract = next(r for r in json.loads(contracts_path.read_text())['contracts'] if r['id'] == 'e5-flotilla')
records = []

for config in contract['tileParams']['flotilla']['hulls']:
    c.reset(); c.ATLAS = atlas; mat = e5.material(); parts = []
    metal = mat.copy(); metal.name = 'BurnishedFlotillaMetal'
    shader = next(n for n in metal.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    shader.inputs['Metallic'].default_value=.5;shader.inputs['Roughness'].default_value=.42
    def box(name, size, pos, ink=3, bevel=.015):
        obj = c.box(name, size, pos, mat, ink, bevel); parts.append(obj); return obj
    def cyl(name, radius, height, pos, ink=10, vertices=12, rotation=(0,0,0)):
        obj = c.cylinder(name, radius, height, pos, mat, ink, vertices, rotation); parts.append(obj); return obj
    def beam(name, a, b, radius=.05, ink=10):
        obj = e5.beam(name, a, b, radius, mat, ink, 8); parts.append(obj); return obj
    def ring(name, radius, tube, pos, ink=10, rotation=(0,0,0)):
        obj = c.torus(name, radius, tube, pos, mat, ink, rotation, (16,4)); parts.append(obj); return obj
    def mesh(name, vertices, faces, ink):
        data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
        obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);c.tag(obj,mat,ink,0);parts.append(obj);return obj
    # Blender +Y is the bow (game -Z). The entire hull fits its owner's radius-five disc.
    outline=[(-2.5,-3.4),(2.5,-3.4),(3.1,-2.5),(3.1,2.5),(2.3,3.6),(0,4.35),(-2.3,3.6),(-3.1,2.5),(-3.1,-2.5)]
    n=len(outline)
    mesh('Tapered timber hull',[(x*.83,y*.9,-.48) for x,y in outline]+[(x,y,.69) for x,y in outline],
         [tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],2)
    mesh('Deck backing',[(x*.97,y*.97,.795) for x,y in outline],[tuple(range(n))],2)
    def clipped(poly, axis, edge, greater):
        result=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            inside_a=(a[axis]>=edge) if greater else (a[axis]<=edge)
            inside_b=(b[axis]>=edge) if greater else (b[axis]<=edge)
            if inside_a:result.append(a)
            if inside_a!=inside_b:
                t=(edge-a[axis])/(b[axis]-a[axis]);result.append(tuple(a[i]+t*(b[i]-a[i]) for i in range(2)))
        return result
    for i in range(13):
        x=-3.25+i*.5
        poly=clipped(clipped([(a*.97,b*.97) for a,b in outline],0,x+.012,True),0,x+.488,False)
        if len(poly)>2:
            plank=mesh('Long timber deck plank',[(a,b,.8) for a,b in poly],[tuple(range(len(poly)))],3)
            plank['long_grain']=True
    for i,(x,y) in enumerate(outline):
        nx,ny=outline[(i+1)%n]
        beam('Hull upper timber',(x,y,.68),(nx,ny,.68),.12,3)
        beam('Hull brass belt',(x*.96,y*.98,.22),(nx*.96,ny*.98,.22),.055,10)
        cyl('Bulwark post',.055,.52,(x*.98,y*.98,1.05),10,8)
        # Gaps amidships let riders reach the central pad without walking through a rail.
        if not (abs(y)==2.5 and abs(ny)==2.5):
            beam('Low side rail',(x*.98,y*.98,1.28),(nx*.98,ny*.98,1.28),.035,10)
    for i in range(10):
        x=-2.25+i*.5
        for y in [-2,1]:box('Staggered plank end',(.48,.018,.008),(x,y+(i%2)*.85,.804),1,0)
    for side in [-1,1]:
        for y in [-2,0,2]:
            cyl('Rope fender',.16,.75,(side*3.07,y,.12),14,10)
            beam('Fender suspension',(side*3.02,y,.9),(side*3.07,y,.44),.027,14)
        e5.lantern(parts,'Bow teal lamp',(side*2.1,3.2,1.45),mat,1.1)
        cyl('Mooring bollard',.11,.32,(side*2.55,-2.85,.98),10,8)
        beam('Bollard crossbar',(side*2.55-.2,-2.85,1.12),(side*2.55+.2,-2.85,1.12),.045,10)

    district=config['district']
    if district == 'kitchen':
        # Aft canvas shelter and flue leave a 1.5 m clear radius at the build pad.
        for x in [-1.75,1.75]:
            for y in [-3.0,-1.65]:beam('Canvas shelter post',(x,y,.8),(x,y,2.35),.065,3)
        for y in [-3.0,-1.65]:
            beam('Canvas roof ridge support',(-1.75,y,2.35),(0,y,3.05),.045,3)
            beam('Canvas roof ridge support',(0,y,3.05),(1.75,y,2.35),.045,3)
        beam('Canvas ridge',(0,-3.1,3.05),(0,-1.55,3.05),.055,3)
        canvas=[]
        for j in range(5):
            for i in range(9):
                x=-1.9+i*.475;y=-3.1+j*1.55/4
                z=3.08-.72*abs(x)/1.9-.16*math.sin(math.pi*j/4)*math.sin(math.pi*abs(x)/1.9)
                canvas.append((x,y,z))
        mesh('Tensioned canvas',canvas,[(j*9+i,j*9+i+1,(j+1)*9+i+1,(j+1)*9+i) for j in range(4) for i in range(8)],12)
        box('Galley counter',(3.2,.52,.82),(0,-2.87,1.21),3)
        box('Galley stove',(.72,.65,.9),(2.05,-1.92,1.25),9)
        cyl('Stove cooking plate',.25,.05,(2.05,-1.92,1.73),1)
        cyl('Galley flue',.14,2.35,(2.05,-2.22,2.1),10)
        cyl('Rain cap',.25,.08,(2.05,-2.22,3.31),10)
        box('Stove door surround',(.53,.025,.52),(2.05,-1.585,1.22),10)
        box('Stove dark fire door',(.43,.025,.42),(2.05,-1.567,1.22),0)
        beam('Fire door handle',(2.10,-1.53,1.23),(2.23,-1.53,1.23),.028,10)
        cyl('Stove saucepan',.2,.25,(2.05,-1.92,1.86),10)
        beam('Saucepan handle',(2.2,-1.92,1.98),(2.55,-1.92,1.98),.045,1)
        for x in [-.85,.85]:
            cyl('Cooking pot',.3,.38,(x,-2.85,1.8),10)
            ring('Pot rim',.3,.035,(x,-2.85,2),11)
            for side in [-1,1]:ring('Pot loop handle',.1,.027,(x+side*.32,-2.85,1.83),10,(math.pi/2,0,0))
            ring('Pot lid handle',.07,.025,(x,-2.85,2.04),10,(math.pi/2,0,0))
    elif district == 'still-room':
        # Bulbous copper kettle, condenser coil and supported return pipe.
        box('Still machinery plinth',(3.9,1.7,.18),(0,-2.5,.9),3)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=(-.8,-2.45,1.9))
        obj=bpy.context.object;obj.name='Copper still belly';obj.scale=(.9,.9,1.0);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);c.tag(obj,mat,10,0);parts.append(obj)
        cyl('Still neck',.34,.7,(-.8,-2.45,3.02),10)
        cyl('Still cap',.42,.12,(-.8,-2.45,3.4),11)
        for z in [1.25,1.6,2.2]:ring('Still copper band',.9*math.sqrt(1-(z-1.9)**2),.035,(-.8,-2.45,z),11)
        cyl('Condenser base',.5,.12,(1.1,-2.45,1.04),9)
        curve=bpy.data.curves.new('Continuous condenser coil','CURVE');curve.dimensions='3D';curve.bevel_depth=.055;curve.bevel_resolution=3;curve.use_fill_caps=True
        spline=curve.splines.new('POLY');spline.points.add(100)
        for i,point in enumerate(spline.points):
            angle=i/100*8*math.pi;point.co=(1.1+.39*math.cos(angle),-2.45+.39*math.sin(angle),1.2+i/100*1.4,1)
        coil=bpy.data.objects.new('Continuous condenser coil',curve);bpy.context.collection.objects.link(coil)
        bpy.ops.object.select_all(action='DESELECT');coil.select_set(True);bpy.context.view_layer.objects.active=coil;bpy.ops.object.convert(target='MESH');coil=bpy.context.object;c.tag(coil,mat,10,0);parts.append(coil)
        for polygon in coil.data.polygons:polygon.use_smooth=True
        beam('Condenser spine',(1.1,-2.45,1.0),(1.1,-2.45,2.7),.055,9)
        beam('Still vapor riser',(-.8,-2.45,3.46),(-.8,-2.45,3.7),.095,10)
        beam('Still vapor bridge',(-.8,-2.45,3.7),(1.49,-2.45,3.7),.095,10)
        beam('Condenser inlet',(1.49,-2.45,3.7),(1.49,-2.45,2.6),.095,10)
        cyl('Collection cask',.38,.6,(2.22,-1.85,1.1),3)
        ring('Cask hoop',.39,.035,(2.22,-1.85,1.3),10)
        beam('Condenser outlet',(1.49,-2.45,1.2),(2.22,-1.85,1.45),.065,10)
    else:
        # The real player-built weapon owns the center; this raft supplies its working rig.
        for x in [-2,2]:
            beam('Rig mast',(x,-2.4,.8),(x,-2.4,2.75),.11,3)
            beam('Rig mast brace',(x,-1.7,.8),(x,-2.4,2.0),.075,10)
            beam('Derrick arm',(x,-2.4,2.75),(x,-.6,3.25),.085,10)
            beam('Derrick stay',(x,-2.4,1.3),(x,-.6,3.25),.05,10)
            cyl('Rig pulley',.26,.16,(x,-.6,3.25),10,12,(0,math.pi/2,0))
            beam('Winch haul rope',(x*.55,-2.45,1.63),(x,-.6,3.5),.028,14)
            beam('Pulley hanging rope',(x,-.35,3.27),(x,-.35,1.8),.028,14)
            beam('Cargo hook shank',(x,-.35,1.8),(x,-.35,1.62),.045,10)
            beam('Cargo hook bend',(x,-.35,1.62),(x+.15,-.35,1.55),.045,10)
            beam('Cargo hook tip',(x+.15,-.35,1.55),(x+.22,-.35,1.7),.045,10)
        beam('Rig aft crossbeam',(-2,-2.4,2.7),(2,-2.4,2.7),.11,3)
        cyl('Aft winch drum',.37,2.25,(0,-2.45,1.23),14,12,(0,math.pi/2,0))
        for x in [-1.2,1.2]:
            box('Winch pedestal',(.22,.6,.65),(x,-2.45,1.125),10)
            cyl('Winch endplate',.44,.14,(x,-2.45,1.3),10,12,(0,math.pi/2,0))

    # Use the established Claim Boat deterministic atlas projection and triangulation.
    c.apply_palette_uv(parts,False)
    for obj in parts:
        if 8<=int(obj['palette_index'])<=11:obj.data.materials[0]=metal
        vertices=obj.data.vertices;uv=obj.data.uv_layers.active
        low=[min(v.co[a] for v in vertices) for a in range(3)];high=[max(v.co[a] for v in vertices) for a in range(3)]
        index=int(obj['palette_index']);column,row=index%4,index//4
        for polygon in obj.data.polygons:
            dominant=max(range(3),key=lambda a:abs(polygon.normal[a]));axes=[a for a in range(3) if a!=dominant]
            if obj.get('long_grain') and dominant==2:axes.reverse()
            for loop in polygon.loop_indices:
                co=vertices[obj.data.loops[loop].vertex_index].co;u,v=[(co[a]-low[a])/max(high[a]-low[a],1e-6) for a in axes]
                uv.data[loop].uv=(round((column+.025+u*.95)/4,6),round((row+.025+v*.95)/4,6))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:obj.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();model=bpy.context.object;model.name=config['id']
    mod=model.modifiers.new('Fixed triangles','TRIANGULATE');mod.quad_method='FIXED';mod.ngon_method='CLIP';bpy.ops.object.modifier_apply(modifier=mod.name)
    old=model.data;faces=[]
    for polygon in old.polygons:
        vertices=list(polygon.vertices);loops=list(polygon.loop_indices);first=vertices.index(min(vertices))
        vertices=vertices[first:]+vertices[:first];loops=loops[first:]+loops[:first]
        faces.append((vertices,[tuple(old.uv_layers.active.data[i].uv) for i in loops],polygon.material_index,polygon.use_smooth))
    faces.sort(key=lambda row:tuple(row[0]));data=bpy.data.meshes.new(config['id']+'Canonical')
    data.from_pydata([tuple(v.co) for v in old.vertices],[],[r[0] for r in faces]);data.update();uv=data.uv_layers.new(name='UVMap')
    for material in old.materials:data.materials.append(material)
    for polygon,(_,coords,material_index,smooth) in zip(data.polygons,faces):
        for loop,coord in zip(polygon.loop_indices,coords):uv.data[loop].uv=coord
        polygon.material_index=material_index;polygon.use_smooth=smooth
    model.data=data;bpy.data.meshes.remove(old)
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    assert len(data.polygons)<=12000,(config['id'],len(data.polygons))
    assert max(math.hypot(v.co.x,v.co.y) for v in data.vertices)<=config['radius'],config['id']
    clearance=[]
    for x in [-1,-.5,0,.5,1]:
        for z in [-1,-.5,0,.5,1]:
            hit,point,_,_=model.ray_cast(Vector((x,-z,20)),Vector((0,0,-1)))
            assert hit and .79<=point.z<=.83,(config['id'],x,z,tuple(point))
            clearance.append({'x':x,'z':z,'topY':point.z})
    stem=config['id'];bpy.ops.wm.save_as_mainfile(filepath=str(out/(stem+'.blend')))
    bpy.ops.export_scene.gltf(filepath=str(out/(stem+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=False)
    (out/(stem+'.export.json')).write_text(json.dumps({'profile':'static','extras':False,'animations':False,'applyTransforms':True,'selection':[stem]},indent=2)+'\n')
    records.append({'id':stem,'district':district,'radius':config['radius'],'deckY':.8,'deckOutline':[[x*.97,-y*.97] for x,y in outline],'triangles':len(data.polygons),'sha256':hashlib.sha256((out/(stem+'.glb')).read_bytes()).hexdigest(),'clearance':clearance})

sources=[Path(__file__).resolve(),helper,helper.with_name('build_era_props_e2.py'),atlas,contracts_path,REPO/'assets/raw/plate-contract-e5-flotilla.png']
(out/'flotilla-contract.json').write_text(json.dumps({'status':'candidate; visual and runtime acceptance pending','concept':'assets/raw/plate-contract-e5-flotilla.png','sourceTier':'build-new with existing E5 helpers and native atlas','textureSize':[512,512],'meshCountPerHull':2,'gltfMeshCountPerHull':1,'materialCountPerHull':2,'hulls':records,'sourceHashes':{str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}},indent=2)+'\n')
print('FLOTILLA',[(r['id'],r['triangles'],r['sha256']) for r in records])
