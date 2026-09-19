from pathlib import Path
import importlib.util
import json
import math
import sys


HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pilot = load_module("wave9_e4_pilot_build", HERE / "build_wave9_e4_pilot.py")
e3_wide = load_module("wave8_e3_wide_build", HERE / "build_wave8_e3_wide.py")
common = pilot.common


def e4_spec(e3_spec, blend_sha, glb_sha):
    return {
        **e3_spec,
        "source": f'{e3_spec["stem"]}.e3',
        "object": e3_spec["output"],
        "output": e3_spec["output"].replace("E3", "E4"),
        "blend_sha": blend_sha,
        "glb_sha": glb_sha,
    }


SPECS = {
    "general_store": e4_spec(
        e3_wide.SPECS["general_store"],
        "bc2470e9ec2e767fa3e6cfda833eb41729ac691520103a50803da7cc0ba1185d",
        "1a13c3f766d35bb3ed4341b327eae53579e00740bde439667f74485ab7b35f57",
    ),
    "claim_office": e4_spec(
        e3_wide.SPECS["claim_office"],
        "b28e8d973208701f49424e923b0027f3cbef72be563c8872a5031eca928ea93f",
        "ce1f6953d4b391b14c3afec57a94f4a2e00c59e785c4c6bf4ccb384277420c73",
    ),
    "assay_office": e4_spec(
        e3_wide.SPECS["assay_office"],
        "cfb93bfea5b3381b32d65d136731ed2e28a4a71cee398e8e9f95ec1deaf633a8",
        "b9562ddbdabf492fe0f4a772fd89d72c1b72a5a78bdf227b5d6513ce6f1beacc",
    ),
    "chapel": e4_spec(
        e3_wide.SPECS["chapel"],
        "d02f38059c63550ea859cbcc4704fdc272de49c0da4b79e2c39bba578869c0fd",
        "ed2e11c0eeccc022d20d5797d1bf9cbeb9d33f9257ff2d9d4a580a3a9bb9ef40",
    ),
    "stamp_mill": e4_spec(
        e3_wide.pilot.SPECS["stamp_mill"],
        "b12de67a0c415f9c39e6ca760a1ab2158ef67b72a663b96a2fe48f9a4b825df9",
        "499fc7ecf4ab991ca276a362c1c79aaa270a9736b1f06e75dc95df8081658d0d",
    ),
    "dynamo_hall": e4_spec(
        e3_wide.SPECS["dynamo_hall"],
        "0c0546c3eb9143e86b46509376f312c78255c6c30ba7ec4b3b2bc36f10c8100c",
        "027857bebc8db0fd0a9c1749d14f2adf17cb585a32e40a091d18528f67ae67d9",
    ),
}


def drum(parts, prefix, location, material, uv, radius=0.24, height=0.82):
    x, y, z = location
    parts.extend((
        common.cylinder(prefix, radius, height, location, material, uv["copper"], 10),
        common.cylinder(f"{prefix} lower rubber band", radius + 0.015, 0.07, (x, y, z - height * 0.28), material, uv["dark"], 10),
        common.cylinder(f"{prefix} upper rubber band", radius + 0.015, 0.07, (x, y, z + height * 0.28), material, uv["dark"], 10),
    ))


def wheel(parts, prefix, location, material, uv, radius=0.25):
    parts.extend((
        common.torus(prefix, radius, 0.045, location, material, uv["dark"], rotation=(math.pi / 2, 0, 0)),
        common.cylinder(f"{prefix} brass hub", 0.09, 0.08, location, material, uv["copper"], 10, rotation=(math.pi / 2, 0, 0)),
    ))


def short_exhaust(parts, prefix, location, material, uv):
    x, y, z = location
    parts.extend((
        common.cylinder(f"{prefix} pipe", 0.07, 0.72, (x, y, z), material, uv["dark"], 8),
        common.cylinder(f"{prefix} brass collar", 0.11, 0.09, (x, y, z + 0.28), material, uv["copper"], 8),
        common.cylinder(f"{prefix} dust cap", 0.12, 0.08, (x, y, z + 0.39), material, uv["warm"], 8),
    ))
    return (x, y, z + 0.45)


def add_general_store(material, uv):
    parts = [
        common.box("Motor Supply garage canopy", (3.90, 0.72, 0.16), (0, 1.25, 2.45), material, uv["dark"], 0),
        common.box("Motor Supply iron fascia", (3.90, 0.08, 0.32), (0, 1.58, 2.28), material, uv["dark"], 0),
        common.box("Motor Supply west brass post", (0.13, 0.13, 2.18), (-1.75, 1.55, 1.13), material, uv["copper"], 0),
        common.box("Motor Supply east brass post", (0.13, 0.13, 2.18), (1.75, 1.55, 1.13), material, uv["copper"], 0),
        common.box("Motor Supply double garage door", (2.36, 0.04, 1.52), (0, 1.60, 1.25), material, uv["dark"], 0),
        common.box("Motor Supply garage door seam", (0.08, 0.04, 1.52), (0, 1.61, 1.25), material, uv["copper"], 0),
    ]
    for x in (-0.58, 0.58):
        for z in (0.91, 1.57):
            parts.append(common.box(f"Motor Supply door panel {x} {z}", (0.86, 0.035, 0.48), (x, 1.612, z), material, uv["warm"], 0))
    for x in (-0.12, 0.12):
        parts.append(common.box(f"Motor Supply brass door handle {x}", (0.055, 0.045, 0.28), (x, 1.607, 1.24), material, uv["copper"], 0))
    wheel(parts, "Motor Supply road wheel", (0, 1.57, 2.29), material, uv, 0.23)
    drum(parts, "Motor Supply fuel drum", (1.40, 1.32, 0.50), material, uv)
    exhaust = short_exhaust(parts, "Motor Supply service exhaust", (-1.95, 1.34, 1.18), material, uv)
    return parts, [exhaust, (1.40, 1.32, 0.96)], "Motor Supply garage canopy, double service doors, fuel drum, road-wheel sign, and light-dust exhaust"


def add_claim_office(material, uv):
    parts = [
        common.box("Road Office permit canopy", (3.10, 0.70, 0.16), (0, -1.18, 2.34), material, uv["dark"], 0),
        common.box("Road Office permit fascia", (3.10, 0.07, 0.30), (0, -1.52, 2.18), material, uv["dark"], 0),
        common.box("Road Office west brass post", (0.13, 0.13, 2.02), (-1.35, -1.49, 1.04), material, uv["copper"], 0),
        common.box("Road Office east brass post", (0.13, 0.13, 2.02), (1.35, -1.49, 1.04), material, uv["copper"], 0),
        common.box("Road Office sign mast", (0.13, 0.13, 3.62), (1.72, -1.45, 2.92), material, uv["copper"], 0),
        common.box("Road Office upper route board", (1.42, 0.08, 0.30), (1.10, -1.50, 4.38), material, uv["dark"], 0),
        common.box("Road Office lower route board", (1.18, 0.08, 0.27), (1.28, -1.50, 3.88), material, uv["warm"], 0),
    ]
    wheel(parts, "Road Office registry wheel", (0, -1.49, 2.18), material, uv, 0.22)
    parts.extend((
        common.torus("Road Office route-board wheel pictogram", 0.13, 0.03, (1.10, -1.525, 4.38), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Road Office route-board wheel hub", 0.05, 0.06, (1.10, -1.525, 4.38), material, uv["copper"], 8, rotation=(math.pi / 2, 0, 0)),
        pilot.beam("Road Office route-board diagonal brace", (1.70, -1.45, 3.42), (0.52, -1.45, 4.23), 0.045, material, uv["copper"], 6),
    ))
    exhaust = short_exhaust(parts, "Road Office registry exhaust", (-1.72, -1.30, 1.10), material, uv)
    return parts, [exhaust, (1.72, -1.45, 4.78)], "Road Office permit canopy, twin route boards, registry wheel, brass supports, and dust-only registry exhaust"


def add_assay_office(material, uv):
    parts = [
        common.box("Fuel Laboratory test hood", (3.52, 0.66, 0.16), (0, -1.31, 2.70), material, uv["dark"], 0),
        common.box("Fuel Laboratory hood fascia", (3.52, 0.06, 0.30), (0, -1.62, 2.52), material, uv["copper"], 0),
        common.box("Fuel Laboratory west tank foot", (0.18, 0.30, 0.72), (-1.18, -1.30, 0.72), material, uv["dark"], 0),
        common.box("Fuel Laboratory east tank foot", (0.18, 0.30, 0.72), (1.18, -1.30, 0.72), material, uv["dark"], 0),
        common.cylinder("Fuel Laboratory west test tank", 0.29, 1.38, (-0.72, -1.29, 1.35), material, uv["copper"], 12, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Fuel Laboratory east test tank", 0.29, 1.38, (0.72, -1.29, 1.35), material, uv["warm"], 12, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Fuel Laboratory roof motor tank", 0.29, 1.80, (-0.30, 0, 3.88), material, uv["warm"], 12, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Fuel Laboratory roof tank west rubber band", 0.31, 0.09, (-0.75, 0, 3.88), material, uv["dark"], 10, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Fuel Laboratory roof tank east rubber band", 0.31, 0.09, (0.15, 0, 3.88), material, uv["dark"], 10, rotation=(0, math.pi / 2, 0)),
        common.box("Fuel Laboratory roof tank west saddle", (0.18, 0.40, 0.24), (-0.75, 0, 3.55), material, uv["dark"], 0),
        common.box("Fuel Laboratory roof tank east saddle", (0.18, 0.40, 0.24), (0.15, 0, 3.55), material, uv["dark"], 0),
    ]
    for x in (-1.18, -0.26, 0.26, 1.18):
        parts.append(common.cylinder(f"Fuel Laboratory tank rubber band {x}", 0.31, 0.08, (x, -1.29, 1.35), material, uv["dark"], 10, rotation=(0, math.pi / 2, 0)))
    wheel(parts, "Fuel Laboratory octane dial", (0, -1.60, 2.53), material, uv, 0.25)
    anchors = [(-0.72, -1.29, 1.72), (0.72, -1.29, 1.72)]
    return parts, anchors, "Fuel Laboratory test hood, twin riveted facade tanks, roof motor-test tank, rubber test bands, and public octane dial"


def add_chapel(material, uv):
    parts = [
        common.box("Chapel parking rail", (1.82, 0.12, 0.14), (0, 1.45, 0.72), material, uv["dark"], 0),
        common.box("Chapel parking rail west post", (0.12, 0.12, 0.90), (-0.79, 1.45, 0.45), material, uv["copper"], 0),
        common.box("Chapel parking rail east post", (0.12, 0.12, 0.90), (0.79, 1.45, 0.45), material, uv["copper"], 0),
        common.cylinder("Chapel motor-age oil stain", 0.38, 0.01, (0.72, 1.18, 0.005), material, uv["dark"], 12),
    ]
    return parts, [], "Quiet Motor-age touch: a low parking rail and old oil stain; inherited chapel and prior-era hardware stay visually dominant"


def add_stamp_mill(material, uv):
    parts = [
        common.box("Engine Works lean-to roof", (4.42, 0.34, 0.16), (0, -0.61, 2.32), material, uv["dark"], 0),
        common.box("Engine Works iron fascia", (4.42, 0.04, 0.30), (0, -0.77, 2.15), material, uv["dark"], 0),
        common.box("Engine Works west brass post", (0.13, 0.08, 2.04), (-2.00, -0.74, 1.06), material, uv["copper"], 0),
        common.box("Engine Works east brass post", (0.13, 0.08, 2.04), (2.00, -0.74, 1.06), material, uv["copper"], 0),
    ]
    wheel(parts, "Engine Works rubber flywheel", (-1.18, -0.74, 1.42), material, uv, 0.52)
    wheel(parts, "Engine Works roof flywheel", (0, 0, 4.00), material, uv, 0.43)
    parts.extend((
        common.cylinder("Engine Works roof motor tank", 0.27, 1.46, (1.40, 0, 3.75), material, uv["copper"], 10, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Engine Works roof tank rubber band", 0.29, 0.09, (1.40, 0, 3.75), material, uv["dark"], 10, rotation=(0, math.pi / 2, 0)),
        common.box("Engine Works roof tank west saddle", (0.16, 0.38, 0.28), (0.92, 0, 3.47), material, uv["dark"], 0),
        common.box("Engine Works roof tank east saddle", (0.16, 0.38, 0.28), (1.88, 0, 3.47), material, uv["dark"], 0),
    ))
    for start, end in (((-1.70, -0.74, 1.42), (-0.66, -0.74, 1.42)), ((-1.18, -0.74, 0.90), (-1.18, -0.74, 1.94))):
        parts.append(pilot.beam("Engine Works flywheel spoke", start, end, 0.04, material, uv["copper"], 6))
    drum(parts, "Engine Works fuel drum", (2.42, -0.47, 0.50), material, uv)
    exhaust = short_exhaust(parts, "Engine Works motor exhaust", (2.64, -0.34, 1.10), material, uv)
    return parts, [exhaust, (1.40, 0, 4.04)], "Engine Works lean-to, facade and roof rubber-and-brass flywheels, saddle-mounted roof motor tank, fuel drum, retained electric motor, and dust-only exhaust"


def add_dynamo_hall(material, uv):
    parts = [
        common.box("Motor Works filling canopy", (4.42, 0.72, 0.16), (0, -1.23, 2.54), material, uv["dark"], 0),
        common.box("Motor Works filling fascia", (4.42, 0.06, 0.32), (0, -1.58, 2.36), material, uv["dark"], 0),
        common.box("Motor Works west brass post", (0.13, 0.13, 2.22), (-2.00, -1.54, 1.15), material, uv["copper"], 0),
        common.box("Motor Works east brass post", (0.13, 0.13, 2.22), (2.00, -1.54, 1.15), material, uv["copper"], 0),
        common.box("Motor Works west fuel pump", (0.52, 0.15, 1.36), (-1.18, -1.50, 0.86), material, uv["warm"], 0),
        common.box("Motor Works east fuel pump", (0.52, 0.15, 1.36), (1.18, -1.50, 0.86), material, uv["warm"], 0),
        common.box("Motor Works roof sign west mast", (0.12, 0.12, 0.92), (-1.18, 0, 3.57), material, uv["copper"], 0),
        common.box("Motor Works roof sign east mast", (0.12, 0.12, 0.92), (1.18, 0, 3.57), material, uv["copper"], 0),
        common.box("Motor Works roof road board", (3.24, 0.20, 0.20), (0, 0, 4.04), material, uv["warm"], 0),
        common.box("Motor Works west roof road fin", (0.30, 0.20, 0.76), (-2.38, 0, 3.70), material, uv["warm"], 0),
        common.box("Motor Works east roof road fin", (0.30, 0.20, 0.76), (2.38, 0, 3.70), material, uv["warm"], 0),
    ]
    for x in (-1.18, 1.18):
        wheel(parts, f"Motor Works rubber pump hose {x}", (x, -1.56, 0.93), material, uv, 0.18)
        parts.append(common.box(f"Motor Works brass pump handle {x}", (0.26, 0.06, 0.07), (x, -1.57, 1.30), material, uv["copper"], 0))
    wheel(parts, "Motor Works road crest", (0, -1.56, 2.37), material, uv, 0.24)
    parts.extend((
        common.torus("Motor Works roof road crest", 0.25, 0.045, (0, -0.12, 3.82), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Motor Works roof road crest hub", 0.09, 0.08, (0, -0.13, 3.82), material, uv["copper"], 10, rotation=(math.pi / 2, 0, 0)),
    ))
    anchors = [(-1.18, -1.58, 1.36), (1.18, -1.58, 1.36), (0, 0.22, 3.82)]
    return parts, anchors, "Motor Works filling canopy, twin brass-and-rubber pumps, plaza-visible roof road-sign rig, and retained voltage crown"


BUILDERS = {
    "general_store": add_general_store,
    "claim_office": add_claim_office,
    "assay_office": add_assay_office,
    "chapel": add_chapel,
    "stamp_mill": add_stamp_mill,
    "dynamo_hall": add_dynamo_hall,
}


def main():
    pilot.BUILDERS.update(BUILDERS)
    print(json.dumps([pilot.build_variant(key, spec) for key, spec in SPECS.items()], indent=2))


if __name__ == "__main__":
    main()
