from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

sys.dont_write_bytecode = True


HERE = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = load("salvage_claw_detail_sol_render_base", HERE / "render_salvage_claw.py")
base.GLB = HERE / "salvage-claw-detail-sol.glb"
original_save_grid_image = base.save_grid_image
original_stamp = base.stamp


def detail_path(path: Path) -> Path:
    if path.name == "salvage-claw-turntable.png":
        return path.with_name("salvage-claw-detail-sol-turntable.png")
    return path


base.save_grid_image = lambda paths, output, rows, columns: original_save_grid_image(paths, detail_path(output), rows, columns)
base.stamp = lambda path, title, sha: original_stamp(detail_path(path), title.replace("SALVAGE CLAW", "SALVAGE CLAW DETAIL SOL"), sha)


if __name__ == "__main__":
    base.OUT.mkdir(parents=True, exist_ok=True)
    sha = base.subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=base.ROOT, text=True).strip()
    print(detail_path(base.render_turntable(sha)))
