"""Assert that the pinned E1 panorama builder still reproduces the shipped E1 art.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
      --python assets/pilots/map-rebuild-spike/verify_e1_panoramas.py

Rebuilds every Epoch 1 panorama into a scratch directory -- it never writes into
`map-rebuild-spike/` -- and compares each rebuilt atlas PNG and GLB against the file
committed next to it. Exit 0 means "the generator and the shipped art still agree".

This guard exists because they once silently stopped agreeing: the E1 builder was
generalised into `build_contract_panoramas.py` for the E2..E10 families, its shared
paint and ring code was retuned, and E1 was never re-run. Nothing noticed for three
weeks, and a beauty shift that tried to repaint the night sky found that the only
gate-clean route would have replaced five shipped panoramas with art nobody approved
(reviews/beauty-night-shift.md F-2).

The .blend is deliberately NOT compared: Blender stores the absolute save path inside
it, so its bytes and sha256 depend on where the file was written. That is also the only
field the regenerated contract moves, which is why `files.blend` is not evidence of a
repaint and `files.atlas` / `files.glb` are.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile

OUT = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("e1_panorama_builder", OUT / "build_e1_contract_panoramas.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

# Compared artefacts, in the order a reader wants to see them fail.
ARTEFACTS = ("panorama-atlas.png", "panorama.glb")


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def main() -> int:
    keys = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else list(builder.PROFILES)
    unknown = [key for key in keys if key not in builder.PROFILES]
    if unknown:
        raise ValueError(f"not an Epoch 1 panorama: {', '.join(unknown)}")

    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="verify-e1-panoramas-") as scratch:
        builder.OUT = Path(scratch)
        for key in keys:
            builder.build(key)
            for artefact in ARTEFACTS:
                name = f"{key}-{artefact}"
                shipped, rebuilt = OUT / name, Path(scratch) / name
                if not shipped.is_file():
                    failures.append(f"{name}: no shipped file to compare against")
                    continue
                shipped_sha, rebuilt_sha = digest(shipped), digest(rebuilt)
                if shipped_sha == rebuilt_sha:
                    print(f"OK       {name}  {shipped_sha[:16]}")
                else:
                    failures.append(f"{name}: shipped {shipped_sha[:16]} != rebuilt {rebuilt_sha[:16]}")

    if failures:
        print("\nE1 PANORAMA DRIFT — the generator no longer reproduces the shipped art:")
        for failure in failures:
            print(f"  FAIL   {failure}")
        print("\nEither the art was hand-replaced, or a shared edit changed the E1 path.")
        return 1
    print(f"\nall {len(keys) * len(ARTEFACTS)} E1 panorama artefacts reproduce byte for byte")
    return 0


if __name__ == "__main__":
    sys.exit(main())
