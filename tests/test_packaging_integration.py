from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import pytest

from spindle_token import __version__


@pytest.mark.integration
def test_wheel_metadata_marks_pyspark_as_spark_extra_only() -> None:
    result = subprocess.run(
        ["poetry", "build", "-f", "wheel"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    dist_dir = Path(__file__).resolve().parents[1] / "dist"
    wheel = sorted(dist_dir.glob(f"spindle_token-{__version__}-*.whl"))[-1]
    with zipfile.ZipFile(wheel) as zf:
        metadata = zf.read(f"spindle_token-{__version__}.dist-info/METADATA").decode()

    assert "Requires-Dist: cryptography (>=50.0.0,<51.0.0)" in metadata
    assert "Provides-Extra: spark" in metadata
    assert 'Requires-Dist: pyspark (>=3.5.0,<4.2.0) ; extra == "spark"' in metadata
    assert "Requires-Dist: pyspark (>=3.5.0,<4.2.0)\n" not in metadata
