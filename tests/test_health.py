import json
import importlib.util
from pathlib import Path

def test_module_loads():
    p = Path(__file__).resolve().parents[1] / "src" / "app.py"
    spec = importlib.util.spec_from_file_location("app", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main")
