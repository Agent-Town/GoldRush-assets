from pathlib import Path
import hashlib
import importlib.util
import json
import math
import subprocess
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TEMP = Path("/tmp/gold-rush-wave14-e7")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h = load_module("wave14_e7_build_helpers", HERE / "build_wave13_e7_pilot.py")

PLAYBOOK_REFERENCE_SHA = "927edd372a0c42e127339d7bae41d78a253abec83b0af371ff3ba1b0f54461c1"
SIGNAL_TURRET_REFERENCE_SHA = "dbaf7349deb547de737fbf41d0f882687f982092063281d87c2c31340c4f7975"
E6_WIDE_REF = "origin/sol/mesa-town-e6-wide"
SOURCES = {
    "beam_relay": {
        "blend": "assets/pilots/run3d/turret.e6.blend",
        "blend_sha": "2459bdc55bdcf063d3d7282d526374a8f0832341277ce391fe321075928e18c5",
        "glb": "assets/pilots/run3d/turret.e6.glb",
        "glb_sha": "44d17919c60e294bbe977736a01ce93bf1a9f72a8ed85ca4b167a305b5cf1bbe",
        "object": "SunlineMountE6",
        "output_object": "BeamRelayTurretE7",
    },
    "signal_works": {
        "blend": "assets/pilots/schoolhouse-3d/schoolhouse.e6.blend",
        "blend_sha": "7be45aeb005544b861297aced589c7be17420ca5096067fb8e3b5aadbbf92825",
        "glb": "assets/pilots/schoolhouse-3d/schoolhouse.e6.glb",
        "glb_sha": "f3de54fb073729e1b251f0809b9ea65b2f869afd9c731430454636c03351bfb3",
        "object": "IsotopeInstituteE6",
        "output_object": "SignalWorksE7",
    },
    "tape_post": {
        "blend": "assets/pilots/catalog-warehouse-3d/catalog-warehouse.blend",
        "blend_sha": "596b964914b73b8e5c4457b62cd1cff6dba038c52c6c86ef23afe48f5a9e05e2",
        "glb": "assets/pilots/catalog-warehouse-3d/catalog-warehouse.glb",
        "glb_sha": "f72109125d3c036a3ac8a06004fa212f02539c762076dd9959c30cd578fcce24",
        "object": "CatalogWarehouseE6",
        "output_object": "TapePostE7",
    },
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_references():
    assert sha256(ROOT / "assets/raw/plate-e7-bld-playbook-library.png") == PLAYBOOK_REFERENCE_SHA
    assert sha256(ROOT / "assets/raw/bld-signal-turret.png") == SIGNAL_TURRET_REFERENCE_SHA


def configure_warm_signal_palette():
    # E7 keeps walnut warmth without dropping below the pastel E6 neighborhood.
    h.PALETTE.update({
        "shadow": (0.080, 0.060, 0.042),
        "walnut": (0.450, 0.280, 0.150),
        "dark": (0.180, 0.130, 0.080),
        "roof": (0.400, 0.240, 0.130),
        "warm": (0.610, 0.335, 0.125),
    })


def add_tape_reel(parts, prefix, center, radius, material, region="tape"):
    x, y, z = center
    parts.extend((
        h.cylinder(f"{prefix} reel", radius, 0.14, center, material, region, 14,
                   rotation=(math.pi / 2, 0, 0)),
        h.cylinder(f"{prefix} hub", radius * 0.24, 0.18, (x, y - 0.02, z), material,
                   "teal", 10, rotation=(math.pi / 2, 0, 0)),
    ))
    for index in range(6):
        angle = index * math.tau / 6
        parts.append(h.cylinder(
            f"{prefix} punch {index + 1}", radius * 0.065, 0.18,
            (x + math.cos(angle) * radius * 0.55, y - 0.03,
             z + math.sin(angle) * radius * 0.55), material, "shadow", 6,
            rotation=(math.pi / 2, 0, 0),
        ))


def build_playbook_library():
    h.reset_scene()
    directory = ROOT / "assets/pilots/playbook-library-3d"
    material = h.make_material(
        "PlaybookLibraryE7PaintedMaterial",
        h.make_atlas("PlaybookLibraryE7PaintedAtlas", 2700),
    )
    parts = [
        h.box("Playbook Library grounded stone foot", (6.10, 4.46, 0.22), (0, 0, 0.11),
              material, "shadow", 0.024),
        h.box("Playbook Library walnut hall", (5.76, 4.10, 3.12), (0, 0.08, 1.76),
              material, "walnut", 0.030),
        h.barrel_roof("Playbook Library vaulted roof", 5.88, 4.18, 3.24, 1.24,
                      material, "roof", 16),
        h.box("Playbook Library public catalog front", (5.94, 0.64, 1.82),
              (0, -2.12, 1.40), material, "cream", 0.024),
        h.box("Playbook Library teal catalog sill", (6.00, 0.10, 0.22),
              (0, -2.48, 0.96), material, "teal", 0.008),
        h.box("Playbook Library roof reader bed", (3.84, 1.36, 0.24),
              (0, 0.18, 4.34), material, "brass", 0.016),
        h.box("Playbook Library rear archive frame", (4.72, 0.18, 1.70),
              (0, 2.17, 1.76), material, "dark", 0.012),
    ]
    # Card catalog frontage: pictogram-only drawers and teal index pips.
    for row, z in enumerate((1.02, 1.58, 2.14), 1):
        for column, x in enumerate((-2.28, -1.52, -0.76, 0.0, 0.76, 1.52, 2.28), 1):
            parts.extend((
                h.box(f"Playbook Library catalog drawer {row}.{column}", (0.58, 0.10, 0.38),
                      (x, -2.48, z), material, "walnut", 0.006),
                h.box(f"Playbook Library catalog index {row}.{column}", (0.20, 0.04, 0.09),
                      (x, -2.55, z), material, "glass" if (row + column) % 3 == 0 else "brass", 0.003),
            ))
    # Large roof reels and a reader clock make the program-library silhouette legible.
    add_tape_reel(parts, "Playbook Library west roof", (-1.42, -0.18, 5.02), 0.62, material)
    add_tape_reel(parts, "Playbook Library east roof", (1.42, -0.18, 5.02), 0.62, material)
    parts.extend((
        h.cylinder("Playbook Library reader clock", 0.64, 0.18, (0, -0.26, 5.82),
                   material, "brass", 18, rotation=(math.pi / 2, 0, 0)),
        h.cylinder("Playbook Library reader clock face", 0.50, 0.06, (0, -0.38, 5.82),
                   material, "glass", 18, rotation=(math.pi / 2, 0, 0)),
        h.beam("Playbook Library reader clock hand", (0, -0.43, 5.82),
               (0.30, -0.43, 6.02), 0.035, material, "dark", 6),
        h.cylinder("Playbook Library signal finial mast", 0.07, 1.18,
                   (0, 0.16, 6.58), material, "dark", 8),
        h.sphere("Playbook Library signal finial", 0.13, (0, 0.16, 7.22),
                 material, "signal", 8, 4),
    ))
    h.signal_arcs(parts, "Playbook Library broadcast", (0, -0.46, 6.24),
                  (0.86, 1.20, 1.56), material, segments=6)
    # Tube lamps and supported tape runs wrap the flanks and archive rear.
    for side, x in (("west", -2.92), ("east", 2.92)):
        for index, z in enumerate((1.10, 1.78, 2.46), 1):
            parts.extend((
                h.cylinder(f"Playbook Library {side} tube socket {index}", 0.15, 0.16,
                           (x, -0.52 + index * 0.46, z), material, "brass", 10,
                           rotation=(0, math.pi / 2, 0)),
                h.cylinder(f"Playbook Library {side} honey tube {index}", 0.095, 0.46,
                           (x, -0.52 + index * 0.46, z + 0.24), material,
                           "honey" if index % 2 else "glass", 10),
            ))
    for index, x in enumerate((-2.04, -1.02, 0.0, 1.02, 2.04), 1):
        parts.extend((
            h.box(f"Playbook Library rear archive door {index}", (0.72, 0.08, 1.18),
                  (x, 2.30, 1.62), material, "walnut", 0.008),
            h.cylinder(f"Playbook Library rear tape port {index}", 0.13, 0.08,
                       (x, 2.36, 2.10), material, "glass" if index % 2 else "honey", 10,
                       rotation=(math.pi / 2, 0, 0)),
        ))
    h.apply_and_uv(parts)
    model = h.join_parts(parts, "PlaybookLibraryE7")
    model["epoch_variant"] = "E7 Signal Mesa"
    model["identity"] = (
        "Walnut public program library with drawer-wall facade, paired punch-tape reels, "
        "reader clock, tube flanks, signal crown, and complete rear archive"
    )
    model["reference_sha256"] = PLAYBOOK_REFERENCE_SHA
    return h.export_model(model, directory / "playbook-library.blend", directory / "playbook-library.glb")


def add_drone(parts, prefix, center, material, scale=1.0):
    x, y, z = center
    parts.extend((
        h.sphere(f"{prefix} body", 0.22 * scale, center, material, "honey", 10, 5),
        h.cylinder(f"{prefix} eye", 0.075 * scale, 0.10 * scale,
                   (x, y - 0.21 * scale, z), material, "glass", 8,
                   rotation=(math.pi / 2, 0, 0)),
        h.beam(f"{prefix} port arm", (x - 0.16 * scale, y, z),
               (x - 0.42 * scale, y, z), 0.035 * scale, material, "brass", 6),
        h.beam(f"{prefix} starboard arm", (x + 0.16 * scale, y, z),
               (x + 0.42 * scale, y, z), 0.035 * scale, material, "brass", 6),
        h.torus(f"{prefix} port rotor", 0.21 * scale, 0.025 * scale,
                (x - 0.46 * scale, y, z), material, "teal",
                rotation=(0, math.pi / 2, 0), major_segments=12, minor_segments=4),
        h.torus(f"{prefix} starboard rotor", 0.21 * scale, 0.025 * scale,
                (x + 0.46 * scale, y, z), material, "teal",
                rotation=(0, math.pi / 2, 0), major_segments=12, minor_segments=4),
    ))


def build_drone_coop():
    h.reset_scene()
    directory = ROOT / "assets/pilots/drone-coop-3d"
    material = h.make_material("DroneCoopE7PaintedMaterial", h.make_atlas("DroneCoopE7PaintedAtlas", 3700))
    parts = [
        h.cylinder("Drone Coop grounded round foot", 2.24, 0.22, (0, 0, 0.11), material, "shadow", 18),
        h.box("Drone Coop keeper hut", (3.82, 3.52, 1.82), (0, 0.06, 1.02), material, "walnut", 0.028),
        h.barrel_roof("Drone Coop keeper roof", 3.94, 3.62, 1.86, 0.72, material, "roof", 14),
        h.box("Drone Coop tower trunk", (2.06, 2.06, 3.52), (0, 0.10, 3.46), material, "cream", 0.022),
        h.cylinder("Drone Coop crown floor", 1.52, 0.24, (0, 0.10, 5.34), material, "brass", 16),
        h.cylinder("Drone Coop domed cap", 1.32, 0.26, (0, 0.10, 6.26), material, "roof", 16),
        h.sphere("Drone Coop cap dome", 1.18, (0, 0.10, 6.22), material, "roof", 16, 8),
        h.cylinder("Drone Coop signal mast", 0.07, 0.92, (0, 0.10, 7.12), material, "dark", 8),
        h.sphere("Drone Coop signal finial", 0.13, (0, 0.10, 7.62), material, "signal", 8, 4),
    ]
    # Twelve teal nesting cells make the dovecote unmistakable from every side.
    cell_index = 0
    for level, z in enumerate((3.00, 3.78, 4.56), 1):
        for face, (x, y, rotation) in enumerate((
            (0, -1.06, (math.pi / 2, 0, 0)),
            (1.06, 0, (0, math.pi / 2, 0)),
            (0, 1.16, (math.pi / 2, 0, 0)),
            (-1.06, 0, (0, math.pi / 2, 0)),
        ), 1):
            cell_index += 1
            parts.extend((
                h.cylinder(f"Drone Coop nesting cell {cell_index}", 0.25, 0.14,
                           (x, y, z), material, "glass" if (level + face) % 2 else "honey", 12,
                           rotation=rotation),
                h.box(f"Drone Coop nesting perch {cell_index}", (0.52, 0.34, 0.08),
                      (x, y - 0.12 if y < 0 else y + 0.12, z - 0.26), material, "brass", 0.006),
            ))
    # Playful multiplied companion flock, parked on structural side arms.
    for index, (x, y, z) in enumerate((
        (-1.72, -0.78, 3.36), (1.72, -0.20, 4.06), (-1.56, 0.92, 4.82),
        (1.42, 0.92, 5.42), (0.00, -1.56, 5.48),
    ), 1):
        parts.append(h.beam(
            f"Drone Coop perch arm {index}",
            (math.copysign(0.92, x) if x else 0, y * 0.54, z - 0.12),
            (x, y, z - 0.12), 0.055, material, "dark", 7,
        ))
        add_drone(parts, f"Drone Coop parked drone {index}", (x, y, z), material, 0.82)
    h.signal_arcs(parts, "Drone Coop flock signal", (0, -0.42, 6.90),
                  (0.62, 0.94, 1.26), material, segments=6)
    # Keeper doors and rear service battery keep the lower shell finished.
    for side, x in (("west", -1.96), ("east", 1.96)):
        parts.extend((
            h.box(f"Drone Coop {side} keeper door", (0.08, 0.82, 1.14),
                  (x, 0.12, 1.06), material, "dark", 0.008),
            h.cylinder(f"Drone Coop {side} keeper dial", 0.13, 0.08,
                       (x, -0.42, 1.36), material, "glass", 10,
                       rotation=(0, math.pi / 2, 0)),
        ))
    for index, x in enumerate((-1.18, -0.40, 0.40, 1.18), 1):
        parts.append(h.box(f"Drone Coop rear battery hatch {index}", (0.60, 0.08, 0.64),
                           (x, 1.86, 1.10), material, "dark", 0.008))
    h.apply_and_uv(parts)
    model = h.join_parts(parts, "DroneCoopE7")
    model["epoch_variant"] = "E7 Signal Mesa"
    model["identity"] = (
        "Warm civic dovecote for multiplied hover drones, with twelve nesting cells, five visible "
        "parked companions, keeper hut, dome, and flock-signal crown"
    )
    return h.export_model(model, directory / "drone-coop.blend", directory / "drone-coop.glb")


def build_signal_refinery():
    h.reset_scene()
    directory = ROOT / "assets/pilots/signal-refinery-3d"
    material = h.make_material(
        "SignalRefineryE7PaintedMaterial", h.make_atlas("SignalRefineryE7PaintedAtlas", 4700),
    )
    parts = [
        h.box("Signal Refinery grounded service slab", (6.18, 4.62, 0.22), (0, 0, 0.11),
              material, "shadow", 0.024),
        h.box("Signal Refinery walnut plant", (5.70, 4.12, 2.42), (0, 0.04, 1.42),
              material, "walnut", 0.028),
        h.barrel_roof("Signal Refinery band roof", 5.82, 4.20, 2.56, 0.92,
                      material, "roof", 16),
        h.box("Signal Refinery front spectrum bench", (5.90, 0.70, 1.10),
              (0, -2.12, 0.84), material, "cream", 0.020),
        h.box("Signal Refinery teal frequency rail", (5.96, 0.10, 0.20),
              (0, -2.51, 1.20), material, "teal", 0.008),
        h.box("Signal Refinery rear condenser gallery", (4.88, 0.26, 1.40),
              (0, 2.18, 1.52), material, "dark", 0.014),
    ]
    # Three spectrum columns visibly turn signal into a civic resource.
    for index, x in enumerate((-1.62, 0.0, 1.62), 1):
        height = 1.48 + index * 0.16
        parts.extend((
            h.cylinder(f"Signal Refinery spectrum tank {index}", 0.52, height,
                       (x, 0.12, 3.40 + index * 0.10), material,
                       "glass" if index != 2 else "honey", 16),
            h.cylinder(f"Signal Refinery spectrum tank foot {index}", 0.62, 0.20,
                       (x, 0.12, 2.62), material, "brass", 16),
            h.cylinder(f"Signal Refinery spectrum tank crown {index}", 0.62, 0.20,
                       (x, 0.12, 4.18 + index * 0.16), material, "brass", 16),
            h.sphere(f"Signal Refinery spectrum finial {index}", 0.12,
                     (x, 0.12, 4.46 + index * 0.16), material, "signal", 8, 4),
        ))
        for rib in range(4):
            angle = rib * math.tau / 4
            parts.append(h.beam(
                f"Signal Refinery tank cage {index}.{rib + 1}",
                (x + math.cos(angle) * 0.54, 0.12 + math.sin(angle) * 0.54, 2.78),
                (x + math.cos(angle) * 0.54, 0.12 + math.sin(angle) * 0.54,
                 4.14 + index * 0.14), 0.030, material, "dark", 6,
            ))
    # Public frequency dials, wave combs, and roof rings carry the gameplay read.
    for index, x in enumerate((-2.18, -1.10, 0.0, 1.10, 2.18), 1):
        parts.extend((
            h.cylinder(f"Signal Refinery public frequency dial {index}", 0.25, 0.09,
                       (x, -2.52, 1.56), material, "glass" if index % 2 else "honey", 14,
                       rotation=(math.pi / 2, 0, 0)),
            h.beam(f"Signal Refinery frequency needle {index}", (x, -2.58, 1.56),
                   (x + 0.12, -2.58, 1.70), 0.020, material, "dark", 5),
        ))
    for index, radius in enumerate((0.70, 1.02, 1.34), 1):
        parts.append(h.torus(f"Signal Refinery roof tuning ring {index}", radius, 0.045,
                             (0, 0.10, 5.22), material, "teal" if index == 3 else "brass",
                             rotation=(math.pi / 2, 0, 0), major_segments=18, minor_segments=5))
    parts.extend((
        h.beam("Signal Refinery tuning mast", (0, 0.10, 4.34), (0, 0.10, 6.28),
               0.075, material, "dark", 8),
        h.sphere("Signal Refinery tuning eye", 0.18, (0, -0.02, 5.22),
                 material, "signal", 10, 5),
    ))
    h.signal_arcs(parts, "Signal Refinery outgoing band", (0, -0.16, 5.72),
                  (1.62, 2.00), material, segments=7)
    for side, x in (("west", -2.90), ("east", 2.90)):
        for index, z in enumerate((1.10, 1.76, 2.42), 1):
            parts.append(h.cylinder(
                f"Signal Refinery {side} spectrum port {index}", 0.15, 0.10,
                (x, 0.62 - index * 0.46, z), material, "glass" if index != 2 else "honey", 10,
                rotation=(0, math.pi / 2, 0),
            ))
    for index, x in enumerate((-1.86, -0.62, 0.62, 1.86), 1):
        parts.extend((
            h.box(f"Signal Refinery rear condenser hatch {index}", (0.78, 0.08, 0.82),
                  (x, 2.34, 1.42), material, "walnut", 0.008),
            h.beam(f"Signal Refinery rear condenser pipe {index}", (x, 2.39, 1.03),
                   (x + (0.18 if index % 2 else -0.18), 2.39, 0.66),
                   0.040, material, "teal", 6),
        ))
    h.apply_and_uv(parts)
    model = h.join_parts(parts, "SignalRefineryE7")
    model["epoch_variant"] = "E7 Signal Mesa"
    model["identity"] = (
        "Working spectrum plant with three caged signal columns, public frequency dials, "
        "concentric tuning crown, supported outgoing bands, and complete condenser gallery"
    )
    return h.export_model(model, directory / "signal-refinery.blend", directory / "signal-refinery.glb")


def extract_source(key):
    spec = SOURCES[key]
    TEMP.mkdir(parents=True, exist_ok=True)
    paths = {}
    for kind in ("blend", "glb"):
        target = TEMP / f"{key}-source.{kind}"
        with target.open("wb") as handle:
            subprocess.run(["git", "show", f"{E6_WIDE_REF}:{spec[kind]}"],
                           cwd=ROOT, stdout=handle, check=True)
        assert sha256(target) == spec[f"{kind}_sha"]
        paths[kind] = target
    return spec, paths


def join_additions(model, parts, output_name):
    for part in parts:
        part.modifiers.clear()
    h.apply_and_uv(parts)
    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.object.join()
    model.name = output_name
    model.data.name = f"{output_name}Mesh"
    for polygon in model.data.polygons:
        polygon.material_index = 0
    while len(model.data.materials) > 1:
        model.data.materials.pop(index=len(model.data.materials) - 1)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return model


def build_beam_relay():
    spec, paths = extract_source("beam_relay")
    bpy.ops.wm.open_mainfile(filepath=str(paths["blend"]))
    model = bpy.data.objects[spec["object"]]
    material = model.data.materials[0]
    parts = [
        h.cylinder("Beam Relay receiver neck", 0.13, 0.76, (0, 0, 2.24),
                   material, "e6_dark", 8),
        h.torus("Beam Relay outer routing ring", 0.60, 0.040, (0, -0.04, 2.68),
                material, "e6_teal", rotation=(math.pi / 2, 0, 0),
                major_segments=16, minor_segments=5),
        h.torus("Beam Relay inner routing ring", 0.39, 0.032, (0, -0.05, 2.68),
                material, "e6_chrome", rotation=(math.pi / 2, 0, 0),
                major_segments=14, minor_segments=4),
        h.sphere("Beam Relay routing eye", 0.16, (0, -0.18, 2.68),
                 material, "e6_glass", 10, 5),
    ]
    for side, x in (("port", -0.50), ("starboard", 0.50)):
        parts.extend((
            h.cylinder(f"Beam Relay {side} cell", 0.13, 0.46, (x, 0.02, 2.24),
                       material, "e6_amber" if x < 0 else "e6_glass", 10),
            h.beam(f"Beam Relay {side} cell arm", (0, 0.02, 2.24), (x, 0.02, 2.24),
                   0.040, material, "e6_chrome", 6),
        ))
    h.signal_arcs(parts, "Beam Relay outgoing hop", (0, -0.24, 2.76),
                  (0.48, 0.66), material, "e6_teal", segments=5)
    model = join_additions(model, parts, spec["output_object"])
    model["epoch_variant"] = "E7 Signal Mesa"
    model["identity_transform"] = (
        "Complete E6 Sunline Mount retained; paired cells, routing rings, and outgoing signal arcs "
        "make the LOS damage relay legible"
    )
    model["source_e6_glb_sha256"] = spec["glb_sha"]
    directory = ROOT / "assets/pilots/run3d"
    return h.export_model(model, directory / "turret.e7.blend", directory / "turret.e7.glb")


def build_signal_works():
    spec, paths = extract_source("signal_works")
    bpy.ops.wm.open_mainfile(filepath=str(paths["blend"]))
    model = bpy.data.objects[spec["object"]]
    material = model.data.materials[0]
    parts = []
    # Tube-bank crown and dish live inside the institute's exact XZ footprint.
    for index, x in enumerate((-1.18, -0.70, -0.22, 0.26, 0.74, 1.22), 1):
        parts.extend((
            h.cylinder(f"Signal Works tube socket {index}", 0.13, 0.12,
                       (x, 0.42, 5.36), material, "e6_chrome", 10),
            h.cylinder(f"Signal Works honey tube {index}", 0.085, 0.52,
                       (x, 0.42, 5.68 + (0.08 if index % 2 else 0)), material,
                       "e6_amber" if index % 2 else "e6_glass", 10),
        ))
    parts.extend((
        h.beam("Signal Works dish mast", (-1.34, 0.42, 5.34), (-1.34, 0.42, 6.58),
               0.065, material, "e6_dark", 7),
        h.parabolic_dish("Signal Works relay dish", (-1.34, 0.22, 6.78), 0.56, 0.18,
                         material, "e6_chrome", 3, 12),
        h.sphere("Signal Works dish focus", 0.085, (-1.34, -0.05, 6.78),
                 material, "e6_glass", 8, 4),
    ))
    h.signal_arcs(parts, "Signal Works research broadcast", (0.34, -0.10, 6.38),
                  (0.72, 1.00, 1.28), material, "e6_teal", segments=6)
    model = join_additions(model, parts, spec["output_object"])
    model["epoch_variant"] = "E7 Signal Mesa"
    model["identity_transform"] = (
        "Complete E6 Isotope Institute retained; roof tube bank, relay dish, and broadcast crown "
        "turn its calculation work into the Signal Works"
    )
    model["source_e6_glb_sha256"] = spec["glb_sha"]
    directory = ROOT / "assets/pilots/schoolhouse-3d"
    return h.export_model(model, directory / "schoolhouse.e7.blend", directory / "schoolhouse.e7.glb")


def build_tape_post():
    spec, paths = extract_source("tape_post")
    bpy.ops.wm.open_mainfile(filepath=str(paths["blend"]))
    model = bpy.data.objects[spec["object"]]
    material = model.data.materials[0]
    parts = [
        h.box("Tape Post parcel reader bridge", (3.42, 0.52, 0.26),
              (0, -1.58, 3.84), material, "e6_chrome", 0.012),
        h.beam("Tape Post courier mast", (1.74, 0.52, 3.56), (1.74, 0.52, 5.74),
               0.070, material, "e6_dark", 8),
        h.cylinder("Tape Post courier tube", 0.22, 1.62, (1.74, 0.52, 4.52),
                   material, "e6_glass", 12),
        h.cylinder("Tape Post courier tube crown", 0.28, 0.18, (1.74, 0.52, 5.38),
                   material, "e6_chrome", 12),
        h.sphere("Tape Post courier signal", 0.12, (1.74, 0.52, 5.68),
                 material, "e6_amber", 8, 4),
    ]
    # Large paired reels turn the old parcel depot into a punch-tape post.
    for side, x in (("west", -1.22), ("east", 0.10)):
        parts.extend((
            h.cylinder(f"Tape Post {side} reel", 0.50, 0.14, (x, -1.72, 4.46),
                       material, "e6_cream", 14, rotation=(math.pi / 2, 0, 0)),
            h.cylinder(f"Tape Post {side} reel hub", 0.13, 0.18, (x, -1.75, 4.46),
                       material, "e6_teal", 10, rotation=(math.pi / 2, 0, 0)),
        ))
    previous = (-1.22, -1.80, 4.46)
    for step in range(1, 9):
        fraction = step / 8
        point = (-1.22 + 1.32 * fraction, -1.80,
                 4.46 + math.sin(math.pi * fraction) * 0.62)
        parts.append(h.beam(f"Tape Post public tape loop {step}", previous, point,
                            0.050, material, "e6_cream", 5))
        previous = point
    h.signal_arcs(parts, "Tape Post dispatch signal", (1.74, 0.18, 5.38),
                  (0.52, 0.78, 1.04), material, "e6_teal", segments=5)
    model = join_additions(model, parts, spec["output_object"])
    model["epoch_variant"] = "E7 Signal Mesa"
    model["identity_transform"] = (
        "Complete E6 Catalog Warehouse parcel shell retained; paired tape reels, courier tube, "
        "reader bridge, and dispatch signal convert the clerk lineage into the Tape Post"
    )
    model["source_e6_glb_sha256"] = spec["glb_sha"]
    directory = ROOT / "assets/pilots/catalog-warehouse-3d"
    return h.export_model(model, directory / "catalog-warehouse.e7.blend",
                          directory / "catalog-warehouse.e7.glb")


def main():
    assert_references()
    configure_warm_signal_palette()
    result = {
        "playbook_library": build_playbook_library(),
        "drone_coop": build_drone_coop(),
        "signal_refinery": build_signal_refinery(),
        "beam_relay": build_beam_relay(),
        "signal_works": build_signal_works(),
        "tape_post": build_tape_post(),
        "sourceBase": "origin/main@3fe1e493fb11b6685f1ffc76b65dd81ebff8dd6b",
        "sourceE6Wide": "origin/sol/mesa-town-e6-wide@bcc9764bd320460c6de99e901a4e979694341030",
        "sourceE7Pilot": "origin/sol/mesa-town-e7-pilot@3947af4943f784a1e26d4ed1ae9b8aed47da2293",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
