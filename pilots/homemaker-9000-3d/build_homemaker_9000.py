from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

sys.dont_write_bytecode = True

import bpy
import numpy as np
from mathutils import Vector


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "package.json").is_file() and (p / "assets").is_dir())
HERE = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/raw/plate-e6-boss-homemaker-9000.png"
BLEND = HERE / "homemaker-9000.blend"
GLB = HERE / "homemaker-9000.glb"
MODEL_LENGTH = 7.2


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dq = load("homemaker_shared_builder", ROOT / "assets/pilots/dredge-queen-3d/build_dredge_queen.py")
kit = load("homemaker_shape_helpers", ROOT / "assets/pilots/dredge-queen-3d/detail_opus5_kit.py")


def create_atomic_atlas() -> bpy.types.Image:
    # Keep UVs inside each native field, away from the painted tile borders.
    cells={"iron":(0,2),"plate":(0,2),"amber":(1,2),"teal":(2,2),"brass":(0,1),
           "soot":(1,1),"cargo":(2,1),"sail":(0,0),"deck":(1,0),
           "damage":(2,0)}
    dq.REGIONS={name:((x+.07)/3,(y+.07)/3,(x+.93)/3,(y+.93)/3)
                for name,(x,y) in cells.items()}
    dq.REGIONS["glow"]=(.48,.80,.54,.87)
    image=bpy.data.images.load(str(ROOT / "assets/raw/homemaker-atlas-fidelity-e6.png"),check_existing=False)
    image.name="Homemaker9000NativeAtlas"
    image.colorspace_settings.name="sRGB"
    image.scale(1024,1024)
    image.pack()
    return image


def build_vac(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    upper, hose, head = "VacUpperArm", "VacHose", "VacHead"
    shoulder = Vector((-1.72, -0.12, 4.35))
    elbow = Vector((-2.60, -0.24, 3.72))
    wrist = Vector((-2.78, -0.38, 2.58))
    parts.append(dq.cylinder("VAC shoulder bearing", 0.48, 0.52, tuple(shoulder), "brass", material,
                             vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=upper))
    parts.append(dq.torus("VAC shoulder teal seal", 0.40, 0.07, tuple(shoulder), "teal", material,
                          rotation=(math.pi / 2, 0, 0), damage_group=upper, major_segments=14))
    parts.append(dq.beam("VAC upper service arm", tuple(shoulder), tuple(elbow), 0.34, "plate", material, upper))
    parts.append(dq.cylinder("VAC elbow joint", 0.34, 0.48, tuple(elbow), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=upper))
    parts.append(dq.beam("VAC lower service arm", tuple(elbow), tuple(wrist), 0.30, "iron", material, upper))
    parts.append(dq.cylinder("VAC wrist coupling", 0.26, 0.42, tuple(wrist), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=upper))

    control = [Vector(p) for p in ((-1.48,-1.04,3.66),(-3.36,-1.5,3.28),
                                       (-3.48,-1.1,1.86),(-2.72,-.52,.72))]
    hose_points=[]
    for i in range(17):
        t=i/16
        hose_points.append(control[0]*(1-t)**3+control[1]*(3*t*(1-t)**2)
                           +control[2]*(3*t*t*(1-t))+control[3]*t**3)
    rings=[]
    for i,center in enumerate(hose_points):
        tangent=(hose_points[min(16,i+1)]-hose_points[max(0,i-1)]).normalized()
        side=tangent.cross(Vector((0,1,0))).normalized();up=tangent.cross(side)
        radius=.38+.07*math.sin(math.pi*i/16)
        rings.append([tuple(center+radius*(side*math.cos(a)+up*math.sin(a)))
                      for a in (j*math.tau/12 for j in range(12))])
        parts.append(dq.torus(f"VAC hose rib {i}",radius+.025,.035,tuple(center),
            "iron",material,rotation=tuple(tangent.to_track_quat("Z","Y").to_euler()),
            damage_group=hose,major_segments=12))
    parts.append(kit.loft("VAC curved hose",rings,"soot",material,damage_group=hose,smooth=True))
    head_rings=[]
    for z,rx,ry in ((.12,1.16,.76),(.22,1.20,.78),(.42,1.12,.72),(.67,.68,.50),(.76,.35,.28)):
        head_rings.append([(-2.72+rx*math.cos(a),-.52+ry*math.sin(a),z)
                           for a in (j*math.tau/24 for j in range(24))])
    parts.append(kit.loft("VAC domed floor head",head_rings,"plate",material,damage_group=head,smooth=True))
    parts.append(dq.box("VAC mint bumper",(2.30,1.45,.15),(-2.72,-.52,.15),
                        "cargo",material,.055,damage_group=head))
    parts.append(dq.box("VAC teal starburst pane",(.76,.055,.31),(-2.72,-1.21,.40),
                        "teal",material,.05,damage_group=head))
    for x in (-3.43,-2.01):
        parts.append(dq.cylinder(f"VAC amber intake {x}",.23,.12,(x,-1.14,.29),
            "brass",material,vertices=12,rotation=(math.pi/2,0,0),bevel=0,damage_group=head))
    for x in (-3.48, -1.96):
        parts.append(dq.cylinder(f"VAC caster {x}", 0.18, 0.22, (x, -0.42, 0.13), "soot", material,
                                 vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=head))
    for shard, at in enumerate(((-2.65, -0.62, 0.32), (-2.58, -0.54, 0.30), (-2.72, -0.58, 0.28))):
        parts.append(dq.box(f"Hidden VAC scrap {shard}", (0.18, 0.10, 0.08), at,
                            "damage", material, 0.002, damage_group=f"VacShard{shard}"))
    return parts


def bread_slice(parts: list[bpy.types.Object], index: int, x: float, material: bpy.types.Material) -> None:
    profile=[(-.62,5.84),(.62,5.84),(.62,6.45),(.53,6.68),(.29,6.82),
             (-.29,6.82),(-.53,6.68),(-.62,6.45)]
    parts.append(kit.loft(f"RACK rounded toast {index}",
        [[(xx,y,z) for y,z in profile] for xx in (x-.20,x+.20)],
        "brass",material,damage_group="RackUpper"))
    for side in (-1,1):
        points=[(x+side*.22,y,z) for y,z in profile+[profile[0]]]
        kit.polyline(parts,f"RACK toast rim {index} {side}",points,.035,"brass",material,"RackUpper")


def build_rack(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    group = "RackUpper"
    parts.append(dq.box("RACK battery sill", (4.04, 2.10, 0.30), (0, 0, 5.62),
                        "iron", material, 0.05, damage_group=group))
    parts.append(dq.box("RACK amber rail front", (4.18, 0.10, 0.16), (0, -1.02, 5.76),
                        "brass", material, 0.015, damage_group=group))
    parts.append(dq.box("RACK amber rail rear", (4.18, 0.10, 0.16), (0, 1.02, 5.76),
                        "brass", material, 0.015, damage_group=group))
    for index, x in enumerate(np.linspace(-1.58, 1.58, 7)):
        bread_slice(parts, index, float(x), material)
        arch=[(float(x),-.94,5.75)]+[(float(x),.94*math.cos(a),6.0+.94*math.sin(a))
            for a in (math.pi-j*math.pi/8 for j in range(9))]+[(float(x),.94,5.75)]
        kit.polyline(parts,f"RACK arched cage {index}",arch,.065,"iron",material,group)
    for side in (-1,1):
        profile=[(-1.02,5.57),(1.02,5.57)]+[(.99*math.cos(a),6.0+.99*math.sin(a))
                 for a in (j*math.pi/8 for j in range(9))]
        parts.append(kit.loft(f"RACK curved end housing {side}",
            [[(side*2.04+dx,y,z) for y,z in profile] for dx in (-.06,.06)],
            "iron",material,damage_group=group))
        parts.append(dq.cylinder(f"RACK end terminal {side}",.24,.12,(side*2.16,0,6.05),
            "teal",material,vertices=12,rotation=(0,math.pi/2,0),bevel=0,damage_group=group))
        parts.append(dq.torus(f"RACK end terminal rim {side}",.28,.035,(side*2.23,0,6.05),
            "brass",material,rotation=(0,math.pi/2,0),damage_group=group,major_segments=12))
    for shard, at in enumerate(((-1.2, 0, 5.96), (0.1, 0, 5.92), (1.1, 0, 5.94))):
        parts.append(dq.box(f"Hidden toast shard {shard}", (0.24, 0.12, 0.10), at,
                            "damage", material, 0.002, damage_group=f"RackShard{shard}"))
    return parts


def build_core(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    body, left_leg, right_leg, broom, chair = "ChairBody", "ChairLeftLeg", "ChairRightLeg", "ChairBroom", "ChairDebris"
    body_rings=[]
    for z,rx,ry in ((2.5,1.65,1.24),(3.0,1.85,1.34),(4.45,1.85,1.34),
                    (4.95,1.7,1.24),(5.28,1.3,1.0),(5.48,.62,.60),(5.50,.15,.20)):
        body_rings.append([(rx*math.cos(a),ry*math.sin(a),z)
                           for a in (j*math.tau/32 for j in range(32))])
    parts.append(kit.loft("CORE rounded pressure body",body_rings,"plate",material,damage_group=body,smooth=True))
    for name,z,rx,ry,region in (("upper casing seam",4.74,1.83,1.35,"brass"),
                                ("lower machine belt",3.02,1.88,1.38,"soot")):
        rings=[[(radius_x*math.cos(a),radius_y*math.sin(a),height)
                for a in (j*math.tau/32 for j in range(32))]
               for height,radius_x,radius_y in ((z-.06,rx,ry),(z,rx+.10,ry+.10),(z+.06,rx,ry))]
        parts.append(kit.loft(f"CORE {name}",rings,region,material,cap_start=False,cap_end=False,damage_group=body))
    for name,region,profile in (("CORE flared teal skirt","cargo",((1.85,2.10,1.66),(2.05,2.04,1.61),(2.9,1.61,1.25))),
                                ("CORE cream dust ruffle","sail",((1.64,2.16,1.71),(1.87,2.10,1.66)))):
        rings=[]
        for z,rx,ry in profile:
            rings.append([(rx*math.cos(a)*(1+.025*math.cos(16*a)),ry*math.sin(a)*(1+.025*math.cos(16*a)),z)
                          for a in (j*math.tau/64 for j in range(64))])
        parts.append(kit.loft(name,rings,region,material,damage_group=body))
    apron=[]
    for z,width,y in ((1.93,.66,-1.72),(2.1,.76,-1.68),(2.84,.57,-1.40)):
        apron.append([(-width,y,z),(width,y,z),(width,y+.055,z),(-width,y+.055,z)])
    parts.append(kit.loft("CORE cream apron",apron,"sail",material,damage_group=body))
    lens_rings=[]
    for y,radius in ((-1.28,.97),(-1.95,.97),(-2.02,.90),(-1.93,.79),(-1.78,.66)):
        lens_rings.append([(radius*math.cos(a),y,4.02+radius*math.sin(a))
                           for a in (j*math.tau/24 for j in range(24))])
    parts.append(kit.loft("CORE inset lens barrel",lens_rings,"iron",material,
                          cap_start=False,cap_end=False,damage_group=body))
    parts.append(dq.torus("CORE amber lens cage",.91,.075,(0,-1.98,4.02),"brass",material,
        rotation=(math.pi/2,0,0),damage_group=body,major_segments=24))
    parts.append(dq.cylinder("CORE amber lens",.66,.06,(0,-1.80,4.02),"amber",material,
        vertices=24,rotation=(math.pi/2,0,0),bevel=0,damage_group=body))
    parts.append(dq.ico_sphere("CORE lens glow",.63,(0,-1.84,4.02),"amber",material,body,scale=(1,.20,1)))
    for i in range(12):
        a=i*math.tau/12
        parts.append(dq.beam(f"CORE lens radial spoke {i}",(.23*math.cos(a),-1.974,4.02+.23*math.sin(a)),
            (.73*math.cos(a),-1.974,4.02+.73*math.sin(a)),.032,"brass",material,body))
    parts.append(dq.cylinder("CORE bright iris center",.20,.008,(0,-1.974,4.02),"glow",material,
        vertices=24,rotation=(math.pi/2,0,0),bevel=0,damage_group=body))
    # This cold shutter begins hidden inside the body and moves over the amber
    # core only in the final chair morph: powered down must read without light.
    parts.append(dq.ico_sphere("CORE hidden shutdown shutter",.64,(0,0,4.02),
                              "soot",material,"CoreShutdownShutter",scale=(1,.21,1)))
    for x, z in ((-1.12, 4.38), (1.10, 4.42), (-0.78, 3.50), (0.78, 3.48)):
        parts.append(dq.cylinder(f"CORE teal dial {x} {z}", 0.24, 0.10, (x, -1.51, z),
                                 "teal", material, vertices=12, rotation=(math.pi / 2, 0, 0),
                                 bevel=0, damage_group=body))
        parts.append(dq.torus(f"CORE dial cage {x} {z}", 0.26, 0.035, (x, -1.57, z),
                              "brass", material, rotation=(math.pi / 2, 0, 0),
                              damage_group=body, major_segments=12))
    for side in (-1, 1):
        x = side * 1.80
        parts.append(dq.beam(f"CORE side grab rail {side}", (x, -1.05, 3.10), (x, -1.05, 4.74),
                             0.08, "brass", material, body))
        for z in (3.10, 4.74):
            parts.append(dq.beam(f"CORE grab rail bracket {side} {z}", (x, -1.05, z), (x*.94, 0, z),
                                 0.08, "brass", material, body))
        for z in (3.10, 3.50, 3.90, 4.30, 4.70):
            parts.append(dq.cylinder(f"CORE rivet {side} {z}", 0.045, 0.06, (x, -1.10, z),
                                     "brass", material, vertices=8, rotation=(math.pi / 2, 0, 0),
                                     bevel=0, damage_group=body))

    for side, group in ((-1, left_leg), (1, right_leg)):
        x = side * 0.94
        parts.append(dq.cylinder(f"CORE hip {side}", 0.38, 0.56, (x, 0, 2.05),
                                 "brass", material, vertices=12, rotation=(math.pi / 2, 0, 0),
                                 bevel=0, damage_group=group))
        parts.append(dq.beam(f"CORE leg {side}", (x, 0, 1.94), (x, -0.06, 0.72),
                             0.46, "iron", material, group))
        # A broad flat sole and armored dome replace the rounded slipper shape.
        foot_rings=[]
        for z,rx,ry in ((-.05,.68,.80),(.09,.70,.82),(.31,.66,.76),(.58,.41,.51),(.66,.17,.24)):
            foot_rings.append([(x+rx*math.cos(a),-.28+ry*math.sin(a),z)
                               for a in (j*math.tau/16 for j in range(16))])
        parts.append(kit.loft(f"CORE armored foot {side}",foot_rings,"plate",material,
                              damage_group=group,smooth=True))
        parts.append(dq.box(f"CORE dark foot sole {side}",(1.32,1.51,.10),(x,-.28,0),
                            "soot",material,.04,damage_group=group))
        parts.append(dq.cylinder(f"CORE foot teal cap {side}", 0.18, 0.12,
                                 (x, -0.92, 0.42), "teal", material, vertices=10,
                                 rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))

    shoulder = Vector((1.78, 0.0, 4.32))
    elbow = Vector((2.58, -0.18, 3.58))
    hand = Vector((2.86, -0.44, 2.42))
    parts.append(dq.cylinder("CORE broom shoulder", 0.42, 0.48, tuple(shoulder), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=broom))
    dq.mark_all(parts[-1], "BroomShoulderPivot")
    parts.append(dq.beam("CORE broom upper arm", tuple(shoulder), tuple(elbow), 0.30,
                         "plate", material, broom))
    parts.append(dq.cylinder("CORE broom elbow", 0.28, 0.38, tuple(elbow), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=broom))
    parts.append(dq.beam("CORE broom forearm", tuple(elbow), tuple(hand), 0.25,
                         "iron", material, broom))
    parts.append(dq.beam("CORE broom handle", tuple(hand), (3.20, -0.60, 0.72),
                         0.12, "deck", material, broom))
    for index, x in enumerate(np.linspace(2.74, 3.60, 9)):
        parts.append(dq.beam(f"CORE broom bristle {index}", (float(x), -0.62, 0.72),
                             (float(x) + (x - 3.16) * 0.18, -0.66, 0.18),
                             0.10, "sail", material, broom))

    parts.append(dq.cylinder("CORE crown mast", 0.10, 0.84, (0, 0, 5.68),
                             "brass", material, vertices=10, damage_group=body))
    parts.append(dq.ico_sphere("CORE crown hub", 0.16, (0, 0, 6.14), "brass", material, body))
    for ray in range(8):
        angle = ray * math.tau / 8
        start = Vector((math.cos(angle) * 0.12, 0, 6.14 + math.sin(angle) * 0.12))
        end = Vector((math.cos(angle) * 0.58, 0, 6.14 + math.sin(angle) * 0.58))
        parts.append(dq.beam(f"CORE starburst ray {ray}", tuple(start), tuple(end),
                             0.055, "brass", material, body))
        parts.append(dq.ico_sphere(f"CORE starburst pip {ray}", 0.09, tuple(end),
                                   "brass", material, body))

    # Act 3 chair is production geometry carried by CORE. It is collapsed into
    # the floor in the basis and expands only under Damage_ChairPose.
    parts.append(dq.box("Chair debris seat", (4.18, 3.36, 0.32), (0, 1.02, 1.12),
                        "deck", material, 0.07, damage_group=chair))
    parts.append(dq.box("Chair debris back", (4.12, 0.34, 3.34), (0, 2.54, 2.46),
                        "plate", material, 0.07, rotation=(math.radians(-8), 0, 0), damage_group=chair))
    dq.mark_all(parts[-1], "ChairBackPanel")
    for side in (-1, 1):
        x = side * 1.82
        parts.append(dq.beam(f"Chair rear leg {side}", (x, 2.30, 1.08), (x, 2.48, -0.025),
                             0.20, "iron", material, chair))
        parts.append(dq.beam(f"Chair front leg {side}", (x, -0.46, 1.08), (x, -0.62, -0.025),
                             0.20, "iron", material, chair))
        parts.append(dq.beam(f"Chair arm {side}", (x, -0.30, 1.78), (x, 2.18, 1.78),
                             0.18, "brass", material, chair))
        parts.append(dq.ico_sphere(f"Chair arm finial {side}", 0.16, (x, -0.34, 1.80),
                                   "brass", material, chair))
    parts.append(dq.beam("Chair back brace one", (-1.82, 2.64, 1.28), (1.82, 2.64, 3.62),
                         0.14, "brass", material, chair))
    parts.append(dq.beam("Chair back brace two", (1.82, 2.64, 1.28), (-1.82, 2.64, 3.62),
                         0.14, "brass", material, chair))
    return parts


def group_bounds(obj: bpy.types.Object, group_name: str) -> tuple[Vector, Vector]:
    points = [obj.data.vertices[index].co for index in dq.group_vertex_indices(obj, group_name)]
    assert points, f"missing group {obj.name}:{group_name}"
    return (
        Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


def group_center(obj: bpy.types.Object, group_name: str) -> Vector:
    minimum, maximum = group_bounds(obj, group_name)
    return (minimum + maximum) * 0.5


def rotate_x(co: Vector, pivot: Vector, angle: float) -> None:
    local = co - pivot
    y = local.y * math.cos(angle) - local.z * math.sin(angle)
    z = local.y * math.sin(angle) + local.z * math.cos(angle)
    co.y = pivot.y + y
    co.z = pivot.z + z


def add_damage_shapes(vac: bpy.types.Object, rack: bpy.types.Object, core: bpy.types.Object) -> None:
    vac.shape_key_add(name="Basis")
    dropped = vac.shape_key_add(name="Damage_DroppedVac")
    pivot = group_center(vac, "VacUpperArm")
    for index in dq.group_vertex_indices(vac, "VacUpperArm"):
        co = dropped.data[index].co
        dq.rotate_y(co, pivot, math.radians(-28))
        co += Vector((-0.18, -0.18, -0.46))
    for index in dq.group_vertex_indices(vac, "VacHose"):
        co = dropped.data[index].co
        co += Vector((-0.18, -0.20, -0.55 * min(1, max(0, (co.z-.2)/1.2)) - max(0.0, co.z - 0.8) * 0.12))
    for index in dq.group_vertex_indices(vac, "VacHead"):
        dropped.data[index].co += Vector((-0.68, -0.88, 0.02))
    for shard, move in enumerate((Vector((-1.1, -1.0, -0.10)), Vector((-0.2, -1.35, -0.18)), Vector((0.45, -0.82, -0.12)))):
        for index in dq.group_vertex_indices(vac, f"VacShard{shard}"):
            dropped.data[index].co += move
        indices = dq.group_vertex_indices(vac, f"VacShard{shard}")
        floor_delta = 0.02 - min(dropped.data[index].co.z for index in indices)
        for index in indices:
            dropped.data[index].co.z += floor_delta

    rack.shape_key_add(name="Basis")
    spent = rack.shape_key_add(name="Damage_SpentRack")
    minimum, maximum = group_bounds(rack, "RackUpper")
    pivot = Vector((minimum.x, (minimum.y + maximum.y) * 0.5, minimum.z))
    for index in dq.group_vertex_indices(rack, "RackUpper"):
        co = spent.data[index].co
        rotate_x(co, pivot, math.radians(18))
        dq.rotate_y(co, pivot, math.radians(-14))
        co += Vector((2.18, 0.78, -4.96))
    for shard, move in enumerate((Vector((-1.35, -1.15, -5.57)), Vector((0.15, -1.55, -5.52)), Vector((1.18, -0.82, -5.52)))):
        for index in dq.group_vertex_indices(rack, f"RackShard{shard}"):
            spent.data[index].co += move
        indices = dq.group_vertex_indices(rack, f"RackShard{shard}")
        floor_delta = 0.02 - min(spent.data[index].co.z for index in indices)
        for index in indices:
            spent.data[index].co.z += floor_delta

    core.shape_key_add(name="Basis")
    chair_pose = core.shape_key_add(name="Damage_ChairPose")
    body_pivot = group_center(core, "ChairBody")
    for index in dq.group_vertex_indices(core, "ChairBody"):
        co = chair_pose.data[index].co
        rotate_x(co, body_pivot, math.radians(-12))
        co += Vector((0.0, 0.72, -1.24))
    for index in dq.group_vertex_indices(core, "CoreShutdownShutter"):
        co = chair_pose.data[index].co
        co.y -= 1.888
        rotate_x(co, body_pivot, math.radians(-12))
        co += Vector((0.0, 0.72, -1.24))
    for group_name, x_move in (("ChairLeftLeg", -0.22), ("ChairRightLeg", 0.22)):
        pivot = group_center(core, group_name)
        for index in dq.group_vertex_indices(core, group_name):
            co = chair_pose.data[index].co
            rotate_x(co, pivot, math.radians(-42))
            co += Vector((x_move, -0.90, 0.21))
    broom_pivot = group_center(core, "BroomShoulderPivot")
    for index in dq.group_vertex_indices(core, "ChairBroom"):
        co = chair_pose.data[index].co
        dq.rotate_y(co, broom_pivot, math.radians(-30))
        rotate_x(co, body_pivot, math.radians(-12))
        co += Vector((0.0, 0.72, -1.24))

    # Keep the target's full chair coordinates, but make the intact basis a
    # near-zero bundle under the body. At weight 1 the debris chair builds.
    anchor = Vector((0.0, 0.55, 0.12))
    basis = core.data.shape_keys.key_blocks["Basis"]
    for index in dq.group_vertex_indices(core, "ChairDebris"):
        basis.data[index].co = anchor + (basis.data[index].co - anchor) * 0.006

    for obj in (vac, rack, core):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0
        obj.data.update()


def recenter_shape_keyed_basis(objects: tuple[bpy.types.Object, ...]) -> None:
    """Re-center the basis after the hidden chair bundle changes its bounds.

    Apply the same translation to every key block so the authored damage
    deltas remain unchanged while the exported intact basis stays base-center.
    """
    points = [
        point.co
        for obj in objects
        for point in obj.data.shape_keys.key_blocks["Basis"].data
    ]
    minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    offset = Vector(((minimum.x + maximum.x) * 0.5, (minimum.y + maximum.y) * 0.5, minimum.z))
    for obj in objects:
        keys = obj.data.shape_keys
        assert keys is not None
        for key in keys.key_blocks:
            for point in key.data:
                point.co -= offset
        obj.data.update()


def shape_basis_bounds(objects: tuple[bpy.types.Object, ...]) -> tuple[Vector, Vector]:
    points = [
        point.co
        for obj in objects
        for point in obj.data.shape_keys.key_blocks["Basis"].data
    ]
    return (
        Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    dq.reset_scene()
    atlas = create_atomic_atlas()
    material = dq.create_material(atlas)
    material.name = "Homemaker9000PaintedMaterial"
    groups={"vac":build_vac(material),"rack":build_rack(material),"core":build_core(material)}
    for parts in groups.values():
        for part in parts:
            if any(word in part.name.lower() for word in ("rim", "cage", "bristle", "ray", "rail")):
                for modifier in list(part.modifiers):
                    if modifier.type=="BEVEL":part.modifiers.remove(modifier)
    vac,rack,core=(dq.join_component(name,groups[name],material) for name in ("vac","rack","core"))
    objects = (vac, rack, core)
    dq.MODEL_LENGTH = MODEL_LENGTH
    dq.normalize_base_center(objects)
    add_damage_shapes(*objects)
    recenter_shape_keyed_basis(objects)


    triangles = dq.triangle_count(objects)
    minimum, maximum = shape_basis_bounds(objects)
    assert triangles <= 12_000
    assert abs(maximum.x - minimum.x - MODEL_LENGTH) < 0.01
    assert abs(minimum.z) < 0.001
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    dq.BLEND, dq.GLB = BLEND, GLB
    dq.export(objects)
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB), "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlate": {str(REFERENCE.relative_to(ROOT)): hashlib.sha256(REFERENCE.read_bytes()).hexdigest()},
        "components": [obj.name for obj in objects],
        "damageMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "triangles": triangles,
        "boundsBlender": {"min": [round(v, 6) for v in minimum], "max": [round(v, 6) for v in maximum]},
    }, indent=2))


if __name__ == "__main__":
    main()
