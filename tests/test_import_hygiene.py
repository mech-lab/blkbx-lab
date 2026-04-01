import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_importing_hybrid_mechlab_does_not_import_hm_pyo3():
    env = os.environ.copy()
    existing_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) if not existing_path else f"{ROOT}{os.pathsep}{existing_path}"
    command = [
        sys.executable,
        "-c",
        (
            "import sys; "
            "import hybrid_mechlab; "
            "raise SystemExit(1 if 'hm_pyo3' in sys.modules else 0)"
        ),
    ]
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
