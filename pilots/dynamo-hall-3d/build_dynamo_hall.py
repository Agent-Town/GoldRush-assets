from pathlib import Path
import hashlib, json, math

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/raw/plate-e3-bld-dynamo-hall.png"
BLEND, GLB = OUT / "dynamo-hall.blend", OUT / "dynamo-hall.glb"
SIZE = 1024
REGIONS = {
    "brick": (.02, .02, .48, .48), "roof": (.52, .52, .98, .98),
    "timber": (.02, .52, .23, .73), "window": (.52, .02, .73, .48),
    "copper": (.77, .02, .98, .48), "stone": (.27, .52, .48, .73),
    "teal": (.02, .77, .23, .98), "dark": (.27, .77, .48, .98),
}

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"

def atlas():
    source = bpy.data.images.load(str(REFERENCE), check_existing=False)
    pixels = np.array(source.pixels[:], dtype=np.float32).reshape(source.size[1], source.size[0], 4)
    colors = pixels[:, :, :3]
    useful = colors[(colors.mean(2) < .72) & ((colors.max(2) - colors.min(2)) > .05)]
    base = np.median(useful, axis=0)
    image = np.ones((SIZE, SIZE, 4), dtype=np.float32)
    image[:, :, :3] = base * .38
    palette = {
        "brick": (.34, .16, .055), "roof": (.075, .047, .023), "timber": (.19, .105, .04),
        "window": (.33, .19, .065), "copper": (.38, .19, .07), "stone": (.28, .23, .15),
        "teal": (.08, .35, .34), "dark": (.055, .055, .04),
    }
    rng = np.random.default_rng(713)
    for name, (u0, v0, u1, v1) in REGIONS.items():
        x0, y0, x1, y1 = [int(v * SIZE) for v in (u0, v0, u1, v1)]
        block = np.array(palette[name], dtype=np.float32) * .97 + rng.normal(0, .018, (y1-y0, x1-x0, 1))
        image[y0:y1, x0:x1, :3] = np.clip(block, .02, .72)
        if name == "brick":
            for row, y in enumerate(range(y0 + 22, y1, 22)):
                image[y:y+2, x0:x1, :3] *= .42
                for x in range(x0 + (18 if row % 2 else 0), x1, 36): image[max(y-22, y0):y, x:x+2, :3] *= .42
        elif name == "roof":
            for y in range(y0 + 20, y1, 20): image[y:y+2, x0:x1, :3] *= .45
        elif name == "timber":
            for x in range(x0 + 18, x1, 28): image[y0:y1, x:x+2, :3] *= .42
        elif name == "window":
            image[y0:y1, x0:x1, :3] = (.31, .18, .06)
            for x in range(x0 + 24, x1, 48): image[y0:y1, x:x+3, :3] = (.055, .07, .055)
            for y in range(y0 + 24, y1, 48): image[y:y+3, x0:x1, :3] = (.055, .07, .055)
        elif name == "copper":
            for x in range(x0 + 16, x1, 25): image[y0:y1, x:x+2, :3] = (.08, .28, .25)
    packed = bpy.data.images.new("DynamoHallPaintedAtlas", SIZE, SIZE, alpha=True)
    packed.colorspace_settings.name = "sRGB"
    packed.pixels.foreach_set(image.ravel()); packed.pack()
    return packed

def material(image):
    mat = bpy.data.materials.new("DynamoHallPaintedMaterial"); mat.use_nodes = True
    nodes = mat.node_tree.nodes; nodes.clear()
    out, shader, tex = nodes.new("ShaderNodeOutputMaterial"), nodes.new("ShaderNodeBsdfPrincipled"), nodes.new("ShaderNodeTexImage")
    tex.image = image; tex.projection = "FLAT"; tex.extension = "REPEAT"; tex.interpolation = "Linear"
    shader.inputs["Metallic"].default_value = 0; shader.inputs["Roughness"].default_value = .9
    shader.inputs["Emission Color"].default_value = (0, 0, 0, 1); shader.inputs["Emission Strength"].default_value = 0
    mat.node_tree.links.new(tex.outputs["Color"], shader.inputs["Base Color"]); mat.node_tree.links.new(shader.outputs["BSDF"], out.inputs["Surface"])
    return mat

def tag(obj, region, mat, bevel=.018):
    obj["atlas_region"] = region; obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Painted edge", "BEVEL"); mod.width = bevel; mod.segments = 1; mod.limit_method = "ANGLE"
    return obj

def box(name, size, at, region, mat, bevel=.018):
    bpy.ops.mesh.primitive_cube_add(location=at); obj = bpy.context.object; obj.name = name; obj.scale = tuple(v/2 for v in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return tag(obj, region, mat, bevel)

def cyl(name, radius, depth, at, region, mat, vertices=12, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=at, rotation=rotation)
    obj = bpy.context.object; obj.name = name
    return tag(obj, region, mat, .012)

def roof(name, width, depth, eave, ridge, region, mat):
    x, y = width/2, depth/2
    verts = [(-x,-y,eave),(x,-y,eave),(x,y,eave),(-x,y,eave),(-x,0,ridge),(x,0,ridge)]
    faces = [(0,1,5,4),(3,4,5,2),(0,4,3),(1,2,5),(0,3,2,1)]
    mesh = bpy.data.meshes.new(name+"Mesh"); mesh.from_pydata(verts, [], faces); mesh.update()
    obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj)
    return tag(obj, region, mat, .025)

def build(mat):
    p=[]; add=p.append
    add(box("Brick dynamo hall", (5.08,2.82,2.72),(0,0,1.36),"brick",mat,.025))
    add(roof("Full wrap roof",5.38,3.24,2.66,3.72,"roof",mat))
    add(box("Raised clerestory",(3.65,1.55,.62),(0,.18,3.36),"timber",mat,.018))
    add(roof("Clerestory roof",4.0,1.9,3.62,4.16,"roof",mat))
    for x in (-1.95,0,1.95):
        add(box(f"Front pier {x}",(.18,.18,2.62),(x,-1.44,1.38),"timber",mat))
    add(box("Front beam",(4.86,.18,.18),(0,-1.44,2.56),"timber",mat))
    add(box("Double door",(.82,.10,1.66),(-1.72,-1.425,.93),"timber",mat))
    for x in (-.55,1.05):
        add(cyl(f"Arched flywheel window {x}",.67,.10,(x,-1.43,1.42),"window",mat,20,rotation=(math.pi/2,0,0)))
        add(cyl(f"Flywheel hub {x}",.16,.16,(x,-1.52,1.42),"copper",mat,12,rotation=(math.pi/2,0,0)))
        for angle in range(0,180,30):
            spoke=box(f"Flywheel spoke {x} {angle}",(1.05,.10,.07),(x,-1.52,1.42),"dark",mat,.008); spoke.rotation_euler.y=math.radians(angle); add(spoke)
    for y in (-.72,.15,.92):
        add(box(f"Side window right {y}",(.10,.58,.72),(2.55,y,1.43),"window",mat))
        add(box(f"Side window left {y}",(.10,.58,.72),(-2.55,y,1.43),"window",mat))
    add(box("Back switchboard",(1.55,.10,1.12),(.65,1.425,1.22),"window",mat))
    add(box("Back service door",(.72,.10,1.55),(-1.30,1.425,.90),"timber",mat))
    for x in (-1.25,-.55,.15,.85,1.55): add(box(f"Clerestory pane {x}",(.46,.08,.30),(x,-.60,3.35),"window",mat,.008))
    for x in (.55,.85,1.15,1.45):
        add(cyl(f"Copper bus bar {x}",.055,1.0,(x,-.12,3.05),"copper",mat,10,rotation=(math.pi/2,0,0)))
    for x in (-2.08,2.08):
        add(box(f"Stone footing {x}",(.48,3.02,.38),(x,0,.19),"stone",mat))
    add(cyl("Teal door lamp",.11,.28,(-1.15,-1.53,1.68),"teal",mat,12))
    return p

def finish(parts):
    for obj in parts:
        bpy.context.view_layer.objects.active=obj; obj.select_set(True)
        for mod in list(obj.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.025); bpy.ops.object.mode_set(mode="OBJECT")
        uv=obj.data.uv_layers.active.data; coords=np.array([[v.uv.x,v.uv.y] for v in uv]); low=coords.min(0); span=np.maximum(coords.max(0)-low,1e-6)
        u0,v0,u1,v1=REGIONS[obj["atlas_region"]]
        for loop, coord in zip(uv,coords):
            n=(coord-low)/span; loop.uv=(u0+n[0]*(u1-u0),v0+n[1]*(v1-v0))
        obj.select_set(False)
    for obj in parts: obj.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join(); hall=bpy.context.object
    hall.name="DynamoHallFullWrap"; hall.data.name="DynamoHallFullWrapMesh"; hall.data.uv_layers.active.name="UVMap"
    bpy.context.scene.cursor.location=(0,0,0); bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(filepath=str(GLB),export_format="GLB",use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials="EXPORT")
    return hall

def main():
    OUT.mkdir(parents=True,exist_ok=True); reset(); hall=finish(build(material(atlas())))
    print(json.dumps({"blend":str(BLEND),"glb":str(GLB),"sha256":hashlib.sha256(GLB.read_bytes()).hexdigest(),"vertices":len(hall.data.vertices),"polygons":len(hall.data.polygons)},indent=2))

if __name__ == "__main__": main()
