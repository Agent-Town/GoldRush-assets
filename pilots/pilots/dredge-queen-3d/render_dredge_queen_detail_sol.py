from pathlib import Path
import importlib.util
import sys


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("dredge_queen_detail_sol_render_base", HERE / "render_dredge_queen.py")
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = base
spec.loader.exec_module(base)

base.GLB = HERE / "dredge-queen-detail-sol.glb"
save_grid = base.save_grid


def renamed_grid(paths, output, rows, columns):
    if output.name == "dredge-queen-turntable.png":
        output = output.with_name("dredge-queen-detail-sol-turntable.png")
    save_grid(paths, output, rows, columns)


base.save_grid = renamed_grid
base.render_turntable()
