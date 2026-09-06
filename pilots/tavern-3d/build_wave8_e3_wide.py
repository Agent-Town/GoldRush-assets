from pathlib import Path
import importlib.util
import json
import math
import sys

from mathutils import Vector


HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pilot = load_module("wave8_pilot_build", HERE / "build_wave8_e3_pilot.py")
claim = load_module(
    "claim_e2_build",
    HERE.parent / "claim-office-3d" / "build_claim_office_e2.py",
)
common = pilot.common


def standard_spec(directory, stem, object_name, output, blend_sha, glb_sha, common_key):
    source_uv = common.SPECS[common_key]["uv"]
    return {
        "directory": directory,
        "stem": stem,
        "source": f"{stem}.e2",
        "object": object_name,
        "output": output,
        "blend_sha": blend_sha,
        "glb_sha": glb_sha,
        "uv": {
            "dark": source_uv["iron"],
            "copper": source_uv["brass"],
            "teal": source_uv["teal"],
            "warm": source_uv["face"],
        },
    }


SPECS = {
    "tavern": pilot.SPECS["tavern"],
    "general_store": standard_spec(
        "general-store-3d", "general-store", "GeneralStoreE2", "GeneralStoreE3",
        "a0e3716c388c162cb3c8c4fa1493ae103ede62bb7d4786f73a4da106449b9cd1",
        "64e69511c5f894d6e9ce10c7d060d57a7ee667c76cac94bf194ac44ecdb2058e",
        "general_store",
    ),
    "claim_office": {
        "directory": "claim-office-3d", "stem": "claim-office", "source": "claim-office.e2",
        "object": "ClaimOfficeE2", "output": "ClaimOfficeE3",
        "blend_sha": "0c8a9c38530174794b6722dd4ed739f0dc6d6cd09c36205bd4e802ab14b2e1cd",
        "glb_sha": "715b721d8c3896c82bf8468d6d18fc30d8628c2d2c69720f85b6476f7f86d656",
        "uv": {
            "dark": claim.UV_IRON, "copper": claim.UV_BRASS,
            "teal": claim.UV_TEAL, "warm": claim.UV_STONE,
        },
    },
    "assay_office": standard_spec(
        "assay-office-3d", "assay-office", "AssayOfficeE2", "AssayOfficeE3",
        "89043ff16eca1f85e6d882fbed873c2fe959e192dfdd9b64927c1d8610494e86",
        "9ca6acdc3ba3061dda77098ad86dc17d8caa621d7df019006403b407f3d7a83e",
        "assay_office",
    ),
    "chapel": standard_spec(
        "chapel-3d", "chapel", "ChapelE2", "ChapelE3",
        "06dcd071ac85d73145fe750f477639721c7c190a78cc06331687fc28e0ded658",
        "ce63f235db7f31fe2e003abcb1580ad67d95ba164656e50c0a81127c9bec7ccd",
        "chapel",
    ),
    "dynamo_hall": standard_spec(
        "dynamo-hall-3d", "dynamo-hall", "DynamoHallE2", "DynamoHallE3",
        "04175cb2fefdc7e808c97afe34747f893293ca64adc4b56ee56a44012e2a6b44",
        "9db911e453593b3ac3a89bc76c1b967781a647f833f93c1a138f0ddcef1644e8",
        "dynamo_hall",
    ),
}


def lamp(parts, prefix, x, y, z, material, uv, inward=1):
    parts.extend((
        common.box(f"{prefix} iron lamp arm", (0.58, 0.10, 0.10), (x + inward * 0.24, y, z), material, uv["dark"], 0),
        common.box(f"{prefix} copper lamp drop", (0.07, 0.07, 0.28), (x + inward * 0.47, y, z - 0.16), material, uv["copper"], 0),
        pilot.sphere(f"{prefix} warm lamp bell", 0.15, (x + inward * 0.47, y, z - 0.36), material, uv["warm"], (0.82, 0.82, 1.10), 8, 4),
        common.torus(f"{prefix} teal lamp rim", 0.13, 0.025, (x + inward * 0.47, y, z - 0.34), material, uv["teal"]),
    ))


def roof_bus(parts, prefix, xs, y, base, material, uv):
    for index, x in enumerate(xs, 1):
        pilot.insulator(parts, f"{prefix} insulator {index}", x, y, base, material, uv)
    top = base + 0.48
    parts.extend((
        pilot.beam(f"{prefix} dark crossarm", (xs[0] - 0.18, y, base + 0.30), (xs[-1] + 0.18, y, base + 0.30), 0.075, material, uv["dark"], 8),
        pilot.beam(f"{prefix} copper line", (xs[0], y, top), (xs[-1], y, top), 0.045, material, uv["copper"], 8),
    ))
    return [(x, y, top + 0.08) for x in xs]


def add_tavern(material, uv):
    parts, _, _ = pilot.add_tavern(material, uv)
    for index, x in enumerate((-1.72, 1.72), 1):
        parts.extend((
            pilot.beam(
                f"Lounge roofline wire drop {index}", (x, -0.72, 3.52), (x, -1.50, 2.48),
                0.080, material, uv["copper"], 5,
            ),
            common.box(
                f"Lounge silhouette lamp arm {index}", (0.90, 0.16, 0.16),
                (x + (-0.34 if x > 0 else 0.34), -1.50, 2.52), material, uv["copper"], 0,
            ),
        ))
    parts.append(pilot.beam(
        "Lounge roofline conductor", (-1.72, -0.72, 3.52), (1.72, -0.72, 3.52),
        0.060, material, uv["copper"], 5,
    ))
    anchors = [(-1.72, -0.72, 3.58), (1.72, -0.72, 3.58), (2.065, 0.48, 2.25)]
    return parts, anchors, "Electric Lounge festoon, supported lamp arms, roofline wire drops, warm panes, and voltage pictogram"


def add_general_store(material, uv):
    parts = []
    # The false front hides the rear roof at the locked town camera. Put the
    # public feed on the facade roofline so its insulators break the silhouette.
    anchors = roof_bus(parts, "Store public roof feed", (-1.45, 0.0, 1.45), 1.02, 3.58, material, uv)
    lamp(parts, "Store west", -1.82, 1.44, 2.72, material, uv, 1)
    lamp(parts, "Store east", 1.82, 1.44, 2.72, material, uv, -1)
    parts.extend((
        pilot.beam("Store teal public conductor", (-1.45, 1.02, 4.04), (1.45, 1.02, 4.04), 0.065, material, uv["teal"], 8),
        pilot.beam("Store copper service drop", (1.45, 1.02, 4.06), (1.78, 1.20, 2.92), 0.070, material, uv["copper"], 8),
        pilot.beam("Store west lamp feed", (-1.45, 1.02, 4.06), (-1.58, 1.36, 2.96), 0.055, material, uv["copper"], 8),
        common.torus("Store delivery coil tell", 0.28, 0.045, (1.72, 1.55, 2.00), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
    ))
    return parts, anchors, "silhouette-breaking public roof feed, twin loading lamps, attached copper drops, and delivery coil"


def add_claim_office(material, uv):
    parts = []
    anchors = roof_bus(parts, "Civic voltage mast", (-1.35, -0.35, 0.65), -0.20, 4.30, material, uv)
    lamp(parts, "Civic west", -1.72, -1.38, 2.56, material, uv, 1)
    lamp(parts, "Civic east", 1.72, -1.38, 2.56, material, uv, -1)
    parts.extend((
        pilot.beam("Civic copper hall drop", (0.65, -0.20, 4.78), (1.38, -1.18, 3.12), 0.055, material, uv["copper"], 8),
        common.torus("Civic public voltage dial", 0.31, 0.045, (0, -1.50, 3.18), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Civic public dial hub", 0.08, 0.08, (0, -1.51, 3.18), material, uv["copper"], 8, rotation=(math.pi / 2, 0, 0)),
    ))
    return parts, anchors, "municipal roof feed, twin public arc lamps, copper hall drop, and voltage dial"


def add_assay_office(material, uv):
    parts = []
    anchors = roof_bus(parts, "Assay electrode rack", (-1.25, 0.0, 1.25), -0.16, 3.45, material, uv)
    lamp(parts, "Assay workbench", 1.72, -1.46, 2.48, material, uv, -1)
    parts.extend((
        pilot.beam("Assay high-voltage drop", (-1.25, -0.16, 3.93), (-1.72, -1.18, 2.62), 0.055, material, uv["copper"], 8),
        common.torus("Assay induction coil outer", 0.34, 0.045, (-0.48, -1.57, 2.44), material, uv["copper"], rotation=(math.pi / 2, 0, 0)),
        common.torus("Assay induction coil inner", 0.21, 0.035, (-0.48, -1.60, 2.44), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
        pilot.beam("Assay spark gap", (-0.69, -1.60, 2.44), (-0.27, -1.60, 2.44), 0.025, material, uv["dark"], 6),
    ))
    return parts, anchors, "roof electrode rack, copper laboratory drop, work lamp, and induction-coil assay tell"


def add_chapel(material, uv):
    parts = []
    lamp(parts, "Chapel west", -1.38, -1.41, 2.56, material, uv, 1)
    lamp(parts, "Chapel east", 1.38, -1.41, 2.56, material, uv, -1)
    # Two grounded lightning masts flank the heritage cross without boxing the
    # belfry in a construction-like gantry.
    for index, x in enumerate((-0.88, 0.88), 1):
        parts.extend((
            common.box(
                f"Chapel lightning mast roof saddle {index}", (0.34, 0.30, 0.14),
                (x, 0.34, 3.34), material, uv["dark"], 0.01,
            ),
            common.cylinder(
                f"Chapel lightning mast copper boot {index}", 0.13, 0.22,
                (x, 0.34, 3.49), material, uv["copper"], 10,
            ),
            common.cylinder(
                f"Chapel lightning mast teal boot band {index}", 0.145, 0.08,
                (x, 0.34, 3.55), material, uv["teal"], 10,
            ),
            pilot.beam(
                f"Chapel lightning mast support {index}", (x, 0.34, 3.42), (x, 0.34, 4.92),
                0.070, material, uv["dark"], 8,
            ),
        ))
        pilot.insulator(parts, f"Chapel lightning mast insulator {index}", x, 0.34, 4.72, material, uv)
    parts.extend((
        pilot.beam("Chapel west arc horn", (-0.88, 0.34, 5.20), (-0.30, 0.34, 5.48), 0.055, material, uv["copper"], 8),
        pilot.beam("Chapel east arc horn", (0.88, 0.34, 5.20), (0.30, 0.34, 5.48), 0.055, material, uv["copper"], 8),
        common.torus("Chapel west voltage crown", 0.18, 0.045, (-0.88, 0.34, 5.20), material, uv["teal"]),
        common.torus("Chapel east voltage crown", 0.18, 0.045, (0.88, 0.34, 5.20), material, uv["teal"]),
    ))
    parts.extend((
        common.torus("Chapel voltage covenant ring", 0.22, 0.035, (0, -1.53, 3.28), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
    ))
    anchors = [(-0.30, 0.34, 5.52), (0.30, 0.34, 5.52), (0, -1.53, 3.32)]
    return parts, anchors, "grounded twin lightning masts, teal voltage crowns, inward arc horns, porch lamps, and covenant ring"


def add_dynamo_hall(material, uv):
    parts = []
    anchors = roof_bus(parts, "Dynamo crown bus", (-1.70, -0.58, 0.58, 1.70), 0.55, 3.60, material, uv)
    lamp(parts, "Dynamo west status", -1.90, -1.41, 2.56, material, uv, 1)
    lamp(parts, "Dynamo east status", 1.90, -1.41, 2.56, material, uv, -1)
    parts.extend((
        pilot.beam("Dynamo west copper busbar", (-1.70, 0.55, 4.08), (-2.25, -1.18, 2.98), 0.075, material, uv["copper"], 8),
        pilot.beam("Dynamo east copper busbar", (1.70, 0.55, 4.08), (2.25, -1.18, 2.98), 0.075, material, uv["copper"], 8),
        pilot.beam("Dynamo teal crown conductor", (-1.70, 0.55, 4.06), (1.70, 0.55, 4.06), 0.080, material, uv["teal"], 8),
        common.torus("Dynamo roof induction toroid", 0.52, 0.075, (0, 0.22, 3.72), material, uv["teal"]),
        common.cylinder("Dynamo roof toroid hub", 0.15, 0.12, (0, 0.22, 3.72), material, uv["copper"], 10),
        common.box("Dynamo arc crown roof saddle", (0.42, 0.30, 0.12), (0.82, 0.55, 3.35), material, uv["dark"], 0.01),
        pilot.beam("Dynamo arc crown support", (0.82, 0.55, 3.36), (0.82, 0.55, 3.75), 0.075, material, uv["copper"], 8),
        common.torus("Dynamo arc crown", 0.32, 0.065, (0.82, 0.55, 3.75), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
        common.torus("Dynamo grid status toroid", 0.34, 0.055, (0, -1.54, 3.02), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Dynamo grid status hub", 0.10, 0.08, (0, -1.54, 3.02), material, uv["copper"], 10, rotation=(math.pi / 2, 0, 0)),
    ))
    return parts, anchors[:3], "four-insulator crown bus, high-contrast teal conductor, roof induction toroid, exiting busbars, and status lamps"


BUILDERS = {
    "tavern": add_tavern,
    "general_store": add_general_store,
    "claim_office": add_claim_office,
    "assay_office": add_assay_office,
    "chapel": add_chapel,
    "dynamo_hall": add_dynamo_hall,
}


def main():
    pilot.BUILDERS.update(BUILDERS)
    print(json.dumps([pilot.build_variant(key, spec) for key, spec in SPECS.items()], indent=2))


if __name__ == "__main__":
    main()
