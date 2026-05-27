# ABOUTME: Pytest helpers to import Lambda handler/psi modules that are packaged
# ABOUTME: independently (each lambdas/*/ is a zip root, not an importable package).
import importlib.util
import sys
from pathlib import Path

import pytest

SESSION_ROOT = Path(__file__).resolve().parent.parent
LAMBDAS = SESSION_ROOT / "lambdas"


def _load(path: Path, modname: str):
    """Load a module from a file path under a unique name.

    The module's own directory is placed on ``sys.path`` so sibling imports
    (e.g. the drift-detector handler importing ``psi``) resolve the same way they
    do inside the deployed Lambda zip.
    """
    pkg_dir = str(path.parent)
    if pkg_dir not in sys.path:
        sys.path.insert(0, pkg_dir)
    spec = importlib.util.spec_from_file_location(modname, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def import_lambda():
    """Return a loader: ``import_lambda(lambda_name, module="handler")``."""
    def _import(lambda_name: str, module: str = "handler"):
        path = LAMBDAS / lambda_name / f"{module}.py"
        modname = f"{lambda_name.replace('-', '_')}_{module}"
        return _load(path, modname)
    return _import


@pytest.fixture
def reference_df():
    """The captured reference distribution, if present (built in Phase 1)."""
    import pandas as pd
    parquet = SESSION_ROOT / "reference.parquet"
    if not parquet.exists():
        pytest.skip("reference.parquet not built; run scripts/capture-reference-distribution.py")
    return pd.read_parquet(parquet)
